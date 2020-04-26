import math
import numpy as np

def assetsDict(balance):
    for k, v in balance.items():
        v['value'] = v['amount'] * v['price']
    return balance

def normalize(balance):
    total = 0
    for k, v in balance.items():
        total += v 
    ret = dict()
    for k, v in balance.items():
        ret[k] = float(v) / float(total)
    return ret

def amounts(balance):
    return [ v['amount'] for k, v in balance.items() ]

def prices(balance):
    return [ v['price'] for k, v in balance.items() ]

def ratios(balance):
    return [ float(v['ratio']) for k, v in balance.items() ]

def rebalance(balance):
    assets = np.multiply(amounts(balance), prices(balance))
    normAssets = assets / np.abs(assets).sum()
    normRatios = ratios(balance) / np.abs(ratios(balance)).sum()
    sellRatios = list(map(lambda a, r: (a - r)/a if a > r else 0, normAssets, normRatios))
    buyRatios  = list(map(lambda a, r: (r - a)/a if r > a else 0, normAssets, normRatios))
    keys = [ k for k, v in balance.items()]
    sellAmounts = dict(zip(keys, 
        list(map(lambda a, r: math.floor(a * r), amounts(balance), sellRatios))
        ))
    buyAmounts  = dict(zip(keys, 
        list(map(lambda a, r: math.floor(a * r), amounts(balance), buyRatios))
        ))
    change = 0
    balanceExceptCash = dict(filter(lambda elem: elem[0] != 'cash', balance.items()))
    for k, v in balanceExceptCash.items():
        v['amount'] -= sellAmounts[k]
        change += (v['price'] * sellAmounts[k])
    change += balance['cash']['amount']
    for k, v in balanceExceptCash.items():
        ableAmount = math.floor(change / v['price'])
        amount = buyAmounts[k] if buyAmounts[k] <= ableAmount else ableAmount
        v['amount'] += amount
        change -= v['price'] * amount
    balance['cash']['amount'] = change
    return balance
