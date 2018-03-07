#!/usr/bin/env python

from uuid import uuid4
import re
from telegram.utils.helpers import escape_markdown
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent, ParseMode
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import logging
import math
import random
import datetime
from bs4 import BeautifulSoup
from operator import itemgetter

from hodlcore import api
from hodlcore import model
from hodlcore import db
from hodlcore import stringformat

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def ico(bot, update, args):
    token_id = args[0]
    ico_text = api.get_ico_text(token_id)
    if ico_text:
        bot.send_message(chat_id=update.message.chat_id, text=ico_text, parse_mode=ParseMode.MARKDOWN)
    else:
        text = 'Sorry, I couldn\'t find *%s* on ICO Drops.'.format(token_id)
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def search(bot, update, args):
    query = args[0].lower()
    tokens = api.search_tokens(search=query, limit=10000)
    i = 0
    for token in tokens:
        matches.append('{}. ID: *{}*, Name: {} ({}), rank #{})'.format(i, token.rank, token.id, token.name, token.symbol))
        i += 1
    if len(tokens) > 0:
        search_result = 'Found *{}* match(es):\n{}'.format(len(tokens), '\n'.join(matches))
    else:
        search_result = 'Sorry, *0 matches* for query: {}'.format()
    
    update.message.reply_text(search_result, parse_mode=ParseMode.MARKDOWN)


def webpage(bot, update, args):
    query = args[0].lower()
    token = api.search_token(query)
    if not token:
	    bot.send_message(chat_id=update.message.chat_id, text='Could not find webpage for {}'.format(query), parse_mode=ParseMode.MARKDOWN)
    bot.send_message(chat_id=update.message.chat_id, text=token.url, parse_mode=ParseMode.MARKDOWN)


def mcap(bot, update):
    mcap_now = api.get_market_data().mcap
    mcap_db = db.MarketCapitalizationDB()
    mcap_prev_tuple = db.get_latest()
    mcap_prev = model.MarketCapitalization(mcap_prev_tuple[0], mcap_prev_tuple[1])

    mcap_db.insert(mcap_now)

    change = stringformat.percent(num=((mcap_now.mcap-mcap_prev.mcap)/mcap_now.mcap)*100, emoji=False)
    adj = ''
    if change > 0:
        adj = stringformat.emoji['rocket']
        prefix = '+'
    elif change < 0:
        adj = stringformat.emoji['skull']
        prefix = ''
    
    if adj:    
        text = u'Total Market Cap *{}{:.2f}* since last check, *$%s*. %s' % (prefix, change, stringformat.large_number(mcap_now.mcap), adj)
    else:
        text = u'Total Market Cap unchanged, *$%s*. %s' % (millify(mcap_now.mcap, short=True), emoji['carlos'])
        
    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def airdrops(bot, update):
    airdrops_text = api.get_airdrops_text()
    if airdrops_text:
        bot.send_message(chat_id=update.message.chat_id, text=airdrops_text, parse_mode=ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="*No upcoming airdrops!*", parse_mode=ParseMode.MARKDOWN)


