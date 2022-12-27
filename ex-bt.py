import bt

data = bt.get('spy,agg', start='2010-01-01')
print(data.head())
