from datetime import datetime, timedelta, timezone
import requests
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from app.db.models import User, CalendarEvent
from google.oauth2.credentials import Credentials
from config import settings

# Replace this with the actual scope for calendar read-only access
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
def create_google_calendar_event(user: User, event_details: dict):
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {user.oauth_token}",
        "Content-Type": "application/json"
    }
    event_data = {
        "summary": event_details['title'],
        "description": event_details['description'],
        "start": {
            "dateTime": event_details['start_time'].isoformat(),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": event_details['end_time'].isoformat(),
            "timeZone": "UTC"
        },
        "attendees": [{"email": email} for email in event_details['participants']],
        "reminders": {
            "useDefault": True
        }
    }
    response = requests.post(url, headers=headers, json=event_data)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Failed to create event: {response.text}")

def get_user_credentials(user_email: str, db: Session):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise ValueError(f"User with email {user_email} not found.")

    # Set credentials for the Google Calendar API
    creds = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_CALENDAR_SCOPES,
    )
    return creds

def fetch_and_store_calendar_events(user: User, time_min: datetime, time_max: datetime, db: Session):
    # Get the user's credentials
    user_email = user.email
    credentials = get_user_credentials(user_email, db)
    print(time_min)
    print(time_max)
    # Call Google Calendar API to fetch events
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min.isoformat() + 'Z',  # Time window start
        timeMax=time_max.isoformat() + 'Z',  # Time window end
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    if not events:
        return []

    # Store each event in the database
    for event in events:
        # Extract start and end times
        start_time_str = event['start'].get('dateTime', event['start'].get('date'))
        end_time_str = event['end'].get('dateTime', event['end'].get('date'))

        # Convert strings to datetime objects
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

        # Subtract 5 hours and 30 minutes from the times
        time_difference = timedelta(hours=5, minutes=30)
        adjusted_slot_start = start_time - time_difference
        adjusted_slot_end = end_time - time_difference

        # Ensure the times are in UTC
        utc_slot_start = adjusted_slot_start.replace(tzinfo=timezone.utc).isoformat()
        utc_slot_end = adjusted_slot_end.replace(tzinfo=timezone.utc).isoformat()

        # Store event in the database
    #     calendar_event = CalendarEvent(
    #         id=event['id'],
    #         user_id=user.user_id,
    #         start_time=utc_slot_start,
    #         end_time=utc_slot_end,
    #         title=event.get('summary', 'No Title'),
    #         description=event.get('description', None),
    #         location=event.get('location', None)
    #     )
    #     db.add(calendar_event)

    # db.commit()

    events_list = [(event['start'].get('dateTime', event['start'].get('date')), 
                    event['end'].get('dateTime', event['end'].get('date'))) for event in events]
    
    return events_list




# def fetch_google_calendar_events(user: User, time_min: datetime.datetime, time_max: datetime.datetime, db: Session):
#     # Fetch and store calendar events from Google Calendar
#     fetch_and_store_calendar_events(user.email, db)

#     url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
#     headers = {
#         "Authorization": f"Bearer {user.oauth_token}"
#     }
#     params = {
#         "timeMin": time_min.isoformat() + "Z",
#         "timeMax": time_max.isoformat() + "Z",
#         "singleEvents": True,
#         "orderBy": "startTime"
#     }
#     response = requests.get(url, headers=headers, params=params)
#     events = response.json().get('items', [])
#     print('response')
#     print(response)
#     events_list=[(event['start'].get('dateTime', event['start'].get('date')),event['end'].get('dateTime', event['end'].get('date'))) for event in events]
#     return events_list