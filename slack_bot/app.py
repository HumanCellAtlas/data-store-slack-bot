import json
import logging
import shlex
from urllib.parse import parse_qs

import hca
import requests

from chalice import Chalice, Response

app = Chalice(app_name='slack_bot')
app.log.setLevel(logging.DEBUG)


@app.route('/hca', methods=['GET', 'POST'], content_types=["application/x-www-form-urlencoded"])
def index():
    app.log.debug("In index")

    body = parse_qs(app.current_request.raw_body.decode())
    app.log.debug(body)

    # Every parameter comes wrapped in an array for some reason
    command_args_text = body['text'][0]
    args = shlex.split(command_args_text)
    cli = hca.cli.CLI()

    payload_text = ""

    try:
        response = cli.make_request(args)

        if isinstance(response, requests.Response):
            payload_text = json.dumps(response.json(), indent=4)
        elif isinstance(response, str):
            payload_text = response
        else:
            payload_text = json.dumps(response, indent=4)

    except Exception as e:
        app.log.debug(e)
        payload_text = e.args[0]

    payload = {'response_type': "in_channel",
               'text': payload_text}

    return Response(body=payload,
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})
