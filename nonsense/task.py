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
        infractioning = datetime(2020, 3, 16, 9, 00, tzinfo=tz)
        delta = infractioning - today
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
        channel=channel_id
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
        "Welcome to the Purge. For 24 hours, any nonsense has been sanctioned until midnight, when the Purge concludes. Blessed be the great Leafy and FreshBooksj, a company reborn. May nonsense be with you all.",
        "Support our Troups and be nonsensical.",
        "The nonsense-counter has overfl0wed. It's now a free-for-all.",
        "Brave souls who are WFO - please take this opporunity to waste a precious resource of toilet paper to cover Troup's desk in celebration of the nonsense-purge",
        "I guess the Leafs don't have any need for a playoff beard.",
        "The titantic amd the Leafs both look good - until they hit the ice.",
        "After a detailed analysis, I have concluded that Troup's age is increasing linearly.",
        "Don't forget to have a ball today. https://freshbooks.slack.com/files/U02M4M44K/FFLCAFXFT/20120426090404-64cabef9-me.jpg",
        "Please practise social isolation: https://freshbooks.slack.com/files/U02M4M44K/FFNGKUEJV/dee.jpg",
        "I don't have a witty message. I just wanted to share this picture of young @Anandh Sridharan: https://freshbooks.slack.com/files/U02M4M44K/FFP1ST0HZ/dsc04185.jpg",
        "Here is some nonsense inspiration: https://freshbooks.slack.com/files/U02M4M44K/FFQHKMBPG/troup.png",
        "Ok boomer",
        "Why, you stuck up, half-witted, scruffy-looking… Nerf herder!",
        "By the time you've rhymed one line, I've already busted ten; You rap in exponential time and I'm big-O of log(n)",
        "Your code runs so slow your data brings sleeping bags to camp-out in the cache lines.",
        "I never believed in chaos theory until I saw your variable naming convention!",
        "Your code is so bad your child processes disowned you.",
        "By popular demand, your code backup is in /dev/null/",
        "Your code is so bad, Richard Stallman suggested that you keep it proprietary.",
        "Your code looks as though you have been playing bingo with anti-patterns.",
        "More unit tests? No! What your code needs is petrol and a match.",
        "I would ask you your age, but I don't want my stack to overflow",
        "And now, a word from our sponsor for @troup: https://v.cameo.com/1WTlnO7hU4",
    ]

    return choice(messages).format(days=days)


def unknown_command_message(command):
    return "Welcome to the Purge. For 24 hours, any nonsense has been sanctioned until midnight, when the Purge concludes. Blessed be the great Leafy and FreshBooksj, a company reborn. May nonsense be with you all."


def report_message():
    return "Welcome to the Purge. For 24 hours, any nonsense has been sanctioned until midnight, when the Purge concludes. Blessed be the great Leafy and FreshBooksj, a company reborn. May nonsense be with you all."
