from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
import json

app = Flask(__name__)
client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

def create_next_steps_modal(next_steps):
    """Create modal view with next steps as checkboxes."""
    blocks = []
    
    # Add header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Next Steps",
            "emoji": True
        }
    })
    
    # Add checkboxes for each next step
    for i, step in enumerate(next_steps):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": step
            }
        })
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "checkboxes",
                "action_id": f"step-{i}",
                "options": [{
                    "text": {
                        "type": "mrkdwn",
                        "text": "Add to calendar"
                    },
                    "value": f"step-{i}"
                }]
            }]
        })
    
    return {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Next Steps"
        },
        "blocks": blocks
    }

@app.route('/slack/interactions', methods=['POST'])
def handle_interaction():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({'error': 'Invalid request'}), 403

    payload = json.loads(request.form.get('payload'))
    
    if payload.get('type') == 'block_actions':
        action = payload['actions'][0]
        
        # Handle main button click
        if action.get('action_id') == 'view_next_steps':
            # Read next steps from sales_summary.txt
            with open('sales_summary.txt', 'r') as f:
                content = f.read()
                next_steps = [line.strip() for line in content.split('\n') 
                            if line.strip().startswith('- ') 
                            and 'Next Steps:' in content.split(line)[0]]
            
            client.views_open(
                trigger_id=payload["trigger_id"],
                view=create_next_steps_modal(next_steps)
            )
        
        # Handle checkbox interactions
        elif action.get('type') == 'checkboxes':
            client.views_open(
                trigger_id=payload["trigger_id"],
                view={
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Confirmation"
                    },
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Sent to calendar!"
                        }
                    }]
                }
            )
    
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(port=3000)