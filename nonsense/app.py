from datetime import datetime
from flask import Flask, request, jsonify
from math import fabs
from nonsense import task
from pytz import timezone


import hashlib
import hmac
import os
import re
import redis
import time

app = Flask(__name__)
app.config.from_pyfile("config.py")
redisClient = redis.from_url(os.getenv('REDIS_URL'), db=1)


@app.route('/nonsense', methods=['POST'])
def nonsense_response():
    if not verify_slack_request():
        return jsonify({}), 403

    data = request.form
    text = data.get('text', '').lower().strip()
    team_id = data.get('team_id')
    channel_id = data.get('channel_id')

    last_infraction = get_current_record(team_id)

    if text == "status":
        tz = timezone('EST')
        today = datetime.now(tz)
        delta = today - last_infraction
        task.upload_image.delay(channel_id, delta.days)

        return generate_response(f"This office has been nonsense-free for {delta.days} days")

    if text == "report infraction":
        report_infraction(team_id, last_infraction)
        return generate_response("Thank you for keeping tnis a no-nonsense office.")

    report_infraction(team_id, last_infraction)
    return generate_response(f"{text.capitalize()} is not in the supported-commands file. This incident will be reported.")


def get_current_record(team_id):
    if not redisClient.exists(team_id):
        tz = timezone('EST')
        today = datetime.now(tz)

        redisClient.set(team_id, today.isoformat())
        return today
    current_record = redisClient.get(team_id)
    return datetime.fromisoformat(current_record.decode('utf-8'))


def report_infraction(team_id, last_infraction):
    tz = timezone('EST')
    today = datetime.now(tz)
    if today.date() == last_infraction.date():
        return

    redisClient.set(team_id, today.isoformat())


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


