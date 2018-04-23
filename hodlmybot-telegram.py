#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Telegram bot
"""

import json
import argparse
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

import commands
from commands import AbstractCommand
from bot import AbstractBot

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandAdapter(object):
    def __init__(self, bot, command):
        self.bot = bot
        self.command = command

    def invoke(self, bot, update, args, job_queue=None, chat_data=None):
        channel = update.message.chat_id
        self.command.invoke(bot=self.bot, channel=channel, args=args)

    def job_callback(self, bot, job):
        channel = job.context
        self.command.invoke(bot=self.bot, channel=channel, args=[job._interval, job._threshold])


class TelegramBot(AbstractBot):
    def __init__(self):
        # Create the Updater and pass it your bot's token.
        with open('api-creds-bot.json', 'r') as file:
            access_token = json.load(file)['telegram']['access_token']
            self.updater = Updater(access_token)

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher
        self.bot = self.dp.bot

        # Add general commands
        self._commands = commands.AllCommands(prefix='/')
        for command in self._commands.all_commands:
            adapter = CommandAdapter(self, command)
            self.dp.add_handler(CommandHandler(command.name, adapter.invoke, pass_args=True))
        
        # Add Telegram specific commands
        self.dp.add_handler(CommandHandler("start", self._start_jobs, pass_args=True, pass_job_queue=True, pass_chat_data=True))
        self.dp.add_handler(CommandHandler("stop", self._stop_jobs, pass_args=True, pass_job_queue=True))
        self.dp.add_handler(CommandHandler('help', self._help))

        # log all errors
        self.dp.add_error_handler(self._error)

    def start(self):
        # Start the Bot
        self.updater.start_polling()
        print("HODL My Bot connected and running!")

        # Block until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

    def post_message(self, message, channel):
        self.bot.send_message(chat_id=channel, text=message, parse_mode=ParseMode.MARKDOWN)

    def post_reply(self, message, channel):
        self.post_message(message, channel)

    def post_image(self, image, animated, channel):
        if animated:
            self.bot.sendDocument(chat_id=channel, document=image)
        else:
            self.bot.send_photo(chat_id=channel, photo=image)

    def _help(self, bot, update):
        self.post_message(self._commands.help(), update.message.chat_id)

    def _error(self, bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def _start_jobs(self, bot, update, args, job_queue, chat_data):
        chat_id = update.message.chat_id
        # Moonwatch
        moonw = self._commands.get_job_command('moonwatch')
        job = job_queue.run_repeating(CommandAdapter(self, moonw).job_callback, 300, context=chat_id)
        job._threshold = 0.7
        job._interval = 300
        chat_data['job'] = job
        # Market watch
        marketw = self._commands.get_job_command('marketwatch')
        job = job_queue.run_repeating(CommandAdapter(self, marketw).job_callback, 900, context=chat_id)
        job._threshold = 10
        job._interval = 900
        chat_data['job'] = job
        # Start rank watch
        marketw = self._commands.get_job_command('rankwatch')
        job = job_queue.run_repeating(CommandAdapter(self, marketw).job_callback, 1, context=chat_id)
        job._threshold = 500000
        job._interval = 1
        chat_data['job'] = job
        # explicit start, in case explicit stop
        job_queue.start()

    def _stop_jobs(self, bot, update, args, job_queue):
        for job in job_queue.jobs():
            job.enabled = False
            job.schedule_removal()


def main():
    # Fetch and parse commandline arguments
    parser = argparse.ArgumentParser(
        description="Telegram bot with a wide variety of features related to crypto currency",
        epilog='Example: {} --start --debug'.format(sys.argv[0]))
    parser.add_argument(
        '--log', help="log to file (default: None)", metavar='FILE', default=None)
    parser.add_argument(
        '--debug', help="set loglevel to debug", action='store_true', default=False)

    args = parser.parse_args()

    # Set debug level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # If we have log file, log to that file
    if args.log:
        log_file = handlers.RotatingFileHandler(args.log, maxBytes=(1048576*5), backupCount=7)
        logger.addHandler(log_file)

    bot = TelegramBot()
    bot.start()

if __name__ == '__main__':
    main()
