import math

from src.black_scholes import black_scholes_call, black_scholes_put

S=100  # Current stock price
K=100  # Strike price
T=1    # Time to expiration in years
r=0.05 # Risk-free interest rate
sigma=0.2 # Volatility of the underlying stock

call_price = black_scholes_call(S, K, T, r, sigma)
put_price = black_scholes_put(S, K, T, r, sigma)

print(f"Call Option Price: {call_price:.4f}")
print(f"Put Option Price: {put_price:.4f}")

# Test 1: prices should be positive
assert call_price > 0
assert put_price > 0

# Test 2: higher volatility should increase both option prices
higher_vol_call = black_scholes_call(S, K, T, r, 0.4)
higher_vol_put = black_scholes_put(S, K, T, r, 0.4)

assert higher_vol_call > call_price
assert higher_vol_put > put_price

# Test 3: put-call parity 
left_side = call_price - put_price
right_side = S - K * math.exp(-r * T)

assert abs(left_side - right_side) < 1e-6

print("All tests passed successfully.")