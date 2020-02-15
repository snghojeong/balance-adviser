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
    subtracted = np.subtract(normAssets, normRatios)
    print(subtracted)
