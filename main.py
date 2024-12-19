from typing import Dict
from next_step_agent.slack.slack_client import SlackDataFetcher
from next_step_agent.tasks.task_mapper import TaskMapper
from next_step_agent.notion.notion_client import NotionClient
import logging
from datetime import datetime, timedelta
import json
from pprint import pprint
import re
from next_step_agent.calendar.calendar_utils import create_test_event
import sys
from next_step_agent.summarizer import ConversationSummarizer
import config
from next_step_agent.tasks.task_prioritizer import TaskPrioritizer
from next_step_agent.calendar.calendar_utils import create_calendar_event
from next_step_agent.interaction_handler import create_flask_app
import threading
import subprocess
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_flask_server():
    """Start the Flask server for handling Slack interactions"""
    app = create_flask_app()
    logger.info("Starting Flask server on port 5000...")
    app.run(port=5000)

def get_highest_priority_subproject():
    """Get the highest priority subproject from Notion"""
    try:
        notion_client = NotionClient()
        
        # Get Miles Porter's Notion ID from users.json
        with open("next_step_agent/data/users.json") as f:
            users_data = json.load(f)
            user_id = None
            for user in users_data["users"]:
                if user.get("name") == "Miles Porter":
                    user_id = user.get("notion_id")
                    break

        if not user_id:
            logger.error("Could not find Miles Porter's Notion ID")
            return None

        # Get all potential/not started subprojects for Miles Porter
        subprojects = notion_client.fetch_user_subprojects(user_id)
        if not subprojects:
            logger.info("No eligible subprojects found for Miles Porter")
            return None

        # Prioritize tasks
        task_prioritizer = TaskPrioritizer()
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
            return next_task
        else:
            logger.info("No next task identified - all tasks are blocked")
            return None

    except Exception as e:
        logger.error(f"Error getting highest priority subproject: {e}")
        return None

def triggered_updates(target_slack_channel: str):
    """This DMs the highest priority subproject, and generates a calendar event for the user when the complete button is pushed"""
    slack_fetcher = SlackDataFetcher()
    # Get the highest priority subproject
    highest_priority_subproject = get_highest_priority_subproject()
    if highest_priority_subproject:
        # Create calendar event first - pass the entire subproject info
        calendar_event = create_calendar_event({
            'title': highest_priority_subproject['title'],
            'description': highest_priority_subproject['description'],
            'deadline': highest_priority_subproject['deadline']
        })
        
        # Get the calendar event URL from the result
        calendar_link = calendar_event[0]['event_url'] if calendar_event and calendar_event[0].get('event_url') else None
        
        highest_priority_subproject_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Highest priority subproject:* {highest_priority_subproject['title']}\n\n"
                        f"*Step:* {highest_priority_subproject['step']}\n"
                        f"*Project:* {highest_priority_subproject['parent_project']}\n"
                        f"*Description:*\n{highest_priority_subproject['description']}\n\n"
                        f"*How it forwards milestones:*\n{highest_priority_subproject['milestones']}\n\n"
                        f"*Deadline:*\n{highest_priority_subproject['deadline']}\n\n"
                        f"*Link:* {highest_priority_subproject['self_link']}\n\n"
                        + (f"*Calendar Event:* {calendar_link}\n\n" if calendar_link else "")
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Add Meetings",
                            "emoji": True
                        },
                        "action_id": "add_meetings"
                    }
                ]
            }
        ]
        slack_fetcher.send_message_to_channel(
            target_slack_channel, highest_priority_subproject_blocks
        )

def main():
    """Run the application"""
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    logger.info("Started Flask server thread")

    # Run your main bot logic
    try:
        while True:
            triggered_updates(config.SLACK_TEST_CHANNEL)
            time.sleep(300)  # Run every 5 minutes or adjust as needed
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