def coinmarketcap(bot, update, args):
    token_db = db.TokenDB()
    tokens = token_db.get_tokens()

    text = '*Coins (20 from top 300, by weekly mcap growth) %s:*\n' % stringformat.emojis['charts']
    mcaps = []
    for token in tokens:
        d = token_db.get_mcaps(token)
        try:
            d = {
                'name': coin,
                'now': float(d['now']),
                'diff_today': d['now'] - d['today'],
                'pct_today': ((d['now']/float(d['today']))-1)*100,
                'diff_week': d['now'] - d['last_week'],
                'pct_week':  ((d['now']/float(d['last_week']))-1)*100,
                'diff_month': d['now'] - d['last_month'],
                'pct_month': ((d['now']/float(d['last_month']))-1)*100
            }
        except TypeError:
            # Not in db yet.
            d = {
                'name': sr,
                'now': 0,
                'diff_today': 0,
                'pct_today': 0.0,
                'diff_week': 0,
                'pct_week':  0.0,
                'diff_month': 0,
                'pct_month': 0.0
            }
        mcaps.append(d)
        # logger.info('reddit dict: %s' % d)
        
    i = 1
    sorted_mcaps = sorted(mcaps, key=itemgetter('pct_week'), reverse=True)
    for m in sorted_mcaps:
        text += '    %s. *%s*: *%s* (*W:%s*, *M:%s*)\n' % (
            i, m['name'], float(m['now']), pct(m['pct_week'], emo=False), pct(m['pct_month'], emo=False))
        i += 1

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def twitter(bot, update, args):
    twitter_db = db.TwitterDB()

    # handle add/del/list functions
    try:
        if args[0].lower() == 'add':
            twitter_db.track(args[1])
            message = '*Added Twitter user {} to watch list.*'.format(args[1])
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'del':
            reddit_db.untrack(args[1])
            message = '*Removed Twitter user {} to watch list.*'.format(args[1])
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'list':
            twitters = twitter_db.get_tracked()
            message = '*Currently watching these Twitters accounts (%s total):*\n\n' % len(twitters) 
            message += ', '.join(twitters)
            bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
            return
    except IndexError:
        pass

    users = twitter_db.get_tracked()

    text = '*Twitter users (top 20, by weekly growth) %s:*\n' % stringformat.emojis['charts']

    followers = []
    for user in users:
        followers.append(twitter_db.get_subscribers(user))
        
    i = 1
    sorted_followers = sorted(followers, key=itemgetter('pct_week'), reverse=True)[:20]
    for s in sorted_followers:
        text += '    %s. *%s*: %s (W:%s, M:%s)\n' % (
            i, s['name'], int(s['now']), pct(s['pct_week'], emo=False), pct(s['pct_month'], emo=False))
        i += 1

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def reddit(bot, update, args):
    reddit_db = db.RedditDB()

    # handle add/del/list functions
    try:
        if args[0].lower() == 'add':
            subreddit = args[1]
            reddit_db.track(subreddit)
            message = '*Added subreddit {} to watch list.*'.format(subreddit)
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'del':
            subreddit = args[1]
            reddit_db.untrack(subreddit)
            message = '*Removed subreddit {} to watch list.*'.format(subreddit)
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'list':
            subreddits = reddit_db.get_tracked()
            message = '*Currently watching these subreddits (%s total):*\n\n' % len(subreddits) 
            message += ', '.join(subreddits)
            bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
            return
    except IndexError:
        pass

    tracked_subreddits = reddit_db.get_tracked()
    
    text = '*Reddit communities (top 20, by weekly growth) {}:*\n'.format(stringformat.emojis['charts'])
    subs = []
    for tracked_subreddit in tracked_subreddits:
        subs.append(reddit_db.get_subscribers())
    i = 1
    sorted_subs = sorted(subs, key=itemgetter('pct_week'), reverse=True)[:20]
    for s in sorted_subs:
        text += '    {}. *{}*: {} (W:{}, M:{})\n'.format(i, s['name'], int(s['now']), pct(s['pct_week'], emo=False), pct(s['pct_month'], emo=False))
        i += 1

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def usd(bot, update, args):
    token = api.get_token(args[0])
    if not token:
		error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return    
    message = '{} 1 {} = *$({:.2f}*'.format(stringformat.emojis['dollar'], token.symbol.upper(), token.price_usd)
    bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


def convert(bot, update, args):
    amount = args[0]
    from_coin = api.get_token(args[1])
    to_coin = api.get_token(args[2])
    new_coins = (float(amount) * from_coin.price_usd) / to_coin.price_usd
    text = '%s %s %s = *%.8f %s*' % (stringformat.emojis['dollar'], amount, from_coin.symbol.upper(), new_coins, to_coin.symbol.upper())
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def stats(bot, update, args):
    # No args means global stats
    if len(args) == 0:
        mcap = api.get_mcap()        
        message = '*Global data {}:*'.format(stringformat.emojis['chart'])
        message += '*Total Market Cap (USD):* ${}'.format(mcap.total_market_cap_usd)
        message += '*Total 24h Volume (USD):* ${}'.format(mcap.volume_usd_24h)
        message += '*BTC Dominance:* {}'.format(mca.bitcoin_percentage_of_market_cap)
        bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)
        return

    token = get_coin_id(args[0])
    if not token:
		error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return    
    s += '*Rank:* #{}'.format(token.rank)
    s += '*Price (USD):* ${}'.format(token.price_usd)
    s += '*Price (BTC):* ${}'.format(token.price_btc)
    s += '*24h Volume:* ${}'.format(token.volume_usd_24h)
    s += '*Market Cap:* ${}'.format(token.mcap)
    s += '*Avail. Supplu:* ${}'.format(token.available_supply)
    s += '*Total Supplu:* ${}'.format(token.total_supply)
    s += '*Max Supply:* ${}'.format(token.max_supply)
    s += '*Change (1h):* ${}'.format(token.percent_change_1h)
    s += '*Change (12h):* ${}'.format(token.percent_change_12h)
    s += '*Change (7d):* ${}'.format(token.percent_change_7d)
    bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)


