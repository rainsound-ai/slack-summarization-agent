from flask import Flask, request, jsonify
import logging
import os
import subprocess
from dotenv import load_dotenv
import threading
from task_prioritizer import TaskPrioritizer
from notion_client import NotionClient

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notion_client = NotionClient()
task_prioritizer = TaskPrioritizer()

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
        webhook_data = request.json
        logger.info("Received webhook from Notion automation")
        
        # Get all potential/not started subprojects for Miles Porter
        subprojects = notion_client.get_user_subprojects()  # Uses default "Miles Porter"
        
        if not subprojects:
            logger.info("No eligible subprojects found for Miles Porter")
            return jsonify({'message': 'No eligible subprojects found'}), 200
        
        # Prioritize tasks
        next_task = task_prioritizer.prioritize_tasks(subprojects)
        
        if next_task:
            logger.info(f"""
            Next task identified for Miles Porter:
            - Title: {next_task['title']}
            - Score: {next_task['score']}
            - Impact: {next_task['impact']}
            - Urgency: {next_task['urgency']}
            - Importance: {next_task['importance']}
            - Blocking: {len(next_task['blocking'])} tasks
            - Blocked by: {len(next_task['blocked_by'])} tasks
            """)
        else:
            logger.info("No next task identified - all tasks are blocked")
            
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