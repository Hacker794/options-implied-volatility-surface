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

# Testing the function with example values

S = 100  # Current stock price
K = 100  # Strike price
T = 1    # Time to expiration in years
r = 0.05  # Risk-free interest rate
sigma = 0.2  # Volatility of the underlying stock

call_price = black_scholes_call(S, K, T, r, sigma)
print(f"The Black-Scholes call option price is: {call_price:.2f}")

# Puts price function

def black_scholes_put(S, K, T, r, sigma):
    d_1 = d1(S, K, T, r, sigma)
    d_2 = d2(S, K, T, r, sigma)

    return (
        K * math.exp(-r * T) * norm.cdf(-d_2) - S * norm.cdf(-d_1)
    )

# Testing the put option price function with example values

S = 100  # Current stock price
K = 100  # Strike price
T = 1    # Time to expiration in years
r = 0.05  # Risk-free interest rate
sigma = 0.2  # Volatility of the underlying stock

put_price = black_scholes_put(S, K, T, r, sigma)
print(f"The Black-Scholes put option price is: {put_price:.2f}")