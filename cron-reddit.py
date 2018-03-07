#!/usr/bin/env python

import time

from hodlcore import model
from hodlcore import api
from hodlcore import db

def main():
    database = db.RedditDB()
    names = database.get_tracked()
    for name in names:
        subreddit = api.get_subreddit(name)
        if subreddit is not None:
            database.insert(subreddit)

if __name__ == '__main__':
    main()
