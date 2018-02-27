#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import os
import sqlite3
import time
from sqlite3 import Error

url = 'https://www.reddit.com/r/%s/about.json'
user_agent = 'your bot 0.1'

default_values = [
    'bitcoin',
    'ethereum',
    'litecoin',
    'nebulas',
    'Monero',
    'Ripple',
    'IOTA',
    'nanocurrency',
    'vertcoin',
    'HEROcoin',
    'XRPTalk',
    'Electroneum',
    'dogecoin',
    'reddCoin',
    'Lisk',
    'siacoin',
    'steem',
    'komodoplatform',
    'SaltCoin',
    'gnosisPM',
    'Quantstamp',
    'COSS',
    'CossIO',
]

def get_subscribers(subreddit):
    r = requests.get(url % subreddit, headers = {'User-agent': user_agent})
    res = r.json()
    try:
        subscribers = res['data']['subscribers']
    except KeyError:
        subscribers = 0
    time.sleep(3)
    return subscribers


def create_tables(c):
    try:
        # Create table
        c.execute('''CREATE TABLE subreddits
                    (subreddit TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE followers
                    (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, subreddit TEXT, followers INTEGER)''')
        c.commit()
    except Error as e:
        print(e)


def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db', help="database file (sqlite3)", default=None)
    args = parser.parse_args()

    # Check args
    if not args.db:
        parser.print_help()
        sys.exit(1)

    # create connection
    c = sqlite3.connect(args.db)

    srs = []
    try:
        for subreddit in c.execute('SELECT * FROM subreddits'):
            srs.append(subreddit[0])
    except sqlite3.OperationalError:
        print('creating tables!')
        create_tables(c)
        for sr in default_values:
            c.execute('INSERT INTO subreddits(subreddit) VALUES (?)', (sr,))
        c.commit()
        sys.exit(0)

    for sr in list(set(srs)):
        c.execute('INSERT INTO followers(subreddit, followers) VALUES (?, ?)', (sr, get_subscribers(sr)))
    c.commit() 


if __name__ == '__main__':
    main()
