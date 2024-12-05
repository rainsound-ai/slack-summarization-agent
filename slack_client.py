from datetime import datetime, timedelta
import pytz
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict
from config import SLACK_BOT_TOKEN, EST, START_DATE, END_DATE
import urllib.parse

logger = logging.getLogger(__name__)

class SlackDataFetcher:
    def __init__(self):
        self.client = WebClient(token=SLACK_BOT_TOKEN)
        self.user_map = self._get_user_info()

    def _get_user_info(self) -> Dict[str, str]:
        """Fetch and cache user ID to username mapping."""
        user_map = {}
        try:
            response = self.client.users_list()
            for user in response["members"]:
                name = user.get("profile", {}).get("display_name") or user.get("profile", {}).get("real_name", "Unknown User")
                user_map[user["id"]] = name
            return user_map
        except SlackApiError as e:
            logger.error(f"Error fetching user info: {e}")
            return {}

    def _generate_message_url(self, channel_id: str, timestamp: str) -> str:
        """Generate a direct URL to a Slack message."""
        base_url = "https://yourworkspace.slack.com/archives"
        # Replace 'yourworkspace' with your actual Slack workspace domain
        
        ts_formatted = timestamp.replace('.', '')
        message_url = f"{base_url}/{channel_id}/p{ts_formatted}"
        return message_url
    
    def organize_conversations(self) -> Dict[str, List[Dict]]:
        """Fetch and organize conversations from sales-team channel only."""
        conversations = {}
        
        try:
            result = self.client.conversations_list(
                types="public_channel",
                exclude_archived=True
            )
            
            if not result["ok"]:
                logger.error(f"Error fetching channel list: {result['error']}")
                return conversations

            channels = result.get("channels", [])
            
            # Find sales-team channel
            for channel in channels:
                if channel["name"] == "sales-team":
                    channel_id = channel["id"]
                    
                    try:
                        messages = self.get_channel_messages(channel_id)
                        if messages:
                            conversations["sales-team"] = messages
                    except SlackApiError as e:
                        logger.error(f"Error fetching messages for sales-team channel: {e}")
                    break
            
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")

        return conversations

    def get_channel_messages(self, channel_id: str) -> List[Dict]:
        """Fetch messages from a channel with proper time window."""
        messages = []
        try:
            now = datetime.now(EST)
            start_time = now - timedelta(hours=24)
            
            logger.info(f"=== Time Window ===")
            logger.info(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"End: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            start_ts = start_time.timestamp()
            end_ts = now.timestamp()
            
            response = self.client.conversations_history(
                channel=channel_id,
                oldest=str(start_ts),
                latest=str(end_ts),
                limit=1000
            )
            
            if response["ok"]:
                raw_messages = response["messages"]
                logger.info(f"Retrieved {len(raw_messages)} messages from channel")
                
                for msg in raw_messages:
                    processed_msg = self._process_message_content(msg, channel_id)
                    
                    if msg.get("thread_ts"):
                        thread_replies = self.get_thread_replies(channel_id, msg["thread_ts"], start_ts, end_ts)
                        if thread_replies:
                            processed_msg["thread_replies"] = thread_replies
                            logger.info(f"Found {len(thread_replies)} replies in thread {msg['thread_ts']}")
                    
                    messages.append(processed_msg)
            
            return messages
            
        except SlackApiError as e:
            logger.error(f"Error fetching channel messages: {e}")
            return []

    def get_thread_replies(self, channel_id: str, thread_ts: str, start_ts: float, end_ts: float) -> List[Dict]:
        """Fetch replies in a thread within the time window."""
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                oldest=str(start_ts),
                latest=str(end_ts),
                limit=1000
            )
            
            if response["ok"]:
                thread_messages = response["messages"][1:]  # Exclude parent message
                logger.info(f"Retrieved {len(thread_messages)} replies from thread {thread_ts}")
                return [self._process_message_content(msg, channel_id) for msg in thread_messages]
            
            return []
            
        except SlackApiError as e:
            logger.error(f"Error fetching thread replies: {e}")
            return []

    def _process_message_content(self, message: Dict, channel_id: str) -> Dict:
        """Process a message to extract text, files, links, and generate message URLs."""
        user_id = message.get("user", "")
        username = self.user_map.get(user_id, "Unknown User")
        timestamp = message.get("ts", "")
        message_url = self._generate_message_url(channel_id, timestamp)

        processed = {
            "text": message.get("text", ""),
            "files": message.get("files", []),
            "links": [],
            "timestamp": timestamp,
            "user": username,
            "user_id": user_id,
            "thread_ts": message.get("thread_ts", ""),
            "message_url": message_url
        }
        
        return processed

    def _generate_message_url(self, channel_id: str, timestamp: str) -> str:
        """Generate a direct URL to a Slack message."""
        base_url = "https://yourworkspace.slack.com/archives"
        # Replace 'yourworkspace' with your actual Slack workspace domain
        
        ts_formatted = timestamp.replace('.', '')
        message_url = f"{base_url}/{channel_id}/p{ts_formatted}"
        return message_url

    def send_message_to_channel(self, channel_name: str, blocks: List[Dict]) -> None:
        """Send a message to a specific channel."""
        try:
            # First, find the channel ID
            result = self.client.conversations_list(types="public_channel")
            if not result["ok"]:
                logger.error(f"Error fetching channel list: {result['error']}")
                return

            channel_id = None
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    channel_id = channel["id"]
                    break

            if not channel_id:
                logger.error(f"Channel {channel_name} not found")
                return

            response = self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text="Sales Team Summary"  # Fallback text
            )
            if not response["ok"]:
                logger.error(f"Error sending message: {response['error']}")
            
        except SlackApiError as e:
            logger.error(f"Error sending message to channel: {e}")

    def post_summary(self, channel_id: str, summary: List[Dict]) -> None:
        """Post the summary to Slack using interactive blocks."""
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                blocks=summary,
                text="Sales Team Summary" # Fallback text
            )
            if not response["ok"]:
                logger.error(f"Error posting summary: {response['error']}")
        except SlackApiError as e:
            logger.error(f"Error posting summary: {e}")

    def chunk_summary(self, summary: str, limit: int) -> List[str]:
        """Split summary into chunks of maximum size."""
        chunks = []
        current_chunk = ""
        
        for line in summary.split('\n'):
            if len(current_chunk) + len(line) + 1 <= limit:
                current_chunk += line + '\n'
            else:
                chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks