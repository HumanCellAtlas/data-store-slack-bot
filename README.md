# data-store-slack-bot
Simple Slack bot to query the data store and subscribe to notifications coming from the data store.

## Deploying slack_bot chalice project

1. Re-download `dss-slack-bot` service account key file.
2. Save service account key file to `data-store-slack-bot/slack_bot/chalicelib/google-service-account-credentials.json`
3. navigate to `slack_bot` directory and run `chalice deploy`
