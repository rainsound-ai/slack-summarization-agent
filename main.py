from slack_client import SlackDataFetcher
from summarizer import ConversationSummarizer
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_substantive_summary(summary: str) -> bool:
    """Check if the summary is substantive."""
    # Define keywords or phrases that indicate a non-substantive summary
    non_substantive_phrases = [
        "only indicates that a user",
        "no further information or context",
        "does not contain a conversation",
        "only a notification that a user"
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

        # Process and summarize conversations
        logger.info("Summarizing conversations...")
        final_summary = []
        
        for channel_name, messages in conversations.items():
            if not messages:
                continue
                
            channel_summary = f"\n## Channel: #{channel_name}\n"
            formatted_conversation = summarizer._prepare_conversation(messages)
            summary = summarizer.summarize_conversation(formatted_conversation, channel_name)
            
            # Only add substantive summaries
            if is_substantive_summary(summary):
                final_summary.append(channel_summary + summary)

        # Combine all summaries
        complete_summary = "\n\n".join(final_summary)
        
        # Send to Slack
        logger.info("Sending summary to Slack...")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%m/%d")
        end_date = datetime.now().strftime("%m/%d")
        title = f"Weekly Slack Summary ({start_date} - {end_date})"
        
        message = f"*{title}*\n\n{complete_summary}"
        slack_fetcher.send_message_to_channel('slack-summarization-agent', message)
        
        logger.info("Weekly summary successfully sent!")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()