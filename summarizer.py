import openai
from typing import List, Dict
import logging
from config import OPENAI_API_KEY, MAX_CHUNK_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY

class ConversationSummarizer:
    def __init__(self):
        self.model = "gpt-4-1106-preview"

    def _prepare_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for the AI model."""
        formatted_msgs = []
        for msg in messages:
            text = msg.get("text", "")
            thread_replies = msg.get("thread_replies", [])
            
            if text:
                formatted_msgs.append(f"Message: {text}")
            
            for reply in thread_replies:
                reply_text = reply.get("text", "")
                if reply_text:
                    formatted_msgs.append(f"Reply: {reply_text}")
            
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
            client = openai.OpenAI()
            prompt = f"""
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

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional business analyst creating concise summaries of Slack conversations."},
                    {"role": "user", "content": prompt}
               ]
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return f"Error summarizing conversation: {str(e)}"

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