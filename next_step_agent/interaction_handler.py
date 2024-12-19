from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from next_step_agent.notion.notion_client import NotionClient
from next_step_agent.calendar.calendar_utils import create_calendar_event
import logging
import re
import json

logger = logging.getLogger(__name__)

# Initialize Slack app
slack_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
handler = SlackRequestHandler(slack_app)

# Store selected meetings in memory (consider using a database in production)
selected_meetings = {}

@slack_app.action("add_meetings")
def handle_add_meetings_button(ack, body, client):
    """Handle the button click and show search modal"""
    logger.info(f"Add meetings button clicked by user: {body['user']['id']}")
    ack()
    
    try:
        # Get the Notion link from the message text
        blocks = body.get("message", {}).get("blocks", [])
        notion_page_id = None
        
        for block in blocks:
            if block.get("type") == "section":
                text = block.get("text", {}).get("text", "")
                # Look specifically for the Link field
                link_match = re.search(r'\*Link:\* <https://(?:www\.)?notion\.so/(?:[^/]+/)?([a-f0-9]{32})', text)
                if link_match:
                    notion_page_id = link_match.group(1)
                    logger.debug(f"Found Notion page ID: {notion_page_id}")
                    break

        if not notion_page_id:
            logger.error("No valid Notion page ID found in message")
            return

        # Store the page ID in private_metadata
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "meeting_search_modal",
                "private_metadata": notion_page_id,
                "title": {"type": "plain_text", "text": "Search Meetings"},
                "submit": {"type": "plain_text", "text": "Done"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "search_block",
                        "dispatch_action": True,
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "search_input",
                            "placeholder": {"type": "plain_text", "text": "Start typing to search meetings..."},
                            "dispatch_action_config": {
                                "trigger_actions_on": ["on_character_entered"]
                            }
                        },
                        "label": {"type": "plain_text", "text": "Search"}
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error opening modal: {str(e)}")

@slack_app.action("search_input")
def handle_search(ack, body, client):
    """Handle real-time search input"""
    logger.info("Search input received")
    ack()
    
    query = body["actions"][0]["value"]
    logger.info(f"Search query: {query}")
    
    if len(query) < 3:  # Only search for 3+ characters
        logger.debug("Query too short, skipping search")
        return
    
    notion = NotionClient()
    results = notion.search_meetings(query)
    logger.info(f"Found {len(results)} results")
    
    # Update the modal with results
    try:
        result_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{result['title']}*\n{result['date']}"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Select"},
                    "value": result['id'],
                    "action_id": f"select_meeting_{result['id']}"
                }
            }
            for result in results[:5]  # Limit to 5 results
        ]
        
        if not results:
            result_blocks = [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No matching meetings found."
                }
            }]
        
        client.views_update(
            view_id=body["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "meeting_search_modal",
                "private_metadata": body["view"]["private_metadata"],  # Preserve the metadata
                "title": {"type": "plain_text", "text": "Search Meetings"},
                "submit": {"type": "plain_text", "text": "Done"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": [
                    body["view"]["blocks"][0],  # Keep the search input
                    *result_blocks
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error updating modal: {str(e)}")

@slack_app.action(re.compile("select_meeting_.*"))
def handle_meeting_selection(ack, body, client):
    """Handle when a meeting is selected from search results"""
    ack()
    
    # Extract the meeting ID from the action ID
    meeting_id = body["actions"][0]["action_id"].replace("select_meeting_", "")
    user_id = body["user"]["id"]
    
    # Initialize user's selected meetings if not exists
    if user_id not in selected_meetings:
        selected_meetings[user_id] = set()
    
    # Toggle selection
    if meeting_id in selected_meetings[user_id]:
        selected_meetings[user_id].remove(meeting_id)
        selection_status = "removed from"
    else:
        selected_meetings[user_id].add(meeting_id)
        selection_status = "added to"
    
    logger.info(f"Meeting {meeting_id} {selection_status} selection for user {user_id}")
    
    # Update the button style to show selection state
    try:
        blocks = body["view"]["blocks"]
        for block in blocks:
            if (block.get("type") == "section" and 
                block.get("accessory", {}).get("action_id") == body["actions"][0]["action_id"]):
                block["accessory"]["text"]["text"] = "Selected" if selection_status == "added to" else "Select"
                if selection_status == "added to":
                    block["accessory"]["style"] = "primary"
                else:
                    block["accessory"].pop("style", None)
        
        client.views_update(
            view_id=body["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "meeting_search_modal",
                "private_metadata": body["view"]["private_metadata"],  # Preserve the metadata
                "title": {"type": "plain_text", "text": "Search Meetings"},
                "submit": {"type": "plain_text", "text": "Done"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": blocks
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating selection: {str(e)}")

@slack_app.view("meeting_search_modal")
def handle_modal_submission(ack, body, client):
    """Handle modal submission"""
    ack()
    user_id = body["user"]["id"]
    
    try:
        # Get the selected meetings for this user
        user_selections = selected_meetings.get(user_id, set())
        if not user_selections:
            logger.info("No meetings selected")
            return
        
        # Get the page ID from private_metadata
        page_id = body["view"]["private_metadata"]
        if not page_id:
            logger.error("No page ID found in private metadata")
            return
        
        # Add selected meetings to the subproject
        notion = NotionClient()
        success = notion.add_meetings_to_subproject(page_id, list(user_selections))
        
        if success:
            # Clear selections after successful submission
            selected_meetings[user_id] = set()
            
            # Send confirmation message
            client.chat_postMessage(
                channel=user_id,
                text="✅ Selected meetings have been added to the subproject!"
            )
        else:
            client.chat_postMessage(
                channel=user_id,
                text="❌ There was an error adding meetings to the subproject."
            )
            
    except Exception as e:
        logger.error(f"Error handling modal submission: {str(e)}", exc_info=True)
        client.chat_postMessage(
            channel=user_id,
            text="❌ There was an error processing your selection."
        )

# Add Flask app setup
def create_flask_app():
    flask_app = Flask(__name__)
    
    @flask_app.route("/slack/interactions", methods=["POST"])
    def slack_events():
        """Handle all incoming Slack events"""
        return handler.handle(request)
    
    return flask_app
