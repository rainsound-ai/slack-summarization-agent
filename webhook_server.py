from flask import Flask, request, jsonify
import logging
import os
import subprocess
from dotenv import load_dotenv
import threading

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_ngrok():
    """Start ngrok in a separate thread with the configured static endpoint."""
    try:
        # Using your reserved static domain
        subprocess.run([
            "ngrok", 
            "http", 
            "--hostname=whole-mastodon-top.ngrok-free.app", 
            "5000"
        ])
    except Exception as e:
        logger.error(f"Error starting ngrok: {e}")

# Notion sends a verification request when setting up the webhook
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        logger.info("Received webhook from Notion automation")
        
        # Log the full payload for debugging
        logger.info(f"Webhook payload: {data}")
        
        # Extract properties from the webhook payload
        properties = data.get('properties', {})
        
        if properties:
            subproject = properties.get('Sub-project', {}).get('title', [{}])[0].get('text', {}).get('content', 'Unknown')
            button_clicker = properties.get('Button Clicker', {}).get('people', [])
            blocked_by = properties.get('Blocked by', {}).get('relation', [])
            blocking = properties.get('Blocking', {}).get('relation', [])
            
            logger.info(f"""
            Button clicked for:
            - Subproject: {subproject}
            - Clicked by: {button_clicker}
            - Blocked by: {len(blocked_by)} items
            - Blocking: {len(blocking)} items
            """)
            
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start ngrok in a separate thread
    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()
    
    # Start Flask server
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting webhook server on port {port}")
    logger.info("Webhook URL: https://whole-mastodon-top.ngrok-free.app/webhook")
    app.run(host='0.0.0.0', port=port) 