def steep_decline(x):
    x = min(1, max(0, x))
    res = (0.11)/(x+0.1)-0.1
    return min(1, max(0, res))