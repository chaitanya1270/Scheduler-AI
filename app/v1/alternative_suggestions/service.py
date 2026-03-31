from sqlalchemy.orm import Session
from app.db.models import Meeting, MeetingParticipant, DeclinedMeeting, User  # Import CalendarEvent
from app.v1.models import MeetingSlotRequest, ScheduleMeetingRequest
from core.scheduler import find_best_meeting_times
from app.v1.schedule_demo.service import store_meeting_details  # Import the existing scheduling logic
from datetime import timezone, timedelta
import random
import string

def generate_meeting_id(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def handle_rejected_meeting(session: Session, meeting_id: str, rejection_reason: str = None):
    # Fetch the meeting by ID
    meeting = session.query(Meeting).filter_by(meeting_id=meeting_id).first()
    if not meeting:
        raise ValueError(f"Meeting with ID {meeting_id} not found")

    # Fetch the organizer's information
    organizer = session.query(User).filter_by(user_id=meeting.organizer_id).first()
    if not organizer:
        raise ValueError(f"Organizer for meeting ID {meeting_id} not found")

    organizer_email = organizer.email  # Get the organizer's email
    organizer_id = organizer.user_id  # Get the organizer's user ID
    print(organizer_email)
    print(organizer_id)
    declined_id = generate_meeting_id()
    declined_meeting = DeclinedMeeting(
        id = declined_id,
        meeting_id=meeting_id,
        user_id=organizer_id,  # Set the user_id as the organizer's user ID
        email=organizer_email,  # Only the organizer's email  # Optional reason for rejection
    )
    session.add(declined_meeting)  # Add the declined meeting to the session

    # Commit the changes to save the declined meeting
    session.commit()

    # Create a new MeetingSlotRequest to find alternative slots
    participants = session.query(MeetingParticipant).filter_by(meeting_id=meeting_id).all()
    participant_emails = [participant.email for participant in participants]  # Collect participant emails

    request = MeetingSlotRequest(
        participants=participant_emails,
        meeting_duration=(meeting.end_time - meeting.start_time).total_seconds() // 60,
        meeting_title=meeting.title,
        meeting_description=meeting.description,
        start_time_window=meeting.start_time_window,
        end_time_window=meeting.end_time_window,
        priority=meeting.priority
    )

    # Find available slots for rescheduling
    available_slots = find_best_meeting_times(session, request)

    # Convert the current meeting start and end times to UTC
    utc_meeting_start = meeting.start_time.replace(tzinfo=timezone.utc).isoformat()
    utc_meeting_end = meeting.end_time.replace(tzinfo=timezone.utc).isoformat()

    next_best_slot = None

    # Iterate through the available slots and compare with the original meeting times
    for slot in available_slots["best_slots"]:
        selected_slot_start = slot["slot_start"]
        selected_slot_end = slot["slot_end"]

        # Convert to UTC
        utc_slot_start = selected_slot_start.replace(tzinfo=timezone.utc).isoformat()
        utc_slot_end = selected_slot_end.replace(tzinfo=timezone.utc).isoformat()

        # If the slot is different from the original meeting time, it's a potential next best slot
        if utc_slot_start != utc_meeting_start and utc_slot_end != utc_meeting_end:
            next_best_slot = slot
            break

    # If a next best slot is found, return it, otherwise return failure
    if next_best_slot:
        return {
            "status": "success",
            "message": "Next best slot found",
            "next_slot": next_best_slot
        }
    else:
        return {
            "status": "failure",
            "message": "No alternative slots available"
        }


async def suggest_alternative_slots(session: Session, meeting_id: str):
    response = handle_rejected_meeting(session, meeting_id)

    meeting = session.query(Meeting).filter_by(meeting_id=meeting_id).first()
    if not meeting:
        raise ValueError(f"Meeting with ID {meeting_id} not found")

    participants = session.query(MeetingParticipant).filter_by(meeting_id=meeting_id).all()

    if response["status"] == "failure":
        meeting_priority = meeting.priority

        if meeting_priority == "high":
            return {
                "status": "reschedule",
                "message": "No common availability found. Rescheduling for a high-priority meeting.",
                "next_steps": "Reschedule immediately."
            }
        else:
            return {
                "status": "notify",
                "message": "No common availability found. Notify participants to find a suitable time.",
                "next_steps": "Send notifications to participants."
            }

    next_best_slot = response["next_slot"]
    reschedule_request = ScheduleMeetingRequest(
        participants=[participant.email for participant in participants],
        meeting_duration=(next_best_slot['slot_end'] - next_best_slot['slot_start']).total_seconds() // 60,
        meeting_title=meeting.title,
        meeting_description=meeting.description,
        slot_start=next_best_slot['slot_start'],
        slot_end=next_best_slot['slot_end'],
        start_time_window=meeting.start_time_window,
        end_time_window=meeting.end_time_window,
        priority=meeting.priority
    )

    # If schedule_meeting is asynchronous, await it properly
    schedule_meeting_response = await store_meeting_details(next_best_slot, reschedule_request, db=session)

    if schedule_meeting_response:
        return {
            "status": "success",
            "message": "Meeting rescheduled to the next best slot.",
            "meeting_details": schedule_meeting_response
        }
    else:
        return {
            "status": "failure",
            "message": "Failed to reschedule the meeting."
        }
