from openai import OpenAI
from typing import List, Dict
import logging
from config import OPENAI_API_KEY, MAX_CHUNK_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class ConversationSummarizer:
    def __init__(self):
        self.model = "o1-mini"

    def _prepare_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for the AI model."""
        formatted_msgs = []
        for msg in messages:
            user = msg.get("user", "Unknown User")
            text = msg.get("text", "")
            thread_replies = msg.get("thread_replies", [])
            
            if text:
                formatted_msgs.append(f"{user}: {text}")
            
            for reply in thread_replies:
                reply_user = reply.get("user", "Unknown User")
                reply_text = reply.get("text", "")
                if reply_text:
                    formatted_msgs.append(f"{reply_user} (reply): {reply_text}")
            
            for file in msg.get("files", []):
                formatted_msgs.append(
                    f"File shared: {file['name']} ({file['type']}) - {file['url']}"
                )
            
            for link in msg.get("links", []):
                formatted_msgs.append(
                    f"Link shared: {link['text']} - {link['url']}"
                )
            
        return "\n".join(formatted_msgs)

    def summarize_conversation(self, conversation: str, channel_name: str) -> str:
        """Summarize a single conversation."""
        try:
            prompt = f"""
            You are a professional business analyst creating concise summaries of Slack conversations.
            Analyze this Slack conversation from the channel #{channel_name} and provide a concise summary.
            Include:
            1. Main topic(s) discussed
            2. Key decisions made (if any)
            3. Action items (if any)
            4. Important quotes (if relevant)
            5. Relevant files and links shared (include the URLs if they seem important)
            
            Keep the summary brief and focused on the most important points.
            If files or links were shared, include them only if they're relevant to the main discussion.
            
            Conversation:
            {conversation}
            """

            # Use the new API interface
            response = client.chat.completions.create(
                model="o1-mini",  # Use the correct model name
                messages=[{"role": "user", "content": prompt}]
            )

            # Format the response for Slack
            summary = response.choices[0].message.content.strip()
            formatted_summary = self.format_for_slack(summary)
            return formatted_summary
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return f"Error summarizing conversation: {str(e)}"

    def format_for_slack(self, summary: str) -> str:
        """Format the summary for better readability in Slack."""
        # Replace markdown with Slack-friendly formatting
        summary = summary.replace("**", "*")  # Convert bold markdown to Slack bold
        summary = summary.replace("__", "_")  # Convert italic markdown to Slack italics
        # Add more formatting adjustments as needed
        return summary

    def chunk_summary(self, summary: str) -> List[str]:
        """Split summary into chunks of maximum size."""
        chunks = []
        current_chunk = ""
        
        for paragraph in summary.split('\n'):
            if len(current_chunk) + len(paragraph) + 1 <= MAX_CHUNK_SIZE:
                current_chunk += (paragraph + '\n')
            else:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks 