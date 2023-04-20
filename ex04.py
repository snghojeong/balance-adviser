import bt
import pandas as pd
from pandas.tseries.frequencies import to_offset
import numpy as np
np.random.seed(1234)
%matplotlib inline

# (Approximate) Price to yield calcs, and pvbp, for later use. Note we use clean price here.
def price_to_yield( p, ttm, coupon ):
    return ( coupon + (100. - p)/ttm ) / ( ( 100. + p)/2. ) * 100
def yield_to_price( y, ttm, coupon ):
    return (coupon + 100/ttm - 0.5 * y) / ( y/200 + 1/ttm)
def pvbp( y, ttm, coupon ):
    return (yield_to_price( y + 0.01, ttm, coupon ) - yield_to_price( y, ttm, coupon ))

# Utility function to set data frame values to nan before the security has been issued or after it has matured
def censor( data, ref_data ):
    for bond in data:
        data.loc[ (data.index > ref_data['mat_date'][bond]) | (data.index < ref_data['issue_date'][bond]), bond] = np.NaN
    return data.ffill(limit=1,axis=0) # Because bonds might mature during a gap in the index (i.e. on the weekend)

# Backtesting timeline setup
start_date = pd.Timestamp('2020-01-01')
end_date = pd.Timestamp('2022-01-01')
timeline = pd.date_range( start_date, end_date, freq='B')

# Government Bonds: Create synthetic data for a single series of rolling government bonds

# Reference Data
roll_freq = 'Q'
maturity = 10
coupon = 2.0
roll_dates = pd.date_range( start_date, end_date+to_offset(roll_freq), freq=roll_freq) # Go one period beyond the end date to be safe
issue_dates = roll_dates - roll_dates.freq
mat_dates = issue_dates + pd.offsets.DateOffset(years=maturity)
series_name = 'govt_10Y'
names = pd.Series(mat_dates).apply( lambda x : 'govt_%s' % x.strftime('%Y_%m'))
# Build a time series of OTR
govt_otr = pd.DataFrame( [ [ name for name, roll_date in zip(names, roll_dates) if roll_date >=d ][0] for d in timeline ],
                        index=timeline,
                        columns=[series_name])
# Create a data frame of reference data
govt_data = pd.DataFrame( {'mat_date':mat_dates, 'issue_date': issue_dates, 'roll_date':roll_dates}, index = names)
govt_data['coupon'] = coupon

# Create the "roll map"
govt_roll_map = govt_otr.copy()
govt_roll_map['target'] = govt_otr[series_name].shift(-1)
govt_roll_map = govt_roll_map[ govt_roll_map[series_name] != govt_roll_map['target']]
govt_roll_map['factor'] = 1.
govt_roll_map = govt_roll_map.reset_index().set_index(series_name).rename(columns={'index':'date'}).dropna()

# Market Data and Risk
govt_yield_initial = 2.0
govt_yield_vol = 1.
govt_yield = pd.DataFrame( columns = govt_data.index, index=timeline )
govt_yield_ts = (govt_yield_initial + np.cumsum( np.random.normal( 0., govt_yield_vol/np.sqrt(252), len(timeline)))).reshape(-1,1)
govt_yield.loc[:,:] = govt_yield_ts

govt_mat = pd.DataFrame( columns = govt_data.index, index=timeline, data=pd.NA ).astype('datetime64')
govt_mat.loc[:,:] = govt_data['mat_date'].values.T
govt_ttm = (govt_mat - timeline.values.reshape(-1,1))/pd.Timedelta('1Y')
govt_coupon = pd.DataFrame( columns = govt_data.index, index=timeline )
govt_coupon.loc[:,:] = govt_data['coupon'].values.T
govt_accrued = govt_coupon.multiply( timeline.to_series().diff()/pd.Timedelta('1Y'), axis=0 )
govt_accrued.iloc[0] = 0

