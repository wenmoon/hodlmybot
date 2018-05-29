#!/usr/bin/env python3

import os
import time
import re
import json
import random

import logging

from operator import itemgetter
from operator import attrgetter

from hodlcore import api
from hodlcore import model
from hodlcore import db
from hodlcore import stringformat

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class AbstractCommand(object):
    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name

    async def invoke(self, bot, channel, args):
        pass

    @property
    def usage(self):
        pass


class MessageCommand(AbstractCommand):
    def __init__(self, prefix, name, message_text, usage_text):
        self.prefix = prefix
        self.name = name
        self.message_text = message_text
        self.usage_text = usage_text

    async def invoke(self, bot, channel, args):
        await bot.post_message(self.message_text, channel)

    @property
    def usage(self):
        return '{}{} - {}'.format(self.prefix, self.name, self.usage_text)

    @classmethod
    def from_json(cls, json, prefix):
        try:
            prefix = prefix
            name = json['name']
            message_text = json['message']
            usage_text = json['usage']
            return cls(prefix, name, message_text, usage_text)
        except Exception as e:
            return None

    @staticmethod
    def from_config(prefix):
        try:
            file = open('message_commands.json', 'r')
            cmds_json = json.load(file)
            cmds = []
            for cmd in cmds_json:
                cmds.append(MessageCommand.from_json(cmd, prefix))
            return cmds
        except Exception as e:
            return []


