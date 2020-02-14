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
    normAssets = assets / np.abs(assets).max(axis=0) # Normalized
    normRatios = ratios / np.abs(ratios).max(axis=0) # Normalized
    subtracted = np.subtract(normAssets, normRatios)
