from io import BytesIO
from nonsense.nonsense import Nonsense, NonenseException

import celery
import os
import slack

app = celery.Celery(__name__)
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

SLACK_TOKEN = os.getenv("SLACK_TOKEN")

@app.task
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