from statistics import mean

from connection import *

class Executor(object):
    def __init__(self, test_mode):
        self.order_id = None
        if test_mode:
            self.hostname = '10.0.163.230'
            test_exchange_index = 0
            self.port = 250000 + test_exchange_index
        else:
            self.hostname = 'production'
        self.bondBook = [[], []]
        self.valbzBook = [[], []]
        self.valeBook = [[], []]
        self.gsBook = [[], []]
        self.msBook = [[], []]
        self.wfcBook = [[], []]
        self.xlfBook = [[], []]

        self.bond = []
        self.valbz = []
        self.vale = []
        self.gs = []
        self.ms = []
        self.wfc = []
        self.xlf = []

        self.bondAvg = 0
        self.valbzAvg = 0
        self.valeAvg = 0
        self.gsAvg = 0
        self.msAvg = 0
        self.wfcAvg = 0
        self.xlfAvg = 0

        self.order_id = 0

    def executeOrder(self, symbol, direction, price, size, exchange):
        # Direction is BUY or SELL

        if price:
            # if price exists. Is buy or sell order
            jsonObject = {
                "type": "add",
                "order_id": self.order_id,
                "symbol": symbol,
                "dir": direction,
                "price": price,
                "size": size,
            }
            print("JSON OBJECT IS ", jsonObject)
            write_to_exchange(exchange, jsonObject)
            self.order_id += 1
        else:
            # price don't exist. Is convert order
            jsonObject = {
                "type": "convert",
                "order_id": self.order_id,
                "symbol": symbol,
                "dir": direction,
                "size": size,
            }
            print(jsonObject)
            write_to_exchange(exchange, jsonObject)
            self.order_id += 1

    def executeCancel(self, id, exchange):
        jsonObject = {"type": "cancel", "order_id": id}
        write_to_exchange(exchange, jsonObject)
        print("Cancelled order ", id)


    def executeFairValue(self, symbol, fairValue, exchange, isConvert):
        buyOrders = {"size": 0, "price": 0}
        sellOrders = {"size": 0, "price": 100000000000000000}
        bookDict = {
            "BOND": self.bondBook,
            "VALBZ": self.valbzBook,
            "VALE": self.valeBook,
            "GS": self.gsBook,
            "MS": self.msBook,
            "WFC": self.wfcBook,
            "XLF": self.xlfBook,
        }
        targetBook = bookDict[symbol]
        for order in targetBook[
            0
        ]:  # bond[0] stores the information of BUY prices and sizes from the LATEST BOOK message for BOND
            if order[0] > fairValue:
                sellOrders["size"] += order[1]
                sellOrders["price"] = min(sellOrders["price"], order[0])

        for order in targetBook[
            1
        ]:  # bond[1] stores the information of SELL prices and sizes from the LATEST BOOK message for BOND
            if order[0] < fairValue:
                buyOrders["size"] += order[1]
                buyOrders["price"] = max(buyOrders["price"], order[0])

        if sellOrders["size"] > 0:
            self.executeOrder(symbol, "SELL", sellOrders["price"], sellOrders["size"], exchange)
        if buyOrders["size"] > 0:
            self.executeOrder(symbol, "BUY", buyOrders["price"], buyOrders["size"], exchange)

    def handleBook(self, message):
        symbol = message["symbol"]

        buyArray = message["buy"]
        sellArray = message["sell"]

        # Update the corresponding symbolBook to latest from updates from market BOOK message
        if symbol == "BOND":
            self.bondBook[0] = copy.deepcopy(buyArray)
            self.bondBook[1] = copy.deepcopy(sellArray)
        elif symbol == "VALBZ":
            self.valbzBook[0] = copy.deepcopy(buyArray)
            self.valbzBook[1] = copy.deepcopy(sellArray)
        elif symbol == "VALE":
            self.valeBook[0] = copy.deepcopy(buyArray)
            self.valeBook[1] = copy.deepcopy(sellArray)
        elif symbol == "GS":
            self.gsBook[0] = copy.deepcopy(buyArray)
            self.gsBook[1] = copy.deepcopy(sellArray)
        elif symbol == "MS":
            self.msBook[0] = copy.deepcopy(buyArray)
            self.msBook[1] = copy.deepcopy(sellArray)
        elif symbol == "WFC":
            self.wfcBook[0] = copy.deepcopy(buyArray)
            self.wfcBook[1] = copy.deepcopy(sellArray)
        elif symbol == "XLF":
            self.xlfBook[0] = copy.deepcopy(buyArray)
            self.xlfBook[1] = copy.deepcopy(sellArray)

    def handlCurrentPrice(self, message):
        symbol = message["symbol"]
        global bondAvg, valbzAvg, valeAvg, gsAvg, msAvg, wfcAvg, xlfAvg
        if symbol == "BOND":
            self.bond.append(message["price"])
            bondAvg = mean(self.bond)
        elif symbol == "VALBZ":
            self.valbz.append(message["price"])
            valbzAvg = mean(self.valbz)
        elif symbol == "VALE":
            self.vale.append(message["price"])
            valeAvg = mean(self.vale)
        elif symbol == "GS":
            self.gs.append(message["price"])
            gsAvg = mean(self.gs)
        elif symbol == "MS":
            self.ms.append(message["price"])
            msAvg = mean(self.ms)
        elif symbol == "WFC":
            self.wfc.append(message["price"])
            wfcAvg = mean(self.wfc)
        elif symbol == "XLF":
            self.xlf.append(message["price"])
            xlfAvg = mean(self.xlf)


    def handleMessage(self, message):
        type = message["type"]
        if type == "book":
            self.handleBook(message)
        elif type == "trade":
            self.handlCurrentPrice(message)
        elif type == "ack":
            print("ACK: ", message)
        elif type == "reject":
            print(message)
        else:
            print("Other message: ", message)


