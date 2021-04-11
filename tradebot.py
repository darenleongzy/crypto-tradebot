import os
from binance.client import Client
# from binance.websockets import BinanceSocketManager
# from twisted.internet import reactor
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time
import requests
from google.cloud import language_v1
from tqdm import tqdm
from datetime import datetime
# api_key = os.environ.get('demo_binance_api')
# api_secret = os.environ.get('demo_binance_secret')

# print(api_secret)
# client = Client(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'

# init


def main():
    ''' 
    crypto_list: [{coin_name, coin_symbol}, ... ] 
    crypto_content: {'coin_symbol': [
                        {'text': reddit_post, score},
                        ...
                    ] },
                    {'coin_symbol': [
                        {'text': reddit_post, score},
                        ...
                    ] },
                    ....
                    }
    crypto_sentiments: [{coin_name, [sent_val1, ...]}, ... ] 
    '''
    crypto_list, crypto_content, crypto_sentiments = init_crypto_list()
    client = language_v1.LanguageServiceClient()

    while True:
        headers = init_reddit()
        get_reddit_post(headers, crypto_list, crypto_content)
        analyze_sentiments(client, crypto_content, crypto_sentiments)
        print_crypto_sentiments(crypto_sentiments)
        print('\n[Completed round at {}]\n'.format(datetime.now()))
        time.sleep(60*60)

    # start_binance()


def init_reddit():
    print('Initializing reddit API ...')
    # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
    auth = requests.auth.HTTPBasicAuth(os.environ.get(
        'reddit_script'), os.environ.get('reddit_secret'))

    # here we pass our login method (password), username, and password
    data = {'grant_type': 'password',
            'username': os.environ.get('reddit_username'),
            'password': os.environ.get('reddit_password')}

    # setup our header info, which gives reddit a brief description of our app
    headers = {'User-Agent': 'crypto-sentiments'}

    # send our request for an OAuth token
    res = requests.post('https://www.reddit.com/api/v1/access_token',
                        auth=auth, data=data, headers=headers)

    # convert response to JSON and pull access_token value
    TOKEN = res.json()['access_token']
    # add authorization to our headers dictionary
    headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

    # while the token is valid (~2 hours) we just add headers=headers to our requests
    requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    return headers


def market_cap_sort(elem):
    return elem['market_cap_rank']


def init_crypto_list():
    print('Initializing Top 100 Crypto by marketcap...')
    res = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1")
    crypto_data = res.json()
    crypto_data.sort(key=market_cap_sort)
    crypto_list = []
    crypto_content = {}
    crypto_sentiments = {}
    for data in tqdm(crypto_data):
        crypto_list.append([data['name'].lower(), data['symbol'].lower()])
        crypto_content.update(
            {data['symbol']: {'total_votes': 0, 'posts': []}})
        crypto_sentiments.update({data['symbol']: []})
    return crypto_list, crypto_content, crypto_sentiments


def get_reddit_post(headers, crypto_list, crypto_content):

    # reddit posts that are created at least an hour ago
    current_ts = datetime.now().timestamp()
    post_list = get_suitable_reddit_post(current_ts, headers)
    print('Scraping useful post data from {} posts...'.format(len(post_list)))
    # print(res.json())
    for post in post_list:
        # print(post)
        # reddit_posts.set_description("Fetching Reddit Posts")

        headline_words = post['data']['title'].lower().split(' ')
        for word in headline_words:
            for crypto in crypto_list:
                if word == crypto[0] or word == crypto[1]:
                    coin_symbol = crypto[1]

                    #  Prevent 0 votes on post from being excluded in sentiment considerations
                    if post['data']['score'] == 0:
                        post['data']['score'] = 1
                    d = {'text': "" + post['data']['title'] + "\n" + post['data']['selftext'],
                         'votes': post['data']['score']}
                    crypto_content[coin_symbol]['total_votes'] += post['data']['score']
                    crypto_content[coin_symbol]['posts'].append(d)
                    break
    # print(crypto_content)
    return crypto_content


