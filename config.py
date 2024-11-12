import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# API Tokens
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Time configurations
WEEK_DELTA = 7
CURRENT_DATE = datetime.now()
START_DATE = (CURRENT_DATE - timedelta(days=WEEK_DELTA)).replace(hour=0, minute=0, second=0, microsecond=0)
END_DATE = CURRENT_DATE.replace(hour=23, minute=59, second=59, microsecond=999999)

# Formatting
MAX_CHUNK_SIZE = 2000

# Channel configurations
EXCLUDE_ARCHIVED = True
DEBUG_LOGGING = False  # Set to True if you want to see the debug logs