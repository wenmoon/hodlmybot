#!/usr/bin/env python3

import json
from hodlcore import model
from hodlcore import api
from hodlcore import db

def main():
    print('Importing latest Twitter metrics...')

    with open('api-creds-twitter.json', 'r') as file:
        creds = model.OAuthCredentials.from_json(json.load(file))
    database = db.TwitterDB()
    names = database.get_tracked()
    for name in names:
        twitter = api.get_twitter(name, creds)
        if twitter is not None:
            database.insert(twitter)

    print('Done!')

if __name__ == '__main__':
    main()
