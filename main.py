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

balanceStockAndBond = { 
        "stock": { "price": 0, "amount": 0, "ratio": 1 }, 
        "bond": { "price": 0, "amount": 0, "ratio": 1 },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }
        }

ratios = [v['ratio'] for k, v in balanceStockAndBond.items()]
normRatios = ratios / np.abs(ratios).sum()
balanceStockAndBond["stock"]["price"] = snp['Close'][0]
balanceStockAndBond["stock"]["amount"] = math.floor((normRatios[0] * initialCash) / balanceStockAndBond["stock"]["price"])
balanceStockAndBond["bond"]["price"] = treas['Close'][0]
balanceStockAndBond["bond"]["amount"] = math.floor((normRatios[1] * initialCash) / balanceStockAndBond["bond"]["price"])

onlyStock = [ (balanceOnlyStock["stock"]["price"] * balanceOnlyStock["stock"]["amount"]) ]

portfolio = [ (balanceStockAndBond["stock"]["price"] * balanceStockAndBond["stock"]["amount"]) + 
              (balanceStockAndBond["bond"]["price"] * balanceStockAndBond["bond"]["amount"]) ]

stock = [balanceStockAndBond["stock"]["amount"]]
bond = [balanceStockAndBond["bond"]["amount"]]
cash = [balanceStockAndBond["cash"]["amount"]]

for s, b in zip(snp['Close'], treas['Close']):
    balanceStockAndBond['stock']['price'] = s
    balanceStockAndBond['bond']['price'] = b
    rebalance(balanceStockAndBond)
    stockVal = s * balanceStockAndBond["stock"]["amount"]
    bondVal = b * balanceStockAndBond["bond"]["amount"]
    cashVal = balanceStockAndBond["cash"]["amount"]
    portfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * balanceOnlyStock["stock"]["amount"])
    stock.append(balanceStockAndBond["stock"]["amount"])
    bond.append(balanceStockAndBond["bond"]["amount"])
    cash.append(balanceStockAndBond["cash"]["amount"])

print(snp)
print(treas)

plt.subplot(3,2,1)
plt.plot(snp['Close'], label='S&P500')
plt.subplot(3,2,3)
plt.plot(treas['Close'], label='Treasury Bond')
plt.subplot(3,2,5)
plt.plot(portfolio, label='Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.subplot(3,2,2)
plt.plot(stock, label='Portfolio-Stock')
plt.subplot(3,2,4)
plt.plot(bond, label='Portfolio-Bond')
plt.subplot(3,2,6)
plt.plot(cash, label='Portfolio-Cash')
plt.show()
