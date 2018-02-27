#!/usr/bin/env python
import requests
import json
import argparse
import sys
import os
import sqlite3
import time
from sqlite3 import Error


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

    try:
        c.execute('SELECT * FROM subreddits')
    except sqlite3.OperationalError:
        print('creating tables!')
        create_tables(c)
        sys.exit(0)

    coins = requests.get('https://api.coinmarketcap.com/v1/ticker/?convert=USD&limit=300').json()
    
    for coin in coins:
        r = requests.get('https://coinmarketcap.com/currencies/%s/#social' % coin['id'])
        lines = r.text.split('\n')
        for line in lines:
            if 'www.reddit.com' in line:
                try:
                    reddit = line.split('"')[1].split('/')[4].split('.')[0]
                except IndexError:
                    print('%s has no reddit page.' % reddit)

                try:
                    c.execute('INSERT INTO subreddits(subreddit) VALUES (?)', (reddit,))
                    c.commit()
                except sqlite3.IntegrityError:
                    print('%s already exists' % reddit)
                    continue
                print('adding %s' % reddit)


if __name__ == '__main__':
    main()
