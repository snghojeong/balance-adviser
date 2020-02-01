import yfinance as yf
from matplotlib import pyplot as plt

snp500 = yf.Ticker("VOO")

# get stock info
snp500.info

# get historical market data
hist = snp500.history(period="max")

plt.plot(hist)
plt.show()
