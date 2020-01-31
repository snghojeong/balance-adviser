import yfinance as yf

snp500 = yf.Ticker("VOO")

# get stock info
snp500.info

# get historical market data
hist = snp500.history(period="max")
print hist
