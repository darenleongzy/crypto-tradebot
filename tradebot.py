import os
from binance.client import Client
# from binance.websockets import BinanceSocketManager
# from twisted.internet import reactor
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time

api_key = os.environ.get('demo_binance_api')
api_secret = os.environ.get('demo_binance_secret')

client = Client(api_key, api_secret)
client.API_URL = 'https://testnet.binance.vision/api'

global btc_price
#init
def main():
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
main()