### strategy
    def ADRStrategy(self, exchange):
        valefair = (self.valbzBook[0][0][0] + self.valbzBook[1][0][0]) / 2
        self.executeFairValue("VALE", valefair, exchange, False)

    def pennyingStrategy(self, exchange):
        fairValue = 1000
        buyOrders = {"size": 0, "price": 0}
        sellOrders = {"size": 0, "price": 100000000000000000}
        bookDict = {
            "BOND": self.bondBook,
            "VALBZ": self.valbzBook,
            "VALE": self.valeBook,
            "GS": self.gsBook,
            "MS": self.msBook,
            "WFC": self.wfcBook,
            "XLF": self.xlfBook,
        }
        symbol = 'BOND'
        targetBook = bookDict[symbol]
        for order in targetBook[
            0
        ]:  # bond[0] stores the information of BUY prices and sizes from the LATEST BOOK message for BOND
            if order[0] > fairValue:
                sellOrders["size"] += order[1]
                sellOrders["price"] = min(sellOrders["price"], order[0])

        for order in targetBook[
            1
        ]:  # bond[1] stores the information of SELL prices and sizes from the LATEST BOOK message for BOND
            if order[0] < 1000:
                buyOrders["size"] += order[1]
                buyOrders["price"] = max(buyOrders["price"], order[0])

        if sellOrders["size"] > 0:
            self.executeOrder(symbol, "SELL", sellOrders["price"], sellOrders["size"], exchange)
        if buyOrders["size"] > 0:
            self.executeOrder(symbol, "BUY", buyOrders["price"], buyOrders["size"], exchange)

    def ETFStrategy(self, exchange):
        basket_price = 0
        try:
            bondfair = (self.bondBook[0][0][0] + self.bondBook[1][0][0])/2
            gsfair = (self.gsBook[0][0][0] + self.gsBook[1][0][0])/2
            msfair = (self.msBook[0][0][0] + self.msBook[1][0][0])/2
            wffair = (self.wfcBook[0][0][0] + self.wfcBook[1][0][0])/2

            fairValue = (bondfair*3+2*gsfair+msfair*3+2*wffair)
            symbol = 'XLF'
            buyOrders = {"size": 0, "price": 0}
            sellOrders = {"size": 0, "price": 100000000000000000}
            bookDict = {
                "BOND": self.bondBook,
                "VALBZ": self.valbzBook,
                "VALE": self.valeBook,
                "GS": self.gsBook,
                "MS": self.msBook,
                "WFC": self.wfcBook,
                "XLF": self.xlfBook,
            }
            targetBook = bookDict[symbol]
            for order in targetBook[
                0
            ]:  # bond[0] stores the information of BUY prices and sizes from the LATEST BOOK message for BOND
                if order[0]*10-150 > fairValue*10:
                    sellOrders["size"] += order[1]
                    sellOrders["price"] = min(sellOrders["price"], order[0])

            for order in targetBook[
                1
            ]:  # bond[1] stores the information of SELL prices and sizes from the LATEST BOOK message for BOND
                if order[0]*10+150 < fairValue*10:
                    buyOrders["size"] += order[1]
                    buyOrders["price"] = max(buyOrders["price"], order[0])

            if sellOrders["size"] > 0:
                self.executeOrder(symbol, "SELL", sellOrders["price"], sellOrders["size"], exchange)
            if buyOrders["size"] > 0:
                self.executeOrder(symbol, "BUY", buyOrders["price"], buyOrders["size"], exchange)
        except:
            pass

if __name__ == "__main__":
    exchange = connect()
    exe = Executor(test_mode=True)
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    while True:
        message = read_from_exchange(exchange)
        if message["type"] == "close":
            print("The round has ended")
            break
        exe.handleMessage(message)
        try:
            exe.pennyingStrategy(exchange)
            exe.ADRStrategy(exchange)
            #exe.ETFStrategy(exchange)
        except Exception as e:
            print(e)