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
        file = open('api-creds-slack.json', 'r')
        access_token = json.load(file)['access_token']
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
        attachements = [{"title": "", "image_url": image}]
        self._slack_client.api_call("chat.postMessage", channel=channel, text='', attachments=attachments)



if __name__ == "__main__":
    bot = SlackBot()
    while True:
        bot.parse_commands()
        time.sleep(RTM_READ_DELAY)
