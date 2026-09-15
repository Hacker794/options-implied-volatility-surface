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


def process_expiry(ticker_symbol, expiry, S, r):
    T = calculate_time_to_expiry(expiry)
    calls, puts = get_option_chain(ticker_symbol, expiry)

    # Preserve the downloaded data before cleaning.

    raw_folder = Path(__file__).resolve().parent.parent / "data" / "raw"
    raw_folder.mkdir(parents=True, exist_ok=True)

    calls.to_csv(raw_folder / f"{ticker_symbol}_calls_{expiry}.csv", index=False)
    puts.to_csv(raw_folder / f"{ticker_symbol}_puts_{expiry}.csv", index=False)

    results = []

    for option_type, raw_data in [("call", calls), ("put", puts)]:
        cleaned = clean_option_data(raw_data, allow_last_price=False)

        if cleaned.empty:
            print(f"{expiry} {option_type}: no usable quotes")
            continue

        cleaned["calculated_iv"] = cleaned.apply(
            lambda row: calculate_row_iv(row, option_type, S, T, r), axis=1)

        failures = cleaned["calculated_iv"].isna().sum()
        print(f"{expiry} {option_type}: {failures} IV failures")

        cleaned = cleaned[cleaned["calculated_iv"].between(0.01, 3.0)].copy()

        cleaned["expiry"] = expiry
        cleaned["option_type"] = option_type
        cleaned["time_to_expiry"] = T
        cleaned["underlying_price"] = S
        cleaned["moneyness"] = cleaned["strike"] / S

        results.append(cleaned)

    if not results:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)
    

if __name__ == "__main__":
    ticker_symbol = "SPY"
    risk_free_rate = 0.04  # Temporary assumption
    today = date.today()

    expiries = get_expiries(ticker_symbol)

    selected_expiries = [
        expiry
        for expiry in expiries
        if 7 <= (
            datetime.strptime(expiry, "%Y-%m-%d").date() - today
        ).days <= 90
    ]

    if not selected_expiries:
        raise ValueError("No expirations available 7–90 days away.")

    target_days = [7, 14, 30, 60, 90]
    available_expiries = selected_expiries.copy()
    selected_expiries = []

    for target in target_days:
        closest_expiry = min(
            available_expiries,
            key=lambda expiry: abs(
                (
                    datetime.strptime(expiry, "%Y-%m-%d").date()
                    - today
               ).days - target
            )
        )

        if closest_expiry not in selected_expiries:
            selected_expiries.append(closest_expiry)

    selected_expiries.sort()

    print("\nSelected expiration dates:")

    for expiry in selected_expiries:
        days_remaining = (
            datetime.strptime(expiry, "%Y-%m-%d").date() - today
        ).days

        print(f"{expiry}: {days_remaining} days")

    current_price = get_current_price(ticker_symbol)

    print("Underlying price:", current_price)
    print("Selected expirations:", selected_expiries)

    all_results = []

    for expiry in selected_expiries:
        print(f"\nProcessing {expiry}")

        expiry_data = process_expiry(
            ticker_symbol,
            expiry,
            current_price,
            risk_free_rate
        )

        if expiry_data.empty:
            print("No usable IV results for this expiry.")
            continue

        all_results.append(expiry_data)

    if not all_results:
        raise ValueError("No usable IV results across selected expirations.")

    combined_data = pd.concat(all_results, ignore_index=True)

    combined_data = combined_data.sort_values(["expiry", "option_type", "moneyness"]).reset_index(drop=True)

    print("\nCombined IV data:")
    print(combined_data[["expiry", "option_type", "strike", "underlying_price", "moneyness", "time_to_expiry", "calculated_iv"]].head(10))

    print("\nRows by expiry and option type:")
    print(combined_data.groupby(["expiry", "option_type"]).size())

    clean_folder = (
        Path(__file__).resolve().parent.parent / "data" / "clean"
    )
    clean_folder.mkdir(parents=True, exist_ok=True)

    output_path = clean_folder / f"{ticker_symbol}_combined_iv.csv"
    combined_data.to_csv(output_path, index=False)

    print("\nSaved:", output_path)
