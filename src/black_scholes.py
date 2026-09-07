import math
from scipy.stats import norm

#Calculating d1 for the Black-Schoeles formula

def d1(S, K, T, r, sigma):
    return (
        math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T)
    )

def d2(S, K, T, r, sigma):
    return d1(S, K, T, r, sigma) - sigma * math.sqrt(T)
