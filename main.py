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

## download some data & calc SMAs
data = bt.get('spy', start='2010-01-01')
sma50 = data.rolling(50).mean()
sma200 = data.rolling(200).mean()

## now we need to calculate our target weight DataFrame
# first we will copy the sma200 DataFrame since our weights will have the same strucutre
tw = sma200.copy()
# set appropriate target weights
tw[sma50 > sma200] = 1.0
tw[sma50 <= sma200] = -1.0
# here we will set the weight to 0 - this is because the sma200 needs 200 data points before
# calculating its first point. Therefore, it will start with a bunch of nulls (NaNs).
tw[sma200.isnull()] = 0.0

# plot the target weights + chart of price & SMAs
tmp = bt.merge(tw, data, sma50, sma200)
tmp.columns = ['tw', 'price', 'sma50', 'sma200']
ax = tmp.plot(figsize=(15,5), secondary_y=['tw'])

# first let's create a helper function to create a ma cross backtest
def ma_cross(ticker, start='2010-01-01',
             short_ma=50, long_ma=200, name='ma_cross'):
    # these are all the same steps as above
    data = bt.get(ticker, start=start)
    short_sma = data.rolling(short_ma).mean()
    long_sma  = data.rolling(long_ma).mean()

    # target weights
    tw = long_sma.copy()
    tw[short_sma > long_sma] = 1.0
    tw[short_sma <= long_sma] = -1.0
    tw[long_sma.isnull()] = 0.0

    # here we specify the children (3rd) arguemnt to make sure the strategy
    # has the proper universe. This is necessary in strategies of strategies
    s = bt.Strategy(name, [WeighTarget(tw), bt.algos.Rebalance()], [ticker])

    return bt.Backtest(s, data)

# ok now let's create a few backtests and gather the results.
# these will later become our "synthetic securities"
t1 = ma_cross('aapl', name='aapl_ma_cross')
t2 = ma_cross('msft', name='msft_ma_cross')

# let's run these strategies now
res = bt.run(t1, t2)

# now that we have run the strategies, let's extract
# the data to create "synthetic securities"
data = bt.merge(res['aapl_ma_cross'].prices, res['msft_ma_cross'].prices)

# now we have our new data. This data is basically the equity
# curves of both backtested strategies. Now we can just use this
# to test any old strategy, just like before.
s = bt.Strategy('s', [bt.algos.SelectAll(),
                      bt.algos.WeighInvVol(),
                      bt.algos.Rebalance()])

# create and run
t = bt.Backtest(s, data)
res = bt.run(t)

res.plot();

# once again, we will create a few backtests
# these will be the child strategies
t1 = ma_cross('aapl', name='aapl_ma_cross')
t2 = ma_cross('msft', name='msft_ma_cross')

# let's extract the data object
data = bt.merge(t1.data, t2.data)

# now we create the parent strategy
# we specify the children to be the two
# strategies created above
s = bt.Strategy('s', [bt.algos.SelectAll(),
                      bt.algos.WeighInvVol(),
                      bt.algos.Rebalance()],
                [t1.strategy, t2.strategy])

# create and run
t = bt.Backtest(s, data)
res = bt.run(t)

res.plot()
res.plot_weights()


names = ['foo','bar','rf']
dates = pd.date_range(start='2017-01-01',end='2017-12-31', freq=pd.tseries.offsets.BDay())
n = len(dates)
rdf = pd.DataFrame(
    np.zeros((n, len(names))),
    index = dates,
    columns = names
)

np.random.seed(1)
rdf['foo'] = np.random.normal(loc = 0.1/n,scale=0.2/np.sqrt(n),size=n)
rdf['bar'] = np.random.normal(loc = 0.04/n,scale=0.05/np.sqrt(n),size=n)
rdf['rf'] = 0.

pdf = 100*np.cumprod(1+rdf)
pdf.plot()

# algo to fire on the beginning of every month and to run on the first date
runMonthlyAlgo = bt.algos.RunMonthly(
    run_on_first_date=True
)

# algo to set the weights
#  it will only run when runMonthlyAlgo returns true
#  which only happens on the first of every month
weights = pd.Series([0.6,0.4,0.],index = rdf.columns)
weighSpecifiedAlgo = bt.algos.WeighSpecified(**weights)

# algo to rebalance the current weights to weights set by weighSpecified
#  will only run when weighSpecifiedAlgo returns true
#  which happens every time it runs
rebalAlgo = bt.algos.Rebalance()

# a strategy that rebalances monthly to specified weights
strat = bt.Strategy('static',
    [
        runMonthlyAlgo,
        weighSpecifiedAlgo,
        rebalAlgo
    ]
)

