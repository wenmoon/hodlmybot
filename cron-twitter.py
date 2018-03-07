#!/usr/bin/env python

import time

from hodlcore import model
from hodlcore import api
from hodlcore import db

def main():
    database = db.TwitterDB()
    names = database.get_tracked()
    for name in names:
        twitter = api.get_twitter(name)
        if twitter is not None:
            database.insert(twitter)

if __name__ == '__main__':
    main()