def compare(bot, update, args):
    token1 = api.get_token(args[0])
    token2 = api.get_token(args[1])

    if not token1:
    	error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'.format(args[0])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return
    if not token2:
    	error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'format(args[1])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    mcap_factor = token1.mcap / token2.mcap
    mcap_price = mcap_factor * token2.price_usd
    vol_factor = token1.volume_24h / token2.volume_24h

    s = '*{} {} {}*:'.format(token1.name, stringformat.emojis['vs'], token2.name)
    s += '*Rank:* #{} vs #{}'.format(token1.rank, token2.rank)
    s += '*Price (USD):* ${} vs ${}'.format(token1.price_usd, token2.price_usd)
    s += '*Price (BTC):* ${} vs ${}'.format(token1.price_btc, token2.price_btc)
    s += '*24h Volume:* ${} vs ${}'.format(token1.volume_usd_24h, token2.volume_usd_24h)
    s += '*Market Cap:* ${} vs ${}'.format(token1.mcap, token2.mcap)
    s += '*Avail. Supplu:* ${} vs ${}'.format(token1.available_supply, token2.available_supply)
    s += '*Total Supplu:* ${} vs ${}'.format(token1.total_supply, token2.total_supply)
    s += '*Max Supply:* ${} vs ${}'.format(token1.max_supply, token2.max_supply)
    s += '*Change (1h):* ${} vs ${}'.format(token1.percent_change_1h, token2.percent_change_1h)
    s += '*Change (12h):* ${} vs ${}'.format(token1.percent_change_12h, token2.percent_change_12h)
    s += '*Change (7d):* ${} vs ${}'.format(token1.percent_change_7d, token2.percent_change_7d)    
    s += '*{} has {:.2f}x the 24h volume of {}.*'.format(token1.name, vol_factor, token2.name)
    s += '*{} has {:.2f}x the 24h volume of {}.*'.format(token1.name, vol_factor, token2.name)
    s += '*If {} had the market cap of {}, the USD price would be: ${} ({:.1f}x)*'.format(token1.name, token2.name, mcap_price, mcap_factor)

    bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)


def set_marketwatch_timer(bot, update, args, job_queue, chat_data):
    """Add a job to the queue."""
    chat_id = update.message.chat_id

    if args[0].lower() == 'stop':
        if 'job' not in chat_data:
            update.message.reply_text('You have no active timer.')
            return

        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']

        update.message.reply_text('*Marketwatch stopped.*', parse_mode=ParseMode.MARKDOWN)
        return

    try:
        # args[0] should contain the time for the timer in seconds
        threshold = float(args[0])
        interval = int(args[1])
        if interval < 0:
            update.message.reply_text('*Sorry we can not go back to future!*', parse_mode=ParseMode.MARKDOWN)
            return
        # Add job to queue
        logger.info('starting marketwatch, interval: %s, threshold: %s%%.' % (interval, threshold))
        job = job_queue.run_repeating(marketwatch, interval, context=chat_id)
        job._threshold = threshold
        job._interval = interval
        chat_data['job'] = job

        update.message.reply_text('*Marketwatch successfully started, interval: %s, threshold: %s%%.*' % (interval, threshold), parse_mode=ParseMode.MARKDOWN)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /marketwatch <threshold (%)> <interval (s)>')


def marketwatch(bot, job):
    cmc_api = 'https://api.coinmarketcap.com/v1/global/?convert=USD'
    r = requests.get(cmc_api)
    mcap = float(r.json()['total_market_cap_usd'])
    mcap_prev = mcap
    fn = 'data/mcap-major-mov.data'

    try:
        f = open(fn, 'r')
        mcap_prev = float(f.readline().strip())
        f.close()
    except IOError:
        f = open(fn, 'w')
        f.write('%f' % mcap)
        f.close()
    f = open(fn, 'w')
    f.write('%f' % mcap)
    f.close()

    change = ((mcap-mcap_prev)/mcap)*100
    logger.info('old mcap: %.2f, new mcap: %.2f, threshold: %.1f, change: %.8f' % (mcap_prev, mcap, job._threshold, change))

    # Do nothing if change is not significant.
    if not abs(change) > job._threshold:
        return

    if change > 0:
        t = 'Double rainbow!%s%s' % (stringformat.emojis['rainbow'], stringformat.emojis['rainbow'])
        adj = stringformat.emojis['rocket']
        prefix = '+'
    elif change < 0:
        t = 'ACHTUNG!%s' % stringformat.emojis['collision']
        adj = stringformat.emojis['poop']
        prefix = ''

    return_url = 'https://coinmarketcap.com/charts/'
    text = u'*%s* Total Market Cap *%s%.2f%%* in %s seconds, *$%s!*\n\n%s' % (t, prefix, change, job._interval, millify(mcap, short=True), return_url)
    bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)


