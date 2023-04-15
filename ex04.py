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

