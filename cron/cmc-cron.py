#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import os
import sqlite3
from sqlite3 import Error

url = 'https://api.coinmarketcap.com/v1/ticker/?convert=USD&limit=300'
user_agent = 'fomo bot 0.1'

def create_tables(c):
    try:
        # Create table
        c.execute('''CREATE TABLE coinmarketcap
                    (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     id TEXT,
                     name TEXT,
                     symbol TEXT,
                     rank INTEGER,
                     price_usd REAL,
                     price_btc REAL,
                     volume_usd REAL,
                     market_cap_usd REAL,
                     available_supply REAL)''')
        c.commit()
    except Error as e:
        print(e)


def main():
    # Arguments
    parser = argparse.ArgumentParser(description="Script to mirror CoinMarketCap API")
    parser.add_argument('-d', '--db', help="database file (sqlite3)", default=None)
    args = parser.parse_args()

    # Check args
    if not args.db:
        parser.print_help()
        sys.exit(1)

    # create connection
    c = sqlite3.connect(args.db)

    try:
        c.execute('SELECT * FROM coinmarketcap LIMIT 1')
    except sqlite3.OperationalError:
        print('creating tables and exiting!')
        create_tables(c)
        c.commit()
        sys.exit(0)

    r = requests.get(url, headers = {'User-agent': user_agent})
    res = r.json()
    
    for coin in res:
        try:
            c.execute('INSERT INTO coinmarketcap(id, name, symbol, rank, price_usd, price_btc, volume_usd, market_cap_usd, available_supply) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                    coin['id'],
                    coin['name'],
                    coin['symbol'],
                    int(coin['rank']),
                    float(coin['price_usd']),
                    float(coin['price_btc']),
                    float(coin['24h_volume_usd']),
                    float(coin['market_cap_usd']),
                    float(coin['available_supply']),))
        except KeyError:
            print('error importing coin: %s' % coin)

    c.commit() 


if __name__ == '__main__':
    main()
