# hodlmybot
Telegram bot with a wide variety of features related to crypto currency.

## Commands
```
This bot currently supports the following commands:
    Help:
    /help - This help

    Tools:
    /search - Search for coin
    /webpage <coin> - Link to coin webpage
    /mcap - Total market cap
    /usd <coin> - USD value of <coin>
    /stats [<coin>] - Global core metrics or metrics of <coin>
    /ico <coin> - Get ICO info
    /convert <amount> <from coin> <to coin> - Coin conversion
    /compare <coin1> <coin2> - Compare two coins

    Watchers:
    /marketwatch [<threshold (%)> <interval (sec)>]|stop - Set threshold and interval for market watcher or stop
    /moonwatch [<threshold (%)> <interval (sec)>]|stop - Set threshold and interval for mooning coins

    Intel:
    /airdrops - List of upcoming airdrops
    /reddit [add|del <subreddit> or list] - Add or list Reddit followers
    /twitter [add|del <user> or list] - Add or list Twitter followers

    Fun:
    /hodl - Helps you decide whether or not to HODL
    /fomo - When you have FOMO
    /fud - No FUD
    /carlos - CARLOS MATOS!
    /rackle - The Crazy Racklehahn
    /shouldi - Helps you decide
    /diceroll - Throw 1d6
```

## Requred dependencies
python-telegram-bot, requirements, json, bs4, lxml

## Credentials
In order to actually run your bot on Telegram, you will need to have an access token, and put it in `api-creds-telegram.json`:
```
{
	"token": "YOUR_ACCESS_TOKEN"
}
```

To have access to the twitter functinality you need to create `api-creds-twitter.json`:
```
{
	"consumer_key": "YOUR_CONSUMER_KEY",
	"consumer_secret": "YOUR_CONSUMER_SECRET",
	"access_token": "YOUR_ACCESS_TOKEN",
	"access_token_secret": "YOUR_TOKEN_SECRET"
}
```

## Updating historical data
The bot works best if it can continuously poll the latest data from several sources, and import them into the database in the form of historical data. For this purpose there are a few scripts can be added to `cron`.

### Coinmarketcap
Use `cron-cmc.py` to import the lastest data from Coinmarketcap, which becomes the historical data used for token metrics. You must run this at least once.

### Twitter
Use `cron-twitter.py` to gather historical followers metrics from the tracked twitter accounts. You must run this at least once. There is a default set of accounts that will be tracked, and to update these based on the currently top ranked tokens, run `cron-twitter-update.py`.

### Reddit
Use `cron-reddit.py` to gather historical subscribers metrics from the tracked Reddit subreddits. You must run this at least once. There is a default set of subreddits that will be tracked, and to update these based on the currently top ranked tokens, run `cron-reddit-update.py`.