class AllCommands(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.all_commands = [
            TokenSearchCommand(prefix, 'find'),
            TokenSearchCommand(prefix, 'f'),
            TokenSearchCommand(prefix, 'search'),
            TokenStatsCommand(prefix, 'stats'),
            TokenStatsCommand(prefix, 's'),
            TokenLogoCommand(prefix, 'logo'),
            TokenLogoCommand(prefix, 'l'),
            TokenUSDCommand(prefix, 'usd'),
            TokenUSDCommand(prefix, 'u'),
            TokenConvertCommand(prefix, 'convert'),
            TokenConvertCommand(prefix, 'conv'),
            TokenCompareCommand(prefix, 'compare'),
            TokenCompareCommand(prefix, 'comp'),
            MarketCapitalizationCommand(prefix, 'mcap'),
            MarketCapitalizationCommand(prefix, 'm'),
            TopMCAPCommand(prefix, 'topmcap'),
            TopMCAPCommand(prefix, 'tm'),
            ICOCommand(prefix, 'ico'),
            TokenWebpageCommand(prefix, 'web'),
            TokenWebpageCommand(prefix, 'w'),
            AirdropsCommand(prefix, 'airdrop'),
            TwitterCommand(prefix, 'twitter'),
            RedditCommand(prefix, 'reddit'),
        ]
        # Basic 
        scmds = MessageCommand.from_config(self.prefix)
        for scmd in scmds:
            self.all_commands.insert(0, scmd)

        ricmds = RandomImageCommand.from_config(self.prefix)
        for ricmd in ricmds:
            self.all_commands.append(ricmd)

        rmcmds = RandomMessageCommand.from_config(self.prefix)
        for rmcmd in rmcmds:
            self.all_commands.append(rmcmd)

        help_text = 'This bot currently supports the following commands:\n```'
        for command in self.all_commands:
            help_text += '\t{}\n'.format(command.usage)
        help_text += '```'
        help_command = MessageCommand(prefix, 'help', help_text, 'Lists all available commands')
        self.all_commands.insert(0, help_command)

        self.job_commands = [
            MarketWatchCommand(prefix, 'marketwatch'),
            MoonWatchCommand(prefix, 'moonwatch'),
            RankWatchCommand(prefix, 'rankwatch'),
        ]

    def get_command(self, name):
        for command in self.all_commands:
            if command.name == name:
                return command
        return None

    def get_job_command(self, name):
        for command in self.job_commands:
            if command.name == name:
                return command
        return None



class AboutCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        message =  '{} HODL My Bot - The Simple Crypto Bot\n'.format(stringformat.emoji('robot'))
        message += '{} github.com/wenmoon/hodlmybot\n'.format(stringformat.emoji('link'))
        message += '{} ETH: 0x73eFDa13bC0d0717b4f2f36418279FD4E2Cd0Af9\n'.format(stringformat.emoji('money_bag'))
        await bot.post_message(message, channel)

    @property
    def usage(self):
        return '{}{} - A little bit about myself'.format(self.prefix, self.name)


class TokenStatsCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        if len(args) == 0:
            mcap = api.get_mcap()
            await bot.post_message(stringformat.mcap_summary(mcap), channel)
            return

        token = api.search_token(args[0])
        if token is None:
            error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
            await bot.post_reply(error, channel)
            return

        summary_btc = None
        if not token.is_bitcoin():
            summary_btc = db.TokenDB().get_prices_btc(token.id)
        await bot.post_message(stringformat.token_summary(token, summary_btc), channel)

    @property
    def usage(self):
        return '{}{} [<token>] - Global metrics, or metrics of <token>'.format(self.prefix, self.name)


class TokenLogoCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        query = args[0].lower()
        token = api.search_token(query)
        if token is None:
            await bot.post_message('Could not find logo for {}'.format(query), channel)
        else:
            await bot.post_image(image=token.logo_url, animated=False, channel=channel)

    @property
    def usage(self):
        return '{}{} <token> - Show token logo'.format(self.prefix, self.name)


class TokenSearchCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        try:
            query = args[0].lower()
            tokens = api.search_tokens(search=query, limit=10000)
            sorted_tokens = sorted(tokens, key=attrgetter('rank'), reverse=False)
            matches = []
            for token in sorted_tokens:
                matches.append('\t#{}: *{} ({})*, ID: {}'.format(token.rank, token.name, token.symbol, token.id))
            if len(tokens) > 0:
                search_result = 'Found *{}* match(es), sorted by rank:\n{}'.format(len(tokens), '\n'.join(matches))
            else:
                search_result = 'Sorry, *0 matches* for query: {}'.format()

            await bot.post_reply(search_result, channel)
        except (IndexError, ValueError):
            await bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <query> - Search for a token'.format(self.prefix, self.name)


class TokenUSDCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        try:
            token = api.search_token(args[0])
            if token is None:
                error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
                await bot.post_message(error, channel)
            else:
                message = '{} 1 {} = *${:.2f}*'.format(stringformat.emoji('dollar'), token.symbol.upper(), token.price)
                await bot.post_message(message, channel)
        except (IndexError, ValueError):
                await bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <token> - Convert <token> to USD'.format(self.prefix, self.name)


class TokenConvertCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        try:
            amount = args[0]
            from_token = api.search_token(args[1])
            to_token = api.search_token(args[2])
            converted_amount = (float(amount) * from_token.price) / to_token.price
            message = '{} {} {} = *{:.8f} {}*'.format(stringformat.emoji('dollar'), amount, from_token.symbol.upper(), converted_amount, to_token.symbol.upper())
            await bot.post_reply(message, channel)
        except (IndexError, ValueError):
            await bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <amount> <from> <to> - Convert between tokens'.format(self.prefix, self.name)


class TokenCompareCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        try:
            token1 = api.search_token(args[0])
            token2 = api.search_token(args[1])

            if token1 is None:
                error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'.format(args[0])
                await bot.post_reply(error, channel)
                return
            if token2 is None:
                error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'.format(args[1])
                await bot.post_reply(error, channel)
                return

            await bot.post_message(stringformat.token_compared_summary(token1, token2), channel)
        except (IndexError, ValueError):
            await bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <token1> <token2> - Compare two tokens'.format(self.prefix, self.name)


class MarketCapitalizationCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        mcap_now = api.get_mcap()
        mcap_db = db.MarketCapitalizationDB()
        mcap_prev = mcap_db.get_latest()
        mcap_db.insert(mcap_now)

        if mcap_prev is None:
            text = 'Total Market Cap, *${}*'.format(stringformat.large_number(mcap_now.mcap_usd))
        else:
            change = ((mcap_now.mcap_usd - mcap_prev.mcap_usd) / mcap_now.mcap_usd) * 100
            if change == 0:
                text = 'Total Market Cap unchanged, *${}*. {}'.format(stringformat.large_number(mcap_now.mcap_usd), stringformat.emoji('carlos'))
            else:
                emoji = stringformat.emoji('rocket') if change > 0 else stringformat.emoji('skull')
                text = 'Total Market Cap *{}* since last check, *${}*. {}'.format(stringformat.percent(num=change, emo=False), stringformat.large_number(mcap_now.mcap_usd), emoji)

        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Show a breakdown of total mcap'.format(self.prefix, self.name)


class ICOCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        token = api.search_token(args[0])
        if token is None:
            error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
            await bot.post_message(error, channel)
            return

        ico_text = api.get_ico_text(token)
        if ico_text:
            await bot.post_message(ico_text, channel)
        else:
            text = 'Sorry, I couldn\'t find *{}* on ICO Drops.'.format(token.id)
            await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} <token> - Get ICO info'.format(self.prefix, self.name)


class TokenWebpageCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        query = args[0].lower()
        token = api.search_token(query)
        if token is None:
            await bot.post_message('Could not find webpage for {}'.format(query), channel)
        else:
            await bot.post_message(token.url, channel)

    @property
    def usage(self):
        return '{}{} <token> - Link to token webpage'.format(self.prefix, self.name)


class AirdropsCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        airdrops = api.get_airdrops()
        if len(airdrops) > 0:
            await bot.post_message(stringformat.airdrops_summary(airdrops), channel)
        else:
            await bot.post_message("*No upcoming airdrops!*", channel)

    @property
    def usage(self):
        return '{}{} - List of upcoming airdrops'.format(self.prefix, self.name)


class TopMCAPCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        token_db = db.TokenDB()
        tokens = api.get_top_tokens(limit=200)

        text = '*Tokens (20 from top 300, by weekly mcap growth) {}:*\n'.format(stringformat.emoji('charts'))
        mcaps = []
        for token in tokens:
            summary = token_db.get_mcaps(token.id)
            if summary is not None:
                mcaps.append(summary)

        i = 1
        sorted_mcaps = sorted(mcaps, key=attrgetter('pct_week'), reverse=True)[:20]
        for m in sorted_mcaps:
            text += '\t{}. *{}*: {} (W:{}, M:{})\n'.format(i, m.name, m.now, stringformat.percent(m.pct_week, emo=False), stringformat.percent(m.pct_month, emo=False))
            i += 1

        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - List top 20 mcap tokens'.format(self.prefix, self.name)


class TwitterCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        twitter_db = db.TwitterDB()

        # handle add/del/list functions
        try:
            if args[0].lower() == 'add':
                twitter_db.track(args[1])
                message = '*Added Twitter user {} to watch list.*'.format(args[1])
                await bot.post_reply(message, channel)
                return
            elif args[0].lower() == 'del':
                reddit_db.untrack(args[1])
                message = '*Removed Twitter user {} to watch list.*'.format(args[1])
                await bot.post_reply(message, channel)
                return
            elif args[0].lower() == 'list':
                twitters = twitter_db.get_tracked()
                message = '*Currently watching these Twitters accounts (%s total):*\n\n' % len(twitters)
                message += ', '.join(twitters)
                await bot.post_message(message, channel)
                return
        except IndexError:
            pass

        users = twitter_db.get_tracked()
        followers = []
        for user in users:
            subscribers = twitter_db.get_subscribers(user)
            if subscribers is not None:
                followers.append(subscribers)
        if len(followers) > 0:
            i = 1
            sorted_followers = sorted(followers, key=attrgetter('pct_week'), reverse=True)[:20]
            text = '*Twitter users (top 20, by weekly growth) {}:*\n'.format(stringformat.emoji('charts'))
            for s in sorted_followers:
                text += '    {}. *{}*: {} (W: {}, M: {})\n'.format(i, s.name, s.now, stringformat.percent(s.pct_week, emo=False), stringformat.percent(s.pct_month, emo=False))
                i += 1
        else:
            text = 'No Twitter data available.'

        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - [add|del <user>] - Add or list followers'.format(self.prefix, self.name)


class RedditCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        reddit_db = db.RedditDB()

        # handle add/del/list functions
        try:
            if args[0].lower() == 'add':
                subreddit = args[1]
                reddit_db.track(subreddit)
                message = '*Added subreddit {} to watch list.*'.format(subreddit)
                await bot.post_message(message, channel)
                return
            elif args[0].lower() == 'del':
                subreddit = args[1]
                reddit_db.untrack(subreddit)
                message = '*Removed subreddit {} to watch list.*'.format(subreddit)
                await bot.post_message(message, channel)
                return
            elif args[0].lower() == 'list':
                subreddits = reddit_db.get_tracked()
                message = '*Currently watching these subreddits (%s total):*\n\n' % len(subreddits)
                message += ', '.join(subreddits)
                await bot.post_message(message, channel)
                return
        except IndexError:
            pass

        tracked_subreddits = reddit_db.get_tracked()
        subs = []
        for tracked_subreddit in tracked_subreddits:
            subscribers = reddit_db.get_subscribers(tracked_subreddit)
            if subscribers is not None:
                subs.append(subscribers)
        if len(subs) > 0:
            i = 1
            sorted_subs = sorted(subs, key=attrgetter('pct_week'), reverse=True)[:20]
            text = '*Reddit communities (top 20, by weekly growth) {}:*\n'.format(stringformat.emoji('charts'))
            for s in sorted_subs:
                text += '    {}. *{}*: {} (W: {}, M: {})\n'.format(i, s.name, s.now, stringformat.percent(s.pct_week, emo=False), stringformat.percent(s.pct_month, emo=False))
                i += 1
        else:
            text += 'No Reddit data available.'

        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - [add|del <subreddit>] - Add or list subscribers'.format(self.prefix, self.name)


class MarketWatchCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        mcap_now = api.get_mcap()
        mcap_db = db.MarketCapitalizationDB()
        mcap_prev = mcap_db.get_latest()
        mcap_db.insert(mcap_now)

        change = stringformat.percent(num=((mcap_now.mcap_usd - mcap_prev.mcap_usd) / mcap_now.mcap_usd) * 100, emo=False)

        threshold = 0.7
        try:
            threshold = args[1]
        except Exception:
            pass
        if abs(change) < 0.7:
            return

        if change > 0:
            t = 'Double rainbow!{}{}'.format(stringformat.emoji('rainbow'), stringformat.emoji('rainbow'))
            adj = stringformat.emoji('rocket')
            prefix = '+'
        elif change < 0:
            t = 'ACHTUNG!{}'.format(stringformat.emoji('collision'))
            adj = stringformat.emoji('poop')
            prefix = ''

        return_url = 'https://coinmarketcap.com/charts/'
        text = '*{}* Total Market Cap *{}{}%* in {} seconds, *${}!*\n\n{}'.format(t, prefix, change, interval, stringformat.large_number(mcap_now.mcap_usd), return_url)
        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows large changes in the market'.format(self.prefix, self.name)


class MoonWatchCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        eth = api.search_token('ethereum')
        btc = api.search_token('bitcoin')
        top_tokens = api.get_top_tokens(limit=300)
        tokens = [token for token in top_tokens if token.volume_24h >= 500000]
        for token in tokens:
            text = '*{}* ({}, #{}) *+{:.2f}%* in the last hour, trading at *${:.2f}*. BTC ${:.2f}, ETH ${:.2f}. %{}'.format(
                token.name, token.symbol, token.rank, token.percent_change_1h,
                token.price, btc.price, eth.price, stringformat.emoji('rocket'))
            await bot.post_message(text, channel)

            # Change in volume
            token_db = db.TokenDB()
            volumes = token_db.get_volumes(token.id)
            if not volumes:
                continue
            pct_change = ((token.volume_24h / volumes.now) - 1) * 100
            if pct_change >= 80 and \
                token.volume_24h > volumes.yesterday and \
                token.volume_24h > volumes.avg_last_week:
                text = '*24h volume* of *{}* ({}, #{}) increased by *{:.2f}%* to *${}*. Last ${}, yesterday ${}, week avg ${}. {}'.format(
                    token.name, token.symbol, token.rank, pct_change, token.volume_24h,
                    volumes.now, volumes.yesterday, volumes.avg_last_week, stringformat.emoji('fire'))
                logger.info('{} is trading {:.2f}% above last check'.format(token.id, pct_change))
            await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows what tokens are mooning'.format(self.prefix, self.name)


class RankWatchCommand(AbstractCommand):
    async def invoke(self, bot, channel, args):
        volume_threshold = 500000
        top_tokens = api.get_top_tokens(limit=200)
        token_db = db.TokenDB()
        tokens_ranks = []
        for token in top_tokens:
            ranks = token_db.get_ranks(token.id)
            if not ranks:
                continue
            if token.volume_24h >= volume_threshold and ranks.now < ranks.last_week and ranks.now < ranks.today and ranks.is_atl:
                tokens_ranks.append((token, ranks))

        if len(tokens_ranks) > 0:
            tokens_ranks = sorted(tokens_ranks, key=itemgetter(1), reverse=False)
            text = '*tokenMarketCap rank climbers (w/m):*\n'
            for (token, ranks) in token_ranks:
                text += stringformat.token_ranks_summary(token, ranks)
            text += '\nShowing All Time High ranks only {}'.format(stringformat.emoji('fire'))
            await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows what tokens are climbing the ranks'.format(self.prefix, self.name)


class RandomImageCommand(AbstractCommand):
    def __init__(self, prefix, name, usage_text, images):
        super().__init__(prefix, name)
        self.usage_text = usage_text
        self.images = images

    async def invoke(self, bot, channel, args):
        image = random.choice(self.images)
        await bot.post_image(image=image, animated=image.endswith('.gif'), channel=channel)

    @property
    def usage(self):
        return '{}{} - {}'.format(self.prefix, self.name, self.usage_text)

    @classmethod
    def from_json(cls, json, prefix):
        try:
            prefix = prefix
            name = json['name']
            usage_text = json['usage']
            images = json['images']
            return cls(prefix, name, usage_text, images)
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def from_config(prefix):
        try:
            file = open('random_image_commands.json', 'r')
            cmds_json = json.load(file)
            cmds = []
            for cmd_json in cmds_json:
                cmds.append(RandomImageCommand.from_json(cmd_json, prefix))
            return cmds
        except Exception as e:
            print(e)
            return []

class RandomMessageCommand(AbstractCommand):
    def __init__(self, prefix, name, usage_text, texts):
        super().__init__(prefix, name)
        self.usage_text = usage_text
        self.texts = texts

    async def invoke(self, bot, channel, args):
        text = random.choice(self.texts)
        await bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - {}'.format(self.prefix, self.name, self.usage_text)

    @classmethod
    def from_json(cls, json, prefix):
        try:
            prefix = prefix
            name = json['name']
            usage_text = json['usage']
            messages = json['messages']
            return cls(prefix, name, usage_text, messages)
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def from_config(prefix):
        try:
            file = open('random_message_commands.json', 'r')
            cmds_json = json.load(file)
            cmds = []
            for cmd_json in cmds_json:
                cmds.append(RandomMessageCommand.from_json(cmd_json, prefix))
            return cmds
        except Exception as e:
            print(e)
            return []
