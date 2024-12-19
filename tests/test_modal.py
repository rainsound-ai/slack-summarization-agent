import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_modal_flow():
    # 1. Simulate button click
    button_payload = {
        "type": "block_actions",
        "trigger_id": "test_trigger",
        "user": {"id": "test_user"},
        "actions": [{
            "action_id": "add_meetings",
            "block_id": "actions_block",
            "type": "button"
        }]
    }
    
    response = requests.post(
        "http://localhost:5000/slack/interactions",
        json=button_payload,
        headers={
            "Content-Type": "application/json"
        }
    )
    print("Button click response:", response.status_code)
    
    # 2. Simulate search input
    search_payload = {
        "type": "block_actions",
        "view": {
            "id": "test_view",
            "blocks": [{"block_id": "search_block"}]
        },
        "actions": [{
            "action_id": "search_input",
            "value": "test search",
            "type": "plain_text_input"
        }]
    }
    
    response = requests.post(
        "http://localhost:5000/slack/interactions",
        json=search_payload,
        headers={
            "Content-Type": "application/json"
        }
    )
    print("Search response:", response.status_code)

if __name__ == "__main__":
    test_modal_flow() 