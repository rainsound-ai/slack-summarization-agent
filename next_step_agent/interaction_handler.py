from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
import json

app = Flask(__name__)
client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)


@app.route("/slack/interactions", methods=["POST"])
def handle_interaction():
    # Verify the request is from Slack
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({"error": "Invalid request"}), 403

    # Parse the interaction payload
    payload = json.loads(request.form.get("payload"))

    # Handle checkbox interactions
    if payload.get("type") == "block_actions":
        for action in payload["actions"]:
            if action["type"] == "checkboxes":
                # Open a modal when checkbox is clicked
                client.views_open(
                    trigger_id=payload["trigger_id"],
                    view={
                        "type": "modal",
                        "title": {"type": "plain_text", "text": "Hello World!"},
                        "blocks": [
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": "Hello World!"},
                            }
                        ],
                    },
                )

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=3000)
