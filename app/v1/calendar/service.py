from sqlalchemy.orm import Session
from app.db.models import CalendarEvent
from datetime import datetime

# Function to store event data in the database
def store_event_data(db: Session, event_data: dict, user_id: str):
    # Extract event details from the event_data
    event_id = event_data.get('id')
    start_time = event_data.get('start_time')
    end_time = event_data.get('end_time')
    title = event_data.get('summary', 'No Title')
    description = event_data.get('description', '')
    location = event_data.get('location', '')

    # Create a new CalendarEvent object
    new_event = CalendarEvent(
        id=event_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        title=title,
        description=description,
        location=location
    )

    # Add and commit the new event to the database
    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while storing event data: {e}")

    return new_event
