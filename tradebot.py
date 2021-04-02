import os
from binance.client import Client
# from binance.websockets import BinanceSocketManager
# from twisted.internet import reactor
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time
import requests

# api_key = os.environ.get('demo_binance_api')
# api_secret = os.environ.get('demo_binance_secret')

# print(api_secret)
# client = Client(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'

#init
def main():
    init_reddit()
    # start_binance()

def init_reddit():
    # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
    auth = requests.auth.HTTPBasicAuth(os.environ.get('reddit_script'), os.environ.get('reddit_secret'))

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
    get_reddit_post(headers)

def get_reddit_post(headers):
    res = requests.get("https://oauth.reddit.com/r/cryptocurrency/hot",
                   headers=headers)
    cryptos = ['bitcoin', 'ethereum', 'btc', 'eth']
    crypto_headlines = {'bitcoin':[],'btc':[],'ethereum':[],'eth':[] }
    # print(res.json()) 
    for post in res.json()['data']['children']:
        # print(post['data']['title'])
        headline_words =  post['data']['title'].lower().split(' ')
        for word in headline_words:
            if word in cryptos:
                crypto_headlines[word].append(post['data']['title'])
    
    print(crypto_headlines)

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
    print('succesfully bought ' + str(buy_qty) + ' ' +coin_symbol + ' at ' + buy_order['price'])
    while True:
        orders = client.get_all_orders(symbol=coin_symbol)
        for order in orders:
            print('order',order['orderId'], 'status:', order['status'] )
        print()
        time.sleep(10)

if __name__ == "__main__":
    main()
    