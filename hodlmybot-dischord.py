#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Slack bot
"""
import os
import argparse
import sys
import time
import re
import json
import logging

from hodlcore import api
from hodlcore import model
from bot import AbstractBot
import commands

import discord

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class DischordBot(AbstractBot):
    def __init__(self):
        file = open('api-creds-bot.json', 'r')
        access_token = json.load(file)['dischord']['access_token']
        self._client = discord.Client()
        self._commands = commands.AllCommands(prefix='!')

    def start(self):
        self._client.run(access_token)

    def post_message(self, message, channel):
        if message is not None and channel is not None:
           await self._client.send_message(message, channel)

    def post_reply(self, message, channel):
        self.post_message(message, channel)

    def post_image(self, image, animated, channel):
        self.post_message(image, channel)

    @_client.event
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author == client.user:
            return

        try:
            channel = message.channel
            message = message.content.split()
            command_str = message[0]
            raw_command = command_str[1:]
            if raw_command == 'help':
                self.post_message(self._commands.help(), channel)
                return
            command = self._commands.get_command(raw_command)
            if command is not None:
                args = message[1:]
                command.invoke(self, channel, args)
        except Exception as e:
            pass

    @_client.event
    async def on_ready(self):
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')
        print("HODL My Bot connected and running!")


def main(): 
    # Fetch and parse commandline arguments
    parser = argparse.ArgumentParser(
        description="Slack bot with a wide variety of features related to crypto currency",
        epilog='Example: {} --debug'.format(sys.argv[0]))
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

    bot = DischordBot()
    bot.start()


if __name__ == "__main__":
    main()
