import os
from dotenv import load_dotenv
import pytz
from datetime import datetime, timedelta

load_dotenv()

# API Tokens
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_STEPS_DATABASE_ID = os.getenv("NOTION_STEPS_DATABASE_ID")
NOTION_PROCESS_DATABASE_ID = os.getenv("NOTION_PROCESS_DATABASE_ID")
NOTION_SOP_DATABASE_ID = os.getenv("NOTION_SOP_DATABASE_ID")
NOTION_SUBPROJECTS_DATABASE_ID = os.getenv("NOTION_SUBPROJECTS_DATABASE_ID")
NOTION_PROJECTS_DATABASE_ID = os.getenv("NOTION_PROJECTS_DATABASE_ID")

# Time configurations with explicit timezone
EST = pytz.timezone("America/New_York")
CURRENT_DATE = datetime.now(EST)
HOURS_DELTA = 24
START_DATE = (CURRENT_DATE - timedelta(hours=HOURS_DELTA)).replace(
    minute=0, second=0, microsecond=0
)
END_DATE = CURRENT_DATE.replace(microsecond=999999)

# Formatting
MAX_CHUNK_SIZE = 3999

# Channel configurations
EXCLUDE_ARCHIVED = True
DEBUG_LOGGING = True
SEND_TO_TEST_CHANNEL = True
SLACK_TEST_CHANNEL = "bot-spam-channel"
