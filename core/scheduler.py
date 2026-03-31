from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
import pytz
from app.db.models import User, Meeting, DeclinedMeeting
from app.v1.models import MeetingSlotRequest
from core.google.calendar import fetch_and_store_calendar_events
from core.microsoft.calendar import fetch_microsoft_calendar_events
from core.suggest_alternative import suggest_alternatives


import pytz
from datetime import datetime, timedelta

def calculate_proximity_factor(slot_start, end_time_window, meeting_duration):
    """
    Calculate the proximity factor based on how close the slot is to the end of the time window,
    factoring in the duration of the meeting.
    """
    if isinstance(meeting_duration, int):
        meeting_duration = timedelta(minutes=meeting_duration)

    timezone = pytz.UTC  # Adjust this to the appropriate timezone if needed

    # Ensure `slot_start` and `end_time_window` are timezone-aware
    if slot_start.tzinfo is None:
        slot_start = timezone.localize(slot_start)
    if end_time_window.tzinfo is None:
        end_time_window = timezone.localize(end_time_window)

    # Ensure `current_time` is timezone-aware
    current_time = datetime.now(timezone)

    # Calculate the latest possible start time for the meeting
    last_possible_start_time = end_time_window - meeting_duration

    # Time until the latest possible start time and slot start
    time_until_latest_start = (last_possible_start_time - current_time).total_seconds()
    time_until_slot_start = (slot_start - current_time).total_seconds()

    # If there's no time left to start the meeting or the slot is in the past
    if time_until_latest_start <= 0 or time_until_slot_start <= 0:
        return 1.0  # Maximum risk

    # Avoid division by very small `time_until_latest_start`
    if time_until_latest_start < 60:  # Less than 1 minute
        return 1.0  # Maximum risk if it's too close to the deadline

    # Calculate the proximity factor
    proximity_factor =1- (time_until_slot_start / time_until_latest_start)

    # Ensure the proximity factor is between 0 and 1
    proximity_factor = max(0, min(proximity_factor, 1))

    return proximity_factor




def calculate_buffer_factor(
    slot_start,
    slot_end,
    previous_slot_end=None,
    next_slot_start=None,
    buffer_duration=timedelta(minutes=15),
):
    """
    Calculate the buffer factor based on available buffer time before and after the slot.
    """
    buffer_factor = 0.0

    if previous_slot_end and (slot_start - previous_slot_end) < buffer_duration:
        buffer_factor += 0.5  # Increase risk if there is no buffer before the slot

    if next_slot_start and (next_slot_start - slot_end) < buffer_duration:
        buffer_factor += 0.5  # Increase risk if there is no buffer after the slot

    return buffer_factor


def calculate_risk_and_feasibility(
    best_slot, end_time_window, meeting_duration, adhoc_skip_factor, risk_tolerance
):
    """
    Calculate the risk score and feasibility score for a given time slot.
    """
    slot_start, slot_end = best_slot

    proximity_factor = calculate_proximity_factor(slot_start, end_time_window, meeting_duration)
    buffer_factor = calculate_buffer_factor(slot_start, slot_end)

    risk_score = proximity_factor + adhoc_skip_factor + buffer_factor
    risk_score = risk_score / (1 + risk_tolerance)
    feasibility_score = 1 / (1 + risk_score)

    return risk_score, feasibility_score


def sort_by_risk(
    common_slots,
    end_time_window,
    meeting_duration,
    adhoc_skip_factor=0.0,
    risk_tolerance=0.0,
    risk_calculation_start_time=None,
):
    """
    Sort the common time slots by risk.
    """
    if risk_calculation_start_time is None:
        risk_calculation_start_time = datetime.now()

    sorted_slots = []

    for i, (slot_start, slot_end) in enumerate(common_slots):
        proximity_factor = calculate_proximity_factor(slot_start, end_time_window, meeting_duration)
        print(slot_start, slot_end, proximity_factor)
        previous_slot_end = common_slots[i - 1][1] if i > 0 else None
        next_slot_start = common_slots[i + 1][0] if i < len(common_slots) - 1 else None
        buffer_factor = calculate_buffer_factor(slot_start, slot_end, previous_slot_end, next_slot_start)

        risk_score = proximity_factor + adhoc_skip_factor + buffer_factor
        risk_score = 1-(risk_score / (1 + risk_tolerance))
        feasibility_score = 1 / (1 + risk_score)

        sorted_slots.append((slot_start, slot_end, risk_score, feasibility_score))

    sorted_slots.sort(key=lambda x: x[2])  # Sort by risk score
    return sorted_slots

