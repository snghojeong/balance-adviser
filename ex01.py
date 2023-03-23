import bt
%matplotlib inline

# fetch some data
data = bt.get('spy,agg', start='2010-01-01')
print(data.head())

# create the strategy
s = bt.Strategy('s1', [bt.algos.RunMonthly(),
                       bt.algos.SelectAll(),
                       bt.algos.WeighEqually(),
                       bt.algos.Rebalance()])

# create a backtest and run it
test = bt.Backtest(s, data)
res = bt.run(test)

# first let's see an equity curve
res.plot();

# ok and what about some stats?
res.display()

# ok and how does the return distribution look like?
res.plot_histogram()

# and just to make sure everything went along as planned, let's plot the security weights over time
res.plot_security_weights()
