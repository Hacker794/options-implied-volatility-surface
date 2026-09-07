import math
from scipy.stats import norm

# Calculating d1 and d2 for the Black-Schoeles formula

def d1(S, K, T, r, sigma):
    return (
        math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T)
    )

def d2(S, K, T, r, sigma):
    return d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

# Call-price function 

def black_scholes_call(S, K, T, r, sigma):
    d_1 = d1(S, K, T, r, sigma)
    d_2 = d2(S, K, T, r, sigma)

    return (
        S * norm.cdf(d_1) - K * math.exp(-r * T) * norm.cdf(d_2)
    )