from datetime import datetime
import pytz

def filter_existing_events_by_working_hours(events, working_hours_start, working_hours_end, start_time_window, end_time_window):
    """
    Filter events by working hours and the request's time window.
    If no events exist, return an empty list.
    """
    # Ensure start_time_window and end_time_window are offset-aware by setting a timezone (e.g., UTC)
    timezone = pytz.UTC
    if start_time_window.tzinfo is None:
        start_time_window = timezone.localize(start_time_window)
    if end_time_window.tzinfo is None:
        end_time_window = timezone.localize(end_time_window)
    print('events')
    print(events)
    print(len(events))
    # If there are no events, return an empty list
    if len(events)==0:
        return []

    filtered_events = []
    for event_start, event_end in events:
        # Parse event start and end times, which should already be offset-aware
        event_start = datetime.fromisoformat(event_start)
        event_end = datetime.fromisoformat(event_end)

        # Ensure event times are offset-aware
        if event_start.tzinfo is None:
            event_start = timezone.localize(event_start)
        if event_end.tzinfo is None:
            event_end = timezone.localize(event_end)

        # Filter by working hours and the provided time window
        if event_start.time() >= working_hours_start and event_end.time() <= working_hours_end:
            if event_start >= start_time_window and event_end <= end_time_window:
                filtered_events.append((event_start, event_end))

    return filtered_events




def fetch_and_filter_availability(
    session: Session, participants, start_time_window, end_time_window, meeting_duration
):
    """
    Fetch and filter availability for all participants within the given time window.
    """
    filtered_availabilities = {}

    for user_id in participants:
        print(user_id)
        user = session.query(User).filter_by(email=user_id).first()

        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if user.provider == "google":
            events = fetch_and_store_calendar_events(user, start_time_window, end_time_window, session)
        else:
            raise ValueError(f"Unknown provider: {user.provider}")

        # Check the declined_meetings table for any declined meetings by the participant
        declined_meetings = session.query(DeclinedMeeting).filter_by(user_id=user.user_id).all()

        for declined in declined_meetings:
            # Fetch the corresponding meeting
            meeting = session.query(Meeting).filter_by(meeting_id=declined.meeting_id).first()

            # Compare the start and end time windows of the meeting with the requested window
            if meeting.start_time_window == start_time_window and meeting.end_time_window == end_time_window:
                # If it matches, convert the meeting's start and end times to strings and add them to the events list
                events.append((meeting.start_time.isoformat(), meeting.end_time.isoformat()))

        # Ensure 'start' and 'end' are properly handled as datetime objects in tuples
        events_list = []
        for event in events:
            # Access start and end times using tuple indices (0 for start, 1 for end)
            start_time = event[0]
            end_time = event[1]

            events_list.append((start_time, end_time))

        # Filter the user's events by working hours
        existing_events = filter_existing_events_by_working_hours(
            events_list, user.working_hours_start, user.working_hours_end, start_time_window, end_time_window
        )

        # Get free slots based on the filtered events
        free_slots = get_free_slots(
            existing_events, start_time_window, end_time_window, user.working_hours_start, user.working_hours_end, meeting_duration
        )

        filtered_availabilities[user_id] = free_slots

    return filtered_availabilities





from datetime import datetime, timedelta
import pytz

