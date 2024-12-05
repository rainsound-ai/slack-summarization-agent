import os
from dotenv import load_dotenv
import pytz
from datetime import datetime, timedelta

load_dotenv()

DEVELOPMENT = False

# API Tokens
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
