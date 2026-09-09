# Note: Use python3 -m src.implied_volatility in terminal to run code

import math

from src.black_scholes import black_scholes_call, black_scholes_put

def implied_volatility_call(S, K, T, r, market_price, tolerance=1e-6, max_iterations=100):
    low = 0.01
    high = 5.0

    lower_bound = max(S - K * math.exp(-r * T), 0.0)
    upper_bound = S

    if market_price < lower_bound or market_price > upper_bound:
        raise ValueError("Market price is outside of valid call price bounds.")

    for _ in range(max_iterations):

        sigma = (low + high) / 2

        model_price = black_scholes_call(S, K, T, r, sigma)

        difference = model_price - market_price

        if abs(difference) < tolerance:
            return sigma

        if model_price > market_price:
            high = sigma
        else:
            low = sigma

    raise ValueError("Implied volatility solver did not converge.")

def implied_volatility_put(S, K, T, r, market_price, tolerance=1e-6, max_iterations=100):
    low = 0.0001
    high = 5.0

    lower_bound = max(K * math.exp(-r * T) - S, 0.0)
    upper_bound = K * math.exp(-r * T)

    if market_price < lower_bound or market_price > upper_bound:
        raise ValueError("Market price is outside of valid put price bounds.")

    for _ in range(max_iterations):

        sigma = (low + high) / 2

        model_price = black_scholes_put(S, K, T, r, sigma)

        difference = model_price - market_price

        if abs(difference) < tolerance:
            return sigma

        if model_price > market_price:
            high = sigma
        else:
            low = sigma

    raise ValueError("Implied volatility solver did not converge.")

# test the implied volatility call function with an example

if __name__ == "__main__":

    iv_call = implied_volatility_call(S=100, K=100, T=1, r=0.05, market_price=10.4506)
    print(f"Implied Volatility Call: {iv_call:.4f}")

    iv_put = implied_volatility_put(S=100, K=100, T=1, r=0.05, market_price=5.5735)
    print(f"Implied Volatility Put: {iv_put:.4f}")

