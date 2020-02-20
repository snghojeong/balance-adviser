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

def rebalance(balance, prices):
    assets = np.multiply(amounts(balance), prices)
    ratios = [v['ratio'] for k, v in balance.items()]
    normAssets = assets / np.abs(assets).sum()
    normRatios = ratios / np.abs(ratios).sum()
    sellRatios = list(map(lambda a, r: (a - r)/a if a > r else 0, normAssets, normRatios))
    buyRatios  = list(map(lambda a, r: (r - a)/a if r > a else 0, normAssets, normRatios))
    sellAmounts = list(map(lambda a, r: math.floor(a * r), amounts(balance), sellRatios))
    buyAmounts  = list(map(lambda a, r: math.floor(a * r), amounts(balance), buyRatios))
    i = 0
    for k, v in balance.items():
        i = i + 1
        v['amount'] -= sellAmounts[i]
    i = 0
    for k, v in balance.items():
        i = i + 1
        v['amount'] += buyAmounts[i]
