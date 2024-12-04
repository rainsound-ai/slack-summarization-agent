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
        # Initialize components
        slack_fetcher = SlackDataFetcher()
        summarizer = ConversationSummarizer()

        # Get messages only from sales-team channel
        logger.info("Fetching sales team conversations...")
        conversations = slack_fetcher.organize_conversations()
        
        if 'sales-team' not in conversations:
            logger.error("Sales-team channel not found or no messages available")
            return
            
        # Process sales-team messages
        formatted_conversation = summarizer._prepare_conversation(conversations['sales-team'])
        channel_summary = summarizer.summarize_conversation(formatted_conversation, 'sales-team')
        
        if is_substantive_summary(channel_summary):
            # Create final summary
            start_date = (datetime.now() - timedelta(days=7)).strftime("%m/%d")
            end_date = datetime.now().strftime("%m/%d")
            
            final_summary = summarizer.create_final_summary(
                channel_summaries=[channel_summary],
                start_date=start_date,
                end_date=end_date
            )
            
            # Send to Slack
            logger.info("Sending sales summary to Slack...")
            slack_fetcher.send_message_to_channel('slack-summarization-agent', final_summary)
            logger.info("Sales team summary successfully sent!")
        else:
            logger.info("No substantive sales updates found this week")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()