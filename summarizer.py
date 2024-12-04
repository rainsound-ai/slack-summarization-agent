from openai import OpenAI
from typing import List, Dict
import logging
from config import OPENAI_API_KEY, MAX_CHUNK_SIZE, EST
from prompt import get_sales_summary_prompt
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class ConversationSummarizer:
    def __init__(self):
        self.model = "o1-preview"

    def _clean_text(self, text: str) -> str:
        """Remove user tags like <@U12345> from the text."""
        # Remove user tags
        text = re.sub(r'<@U[A-Z0-9]+>', '', text)
        # Remove channel tags like <#C12345>
        text = re.sub(r'<#C[A-Z0-9]+>', '', text)
        # Remove special tokens like <!here>, <!channel>
        text = re.sub(r'<![a-zA-Z]+>', '', text)
        return text.strip()

    def _prepare_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for the AI model."""
        formatted_msgs = []
        for msg in messages:
            user = msg.get("user", "Unknown User")
            text = msg.get("text", "")
            timestamp = msg.get("timestamp", "")
            thread_replies = msg.get("thread_replies", [])
            files = msg.get("files", [])
            links = msg.get("links", [])

            # Clean the text to remove user tags
            text = self._clean_text(text)

            # Convert timestamp to datetime string
            if timestamp:
                timestamp_dt = datetime.fromtimestamp(float(timestamp), EST)
                timestamp_str = timestamp_dt.strftime("%m/%d/%Y %H:%M")
            else:
                timestamp_str = "Unknown Time"

            # Format main message
            if text:
                formatted_msgs.append(f"[{timestamp_str}] **{user}**: {text}")

            # Include shared files
            for file in files:
                if isinstance(file, dict):
                    file_name = file.get('name', 'Unnamed file')
                    file_url = file.get('url_private', 'No URL')
                    formatted_msgs.append(f"[File shared] {file_name} - [Link]({file_url})")

            # Include shared links
            for link in links:
                if isinstance(link, dict):
                    link_url = link.get('url', 'No URL')
                    formatted_msgs.append(f"[Link shared] {link_url}")

            # Format thread replies
            if thread_replies:
                formatted_msgs.append("[Thread started]")
                for reply in thread_replies:
                    reply_user = reply.get("user", "Unknown User")
                    reply_text = reply.get("text", "")
                    reply_timestamp = reply.get("timestamp", "")

                    # Clean the reply text
                    reply_text = self._clean_text(reply_text)

                    # Convert reply timestamp to datetime string
                    if reply_timestamp:
                        reply_timestamp_dt = datetime.fromtimestamp(float(reply_timestamp), EST)
                        reply_timestamp_str = reply_timestamp_dt.strftime("%m/%d/%Y %H:%M")
                    else:
                        reply_timestamp_str = "Unknown Time"

                    if reply_text:
                        formatted_msgs.append(f"    [{reply_timestamp_str}] **{reply_user}** (reply): {reply_text}")
                formatted_msgs.append("[End of thread]")
        
        return "\n\n".join(formatted_msgs)

    def summarize_conversation(self, conversation: str, start_date: str, end_date: str) -> str:
        """Summarize the conversation using the OpenAI model."""
        try:
            prompt = get_sales_summary_prompt(conversation, start_date, end_date)
            # Replace with your OpenAI API call
            response = client.chat.completions.create(
                model=self.model,
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