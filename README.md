# crypto-tradebot

Tradebot that analyzes sentiments from reddit to determine general sentiments on individual coins, and formulate a trading decision to buy / sell the coin.

Crypto-tradebot monitors chatter on the top 100 coins from coingecko, and scrape posts in r/cryptocurrency for these coins. The posts title are evaluated using google senntiments api to get a sentiment score, and assign a weightage based on post's upvotes. After analyzing, the coins found will be assign a final sentiment score.

Written in python3, with binance and reddit API.

Installation:

pip install -r requirements.txt

Set up API keys for Binance and Reddit in local environment

![Screenshot 2021-10-23 at 2 28 57 PM](https://user-images.githubusercontent.com/9610243/138545382-e1db86ed-5f43-40fd-b5d4-cb608095616f.png)