# set integer_positions=False when positions are not required to be integers(round numbers)
backtest = bt.Backtest(
    strat,
    pdf,
    integer_positions=False
)

res = bt.run(backtest)
res.stats
res.prices.head()
res.plot_security_weights()

performanceStats = res['static']
#performance stats is an ffn object
res.backtest_list[0].strategy.values.plot();

res.backtest_list[0].strategy.outlays.plot();

security_names = res.backtest_list[0].strategy.outlays.columns


res.backtest_list[0].strategy.outlays/pdf.loc[:,security_names]
res.backtest_list[0].positions.diff(1)
res.backtest_list[0].positions

rf = 0.04
np.random.seed(1)
mus = np.random.normal(loc=0.05,scale=0.02,size=5) + rf
sigmas = (mus - rf)/0.3 + np.random.normal(loc=0.,scale=0.01,size=5)

num_years = 10
num_months_per_year = 12
num_days_per_month = 21
num_days_per_year = num_months_per_year*num_days_per_month

rdf = pd.DataFrame(
    index = pd.date_range(
        start="2008-01-02",
        periods=num_years*num_months_per_year*num_days_per_month,
        freq="B"
    ),
    columns=['foo','bar','baz','fake1','fake2']
)

for i,mu in enumerate(mus):
    sigma = sigmas[i]
    rdf.iloc[:,i] = np.random.normal(
        loc=mu/num_days_per_year,
        scale=sigma/np.sqrt(num_days_per_year),
        size=rdf.shape[0]
    )
pdf = np.cumprod(1+rdf)*100

pdf.plot();

sma  = pdf.rolling(window=num_days_per_month*12,center=False).median().shift(1)
plt.plot(pdf.index,pdf['foo'])
plt.plot(sma.index,sma['foo'])
plt.show()

#sma with 1 day lag
sma.tail()
#sma with 0 day lag
pdf.rolling(window=num_days_per_month*12,center=False).median().tail()
# target weights
trend = sma.copy()
trend[pdf > sma] = True
trend[pdf <= sma] = False
trend[sma.isnull()] = False
trend.tail()

tsmom_invvol_strat = bt.Strategy(
    'tsmom_invvol',
    [
        bt.algos.RunDaily(),
        bt.algos.SelectWhere(trend),
        bt.algos.WeighInvVol(),
        bt.algos.LimitWeights(limit=0.4),
        bt.algos.Rebalance()
    ]
)

tsmom_ew_strat = bt.Strategy(
    'tsmom_ew',
    [
        bt.algos.RunDaily(),
        bt.algos.SelectWhere(trend),
        bt.algos.WeighEqually(),
        bt.algos.LimitWeights(limit=0.4),
        bt.algos.Rebalance()
    ]
)

# create and run
tsmom_invvol_bt = bt.Backtest(
    tsmom_invvol_strat,
    pdf,
    initial_capital=50000000.0,
    commissions=lambda q, p: max(100, abs(q) * 0.0021),
    integer_positions=False,
    progress_bar=True
)
tsmom_invvol_res = bt.run(tsmom_invvol_bt)

tsmom_ew_bt = bt.Backtest(
    tsmom_ew_strat,
    pdf,

    initial_capital=50000000.0,
    commissions=lambda q, p: max(100, abs(q) * 0.0021),
    integer_positions=False,
    progress_bar=True
)
tsmom_ew_res = bt.run(tsmom_ew_bt)

ax = plt.subplot()
ax.plot(tsmom_ew_res.prices.index,tsmom_ew_res.prices,label='EW')
pdf.plot(ax=ax)

ax.legend()
plt.legend()
plt.show()

tsmom_ew_res.stats

np.random.seed(0)
returns =  np.random.normal(0.08/12,0.2/np.sqrt(12),12*10)
pdf = pd.DataFrame(
    np.cumprod(1+returns),
    index = pd.date_range(start="2008-01-01",periods=12*10,freq="m"),
    columns=['foo']
)

pdf.plot();

runMonthlyAlgo = bt.algos.RunMonthly()
rebalAlgo = bt.algos.Rebalance()

class Signal(bt.Algo):

    """

    Mostly copied from StatTotalReturn

    Sets temp['Signal'] with total returns over a given period.

    Sets the 'Signal' based on the total return of each
    over a given lookback period.

    Args:
        * lookback (DateOffset): lookback period.
        * lag (DateOffset): Lag interval. Total return is calculated in
            the inteval [now - lookback - lag, now - lag]

    Sets:
        * stat

    Requires:
        * selected

    """

    def __init__(self, lookback=pd.DateOffset(months=3),
                 lag=pd.DateOffset(days=0)):
        super(Signal, self).__init__()
        self.lookback = lookback
        self.lag = lag

    def __call__(self, target):
        selected = 'foo'
        t0 = target.now - self.lag

        if target.universe[selected].index[0] > t0:
            return False
        prc = target.universe[selected].loc[t0 - self.lookback:t0]


        trend = prc.iloc[-1]/prc.iloc[0] - 1
        signal = trend > 0.

        if signal:
            target.temp['Signal'] = 1.
        else:
            target.temp['Signal'] = 0.

        return True

