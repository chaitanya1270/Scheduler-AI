import requests


def create_microsoft_calendar_event(user, event_details):
    url = "https://graph.microsoft.com/v1.0/me/events"
    headers = {
        "Authorization": f"Bearer {user.oauth_token['access_token']}",
        "Content-Type": "application/json"
    }
    event_data = {
        "subject": event_details['title'],
        "body": {
            "contentType": "HTML",
            "content": event_details['description']
        },
        "start": {
            "dateTime": event_details['start_time'].isoformat(),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": event_details['end_time'].isoformat(),
            "timeZone": "UTC"
        },
        "attendees": [
            {"emailAddress": {"address": email}, "type": "required"} 
            for email in event_details['participants']
        ],
        "allowNewTimeProposals": True
    }
    response = requests.post(url, headers=headers, json=event_data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create event: {response.text}")



# Function to fetch availability from Microsoft 365 Calendar (Outlook)
def fetch_microsoft_calendar_events(user, time_min, time_max):
    url = f"https://graph.microsoft.com/v1.0/me/calendarview"
    headers = {
        "Authorization": f"Bearer {user.oauth_token['access_token']}",
        "Prefer": 'outlook.timezone="UTC"'
    }
    params = {
        "startDateTime": time_min.isoformat() + "Z",
        "endDateTime": time_max.isoformat() + "Z",
    }
    response = requests.get(url, headers=headers, params=params)
    events = response.json().get('value', [])
    return [(event['start']['dateTime'], event['end']['dateTime']) for event in events]
