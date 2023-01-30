import pandas as pd
from datetime import datetime
from pandas_datareader import data
from matplotlib import pyplot as plt
from rebalance import *
from envelope import *
import bt

s = bt.Strategy('s1', [bt.algos.RunMonthly(),
                       bt.algos.SelectAll(),
                       bt.algos.WeighEqually(),
                       bt.algos.Rebalance()])
test = bt.Backtest(s, data)
res = bt.run(test)
res.plot()
res.display()
res.plot_histogram()
res.plot_security_weights()

# create our new strategy
s2 = bt.Strategy('s2', [bt.algos.RunWeekly(),
                        bt.algos.SelectAll(),
                        bt.algos.WeighInvVol(),
                        bt.algos.Rebalance()])

# now let's test it with the same data set. We will also compare it with our first backtest.
test2 = bt.Backtest(s2, data)
# we include test here to see the results side-by-side
res2 = bt.run(test, test2)

res2.plot()
res2.display()

# download data
data = bt.get('aapl,msft,c,gs,ge', start='2010-01-01')

# calculate moving average DataFrame using pandas' rolling_mean
import pandas as pd
# a rolling mean is a moving average, right?
sma = data.rolling(50).mean()

plot = bt.merge(data, sma).plot(figsize=(15, 5))

class SelectWhere(bt.Algo):

    """
    Selects securities based on an indicator DataFrame.

    Selects securities where the value is True on the current date (target.now).

    Args:
        * signal (DataFrame): DataFrame containing the signal (boolean DataFrame)

    Sets:
        * selected

    """
    def __init__(self, signal):
        self.signal = signal

    def __call__(self, target):
        # get signal on target.now
        if target.now in self.signal.index:
            sig = self.signal.loc[target.now]

            # get indices where true as list
            selected = list(sig.index[sig])

            # save in temp - this will be used by the weighing algo
            target.temp['selected'] = selected

        # return True because we want to keep on moving down the stack
        return True

# first we create the Strategy
s = bt.Strategy('above50sma', [SelectWhere(data > sma),
                               bt.algos.WeighEqually(),
                               bt.algos.Rebalance()])

# now we create the Backtest
t = bt.Backtest(s, data)

# and let's run it!
res = bt.run(t)

# what does the equity curve look like?
res.plot()

# and some performance stats
res.display()

def above_sma(tickers, sma_per=50, start='2010-01-01', name='above_sma'):
    """
    Long securities that are above their n period
    Simple Moving Averages with equal weights.
    """
    # download data
    data = bt.get(tickers, start=start)
    # calc sma
    sma = data.rolling(sma_per).mean()

    # create strategy
    s = bt.Strategy(name, [SelectWhere(data > sma),
                           bt.algos.WeighEqually(),
                           bt.algos.Rebalance()])

    # now we create the backtest
    return bt.Backtest(s, data)

# simple backtest to test long-only allocation
def long_only_ew(tickers, start='2010-01-01', name='long_only_ew'):
    s = bt.Strategy(name, [bt.algos.RunOnce(),
                           bt.algos.SelectAll(),
                           bt.algos.WeighEqually(),
                           bt.algos.Rebalance()])
    data = bt.get(tickers, start=start)
    return bt.Backtest(s, data)

# create the backtests
tickers = 'aapl,msft,c,gs,ge'
sma10 = above_sma(tickers, sma_per=10, name='sma10')
sma20 = above_sma(tickers, sma_per=20, name='sma20')
sma40 = above_sma(tickers, sma_per=40, name='sma40')
benchmark = long_only_ew('spy', name='spy')

# run all the backtests!
res2 = bt.run(sma10, sma20, sma40, benchmark)
res2.plot(freq='m');
res2.display()

class WeighTarget(bt.Algo):
    """
    Sets target weights based on a target weight DataFrame.

    Args:
        * target_weights (DataFrame): DataFrame containing the target weights

    Sets:
        * weights

    """

    def __init__(self, target_weights):
        self.tw = target_weights

    def __call__(self, target):
        # get target weights on date target.now
        if target.now in self.tw.index:
            w = self.tw.loc[target.now]

            # save in temp - this will be used by the weighing algo
            # also dropping any na's just in case they pop up
            target.temp['weights'] = w.dropna()

        # return True because we want to keep on moving down the stack
        return True

# start day of TLT: 2003-01-02
snp = data.DataReader('^GSPC', 'yahoo', start='2003-01-02')
treas = data.DataReader('TLT', 'yahoo', start='2003-01-02')
sbond = data.DataReader('SHY', 'yahoo', start='2003-01-02')
gold = data.DataReader('GLD', 'yahoo', start='2003-01-02')

exampleStaticPortfolio = [
        { "name": "S&P500", "ratio": 3, "data": snp },
        { "name": "TLT",   "ratio": 3, "data": treas },
        { "name": "SHY",   "ratio": 2, "data": sbond },
        { "name": "GLD",   "ratio": 2, "data": gld }
        ]

