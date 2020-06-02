top = 0
bottom = 10000000
def envelope(value):
    if value > top:
        top = value
    if value < bottom:
        bottom = value
    return float(top - bottom / value)
