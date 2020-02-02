from pandas_datareader import data
from matplotlib import pyplot as plt

df = data.DataReader('005930.KS','yahoo','2019-01-01','2019-12-31')

plt.plot(df['Close'], label='Close')
plt.show()
