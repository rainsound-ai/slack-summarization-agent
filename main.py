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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def daily_updates(target_slack_channel: str, summary_channel: str):
    """This DMs the channel summary, the highest priority subproject, and generates a calendar event for the user once a day"""
    slack_fetcher = SlackDataFetcher()

    daily_update_summary = summarize_slack_channel(summary_channel)
    if daily_update_summary:
        formatted_blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": daily_update_summary},
            }
        ]
        slack_fetcher.send_message_to_channel(target_slack_channel, formatted_blocks)

        # Get the highest priority subproject
        highest_priority_subproject = get_highest_priority_subproject()
        if highest_priority_subproject:
            formatted_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Highest priority subproject: {highest_priority_subproject['title']}\nStep: {highest_priority_subproject['step']}\nProject: {highest_priority_subproject['parent_project']}",
                    },
                }
            ]
            slack_fetcher.send_message_to_channel(
                target_slack_channel, formatted_blocks
            )

        # Generate a calendar event for the user
        generate_calendar_event(highest_priority_subproject)
    pass


def test_daily_updates():
    daily_updates("bot-spam-channel", "sales-team")


def triggered_updates():
    """This DMs the channel summary, the highest priority subproject, and generates a calendar event for the user when the complete button is pushed"""
    pass


def generate_calendar_event(subproject: Dict):
    """This creates a calendar event with the highest priority subproject for the user"""
    event_data = {
        "summary": subproject["title"],
        "description": f"Step: {subproject['step']}\nProject: {subproject['parent_project']}",
    }
    logger.info(f"Creating calendar event: {event_data}")
    create_calendar_event(event_data)


def send_slack_message():
    pass


def get_highest_priority_subproject():
    notion_client = NotionClient()
    user_notion_ID = get_user_notion_id("Miles Porter")
    subprojects = notion_client.fetch_user_subprojects(user_notion_ID)
    task_prioritizer = TaskPrioritizer()
    next_task = task_prioritizer.prioritize_tasks(subprojects)
    return next_task
    pass


def get_user_notion_id(name: str):
    with open("next_step_agent/data/users.json") as f:
        users_data = json.load(f)
        user_id = None
        for user in users_data["users"]:  # Access the "users" array
            if user.get("name") == "Miles Porter":
                user_id = user.get("notion_id")
                break
    return user_id


def summarize_slack_channel(channel_name):
    try:
        # Initialize components
        slack_fetcher = SlackDataFetcher()
        summarizer = ConversationSummarizer(slack_fetcher.user_map)

        # Get messages from the sales-team channel
        logger.info(f"Fetching {channel_name} conversations...")

        conversations = slack_fetcher.fetch_conversations(channel_name)

        if channel_name not in conversations:
            logger.error(f"{channel_name} channel not found or no messages available")
            return None, None

        # Format conversation for both file and AI
        formatted_conversation = summarizer._prepare_conversation(
            conversations[channel_name]
        )

        # Save formatted conversation to file (overwrite mode)
        logger.info(f"Saving formatted messages to slack_messages_{channel_name}...")
        with open(
            f"outputs/slack_messages_{channel_name}.txt", "w", encoding="utf-8"
        ) as f:
            f.write("\n=== Channel: sales-team ===\n\n")
            f.write(formatted_conversation)

        # Get current date range
        start_date = (datetime.now() - timedelta(hours=24)).strftime("%m/%d %H:%M")
        end_date = datetime.now().strftime("%m/%d %H:%M")

        # Summarize using the same formatted conversation
        logger.info("Summarizing conversation...")
        channel_summary = summarizer.summarize_conversation(
            formatted_conversation, start_date, end_date
        )

        # Format the summary as Slack blocks
        formatted_blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": channel_summary}}
        ]

        logger.info("Sending sales summary to Slack...")
        if config.SEND_TO_TEST_CHANNEL:
            if config.SLACK_TEST_CHANNEL:
                slack_fetcher.send_message_to_channel(
                    config.SLACK_TEST_CHANNEL, formatted_blocks
                )
                logger.info(f"Summary: {channel_summary}")
                logger.info(f"Sales summary sent to {config.SLACK_TEST_CHANNEL}")
            else:
                logger.error("Test channel not set in config.py")
        else:
            slack_fetcher.send_message_to_channel(
                "slack-summarization-agent", formatted_blocks
            )
            logger.info("Sales team summary successfully sent!")

        return channel_summary

    except Exception as e:
        logger.error(f"Error parsing sales summary file: {e}")
        return None, None


def get_tasks_from_channel_summary(channel_name):
    messages = []
    try:
        slack_fetcher = SlackDataFetcher()
        summarizer = ConversationSummarizer(slack_fetcher.user_map)

        channel_summary = summarize_slack_channel(channel_name)

        # Add type check before passing to format_for_slack
        if isinstance(channel_summary, tuple) or channel_summary is None:
            logger.error("No valid channel summary found")
            return messages

        formatted_summary = summarizer.format_for_slack(channel_summary)
        logger.info(f"Formatted summary: {formatted_summary}")
        if not formatted_summary:
            logger.error("No channel summary found")
            return messages

        # Parse the formatted_summary if it's a string
        if isinstance(formatted_summary, str):
            formatted_summary = json.loads(formatted_summary)

        # Extract tasks from the checkboxes in the formatted summary
        for block in formatted_summary:
            if block.get("type") == "actions":
                for element in block.get("elements", []):
                    if element.get("type") == "checkboxes":
                        for option in element.get("options", []):
                            text = option.get("text", {}).get("text", "")
                            # Extract task and assignee using regex
                            match = re.search(r"(.*?)\(Assigned to: @([^,]+)", text)
                            if match:
                                task = match.group(1).strip()
                                assignee = match.group(2).strip()
                                messages.append({"user": assignee, "text": task})

        logger.info(f"Extracted tasks: {messages}")
        return messages
    except Exception as e:
        logger.error(f"Error parsing sales summary file: {e}")
        return []


def map_and_create_subprojects(channel_name):
    try:
        # Initialize components
        task_mapper = TaskMapper()
        notion_client = NotionClient()

        # Read messages from sales_summary.txt
        messages = get_tasks_from_channel_summary(channel_name)
        if not messages:
            logger.error("No messages found in the channel summary")
            return

        # Extract tasks from messages
        logger.info("Extracting tasks from messages...")
        tasks = task_mapper.extract_tasks(messages)

        # Map tasks to processes
        logger.info("Mapping tasks to processes...")
        mapped_tasks = task_mapper.map_tasks_to_processes(tasks)

        # Create subprojects in Notion
        logger.info("Creating subprojects in Notion...")
        results = notion_client.create_subprojects(mapped_tasks)

        # Pretty print the results
        logger.info("\n=== Results ===")
        pprint(results, indent=2, width=100)

        # Save results to file
        output_file = "mapped_tasks.json"
        logger.info(f"\nSaving results to {output_file}...")
        with open(f"outputs/{output_file}", "w") as f:
            json.dump(results, f, indent=2)

        logger.info("Process completed successfully!")
    except Exception as e:
        logger.error(f"Error in map_and_create_subprojects: {e}")
        raise


def main():
    try:
        map_and_create_subprojects("sales-team")
        test_daily_updates()

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise


if __name__ == "__main__":
    if "--create-test-event" in sys.argv:
        logger.info("Creating test event...")
        try:
            event_id = create_test_event()
            print(f"Successfully created event with ID: {event_id}")
        except Exception as e:
            print(f"Error creating event: {str(e)}")
    else:
        logger.info("Running main process...")
        main()
