from slack_client import SlackDataFetcher
from summarizer import ConversationSummarizer
from notion_fetcher import NotionDataFetcher
import logging
from datetime import datetime, timedelta
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        # Initialize components
        slack_fetcher = SlackDataFetcher()
        summarizer = ConversationSummarizer(slack_fetcher.user_map)

        # Get messages from the sales-team channel
        logger.info("Fetching sales team conversations...")
        conversations = slack_fetcher.organize_conversations()

        if "sales-team" not in conversations:
            logger.error("Sales-team channel not found or no messages available")
            return

        # Format conversation for both file and AI
        formatted_conversation = summarizer._prepare_conversation(
            conversations["sales-team"]
        )

        # Save formatted conversation to file (overwrite mode)
        filename = "outputs/slack_messages.txt"

        logger.info(f"Saving formatted messages to {filename}...")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n=== Channel: sales-team ===\n\n")
            f.write(formatted_conversation)

        # Get current date range
        start_date = (datetime.now() - timedelta(hours=24)).strftime("%m/%d %H:%M")
        end_date = datetime.now().strftime("%m/%d %H:%M")

        # Initialize NotionDataFetcher
        notion_fetcher = NotionDataFetcher()

        # Fetch steps from Notion
        logger.info("Fetching steps from Notion...")
        notion_steps = notion_fetcher.fetch_step_data()

        # Summarize using the same formatted conversation
        logger.info("Summarizing conversation...")
        channel_summary = summarizer.summarize_conversation(
            formatted_conversation, start_date, end_date
        )

        logger.info("Linking next steps to notion steps...")
        linked_steps = summarizer.link_next_steps_to_notion_steps(
            channel_summary, notion_steps
        )

        # Save original summary and linked steps for comparison
        logger.info("Saving original summary and linked steps before modifications...")
        with open("outputs/sales_summary_original.txt", "w", encoding="utf-8") as f:
            f.write(channel_summary)
        with open("outputs/linked_steps.txt", "w", encoding="utf-8") as f:
            f.write(linked_steps)

        # Replace the Next Steps section in channel_summary with linked_steps
        logger.info("Replacing Next Steps section with linked steps...")
        sections = channel_summary.split("\n\n")
        for i, section in enumerate(sections):
            if section.startswith("*Next Steps:*") or section.startswith("Next Steps:"):
                sections[i] = linked_steps
                break
        channel_summary = "\n\n".join(sections)

        # Write to file if in development mode, otherwise send to Slack
        if config.DEVELOPMENT:
            logger.info("Development mode: Writing sales summary to file...")
            with open("outputs/sales_summary.txt", "w", encoding="utf-8") as f:
                f.write(channel_summary)
            logger.info("Sales summary written to outputs/sales_summary.txt")
            slack_fetcher.send_message_to_channel(
                config.SLACK_TEST_CHANNEL, channel_summary
            )
            logger.info(f"Sales summary sent to {config.SLACK_TEST_CHANNEL}")
        else:
            logger.info("Sending sales summary to Slack...")
            slack_fetcher.send_message_to_channel(
                "slack-summarization-agent", channel_summary
            )
            logger.info("Sales team summary successfully sent!")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise


if __name__ == "__main__":
    main()
