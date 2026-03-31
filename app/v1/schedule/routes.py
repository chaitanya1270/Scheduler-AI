# app/v1/routes.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import User
from app.response import ApiResponse
from app.supabase_auth import verify_user
from app.db.database import get_db
from app.v1.models import MeetingSlotRequest
from core.scheduler import fetch_and_filter_availability, find_best_meeting_times
from core.suggest_alternative import suggest_alternatives
from datetime import datetime, timedelta
from app.db import models
from app.db.models import User, Meeting, MeetingParticipant
from app.v1.models import MeetingSlotRequest
from core.google.calendar import create_google_calendar_event
from core.microsoft.calendar import create_microsoft_calendar_event
from app.v1.communication import service as comm_service

scheduler_router = APIRouter()

# --- Smart Meeting Scheduler Routes ---

# Route to schedule a meeting
@scheduler_router.post("/schedule/find_slot")
async def find_slot(
    request: MeetingSlotRequest,
    token: str,
    db: Session = Depends(get_db)
):
    user_data = await verify_user(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    organizer_id = user_data['id']
    organizer = db.query(User).filter_by(user_id=organizer_id).first()

    if not organizer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizer not found")

    # Prepare meeting details
    meeting_details = {
        'organizer_id': organizer_id,
        'title': request.meeting_title,
        'description': request.meeting_description,
        'participants': request.participants,
        'priority': request.priority,
        'meeting_duration': request.meeting_duration,
        'start_time_window': request.start_time_window,
        'end_time_window': request.end_time_window
    }

    # Fetch availability for participants who are users
    participants_info = []
    for email in request.participants:
        participant_user = db.query(User).filter_by(email=email).first()
        if participant_user:
            participants_info.append({'user_id': participant_user.user_id})
        else:
            # External participant
            pass  # Handle as needed
    result = find_best_meeting_times(db, participants_info, meeting_details, datetime.now(), timedelta(days=30), 0, 0)
    ApiResponse.response_ok(result)


@scheduler_router.post("/schedule/confirm_slot")
async def schedule_meeting_route(
    request: MeetingSlotRequest,
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user_data = await verify_user(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    organizer_id = user_data['id']
    organizer = db.query(models.User).filter_by(id=organizer_id).first()

    if not organizer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizer not found")

    # Find the best meeting times
    best_slot_info = find_best_meeting_times(db, request)
    best_slot = best_slot_info['best_slot']
    risk_score = best_slot_info['risk_score']
    feasibility_score = best_slot_info['feasibility_score']

    if not best_slot:
        raise HTTPException(status_code=400, detail="No suitable meeting slot found.")

    # Prepare attendees list
    attendees = []
    participants_info = []
    for email in request.participants:
        participant_user = db.query(models.User).filter_by(email=email).first()
        if participant_user:
            participants_info.append(participant_user)
            attendees.append({'email': participant_user.email})
        else:
            # External participant
            attendees.append({'email': email})
            participants_info.append({'email': email})

    # Create the event in the organizer's calendar
    event = {
        'summary': request.meeting_title,
        'description': request.meeting_description,
        'start': {
            'dateTime': best_slot[0].isoformat(),
            'timeZone': organizer.timezone or 'UTC'  # Default to UTC if timezone not set
        },
        'end': {
            'dateTime': best_slot[1].isoformat(),
            'timeZone': organizer.timezone or 'UTC'
        },
        'attendees': attendees,
    }

    # Depending on the organizer's provider, create the event in their calendar
    if organizer.provider == 'google':
        event_result = await create_google_calendar_event(organizer, event)
    elif organizer.provider == 'microsoft':
        event_result = await create_microsoft_calendar_event(organizer, event)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {organizer.provider}"
        )

    # Save the meeting details to the database
    meeting = models.Meeting(
        id=uuid.uuid4(),
        organizer_id=organizer.id,
        title=request.meeting_title,
        description=request.meeting_description,
        start_time=best_slot[0],
        end_time=best_slot[1],
        status='scheduled',
        priority=request.priority,
        risk_score=risk_score,
        feasibility_score=feasibility_score,
        calendar_event_id=event_result.get('id')  # Assuming event_result contains the event ID
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Add participants with RSVP status
    for participant in participants_info:
        if isinstance(participant, models.User):
            meeting_participant = models.MeetingParticipant(
                meeting_id=meeting.id,
                user_id=participant.id,
                email=participant.email,
                role='participant',
                accepted=0  # Initial RSVP status
            )
        else:
            meeting_participant = models.MeetingParticipant(
                meeting_id=meeting.id,
                email=participant['email'],
                role='participant',
                accepted=0  # Initial RSVP status
            )
        db.add(meeting_participant)

    db.commit()

    # Generate .ics file
    ics_file = comm_service.generate_ics_file(
        meeting_title=meeting.title,
        slot_start=meeting.start_time,
        slot_end=meeting.end_time,
        description=meeting.description or "",
        location=""
    )

    # Send initial notifications
    for participant in meeting.participants:
        comm_service.notify_participant(
            background_tasks,
            participant_email=participant.email,
            meeting_title=meeting.title,
            slot_start=meeting.start_time.strftime("%Y-%m-%d %H:%M"),
            slot_end=meeting.end_time.strftime("%Y-%m-%d %H:%M"),
            message="You have been invited to a meeting. Please respond to this invitation.",
            ics_file=ics_file,
            ics_filename=f"{meeting.title}.ics"
        )

    return {
        'message': 'Meeting scheduled successfully',
        'meeting_id': meeting.id,
        'best_slot': best_slot,
        'risk_score': risk_score,
        'feasibility_score': feasibility_score
    }