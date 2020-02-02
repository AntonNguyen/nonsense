from datetime import datetime
from io import BytesIO
from nonsense.nonsense import Nonsense, NonenseException
from pytz import timezone
from random import choice

import celery
import os
import redis
import slack

app = celery.Celery(__name__)
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

redisClient = redis.from_url(os.getenv('REDIS_URL'), db=1)

SLACK_TOKEN = os.getenv("SLACK_TOKEN")


@app.task
def handle_request(team_id, channel_id, user_id, text):
    print(f"Task received from team '{team_id}' in channel '{channel_id}' from user '{user_id}")
    last_infraction = get_current_record(team_id)

    if text == "status":
        tz = timezone('EST')
        today = datetime.now(tz)
        delta = today - last_infraction
        upload_image(channel_id, delta.days)
        post_message(channel_id, status_message(delta.days))
        return

    if text == "report infraction":
        report_infraction(team_id, last_infraction)
        post_message(channel_id, report_message())
        return

    report_infraction(team_id, last_infraction)
    post_message(channel_id, unknown_command_message(text))


def report_infraction(team_id, last_infraction):
    tz = timezone('EST')
    today = datetime.now(tz)
    if today.date() == last_infraction.date():
        return

    redisClient.set(team_id, today.isoformat())


def upload_image(channel_id, days):
    client = slack.WebClient(token=SLACK_TOKEN)
    try:
        nonsense = Nonsense()
        image = nonsense.track_days(days)
        io_stream = BytesIO()
        image.save(io_stream, "JPEG")
        io_stream.seek(0)

        response = client.files_upload(
            file=io_stream.read(),
            channels=channel_id
        )
        print(response)
    except NonenseException as e:
        return generate_response(str(e))


def post_message(channel_id, text):
    client = slack.WebClient(token=SLACK_TOKEN)
    response = client.chat_postMessage(
        text=text,
        channels=channel_id
    )
    print(response)


def get_current_record(team_id):
    if not redisClient.exists(team_id):
        tz = timezone('EST')
        today = datetime.now(tz)

        redisClient.set(team_id, today.isoformat())
        return today
    current_record = redisClient.get(team_id)
    return datetime.fromisoformat(current_record.decode('utf-8'))


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