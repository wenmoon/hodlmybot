#!/usr/bin/env python

from hodlcore import api
from hodlcore import db

def main():
    database = db.RedditDB()
    for subscribable in api.get_top_reddits():
        database.track(subscribable)


if __name__ == '__main__':
    main()
