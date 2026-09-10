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

def clean_option_data(df):

    """""
    df = df.copy()

    # Remove rows with missing bid or ask 
    df = df.dropna(subset=["bid", "ask", "strike"])

    # Remove zero or negative quotes 
    df = df[(df["bid"] > 0) & (df["ask"] > 0)]

    # Calculate mid price
    df["mid_price"] = (df["bid"] + df["ask"]) / 2

    # Calculate bid-ask spread
    df["spread"] = df["ask"] - df["bid"]

    # Calculate spread as a fraction of the mid price
    df["relative_spread"] = df["spread"] / df["mid_price"]

    # Remove extremely wide spreads (might need to tighten 50% threshold)
    df = df[df["relative_spread"] <= 0.5]

    return df

    """

    df = df.copy()

    print("Starting rows:", len(df))

    df = df.dropna(subset=["bid", "ask", "strike"])
    print("After removing missing values:", len(df))

    df = df[(df["bid"] > 0) & (df["ask"] > 0)]
    print("After removing zero quotes:", len(df))

    df["mid_price"] = (df["bid"] + df["ask"]) / 2
    df["spread"] = df["ask"] - df["bid"]
    df["relative_spread"] = df["spread"] / df["mid_price"]

    df = df[df["relative_spread"] <= 0.50]
    print("After spread filter:", len(df))

    return df


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

    clean_calls = clean_option_data(calls)
    clean_puts = clean_option_data(puts)

    print("\nCleaned Calls:")
    print(clean_calls.head())

    print("\nCleaned Puts:")
    print(clean_puts.head())
