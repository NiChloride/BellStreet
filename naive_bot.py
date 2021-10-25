#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function
from os import read

import sys
import socket
import json
import time

import os
import numpy as np

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="bellstreet"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())


        
# ~~~~~============== INITIALIZATION ==============~~~~~



# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    actions = ["add", "cancel"]
    symbols = ["BOND", "GS", "MS", "USD", "VALBZ", "VALE", "WFC", "XLF"]


    #starting 8 processes, each process will handle one type of product
    sym_index = 0
    order_id = 0
    for i in range(8):
        newpid = os.fork()
        if newpid == 0:
            order_id = sym_index * 100
            break
        else:
            sym_index += 1
    
    sym = symbols[sym_index]
    price_history = []
    counter = 10
    while counter < 10:
        message = read_from_exchange(exchange)
        if message['type'] == 'book' and message['symbol']==sym:
            print(message)
            market_ask = message['sell'][0][0]
            market_bid = message['buy'][0][0]
            market_price = (market_ask + market_bid)/2
            price_history.append(market_price)
            counter -= 1
    # position = 0
 

    while True:
        fair_price = np.mean(price_history)
        sd = np.std(price_history, ddof=1)
        message = read_from_exchange(exchange)
        if message['type'] == 'error':
            print("error: ", message['error'])
        if message['type'] != 'book' or message['symbol']!=sym:
            continue
        
        print('message_type is: ', message['type'])
        # Vmin = fair_price - 4 * sd * fair_price
		# Vmax = fair_price + 4 * sd * fair_price - .01
        price_to_buy = fair_price - sd * fair_price * 0.5
        price_to_sell = fair_price + sd * fair_price* 0.5

        market_ask = message['sell'][0][0]
        market_bid = message['buy'][0][0]
        market_price = (market_ask+market_bid)/2

        order_id += 1
        trade_size = 10

        if market_price < price_to_buy:
            #buy
            write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": sym, "dir": "BUY", "price": market_price, "size": trade_size})


        if market_price > price_to_sell:
            #sell
            write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": sym, "dir": "SELL", "price": market_price, "size": trade_size})
        
        price_history.append(market_price)


if __name__ == "__main__":
    main()
