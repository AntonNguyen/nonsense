from flask import Flask, request, jsonify
from io import BytesIO
from nonsense.nonsense import Nonsense

import os
import re
import slack

app = Flask(__name__)
app.config.from_pyfile("config.py")


@app.route('/nonsense')
def nonsense_response():
    text = request.args.get('text', '').lower().strip()
    channel_id = request.args.get('channel_id')

    days = re.compile('^(\d+)$', re.IGNORECASE)
    days_match = days.match(text)
    if days_match:
        days = days_match.group(1)
        return jsonify({
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{days} what? Cats? Dogs? This is nonsense. Resetting counter to 0 days."
                    }
                }
            ]
        })

    days_pattern = re.compile('^(\d+) days$', re.IGNORECASE)
    days_match = days_pattern.match(text)
    if days_match:
        days = days_match.group(1)
        return jsonify({
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Updating nonsense counter to {days} days."
                    }
                }
            ]
        })

    if text == "help":
        return jsonify({
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"It nonsense that you need help. Resetting nonsense counter to 0 days."
                    }
                }
            ]
        })

    return jsonify({
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"I don't quite understand what you're trying to say"
                }
            }
        ]
    })

@app.route("/")
def slack_response():
    days = 10
    nonsense = Nonsense()
    image = nonsense.track_days(days)
    io_stream = BytesIO()
    image.save(io_stream, "JPEG")
    io_stream.seek(0)

    client = slack.WebClient(token=app.config.get("SLACK_TOKEN"))

    response = client.files_upload(
        file=io_stream.read(),
        initial_comment=f'{days} days since our last nonsense',
        channels='#anandh4prez'
    )
    return jsonify({"response": "hello world!"})