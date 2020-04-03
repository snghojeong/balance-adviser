import math
import numpy as np

def amounts(balance):
    return [ v['amount'] for k, v in balance.items() ]

def getValueEachAsset(balance):
    valueList = []
    for k, v in balance.items():
        valueList.append(v['price'] * v['amount'])
    return valueList

def getValue(balance):
    return sum(getValueEachAsset(balance))

def rebalance(balance):
    prices = [v['price'] for k, v in balance.items()]
    assets = np.multiply(amounts(balance), prices)
    ratios = [v['ratio'] for k, v in balance.items()]
    normAssets = assets / np.abs(assets).sum()
    normRatios = ratios / np.abs(ratios).sum()
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
    if change > 2000:
        print(change)
    balance['cash']['amount'] = change
