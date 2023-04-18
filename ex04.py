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