class StaticPortfolio:
    def __init__(self, portfolio, cash):
        self.name = 'StaticPortfolio'
        self.values = []
        ratiosSum = np.abs([float(v['ratio']) for v in portfolio]).sum()
        balance = dict()
        startDate = datetime(1900, 1, 1, 0, 0)
        endDate = datetime.now()
        balance["cash"] = { "price": 1, 
                            "amount": 0, 
                            "ratio": 0 }
        for item in portfolio:
            price = item["data"]['Close'][0]
            amount = math.floor(cash * (item["ratio"] / ratiosSum / price))
            balance[item["name"]] = { "price": price, 
                                      "amount": amount, 
                                      "ratio": item["ratio"] }
            if startDate < item["data"]['Close'].keys()[0]:
                startDate = item["data"]['Close'].keys()[0]
            if endDate > item["data"]['Close'].keys()[-1]:
                endDate = item["data"]['Close'].keys()[-1]
        date_range = pd.period_range(start=startDate, end=endDate, freq='D')
        for d in date_range.astype(str):
            for item in portfolio:
                if d in item["data"]["Close"]:
                    balance[item["name"]]["price"] = item["data"]["Close"][d]
                    changed = True
            balance = rebalance(balance)
            value = 0
            for k, v in balance.items():
                value = value + (v["price"] * v["amount"])
            self.values.append(value)

class Portfolio:
    def __init__(self, ratio):
        self.name = 'Portfolio'
        self.ratio = ratio
        self.values = []
    def rebalance(balance, price):
        return rebalance(balance)

class Simulator:
    def __init__(self, data, cash, portfolio):
        self.values = []
        balance = dict()
        startDate = datetime(1900, 1, 1, 0, 0)
        endDate = datetime.now()
        balance["cash"] = { "price": 1, 
                            "amount": 0 }
        for item in data:
            price = item['Close'][0]
            if startDate < item['Close'].keys()[0]:
                startDate = item['Close'].keys()[0]
            if endDate > item['Close'].keys()[-1]:
                endDate = item['Close'].keys()[-1]
        data_elem = dict()
        date_range = pd.period_range(start=startDate, end=endDate, freq='D')
        for d in date_range.astype(str):
            for item in data:
                if d in item["Close"]:
                    data_elem[item["name"]] = item["Close"][d]
            balance = portfolio.rebalance(balance, data_elem)
            value = 0
            for k, v in balance.items():
                value = value + (v["price"] * v["amount"])
            self.values.append(value)

initialCash = 10000

staticPort = StaticPortfolio(exampleStaticPortfolio, initialCash)

balanceOnlyStock = {
        "stock": { "price": 0, "amount": 0 }
        }
balanceOnlyStock["stock"]["price"] = snp['Close'][0]
balanceOnlyStock["stock"]["amount"] = math.floor(initialCash / balanceOnlyStock["stock"]["price"])

dynamicBalance = { "bond": { "price": 0, "amount": 0, "ratio": 2 },
        "cash": { "price": 1, "amount": 0, "ratio": 0 }, 
        "stock": { "price": 0, "amount": 0, "ratio": 8 }
        }
dynamicBalance["stock"]["price"] = snp['Close'][0]
dynamicBalance["stock"]["amount"] = math.floor((1 * initialCash) / dynamicBalance["stock"]["price"])
dynamicBalance["bond"]["price"] = treas['Close'][0]
dynamicBalance["bond"]["amount"] = math.floor((0 * initialCash) / dynamicBalance["bond"]["price"])

onlyStock = [ (balanceOnlyStock["stock"]["price"] * balanceOnlyStock["stock"]["amount"]) ]
dynamicPortfolio = []
dynamicPortfolio.append((dynamicBalance["stock"]["price"] * dynamicBalance["stock"]["amount"]) + 
            (dynamicBalance["bond"]["price"] * dynamicBalance["bond"]["amount"]))

ratio = []
ewmCnt = 90
for s, b, hi, lo in zip(snp['Close'], treas['Close'], envelopeHiBounds(snp['Close'], ewmCnt), envelopeLoBounds(snp['Close'], ewmCnt)):
    dynamicBalance = rearrangeRatio(dynamicBalance, hi, lo, s)
    ratio.append(dynamicBalance['stock']['ratio'])
    dynamicBalance['stock']['price'] = s
    dynamicBalance['bond']['price'] = b
    dynamicBalance = rebalance(dynamicBalance)
    stockVal = s * dynamicBalance["stock"]["amount"]
    bondVal = b * dynamicBalance["bond"]["amount"]
    cashVal = dynamicBalance["cash"]["amount"]
    dynamicPortfolio.append(stockVal + bondVal + cashVal)
    onlyStock.append(s * balanceOnlyStock["stock"]["amount"])

plt.subplot(3,1,1)
plt.plot(dynamicPortfolio, label='Dynamic Portfolio')
plt.plot(onlyStock, label='Only Stock')
plt.plot(staticPort.values, label='Static')
plt.legend(loc='upper left')
plt.subplot(3,1,2)
plt.plot(snp['Close'], label='Stock')
plt.plot(snp['Close'].ewm(ewmCnt).mean(), label='EMA')
plt.plot(envelopeHiBounds(snp['Close'], ewmCnt), label='upper')
plt.plot(envelopeLoBounds(snp['Close'], ewmCnt), label='lower')
plt.legend(loc='upper left')
plt.subplot(3,1,3)
plt.plot(ratio, label='Stock ratio')
plt.show()

print('%d(stock) : %d(bond)' % (ratio[-1], 10 - ratio[-1]))