signalAlgo = Signal(pd.DateOffset(months=12),pd.DateOffset(months=1))

class WeighFromSignal(bt.Algo):

    """
    Sets temp['weights'] from the signal.
    Sets:
        * weights

    Requires:
        * selected

    """

    def __init__(self):
        super(WeighFromSignal, self).__init__()

    def __call__(self, target):
        selected = 'foo'
        if target.temp['Signal'] is None:
            raise(Exception('No Signal!'))

        target.temp['weights'] = {selected : target.temp['Signal']}
        return True

weighFromSignalAlgo = WeighFromSignal()

s = bt.Strategy(
    'example1',
    [
        runMonthlyAlgo,
        signalAlgo,
        weighFromSignalAlgo,
        rebalAlgo
    ]
)

t = bt.Backtest(s, pdf, integer_positions=False, progress_bar=True)
res = bt.run(t)

rf = 0.04
np.random.seed(1)
mus = np.random.normal(loc=0.05,scale=0.02,size=5) + rf
sigmas = (mus - rf)/0.3 + np.random.normal(loc=0.,scale=0.01,size=5)

num_years = 10
num_months_per_year = 12
num_days_per_month = 21
num_days_per_year = num_months_per_year*num_days_per_month

rdf = pd.DataFrame(
    index = pd.date_range(
        start="2008-01-02",
        periods=num_years*num_months_per_year*num_days_per_month,
        freq="B"
    ),
    columns=['foo','bar','baz','fake1','fake2']
)

for i,mu in enumerate(mus):
    sigma = sigmas[i]
    rdf.iloc[:,i] = np.random.normal(
        loc=mu/num_days_per_year,
        scale=sigma/np.sqrt(num_days_per_year),
        size=rdf.shape[0]
    )
pdf = np.cumprod(1+rdf)*100
pdf.iloc[0,:] = 100

pdf.plot();

strategy_names = np.array(
    [
        'Equal Weight',
        'Inv Vol'
    ]
)

runMonthlyAlgo = bt.algos.RunMonthly(
    run_on_first_date=True,
    run_on_end_of_period=True
)
selectAllAlgo = bt.algos.SelectAll()
rebalanceAlgo = bt.algos.Rebalance()

strats = []
tests = []

for i,s in enumerate(strategy_names):
    if s == "Equal Weight":
        wAlgo = bt.algos.WeighEqually()
    elif s == "Inv Vol":
        wAlgo = bt.algos.WeighInvVol()

    strat = bt.Strategy(
        str(s),
        [
            runMonthlyAlgo,
            selectAllAlgo,
            wAlgo,
            rebalanceAlgo
        ]
    )
    strats.append(strat)

    t = bt.Backtest(
        strat,
        pdf,
        integer_positions = False,
        progress_bar=False
    )
    tests.append(t)

combined_strategy = bt.Strategy(
    'Combined',
    algos = [
        runMonthlyAlgo,
        selectAllAlgo,
        bt.algos.WeighEqually(),
        rebalanceAlgo
    ],
    children = [x.strategy for x in tests]
)

combined_test = bt.Backtest(
    combined_strategy,
    pdf,
    integer_positions = False,
    progress_bar = False
)

res = bt.run(combined_test)


strategy_names = np.array(
    [
        'Equal Weight',
        'Inv Vol'
    ]
)

runMonthlyAlgo = bt.algos.RunMonthly(
    run_on_first_date=True,
    run_on_end_of_period=True
)
selectAllAlgo = bt.algos.SelectAll()
rebalanceAlgo = bt.algos.Rebalance()

strats = []
tests = []
results = []

for i,s in enumerate(strategy_names):
    if s == "Equal Weight":
        wAlgo = bt.algos.WeighEqually()
    elif s == "Inv Vol":
        wAlgo = bt.algos.WeighInvVol()

    strat = bt.Strategy(
        s,
        [
            runMonthlyAlgo,
            selectAllAlgo,
            wAlgo,
            rebalanceAlgo
        ]
    )
    strats.append(strat)

    t = bt.Backtest(
        strat,
        pdf,
        integer_positions = False,
        progress_bar=False
    )
    tests.append(t)

    res = bt.run(t)
    results.append(res)



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
