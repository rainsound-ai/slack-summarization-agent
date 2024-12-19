from interaction_handler import create_flask_app
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_flask_app()

if __name__ == "__main__":
    logger.info("Starting Flask server...")
    app.run(port=5000) 