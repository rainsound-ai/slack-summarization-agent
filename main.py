from slack_client import SlackDataFetcher
from task_mapper import TaskMapper
import logging
from datetime import datetime, timedelta
import json
from pprint import pprint
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_sales_summary(file_path='sales_summary.txt'):
    """Parse the sales summary file into a list of message dictionaries."""
    messages = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract tasks from the "Next Steps:" section
        next_steps_pattern = r'- (.*?) \(Assigned to: @(.*?),.*?\)'
        matches = re.findall(next_steps_pattern, content)
        
        for task, assignees in matches:
            # Handle multiple assignees
            assignee_list = [name.strip() for name in assignees.split('and')]
            for assignee in assignee_list:
                messages.append({
                    "user": assignee,
                    "text": task
                })
                
        return messages
    except Exception as e:
        logger.error(f"Error parsing sales summary file: {e}")
        return []

def main():
    try:
        # Initialize components
        slack_fetcher = SlackDataFetcher()
        task_mapper = TaskMapper()

        # Read messages from sales_summary.txt instead of using sample data
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

        # Pretty print the results
        logger.info("\n=== Mapped Tasks ===")
        pprint(mapped_tasks, indent=2, width=100)

        # Save mapped tasks to file (keeping this for reference)
        output_file = "mapped_tasks.json"
        logger.info(f"\nSaving mapped tasks to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(mapped_tasks, f, indent=2)

        logger.info("Task mapping completed successfully!")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()