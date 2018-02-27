#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Bot to reply to Telegram messages.
"""

from uuid import uuid4
import re
from telegram.utils.helpers import escape_markdown
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent, ParseMode
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import logging
import math
import requests
import random
import json
import datetime
import sqlite3
from sqlite3 import Error
from bs4 import BeautifulSoup
from operator import itemgetter

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
millnames = ['',' Thousand',' Million',' Billion',' Trillion']
millnames_short = ['','k','m','bn','tn']
    
fomo_pics = [
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

hold_pics = [
    'http://i0.kym-cdn.com/photos/images/newsfeed/001/325/560/cbc.jpg',
    'https://i.redd.it/23hgyh92wtaz.jpg',
    'https://i.imgur.com/vWUqfc1.jpg',
    'http://i.imgur.com/Gr4I4sM.jpg',
    'http://i0.kym-cdn.com/entries/emojis/original/000/024/987/hodlittt.jpg'
]

carlos_gifs = [
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

rackle_gifs = [
    'https://media.giphy.com/media/4PUj9Ueww5tlrhC8ET/giphy.gif',
    'https://media.giphy.com/media/9Dg89jzSNeojyGDCpg/giphy.gif',
    'https://media.giphy.com/media/hTEtcqdYpadJwnTPLo/giphy.gif',
    'https://media.giphy.com/media/fs9B75LDKNXdkHASCB/giphy.gif',
]

fud_pics = [
    'https://cdn-images-1.medium.com/max/827/1*ulMcUA-Kmbk5vBw3vIobVw.png',
]

emoji = {
    'poop':     u'\U0001f4a9',
    'crashing': u'\U0001f4c9',
    'mooning':  u'\U0001f4c8',
    'rocket':   u'\U0001f680',
    'charts':   u'\U0001f4ca',
    'pause':    u'\U000023f8',
    'sleeping':    u'\U0001f634',
    'dollar':      u'\U0001f4b5',
    'triangle_up': u'\U0001f53a',
    'triangle_dn': u'\U0001f53b',
    'apple_green': u'\U0001f34f', # green apple
    'apple_red':   u'\U0001f34e', # red apple
    'pear':        u'\U0001f350', # pear
    'vs':          u'\U0001f19a',
    'squirt':      u'\U0001f4a6',
    'umbrella':    u'\U00002614',
    'fire':        u'\U0001f525',
    'arrow_up':    u'\U00002197',
    'arrow_down':  u'\U00002198',
    'collision':   u'\U0001f4a5',
    'rainbow':     u'\U0001f308',
    'carlos':      u'\U0001f919',
    'skull':       u'\u2620\ufe0f', #U+2620, U+FE0F
}


def millify(n, short=False):
    """ Return human readable large numbers. """
    try:
        n = float(n)
        millidx = max(0,min(len(millnames)-1,
        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
        if short:
            return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames_short[millidx])
        return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
    except TypeError:
        return '?'


def pct(s, emo=True):
    try:
        s = float(s)
        if float(s) > 0:
            if emo:
                s = '%s+%.2f%%' % (emoji['apple_green'], float(s))
            else:
                s = '+%.2f%%' % float(s)
        elif float(s) < 0:
            if emo:
                s = '%s%.2f%%' % (emoji['apple_red'], float(s))
            else:
                s = '%.2f%%' % float(s)
        else:
            if emo:
                s = emoji['pear'] + '+0%'
            else:
                s = '+0%'
    except TypeError:
        logger.warning('wrong type in pct conversion: %s' % type(s))
        s = '-'
        return s
    return s


def get_coin_id(s):
    """ Returns CoinMarketCap ID. """
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=10000'
    r = requests.get(cmc_api).json()
    for token in r:
        if s.lower() == token['id'].lower():
            return token['id']
        elif s.lower() == token['symbol'].lower():
            return token['id']
        elif s.lower == token['name'].lower():
            return token['id']
        
    logger.warning('No coin matched: %s' % s)
    return None


def get_coin_name(s):
    """ Returns CoinMarketCap Name. """
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=10000'
    r = requests.get(cmc_api).json()
    for token in r:
        if s.lower() == token['id'].lower():
            return token['id']
        elif s.lower() == token['symbol'].lower():
            return token['id']
        elif s.lower == token['name'].lower():
            return token['id']
        
    logger.warning('No coin matched: %s' % s)
    return s 


def help(bot, update):
    """Send a message when the command /help is issued."""
    text = """This bot currently supports the following commands:
    Help:
    /help - This help

    Tools:
    /search - Search for coin
    /webpage <coin> - Link to coin webpage
    /mcap - Total market cap
    /usd <coin> - USD value of <coin>
    /stats [<coin>] - Global core metrics or metrics of <coin>
    /ico <coin> - Get ICO info
    /convert <amount> <from coin> <to coin> - Coin conversion
    /compare <coin1> <coin2> - Compare two coins
    
    Watchers:
    /marketwatch [<threshold (%)> <interval (sec)>]|stop - Set threshold and interval for market watcher or stop
    /moonwatch [<threshold (%)> <interval (sec)>]|stop - Set threshold and interval for mooning coins
    
    Intel:
    /airdrops - List of upcoming airdrops
    /reddit [add|del <subreddit> or list] - Add or list Reddit followers
    /twitter [add|del <user> or list] - Add or list Twitter followers
    
    Fun:
    /hodl - Helps you decide whether or not to HODL
    /fomo - When you have FOMO
    /fud - No FUD
    /carlos - CARLOS MATOS!
    /rackle - The Crazy Racklehahn
    /shouldi - Helps you decide
    /diceroll - Throw 1d6"""
    update.message.reply_text(text)


def ico(bot, update, args):
    coin = get_coin_name(args[0])

    url = 'https://icodrops.com/%s'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36'
    }
    r = requests.get(url % coin.lower(), headers=headers)

    soup = BeautifulSoup(r.text, 'lxml')

    rel_sections = soup.find_all('div', 'white-desk ico-desk')
   
    fields = [
        'ticker:',
        'ico token price:',
        'total tokens:',
        'accepts:',
    ]

    entr = []
    for s in rel_sections:
        if not s.find_all('i', 'fa fa-calendar'):
            continue

        ico_info = s.find('div', 'col-12 col-md-6')
        lines = s.find_all('li')
        for line in lines:
            relevant = False
            for f in fields:
                if f in line.text.lower():
                    relevant = True
            if relevant:
                header, value = line.text.split(':')
                line = '*%s*: %s' % (header, value)
                indent = 4 * " "
                entr.append(indent+line)

    # These sections are not always present
    try:
        prices = soup.find('div', 'token-price-list').find_all('li')
        roi = soup.find('div', 'col-12 col-md-6 ico-roi').find_all('li')
        
        # Price list
        price_list = []
        for l in prices:
            indent = 8 * " "
            price_list.append(indent+l.text)

        # Returns on investment
        returns = []
        for l in roi:
            amount = l.find('div', 'roi-amount')
            currency = l.find('div', 'roi-currency')
            indent = 4 * " "
            returns.append(indent+'*Returns %s*: %s' % (currency.text, amount.text))
    except AttributeError:
        prices = None
        roi = None
        price_list = []
        returns = []

    if entr:
        text = '*ICO Information for %s%s:*\n' % (coin, emoji['charts'])
        text += '\n'.join(entr) + '\n'
        if price_list:
            text += '    *Token Price List:*\n' + '\n'.join(price_list) + '\n'
        if returns:
            text += '\n'.join(returns)

        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
    else:
        text = 'Sorry, I couldn\'t find *%s* on ICO Drops.' % coin
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def search(bot, update, args):
    q = args[0].lower()
    
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=10000'
    r = requests.get(cmc_api).json()
    matches = []
    i = 1
    for token in r:
        if q in token['id'].lower():
            matches.append('%s. ID: *%s*, Name: %s (%s), rank #%s)' % (i, token['id'], token['name'], token['symbol'], token['rank']))
            i += 1
        elif q in token['name'].lower():
            matches.append('%s. ID: *%s*, Name: %s (%s), rank #%s)' % (i, token['id'], token['name'], token['symbol'], token['rank']))
            i += 1
        elif q in token['symbol'].lower():
            matches.append('%s. ID: *%s*, Name: %s (%s), rank #%s)' % (i, token['id'], token['name'], token['symbol'], token['rank']))
            i += 1
    if len(matches) > 0:
        s = 'Found *%s* match(es):\n%s' % (len(matches), '\n'.join(matches))
    else:
        s = 'Sorry, *0 matches* for query: %s' % q
    
    update.message.reply_text(s, parse_mode=ParseMode.MARKDOWN)


def webpage(bot, update, args):
    coin_id = get_coin_id(args[0])
    if not coin_id:
        return
    return_url = 'https://coinmarketcap.com/currencies/%s/' % coin_id
    bot.send_message(chat_id=update.message.chat_id, text=return_url, parse_mode=ParseMode.MARKDOWN)


def mcap(bot, update):
    """Send a message when the command /mcap is issued."""
    cmc_api = 'https://api.coinmarketcap.com/v1/global/?convert=USD'
    r = requests.get(cmc_api)
    mcap = float(r.json()['total_market_cap_usd'])
    mcap_prev = mcap
    fn = 'data/mcap-%s.data' % update.message.chat_id

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
    adj = ''
    if change > 0:
        adj = emoji['rocket']
        prefix = '+'
    elif change < 0:
        adj = emoji['skull']
        prefix = ''
    
    if adj:    
        text = u'Total Market Cap *%s%.2f%%* since last check, *$%s*. %s' % (prefix, change, millify(mcap, short=True), adj)
    else:
        text = u'Total Market Cap unchanged, *$%s*. %s' % (millify(mcap, short=True), emoji['carlos'])
        
    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def airdrops(bot, update):
    url = 'https://coindar.org/en/tags/airdrop'
    r = requests.get(url)

    soup = BeautifulSoup(r.text, 'lxml')
    events = soup.find_all('div', 'addeventatc')

    now = datetime.datetime.now()

    text = "*Upcoming Airdrops%s:*\n" % emoji['squirt']
    i = 1
    for e in events:
        airdrop = {
            'start': e.find('span', 'start').text,
            'end': e.find('span', 'end').text,
            'title': e.find('span', 'title').text
        }
        airdrop_start = datetime.datetime.strptime(airdrop['start'][:10], '%m/%d/%Y')
        when = airdrop_start - now

        if when.days == 0:
            text += "%s%s. *%s* (*today*)\n" % (" "*4, i, airdrop['title'])
        elif when.days < 0:
            text += "%s%s. *%s* (*ongoing*)\n" % (" "*4, i, airdrop['title'])
        else:
            text += "%s%s. *%s* (in *%s days*)\n" % (" "*4, i, airdrop['title'], when.days)

        if i >= 20:
            break
        i += 1

    if i > 1:
        text += "\nVisit %s for details." % url
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
    else:
        text = "*No upcoming airdrops!*"
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def get_coin_volumes(coin):
    db = 'data/coinmarketcap.db'

    # create connection
    c = sqlite3.connect(db)

    last = c.execute(
        'SELECT volume_usd FROM coinmarketcap WHERE id=? ORDER BY timestamp DESC LIMIT 1', (coin,)
    ).fetchone()

    a_day_ago = c.execute(
        'SELECT volume_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "-1 days") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC LIMIT 1', (coin,)
    ).fetchone()

    volume_day = c.execute(
        'SELECT volume_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") AND id=?', (coin,)
    ).fetchall()
    
    volume_week = c.execute(
        'SELECT volume_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") AND id=?', (coin,)
    ).fetchall()

    volume_month = c.execute(
        'SELECT volume_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") AND id=?', (coin,)
    ).fetchall()
    
    try:
        ret = {
            'last': last[0],
            'a_day_ago': a_day_ago[0],
            'day_avg': sum([x[0] for x in volume_day]) / len(volume_day),
            'week_avg': sum([x[0] for x in volume_week]) / len(volume_week),
            'month_avg': sum([x[0] for x in volume_month]) / len(volume_month)
        }
    except TypeError:
        return None
    return ret


def get_coin_ranks(coin):
    db = 'data/coinmarketcap.db'

    # create connection
    c = sqlite3.connect(db)
    
    # last count
    _latest = c.execute(
        'SELECT rank FROM coinmarketcap WHERE id=? ORDER BY timestamp DESC LIMIT 2', (coin,)
    )
    now = _latest.fetchone()
    last = _latest.fetchone()

    # count today
    today = c.execute(
        'SELECT rank FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC LIMIT 1', (coin,)
    ).fetchone()
    
    # count last week
    last_week = c.execute(
        'SELECT rank FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC LIMIT 1', (coin,)
    ).fetchone()
    
    # count last month
    last_month = c.execute(
        'SELECT rank FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC LIMIT 1', (coin,)
    ).fetchone()

    # ath
    ath = c.execute(
        'SELECT rank FROM coinmarketcap WHERE id=? ORDER BY rank ASC LIMIT 1', (coin,)
    ).fetchone()
    
    # atl
    atl = c.execute(
        'SELECT rank FROM coinmarketcap WHERE id=? ORDER BY rank DESC LIMIT 1', (coin,)
    ).fetchone()

    c.close()

    try:
        ret = {
            'now': now[0],
            'last': last[0],
            'today': today[0],
            'last_week': last_week[0],
            'last_month': last_month[0],
            'ath': ath[0],
            'atl': atl[0],
            'is_ath': now[0] <= ath[0], 
            'is_atl': now[0] >= atl[0]
        }
    except TypeError:
        return None
    return ret


def get_coin_mcaps(coin):
    db = 'data/coinmarketcap.db'

    # create connection
    c = sqlite3.connect(db)
    
    # last count
    now = c.execute(
        'SELECT market_cap_usd FROM coinmarketcap WHERE id=? ORDER BY timestamp DESC', (coin,)
    ).fetchone()

    # count today
    today = c.execute(
        'SELECT market_cap_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC', (coin,)
    ).fetchone()
    
    # count last week
    last_week = c.execute(
        'SELECT market_cap_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC', (coin,)
    ).fetchone()
    
    # count last month
    last_month = c.execute(
        'SELECT market_cap_usd FROM coinmarketcap WHERE timestamp BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") AND id=? ORDER BY timestamp ASC', (coin,)
    ).fetchone()

    c.close()

    ret = {
        'now': now[0],
        'today': today[0],
        'last_week': last_week[0],
        'last_month': last_month[0]
    }
    return ret

def coinmarketcap(bot, update, args):
    db = 'data/coinmarketcap.db'

    # create connection
    c = sqlite3.connect(db)

    coins = []
    for coin in c.execute('SELECT id FROM coinmarketcap'):
        coins.append(coin[0])

    text = '*Coins (20 from top 300, by weekly mcap growth) %s:*\n' % emoji['charts']

    mcaps = []
    for coin in coins:
        d = get_coin_mcaps(coin)
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
    db = 'data/reddit.db'

    # create connection
    c = sqlite3.connect(db)

    add_subreddit = None
    try:
        if args[0].lower() == 'add':
            add_subreddit = args[1]
            c.execute('INSERT INTO subreddits(subreddit) VALUES (?)', (add_subreddit,))
            c.commit()
            s = '*Added subreddit %s to watch list.*' % add_subreddit
            update.message.reply_text(s, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'del':
            add_subreddit = args[1]
            c.execute('DELETE FROM subreddits WHERE subreddit=? LIMIT 1', (add_subreddit,))
            c.commit()
            s = '*Removed subreddit %s from watch list.*' % add_subreddit
            update.message.reply_text(s, parse_mode=ParseMode.MARKDOWN)
            return
        elif args[0].lower() == 'list':
            l = sorted([x[0] for x in c.execute('SELECT subreddit FROM subreddits')], key=lambda s: s.lower())
            s = '*Currently watching these subreddits (%s total):*\n\n' % len(l) 
            s += ', '.join(l)
            bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)
            return
    except IndexError:
        pass

    srs = []
    for subreddit in c.execute('SELECT * FROM subreddits'):
        srs.append(subreddit[0])

    text = '*Reddit comunities (top 20, by weekly growth) %s:*\n' % emoji['charts']

    subs = []
    for sr in srs:

        # last count
        now = c.execute(
            'SELECT * FROM followers WHERE subreddit=? ORDER BY timestamp DESC', (sr,)
        ).fetchone()

        # count today
        today = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") AND subreddit=? ORDER BY timestamp ASC', (sr,)
        ).fetchone()
        
        # count last week
        last_week = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") AND subreddit=? ORDER BY timestamp ASC', (sr,)
        ).fetchone()
        
        # count last month
        last_month = c.execute(
            'SELECT * FROM followers WHERE timestamp BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") AND subreddit=? ORDER BY timestamp ASC', (sr,)
        ).fetchone()

        try:
            d = {
                'name': sr,
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
                'name': sr,
                'now': 0,
                'diff_today': 0,
                'pct_today': 0.0,
                'diff_week': 0,
                'pct_week':  0.0,
                'diff_month': 0,
                'pct_month': 0.0
            }
            logger.warning('caught exception: %s' % e)
        subs.append(d)
        # logger.info('reddit dict: %s' % d)
        
    i = 1
    sorted_subs = sorted(subs, key=itemgetter('pct_week'), reverse=True)[:20]
    for s in sorted_subs:
        text += '    %s. *%s*: %s (W:%s, M:%s)\n' % (
            i, s['name'], int(s['now']), pct(s['pct_week'], emo=False), pct(s['pct_month'], emo=False))
        i += 1

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def usd(bot, update, args):
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=USD'
    ticker = get_coin_id(args[0])
    if not ticker:
        return

    r = requests.get(cmc_api % ticker)
    price = float(r.json()[0]['price_usd'])
    text = '%s 1 %s = *$%.2f*' % (emoji['dollar'], ticker.upper(), price)
    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def stats(bot, update, args):
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=USD'
    try:
        ticker = get_coin_id(args[0])
    except IndexError:
        cmc_api = 'https://api.coinmarketcap.com/v1/global/?convert=USD'
        r = requests.get(cmc_api).json()
        stats = {}
        stats['total_market_cap_usd'] = millify(r['total_market_cap_usd'])
        stats['total_24h_volume_usd'] = millify(r['total_24h_volume_usd'])
        stats['bitcoin_percentage_of_market_cap'] = r['bitcoin_percentage_of_market_cap']
        stats['active_currencies'] = r['active_currencies']
        stats['active_assets'] = r['active_assets']
        stats['active_markets'] = r['active_markets']
        stats['emoji'] = emoji['charts']
        
        s = u"""*Global data %(emoji)s:*
    *Total Market Cap (USD):* $%(total_market_cap_usd)s
    *Total 24h Volume (USD):* $%(total_24h_volume_usd)s
    *BTC Dominance:* %(bitcoin_percentage_of_market_cap)s%%
    *Active Currencies:* %(active_currencies)s
    *Active Assets:* %(active_assets)s
    *Active Markets:* %(active_markets)s""" % stats
        bot.send_message(chat_id=update.message.chat_id, text=s, parse_mode=ParseMode.MARKDOWN)
        return

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
    """Send a message when the command /mcap is issued."""
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=USD'

    coin1 = get_coin_id(args[0])
    coin2 = get_coin_id(args[1])

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
        t = 'Double rainbow!%s%s' % (emoji['rainbow'], emoji['rainbow'])
        adj = emoji['rocket']
        prefix = '+'
    elif change < 0:
        t = 'ACHTUNG!%s' % emoji['collision']
        adj = emoji['poop']
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
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=300'
    r = requests.get(cmc_api).json()

    logger.info('running moonwatch check')

    coins = []
    volume_threshold = 500000
    for coin in r:
        try:
            coin['percent_change_1h'] = float(str(coin['percent_change_1h']))
            coin['price_usd'] = float(str(coin['price_usd']))
            coin['24h_volume_usd'] = float(str(coin['24h_volume_usd']))
            if coin['id'] == 'bitcoin':
                btc_usd = coin['price_usd']
            elif coin['id'] == 'ethereum':
                eth_usd = coin['price_usd']
        except ValueError:
            continue
        if not coin['24h_volume_usd'] >= volume_threshold:
            # volume needs to be reasonable
            continue
        coins.append(coin)

    winner = sorted(coins, key=itemgetter('percent_change_1h'), reverse=True)[0]
    logger.info('top gainer is %s (%s), up %.2f%% (volume: $%s)' % (
        winner['name'], winner['symbol'], winner['percent_change_1h'], millify(winner['24h_volume_usd'], short=True)))
   
    for coin in coins:
        if not coin['percent_change_1h'] >= job._threshold:
            continue
        text = u'*%s* (%s, #%s) *+%.2f%%* in the last hour, trading at *$%.2f*. BTC $%.2f, ETH $%.2f. %s' % (
            coin['name'], coin['symbol'], coin['rank'], coin['percent_change_1h'],
            coin['price_usd'], btc_usd, eth_usd, emoji['rocket'])
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)

    # Percentwise change in volume
    for coin in coins:
        volumes = get_coin_volumes(coin['id'])
        if not volumes:
            continue
        pct_change = ((coin['24h_volume_usd'] / volumes['last']) - 1) * 100
        if pct_change >= 80 and \
            coin['24h_volume_usd'] > volumes['a_day_ago'] and \
            coin['24h_volume_usd'] > volumes['week_avg']: #job._threshold:
            text = '*24h volume* of *%s* (%s, #%s) increased by *%.2f%%* to *$%d*. Last $%d, yesterday $%d, week avg $%d. %s' % (
                coin['name'], coin['symbol'], coin['rank'], pct_change, coin['24h_volume_usd'],
                volumes['last'], volumes['a_day_ago'], volumes['week_avg'], emoji['fire'])
            logger.info('%s is trading %.2f%% above last check' % (coin['id'], pct_change))
            bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)


def rankwatch(bot, job):
    cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=200'
    r = requests.get(cmc_api).json()

    volume_threshold = 500000
    
    logger.info('running rankwatch check')

    # Looking for changes in ranks
    climbers = []
    for coin in r:
        ranks = get_coin_ranks(coin['id'])
        if not ranks:
            continue

        if ranks['now'] < ranks['last'] and \
           ranks['now'] < ranks['last_week'] and \
           ranks['now'] < ranks['today'] and \
           ranks['is_ath'] and \
           float(str(coin['24h_volume_usd'])) >= volume_threshold:
            logger.info('ranks for %s: %s' % (coin['id'], ranks))
            climber = {
                'name': coin['name'],
                'symbol': coin['symbol'],
                'rank': ranks['now'],
                'ranks_day': ranks['today'] - ranks['now'],
                'ranks_week': ranks['last_week'] - ranks['now'],
                'ranks_month': ranks['last_month'] - ranks['now'],
                'volume': coin['24h_volume_usd'],
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
                emoji['triangle_up'], climber['ranks_day'], climber['ranks_week'], climber['ranks_month'],
                climber['name'], climber['symbol'], climber['rank'])
        text += '\nShowing All Time High ranks only.%s' % emoji['fire'] 
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)


def start_default(bot, update, args, job_queue, chat_data):
    # Start default jobs
    chat_id = update.message.chat_id
    job = job_queue.run_repeating(marketwatch, 300, context=chat_id)
    job._threshold = 0.7
    job._interval = 300
    chat_data['job'] = job

    job = job_queue.run_repeating(moonwatch, 900, context=chat_id)
    job._threshold = 10
    job._interval = 900
    chat_data['job'] = job

    # Start rank watch
    job = job_queue.run_repeating(rankwatch, 43200, context=chat_id)
    chat_data['job'] = job


def inlinequery(bot, update):
    """Handle the inline query."""
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="Caps",
            input_message_content=InputTextMessageContent(
                query.upper())),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Bold",
            input_message_content=InputTextMessageContent(
                "*{}*".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN)),
        InlineQueryResultArticle(
            id=uuid4(),
            title="Italic",
            input_message_content=InputTextMessageContent(
                "_{}_".format(escape_markdown(query)),
                parse_mode=ParseMode.MARKDOWN))]

    update.inline_query.answer(results)


def fomo(bot, update):
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(fomo_pics))


def fud(bot, update):
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(fud_pics))


def hodl(bot, update):
    bot.send_photo(chat_id=update.message.chat_id, photo=random.choice(hold_pics))


def carlos(bot, update):
    image_url = random.choice(carlos_gifs)
    bot.sendDocument(chat_id=update.message.chat_id, document=image_url)


def racklehahn(bot, update):
    image_url = random.choice(rackle_gifs)
    bot.sendDocument(chat_id=update.message.chat_id, document=image_url)


def shouldi(bot, update):
    update.message.reply_text(random.choice(['Yes.', 'No.']))


def diceroll(bot, update):
    update.message.reply_text(random.choice(['1', '2', '3', '4', '5', '6']))


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("<get bot token from @botmaster>")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("h", help))
    dp.add_handler(CommandHandler("search", search, pass_args=True))
    dp.add_handler(CommandHandler("q", search, pass_args=True))
    dp.add_handler(CommandHandler("mcap", mcap))
    dp.add_handler(CommandHandler("m", mcap))
    dp.add_handler(CommandHandler("webpage", webpage, pass_args=True))
    dp.add_handler(CommandHandler("website", webpage, pass_args=True))
    dp.add_handler(CommandHandler("w", webpage, pass_args=True))
    dp.add_handler(CommandHandler("homepage", webpage, pass_args=True))
    dp.add_handler(CommandHandler("convert", convert, pass_args=True))
    dp.add_handler(CommandHandler("c", convert, pass_args=True))
    dp.add_handler(CommandHandler("compare", compare, pass_args=True))
    dp.add_handler(CommandHandler("cmp", compare, pass_args=True))
    dp.add_handler(CommandHandler("usd", usd, pass_args=True))
    dp.add_handler(CommandHandler("u", usd, pass_args=True))
    dp.add_handler(CommandHandler("price", usd, pass_args=True))
    dp.add_handler(CommandHandler("stats", stats, pass_args=True))
    dp.add_handler(CommandHandler("s", stats, pass_args=True))
    dp.add_handler(CommandHandler("coin", stats, pass_args=True))
    dp.add_handler(CommandHandler("ico", ico, pass_args=True))
    dp.add_handler(CommandHandler("i", ico, pass_args=True))
    dp.add_handler(CommandHandler("reddit", reddit, pass_args=True))
    dp.add_handler(CommandHandler("r", reddit, pass_args=True))
    dp.add_handler(CommandHandler("twitter", twitter, pass_args=True))
    dp.add_handler(CommandHandler("t", twitter, pass_args=True))
    dp.add_handler(CommandHandler("coinmarketcap", coinmarketcap, pass_args=True))
    dp.add_handler(CommandHandler("marketwatch", set_marketwatch_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("mw", set_marketwatch_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("moonwatch", set_moonwatch_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("start", start_default,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("airdrops", airdrops))
    dp.add_handler(CommandHandler("airdrop", airdrops))
    dp.add_handler(CommandHandler("ad", airdrops))
    # Fun stuff
    dp.add_handler(CommandHandler("hodl", hodl))
    dp.add_handler(CommandHandler("fomo", fomo))
    dp.add_handler(CommandHandler("fud", fud))
    dp.add_handler(CommandHandler("carlos", carlos))
    dp.add_handler(CommandHandler("rackle", racklehahn))
    dp.add_handler(CommandHandler("shouldi", shouldi))
    dp.add_handler(CommandHandler("si", shouldi))
    dp.add_handler(CommandHandler("diceroll", diceroll))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
