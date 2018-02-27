#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import os
import sqlite3
import time
import tweepy
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

from sqlite3 import Error

url = 'https://www.reddit.com/r/%s/about.json'
user_agent = 'fomo bot 0.1'

default_values = [
    'ethereumproject',
    'Ripple',
    'LitecoinProject',
    'CardanoStiftung',
    'neo_blockchain',
    'StellarOrg',
    'eos_io',
    'Dashpay',
    'iotatoken',
    'monerocurrency',
    'NEMofficial',
    'eth_classic',
    'tronfoundation',
    'vechainofficial',
    'LiskHQ',
    'tether_to',
    'bitcoingold',
    'qtumOfficial',
    'omise_go',
    'helloiconworld',
    'zcashco',
    'nanocurrency',
    'vergecurrency',
    'binance_2017',
    'Bytecoin_BCN',
    'Steemit',
    'BitPopulous',
    'SiaTechHQ',
    'stratisplatform',
    'dogecoin',
    'wavesplatform',
    'rchain_coop',
    'ethstatus',
    'digixglobal',
    'MakerDAO',
    'BitShares',
    'aetrnty',
    'Veritaseuminc',
    'Waltonchain',
    'AugurProject',
    'decredproject',
    'ZclassicCoin',
    'electroneum',
    '0xproject',
    'HcashOfficial',
    'revain_org',
    'ardorplatform',
    'KomodoPlatform',
    'ArkEcosystem',
    'kucoincom',
    'attentiontoken',
    'DigiByteCoin',
    'zilliqa',
    'Cryptonex_CNX',
    'loopringorg',
    'Bytom_Official',
    'aelfblockchain',
    'dragonchaingang',
    'dentcoin',
    'syscoin',
    'dentacoin',
    'kybernetwork',
    'polymathnetwork',
    'quoine_SG',
    'nebulasio',
    'golemproject',
    '_pivx',
    'Aion_Network',
    'ByteballOrg',
    'ethos_io',
    'iostoken',
    'reddcoin',
    'Bitcore_BTX',
    'gongxinbao',
    'factom',
    'powerledger_io',
    'FunFairTech',
    'Crowd_indicator',
    'kin_foundation',
    'smart_contract',
    'PillarWallet',
    'zcoinofficial',
    'SaltLending',
    'NxtCommunity',
    'BancorNetwork',
    'enigmampc',
    'maidsafe',
    'ParticlProject',
    'NeblioTeam',
    'scashofficial',
    'emercoin_press',
    'requestnetwork',
    'Vertcoin',
    'tenxwallet',
    'ignisguide',
    'The_Blocknet',
    'gamecredits',
    'Quantstamp',
    'raiden_network',
    'WAX_io',
    'singularity_net',
    'iconominet',
    'XDNCommunity',
    'enjin',
    'gnosisPM',
    'santimentfeed',
    '_poetproject',
    'BitcoinDark',
    'thebigxp',
    'Skycoinproject',
    'SuperNETorg',
    'civickey',
    'storjproject',
    'substratumnet',
    'CryptoBridge',
    'achainofficial',
    'Storm_Token',
    'ZenCashOfficial',
    'NxsEarth',
    'decentraland',
    'ethlend1',
    'AragonProject',
    'HPB_Global',
    'OysterProtocol',
    'DewFund',
    'AdEx_Network',
    'NAVCoin',
    'XPAtwopointoh',
    'telcoin_team',
    'TokensNet',
    '_medibloc',
    'blockv_io',
    'TimeNewBank',
    'iEx_ec',
    'IoT_Chain',
    'monaco_card',
    'ubiqsmart',
    'bluzellehq',
    'MediShares',
    'Sophia_TX_',
    'Blockchain_Data',
    'PayPiePlatform',
    'genesis_vision',
    'red_pulse_china',
    'Bibox365',
    'udotcash',
    'VibeHubVR',
    'PeercoinPPC',
    'wagerrx',
    'SIRINLABS',
    'AschPlatform',
    'HTMLCOIN',
    'AmbrosusAMB',
    'RCN_token',
    'sonmdevelopment',
    'CRYPTOtwenty',
    'PuraSocial',
    'DeepBrainChain',
    'eidoo_io',
    'xtrabytes',
    'metalpaysme',
    'TauChainOrg',
    'thetatoken',
    'appcoinsproject',
    'einsteiniumcoin',
    'jibrelnetwork',
    'cybermiles',
    'airswap',
    'SingularDTV',
    'etherparty_com',
    'melonport',
    'TheSimpleToken',
    'wabiico',
    'QRLedger',
    'minexcoin',
    'CounterpartyXCP',
    'streamrinc',
    'mvs_org',
    'ins_ecosystem',
    'cobinhood',
    'GIFTO_io',
    'PaccoinOfficial',
    'BitBayofficial',
    'thenagaico',
    'blocksafe',
    'edgelessproject',
    'nulsservice',
    'TrinityProtocol',
    'viacoin',
    'breadapp',
    'UTRUST_Official',
    'WePowerN',
    'mobilegotoken',
    'Burstcoin_dev',
    'AeonCoin',
    'wingsplatform',
    'Tierion',
    'coindashio',
    'bottos_ai',
    'project_ecc',
    'gulden',
    'spankchain',
    'Centra_Card',
    'medical_chain',
    'CloakCoin',
    'ionomics',
    'modum_io',
    'delphy_org',
    'indaHash',
    'TaaSfund',
    'lbryio',
    'hiveproject_net',
    'district0x',
    'BitBeanCoin',
    'qlinkmobi',
    'RiseVisionTeam',
    'GroestlcoinTeam',
    'allsportschain',
    'intchain',
    'ATMChainDev',
    'CrownPlatform',
    'safe_exchange',
    'cosscrypto',
    'myrarepepe',
    'ColossusCoinXT',
    'UnikoinGold',
    'lykke',
    'Feathercoin',
    'cappasity',
    'mercurytoken',
    'stktoken',
    'tokencard_io',
    'SpectreAI',
    'dmdcoin',
    'Namecoin',
    'ad_chain',
    'HorizonState',
    'nimiq',
    'presearchnews',
    'origin_trail',
    'Viberate_com',
    'datumnetwork',
    'mooncoinitalia',
    'Dimecoin_',
    'DECENTplatform',
    'potcoin',
    'SibChervonec',
    'firstbloodio',
    'DeepOnionx',
    'Humaniq',
    'LunyrInc',
    'everexio',
    'Monetha_io',
    'EnergoOfficial',
    'blockmasonio',
    'TheHempCoin ',
    'Qbao2339',
    'AgrelloOfficial',
    'WhiteCoiner',
    'ODYSSEYPROTOCOL',
    'ShiftNrg',
    'inklabsfound',
    'Blockportio',
    'cofound_it',
    'swftcoin',
    'zeepinchain',
    'Zeusshield',
    'io_coin',
    'mintcointeam',
    'FlashCoins',
    'unobtanium_uno',
    'TheSwarmFund',
    'SelfKey',
    'ElectracoinECA',
    'bitconnect',
    'soarcoin',
    'lamdentau',
    'gelert',
    'BloomToken',
    'Xspec_Official',
    'PascalCoin',
    'blocktix',
    'numerai',
    'SHIELDCurrency',
    'carVertical_com',
    'worldcoresocial',
    'sun_contract',
    'dadi',
    'Voxelus',
    'wetrustplatform',
    'maecenasart',
]


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
        for u in default_values:
            c.execute('INSERT INTO twitter_accounts(user) VALUES (?)', (u,))
        c.commit()
        sys.exit(0)

    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    for u in list(set(users)):
        print('fetching followers for: %s' % u)
        try:
            followers = api.get_user(u).followers_count
        except tweepy.error.TweepError:
            print('couldn\'t find twitter account: %s' % u)
        c.execute('INSERT INTO followers(user, followers) VALUES (?, ?)', (u, followers))
        time.sleep(2)
    c.commit() 


if __name__ == '__main__':
    main()
