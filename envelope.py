def envelopeHiBounds(valueList, wnd, ratio):
    return valueList.ewm(50).mean() * (1 + ratio)

def envelopeLoBounds(valueList, wnd, ratio):
    return valueList.ewm(50).mean() * (1 - ratio)
