import json
import logging
import os
import shlex
import urllib.parse

import hca.cli
import requests

from chalice import Chalice, Response

app = Chalice(app_name='slack_bot')
app.log.setLevel(logging.DEBUG)

DEPLOY_URL = "https://i0kzwpxck3.execute-api.us-east-1.amazonaws.com/api/"
SLACK_URL = "https://hooks.slack.com/services/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"

SUBSCRIPTIONS_HELP = """
```
usage: /hca [-h] --replica REPLICA --name NAME --query QUERY

optional arguments:
  -h, --help         show this help message and exit
  --replica REPLICA  Replica to fetch from. Can be one of aws, gcp, or azure.
  --name NAME        The name of your subscription. Only allowed characters are alpha-numeric, -, and _.
  --query QUERY      Elasticsearch query that will trigger the callback.
```
"""

def make_response(payload):
    return Response(body=payload,
                    status_code=200,
                    headers={'Content-Type': 'application/json'})

def _generate_put_subscriptions(args, channel):
    app.log.debug("Generating the put-subscriptions commands.")

    query = args[args.index("--query") + 1]
    app.log.debug(f"Given query is {query}")

    replica = args[args.index("--replica") + 1]
    app.log.debug(f"Given replica is {replica}")

    name = args[args.index("--name") + 1]
    app.log.debug(f"Name of subscription is {name}")

    callback_url = f"{DEPLOY_URL}notify/{channel}/{name}"
    app.log.debug(f"Callback_url is {callback_url}")

    return ["put-subscriptions", "--query", query, "--replica", replica, "--callback-url", callback_url]


@app.route('/hca', methods=['POST'], content_types=["application/x-www-form-urlencoded"])
def index():
    app.log.debug("In index")

    body = urllib.parse.parse_qs(app.current_request.raw_body.decode())
    app.log.debug(body)

    # Every parameter comes wrapped in an array for some reason
    command_args_text = body['text'][0]
    args = shlex.split(command_args_text)
    app.log.debug(args)

    if args[0] == 'put-subscriptions':
        try:
            args = _generate_put_subscriptions(args, body['channel_name'][0])
        except (ValueError, IndexError):
            payload = {'response_type': "in_channel",
                       'icon_emoji': ":hca:",
                       'text': SUBSCRIPTIONS_HELP}
            return make_response(payload)

    cli = hca.cli.CLI()
    payload_text = ""

    try:
        response = cli.make_request(args)

        if isinstance(response, requests.Response):
            if 'Content-Length' in response.headers and int(response.headers['Content-Length']) > 2 ** 20:
                payload_text = "Content too long to show in slack. Try using the cli or python bindings."
            else:
                payload_text = response.content.decode()
        elif isinstance(response, str):
            payload_text = response.replace("bootstrap.py", "/hca")
        else:  # response type is json
            payload_text = json.dumps(response, indent=4)
    except UnicodeDecodeError as e:
        payload_text = "Content is not utf-8 encodable"
    except Exception as e:
        app.log.debug("Exception")
        payload_text = str(e)

    app.log.debug(payload_text)
    payload = {'response_type': "in_channel",
               'icon_emoji': ":hca:",
               'text': f"```\n{payload_text}\n```"}

    return make_response(payload)


@app.route('/notify/{channel}/{notification_name}', methods=['POST'])
def notify(channel, notification_name):
    app.log.debug("In Notify")

    body = app.current_request.json_body
    app.log.debug(body)

    payload = {'username': notification_name,
               'icon_emoji': ":hca:",
               'text': "```\n{}\n```".format(json.dumps(body, indent=4)),
               'channel': channel}

    requests.post(SLACK_URL, json=payload)
    return Response(status_code=200)
