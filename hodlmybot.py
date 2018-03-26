#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Telegram bot
"""

from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

import json
import logging

import commandscrypto
import commandsfun

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def inlinequery(bot, update):
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="Caps",
            input_message_content=InputTextMessageContent(
                query.upper())),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Bold",
            input_message_content=InputTextMessageContent(
                "*{}*".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN)),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Italic",
            input_message_content=InputTextMessageContent(
                "_{}_".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN))]

    update.inline_query.answer(results)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def help(bot, update):
    """Send a message when the command /help is issued."""
    text = """This bot currently supports the following commands:
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
    /diceroll - Throw 1d6"""
    update.message.reply_text(text)


def main():
    # Create the Updater and pass it your bot's token.
    with open('api-creds-telegram.json', 'r') as file:
        access_token = json.load(file)['access_token']
        updater = Updater(access_token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Start command
    dp.add_handler(CommandHandler("start", commandscrypto.start_default, pass_args=True, pass_job_queue=True, pass_chat_data=True))

    # Cyrpto functionality
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("h", help))
    dp.add_handler(CommandHandler("search", commandscrypto.search, pass_args=True))
    dp.add_handler(CommandHandler("q", commandscrypto.search, pass_args=True))
    dp.add_handler(CommandHandler("mcap", commandscrypto.mcap))
    dp.add_handler(CommandHandler("m", commandscrypto.mcap))
    dp.add_handler(CommandHandler("webpage", commandscrypto.webpage, pass_args=True))
    dp.add_handler(CommandHandler("website", commandscrypto.webpage, pass_args=True))
    dp.add_handler(CommandHandler("w", commandscrypto.webpage, pass_args=True))
    dp.add_handler(CommandHandler("homepage", commandscrypto.webpage, pass_args=True))
    dp.add_handler(CommandHandler("convert", commandscrypto.convert, pass_args=True))
    dp.add_handler(CommandHandler("c", commandscrypto.convert, pass_args=True))
    dp.add_handler(CommandHandler("compare", commandscrypto.compare, pass_args=True))
    dp.add_handler(CommandHandler("cmp", commandscrypto.compare, pass_args=True))
    dp.add_handler(CommandHandler("usd", commandscrypto.usd, pass_args=True))
    dp.add_handler(CommandHandler("u", commandscrypto.usd, pass_args=True))
    dp.add_handler(CommandHandler("price", commandscrypto.usd, pass_args=True))
    dp.add_handler(CommandHandler("stats", commandscrypto.stats, pass_args=True))
    dp.add_handler(CommandHandler("s", commandscrypto.stats, pass_args=True))
    dp.add_handler(CommandHandler("coin", commandscrypto.stats, pass_args=True))
    dp.add_handler(CommandHandler("ico", commandscrypto.ico, pass_args=True))
    dp.add_handler(CommandHandler("i", commandscrypto.ico, pass_args=True))
    dp.add_handler(CommandHandler("reddit", commandscrypto.reddit, pass_args=True))
    dp.add_handler(CommandHandler("r", commandscrypto.reddit, pass_args=True))
    dp.add_handler(CommandHandler("twitter", commandscrypto.twitter, pass_args=True))
    dp.add_handler(CommandHandler("t", commandscrypto.twitter, pass_args=True))
    dp.add_handler(CommandHandler("coinmarketcap", commandscrypto.coinmarketcap, pass_args=True))
    dp.add_handler(CommandHandler("cmc", commandscrypto.coinmarketcap, pass_args=True))
    dp.add_handler(CommandHandler("marketwatch", commandscrypto.set_marketwatch_timer,  pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("mw", commandscrypto.set_marketwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("moonwatch", commandscrypto.set_moonwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("airdrops", commandscrypto.airdrops))
    dp.add_handler(CommandHandler("airdrop", commandscrypto.airdrops))
    dp.add_handler(CommandHandler("ad", commandscrypto.airdrops))

    # Fun stuff
    dp.add_handler(CommandHandler("hodl", commandsfun.hodl))
    dp.add_handler(CommandHandler("fomo", commandsfun.fomo))
    dp.add_handler(CommandHandler("fud", commandsfun.fud))
    dp.add_handler(CommandHandler("carlos", commandsfun.carlos))
    dp.add_handler(CommandHandler("rackle", commandsfun.racklehahn))
    dp.add_handler(CommandHandler("shouldi", commandsfun.shouldi))
    dp.add_handler(CommandHandler("si", commandsfun.shouldi))
    dp.add_handler(CommandHandler("diceroll", commandsfun.diceroll))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
