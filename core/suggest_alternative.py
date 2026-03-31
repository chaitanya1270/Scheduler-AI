from datetime import datetime, timedelta

def suggest_alternatives(common_slots, priority, participants_availability, meeting_duration):
    """
    Suggest alternative time slots when no perfect common slot is available.
    
    Parameters:
    common_slots (list): List of common available time slots for participants.
    priority (str): Priority of the meeting (e.g., 'high', 'medium', 'low').
    participants_availability (dict): Availability of each participant, including their busy slots.
    meeting_duration (timedelta): Duration of the required meeting.
    
    Returns:
    tuple: The best alternative time slot (start, end), or None if no suitable slot is found.
    """
    
    # If high priority, try to reschedule conflicting lower-priority meetings
    if priority == 'high':
        # Check each participant's availability and reschedule low-priority meetings
        for participant, availability in participants_availability.items():
            # Look for conflicts with lower-priority meetings and attempt to reschedule them
            for busy_slot in availability.get('busy', []):
                # If a conflict exists in the common slots, we try to move the conflicting meeting
                if any(busy_slot[0] <= common_slot[0] <= busy_slot[1] for common_slot in common_slots):
                    # We assume we can reschedule the lower-priority meeting (e.g., freeing the slot)
                    # Remove the conflict to make room for this high-priority meeting
                    availability['busy'].remove(busy_slot)
                    # After rescheduling, check if we can find a free slot
                    new_slot = find_free_slot(availability, meeting_duration)
                    if new_slot:
                        return new_slot

    # If medium priority, suggest partial availability
    elif priority == 'medium':
        # Find slots where only optional participants are unavailable
        alternative_slots = []
        for common_slot in common_slots:
            unavailable_count = 0
            for participant, availability in participants_availability.items():
                if any(busy_slot[0] <= common_slot[0] <= busy_slot[1] for busy_slot in availability.get('busy', [])):
                    unavailable_count += 1
            # If a majority of required participants are available, suggest the slot
            if unavailable_count == 0:  # All participants are free
                return common_slot
            elif unavailable_count <= len(participants_availability) // 2:  # At least half the participants are free
                alternative_slots.append(common_slot)
        # Return the best partial slot
        if alternative_slots:
            return alternative_slots[0]

    # If low priority, suggest slots with the most participants available
    elif priority == 'low':
        # Find slots with the most participants available
        best_slot = None
        max_available = 0
        for common_slot in common_slots:
            available_count = 0
            for participant, availability in participants_availability.items():
                if not any(busy_slot[0] <= common_slot[0] <= busy_slot[1] for busy_slot in availability.get('busy', [])):
                    available_count += 1
            # Choose the slot with the highest number of available participants
            if available_count > max_available:
                max_available = available_count
                best_slot = common_slot
        return best_slot
    
    # If no slot could be found
    return None

def find_free_slot(availability, meeting_duration):
    """
    Find the next free slot in the participant's availability that can accommodate the meeting duration.
    
    Parameters:
    availability (dict): The participant's availability and busy slots.
    meeting_duration (timedelta): Duration of the required meeting.
    
    Returns:
    tuple: The next available slot (start, end) or None if no suitable slot is found.
    """
    for free_slot in availability.get('free', []):
        start, end = free_slot
        if (end - start) >= meeting_duration:
            return (start, start + meeting_duration)
    return None
