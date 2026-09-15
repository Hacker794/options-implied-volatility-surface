from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    data = pd.read_csv(
        project_root / "data" / "clean" / "SPY_combined_iv.csv"
    )

    columns = ["moneyness", "time_to_expiry", "calculated_iv"]

    data = data[
        np.isfinite(data[columns]).all(axis=1)
        & data["moneyness"].between(0.90, 1.10)
        & (data["time_to_expiry"] > 0)
        & (data["calculated_iv"] > 0)
    ].copy()

    if data.empty:
        raise ValueError("No usable data to plot.")

    fig = plt.figure(figsize=(14, 6))

    for panel, option_type in enumerate(["call", "put"], start=1):
        options = data[data["option_type"] == option_type]

        # Ensure there is one IV value per grid location.
        points = options.groupby(
            ["moneyness", "time_to_expiry"],
            as_index=False
        )["calculated_iv"].median()

        if (
            points["time_to_expiry"].nunique() < 2
            or points["moneyness"].nunique() < 2
        ):
            raise ValueError(
                f"Not enough strikes or expirations for {option_type}s."
            )

        x = points["moneyness"].to_numpy()
        y = points["time_to_expiry"].to_numpy() * 365
        z = points["calculated_iv"].to_numpy() * 100

        coordinates = np.column_stack((x, y))

        if np.linalg.matrix_rank(
            coordinates - coordinates.mean(axis=0)
        ) < 2:
            raise ValueError(
                f"{option_type} points cannot form a 2D surface."
            )

        grid_x, grid_y = np.meshgrid(
            np.linspace(x.min(), x.max(), 60),
            np.linspace(y.min(), y.max(), 60)
        )

        grid_z = griddata(
            coordinates,
            z,
            (grid_x, grid_y),
            method="linear",
            rescale=True
        )

        ax = fig.add_subplot(1, 2, panel, projection="3d")

        ax.plot_surface(
            grid_x,
            grid_y,
            np.ma.masked_invalid(grid_z),
            cmap="viridis",
            alpha=0.75,
            linewidth=0
        )

        # Overlay the observations used to build the surface.
        ax.scatter(x, y, z, color="black", s=5, alpha=0.4)

        ax.set_title(f"SPY {option_type}s — linear interpolation")
        ax.set_xlabel("Moneyness (K/S)")
        ax.set_ylabel("Days to expiry")
        ax.set_zlabel("Implied volatility (%)")

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

    fig.tight_layout()

    figures_folder = project_root / "figures"
    figures_folder.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        figures_folder / "SPY_iv_surfaces.png",
        dpi=150
    )

    plt.show()