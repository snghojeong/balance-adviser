import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import ffn
import bt

%matplotlib inline

names = ['foo','bar','rf']
dates = pd.date_range(start='2015-01-01',end='2018-12-31', freq=pd.tseries.offsets.BDay())
n = len(dates)
rdf = pd.DataFrame(
    np.zeros((n, len(names))),
    index = dates,
    columns = names
)

np.random.seed(1)
rdf['foo'] = np.random.normal(loc = 0.1/252,scale=0.2/np.sqrt(252),size=n)
rdf['bar'] = np.random.normal(loc = 0.04/252,scale=0.05/np.sqrt(252),size=n)
rdf['rf'] = 0.

pdf = 100*np.cumprod(1+rdf)
pdf.plot();

selectTheseAlgo = bt.algos.SelectThese(['foo','bar'])

# algo to set the weights to 1/vol contributions from each asset
#  with data over the last 3 months excluding yesterday
weighInvVolAlgo = bt.algos.WeighInvVol(
    lookback=pd.DateOffset(months=3),
    lag=pd.DateOffset(days=1)
)

# algo to rebalance the current weights to weights set in target.temp
rebalAlgo = bt.algos.Rebalance()

# a strategy that rebalances daily to 1/vol weights
strat = bt.Strategy(
    'Target',
    [
        selectTheseAlgo,
        weighInvVolAlgo,
        rebalAlgo
    ]
)

# set integer_positions=False when positions are not required to be integers(round numbers)
backtest = bt.Backtest(
    strat,
    pdf,
    integer_positions=False
)

res_target = bt.run(backtest)
res_target.get_security_weights().plot();

# algo to fire whenever predicted tracking error is greater than 1%
wdf = res_target.get_security_weights()

PTE_rebalance_Algo = bt.algos.PTE_Rebalance(
    0.01,
    wdf,
    lookback=pd.DateOffset(months=3),
    lag=pd.DateOffset(days=1),
    covar_method='standard',
    annualization_factor=252
)

selectTheseAlgo = bt.algos.SelectThese(['foo','bar'])

# algo to set the weights to 1/vol contributions from each asset
#  with data over the last 12 months excluding yesterday
weighTargetAlgo = bt.algos.WeighTarget(
    wdf
)

rebalAlgo = bt.algos.Rebalance()

# a strategy that rebalances monthly to specified weights
strat = bt.Strategy(
    'PTE',
    [
        PTE_rebalance_Algo,
        selectTheseAlgo,
        weighTargetAlgo,
        rebalAlgo
    ]
)

# set integer_positions=False when positions are not required to be integers(round numbers)
backtest = bt.Backtest(
    strat,
    pdf,
    integer_positions=False
)

res_PTE = bt.run(backtest)
