from io import BytesIO
from nonsense.nonsense import Nonsense, NonenseException

import celery
import os

app = celery.Celery('slack-nonsense')
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

@app.task
def upload_image(channel_id, days, message, token):
    client = slack.WebClient(token=token)
    try:
        nonsense = Nonsense()
        image = nonsense.track_days(days)
        io_stream = BytesIO()
        image.save(io_stream, "JPEG")
        io_stream.seek(0)

        response = client.files_upload(
            file=io_stream.read(),
            initial_comment=message,
            channels=channel_id
        )
        print(response)
    except NonenseException as e:
        return generate_response(str(e))