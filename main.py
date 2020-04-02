from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *

snp = data.DataReader('^GSPC', 'yahoo', start='2003-01-02')
treas = data.DataReader('TLT', 'yahoo', start='2003-01-02')

stockBal = {
        "stock": { "price": 0, "amount": 0 }
        }
stockBal["stock"]["price"] = snp['Close'][0]
stockBal["stock"]["amount"] = 20000

half_bal = { 
        "stock": { "price": 0, "amount": 0, "ratio": 1 }, 
        "bond": { "price": 0, "amount": 0, "ratio": 1 },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }
        }

half_bal["stock"]["price"] = snp['Close'][0]
half_bal["stock"]["amount"] = 10000
half_bal["bond"]["price"] = treas['Close'][0]
half_bal["bond"]["amount"] = math.floor(half_bal["stock"]["price"] * half_bal["stock"]["amount"] / half_bal["bond"]["price"])

onlyStock = [ (stockBal["stock"]["price"] * stockBal["stock"]["amount"]) ]

portfolio = [ (half_bal["stock"]["price"] * half_bal["stock"]["amount"]) + 
              (half_bal["bond"]["price"] * half_bal["bond"]["amount"]) ]

stock = [half_bal["stock"]["amount"]]
bond = [half_bal["bond"]["amount"]]
cash = [half_bal["cash"]["amount"]]

for s, b in zip(snp['Close'], treas['Close']):
    rebalance(half_bal, [s, b, 1])
    stockVal = s * half_bal["stock"]["amount"]
    bondVal = b * half_bal["bond"]["amount"]
    cashVal = half_bal["cash"]["amount"]
    portfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * stockBal["stock"]["amount"])
    stock.append(half_bal["stock"]["amount"])
    bond.append(half_bal["bond"]["amount"])
    cash.append(half_bal["cash"]["amount"])

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
