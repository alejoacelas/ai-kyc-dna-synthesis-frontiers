#!/usr/bin/env python3
"""
Generate New Plot 10: Flag Pass Rate vs Overall (Non-Flag) Pass Rate.

Scatter plot where each point is a customer, colored by customer_type.
X-axis: non-flag pass rate, Y-axis: flag pass rate, averaged across AI models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import setup_style, COLORS

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load and filter tests.csv."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    df = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()
    print(f"AI rows on baseline: {len(df):,}")

    return df


def compute_rates(df):
    """Compute per-customer flag and non-flag pass rates (averaged across AI models)."""
    # Flag pass rate per customer
    flag_df = df[df["test_category"] == "flag_accuracy"]
    flag_rates = flag_df.groupby("customer_name")["pass"].mean() * 100

    # Non-flag pass rate per customer
    nonflag_df = df[df["test_category"] != "flag_accuracy"]
    nonflag_rates = nonflag_df.groupby("customer_name")["pass"].mean() * 100

    # Customer type lookup
    ct_lookup = df.drop_duplicates("customer_name").set_index("customer_name")["customer_type"]

    customers = pd.DataFrame({
        "flag_rate": flag_rates,
        "nonflag_rate": nonflag_rates,
        "customer_type": ct_lookup,
    }).dropna()

    print(f"Customers with both rates: {len(customers)}")
    print(f"Customer type distribution:\n{customers['customer_type'].value_counts()}")

    return customers


def create_figure(customers):
    """Create the scatter plot."""
    setup_style()

    fig, ax = plt.subplots(figsize=(9, 8))

    ct_order = [
        "Controlled Agent Academia",
        "Controlled Agent Industry",
        "General Life Science Customers",
        "Sanctioned Institution Customers",
    ]
    ct_short = {
        "Controlled Agent Academia": "Controlled Academia",
        "Controlled Agent Industry": "Controlled Industry",
        "General Life Science Customers": "General Life Science",
        "Sanctioned Institution Customers": "Sanctioned Institution",
    }

    for ct in ct_order:
        subset = customers[customers["customer_type"] == ct]
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["nonflag_rate"],
            subset["flag_rate"],
            color=COLORS.get(ct, "#6b7280"),
            label=ct_short.get(ct, ct),
            s=70,
            alpha=0.75,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )

    # Add diagonal reference line
    lims = [
        min(ax.get_xlim()[0], ax.get_ylim()[0]),
        max(ax.get_xlim()[1], ax.get_ylim()[1]),
    ]
    ax.plot(lims, lims, "--", color="#cccccc", linewidth=1, zorder=1, label="y = x")

    # Correlation
    r = customers["flag_rate"].corr(customers["nonflag_rate"])
    ax.text(
        0.05,
        0.95,
        f"r = {r:.2f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc", alpha=0.9),
    )

    ax.set_xlabel("Non-Flag Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Flag Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Flag vs Non-Flag Pass Rate per Customer",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def write_outputs(customers):
    """Write data and caption files."""
    r = customers["flag_rate"].corr(customers["nonflag_rate"])

    data_path = output_dir / "new_10_flag_vs_overall_passrate_data.txt"
    with open(data_path, "w") as f:
        f.write("Plot 10: Flag vs Non-Flag Pass Rate per Customer\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Pearson r = {r:.3f}\n\n")
        out = customers[["nonflag_rate", "flag_rate", "customer_type"]].copy()
        out.columns = ["Non-Flag Rate (%)", "Flag Rate (%)", "Customer Type"]
        out = out.sort_values("Non-Flag Rate (%)", ascending=False)
        f.write(out.to_string())
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_10_flag_vs_overall_passrate.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Scatter plot of flag accuracy pass rate vs non-flag pass rate per customer, "
            f"averaged across AI models on the 40-profile subset (r = {r:.2f}). "
            "Each point is one customer, colored by customer type. "
            "Dashed line indicates y = x."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 10: Flag vs Non-Flag Pass Rate")
    print("=" * 60)

    df = load_data()
    customers = compute_rates(df)
    fig = create_figure(customers)

    fig_path = output_dir / "new_10_flag_vs_overall_passrate.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(customers)
    print("Done.")


if __name__ == "__main__":
    main()
