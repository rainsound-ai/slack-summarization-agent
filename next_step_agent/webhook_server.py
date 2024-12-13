from flask import Flask, request, jsonify
import logging
import os
import subprocess
import json
from dotenv import load_dotenv
import threading
from next_step_agent.tasks.task_prioritizer import TaskPrioritizer
from next_step_agent.notion.notion_client import NotionClient

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
        subprocess.run(
            ["ngrok", "http", "--hostname=whole-mastodon-top.ngrok-free.app", "5000"]
        )
    except Exception as e:
        logger.error(f"Error starting ngrok: {e}")


# Notion sends a verification request when setting up the webhook
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    try:
        webhook_data = request.json
        logger.info("Received webhook from Notion automation")

        # Get all potential/not started subprojects for Miles Porter
        # Get Miles Porter's Notion ID from users.json
        with open("users.json") as f:
            users_data = json.load(f)
            user_notion_ID = next(
                user["notion_id"]
                for user in users_data
                if user["name"] == "Miles Porter"
            )

        subprojects = notion_client.fetch_and_prioritize_user_subprojects(
            user_notion_ID
        )

        if not subprojects:
            logger.info("No eligible subprojects found for Miles Porter")
            return jsonify({"message": "No eligible subprojects found"}), 200

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

        current_task = webhook_data["data"]["id"]
        # Update the status for the subproject that was just clicked to "Done"
        # Update the status for the Next task identified for Miles Porter to "In progress"
        notion_client.update_subproject_status(next_task["id"], "In progress")
        notion_client.update_subproject_status(current_task, "Done")
        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Start ngrok in a separate thread
    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()

    # Start Flask server
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting webhook server on port {port}")
    logger.info("Webhook URL: https://whole-mastodon-top.ngrok-free.app/webhook")
    app.run(host="0.0.0.0", port=port)
