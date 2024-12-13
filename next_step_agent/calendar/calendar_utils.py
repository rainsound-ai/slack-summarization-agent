import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
USERS = [
    # 'alex@rainsound.ai',
    # 'miles@rainsound.ai',
    # 'luca@rainsound.ai',
    # 'ian@rainsound.ai',
    'aubrey@rainsound.ai'
]

def create_test_event():
    """
    Creates a test event in multiple Google Calendars
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    start_time = datetime.now().replace(hour=8, minute=0) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    results = []
    for user_email in USERS:
        event = {
            'summary': 'Test Event from Google Calendar API',
            'description': 'A test event',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': user_email}
            ]
        }

        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            results.append({
                'email': user_email,
                'event_id': created_event['id'],
                'status': 'success'
            })
        except Exception as e:
            results.append({
                'email': user_email,
                'error': str(e),
                'status': 'failed'
            })

    return results