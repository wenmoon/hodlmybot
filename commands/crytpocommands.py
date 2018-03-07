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
    if not coin:
        return_url = 'Could not find webpage for {}'.format(query)
    else     
        return_url = token.url
    bot.send_message(chat_id=update.message.chat_id, text=return_url, parse_mode=ParseMode.MARKDOWN)


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
    db = 'data/twitter.db'

    # create connection
    c = sqlite3.connect(db)

    add_user = None
    try:
        if args[0].lower() == 'add':
            add_user = args[1]
            c.execute('INSERT INTO twitter_accounts(user) VALUES (?)', (add_user,))
            c.commit()
            s = '*Added Twitter user %s to watch list.*' % add_user
            update.message.reply_text(s, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'del':
            add_user = args[1]
            c.execute('DELETE FROM twitter_accounts WHERE user=? LIMIT 1', (add_user,))
            c.commit()
            s = '*Removed Twitter user %s from watch list.*' % add_user
            update.message.reply_text(s, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'list':
            l = sorted([x[0] for x in c.execute('SELECT user FROM twitter_accounts')], key=lambda s: s.lower())
            s = '*Currently watching these Twitter accounts (%s total):*\n\n' % len(l) 
            s += ', '.join(l)
            bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)
            return
    except IndexError:
        pass

    users = []
    for user in c.execute('SELECT * FROM twitter_accounts'):
        users.append(user[0])

    text = '*Twitter users (top 20, by weekly growth) %s:*\n' % emoji['charts']

    followers = []
    for user in users:

        # last count
        now = c.execute(
            'SELECT * FROM followers WHERE user=? ORDER BY timestamp DESC', (user,)
        ).fetchone()

        # count today
        today = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") AND user=? ORDER BY timestamp ASC', (user,)
        ).fetchone()
        
        # count last week
        last_week = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") AND user=? ORDER BY timestamp ASC', (user,)
        ).fetchone()
        
        # count last month
        last_month = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") AND user=? ORDER BY timestamp ASC', (user,)
        ).fetchone()

        try:
            d = {
                'name': user,
                'now': float(now[2]),
                'diff_today': now[2] - today[2],
                'pct_today': ((now[2]/float(today[2]))-1)*100,
                'diff_week': now[2] - last_week[2],
                'pct_week':  ((now[2]/float(last_week[2]))-1)*100,
                'diff_month': now[2] - last_month[2],
                'pct_month': ((now[2]/float(last_month[2]))-1)*100
            }
        except (TypeError, ZeroDivisionError) as e:
            # Not in db yet.
            d = {
                'name': user,
                'now': 0,
                'diff_today': 0,
                'pct_today': 0.0,
                'diff_week': 0,
                'pct_week':  0.0,
                'diff_month': 0,
                'pct_month': 0.0
            }
            logger.warning('caught exception: %s' % e)
        followers.append(d)
        
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
        return
    message = '{} 1 {} = *$({:.2f}*'.format(stringformat.emojis['dollar'], token.symbol.upper(), token.price_usd)
    bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


def stats(bot, update, args):
    # No args means global stats
    if len(args) == 0:
        mcap = api.get_mcap()
        
        message = '''*Global data {}}:*
            *Total Market Cap (USD):* $%(total_market_cap_usd)s
            *Total 24h Volume (USD):* $%(total_24h_volume_usd)s
            *BTC Dominance:* %(bitcoin_percentage_of_market_cap)s%%
            *Active Currencies:* %(active_currencies)s
            *Active Assets:* %(active_assets)s
            *Active Markets:* %(active_markets)s'''.format(s)
        bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)
        return

    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=USD'
    try:
         = get_coin_id(args[0])
    except IndexError:

    r = requests.get(cmc_api % ticker)

    stats = {}

    try:
        stats['name'] = r.json()[0]['name']
        stats['symbol'] = r.json()[0]['symbol']
        stats['rank'] = r.json()[0]['rank']
        stats['price_usd'] = float(r.json()[0]['price_usd'])
        stats['price_btc'] = r.json()[0]['price_btc']
        stats['24h_volume_usd'] = millify(r.json()[0]['24h_volume_usd'])
        stats['market_cap_usd'] = millify(r.json()[0]['market_cap_usd'])
        stats['available_supply'] = millify(r.json()[0]['available_supply'])
        stats['total_supply'] = millify(r.json()[0]['total_supply'])
        stats['max_supply'] = millify(r.json()[0]['max_supply'])
        stats['percent_change_1h'] = pct(r.json()[0]['percent_change_1h'])
        stats['percent_change_24h'] = pct(r.json()[0]['percent_change_24h'])
        stats['percent_change_7d'] = pct(r.json()[0]['percent_change_7d'])
        stats['emoji'] = emoji['charts']
    except KeyError:
        error = 'Sorry, I couldn\'t find *%s* on CoinMarketCap.' % args[0]
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    s = u"""*%(name)s* (%(symbol)s) %(emoji)s:
    *Rank #:* %(rank)s
    *Price (USD):* $%(price_usd)s
    *Price (BTC):* %(price_btc)s
    *24h Volume:* $%(24h_volume_usd)s
    *Market Cap:* $%(market_cap_usd)s
    *Avail. Supply:* %(available_supply)s
    *Total Supply:* %(total_supply)s
    *Max Supply:* %(max_supply)s
    *Change (1h):* %(percent_change_1h)s
    *Change (24h):* %(percent_change_24h)s
    *Change (7d):* %(percent_change_7d)s""" % stats

    bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)


