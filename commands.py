#!/usr/bin/env python

import os
import time
import re
import json
import random

from slackclient import SlackClient

from operator import itemgetter
from operator import attrgetter

from hodlcore import api
from hodlcore import model
from hodlcore import db
from hodlcore import stringformat


class AbstractCommand(object):
    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name

    def invoke(self, bot, channel, args):
        pass

    @property
    def usage(self):
        pass


class AllCommands(object):
    def __init__(self, prefix):
        self.all_commands = [
            AboutCommand(prefix, 'about'),
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
            # Fun
            HODLCommand(prefix, 'hodl'),
            FOMOCommand(prefix, 'fomo'),
            FUDCommand(prefix, 'fud'),
            CarlosCommand(prefix, 'carlos'),
            RackleCommand(prefix, 'rackle'),
            YesNoCommand(prefix, 'yn'),
            DicerollCommand(prefix, 'diceroll'),
            DicerollCommand(prefix, 'dice'),
        ]
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

    def help(self):
        text = 'This bot currently supports the following commands:\n```'
        for command in self.all_commands:
            text += '\t{}\n'.format(command.usage)
        text += '```'
        return text


class AboutCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        message =  '{} HODL My Bot - The Simple Crypto Bot\n'.format(stringformat.emoji('robot'))
        message += '{} github.com/wenmoon/hodlmybot\n'.format(stringformat.emoji('link'))
        message += '{} ETH: 0x73eFDa13bC0d0717b4f2f36418279FD4E2Cd0Af9\n'.format(stringformat.emoji('money_bag'))
        bot.post_message(message, channel)

    @property
    def usage(self):
        return '{}{} - A little bit about myself'.format(self.prefix, self.name)


class TokenStatsCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        if len(args) == 0:
            mcap = api.get_mcap()
            bot.post_message(stringformat.mcap_summary(mcap), channel)
            return

        token = api.search_token(args[0])
        if token is None:
            error = 'Sorry, I couldn\'t find *{}* on tokenMarketCap.'.format(args[0])
            bot.post_reply(error, channel)
            return

        summary_btc = None
        if not token.is_bitcoin():
            summary_btc = db.TokenDB().get_prices_btc(token.id)
        bot.post_message(stringformat.token_summary(token, summary_btc), channel)

    @property
    def usage(self):
        return '{}{} [<token>] - Global metrics, or metrics of <token>'.format(self.prefix, self.name)


class TokenLogoCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        query = args[0].lower()
        token = api.search_token(query)
        if token is None:
            bot.post_message('Could not find logo for {}'.format(query), channel)
        else:
            bot.post_image(image=token.logo_url, animated=False, channel=channel)

    @property
    def usage(self):
        return '{}{} <token> - Show token logo'.format(self.prefix, self.name)


class TokenSearchCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
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

            bot.post_reply(search_result, channel)
        except (IndexError, ValueError):
            bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <query> - Search for a token'.format(self.prefix, self.name)


class TokenUSDCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        try:
            token = api.search_token(args[0])
            if token is None:
                error = 'Sorry, I couldn\'t find *{}* on tokenMarketCap.'.format(args[0])
                bot.post_message(error, channel)
            else:
                message = '{} 1 {} = *${:.2f}*'.format(stringformat.emoji('dollar'), token.symbol.upper(), token.price)
                bot.post_message(message, channel)
        except (IndexError, ValueError):
                bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <token> - Convert <token> to USD'.format(self.prefix, self.name)


class TokenConvertCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        try:
            amount = args[0]
            from_token = api.search_token(args[1])
            to_token = api.search_token(args[2])
            converted_amount = (float(amount) * from_token.price) / to_token.price
            message = '{} {} {} = *{:.8f} {}*'.format(stringformat.emoji('dollar'), amount, from_token.symbol.upper(), converted_amount, to_token.symbol.upper())
            bot.post_reply(message, channel)
        except (IndexError, ValueError):
            bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <amount> <from> <to> - Convert between tokens'.format(self.prefix, self.name)


class TokenCompareCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        try:
            token1 = api.search_token(args[0])
            token2 = api.search_token(args[1])

            if token1 is None:
                error = 'Sorry, I couldn\'t find *{}* on tokenMarketCap, or missing MCAP.'.format(args[0])
                bot.post_reply(error, channel)
                return
            if token2 is None:
                error = 'Sorry, I couldn\'t find *{}* on tokenMarketCap, or missing MCAP.'.format(args[1])
                bot.post_reply(error, channel)
                return

            bot.post_message(stringformat.token_compared_summary(token1, token2), channel)
        except (IndexError, ValueError):
            bot.post_reply('Usage: {}'.format(self.usage), channel)

    @property
    def usage(self):
        return '{}{} <token1> <token2> - Compare two tokens'.format(self.prefix, self.name)


class MarketCapitalizationCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        mcap_now = api.get_mcap()
        mcap_db = db.MarketCapitalizationDB()
        mcap_prev = mcap_db.get_latest()
        mcap_db.insert(mcap_now)

        change = stringformat.percent(num=((mcap_now.mcap_usd - mcap_prev.mcap_usd) / mcap_now.mcap_usd) * 100, emo=False)
        adj = ''
        if change > 0:
            adj = stringformat.emoji('rocket')
            prefix = '+'
        elif change < 0:
            adj = stringformat.emoji('skull')
            prefix = ''

        if adj:
            text = 'Total Market Cap *{}{}* since last check, *${}*. {}'.format(prefix, change, stringformat.large_number(mcap_now.mcap_usd), adj)
        else:
            text = 'Total Market Cap unchanged, *${}*. {}'.format(stringformat.large_number(mcap_now.mcap), stringformat.emoji('carlos'))

        bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Show a breakdown of total mcap'.format(self.prefix, self.name)


class ICOCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        token = api.search_token(args[0])
        if token is None:
            error = 'Sorry, I couldn\'t find *{}* on tokenMarketCap.'.format(args[0])
            bot.post_message(error, channel)
            return

        ico_text = api.get_ico_text(token)
        if ico_text:
            bot.post_message(ico_text, channel)
        else:
            text = 'Sorry, I couldn\'t find *{}* on ICO Drops.'.format(token.id)
            bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} <token> - Get ICO info'.format(self.prefix, self.name)


class TokenWebpageCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        query = args[0].lower()
        token = api.search_token(query)
        if token is None:
            bot.post_message('Could not find webpage for {}'.format(query), channel)
        else:
            bot.post_message(token.url, channel)

    @property
    def usage(self):
        return '{}{} <token> - Link to token webpage'.format(self.prefix, self.name)


class AirdropsCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        airdrops = api.get_airdrops()
        if len(airdrops) > 0:
            bot.post_message(stringformat.airdrops_summary(airdrops), channel)
        else:
            bot.post_message("*No upcoming airdrops!*", channel)

    @property
    def usage(self):
        return '{}{} - List of upcoming airdrops'.format(self.prefix, self.name)


class TopMCAPCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        token_db = db.TokenDB()
        tokens = api.get_top_tokens(limit=200)

        text = '*tokens (20 from top 300, by weekly mcap growth) {}:*\n'.format(stringformat.emoji('charts'))
        mcaps = []
        for token in tokens:
            summary = token_db.get_mcaps(token.id)
            if summary is not None:
                mcaps.append(summary)

        i = 1
        sorted_mcaps = sorted(mcaps, key=attrgetter('pct_week'), reverse=True)[:20]
        for m in sorted_mcaps:
            text += '    {}. *{}*: {} (W:{}, M:{})\n'.format(i, m.name, m.now, stringformat.percent(m.pct_week, emo=False), stringformat.percent(m.pct_month, emo=False))
            i += 1

        bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - List top 20 mcap tokens'.format(self.prefix, self.name)


class TwitterCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        twitter_db = db.TwitterDB()

        # handle add/del/list functions
        try:
            if args[0].lower() == 'add':
                twitter_db.track(args[1])
                message = '*Added Twitter user {} to watch list.*'.format(args[1])
                bot.post_reply(message, channel)
                return
            elif args[0].lower() == 'del':
                reddit_db.untrack(args[1])
                message = '*Removed Twitter user {} to watch list.*'.format(args[1])
                bot.post_reply(message, channel)
                return
            elif args[0].lower() == 'list':
                twitters = twitter_db.get_tracked()
                message = '*Currently watching these Twitters accounts (%s total):*\n\n' % len(twitters)
                message += ', '.join(twitters)
                bot.post_message(message, channel)
                return
        except IndexError:
            pass

        users = twitter_db.get_tracked()
        followers = []
        for user in users:
            subscribers = twitter_db.get_subscribers(user)
            if subscribers is not None:
                followers.append(subscribers)
        i = 1
        sorted_followers = sorted(followers, key=attrgetter('pct_week'), reverse=True)[:20]
        text = '*Twitter users (top 20, by weekly growth) {}:*\n'.format(stringformat.emoji('charts'))
        for s in sorted_followers:
            text += '    {}. *{}*: {} (W: {}, M: {})\n'.format(i, s.name, s.now, stringformat.percent(s.pct_week, emo=False), stringformat.percent(s.pct_month, emo=False))
            i += 1

        bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - [add|del <user>] - Add or list followers'.format(self.prefix, self.name)


class RedditCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        reddit_db = db.RedditDB()

        # handle add/del/list functions
        try:
            if args[0].lower() == 'add':
                subreddit = args[1]
                reddit_db.track(subreddit)
                message = '*Added subreddit {} to watch list.*'.format(subreddit)
                bot.post_message(message, channel)
                return
            elif args[0].lower() == 'del':
                subreddit = args[1]
                reddit_db.untrack(subreddit)
                message = '*Removed subreddit {} to watch list.*'.format(subreddit)
                bot.post_message(message, channel)
                return
            elif args[0].lower() == 'list':
                subreddits = reddit_db.get_tracked()
                message = '*Currently watching these subreddits (%s total):*\n\n' % len(subreddits)
                message += ', '.join(subreddits)
                bot.post_message(message, channel)
                return
        except IndexError:
            pass

        tracked_subreddits = reddit_db.get_tracked()
        subs = []
        for tracked_subreddit in tracked_subreddits:
            subscribers = reddit_db.get_subscribers(tracked_subreddit)
            if subscribers is not None:
                subs.append(subscribers)
        i = 1
        sorted_subs = sorted(subs, key=attrgetter('pct_week'), reverse=True)[:20]
        text = '*Reddit communities (top 20, by weekly growth) {}:*\n'.format(stringformat.emoji('charts'))
        for s in sorted_subs:
            text += '    {}. *{}*: {} (W: {}, M: {})\n'.format(i, s.name, s.now, stringformat.percent(s.pct_week, emo=False), stringformat.percent(s.pct_month, emo=False))
            i += 1

        bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - [add|del <subreddit>] - Add or list subscribers'.format(self.prefix, self.name)


class MarketWatchCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
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

        return_url = 'https://tokenmarketcap.com/charts/'
        text = '*{}* Total Market Cap *{}{}%* in {} seconds, *${}!*\n\n{}'.format(t, prefix, change, interval, stringformat.large_number(mcap_now.mcap_usd), return_url)
        bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows large changes in the market'.format(self.prefix, self.name)


class MoonWatchCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        eth = api.search_token('ethereum')
        btc = api.search_token('bitcoin')
        top_tokens = api.get_top_tokens(limit=300)
        tokens = [token for token in top_tokens if token.volume_24h >= 500000]
        for token in tokens:
            text = '*{}* ({}, #{}) *+{:.2f}%* in the last hour, trading at *${:.2f}*. BTC ${:.2f}, ETH ${:.2f}. %{}'.format(
                token.name, token.symbol, token.rank, token.percent_change_1h,
                token.price, btc.price, eth.price, stringformat.emoji('rocket'))
            bot.post_message(text, channel)

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
            bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows what tokens are mooning'.format(self.prefix, self.name)


class RankWatchCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
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
            bot.post_message(text, channel)

    @property
    def usage(self):
        return '{}{} - Shows what tokens are climbing the ranks'.format(self.prefix, self.name)


class AbstractRandomImageCommand(AbstractCommand):
    @property
    def images(self):
        return []

    def invoke(self, bot, channel, args):
        image = random.choice(self.images)
        bot.post_image(image=image, animated=image.endswith('.gif'), channel=channel)


class FOMOCommand(AbstractRandomImageCommand):
    @property
    def images(self):
         return [
            'http://recruitingdaily.com/wp-content/uploads/sites/6/2017/10/fomo1.jpg',
            'https://4.bp.blogspot.com/-AlE0-SaJD9o/VxQa79mwrQI/AAAAAAABp4g/wLAX-ziiVFACgL-EC5aFJI4NNFYdfhfigCLcB/s1600/FOMO.png',
            'http://www.fomofestival.com.au/wp-content/uploads/2017/07/logo.png',
            'https://smartliving365.com/wp-content/uploads/2014/07/FOMO.jpg',
            'https://image.slidesharecdn.com/dontfightthefomo-170213055538/95/dont-fight-the-fomo-6-638.jpg?cb=1487025166',
            'https://victimtocharm.files.wordpress.com/2015/03/fomo-like-a-mofo.jpg?w=640',
            'https://d1qb2nb5cznatu.cloudfront.net/startups/i/4111244-7522ae6e53f25cf0e01ce9c9479bf3c6-medium_jpg.jpg?buster=1494303361',
            'http://www.2uomaha.org/wp-content/uploads/2013/10/YOLO-FOMO.png',
            'http://lovemindbodyheart.com/wp-content/uploads/2016/06/do-i-have-fomo-940x675.jpg',
            'https://s3.amazonaws.com/ns.images/newspring/collection/series_fuse/web.fightingfomo_promo.2x1.jpg',
            'https://i.amz.mshcdn.com/lUiSMH_1GICPM2TblSbwtCt09BI=/950x534/filters:quality(90)/2013%2F07%2F09%2F81%2FSocialNetwo.3f53a.jpg',
        ]

    @property
    def usage(self):
        return '{}{} - When you have that FOMO'.format(self.prefix, self.name)


