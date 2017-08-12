import json
import logging
from urllib.parse import parse_qs

import hca
from chalice import Chalice, Response

app = Chalice(app_name='slack_bot')
app.log.setLevel(logging.DEBUG)


@app.route('/hca', methods=['GET', 'POST'], content_types=["application/x-www-form-urlencoded"])
def index():
    app.log.debug("IN index")

    body = parse_qs(app.current_request.raw_body.decode())
    app.log.debug(body)

    # Every parameter comes wrapped in an array for some reason
    text = body['text'][0]
    args = text.split()
    cli = hca.cli.CLI()
    response = cli.make_request(args)

    formatted_json = json.dumps(response.json(), indent=4)

    payload = {'response_type': "in_channel",
               'text': formatted_json}
    return Response(body=payload,
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})
