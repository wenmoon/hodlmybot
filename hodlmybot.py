#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Telegram bot
"""

from telegram.utils.helpers import escape_markdown
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent, ParseMode
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

from commands import cyrotocommands
from commands import funcommands


def start_default(bot, update, args, job_queue, chat_data):
    # Start default jobs
    chat_id = update.message.chat_id
    job = job_queue.run_repeating(marketwatch, 300, context=chat_id)
    job._threshold = 0.7
    job._interval = 300
    chat_data['job'] = job

    job = job_queue.run_repeating(moonwatch, 900, context=chat_id)
    job._threshold = 10
    job._interval = 900
    chat_data['job'] = job

    # Start rank watch
    job = job_queue.run_repeating(rankwatch, 43200, context=chat_id)
    chat_data['job'] = job


def inlinequery(bot, update):
    """Handle the inline query."""
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
    updater = Updater("<get bot token from @botmaster>")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Cyrpto functionality
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("h", help))
    dp.add_handler(CommandHandler("search", cyrotocommands.search, pass_args=True))
    dp.add_handler(CommandHandler("q", cyrotocommands.search, pass_args=True))
    dp.add_handler(CommandHandler("mcap", cyrotocommands.mcap))
    dp.add_handler(CommandHandler("m", cyrotocommands.mcap))
    dp.add_handler(CommandHandler("webpage", cyrotocommands.webpage, pass_args=True))
    dp.add_handler(CommandHandler("website", cyrotocommands.webpage, pass_args=True))
    dp.add_handler(CommandHandler("w", cyrotocommands.webpage, pass_args=True))
    dp.add_handler(CommandHandler("homepage", cyrotocommands.webpage, pass_args=True))
    dp.add_handler(CommandHandler("convert", cyrotocommands.convert, pass_args=True))
    dp.add_handler(CommandHandler("c", cyrotocommands.convert, pass_args=True))
    dp.add_handler(CommandHandler("compare", cyrotocommands.compare, pass_args=True))
    dp.add_handler(CommandHandler("cmp", cyrotocommands.compare, pass_args=True))
    dp.add_handler(CommandHandler("usd", cyrotocommands.usd, pass_args=True))
    dp.add_handler(CommandHandler("u", cyrotocommands.usd, pass_args=True))
    dp.add_handler(CommandHandler("price", cyrotocommands.usd, pass_args=True))
    dp.add_handler(CommandHandler("stats", cyrotocommands.stats, pass_args=True))
    dp.add_handler(CommandHandler("s", cyrotocommands.stats, pass_args=True))
    dp.add_handler(CommandHandler("coin", cyrotocommands.stats, pass_args=True))
    dp.add_handler(CommandHandler("ico", cyrotocommands.ico, pass_args=True))
    dp.add_handler(CommandHandler("i", cyrotocommands.ico, pass_args=True))
    dp.add_handler(CommandHandler("reddit", cyrotocommands.reddit, pass_args=True))
    dp.add_handler(CommandHandler("r", cyrotocommands.reddit, pass_args=True))
    dp.add_handler(CommandHandler("twitter", cyrotocommands.twitter, pass_args=True))
    dp.add_handler(CommandHandler("t", cyrotocommands.twitter, pass_args=True))
    dp.add_handler(CommandHandler("coinmarketcap", cyrotocommands.coinmarketcap, pass_args=True))
    dp.add_handler(CommandHandler("marketwatch", cyrotocommands.set_marketwatch_timer,  pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("mw", cyrotocommands.set_marketwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("moonwatch", cyrotocommands.set_moonwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("start", cyrotocommands.start_default, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("airdrops", cyrotocommands.airdrops))
    dp.add_handler(CommandHandler("airdrop", cyrotocommands.airdrops))
    dp.add_handler(CommandHandler("ad", cyrotocommands.airdrops))

    # Fun stuff
    dp.add_handler(CommandHandler("hodl", funcommands.hodl))
    dp.add_handler(CommandHandler("fomo", funcommands.fomo))
    dp.add_handler(CommandHandler("fud", funcommands.fud))
    dp.add_handler(CommandHandler("carlos", funcommands.carlos))
    dp.add_handler(CommandHandler("rackle", funcommands.racklehahn))
    dp.add_handler(CommandHandler("shouldi", funcommands.shouldi))
    dp.add_handler(CommandHandler("si", funcommands.shouldi))
    dp.add_handler(CommandHandler("diceroll", funcommands.diceroll))

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
