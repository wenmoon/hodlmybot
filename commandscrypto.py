from telegram.utils.helpers import escape_markdown
from telegram import ParseMode

import logging
import math

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


def search(bot, update, args):
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

        update.message.reply_text(search_result, parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /search <query>')


def usd(bot, update, args):
    try:
        token = api.search_token(args[0])
        if token is None:
            error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
            update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        else:
            message = '{} 1 {} = *${:.2f}*'.format(stringformat.emoji('dollar'), token.symbol.upper(), token.price)
            bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /usd <token>')


def convert(bot, update, args):
    try:
        amount = args[0]
        from_token = api.search_token(args[1])
        to_token = api.search_token(args[2])
        converted_amount = (float(amount) * from_token.price) / to_token.price
        text = '{} {} {} = *{:.8f} {}*'.format(stringformat.emoji('dollar'), amount, from_token.symbol.upper(), converted_amount, to_token.symbol.upper())
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /convert <amount> <from token> <to token>')


def stats(bot, update, args):
    # No args means global stats
    if len(args) == 0:
        mcap = api.get_mcap()
        bot.send_message(chat_id=update.message.chat_id, text=stringformat.mcap_summary(mcap), parse_mode=ParseMode.MARKDOWN)
        return

    token = api.search_token(args[0])
    if token is None:
        error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    summary_btc = None
    if not token.is_bitcoin():
        summary_btc = db.TokenDB().get_prices_btc(token.id)
    bot.send_message(chat_id=update.message.chat_id, text=stringformat.token_summary(token, summary_btc), parse_mode=ParseMode.MARKDOWN)


def compare(bot, update, args):
    try:
        token1 = api.search_token(args[0])
        token2 = api.search_token(args[1])

        if token1 is None:
            error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'.format(args[0])
            update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
            return
        if token2 is None:
            error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap, or missing MCAP.'.format(args[1])
            update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
            return

        bot.send_message(chat_id=update.message.chat_id, text=stringformat.token_compared_summary(token1, token2), parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /compare <token1> <token2>')


def mcap(bot, update):
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

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def ico(bot, update, args):
    token = api.search_token(args[0])
    if token is None:
        error = 'Sorry, I couldn\'t find *{}* on CoinMarketCap.'.format(args[0])
        update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN)
        return

    ico_text = api.get_ico_text(token)
    if ico_text:
        bot.send_message(chat_id=update.message.chat_id, text=ico_text, parse_mode=ParseMode.MARKDOWN)
    else:
        text = 'Sorry, I couldn\'t find *{}* on ICO Drops.'.format(token.id)
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def webpage(bot, update, args):
    query = args[0].lower()
    token = api.search_token(query)
    if token is None:
	    bot.send_message(chat_id=update.message.chat_id, text='Could not find webpage for {}'.format(query), parse_mode=ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=token.url, parse_mode=ParseMode.MARKDOWN)


def airdrops(bot, update):
    airdrops = api.get_airdrops()
    if len(airdrops) > 0:
        bot.send_message(chat_id=update.message.chat_id, text=stringformat.airdrops_summary(airdrops), parse_mode=ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="*No upcoming airdrops!*", parse_mode=ParseMode.MARKDOWN)


def coinmarketcap(bot, update, args):
    token_db = db.TokenDB()
    tokens = api.get_top_tokens(limit=200)

    text = '*Coins (20 from top 300, by weekly mcap growth) {}:*\n'.format(stringformat.emoji('charts'))
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

    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


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
    mcap_now = api.get_mcap()
    mcap_db = db.MarketCapitalizationDB()
    mcap_prev = mcap_db.get_latest()
    mcap_db.insert(mcap_now)

    change = stringformat.percent(num=((mcap_now.mcap_usd - mcap_prev.mcap_usd) / mcap_now.mcap_usd) * 100, emo=False)
    logger.info('old mcap: {:.2f}, new mcap: {:.2f}, threshold: {:.1f}, change: {:.8f}'.format(mcap_prev.mcap, mcap_now.mcap, job._threshold, change))

    # Do nothing if change is not significant.
    if not abs(change) > job._threshold:
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
    text = '*{}* Total Market Cap *{}{}%* in {} seconds, *${}!*\n\n{}'.format(t, prefix, change, job._interval, stringformat.large_number(mcap_now.mcap_usd), return_url)
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
    eth = api.search_token('ethereum')
    btc = api.search_token('bitcoin')
    top_tokens = api.get_top_tokens(limit=300)
    tokens = [token for token in top_tokens if token.volume_24h >= 500000]
    for token in tokens:
        text = '*{}* ({}, #{}) *+{:.2f}%* in the last hour, trading at *${:.2f}*. BTC ${:.2f}, ETH ${:.2f}. %{}'.format(
            token.name, token.symbol, token.rank, token.percent_change_1h,
            token.price, btc.price, eth.price, stringformat.emoji('rocket'))
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)

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
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)


def rankwatch(bot, job):
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

    if climbers:
        tokens_ranks = sorted(tokens_ranks, key=itemgetter(1), reverse=False)
        text = '*CoinMarketCap rank climbers (w/m):*\n'
        for (token, ranks) in token_ranks:
            text += stringformat.token_ranks_summary(token, ranks)
        text += '\nShowing All Time High ranks only {}'.format(stringformat.emoji('fire'))
        bot.send_message(job.context, text=text, parse_mode=ParseMode.MARKDOWN)

