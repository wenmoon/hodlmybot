#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Telegram bot
"""

import json
import commandscrypto
import commandsfun
import argparse
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

import commands
from bot import AbstractBot

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandAdapter(object):
    def __init__(self, bot, command):
        self.bot = bot
        self.command = command

    def invoke(self, bot, update, args):
        self.command.invoke(self.bot, update.message.chat_id, args)


class TelegramBot(AbstractBot):
    def __init__(self):
        # Create the Updater and pass it your bot's token.
        with open('api-creds-telegram.json', 'r') as file:
            access_token = json.load(file)['access_token']
            self.updater = Updater(access_token)

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher
        self.bot = self.dp.bot

        # Add commands
        self._commands = commands.AllCommands(prefix='/')
        for command in self._commands.all_commands:
            adapter = CommandAdapter(self, command)
            self.dp.add_handler(CommandHandler(command.name, adapter.invoke, pass_args=True))
        self.dp.add_handler(CommandHandler('help', self.help))
        # TODO: Handle watcher commands properly - challenge being writing an adaper for all the params
        # dp.add_handler(CommandHandler("marketwatch", commandscrypto.set_marketwatch_timer,  pass_args=True, pass_job_queue=True, pass_chat_data=True))
        # dp.add_handler(CommandHandler("mw", commandscrypto.set_marketwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))
        # dp.add_handler(CommandHandler("moonwatch", commandscrypto.set_moonwatch_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True))

        # on noncommand i.e message - echo the message on Telegram
        self.dp.add_handler(InlineQueryHandler(inlinequery))

        # log all errors
        self.dp.add_error_handler(error)

    def post_message(self, message, channel):
        self.bot.send_message(chat_id=channel, text=message, parse_mode=ParseMode.MARKDOWN)

    def post_reply(self, message, channel):
        # TODO: Handle replies properly
        #update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        self.post_message(message, channel)

    def post_image(self, image, animated, channel):
        if animated:
            self.bot.sendDocument(chat_id=channel, document=image)
        else:
            self.bot.send_photo(chat_id=channel, photo=image)

    def help(self, bot, update):
        self.post_message(self._commands.help(), update.message.chat_id)

    def start(self):
        # Start the Bot
        self.updater.start_polling()

        # Block until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        print("HODL My Bot connected and running!")


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



def main():
    # Fetch and parse commandline arguments
    parser = argparse.ArgumentParser(
        description="Telegram bot with a wide variety of features related to crypto currency",
        epilog='Example: {} --start --debug'.format(sys.argv[0]))
    parser.add_argument(
        '--start', help="start hodlmybot", action='store_true', default=False)
    parser.add_argument(
        '--log', help="log to file (default: None)", metavar='FILE', default=None)
    parser.add_argument(
        '--debug', help="set loglevel to debug", action='store_true', default=False)

    args = parser.parse_args()

    # We need at least --start
    if not args.start:
        parser.print_help()
        return False

    # Set debug level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # If we have log file, log to that file
    if args.log:
        log_file = handlers.RotatingFileHandler(args.log, maxBytes=(1048576*5), backupCount=7)
        logger.addHandler(log_file)

    if args.start:
        bot = TelegramBot()
        bot.start()

if __name__ == '__main__':
    main()