class FUDCommand(AbstractRandomImageCommand):
    @property
    def images(self):
        return [
            'https://cdn-images-1.medium.com/max/827/1*ulMcUA-Kmbk5vBw3vIobVw.png',
            'https://www.smallcapasia.com/wp-content/uploads/2017/09/crypto-lingo.jpg',
            'https://res.cloudinary.com/teepublic/image/private/s--tvWB4gBj--/t_Preview/b_rgb:ffffff,c_limit,f_jpg,h_630,q_90,w_630/v1516580235/production/designs/2297248_0.jpg',
            'http://cdn.shopify.com/s/files/1/2696/8750/articles/FUD_1200x1200.jpg?v=1522260095',
            'https://cdn-images-1.medium.com/max/1600/1*m4_jtyjXtpaHqUSWvSf0hQ.png',
            'https://i.redd.it/qo5nintb93dz.gif',
            'https://media1.tenor.com/images/28953eb0da0e6dcbaa270a491c2881d2/tenor.gif?itemid=4712571',
            'https://i.kinja-img.com/gawker-media/image/upload/t_original/rnhmsghfmdzpprsfvcfu.gif'
        ]

    @property
    def usage(self):
        return '{}{} - When you suffer from FUD'.format(self.prefix, self.name)


class HODLCommand(AbstractRandomImageCommand):
    @property
    def images(self):
        return [
            'http://i0.kym-cdn.com/photos/images/newsfeed/001/325/560/cbc.jpg',
            'https://i.redd.it/23hgyh92wtaz.jpg',
            'https://i.imgur.com/vWUqfc1.jpg',
            'http://i.imgur.com/Gr4I4sM.jpg',
            'http://i0.kym-cdn.com/entries/emojis/original/000/024/987/hodlittt.jpg',
            'https://i.redd.it/h7ctfzwkplgz.jpg',
            'https://res.cloudinary.com/teepublic/image/private/s--9n6OmwoI--/t_Preview/b_rgb:191919,c_limit,f_jpg,h_630,q_90,w_630/v1505698045/production/designs/1909343_1.jpg',
            'https://i.redd.it/taldvguo6jfz.jpg',
            'https://i.redd.it/fvh3ibzxz8kz.jpg'
        ]

    @property
    def usage(self):
        return '{}{} - When you need to hear that voice of reason'.format(self.prefix, self.name)


class CarlosCommand(AbstractRandomImageCommand):
    @property
    def images(self):
        return [
            'https://i.warosu.org/data/biz/img/0066/59/1516312521744.gif',
            'https://everipedia-storage.s3-accelerate.amazonaws.com/ProfilePics/carlos-matos__02520.gif',
            'https://thumbs.gfycat.com/PleasedEducatedGalah-size_restricted.gif',
            'https://thumbs.gfycat.com/QueasyPlaintiveAmberpenshell-max-1mb.gif',
            'https://thumbs.gfycat.com/SecondaryDistinctCapybara-max-1mb.gif',
            'https://thumbs.gfycat.com/IllfatedDismalAracari-size_restricted.gif',
            'https://media1.tenor.com/images/df4fc55538e36393840781b8531486da/tenor.gif',
            'https://media.tenor.com/images/8e52d994707190980f71d1867b498257/tenor.gif',
            'https://thumbs.gfycat.com/DelayedSillyImpala-size_restricted.gif',
            'https://thumbs.gfycat.com/MeaslySpecificHarrierhawk-size_restricted.gif'
        ]

    @property
    def usage(self):
        return '{}{} - Bitconnneeeeeeeeeect!'.format(self.prefix, self.name)


class RackleCommand(AbstractRandomImageCommand):
    @property
    def images(self):
        return [
            'https://media.giphy.com/media/4PUj9Ueww5tlrhC8ET/giphy.gif',
            'https://media.giphy.com/media/9Dg89jzSNeojyGDCpg/giphy.gif',
            'https://media.giphy.com/media/hTEtcqdYpadJwnTPLo/giphy.gif',
            'https://media.giphy.com/media/fs9B75LDKNXdkHASCB/giphy.gif',
        ]

    @property
    def usage(self):
        return '{}{} - The Crazy Racklehahn'.format(self.prefix, self.name)


class YesNoCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        bot.post_reply(random.choice(['Yes.', 'No.']), channel)

    @property
    def usage(self):
        return '{}{} - For moments of unvertainty'.format(self.prefix, self.name)


class DicerollCommand(AbstractCommand):
    def invoke(self, bot, channel, args):
        bot.post_reply(random.choice(['1', '2', '3', '4', '5', '6']), channel)

    @property
    def usage(self):
        return '{}{} - Throw 1d6'.format(self.prefix, self.name)