def set_moonwatch_timer(bot, update, args, job_queue, chat_data):
    """Add a job to the queue."""
    chat_id = update.message.chat_id

    if args[0].lower() == 'stop':
        if 'job' not in chat_data:
            update.message.reply_text('You have no active timer.')
            return

        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']

        update.message.reply_text('*Moonwatch stopped.*', parse_mode=ParseMode.MARKDOWN)
        return

    try:
        # args[0] should contain the time for the timer in seconds
        threshold = float(args[0])
        interval = int(args[1])
        if interval < 0:
            update.message.reply_text('*Sorry we can not go back to future!*', parse_mode=ParseMode.MARKDOWN)
            return
        # Add job to queue
        logger.info('starting moonwatch, interval: %s, threshold: %s%%.' % (interval, threshold))
        job = job_queue.run_repeating(moonwatch, interval, context=chat_id)
        job._threshold = threshold
        job._interval = interval
        chat_data['job'] = job

        update.message.reply_text('*Moonwatch successfully started, interval: %s, threshold: %s%%.*' % (interval, threshold), parse_mode=ParseMode.MARKDOWN)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /moonwatch <threshold (%)> <interval (s)>')


def moonwatch(bot, job):
    logger.info('running moonwatch check')

    top_tokens = api.get_top_tokens(limit=300)
    tokens = []
    volume_threshold = 500000
    for token in top_tokens:
        if token.volume_usd_24h >= volume_threshold:
            tokens.append(coin)

    for token in tokens:
        # Change in price
        if not token.percent_change_1h >= job._threshold:
            continue
        text = u'*%s* (%s, #%s) *+%.2f%%* in the last hour, trading at *$%.2f*. BTC $%.2f, ETH $%.2f. %s' % (
            token.name, token.symbol, token.rank, token.percent_change_1h,
            token.price_usd, btc_usd, eth_usd, stringformat.emojis['rocket'])
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)

        # Change in volume
        db = TokenDB()
        volumes = db.get_volumes(token)
        if not volumes:
            continue
        pct_change = (tokehn.volume_usd_24h] / volumes['last']) - 1) * 100
        if pct_change >= 80 and \
            token.volume_usd_24h > volumes['a_day_ago'] and \
            token.volume_usd_24h > volumes['week_avg']: #job._threshold:
            text = '*24h volume* of *%s* (%s, #%s) increased by *%.2f%%* to *$%d*. Last $%d, yesterday $%d, week avg $%d. %s' % (
                token.name, token.symbol, token.rank, pct_change, token.volume_usd_24h,
                volumes['last'], volumes['a_day_ago'], volumes['week_avg'], stringformat.emojis['fire'])
            logger.info('%s is trading %.2f%% above last check' % (token.id, pct_change))
            bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)


def rankwatch(bot, job):
    logger.info('running rankwatch check')
    top_tokens = api.get_top_tokens(limit=200)    
    volume_threshold = 500000    

    # Looking for changes in ranks
    db = TokenDB()
    climbers = []
    for token in top_tokens:
        ranks = db.get_ranks(token)
        if not ranks:
            continue

        if ranks['now'] < ranks['last'] and \
           ranks['now'] < ranks['last_week'] and \
           ranks['now'] < ranks['today'] and \
           ranks['is_ath'] and \
           coin.volume_usd_24h >= volume_threshold:
            logger.info('ranks for %s: %s' % (token.id, ranks))
            climber = {
                'name': token.name,
                'symbol': token.symbol,
                'rank': ranks['now'],
                'ranks_day': ranks['today'] - ranks['now'],
                'ranks_week': ranks['last_week'] - ranks['now'],
                'ranks_month': ranks['last_month'] - ranks['now'],
                'volume': token.volume_usd_24h,
            }
            climbers.append(climber)
        else:
            continue

    if climbers:
        sorted_climbers = sorted(climbers, key=itemgetter('ranks_day'), reverse=True)
        text = '*CoinMarketCap rank climbers (w/m):*\n'
        for climber in sorted_climbers:
            #            - 6/12/24 ranks, #34 ZClassic (ZCL)
            text += '    -%s*%s* (%s/%s): *%s* (%s, #%s)\n' % (
                stringformat.emojis['triangle_up'], climber['ranks_day'], climber['ranks_week'], climber['ranks_month'],
                climber['name'], climber['symbol'], climber['rank'])
        text += '\nShowing All Time High ranks only.%s' % stringformat.emojis['fire'] 
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)