def get_suitable_reddit_post(current_ts, headers):
    print('Fetching reddit posts...')
    res = requests.get("https://oauth.reddit.com/r/cryptocurrency/new",
                       headers=headers, params={'limit': '100'})
    list_post = []
    end_post = ''
    curr_post = ''

    while not end_post:
        # print('oldest post', (int(current_ts) - int(res.json()
        #                                             ['data']['children'][0]['data']['created_utc']))/60)
        print(len(res.json()['data']['children']))
        for post in res.json()['data']['children']:
            curr_post = post['kind'] + '_' + post['data']['id']
            if int(current_ts) - int(post['data']['created_utc']) >= 60*60:
                list_post.append(post)
                if (int(current_ts) - int(post['data']['created_utc'])) >= 2*60*60:
                    end_post = curr_post
                    break
        if not end_post:
            res = requests.get("https://oauth.reddit.com/r/cryptocurrency/new",
                               headers=headers, params={'limit': '100', 'after': curr_post, 'count': '100'})
    return list_post


def analyze_sentiments(client, crypto_content, crypto_sentiments):
    analyze_content = tqdm(crypto_content.items())
    for crypto, val in analyze_content:
        analyze_content.set_description("Analyzing Sentiments")
        if val['total_votes'] != 0:
            # print('***************')
            # print(crypto.upper())
            # print('***************')
            # print(val['posts'])
            final_crypto_sentiment = 0
            for post in val['posts']:
                try:
                    document = language_v1.Document(
                        content=post['text'], type_=language_v1.Document.Type.PLAIN_TEXT)
                    annotations = client.analyze_sentiment(
                        request={'document': document})
                except Exception as e:
                    print(e)
                    print("Try re-initializing Google Client..")
                    client = language_v1.LanguageServiceClient()
                    document = language_v1.Document(
                        content=post, type_=language_v1.Document.Type.PLAIN_TEXT)
                    annotations = client.analyze_sentiment(
                        request={'document': document})
                score = annotations.document_sentiment.score
                print_sentiment_result(annotations, post['votes'])
                final_crypto_sentiment += (score *
                                           post['votes'] / val['total_votes'])
            # print("Final Sentiment Score", final_crypto_sentiment)
            crypto_sentiments[crypto].append(final_crypto_sentiment)
    print()


def print_sentiment_result(annotations, votes):
    score = annotations.document_sentiment.score
    magnitude = annotations.document_sentiment.magnitude

    for index, sentence in enumerate(annotations.sentences):
        sentence_sentiment = sentence.sentiment.score
        print(
            "Sentence {} has a sentiment score of {}".format(
                index, sentence_sentiment)
        )

    print(
        "Doc Sentiment: score of {} with {} votes".format(
            score, votes)
    )
    return 0


def print_crypto_sentiments(crypto_sentiments):
    for crypto, sentiments in crypto_sentiments.items():
        if sentiments:
            print(crypto.upper(), sentiments)


def start_binance():
    # print(client.get_account())
    # print(client.get_asset_balance(asset='BTC'))
    get_coin_price('BTCUSDT')
    buy_coin('ETHUSDT', 1)
    # bsm = BinanceSocketManager(client)
    # conn_key = bsm.start_symbol_ticker_socket('BTCUSDT', coin_trade_history)
    # bsm.start()


def get_coin_price(coin_symbol):
    coin_price = client.get_symbol_ticker(symbol=coin_symbol)
    # print(coin_price['price'])


def buy_coin(coin_symbol, buy_qty):
    try:
        buy_order = client.order_market_sell(
            symbol=coin_symbol,
            quantity=buy_qty
        )

    except BinanceAPIException as e:
        # error handling goes here
        print(e)
    except BinanceOrderException as e:
        # error handling goes here
        print(e)
    print('succesfully bought ' + str(buy_qty) + ' ' +
          coin_symbol + ' at ' + buy_order['price'])
    while True:
        orders = client.get_all_orders(symbol=coin_symbol)
        for order in orders:
            print('order', order['orderId'], 'status:', order['status'])
        print()
        time.sleep(10)


if __name__ == "__main__":
    main()
