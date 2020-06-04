envelopeRatio = 0.1

def envelopeHiBound(value):
    return value * (1.0 + envelopeRatio)

def envelopeLoBound(value):
    return value * (1.0 - envelopeRatio)
