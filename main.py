from pandas_datareader import data
from matplotlib import pyplot as plt

plt.subplot(1,2,1)
df = data.DataReader('^GSPC','yahoo',start='1950-01-01')
plt.plot(df['Close'], label='Close')
plt.subplot(1,2,2)
df = data.DataReader('VUSTX','yahoo',start='1950-01-01')
plt.plot(df['Close'], label='Close')
plt.show()
