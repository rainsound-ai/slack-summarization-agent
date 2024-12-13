from openai import OpenAI
from typing import List, Dict
import logging
from config import OPENAI_API_KEY, MAX_CHUNK_SIZE, EST
from next_step_agent.openai.prompt import get_sales_summary_prompt
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


class ConversationSummarizer:
    def __init__(self, user_map: Dict[str, str]):
        self.model = "gpt-4o"
        self.user_map = user_map

    def _clean_text(self, text: str) -> str:
        """Clean text while preserving @mentions."""
        # Replace <@U12345> format with just the @ mention
        text = re.sub(r"<@(U[A-Z0-9]+)>", r"@\1", text)

        # Remove channel tags
        text = re.sub(r"<#C[A-Z0-9]+\|([^>]+)>", r"#\1", text)

        # Remove special tokens
        text = re.sub(r"<![a-zA-Z]+>", "", text)

        # Replace user IDs with usernames using the user_map
        for user_id in re.findall(r"@(U[A-Z0-9]+)", text):
            if user_id in self.user_map:
                text = text.replace(f"@{user_id}", f"@{self.user_map[user_id]}")

        return text.strip()

    def _prepare_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for the AI model."""
        formatted_msgs = []
        for msg in messages:
            user = msg.get("user", "Unknown User")
            text = self._clean_text(msg.get("text", ""))
            timestamp = msg.get("timestamp", "")
            timestamp_dt = datetime.fromtimestamp(float(timestamp), EST)
            timestamp_str = timestamp_dt.strftime("%m/%d/%Y %H:%M")
            message_url = msg.get("message_url", "")
            thread_replies = msg.get("thread_replies", [])
            files = msg.get("files", [])
            links = msg.get("links", [])

            # Format main message
            if text:
                formatted_msg = f"[{timestamp_str}] **{user}**: {text}"
                if message_url:
                    formatted_msg += f" [Message URL]: {message_url}"
                formatted_msgs.append(formatted_msg)

            # Include shared files
            for file in files:
                if isinstance(file, dict):
                    file_name = file.get("name", "Unnamed file")
                    file_url = file.get("url_private", "No URL")
                    formatted_msgs.append(
                        f"[File shared] {file_name} - [Link]({file_url})"
                    )

            # Include shared links
            for link in links:
                if isinstance(link, dict):
                    link_url = link.get("url", "No URL")
                    formatted_msgs.append(f"[Link shared] {link_url}")

            # Format thread replies
            if thread_replies:
                formatted_msgs.append("[Thread started]")
                for reply in thread_replies:
                    reply_user = reply.get("user", "Unknown User")
                    reply_text = self._clean_text(reply.get("text", ""))
                    reply_timestamp = reply.get("timestamp", "")
                    reply_timestamp_dt = datetime.fromtimestamp(
                        float(reply_timestamp), EST
                    )
                    reply_timestamp_str = reply_timestamp_dt.strftime("%m/%d/%Y %H:%M")
                    reply_message_url = reply.get("message_url", "")

                    if reply_text:
                        formatted_reply = f"    [{reply_timestamp_str}] **{reply_user}** (reply): {reply_text}"
                        if reply_message_url:
                            formatted_reply += f" [Message URL]: {reply_message_url}"
                        formatted_msgs.append(formatted_reply)
                formatted_msgs.append("[End of thread]")

        return "\n\n".join(formatted_msgs)

    def summarize_conversation(
        self, conversation: str, start_date: str, end_date: str
    ) -> str:
        """Read pre-generated summary from file instead of calling OpenAI."""
        try:
            # Comment out to save 🤑💰💰 on OpenAI calls
            prompt = get_sales_summary_prompt(conversation, start_date, end_date)
            response = client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            logger.info(f"OpenAI response: {response}")
            summary = response.choices[0].message.content.strip()
            logger.info(f"Summary: {summary}")

            # Uncomment to save 🤑💰💰 on OpenAI calls
            # Instead, read from file
            # with open('sales_summary.txt', 'r', encoding='utf-8') as f:
            #     summary = f.read().strip()

            return summary

        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return f"Error summarizing conversation: {str(e)}"

    def format_for_slack(self, summary: str) -> List[Dict]:
        """Format the summary as interactive Slack blocks with next steps only."""
        sections = summary.split("\n")
        blocks = []
        next_steps = []

        def create_header(text: str) -> Dict:
            return {
                "type": "header",
                "text": {"type": "plain_text", "text": text, "emoji": True},
            }

        def truncate_text(text: str, max_length: int = 150) -> str:
            """Truncate text to fit within Slack's limits."""
            if len(text) <= max_length:
                return text
            return text[: max_length - 3] + "..."

        def create_checkbox_items(items: List[str]) -> List[Dict]:
            """Create checkbox items, splitting into multiple blocks if needed."""
            checkbox_blocks = []
            current_items = []

            for i, item in enumerate(items):
                truncated_text = truncate_text(item)
                current_items.append(
                    {
                        "type": "checkboxes",
                        "action_id": f"action-{i}",
                        "options": [
                            {
                                "text": {"type": "mrkdwn", "text": truncated_text},
                                "value": f"value-{i}",
                            }
                        ],
                    }
                )

                if len(current_items) == 5 or len(item) > 150:
                    checkbox_blocks.append(
                        {"type": "actions", "elements": current_items}
                    )
                    current_items = []

            if current_items:
                checkbox_blocks.append({"type": "actions", "elements": current_items})

            return checkbox_blocks

        # Add Next Steps header
        blocks.append(create_header("Next Steps"))

        # Find and process next steps
        in_next_steps = False
        for line in sections:
            line = line.strip()
            if not line:
                continue

            if "Next Steps:" in line:
                in_next_steps = True
            elif in_next_steps and (line.startswith("-") or line.startswith("•")):
                next_steps.append(line[1:].strip())

        # Add checkboxes for next steps
        if next_steps:
            blocks.extend(create_checkbox_items(next_steps))

        return blocks

    def chunk_summary(self, summary: str) -> List[str]:
        """Split summary into chunks of maximum size."""
        chunks = []
        current_chunk = ""

        for paragraph in summary.split("\n"):
            if len(current_chunk) + len(paragraph) + 1 <= MAX_CHUNK_SIZE:
                current_chunk += paragraph + "\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks