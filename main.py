from slack_client import SlackDataFetcher
from summarizer import ConversationSummarizer
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Do this on the frontend of the process
def is_substantive_summary(summary: str) -> bool:
    """Check if the summary is substantive."""
    # Define keywords or phrases that indicate a non-substantive summary
    non_substantive_phrases = [
        "only indicates that a user",
        "no further information or context",
        "does not contain a conversation",
        "only a notification that a user",
        "no substantive topics were discussed"
    ]
    
    # Check if any non-substantive phrase is in the summary
    return not any(phrase in summary for phrase in non_substantive_phrases)

def main():
    try:
        # Initialize our components
        slack_fetcher = SlackDataFetcher()
        summarizer = ConversationSummarizer()

        # Join all public channels first
        logger.info("Joining public channels...")
        slack_fetcher.join_all_public_channels()

        # Fetch all conversations from Slack
        logger.info("Fetching conversations from Slack...")
        conversations = slack_fetcher.organize_conversations()

        # First pass: Generate individual channel summaries
        channel_summaries = []
        for channel_name, messages in conversations.items():
            if not messages:
                continue
                
            formatted_conversation = summarizer._prepare_conversation(messages)
            summary = summarizer.summarize_conversation(formatted_conversation, channel_name)
            
            # Only add substantive summaries
            if is_substantive_summary(summary):
                channel_summaries.append(summary)

        # Second pass: Create ultra-concise final summary
        start_date = (datetime.now() - timedelta(days=7)).strftime("%m/%d")
        end_date = datetime.now().strftime("%m/%d")
        
        final_summary = summarizer.create_final_summary(
            channel_summaries=channel_summaries,
            start_date=start_date,
            end_date=end_date
        )
        
        # Send to Slack
        logger.info("Sending summary to Slack...")
        slack_fetcher.send_message_to_channel('slack-summarization-agent', final_summary)
        
        logger.info("Weekly summary successfully sent!")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()