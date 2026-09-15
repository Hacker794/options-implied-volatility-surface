from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    data = pd.read_csv(project_root / "data" / "clean" / "SPY_combined_iv.csv")

    # Start with the earliest saved expiration.

    expiry = sorted(data["expiry"].unique())[0]

    smile = data[(data["expiry"] == expiry) & data["moneyness"].between(0.90, 1.10)].copy()

    if smile.empty:
        raise ValueError(f"No data available for expiry {expiry}.")

    fig, ax = plt.subplots(figsize=(9, 5))

    for option_type in ["call", "put"]:
        option_data = smile[smile["option_type"] == option_type]

        ax.scatter(
            option_data["moneyness"],
            option_data["calculated_iv"] * 100,
            label=option_type.capitalize(),
            s=25
        )
    ax.axvline(
        1.0,
        color="gray",
        linestyle="--",
        label="At-the-money",
    )

    ax.set_xlabel("Moneyness (Strike / Underlying Price)")
    ax.set_ylabel("Implied Volatility (%)")
    ax.set_title(f"SPY implied volatility - {expiry}")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()

    figures_folder = project_root / "figures"
    figures_folder.mkdir(parents=True, exist_ok=True)

    fig.savefig(figures_folder / f"SPY_smile_{expiry}.png")

    plt.show()