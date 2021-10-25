import sys
import socket
import json
import copy


# team_name = "Bell Street"
# test_mode = False
#
# test_exchange_index=0
# prod_exchange_hostname="production"
#
# port=25000 + (test_exchange_index if test_mode else 0)
# exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname
#
# symbols = ["BOND", "GS", "MS", "USD", "VALBZ", "VALE", "WFC", "XLF"]

# ~~~~~============== CONNECTION ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile("rw", 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())


