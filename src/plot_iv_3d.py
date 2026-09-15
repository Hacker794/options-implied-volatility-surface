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
        raise ValueError("No usable data to plot.")

    expiries = sorted(data["expiry"].unique())

    fig = plt.figure(figsize=(14, 6))

    for panel, option_type in enumerate(["call", "put"], start=1):
        ax = fig.add_subplot(1, 2, panel, projection="3d")

        for index, expiry in enumerate(expiries):
            options = data[
                (data["option_type"] == option_type)
                & (data["expiry"] == expiry)
            ]

            ax.scatter(
                options["moneyness"],
                options["time_to_expiry"] * 365,
                options["calculated_iv"] * 100,
                color=f"C{index}",
                label=expiry,
                s=12,
                alpha=0.7
            )

        ax.set_xlabel("Moneyness (K/S)")
        ax.set_ylabel("Days to expiry")
        ax.set_zlabel("Implied volatility (%)")
        ax.set_title(f"SPY {option_type}s")

        # Use matching scales so the panels are comparable.
        ax.set_xlim(0.90, 1.10)
        ax.set_ylim(
            data["time_to_expiry"].min() * 365,
            data["time_to_expiry"].max() * 365
        )
        ax.set_zlim(
            data["calculated_iv"].min() * 100,
            data["calculated_iv"].max() * 100
        )

        ax.view_init(elev=25, azim=-60)
        ax.legend(fontsize=7)

    fig.tight_layout()

    figures_folder = project_root / "figures"
    figures_folder.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        figures_folder / "SPY_iv_points_3d.png",
        dpi=150
    )

    plt.show()