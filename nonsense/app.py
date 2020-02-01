from datetime import datetime
from flask import Flask, request, jsonify
from math import fabs
from nonsense import task
from pytz import timezone
from random import choice


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
    print(f"Request received from team '{team_id}' in channel '{channel_id}'")

    last_infraction = get_current_record(team_id)

    if text == "status":
        tz = timezone('EST')
        today = datetime.now(tz)
        delta = today - last_infraction
        task.upload_image.delay(channel_id, delta.days)
        return generate_response(status_message(delta.days))

    if text == "report infraction":
        report_infraction(team_id, last_infraction)
        return generate_response(report_message())

    report_infraction(team_id, last_infraction)
    return generate_response(unknown_command_message(text))


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


def status_message(days):
    messages = [
        "This office has been nonsense-free for {days} days",
        "The office is on a nonsense-free streak of {days} days!",
        "Only {days} days. This is ridiculous",
        "Fun fact: Ecobee is on a nonsense-free streak of 368 days. This office is only on {days} days",
        "{days} days. Let’s not get crazy and ruin our no-nonsense streak, all right? So, for instance, if you’re expecting a fax today, please don’t yell out, \"Michael J. Fax from Fax to the Future.\" Ok? That’s nonsense.",
    ]

    return choice(messages).format(days=days)


def unknown_command_message(command):
    messages = [
        "'{command}' is not in the supported-commands file. This incident will be reported.",
        "Exception in thread \"main\" java.lang.NoClassDefFoundError: {command}",
        "NameError: name '{command}' is not defined",
        "errors.New(\"{command} not found\")",
        "Ahhhhhh! This command doesn't exist!",
        "Some of the co-ops forgot to handle the '{command}' command. Thanks Anurag.",
        "I couldn't find the '{command}' command. Here's a pleasant song to listen to while I search: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Your '{command}' command ain't here, kid.",
        "This is not the command you're looking for.",
        "Yeaaah what's happening? We went ahead and stopped supporting the '{command}' command, so if you could just go ahead and use the nonsense bot correctly, that would be great.",
        "Failed to run the '{command}' command. '{command}' is not supported on this bot."
    ]
    return choice(messages).format(command=command)


def report_message():
    messages = [
        "Thank you for keeping tnis a no-nonsense office.",
        "Good call. Together we run a no-nonsense office.",
        "That’s obviously nonsense. Nonsense. And what percentage of nonsense do we tolerate in this office? Right. Zero. No nonsense. You can't have nonsense.",
        "Thank you for stamping out this enormous source of overlooked PFN.",
        "A+ reporting!",
        "Well played, old chap!",
        "GG."
    ]
    return choice(messages)


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


