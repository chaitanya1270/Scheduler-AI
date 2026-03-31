from datetime import datetime, timedelta

def calculate_proximity_factor(slot_end, deadline):
    """Calculate the proximity factor based on how close the slot is to the deadline."""
    time_until_deadline = (deadline - datetime.now()).total_seconds()
    time_until_slot_end = (slot_end - datetime.now()).total_seconds()
    
    if time_until_deadline <= 0:  # Past the deadline
        return 1.0
    
    proximity_factor = 1 - (time_until_slot_end / time_until_deadline)
    return max(0, proximity_factor)  # Ensure it's between 0 and 1

def calculate_buffer_factor(slot_start, slot_end, previous_slot_end=None, next_slot_start=None, buffer_duration=timedelta(minutes=15)):
    """Calculate the buffer factor based on available buffer time before and after the slot."""
    buffer_factor = 0
    
    # Check if there is enough buffer time before the slot
    if previous_slot_end and (slot_start - previous_slot_end) < buffer_duration:
        buffer_factor += 0.5  # Increase risk if there is no buffer before the slot
    
    # Check if there is enough buffer time after the slot
    if next_slot_start and (next_slot_start - slot_end) < buffer_duration:
        buffer_factor += 0.5  # Increase risk if there is no buffer after the slot
    
    return buffer_factor

def calculate_risk_and_feasibility(best_slot, deadline, adhoc_skip_factor, risk_tolerance):
    """
    Calculate the risk score and feasibility score for a given time slot.
    
    Parameters:
    best_slot (tuple): The selected time slot (start, end).
    deadline (datetime): The deadline by which the meeting must be completed.
    adhoc_skip_factor (float): The likelihood of last-minute unavailability (0 to 1).
    risk_tolerance (float): The acceptable threshold for risk (0 to 1, where 1 is high risk tolerance).
    
    Returns:
    tuple: risk_score, feasibility_score
    """
    slot_start, slot_end = best_slot
    
    # Step 1: Calculate proximity factor (closer to the deadline = more risk)
    proximity_factor = calculate_proximity_factor(slot_end, deadline)
    
    # Step 2: Calculate buffer factor (check previous and next slots for buffer times)
    # For simplicity, assume we have no previous or next slots in this implementation
    buffer_factor = calculate_buffer_factor(slot_start, slot_end)
    
    # Step 3: Aggregate the risk score
    risk_score = proximity_factor + adhoc_skip_factor + buffer_factor
    
    # Step 4: Normalize risk score by risk tolerance (the higher the tolerance, the lower the risk impact)
    risk_score = risk_score / (1 + risk_tolerance)
    
    # Step 5: Calculate feasibility score (inverse of risk score)
    feasibility_score = 1 / (1 + risk_score)
    
    return risk_score, feasibility_score

def sort_by_risk(common_slots, deadline, adhoc_skip_factor, current_time=None):
    """
    Sort the common time slots by risk.
    
    Parameters:
    common_slots (list): List of (start, end) tuples representing available slots.
    deadline (datetime): The latest time by which the meeting must occur.
    adhoc_skip_factor (float): A measure of the likelihood of participants skipping (0 to 1).
    current_time (datetime): Current time (default is now).
    
    Returns:
    list: A list of time slots sorted by their risk score (lowest risk first).
    """
    if current_time is None:
        current_time = datetime.now()
    
    sorted_slots = []

    for i, (slot_start, slot_end) in enumerate(common_slots):
        # Calculate proximity factor
        proximity_factor = calculate_proximity_factor(slot_end, current_time, deadline)
        
        # Calculate buffer factor (check neighboring slots if available)
        previous_slot_end = common_slots[i - 1][1] if i > 0 else None
        next_slot_start = common_slots[i + 1][0] if i < len(common_slots) - 1 else None
        buffer_factor = calculate_buffer_factor(slot_start, slot_end, previous_slot_end, next_slot_start)
        
        # Calculate total risk score
        risk_score = proximity_factor + adhoc_skip_factor + buffer_factor

        # Append slot and its risk score to the sorted list
        sorted_slots.append((slot_start, slot_end, risk_score))
    
    # Sort slots by risk score (lower risk scores first)
    sorted_slots.sort(key=lambda x: x[2])
    
    # Return only the time slots without the risk score
    return [(slot_start, slot_end) for slot_start, slot_end, _ in sorted_slots]
