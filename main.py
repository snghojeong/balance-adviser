from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *

snp = data.DataReader('^GSPC', 'yahoo', start='1992-01-02')
treas = data.DataReader('VFITX', 'yahoo', start='1992-01-02')

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
half_bal["bond"]["amount"] = 410000

onlyStock = [ (stockBal["stock"]["price"] * stockBal["stock"]["amount"]) ]

portfolio = [ (half_bal["stock"]["price"] * half_bal["stock"]["amount"]) + 
              (half_bal["bond"]["price"] * half_bal["bond"]["amount"]) ]

for s, b in zip(snp['Close'], treas['Close']):
    rebalance(half_bal, [s, b, 1])
    stockVal = s * half_bal["stock"]["amount"]
    bondVal = b * half_bal["bond"]["amount"]
    cashVal = half_bal["cash"]["amount"]
    portfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * stockBal["stock"]["amount"])

print(snp)
print(treas)

plt.subplot(3,1,1)
plt.plot(snp['Close'], label='S&P500')
plt.subplot(3,1,2)
plt.plot(treas['Close'], label='Treasury Bond')
plt.subplot(3,1,3)
plt.plot(portfolio, label='Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.show()
