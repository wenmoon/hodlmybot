#!/usr/bin/env python

import os
import time
import re
import json
from slackclient import SlackClient
from hodlcore import api
from hodlcore import model

from commands import AbstractBot
import commands

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM


class SlackBot(AbstractBot):
    def __init__(self):
        self.commands = { 
            '!search': commands.TokenSearchCommand(self),
            '!stats': commands.TokenStatusCommand(self),
            '!usd': commands.TokenUSDCommand(self),
            '!convert': commands.TokenConvertCommand(self),
            '!compare': commands.TokenCompareCommand(self),
            '!mcap': commands.MarketCapitalizationCommand(self),
            '!ico': commands.ICOCommand(self),
            '!web': commands.TokenWebpageCommand(self),
            '!airdop': commands.AirdropsCommand(self),
            '!cmc': commands.CMCCommand(self),
            '!twitter': commands.TwitterCommand(self),
            '!reddit': commands.RedditCommand(self),
            '!hodl': commands.HODLCommand(self),
            '!fomo': commands.FOMOCommand(self),
            '!fud': commands.FUDCommand(self),
            '!carlos': commands.CarlosCommand(self),
            '!rackle': commands.RackleCommand(self),
            '!yn': commands.YesNoCommand(self),
            '!diceroll': commands.DicerollCommand(self)
        }
        file = open('api-creds-slack.json', 'r')
        access_token = json.load(file)['access_token']
        self.slack_client = SlackClient(access_token)
        if self.slack_client.rtm_connect(with_team_state=False):
            print("HODL My Bot connected and running!")
            self.bot_id = self.slack_client.api_call("auth.test")["user_id"]
        else:
            print("Connection failed.")


    def parse_commands(self):
        for event in self.slack_client.rtm_read():
            if event["type"] == "message" and not "subtype" in event:
                try:
                    message = event["text"].split()                    
                    channel = event["channel"]
                    command = self.commands[message[0]]
                    args = message[1:]
                    command.invoke(channel, args)
                except Exception as e:
                    print(e)


    def post_message(self, message, channel):
        if message is not None and channel is not None:
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message)


    def post_reply(self, message, channel):
        self.post_message(message, channel)

    def post_image(self, image, animated, channel):
        attachements = [{"title": "", "image_url": image}]
        self.slack_client.api_call("chat.postMessage", channel=channel, text='', attachments=attachments)


    def _help(self, channel, args):
        text = """This bot currently supports the following commands:
        Help:
        !help - This help

        Tools:
        !search - Search for coin
        !webpage <coin> - Link to coin webpage
        !mcap - Total market cap
        !usd <coin> - USD value of <coin>
        !stats [<coin>] - Global core metrics or metrics of <coin>
        !ico <coin> - Get ICO info
        !convert <amount> <from coin> <to coin> - Coin conversion
        !compare <coin1> <coin2> - Compare two coins

        Intel:
        !airdrops - List of upcoming airdrops
        !reddit [add|del <subreddit> or list] - Add or list Reddit followers
        !twitter [add|del <user> or list] - Add or list Twitter followers

        Fun:
        !hodl - Helps you decide whether or not to HODL
        !fomo - When you have FOMO
        !fud - No FUD
        !carlos - CARLOS MATOS!
        !rackle - The Crazy Racklehahn
        !shouldi - Helps you decide
        !diceroll - Throw 1d6"""


if __name__ == "__main__":
    bot = SlackBot()
    while True:
        bot.parse_commands()
        time.sleep(RTM_READ_DELAY)
