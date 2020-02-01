from flask import Flask, request, jsonify
from io import BytesIO
from nonsense.nonsense import Nonsense

import os
import slack

app = Flask(__name__)
app.config.from_pyfile("config.py")


@app.route('/nonsense', methods=['POST'])
def nonsense_response():
    print(request.json)
    return jsonify({})


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