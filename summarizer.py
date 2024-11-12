from openai import OpenAI
from typing import List, Dict
import logging
from config import OPENAI_API_KEY, MAX_CHUNK_SIZE
from prompt import get_channel_prompt, get_final_summary_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class ConversationSummarizer:
    def __init__(self):
        self.model = "o1-preview"

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
            prompt = get_channel_prompt(channel_name, conversation)
            response = client.chat.completions.create(
                model="o1-mini",
                messages=[{"role": "user", "content": prompt}]
            )

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
        summary = summary.replace("__", "_")  # Convert italic markdown to Slack italic
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

    def create_final_summary(self, channel_summaries: List[str], start_date: str, end_date: str) -> str:
        """Create an ultra-concise final summary from all channel summaries."""
        try:
            all_summaries = "\n\n".join(channel_summaries)
            prompt = get_final_summary_prompt(all_summaries, start_date, end_date)
            
            response = client.chat.completions.create(
                model="o1-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.choices[0].message.content.strip()
            formatted_summary = self.format_for_slack(summary)
            return formatted_summary
        except Exception as e:
            logger.error(f"Error in final summarization: {e}")
            return f"Error creating final summary: {str(e)}"