govt_price = yield_to_price( govt_yield, govt_ttm, govt_coupon )
govt_price[ govt_ttm <= 0 ] = 100.
govt_price = censor(govt_price, govt_data)
govt_pvbp = pvbp( govt_yield, govt_ttm, govt_coupon)
govt_pvbp[ govt_ttm <= 0 ] = 0.
govt_pvbp = censor(govt_pvbp, govt_data)

# Corporate Bonds: Create synthetic data for a universe of corporate bonds

# Reference Data
n_corp = 50    # Number of corporate bonds to generate
avg_ttm = 10   # Average time to maturity, in years
coupon_mean = 5
coupon_std = 1.5
mat_dates = start_date + np.random.exponential(avg_ttm*365, n_corp).astype(int) * pd.offsets.Day()
issue_dates = np.minimum( mat_dates, end_date ) - np.random.exponential(avg_ttm*365, n_corp).astype(int) * pd.offsets.Day()
names = pd.Series( [ 'corp{:04d}'.format(i) for i in range(n_corp)])
coupons = np.random.normal( coupon_mean, coupon_std, n_corp ).round(3)
corp_data = pd.DataFrame( {'mat_date':mat_dates, 'issue_date': issue_dates, 'coupon':coupons}, index=names)

# Market Data and Risk
# Model: corporate yield = government yield + credit spread
# Model: credit spread changes = beta * common factor changes + idiosyncratic changes
corp_spread_initial = np.random.normal( 2, 1, len(corp_data) )
corp_betas_raw = np.random.normal( 1, 0.5, len(corp_data) )
corp_factor_vol = 0.5
corp_idio_vol = 0.5
corp_factor_ts = np.cumsum( np.random.normal( 0, corp_factor_vol/np.sqrt(252), len(timeline))).reshape(-1,1)
corp_idio_ts = np.cumsum( np.random.normal( 0, corp_idio_vol/np.sqrt(252), len(timeline))).reshape(-1,1)
corp_spread = corp_spread_initial + np.multiply( corp_factor_ts, corp_betas_raw ) + corp_idio_ts
corp_yield = govt_yield_ts + corp_spread
corp_yield = pd.DataFrame(  columns = corp_data.index, index=timeline, data = corp_yield )

corp_mat = pd.DataFrame( columns = corp_data.index, index=timeline, data=start_date )
corp_mat.loc[:,:] = corp_data['mat_date'].values.T
corp_ttm = (corp_mat - timeline.values.reshape(-1,1))/pd.Timedelta('1Y')
corp_coupon = pd.DataFrame( columns = corp_data.index, index=timeline )
corp_coupon.loc[:,:] = corp_data['coupon'].values.T
corp_accrued = corp_coupon.multiply( timeline.to_series().diff()/pd.Timedelta('1Y'), axis=0 )
corp_accrued.iloc[0] = 0

corp_price = yield_to_price( corp_yield, corp_ttm, corp_coupon )
corp_price[ corp_ttm <= 0 ] = 100.
corp_price = censor(corp_price, corp_data)

corp_pvbp = pvbp( corp_yield, corp_ttm, corp_coupon)
corp_pvbp[ corp_ttm <= 0 ] = 0.
corp_pvbp = censor(corp_pvbp, corp_data)

bidoffer_bps = 5.
corp_bidoffer = -bidoffer_bps * corp_pvbp

corp_betas = pd.DataFrame( columns = corp_data.index, index=timeline )
corp_betas.loc[:,:] = corp_betas_raw
corp_betas = censor(corp_betas, corp_data)

# Set up a strategy and a backtest

# The goal here is to define an equal weighted portfolio of corporate bonds,
# and to hedge the rates risk with the rolling series of government bonds

# Define Algo Stacks as the various building blocks
# Note that the order in which we execute these is extremely important

lifecycle_stack = bt.core.AlgoStack(
    # Close any matured bond positions (including hedges)
    bt.algos.ClosePositionsAfterDates( 'maturity' ),
    # Roll government bond positions into the On The Run
    bt.algos.RollPositionsAfterDates( 'govt_roll_map' ),
)
risk_stack = bt.AlgoStack(
    # Specify how frequently to calculate risk
    bt.algos.Or( [bt.algos.RunWeekly(),
                  bt.algos.RunMonthly()] ),
    # Update the risk given any positions that have been put on so far in the current step
    bt.algos.UpdateRisk( 'pvbp', history=1),
    bt.algos.UpdateRisk( 'beta', history=1),
)
hedging_stack = bt.AlgoStack(
    # Specify how frequently to hedge risk
    bt.algos.RunMonthly(),
    # Select the "alias" for the on-the-run government bond...
    bt.algos.SelectThese( [series_name], include_no_data = True ),
    # ... and then resolve it to the underlying security for the given date
    bt.algos.ResolveOnTheRun( 'govt_otr' ),
    # Hedge out the pvbp risk using the selected government bond
    bt.algos.HedgeRisks( ['pvbp']),
    # Need to update risk again after hedging so that it gets recorded correctly (post-hedges)
    bt.algos.UpdateRisk( 'pvbp', history=True),
)
debug_stack = bt.core.AlgoStack(
    # Specify how frequently to display debug info
    bt.algos.RunMonthly(),
    bt.algos.PrintInfo('Strategy {name} : {now}.\tNotional:  {_notl_value:0.0f},\t Value: {_value:0.0f},\t Price: {_price:0.4f}'),
    bt.algos.PrintRisk('Risk: \tPVBP: {pvbp:0.0f},\t Beta: {beta:0.0f}'),
)
trading_stack =bt.core.AlgoStack(
         # Specify how frequently to rebalance the portfolio
         bt.algos.RunMonthly(),
         # Select instruments for rebalancing. Start with everything
         bt.algos.SelectAll(),
         # Prevent matured/rolled instruments from coming back into the mix
         bt.algos.SelectActive(),
         # Select only corp instruments
         bt.algos.SelectRegex( 'corp' ),
         # Specify how to weigh the securities
         bt.algos.WeighEqually(),
         # Set the target portfolio size
         bt.algos.SetNotional( 'notional_value' ),
         # Rebalance the portfolio
         bt.algos.Rebalance()
)

govt_securities = [ bt.CouponPayingHedgeSecurity( name ) for name in govt_data.index]
corp_securities = [ bt.CouponPayingSecurity( name ) for name in corp_data.index ]
securities = govt_securities + corp_securities
base_strategy = bt.FixedIncomeStrategy('BaseStrategy', [ lifecycle_stack, bt.algos.Or( [trading_stack, risk_stack, debug_stack ] ) ], children = securities)
hedged_strategy = bt.FixedIncomeStrategy('HedgedStrategy', [ lifecycle_stack, bt.algos.Or( [trading_stack, risk_stack, hedging_stack, debug_stack ] ) ], children = securities)

#Collect all the data for the strategies

# Here we use clean prices as the data and accrued as the coupon. Could alternatively use dirty prices and cashflows.
data = pd.concat( [ govt_price, corp_price ], axis=1) / 100.  # Because we need prices per unit notional
additional_data = { 'coupons' : pd.concat([govt_accrued, corp_accrued], axis=1) / 100.,
                   'bidoffer' : corp_bidoffer/100.,
                   'notional_value' : pd.Series( data=1e6, index=data.index ),
                   'maturity' : pd.concat([govt_data, corp_data], axis=0).rename(columns={"mat_date": "date"}),
                   'govt_roll_map' : govt_roll_map,
                   'govt_otr' : govt_otr,
                   'unit_risk' : {'pvbp' : pd.concat( [ govt_pvbp, corp_pvbp] ,axis=1)/100.,
                                  'beta' : corp_betas * corp_pvbp / 100.},
                  }
base_test = bt.Backtest( base_strategy, data, 'BaseBacktest',
                initial_capital = 0,
                additional_data = additional_data )
hedge_test = bt.Backtest( hedged_strategy, data, 'HedgedBacktest',
                initial_capital = 0,
                additional_data = additional_data)
out = bt.run( base_test, hedge_test )
