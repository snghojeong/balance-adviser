from pandas_datareader import data
from matplotlib import pyplot as plt

snp = data.DataReader('^GSPC','yahoo',start='1990-01-01')
treas = data.DataReader('VFITX','yahoo',start='1990-01-01')

half_bal = { 
        "stock": { "price": 0, "amount": 0 }, 
        "bond": { "price": 0, "amount": 0 }
        }

plt.subplot(1,2,1)
plt.plot(snp['Close'], label='Close')
plt.subplot(1,2,2)
plt.plot(treas['Close'], label='Close')
plt.show()
