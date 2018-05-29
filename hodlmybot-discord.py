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

import commands
from bot import AbstractBot

import discord
import asyncio

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)



class DischordBot(AbstractBot):
    def __init__(self):
        self._commands = commands.AllCommands(prefix='!')
        self._client = discord.Client()
        self._queue = []

        @self._client.event
        async def on_message(message):
            # we do not want the bot to reply to itself
            if message.author == self._client.user:
                return
            try:
                channel = message.channel
                message = message.content.split()
                command_str = message[0]
                if not command_str.startswith(self._commands.prefix):
                    return
                raw_command = command_str[1:]
                command = self._commands.get_command(raw_command)
                if command is not None:
                    args = message[1:]
                    await command.invoke(self, channel, args)
            except Exception as e:
                print(e)
                pass

        @self._client.event
        async def on_ready():
            print('Logged in as')
            print(self._client.user.name)
            print(self._client.user.id)
            print('------')
            print("HODL My Bot connected and running!")

    def start(self):
        file = open('api-creds-bot.json', 'r')
        access_token = json.load(file)['discord']['access_token']
        self._client.run(access_token)

    async def post_message(self, message, channel):
        if message is not None and channel is not None:
           await self._client.send_message(channel, message)

    async def post_reply(self, message, channel):
        await self.post_message(message, channel)

    async def post_image(self, image, animated, channel):
        await self.post_message(image, channel)

    async def post_help(self, channel):
        await self.post_message(self._commands.help(), channel)


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
