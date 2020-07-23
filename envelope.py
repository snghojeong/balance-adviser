def envelopeHiBounds(valueList, wnd):
    return envelopeBounds(valueList, wnd, 0.1)

def envelopeLoBounds(valueList, wnd):
    return envelopeBounds(valueList, wnd, 0.05)

def envelopeBounds(valueList, wnd, ratio):
    return valueList.ewm(50).mean() * (1 + ratio)
