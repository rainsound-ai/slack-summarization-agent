from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import logging
from typing import List, Dict, Any
from config import SLACK_BOT_TOKEN, START_DATE, END_DATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackDataFetcher:
    def __init__(self):
        self.client = WebClient(token=SLACK_BOT_TOKEN)
        
    def get_all_channels(self) -> List[Dict]:
        """Fetch all public channels."""
        try:
            channels = []
            cursor = None
            while True:
                response = self.client.conversations_list(
                    types="public_channel",
                    cursor=cursor
                )
                channels.extend(response["channels"])
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            return channels
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")
            return []

    def _process_message_content(self, message: Dict) -> Dict:
        """Process a message to extract text, files, and links."""
        processed = {
            "text": message.get("text", ""),
            "files": [],
            "links": [],
            "timestamp": message.get("ts", ""),
            "user": message.get("user", "")
        }

        # Process files
        if "files" in message:
            for file in message["files"]:
                file_info = {
                    "name": file.get("name", "Unnamed file"),
                    "type": file.get("filetype", ""),
                    "title": file.get("title", ""),
                    "url": file.get("url_private", ""),
                }
                processed["files"].append(file_info)

        # Process links from message text
        if message.get("blocks"):
            for block in message["blocks"]:
                if block["type"] == "rich_text":
                    for element in block.get("elements", []):
                        for item in element.get("elements", []):
                            if item["type"] == "link":
                                link_info = {
                                    "url": item.get("url", ""),
                                    "text": item.get("text", "")
                                }
                                processed["links"].append(link_info)

        return processed

    def get_channel_messages(self, channel_id: str) -> List[Dict]:
        """Fetch messages from a channel within the date range."""
        try:
            messages = []
            cursor = None
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=START_DATE.timestamp(),
                    latest=END_DATE.timestamp(),
                    cursor=cursor
                )
                
                channel_messages = response["messages"]
                for msg in channel_messages:
                    processed_msg = self._process_message_content(msg)
                    
                    # Fetch thread replies if they exist
                    if msg.get("thread_ts"):
                        thread_replies = self.get_thread_replies(channel_id, msg["thread_ts"])
                        processed_msg["thread_replies"] = [
                            self._process_message_content(reply) 
                            for reply in thread_replies
                        ]
                    
                    messages.append(processed_msg)
                
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            
            return messages
        except SlackApiError as e:
            logger.error(f"Error fetching messages for channel {channel_id}: {e}")
            return []

    def get_thread_replies(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """Fetch replies in a thread."""
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                oldest=START_DATE.timestamp(),
                latest=END_DATE.timestamp()
            )
            return response["messages"][1:]  # Exclude the parent message
        except SlackApiError as e:
            logger.error(f"Error fetching thread replies: {e}")
            return []

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
                        logger.error(f"Error fetching messages for sales-team channel: {e.response['error']}")
                    break
                
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e.response['error']}")

        return conversations

    def join_all_public_channels(self):
        """Join all public channels that the bot isn't already a member of and aren't archived."""
        try:
            # Get list of all public channels
            result = self.client.conversations_list(
                types="public_channel",
                exclude_archived=True  # Skip archived channels
            )
            
            if not result["ok"]:
                logger.error(f"Error fetching channel list: {result['error']}")
                return

            channels = result.get("channels", [])
            
            for channel in channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                
                # Skip if bot is already a member
                if channel.get("is_member", False):
                    logger.debug(f"Already a member of #{channel_name}, skipping...")
                    continue
                    
                try:
                    logger.info(f"Joining channel #{channel_name}...")
                    self.client.conversations_join(channel=channel_id)
                except SlackApiError as e:
                    logger.error(f"Error joining channel #{channel_name}: {e.response['error']}")
                    
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e.response['error']}")

    def send_message_to_channel(self, channel_name: str, message: str):
        """Send a message to a specific channel."""
        try:
            response = self.client.chat_postMessage(
                channel=channel_name,
                text=message,
                parse='mrkdwn'
            )
            logger.info(f"Message sent successfully to #{channel_name}")
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message to channel: {e}")
            raise