def get_free_slots(busy_slots, start_time_window, end_time_window, working_hours_start, working_hours_end, meeting_duration):
    """
    Calculate free slots given the busy slots, time window, and required meeting duration.
    If busy_slots is empty, return all available slots within the working hours.
    """
    timezone = pytz.UTC  # Use UTC, or adjust to a specific timezone if required

    # Ensure that start_time_window and end_time_window are timezone-aware
    if start_time_window.tzinfo is None:
        start_time_window = timezone.localize(start_time_window)
    if end_time_window.tzinfo is None:
        end_time_window = timezone.localize(end_time_window)

    # Define working hours for the day, ensuring they are timezone-aware
    start_work_time = timezone.localize(datetime.combine(start_time_window.date(), working_hours_start))
    end_work_time = timezone.localize(datetime.combine(end_time_window.date(), working_hours_end))

    # Determine the valid start and end times within working hours and time window
    start_time = max(start_time_window, start_work_time)
    end_time = min(end_time_window, end_work_time)

    # If busy_slots is empty, return all available slots within working hours
    if not busy_slots:
        return _get_slots_within_duration(start_time, end_time, meeting_duration)

    # Initialize free slots with the working hours time window
    free_slots = [(start_time, end_time)]

    for busy_start, busy_end in busy_slots:
        # Ensure busy slots are also timezone-aware
        if busy_start.tzinfo is None:
            busy_start = timezone.localize(busy_start)
        if busy_end.tzinfo is None:
            busy_end = timezone.localize(busy_end)

        new_free_slots = []
        for free_start, free_end in free_slots:
            # Ensure free slots are timezone-aware
            if free_start.tzinfo is None:
                free_start = timezone.localize(free_start)
            if free_end.tzinfo is None:
                free_end = timezone.localize(free_end)

            # Check for overlap between busy slots and free slots
            if busy_end <= free_start or busy_start >= free_end:
                new_free_slots.append((free_start, free_end))  # No overlap
            else:
                # Split free slot around the busy slot
                if free_start < busy_start:
                    new_free_slots.append((free_start, busy_start))  # Before the busy slot
                if busy_end < free_end:
                    new_free_slots.append((busy_end, free_end))  # After the busy slot

        free_slots = new_free_slots  # Update free slots with the new free slots

    # Split free slots into chunks that match the meeting duration
    exact_duration_slots = []
    for free_start, free_end in free_slots:
        exact_duration_slots.extend(_get_slots_within_duration(free_start, free_end, meeting_duration))

    return exact_duration_slots

def _get_slots_within_duration(start_time, end_time, meeting_duration):
    """
    Helper function to generate free slots based on the meeting duration.
    """
    if not isinstance(meeting_duration, timedelta):
        meeting_duration = timedelta(minutes=meeting_duration)

    exact_duration_slots = []
    slot_start = start_time
    while slot_start + meeting_duration <= end_time:
        slot_end = slot_start + meeting_duration
        exact_duration_slots.append((slot_start, slot_end))
        slot_start = slot_end  # Move to the next slot after the current one

    return exact_duration_slots







def intersect_availability(available_slots, meeting_duration):
    """
    Find common available time slots across all participants.
    """
    if isinstance(meeting_duration, int):
        meeting_duration = timedelta(minutes=meeting_duration)

    common_slots = available_slots[next(iter(available_slots))]
    for user_id, slots in available_slots.items():
        new_common_slots = []
        for slot1_start, slot1_end in common_slots:
            for slot2_start, slot2_end in slots:
                start = max(slot1_start, slot2_start)
                end = min(slot1_end, slot2_end)
                # Ensure that the meeting duration fits within the intersected slot
                if start + meeting_duration <= end:
                    new_common_slots.append((start, end))
        common_slots = new_common_slots

    return common_slots



def find_best_meeting_times(
    session: Session,
    request: MeetingSlotRequest,
    adhoc_skip_factor=0.0,
    risk_tolerance=0.0,
):
    """
    Find the best meeting times based on participants' availability and the request parameters.
    """
    meeting_duration = timedelta(minutes=request.meeting_duration)
    print('calling fetch_and_filter_availability')
    print(request.participants)
    available_slots = fetch_and_filter_availability(
        session,
        request.participants,
        request.start_time_window,
        request.end_time_window,
        meeting_duration
    )

    common_slots = intersect_availability(available_slots, meeting_duration)
    print(common_slots)
    if not common_slots:
        best_slot = suggest_alternatives(
            common_slots, request.priority, available_slots, meeting_duration
        )
        if not best_slot:
            raise ValueError("No available time slots found within the given time window.")
    else:
        risk_free_slots = sort_by_risk(
            common_slots=common_slots, 
            end_time_window=request.end_time_window, 
            meeting_duration=meeting_duration,
            adhoc_skip_factor=adhoc_skip_factor,
            risk_tolerance=risk_tolerance
        )

    best_slots = risk_free_slots[:3]  # Take the first 3 slots, if available
    print(risk_free_slots)
    return {
        "best_slots": [
            {
                "slot_start": slot_start,
                "slot_end": slot_end,
                "risk_score": risk_score,
                "feasibility_score": feasibility_score
            }
            for (slot_start, slot_end, risk_score, feasibility_score) in best_slots
        ]
    }
