import os
import pickle
from typing import Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import logging

SCOPES = ["https://www.googleapis.com/auth/calendar"]
USERS = [
    # 'alex@rainsound.ai',
    # 'miles@rainsound.ai',
    # 'luca@rainsound.ai',
    # 'ian@rainsound.ai',
    "aubrey@rainsound.ai"
]

logger = logging.getLogger(__name__)


def create_test_event():
    """
    Creates a test event in multiple Google Calendars
    """
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    start_time = datetime.now().replace(hour=8, minute=0) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    results = []
    for user_email in USERS:
        event = {
            "summary": "Test Event from Google Calendar API",
            "description": "A test event",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/New_York",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/New_York",
            },
            "attendees": [{"email": user_email}],
        }

        try:
            created_event = (
                service.events()
                .insert(calendarId="primary", body=event, sendUpdates="all")
                .execute()
            )
            results.append(
                {
                    "email": user_email,
                    "event_id": created_event["id"],
                    "status": "success",
                }
            )
        except Exception as e:
            results.append({"email": user_email, "error": str(e), "status": "failed"})

    return results


def create_calendar_event(event: Dict):
    """
    Creates a calendar event in multiple Google Calendars at the next available time during working hours
    """

    logger.info(f"Creating calendar event with details: {event}")

    creds = None
    if os.path.exists("token.pickle"):
        logger.debug("Found existing token.pickle file")
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        logger.info("Credentials invalid or missing, attempting refresh/reauth")
        if creds and creds.expired and creds.refresh_token:
            logger.debug("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.error("No valid credentials found and unable to refresh")
            raise Exception("No valid credentials found")

    service = build("calendar", "v3", credentials=creds)
    logger.debug("Successfully built calendar service")

    # Start checking from next available working hour
    start_time = datetime.now()
    if start_time.hour >= 17:  # After work hours
        start_time = start_time.replace(hour=9, minute=0) + timedelta(days=1)
        logger.info(f"After work hours, scheduling for next day at 9am: {start_time}")
    elif start_time.hour < 9:  # Before work hours
        start_time = start_time.replace(hour=9, minute=0)
        logger.info(f"Before work hours, scheduling for 9am today: {start_time}")
    else:
        logger.info(f"During work hours, starting from current time: {start_time}")

    results = []
    for user_email in USERS:
        logger.info(f"Attempting to schedule event for user: {user_email}")
        # Find next available time slot
        found_slot = False
        current_time = start_time

        while not found_slot:
            # Check if current time is during work hours (9-5)
            if current_time.hour < 9:
                current_time = current_time.replace(hour=9, minute=0)
                logger.debug(f"Adjusted time to start of day: {current_time}")
            elif current_time.hour >= 17:
                current_time = current_time.replace(hour=9, minute=0) + timedelta(
                    days=1
                )
                logger.debug(f"Adjusted time to next day: {current_time}")

            # Check availability - Fixed FreeBusy query format
            free_busy_query = {
                "timeMin": current_time.isoformat() + "Z",  # Add Z for UTC
                "timeMax": (current_time + timedelta(hours=1)).isoformat() + "Z",
                "timeZone": "America/New_York",
                "items": [{"id": user_email}],
                "groupExpansionMax": 1,
                "calendarExpansionMax": 1,
            }
            logger.debug(f"Checking availability with query: {free_busy_query}")

            try:
                free_busy = service.freebusy().query(body=free_busy_query).execute()
                calendar_busy = free_busy["calendars"][user_email]["busy"]

                if not calendar_busy:
                    logger.info(f"Found available time slot at: {current_time}")
                    found_slot = True
                else:
                    logger.debug(f"Time slot {current_time} is busy, trying next slot")
                    current_time += timedelta(minutes=30)
            except Exception as e:
                logger.error(f"FreeBusy query failed: {str(e)}")
                # If we can't check availability, assume the slot is free
                logger.warning(
                    "Assuming time slot is available due to FreeBusy query failure"
                )
                found_slot = True

        event_details = {
            "summary": event.get("summary", "Untitled Event"),
            "description": event.get("description", ""),
            "start": {
                "dateTime": current_time.isoformat(),
                "timeZone": "America/New_York",
            },
            "end": {
                "dateTime": (current_time + timedelta(hours=1)).isoformat(),
                "timeZone": "America/New_York",
            },
            "attendees": [{"email": user_email}],
        }
        logger.debug(f"Created event details: {event_details}")

        try:
            logger.info(f"Attempting to create calendar event for {user_email}")
            created_event = (
                service.events()
                .insert(calendarId="primary", body=event_details, sendUpdates="all")
                .execute()
            )
            logger.info(f"Successfully created event with ID: {created_event['id']}")
            results.append(
                {
                    "email": user_email,
                    "event_id": created_event["id"],
                    "status": "success",
                    "scheduled_time": current_time.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to create event for {user_email}: {str(e)}")
            results.append({"email": user_email, "error": str(e), "status": "failed"})

    logger.info(f"Finished creating calendar events. Results: {results}")
    return results
