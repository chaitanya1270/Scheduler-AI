import datetime
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from app.db.models import User, CalendarEvent
from google.oauth2.credentials import Credentials
from config import settings

# Replace this with the actual scope for calendar read-only access
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

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

def fetch_and_store_calendar_events(user_email: str, db: Session):
    # Get the user's credentials
    credentials = get_user_credentials(user_email, db)
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise ValueError(f"User with email {user_email} not found.")
    
    # Call Google Calendar API to fetch events
    service = build('calendar', 'v3', credentials=credentials)
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return {"message": "No upcoming events found."}

    # Store each event in the database
    for event in events:
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        title = event.get('summary', 'No Title')
        description = event.get('description', None)
        location = event.get('location', None)

        # Store event in the database
        calendar_event = CalendarEvent(
            id=event['id'],
            user_id=user.user_id,  # You can map this to the user_id instead of email
            start_time=start_time,
            end_time=end_time,
            title=title,
            description=description,
            location=location
        )
        db.add(calendar_event)
    db.commit()

    return {"message": "Calendar events successfully stored."}
