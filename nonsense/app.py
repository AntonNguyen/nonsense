from flask import Flask, request, jsonify
from io import BytesIO
from nonsense.nonsense import Nonsense

import hmac
import os
import re
import slack

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
        return generate_response(f"{days} what? Cats? Dogs? This is nonsense. Resetting counter to 0 days.")

    days_pattern = re.compile('^(\d+) days$', re.IGNORECASE)
    days_match = days_pattern.match(text)
    if days_match:
        days = days_match.group(1)
        return generate_response(f"Updating nonsense counter to {days} days.")

    if text == "help":
        return generate_response("It nonsense that you need help. Resetting nonsense counter to 0 days.")

    return generate_response("I don't quite understand what you're trying to say")


def verify_slack_request():
    slack_signing_secret = app.config.get("SLACK_SIGNING_SECRET")
    request_body = request.get_data().decode("utf-8")
    timestamp = request.headers['X-Slack-Request-Timestamp']

    if absolute_value(time.time() - timestamp) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    sig_basestring = f"v0:{timestamp}:{request_body}"
    my_signature = 'v0=' + hmac.compute_hash_sha256(
        slack_signing_secret,
        sig_basestring
    ).hexdigest()

    slack_signature = request.headers['X-Slack-Signature']
    if not hmac.compare(my_signature, slack_signature):
        return False
    return True


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