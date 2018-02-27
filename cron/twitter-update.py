#!/usr/bin/env python

import requests
import json
import argparse
import sys
import os
import sqlite3
import time
from sqlite3 import Error
from bs4 import BeautifulSoup

cmc_api = 'https://api.coinmarketcap.com/v1/ticker/?limit=300'
coin_url = 'https://coinmarketcap.com/currencies/%s/'


def create_tables(c):
    try:
        # Create table
        c.execute('''CREATE TABLE twitter_accounts
                    (user TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE followers
                    (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, user TEXT, followers INTEGER)''')
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

    users = []
    try:
        for user in c.execute('SELECT * FROM twitter_accounts'):
            users.append(user[0])
    except sqlite3.OperationalError:
        print('creating tables!')
        create_tables(c)
        sys.exit(0)
    
    r = requests.get(cmc_api).json()

    for coin in r:    
        co = requests.get(coin_url % coin['id'])
        soup = BeautifulSoup(co.text, 'lxml')
        try:
            twitter = soup.find('a', 'twitter-timeline').attrs['data-screen-name']
        except AttributeError:
            continue
        try:
            c.execute('INSERT INTO twitter_accounts(user) VALUES (?)', (twitter,))
            c.commit()
        except sqlite3.IntegrityError:
            print('%s already exists' % twitter)
            continue
        print('adding %s' % twitter)

if __name__ == '__main__':
    main()
