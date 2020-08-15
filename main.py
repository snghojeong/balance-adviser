import pandas as pd
from datetime import datetime
from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *
from envelope import *

# TLT start='2003-01-02'
snp = data.DataReader('^GSPC', 'yahoo', start='2003-01-02')
treas = data.DataReader('TLT', 'yahoo', start='2003-01-02')

exampleStaticPortfolio = [
        { "name": "S&P500", "ratio": 8, "data": snp },
        { "name": "TLT",   "ratio": 2, "data": treas }
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
            balance = rebalance(balance)
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

balanceStockAndBond = []
for i in range(0, 9):
    balanceStockAndBond.append( {
        "bond": { "price": 0, "amount": 0, "ratio": (10 - i) },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }, 
        "stock": { "price": 0, "amount": 0, "ratio": i }
        } )
    ratios = [float(v['ratio']) for k, v in balanceStockAndBond[i].items()]
    normRatios = ratios / np.abs(ratios).sum()
    balanceStockAndBond[i]["stock"]["price"] = snp['Close'][0]
    balanceStockAndBond[i]["stock"]["amount"] = math.floor((normRatios[2] * initialCash) / balanceStockAndBond[i]["stock"]["price"])
    balanceStockAndBond[i]["bond"]["price"] = treas['Close'][0]
    balanceStockAndBond[i]["bond"]["amount"] = math.floor((normRatios[0] * initialCash) / balanceStockAndBond[i]["bond"]["price"])
dynamicBalance = { "bond": { "price": 0, "amount": 0, "ratio": 2 },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }, 
        "stock": { "price": 0, "amount": 0, "ratio": 8 }
        }
dynamicBalance["stock"]["price"] = snp['Close'][0]
dynamicBalance["stock"]["amount"] = math.floor((normRatios[2] * initialCash) / dynamicBalance["stock"]["price"])
dynamicBalance["bond"]["price"] = treas['Close'][0]
dynamicBalance["bond"]["amount"] = math.floor((normRatios[0] * initialCash) / dynamicBalance["bond"]["price"])

onlyStock = [ (balanceOnlyStock["stock"]["price"] * balanceOnlyStock["stock"]["amount"]) ]
staticPortfolio = []
dynamicPortfolio = []
stock = []
bond = []
cash = []
ratio = []
for i in range(0, 9):
    staticPortfolio.append([ (balanceStockAndBond[i]["stock"]["price"] * balanceStockAndBond[i]["stock"]["amount"]) + 
            (balanceStockAndBond[i]["bond"]["price"] * balanceStockAndBond[i]["bond"]["amount"]) ])
    stock.append([balanceStockAndBond[i]["stock"]["amount"]])
    bond.append([balanceStockAndBond[i]["bond"]["amount"]])
    cash.append([balanceStockAndBond[i]["cash"]["amount"]])
dynamicPortfolio.append((balanceStockAndBond[i]["stock"]["price"] * balanceStockAndBond[i]["stock"]["amount"]) + 
            (balanceStockAndBond[i]["bond"]["price"] * balanceStockAndBond[i]["bond"]["amount"]))

ewmCnt = 100
for s, b, hi, lo in zip(snp['Close'], treas['Close'], envelopeHiBounds(snp['Close'], ewmCnt), envelopeLoBounds(snp['Close'], ewmCnt)):
    for i in range(0, 9):
        balanceStockAndBond[i]['stock']['price'] = s
        balanceStockAndBond[i]['bond']['price'] = b
        balanceStockAndBond[i] = rebalance(balanceStockAndBond[i])
        stockVal = s * balanceStockAndBond[i]["stock"]["amount"]
        bondVal = b * balanceStockAndBond[i]["bond"]["amount"]
        cashVal = balanceStockAndBond[i]["cash"]["amount"]
        staticPortfolio[i].append(stockVal + bondVal + cashVal)
        stock[i].append(balanceStockAndBond[i]["stock"]["amount"])
        bond[i].append(balanceStockAndBond[i]["bond"]["amount"])
        cash[i].append(balanceStockAndBond[i]["cash"]["amount"])
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
#plt.plot(staticPortfolio[5], label='Static Portfolio')
plt.plot(staticPort.values, label='Static Portfolio')
plt.plot(dynamicPortfolio, label='Dynamic Portfolio')
plt.plot(onlyStock, label='Only Stock')
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
