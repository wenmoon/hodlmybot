#!/usr/bin/env python3

from hodlcore import api
from hodlcore import db

def main():
	print('Importing latest top Reddits...')

    database = db.RedditDB()
    for subscribable in api.get_top_reddits():
        database.track(subscribable)

    print('Done!')

if __name__ == '__main__':
    main()
