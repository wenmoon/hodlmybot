# HODLMyBot
Bot with a wide variety of features related to crypto currency.

## Supported platforms
This bot currently works with Slack (`hodlmybot-slack.py`), Telegram (`hodlmybot-telegram.py`) and Dischord (`hodlmybot-dischord.py`).

## Commands
```
This bot currently supports the following commands:
    /about - A little bit about myself
    /find <query> - Search for a token
    /f <query> - Search for a token
    /search <query> - Search for a token
    /stats [<token>] - Global metrics, or metrics of <token>
    /s [<token>] - Global metrics, or metrics of <token>
    /logo <token> - Show token logo
    /l <token> - Show token logo
    /usd <token> - Convert <token> to USD
    /u <token> - Convert <token> to USD
    /convert <amount> <from> <to> - Convert between tokens
    /conv <amount> <from> <to> - Convert between tokens
    /compare <token1> <token2> - Compare two tokens
    /comp <token1> <token2> - Compare two tokens
    /mcap - Show a breakdown of total mcap
    /m - Show a breakdown of total mcap
    /topmcap - List top 20 mcap tokens
    /tm - List top 20 mcap tokens
    /ico <token> - Get ICO info
    /web <token> - Link to token webpage
    /w <token> - Link to token webpage
    /airdrop - List of upcoming airdrops
    /twitter - [add|del <user>] - Add or list followers
    /reddit - [add|del <subreddit>] - Add or list subscribers
    /hodl - When you need to hear that voice of reason
    /fomo - When you have that FOMO
    /fud - When you suffer from FUD
    /carlos - Bitconnneeeeeeeeeect!
    /rackle - The Crazy Racklehahn
    /yn - For moments of unvertainty
    /diceroll - Throw 1d6
    /dice - Throw 1d6
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
    $ sudo systemctl start hodlmybot-slack
    $ sudo systemctl start hodlmybot-telegram
    $ sudo systemctl status hodlmybot-slack
    $ sudo systemctl status hodlmybot-telegram
    $ sudo systemctl status hodlmybot-dischord
    $ sudo systemctl status hodlmybot-dischord
    ```

## Credentials
In order to actually run your bot on Telegram and Slack, you will need to have set up your bots and have their access tokens, and put them in `api-creds-bot.json`:
```
{
    "slack" : {
        "access_token": "YOUR_SLACK_ACCESS_TOKEN"
    },
    "telegram" : {
        "access_token": "YOUR_TELEGRAM_ACCESS_TOKEN"
    },
    "dischord" : {
        "access_token": ""
    }
}
```

To have access to the Twitter functionality, you need access to their API and enter the details in `api-creds-twitter.json`:
```
{
	"consumer_key": "YOUR_CONSUMER_KEY",
	"consumer_secret": "YOUR_CONSUMER_SECRET",
	"access_token": "YOUR_ACCESS_TOKEN",
	"access_token_secret": "YOUR_TOKEN_SECRET"
}
```

## Updating historical data
The bot works best if it can continuously poll the latest data from several sources, and import them into the database in the form of historical data. For this purpose you have the `updater.py` script in `hodlcore` to be used with `cron`.

### CoinMarketCap
Imports the latest data from Coinmarketcap, which becomes the historical data used for token metrics.

### Twitter
Gathers historical followers metrics from the tracked twitter accounts.

### Reddit
Gather historical subscribers metrics from the tracked Reddit subreddits. 
