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

# create our new strategy
s2 = bt.Strategy('s2', [bt.algos.RunWeekly(),
                        bt.algos.SelectAll(),
                        bt.algos.WeighInvVol(),
                        bt.algos.Rebalance()])

# now let's test it with the same data set. We will also compare it with our first backtest.
test2 = bt.Backtest(s2, data)
# we include test here to see the results side-by-side
res2 = bt.run(test, test2)

res2.plot();
