# Note: Use python3 -m src.implied_volatility in terminal to run code

from src.black_scholes import black_scholes_call, black_scholes_put

def implied_volatility_call(S, K, T, r, market_price, tolerance=1e-6, max_iterations=100):
    low = 0.01
    high = 5.0

    for _ in range(max_iterations):

        # initial guess for volatility

        sigma = (low + high) / 2

        model_price = black_scholes_call(S, K, T, r, sigma)

        difference = model_price - market_price

        if abs(difference) < tolerance:
            return sigma

        if model_price > market_price:
            high = sigma
        else:
            low = sigma

    return sigma 

def implied_volatility_put(S, K, T, r, market_price, tolerance=1e-6, max_iterations=100):
    low = 0.0001
    high = 5.0

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

    return sigma 

# test the implied volatility call function with an example

if __name__ == "__main__":

    iv_call = implied_volatility_call(S=100, K=100, T=1, r=0.05, market_price=10.4506)
    print(f"Implied Volatility Call: {iv_call:.4f}")

    iv_put = implied_volatility_put(S=100, K=100, T=1, r=0.05, market_price=5.5735)
    print(f"Implied Volatility Put: {iv_put:.4f}")

