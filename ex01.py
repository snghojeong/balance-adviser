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

runAfterDaysAlgo = bt.algos.RunAfterDays(
    20*6 + 1
)

selectTheseAlgo = bt.algos.SelectThese(['foo','bar'])

# algo to set the weights so each asset contributes the same amount of risk
#  with data over the last 6 months excluding yesterday
weighERCAlgo = bt.algos.WeighERC(
    lookback=pd.DateOffset(days=20*6),
    covar_method='standard',
    risk_parity_method='slsqp',
    maximum_iterations=1000,
    tolerance=1e-9,
    lag=pd.DateOffset(days=1)
)

rebalAlgo = bt.algos.Rebalance()

strat = bt.Strategy(
    'ERC',
    [
        runAfterDaysAlgo,
        selectTheseAlgo,
        weighERCAlgo,
        rebalAlgo
    ]
)

backtest = bt.Backtest(
    strat,
    pdf,
    integer_positions=False
)

res_target = bt.run(backtest)

res_target.get_security_weights().plot();

res_target.prices.plot();
