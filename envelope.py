def envelopeHiBounds(valueList, wnd):
    return envelopeBounds(valueList, wnd, 0.025)

def envelopeLoBounds(valueList, wnd):
    return envelopeBounds(valueList, wnd, 0.025)

def envelopeBounds(valueList, wnd, ratio):
    return valueList.ewm(wnd).mean() * (1 + ratio)
