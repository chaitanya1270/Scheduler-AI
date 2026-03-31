from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Meeting, MeetingParticipant
from app.v1.models import MeetingSlotRequest, ScheduleMeetingRequest  # Import the request model
from core.scheduler import find_best_meeting_times  # Import scheduler
import random
import string
from datetime import timezone, timedelta
from pytz import timezone, UTC  # Import UTC timezone
from datetime import timezone, timedelta

# Function to generate a unique meeting ID
def generate_meeting_id(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# Updated function to schedule a meeting based on user request
# async def schedule_meeting(request: MeetingSlotRequest, db: Session = Depends(get_db)):
#     # Fetch the organizer by email (the first participant is assumed to be the organizer)
#     organizer_email = request.participants[0]
#     organizer = db.query(User).filter(User.email == organizer_email).first()

#     if not organizer:
#         return {"error": "Organizer not found"}

#     # Check if any participants exist in the DB
#     participants_in_db = db.query(User).filter(User.email.in_(request.participants)).all()
#     if not participants_in_db:
#         return {"error": "Some participants are not found in the database"}

#     # Generate a unique string-based meeting ID
#     meeting_id = generate_meeting_id()
#     print(f"Generated meeting ID: {meeting_id}")

#     # Call the scheduler function to find the best meeting slot
#     best_slots_response = find_best_meeting_times(
#         session=db,
#         request=request,
#         adhoc_skip_factor=0.0,
#         risk_tolerance=0.0
#     )

#     # Print the best slots found
#     print("Best Slots Response:", best_slots_response)

#     # If no available slots were found, return an error
#     if not best_slots_response["best_slots"]:
#         return {"error": "No available meeting slots found"}

#     # Choose the first slot
#     selected_slot = best_slots_response["best_slots"][0]  # Access the first slot
#     print(f"Selected Slot: {selected_slot}")

#     # Assuming the selected slot's times are in UTC
#     selected_slot_start = selected_slot['slot_start']  # Should be in UTC
#     selected_slot_end = selected_slot['slot_end']      # Should be in UTC

#     # Ensure the times are timezone-aware and in UTC
#     # if selected_slot_start.tzinfo is None:
#     #     selected_slot_start = selected_slot_start.replace(tzinfo=UTC)
#     # if selected_slot_end.tzinfo is None:
#     #     selected_slot_end = selected_slot_end.replace(tzinfo=UTC)

#     from datetime import timezone, timedelta

#     # Subtract 5 hours and 30 minutes from the selected slot times
#     time_difference = timedelta(hours=5, minutes=30)
#     adjusted_slot_start = selected_slot_start - time_difference
#     adjusted_slot_end = selected_slot_end - time_difference

#     # Ensure adjusted_slot_start and adjusted_slot_end are in UTC timezone
#     utc_slot_start = adjusted_slot_start.replace(tzinfo=timezone.utc).isoformat()
#     utc_slot_end = adjusted_slot_end.replace(tzinfo=timezone.utc).isoformat()

#     meeting = Meeting(
#         meeting_id=meeting_id,
#         organizer_id=organizer.user_id,
#         title=request.meeting_title,
#         description=request.meeting_description,
#         start_time=utc_slot_start,  # Use 'adjusted_slot_start' in UTC with 'Z' format
#         end_time=utc_slot_end,      # Use 'adjusted_slot_end' in UTC with 'Z' format
#         status="pending",
#         priority=request.priority,
#         risk_score=selected_slot['risk_score'],  # Use risk score from selected slot
#         feasibility_score=selected_slot['feasibility_score'],  # Use feasibility score
#         calendar_event_id=None  # Can be linked to Google Calendar later
#     )

#     # Add the meeting to the database
#     db.add(meeting)
#     db.commit()
#     print(f"Meeting scheduled: {meeting}")

#     # Add the participants (including the organizer)
#     for participant_email in request.participants:
#         participant_entry = MeetingParticipant(
#             id=generate_meeting_id(),  # Generate a unique ID for the participant
#             meeting_id=meeting.meeting_id,
#             email=participant_email,
#             role="participant" if participant_email != organizer_email else "organizer",  # Role based on email
#             accepted=0  # Pending acceptance
#         )

#         # Add the participant to the database
#         db.add(participant_entry)
#         print(f"Added participant: {participant_entry}")

#     # Commit the changes for participants
#     db.commit()

#     return {
#         "meeting_id": meeting.meeting_id,
#         "title": meeting.title,
#         "start_time": meeting.start_time,
#         "end_time": meeting.end_time,
#         "status": meeting.status,
#         "priority": meeting.priority,
#         "organizer": organizer.email,
#         "participants": request.participants
#     }
async def schedule_meeting(request: MeetingSlotRequest, db: Session = Depends(get_db)):
    organizer_email = request.participants[0]
    organizer = db.query(User).filter(User.email == organizer_email).first()

    if not organizer:
        return {"error": "Organizer not found"}

    participants_in_db = db.query(User).filter(User.email.in_(request.participants)).all()
    if not participants_in_db:
        return {"error": "Some participants are not found in the database"}

    best_slots_response = find_best_meeting_times(
        session=db,
        request=request,
        adhoc_skip_factor=0.0,
        risk_tolerance=0.0
    )

    if not best_slots_response["best_slots"]:
        return {"error": "No available meeting slots found"}
    selected_slot = best_slots_response["best_slots"][0]
    
    schedule_request = ScheduleMeetingRequest(
        participants=[participant.email for participant in participants_in_db],
        meeting_duration=(selected_slot['slot_end'] - selected_slot['slot_start']).total_seconds() // 60,
        meeting_title=request.meeting_title,
        meeting_description=request.meeting_description,
        slot_start=selected_slot['slot_start'],
        slot_end=selected_slot['slot_end'],
        start_time_window=request.start_time_window,
        end_time_window=request.end_time_window,
        priority=request.priority
    )
    await store_meeting_details(selected_slot, request,  db)


async def store_meeting_details(meeting_details:dict, request:ScheduleMeetingRequest, db:Session):
    
    meeting_id = generate_meeting_id()
    print(f"Generated meeting ID: {meeting_id}")
    
    
    organizer_email = request.participants[0]
    organizer = db.query(User).filter(User.email == organizer_email).first()
    
    selected_slot_start = meeting_details['slot_start']
    selected_slot_end = meeting_details['slot_end']

    # Adjust selected slots if needed and convert to UTC
    time_difference = timedelta(hours=5, minutes=30)
    adjusted_slot_start = selected_slot_start - time_difference
    adjusted_slot_end = selected_slot_end - time_difference
    adjusted_slot_start_window = request.start_time_window - time_difference
    adjusted_slot_end_window = request.end_time_window - time_difference

    utc_slot_start = adjusted_slot_start.replace(tzinfo=timezone.utc).isoformat()
    utc_slot_end = adjusted_slot_end.replace(tzinfo=timezone.utc).isoformat()
    utc_slot_start_window = adjusted_slot_start_window.replace(tzinfo=timezone.utc).isoformat()
    utc_slot_end_window = adjusted_slot_end_window.replace(tzinfo=timezone.utc).isoformat()

    meeting = Meeting(
        meeting_id=meeting_id,
        organizer_id=organizer.user_id,
        title=request.meeting_title,
        description=request.meeting_description,
        start_time=utc_slot_start,
        end_time=utc_slot_end,
        start_time_window=utc_slot_start_window,  # Add the start_time_window from the request
        end_time_window=utc_slot_end_window,      # Add the end_time_window from the request
        status="pending",
        priority=request.priority,
        risk_score=meeting_details['risk_score'],
        feasibility_score=meeting_details['feasibility_score'],
        calendar_event_id=None
    )

    db.add(meeting)
    db.commit()
    print(f"Meeting scheduled: {meeting}")

    # Assuming `request` has the list of participant emails
    for participant_email in request.participants:
        # Fetch the user by email
        user = db.query(User).filter(User.email == participant_email).first()
        
        if not user:
            print(f"User not found for email: {participant_email}. Skipping participant addition.")
            continue  # Skip to the next participant if user is not found

        # Create a MeetingParticipant entry
        participant_entry = MeetingParticipant(
            id=generate_meeting_id(),  # Generate a unique ID for the participant
            meeting_id=meeting.meeting_id,
            email=participant_email,
            user_id=user.user_id,  # Update with the user_id from the User table
            role="participant" if participant_email != organizer_email else "organizer",
            accepted=0  # Pending acceptance
        )

        db.add(participant_entry)
        print(f"Added participant: {participant_entry}")

    # Commit the changes for participants
    db.commit()


    return {
        "meeting_id": meeting.meeting_id,
        "title": meeting.title,
        "start_time": meeting.start_time,
        "end_time": meeting.end_time,
        "start_time_window": meeting.start_time_window,  # Include in response
        "end_time_window": meeting.end_time_window,      # Include in response
        "status": meeting.status,
        "priority": meeting.priority,
        "organizer": organizer.email,
        "participants": request.participants
    }
