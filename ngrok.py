import subprocess
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_ngrok():
    """Start ngrok with the configured static endpoint."""
    try:
        logger.info("Starting ngrok...")
        # Using your reserved static domain
        subprocess.run(
            ["ngrok", "http", "--hostname=whole-mastodon-top.ngrok-free.app", "5000"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ngrok command: {e}")
    except Exception as e:
        logger.error(f"Unexpected error starting ngrok: {e}")

if __name__ == "__main__":
    start_ngrok() 