def convert(bot, update, args):
    """Send a message when the command /mcap is issued."""
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=USD'

    amount = args[0]
    from_coin = get_coin_id(args[1])
    to_coin = get_coin_id(args[2])

    from_price = requests.get(cmc_api % from_coin).json()[0]['price_usd']
    to_price = requests.get(cmc_api % to_coin).json()[0]['price_usd']
    holdings = float(amount) * float(from_price)
    new_coins = holdings/float(to_price)

    text = '%s %s %s = *%.8f %s*' % (emoji['dollar'], amount, from_coin.upper(), new_coins, to_coin.upper())
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def compare(bot, update, args):
    coin1 = api.get_token(args[0])
    coin2 = api.get_token(args[1])

    stats = {}
    
    r = requests.get(cmc_api % coin1)
    try:
        stats['name1'] = r.json()[0]['name']
        stats['symbol1'] = r.json()[0]['symbol']
        stats['rank1'] = r.json()[0]['rank']
        stats['price_usd1'] = float(r.json()[0]['price_usd'])
        stats['price_btc1'] = r.json()[0]['price_btc']
        stats['24h_volume_usd1'] = millify(r.json()[0]['24h_volume_usd'], short=True)
        stats['volume1'] = float(r.json()[0]['24h_volume_usd'])
        stats['market_cap_usd1'] = millify(r.json()[0]['market_cap_usd'], short=True)
        stats['mcap1'] = float(r.json()[0]['market_cap_usd'])
        stats['available_supply1'] = millify(r.json()[0]['available_supply'], short=True)
        stats['total_supply1'] = millify(r.json()[0]['total_supply'], short=True)
        stats['max_supply1'] = millify(r.json()[0]['max_supply'], short=True)
        stats['percent_change_1h1'] = pct(r.json()[0]['percent_change_1h'])
        stats['percent_change_24h1'] = pct(r.json()[0]['percent_change_24h'])
        stats['percent_change_7d1'] = pct(r.json()[0]['percent_change_7d'])
    except (KeyError, TypeError):
        error = 'Sorry, I couldn\'t find *%s* on CoinMarketCap, or missing MCAP.' % args[0]
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    r = requests.get(cmc_api % coin2)
    try:
        stats['name2'] = r.json()[0]['name']
        stats['symbol2'] = r.json()[0]['symbol']
        stats['rank2'] = r.json()[0]['rank']
        stats['price_usd2'] = float(r.json()[0]['price_usd'])
        stats['price_btc2'] = r.json()[0]['price_btc']
        stats['24h_volume_usd2'] = millify(r.json()[0]['24h_volume_usd'], short=True)
        stats['volume2'] = float(r.json()[0]['24h_volume_usd'])
        stats['market_cap_usd2'] = millify(r.json()[0]['market_cap_usd'], short=True)
        stats['mcap2'] = float(r.json()[0]['market_cap_usd'])
        stats['available_supply2'] = millify(r.json()[0]['available_supply'], short=True)
        stats['total_supply2'] = millify(r.json()[0]['total_supply'], short=True)
        stats['max_supply2'] = millify(r.json()[0]['max_supply'], short=True)
        stats['percent_change_1h2'] = pct(r.json()[0]['percent_change_1h'])
        stats['percent_change_24h2'] = pct(r.json()[0]['percent_change_24h'])
        stats['percent_change_7d2'] = pct(r.json()[0]['percent_change_7d'])
    except (KeyError, TypeError):
        error = 'Sorry, I couldn\'t find *%s* on CoinMarketCap, or missing MCAP.' % args[0]
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    stats['emoji'] = emoji['vs']

    stats['mcap_factor'] = stats['mcap2'] / stats['mcap1']
    stats['mcap_price'] = stats['mcap_factor'] * stats['price_usd1']
    stats['mcap_price'] = '%.2f' % stats['mcap_price']
    stats['vol_factor'] = stats['volume2'] / stats['volume1']

    s = u"""*%(name1)s %(emoji)s %(name2)s*:
    *Rank:* #%(rank1)s vs #%(rank2)s
    *Price (USD):* $%(price_usd1)s vs $%(price_usd2)s
    *Price (BTC):* %(price_btc1)s vs %(price_btc2)s
    *24h Volume:* $%(24h_volume_usd1)s vs $%(24h_volume_usd2)s
    *Market Cap:* $%(market_cap_usd1)s vs $%(market_cap_usd2)s
    *Avail. Supply:* %(available_supply1)s vs %(available_supply2)s 
    *Total Supply:* %(total_supply1)s vs %(total_supply2)s
    *Max Supply:* %(max_supply1)s vs %(max_supply2)s
    *Change (1h):* %(percent_change_1h1)s vs %(percent_change_1h2)s
    *Change (24h):* %(percent_change_24h1)s vs %(percent_change_24h2)s
    *Change (7d):* %(percent_change_7d1)s vs %(percent_change_7d2)s
    
    *%(name2)s has %(vol_factor).2fx the 24h volume of %(name1)s.*

    *If %(name1)s had the market cap of %(name2)s, the USD price would be: $%(mcap_price)s (%(mcap_factor).1fx)*""" % stats

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



