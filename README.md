# HODLMyBot
Bot with a wide variety of features related to crypto currency.

## Supported platforms
This bot currently works with Slack (`hodlmybot-slack.py`) and Telegram (`hodlmybot-telegram.py`).

## Commands
```
This bot currently supports the following commands:
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

## Required dependencies
To install required dependencies, run `pip install -r requirements.txt`. Running the bot in a venv is recommended (see Installation)

## Installation
This installation procedure assumes a Debian based system, but should work fine on other distros as well.
It was developed and tested on Ubuntu 17.10.

1. Create and copy the contens of the tarball to `/opt/hodlmybot`.
1. Run the bootstrip script:
    ```
    $ ./bootstrap.sh
    ```
   Say yes to both installing cron jobs and service.
1. Set your access token (see **Credentials**)
1. Reboot or start the service manually:
    ```
    $ sudo systemctl start hodlmybot
    $ sudo systemctl status hodlmybot

## Credentials
In order to actually run your bot on Telegram, you will need to have an access token, and put it in `api-creds-telegram.json`:
```
{
	"access_token": "YOUR_ACCESS_TOKEN"
}
```

To have access to the twitter functionality you need to create `api-creds-twitter.json`:
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

### CoinMarketCap
Use `cron-cmc.py` to import the latest data from Coinmarketcap, which becomes the historical data used for token metrics. You must run this at least once.

### Twitter
Use `cron-twitter.py` to gather historical followers metrics from the tracked twitter accounts. You must run this at least once. There is a default set of accounts that will be tracked, and to update these based on the currently top ranked tokens, run `cron-twitter-update.py`.

### Reddit
Use `cron-reddit.py` to gather historical subscribers metrics from the tracked Reddit subreddits. You must run this at least once. There is a default set of subreddits that will be tracked, and to update these based on the currently top ranked tokens, run `cron-reddit-update.py`.
