#!/usr/bin/env python3
"""
Generate New Plot 17: Flag Accuracy Error Rate by Order.

Horizontal bar chart showing the flag accuracy error rate for each `order`
value, averaged across all AI models. Higher error rates appear at the top.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

from style import setup_style

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load tests dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def prepare_data(df):
    """Filter for flag_accuracy, human baseline dataset, AI models only."""
    df_flag = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
        & (df["test_category"] == "flag_accuracy")
    ].copy()
    print(f"Flag accuracy AI rows on baseline dataset: {len(df_flag):,}")

    # Error rate per order = 1 - mean(pass), expressed as percentage
    order_error = (
        df_flag.groupby("order")["pass"]
        .mean()
        .reset_index()
    )
    order_error["error_rate"] = (1 - order_error["pass"]) * 100

    # Sort by error rate descending (highest at top)
    order_error = order_error.sort_values("error_rate", ascending=True).reset_index(drop=True)

    print(f"Unique orders: {len(order_error)}")
    return order_error


def create_figure(order_error):
    """Create horizontal bar chart of flag error rates."""
    setup_style()

    n = len(order_error)
    fig, ax = plt.subplots(figsize=(10, max(6, n * 0.45)))

    # Red gradient: light red for low error, dark red for high error
    cmap = LinearSegmentedColormap.from_list("reds", ["#f5b7b1", "#c0392b", "#7b241c"])
    vmin = 0
    vmax = max(order_error["error_rate"].max() + 2, 10)
    norm = Normalize(vmin=vmin, vmax=vmax)

    colors = [cmap(norm(v)) for v in order_error["error_rate"]]

    bars = ax.barh(
        range(n),
        order_error["error_rate"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        height=0.75,
    )

    # Add value labels at end of bars
    for i, (bar, val) in enumerate(zip(bars, order_error["error_rate"])):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%",
            ha="left",
            va="center",
            fontsize=9,
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels(order_error["order"].values, fontsize=9)
    ax.set_xlabel("Flag Error Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Flag Accuracy Error Rate by Order\n(Average across AI Models)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Add colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.02)
    cbar.set_label("Error Rate (%)", fontsize=10)

    ax.set_xlim(0, order_error["error_rate"].max() + 5)
    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def write_outputs(order_error):
    """Write data and caption files."""
    data_path = output_dir / "new_17_flag_errors_by_order_data.txt"
    with open(data_path, "w") as f:
        f.write("Flag Accuracy Error Rate by Order (averaged across AI models)\n")
        f.write("=" * 60 + "\n\n")
        # Print in descending error rate order
        for _, row in order_error.iloc[::-1].iterrows():
            f.write(f"{row['order']:55s}  {row['error_rate']:.1f}%\n")
        f.write(f"\nOverall mean error rate: {order_error['error_rate'].mean():.1f}%\n")
        f.write(
            f"Min: {order_error['error_rate'].min():.1f}%  "
            f"Max: {order_error['error_rate'].max():.1f}%\n"
        )
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_17_flag_errors_by_order.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Flag accuracy error rate for each order (gene/protein product), averaged "
            "across all AI models on the 40-profile human baseline subset. Error rate is "
            "defined as 1 minus the mean pass rate for flag_accuracy tests. Bars are "
            "colored with a red gradient; darker red indicates higher error rates."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 17: Flag Errors by Order")
    print("=" * 60)

    df = load_data()
    order_error = prepare_data(df)
    fig = create_figure(order_error)

    fig_path = output_dir / "new_17_flag_errors_by_order.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(order_error)
    print("Done.")


if __name__ == "__main__":
    main()
