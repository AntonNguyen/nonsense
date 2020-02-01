from flask import Flask, request, jsonify
from io import BytesIO
from nonsense.nonsense import Nonsense
from math import fabs

import hashlib
import hmac
import os
import re
import slack
import time

app = Flask(__name__)
app.config.from_pyfile("config.py")


@app.route('/nonsense', methods=['POST'])
def nonsense_response():
    if not verify_slack_request():
        return jsonify({}), 403

    data = request.form
    text = data.get('text', '').lower().strip()
    channel_id = data.get('channel_id')
    print(data, text, channel_id)

    days = re.compile('^(\d+)$', re.IGNORECASE)
    days_match = days.match(text)
    if days_match:
        days = days_match.group(1)
        return upload_image(channel_id, 0, f"{days} what? Cats? Dogs? This is nonsense. Resetting counter to 0 days.")

    days_pattern = re.compile('^(\d+) days$', re.IGNORECASE)
    days_match = days_pattern.match(text)
    if days_match:
        days = days_match.group(1)
        return upload_image(channel_id, days, f"Updating nonsense counter to {days} days.")

    if text == "help":
        return upload_image(channel_id, 0, "Have you not been paying attention? Resetting nonsense counter to 0 days.")

    return generate_response("I don't quite understand what you're trying to say")


def verify_slack_request():
    slack_signing_secret = bytes(app.config.get("SLACK_SIGNING_SECRET"), 'utf-8')
    timestamp = request.headers['X-Slack-Request-Timestamp']

    if fabs(time.time() - float(timestamp)) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    sig_basestring = bytes('v0:' + str(timestamp) + ':', 'utf-8') + request.get_data()
    my_signature = 'v0=' + hmac.new(
        slack_signing_secret,
        sig_basestring,
        hashlib.sha256
    ).hexdigest()

    slack_signature = request.headers['X-Slack-Signature']
    print(my_signature, slack_signature)
    return hmac.compare_digest(my_signature, slack_signature)


def generate_response(text):
    return jsonify({
        "response_type": "in_channel",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        ]
    })

def upload_image(channel_id, days, message):
    nonsense = Nonsense()
    image = nonsense.track_days(days)
    io_stream = BytesIO()
    image.save(io_stream, "JPEG")
    io_stream.seek(0)

    client = slack.WebClient(token=app.config.get("SLACK_TOKEN"))

    response = client.files_upload(
        file=io_stream.read(),
        initial_comment=message,
        channels=channel_id
    )
    return jsonify({})