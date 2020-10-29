import pandas as pd
from datetime import datetime
from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *
from envelope import *

# start day of TLT: 2003-01-02
snp = data.DataReader('^GSPC', 'yahoo', start='2003-01-02')
treas = data.DataReader('TLT', 'yahoo', start='2003-01-02')

exampleStaticPortfolio = [
        { "name": "S&P500", "ratio": 7, "data": snp },
        { "name": "TLT",   "ratio": 3, "data": treas }
        ]

class StaticPortfolio:
    def __init__(self, portfolio, cash):
        self.name = 'StaticPortfolio'
        self.values = []
        ratiosSum = np.abs([float(v['ratio']) for v in portfolio]).sum()
        balance = dict()
        startDate = datetime(1900, 1, 1, 0, 0)
        endDate = datetime.now()
        balance["cash"] = { "price": 1, 
                            "amount": 0, 
                            "ratio": 0 }
        for item in portfolio:
            price = item["data"]['Close'][0]
            amount = math.floor(cash * (item["ratio"] / ratiosSum / price))
            balance[item["name"]] = { "price": price, 
                                      "amount": amount, 
                                      "ratio": item["ratio"] }
            if startDate < item["data"]['Close'].keys()[0]:
                startDate = item["data"]['Close'].keys()[0]
            if endDate > item["data"]['Close'].keys()[-1]:
                endDate = item["data"]['Close'].keys()[-1]
        date_range = pd.period_range(start=startDate, end=endDate, freq='D')
        for d in date_range.astype(str):
            for item in portfolio:
                if d in item["data"]["Close"]:
                    balance[item["name"]]["price"] = item["data"]["Close"][d]
                    changed = True
            balance = rebalance(balance)
            value = 0
            for k, v in balance.items():
                value = value + (v["price"] * v["amount"])
            self.values.append(value)

class Portfolio:
    def __init__(self, ratio):
        self.name = 'Portfolio'
        self.ratio = ratio
        self.values = []
    def rebalance(balance, price):
        return rebalance(balance)

class Simulator:
    def __init__(self, data, cash, portfolio):
        self.values = []
        balance = dict()
        startDate = datetime(1900, 1, 1, 0, 0)
        endDate = datetime.now()
        balance["cash"] = { "price": 1, 
                            "amount": 0 }
        for item in data:
            price = item['Close'][0]
            if startDate < item['Close'].keys()[0]:
                startDate = item['Close'].keys()[0]
            if endDate > item['Close'].keys()[-1]:
                endDate = item['Close'].keys()[-1]
        data_elem = dict()
        date_range = pd.period_range(start=startDate, end=endDate, freq='D')
        for d in date_range.astype(str):
            for item in data:
                if d in item["Close"]:
                    data_elem[item["name"]] = item["Close"][d]
            balance = portfolio.rebalance(balance, data_elem)
            value = 0
            for k, v in balance.items():
                value = value + (v["price"] * v["amount"])
            self.values.append(value)

initialCash = 1000000

staticPort = StaticPortfolio(exampleStaticPortfolio, initialCash)

balanceOnlyStock = {
        "stock": { "price": 0, "amount": 0 }
        }
balanceOnlyStock["stock"]["price"] = snp['Close'][0]
balanceOnlyStock["stock"]["amount"] = math.floor(initialCash / balanceOnlyStock["stock"]["price"])

dynamicBalance = { "bond": { "price": 0, "amount": 0, "ratio": 2 },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }, 
        "stock": { "price": 0, "amount": 0, "ratio": 8 }
        }
dynamicBalance["stock"]["price"] = snp['Close'][0]
dynamicBalance["stock"]["amount"] = math.floor((1 * initialCash) / dynamicBalance["stock"]["price"])
dynamicBalance["bond"]["price"] = treas['Close'][0]
dynamicBalance["bond"]["amount"] = math.floor((0 * initialCash) / dynamicBalance["bond"]["price"])

onlyStock = [ (balanceOnlyStock["stock"]["price"] * balanceOnlyStock["stock"]["amount"]) ]
dynamicPortfolio = []
dynamicPortfolio.append((dynamicBalance["stock"]["price"] * dynamicBalance["stock"]["amount"]) + 
            (dynamicBalance["bond"]["price"] * dynamicBalance["bond"]["amount"]))

ratio = []
ewmCnt = 20
for s, b, hi, lo in zip(snp['Close'], treas['Close'], envelopeHiBounds(snp['Close'], ewmCnt), envelopeLoBounds(snp['Close'], ewmCnt)):
    dynamicBalance = rearrangeRatio(dynamicBalance, hi, lo, s)
    ratio.append(dynamicBalance['stock']['ratio'])
    dynamicBalance['stock']['price'] = s
    dynamicBalance['bond']['price'] = b
    dynamicBalance = rebalance(dynamicBalance)
    stockVal = s * dynamicBalance["stock"]["amount"]
    bondVal = b * dynamicBalance["bond"]["amount"]
    cashVal = dynamicBalance["cash"]["amount"]
    dynamicPortfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * balanceOnlyStock["stock"]["amount"])

plt.subplot(3,1,1)
plt.plot(dynamicPortfolio, label='Dynamic Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.plot(staticPort.values, label='Static')
plt.legend(loc='upper left')
plt.subplot(3,1,2)
plt.plot(snp['Close'], label='Stock')
plt.plot(snp['Close'].ewm(ewmCnt).mean(), label='EMA')
plt.plot(envelopeHiBounds(snp['Close'], ewmCnt), label='upper')
plt.plot(envelopeLoBounds(snp['Close'], ewmCnt), label='lower')
plt.legend(loc='upper left')
plt.subplot(3,1,3)
plt.plot(ratio, label='Stock ratio')
plt.show()

print('%d(stock) : %d(bond)' % (ratio[-1], 10 - ratio[-1]))
