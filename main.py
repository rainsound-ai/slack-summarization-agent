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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_sales_summary(file_path="sales_summary.txt"):
    """Parse the sales summary file into a list of message dictionaries."""
    messages = []
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract tasks from the "Next Steps:" section
        next_steps_pattern = r"- (.*?) \(Assigned to: @(.*?),.*?\)"
        matches = re.findall(next_steps_pattern, content)

        for task, assignees in matches:
            # Handle multiple assignees
            assignee_list = [name.strip() for name in assignees.split("and")]
            for assignee in assignee_list:
                messages.append({"user": assignee, "text": task})

        return messages
    except Exception as e:
        logger.error(f"Error parsing sales summary file: {e}")
        return []


def main():
    try:
        # Initialize components
        slack_fetcher = SlackDataFetcher()
        task_mapper = TaskMapper()
        notion_client = NotionClient()

        # Read messages from sales_summary.txt
        messages = parse_sales_summary()
        if not messages:
            logger.error("No messages found in sales summary file")
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
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info("Process completed successfully!")

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
