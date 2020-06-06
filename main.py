from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *
from envelope import *

snp = data.DataReader('^GSPC', 'yahoo', start='2003-01-02')
treas = data.DataReader('TLT', 'yahoo', start='2003-01-02')

initialCash = 1000000

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

onlyStock = [ (balanceOnlyStock["stock"]["price"] * balanceOnlyStock["stock"]["amount"]) ]
portfolio = []
stock = []
bond = []
cash = []
for i in range(0, 9):
    portfolio.append([ (balanceStockAndBond[i]["stock"]["price"] * balanceStockAndBond[i]["stock"]["amount"]) + 
            (balanceStockAndBond[i]["bond"]["price"] * balanceStockAndBond[i]["bond"]["amount"]) ])
    stock.append([balanceStockAndBond[i]["stock"]["amount"]])
    bond.append([balanceStockAndBond[i]["bond"]["amount"]])
    cash.append([balanceStockAndBond[i]["cash"]["amount"]])

upperBound = []
lowerBound = []
stockEMA = snp['Close'].ewm(100).mean()
for s, b, ema in zip(snp['Close'], treas['Close'], stockEMA):
    for i in range(0, 9):
        balanceStockAndBond[i]['stock']['price'] = s
        balanceStockAndBond[i]['bond']['price'] = b
        balanceStockAndBond[i] = rebalance(balanceStockAndBond[i])
        stockVal = s * balanceStockAndBond[i]["stock"]["amount"]
        bondVal = b * balanceStockAndBond[i]["bond"]["amount"]
        cashVal = balanceStockAndBond[i]["cash"]["amount"]
        portfolio[i].append(stockVal + bondVal + cashVal)
        stock[i].append(balanceStockAndBond[i]["stock"]["amount"])
        bond[i].append(balanceStockAndBond[i]["bond"]["amount"])
        cash[i].append(balanceStockAndBond[i]["cash"]["amount"])
    onlyStock.append(s * balanceOnlyStock["stock"]["amount"])
    upperBound.append(envelopeHiBound(ema))
    lowerBound.append(envelopeLoBound(ema))

print(snp)
print(treas)

plt.subplot(1,1,1)
plt.plot(portfolio[5], label='Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.plot(snp['Close'], label='Stock')
plt.plot(stockEMA, label='EMA')
plt.plot(upperBound, label='upper')
plt.plot(lowerBound, label='lower')
plt.legend(loc='upper left')
plt.show()
