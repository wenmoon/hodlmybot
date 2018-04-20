#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HODL MY BOT - A simple crypto tracking Slack bot
"""

import os
import time
import re
import json
from slackclient import SlackClient
from hodlcore import api
from hodlcore import model

from bot import AbstractBot
import commands

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM


class SlackBot(AbstractBot):
    def __init__(self):
        file = open('api-creds-bot.json', 'r')
        access_token = json.load(file)['slack']['access_token']
        self._commands = commands.AllCommands(prefix='!')
        self._slack_client = SlackClient(access_token)
        if self._slack_client.rtm_connect(with_team_state=False):
            print("HODL My Bot connected and running!")
            self._bot_id = self._slack_client.api_call("auth.test")["user_id"]
        else:
            print("Connection failed.")

    def parse_commands(self):
        for event in self._slack_client.rtm_read():
            if event["type"] == "message" and not "subtype" in event:
                try:
                    channel = event["channel"]
                    message = event["text"].split()
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

    def post_message(self, message, channel):
        if message is not None and channel is not None:
            self._slack_client.api_call("chat.postMessage", channel=channel, text=message)

    def post_reply(self, message, channel):
        self.post_message(message, channel)

    def post_image(self, image, animated, channel):
        attachments = [{"title": "", "image_url": image}]
        self._slack_client.api_call("chat.postMessage", channel=channel, text='', attachments=attachments)


if __name__ == "__main__":
    # Fetch and parse commandline arguments
    parser = argparse.ArgumentParser(
        description="Slack bot with a wide variety of features related to crypto currency",
        epilog='Example: {} --debug'.format(sys.argv[0]))
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

    bot = SlackBot()
    while True:
        bot.parse_commands()
        time.sleep(RTM_READ_DELAY)

