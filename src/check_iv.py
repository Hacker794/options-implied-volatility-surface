from pathlib import Path

import pandas as pd


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    data = pd.read_csv(
        project_root / "data" / "clean" / "SPY_combined_iv.csv"
    )

    calls = data[data["option_type"] == "call"]
    puts = data[data["option_type"] == "put"]

    # Match calls and puts with identical strikes and expirations.
    matched = calls.merge(
        puts,
        on=["expiry", "strike"],
        suffixes=("_call", "_put"),
        validate="one_to_one"
    )

    matched["iv_gap_pp"] = (
        matched["calculated_iv_put"]
        - matched["calculated_iv_call"]
    ) * 100

    near_money = matched[
        matched["moneyness_call"].between(0.99, 1.01)
    ].copy()

    if near_money.empty:
        raise ValueError("No matched near-the-money options found.")

    print("\nMatched options:")
    print(
        near_money[
            [
                "expiry",
                "strike",
                "calculated_iv_call",
                "calculated_iv_put",
                "iv_gap_pp",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nCall–put IV comparison:")
    print(
        near_money.groupby("expiry")["iv_gap_pp"]
        .agg(["count", "median", "min", "max"])
        .round(3)
    )