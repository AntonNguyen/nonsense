from flask import Flask, request, jsonify
from math import fabs
from nonsense import task
from random import choice

import hashlib
import hmac
import time

app = Flask(__name__)
app.config.from_pyfile("config.py")


@app.route('/nonsense', methods=['POST'])
def nonsense_response():
    if not verify_slack_request():
        print("Unauthorized access attempt")
        return jsonify({}), 403

    data = request.form
    text = data.get('text', '').lower().strip()
    team_id = data.get('team_id')
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    print(f"Request received from team '{team_id}' in channel '{channel_id}' from user '{user_id}")
    task.handle_request.delay(team_id, channel_id, user_id, text)

    return jsonify({
        "response_type": "in_channel"
    })


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
    return hmac.compare_digest(my_signature, slack_signature)
