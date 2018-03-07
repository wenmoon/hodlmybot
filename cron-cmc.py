#!/usr/bin/env python

from hodlcore import model
from hodlcore import db
from hodlcore import api

def main():
    tokens = api.get_top_tokens()
    tokens_database = db.TokenDB()
    tokens_database.insert(tokens)

    mcap = api.get_mcap()
    mcap_database = db.MarketCapitalizationDB()
    mcap_database.insert(mcap)

if __name__ == '__main__':
    main()
