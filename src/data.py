# Note: python3 -m src.data in terminal to run code

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import date, datetime 
from src.implied_volatility import implied_volatility_call, implied_volatility_put

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

def clean_option_data(df, allow_last_price=False):
    """Prefer usable midpoints; optionally use last trades for missing quotes."""
    df = df.copy()

    # Keep finite, positive strikes.
    df = df[
        df["strike"].notna()
        & (df["strike"] > 0)
        & (df["strike"] < float("inf"))
    ].copy()

    valid_quotes = (
        (df["bid"] > 0)
        & (df["ask"] >= df["bid"])
        & (df["ask"] < float("inf"))
    )

    df["mid_price"] = (
        (df["bid"] + df["ask"]) / 2
    ).where(valid_quotes)
    df["relative_spread"] = (
        (df["ask"] - df["bid"]) / df["mid_price"]
    )

    use_mid = valid_quotes & (df["relative_spread"] <= 0.50)
    df["market_price"] = df["mid_price"].where(use_mid)
    df["price_source"] = pd.Series(index=df.index, dtype="object")
    df.loc[use_mid, "price_source"] = "mid"

    if allow_last_price:
        valid_last = (
            (df["lastPrice"] > 0)
            & (df["lastPrice"] < float("inf"))
        )
        missing_quotes = (
            df["bid"].isna() | df["ask"].isna()
            | (df["bid"] == 0) | (df["ask"] == 0)
        )
        # Missing quotes may use a last trade; malformed quotes may not.
        malformed_quotes = (
            (df["bid"] < 0) | (df["ask"] < 0)
            | (df["bid"] == float("inf"))
            | (df["ask"] == float("inf"))
        )
        use_last = missing_quotes & ~malformed_quotes & valid_last
        df.loc[use_last, "market_price"] = df.loc[use_last, "lastPrice"]
        df.loc[use_last, "price_source"] = "lastPrice"

    return df.dropna(subset=["market_price"])

# Pull time to expiration in years so implied volatility solver has T

def calculate_time_to_expiry(expiry):
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()

    days_to_expiry = (expiry_date - date.today()).days

    if days_to_expiry <= 0:
        raise ValueError("Expiration date must be in the future.")

    return days_to_expiry / 365.0


if __name__ == "__main__":
    ticker_symbol = "SPY"
    expiries = get_expiries(ticker_symbol)

    # We want first expiry to be at least 7 days away. If it was 0 then Black Scholes could not be used to price the option as it contains sqrt(T).

    first_expiry = next(expiry for expiry in expiries if ( datetime.strptime(expiry, "%Y-%m-%d").date() - date.today()).days >= 7)
    time_to_expiry = calculate_time_to_expiry(first_expiry)

    calls, puts = get_option_chain(ticker_symbol, first_expiry)

    print("Expiration Date:", first_expiry)
    print("Time to Expiry in years:", time_to_expiry)

    print("\nCalls:")
    print(calls.head())

    print("\nPuts:")
    print(puts.head())

    current_price = get_current_price(ticker_symbol)
    print("Current Price:", current_price)

    calls.to_csv(f"data/raw/{ticker_symbol}_calls_{first_expiry}.csv", index=False)
    puts.to_csv(f"data/raw/{ticker_symbol}_puts_{first_expiry}.csv", index=False)

    # Set False to keep only usable bid/ask midpoints.
    allow_last_price = False
    clean_calls = clean_option_data(calls, allow_last_price=allow_last_price)
    clean_puts = clean_option_data(puts, allow_last_price=allow_last_price)

    project_root = Path(__file__).resolve().parent.parent
    clean_data_folder = project_root / "data" / "clean"

    clean_data_folder.mkdir(parents=True, exist_ok=True)

    clean_calls.to_csv(
        clean_data_folder / f"{ticker_symbol}_calls_{first_expiry}.csv",
        index=False
    )

    clean_puts.to_csv(
        clean_data_folder / f"{ticker_symbol}_puts_{first_expiry}.csv",
        index=False
    )

    nearest_call_index = clean_calls["strike"].sub(current_price).abs().idxmin()
    nearest_call = clean_calls.loc[nearest_call_index] 

    nearest_put_index = clean_puts["strike"].sub(current_price).abs().idxmin()
    nearest_put = clean_puts.loc[nearest_put_index]

    print("\nCleaned Calls:")
    print(clean_calls.head())

    print("\nNearest Call to Current Price:")
    print(nearest_call[["strike", "bid", "ask", "market_price", "price_source"]])

    print("\nCleaned Puts:")
    print(clean_puts.head())

    print("\nNearest Put to Current Price:")
    print(nearest_put[["strike", "bid", "ask", "market_price", "price_source"]])

    print("\n\nRaw calls:", len(calls))
    print("Clean calls:", len(clean_calls))
    print(clean_calls["price_source"].value_counts())

    print("Raw puts:", len(puts))
    print("Clean puts:", len(clean_puts))
    print(clean_puts["price_source"].value_counts())
