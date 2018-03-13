# hodlmybot
Telegram bot with a wide variety of features related to crypto currency.

## Requred dependencies
python-telegram-bot, requirements, json, bs4, lxml

## Credentials
In order to actually run your bot on Telegram, you will need to have an access token, and put it in a file named `api-creds-telegramjson`:
```
{
	"token": "YOUR_ACCESS_TOKEN"
}
```

To have access to the twitter functinality you need to create `api-creds-twitter.json' in the following format
```
{
	"consumer_key": "YOUR_CONSUMER_KEY",
	"consumer_secret": "YOUR_CONSUMER_SECRET",
	"access_token": "YOUR_ACCESS_TOKEN",
	"access_token_secret": "YOUR_TOKEN_SECRET"
}
```