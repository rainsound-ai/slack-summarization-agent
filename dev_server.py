from pyngrok import ngrok
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_dev_environment():
    # Start ngrok tunnel
    http_tunnel = ngrok.connect(3000)
    public_url = http_tunnel.public_url
    logger.info(f"Public URL: {public_url}/slack/interactions")
    
    # Start Flask server
    subprocess.run(["python", "interaction_handler.py"])

if __name__ == "__main__":
    start_dev_environment()