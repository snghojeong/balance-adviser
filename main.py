from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *

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
portfolio = [ (balanceStockAndBond[5]["stock"]["price"] * balanceStockAndBond[5]["stock"]["amount"]) + 
              (balanceStockAndBond[5]["bond"]["price"] * balanceStockAndBond[5]["bond"]["amount"]) ]

stock = [balanceStockAndBond[5]["stock"]["amount"]]
bond = [balanceStockAndBond[5]["bond"]["amount"]]
cash = [balanceStockAndBond[5]["cash"]["amount"]]

for s, b in zip(snp['Close'], treas['Close']):
    for i in range(0, 9):
        balanceStockAndBond[i]['stock']['price'] = s
        balanceStockAndBond[i]['bond']['price'] = b
        balanceStockAndBond[i] = rebalance(balanceStockAndBond[i])
        stockVal = s * balanceStockAndBond[i]["stock"]["amount"]
        bondVal = b * balanceStockAndBond[i]["bond"]["amount"]
        cashVal = balanceStockAndBond[i]["cash"]["amount"]
        if i == 5:
            portfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * balanceOnlyStock["stock"]["amount"])
    stock.append(balanceStockAndBond[5]["stock"]["amount"])
    bond.append(balanceStockAndBond[5]["bond"]["amount"])
    cash.append(balanceStockAndBond[5]["cash"]["amount"])

print(snp)
print(treas)

plt.subplot(3,1,1)
plt.plot(snp['Close'], label='S&P500')
plt.subplot(3,1,2)
plt.plot(treas['Close'], label='Treasury Bond')
plt.subplot(3,1,3)
plt.plot(portfolio, label='Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.legend()
plt.show()
