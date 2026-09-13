# Note: python3 -m src.data in terminal to run code

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import date, datetime 
from src.implied_volatility import (implied_volatility_call, implied_volatility_put)

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

def calculate_row_iv(row, option_type, S, T, r):
    try:
        if option_type == "call":
            return implied_volatility_call(
                S=S,
                K=float(row["strike"]),
                T=T,
                r=r,
                market_price=float(row["market_price"])
            )
        elif option_type == "put":
            return implied_volatility_put(
                S=S,
                K=float(row["strike"]),
                T=T,
                r=r,
                market_price=float(row["market_price"])
            )
        else:
            raise ValueError("Invalid option type. Must be 'call' or 'put'.")

    except ValueError:
        return float("nan")  # Return NaN if IV calculation fails


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

    nearest_call_index = clean_calls["strike"].sub(current_price).abs().idxmin()
    nearest_call = clean_calls.loc[nearest_call_index] 

    nearest_put_index = clean_puts["strike"].sub(current_price).abs().idxmin()
    nearest_put = clean_puts.loc[nearest_put_index]

    # Temporary annual risk-free interest rate assumption: 4%
    risk_free_rate = 0.04 

    clean_calls["calculated_iv"] = clean_calls.apply(
        lambda row: calculate_row_iv(row, "call", current_price, time_to_expiry, risk_free_rate), axis=1
    )

    clean_puts["calculated_iv"] = clean_puts.apply(
        lambda row: calculate_row_iv(row, "put", current_price, time_to_expiry, risk_free_rate), axis=1
    )

    call_iv_failures = clean_calls["calculated_iv"].isna().sum()
    put_iv_failures = clean_puts["calculated_iv"].isna().sum()

    print("Call IV failures:", call_iv_failures)
    print("Put IV failures:", put_iv_failures)

    # Remove failed calculations and extreme IV results.
    clean_calls = clean_calls.dropna(subset=["calculated_iv"]).copy()
    clean_puts = clean_puts.dropna(subset=["calculated_iv"]).copy()

    clean_calls = clean_calls[
        clean_calls["calculated_iv"].between(0.01, 3.0)
    ].copy()

    clean_puts = clean_puts[
        clean_puts["calculated_iv"].between(0.01, 3.0)
    ].copy()

    clean_calls.to_csv(
        clean_data_folder / f"{ticker_symbol}_calls_{first_expiry}.csv",
        index=False
    )

    clean_puts.to_csv(
        clean_data_folder / f"{ticker_symbol}_puts_{first_expiry}.csv",
        index=False
    )

    calculated_call_iv = implied_volatility_call(
        S=current_price,
        K=float(nearest_call["strike"]),
        T=time_to_expiry,
        r=risk_free_rate,
        market_price=float(nearest_call["market_price"])
    )

    calculated_put_iv = implied_volatility_put(
        S=current_price,
        K=float(nearest_put["strike"]),
        T=time_to_expiry,
        r=risk_free_rate,
        market_price=float(nearest_put["market_price"]) 
    )

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

    print("\nRaw puts:", len(puts))
    print("Clean puts:", len(clean_puts))
    print(clean_puts["price_source"].value_counts())

    print(f"\n\nCalculated call IV: {calculated_call_iv:.2%}")
    print(f"Yahoo call IV: {nearest_call['impliedVolatility']:.2%}")

    print(f"\nCalculated put IV: {calculated_put_iv:.2%}")
    print(f"Yahoo put IV: {nearest_put['impliedVolatility']:.2%}")

    print("\nCalculated call IVs:")
    print(
        clean_calls[
            ["strike", "market_price", "calculated_iv"]
        ].head(10)
    )

    print("\nCalculated put IVs:")
    print(
        clean_puts[
            ["strike", "market_price", "calculated_iv"]
        ].head(10)
    )

    print(
        "Successful call IVs:",
    clean_calls["calculated_iv"].notna().sum()
    )

    print(
        "Successful put IVs:",
        clean_puts["calculated_iv"].notna().sum()
    )
