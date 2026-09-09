import yfinance as yf
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option("display.width", None)

# Available option expiration dates for a given ticker symbol

def get_expiries(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    return ticker.options

if __name__ == "__main__":
    expiries = get_expiries("SPY")

    print(expiries)

# Pull option chain data for a given ticker symbol and expiration date
# Important columns in the option chain data include: strike, bid, ask, lastPrice, volume, openInterest, impliedVolatility (We can compare our IV with reported IV - Validation Step), inTheMoney

def get_option_chain(ticker_symbol, expiry):
    ticker = yf.Ticker(ticker_symbol)
    chain = ticker.option_chain(expiry)

    return chain.calls, chain.puts

# Pull the current SPY price so IV solver has S

def get_current_price(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    return ticker.history(period="1d")["Close"].iloc[0]

if __name__ == "__main__":
    ticker_symbol = "SPY"
    expiries = get_expiries(ticker_symbol)
    first_expiry = expiries[0]

    calls, puts = get_option_chain(ticker_symbol, first_expiry)

    print("Expiration Date:", first_expiry)

    print("\nCalls:")
    print(calls.head())

    print("\nPuts:")
    print(puts.head())

    current_price = get_current_price(ticker_symbol)
    print("Current Price:", current_price)

    calls.to_csv(f"data/raw/{ticker_symbol}_calls_{first_expiry}.csv", index=False)
    puts.to_csv(f"data/raw/{ticker_symbol}_puts_{first_expiry}.csv", index=False)


