from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Meeting, MeetingParticipant
from app.v1.models import ScheduleMeetingRequest, MeetingSlotRequest  # Import both request models
from core.scheduler import find_best_meeting_times  # Import scheduler
import random
import string


# Function to generate a unique meeting ID
def generate_meeting_id(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# Updated function to schedule a meeting based on user request
async def schedule_meeting(request: ScheduleMeetingRequest, db: Session = Depends(get_db)):
    # Fetch the organizer by email (the first participant is assumed to be the organizer)
    organizer_email = request.participants[0]
    organizer = db.query(User).filter(User.email == organizer_email).first()

    if not organizer:
        return {"error": "Organizer not found"}

    # Check if any participants exist in the DB
    participants_in_db = db.query(User).filter(User.email.in_(request.participants)).all()
    if not participants_in_db:
        return {"error": "Some participants are not found in the database"}

    # Ensure the start and end times are treated as UTC
    slot_start = request.slot_start.replace(tzinfo=None)  # Assuming input is in UTC
    slot_end = request.slot_end.replace(tzinfo=None)      # Assuming input is in UTC

    # Create a MeetingSlotRequest object to pass to the scheduler
    meeting_slot_request = MeetingSlotRequest(
        participants=request.participants,
        meeting_duration=(slot_end - slot_start).total_seconds() // 60,  # Convert duration to minutes
        meeting_title=request.meeting_title,
        meeting_description=request.meeting_description,
        start_time_window=slot_start.isoformat() + "Z",  # Adding 'Z' to indicate UTC
        end_time_window=slot_end.isoformat() + "Z",      # Adding 'Z' to indicate UTC
        priority=request.priority
    )

    # Call the scheduler function to find the best meeting slots
    best_slots = find_best_meeting_times(
        session=db,
        request=meeting_slot_request,
        adhoc_skip_factor=0.0,  # Customizable factor
        risk_tolerance=0.0      # Customizable factor
    )
    
    # If no available slots were found, return an error
    if not best_slots["best_slots"]:
        return {"error": "No available meeting slots found"}

    # Choose the first slot (you can choose other slots based on business logic)
    selected_slot = best_slots["best_slots"][0]

    # Generate a unique string-based meeting ID
    meeting_id = generate_meeting_id()

    # Create a new Meeting instance with the selected slot
    meeting = Meeting(
        meeting_id=meeting_id,
        organizer_id=organizer.user_id,
        title=request.meeting_title,
        description=request.meeting_description,
        start_time=selected_slot['slot_start'],  # Start time from best slots in UTC
        end_time=selected_slot['slot_end'],      # End time from best slots in UTC
        status="scheduled",
        priority=request.priority,
        risk_score=selected_slot['risk_score'],  # Use the risk score from the scheduler
        feasibility_score=selected_slot['feasibility_score'],  # Use the feasibility score
        calendar_event_id=None  # Can be linked to Google Calendar later
    )

    # Add the meeting to the database
    db.add(meeting)
    db.commit()

    # Add the participants (including the organizer)
    for participant_email in request.participants:
        participant_entry = MeetingParticipant(
            id=generate_meeting_id(),  # Generate a unique ID for the participant as well
            meeting_id=meeting.meeting_id,
            email=participant_email,
            role="participant" if participant_email != organizer_email else "organizer",  # Role based on email
            accepted=0  # Pending acceptance
        )

        # Add the participant to the database
        db.add(participant_entry)

    # Commit the changes for participants
    db.commit()

    return {
        "meeting_id": meeting.meeting_id,
        "title": meeting.title,
        "start_time": meeting.start_time.isoformat() + "Z",  # Return time in UTC with 'Z'
        "end_time": meeting.end_time.isoformat() + "Z",      # Return time in UTC with 'Z'
        "status": meeting.status,
        "priority": meeting.priority,
        "organizer": organizer.email,
        "participants": request.participants
    }
