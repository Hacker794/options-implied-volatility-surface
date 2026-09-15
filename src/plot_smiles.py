from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    data = pd.read_csv(
        project_root / "data" / "clean" / "SPY_combined_iv.csv"
    )

    data = data[
        data["moneyness"].between(0.90, 1.10)
        & data["calculated_iv"].notna()
    ].copy()

    if data.empty:
        raise ValueError("No usable data in this moneyness range.")

    expiries = sorted(data["expiry"].unique())

    fig, axes = plt.subplots(
        1, 2,
        figsize=(13, 5),
        sharex=True,
        sharey=True
    )

    for ax, option_type in zip(axes, ["call", "put"]):
        for index, expiry in enumerate(expiries):
            options = data[
                (data["option_type"] == option_type)
                & (data["expiry"] == expiry)
            ]

            ax.scatter(
                options["moneyness"],
                options["calculated_iv"] * 100,
                color=f"C{index}",
                label=expiry,
                s=18,
                alpha=0.7
            )

        ax.axvline(1.0, color="grey", linestyle="--")
        ax.set_title(f"SPY {option_type}s")
        ax.set_xlabel("Moneyness (strike / underlying price)")
        ax.grid(alpha=0.3)
        ax.legend(title="Expiration", fontsize=8)

    axes[0].set_ylabel("Implied volatility (%)")
    fig.tight_layout()

    figures_folder = project_root / "figures"
    figures_folder.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        figures_folder / "SPY_smiles_all_expiries.png",
        dpi=150
    )

    plt.show()