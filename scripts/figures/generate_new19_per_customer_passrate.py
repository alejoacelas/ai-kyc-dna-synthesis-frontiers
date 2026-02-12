#!/usr/bin/env python3
"""
Generate New Plot 19: Per-Customer Overall Pass Rate by Customer Type.

Strip/swarm plot showing the distribution of per-customer overall pass rates,
grouped and colored by customer_type. A horizontal mean line is added for
reference.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

from style import setup_style, COLORS

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
    """Filter and compute per-customer pass rate averaged across AI models."""
    df_ai = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()
    print(f"AI rows on baseline dataset: {len(df_ai):,}")

    # Per customer: mean pass rate across all AI models and test categories
    customer_pass = (
        df_ai.groupby(["customer_name", "customer_type"])["pass"]
        .mean()
        .reset_index()
    )
    customer_pass["pass_rate"] = customer_pass["pass"] * 100

    print(f"Unique customers: {len(customer_pass)}")
    print(f"Customer type distribution:\n{customer_pass['customer_type'].value_counts()}")

    return customer_pass


def create_figure(customer_pass):
    """Create strip/swarm plot."""
    setup_style()

    # Define customer type order for x-axis
    ct_order = [
        "Controlled Agent Academia",
        "Controlled Agent Industry",
        "General Life Science Customers",
        "Sanctioned Institution Customers",
    ]
    # Keep only types that exist in the data
    ct_order = [ct for ct in ct_order if ct in customer_pass["customer_type"].values]

    # Build palette
    palette = {ct: COLORS.get(ct, "#999999") for ct in ct_order}

    fig, ax = plt.subplots(figsize=(12, 7))

    # Swarm plot
    sns.swarmplot(
        data=customer_pass,
        x="customer_type",
        y="pass_rate",
        hue="customer_type",
        order=ct_order,
        hue_order=ct_order,
        palette=palette,
        size=8,
        alpha=0.75,
        legend=False,
        ax=ax,
    )

    # Add horizontal line at overall mean
    overall_mean = customer_pass["pass_rate"].mean()
    ax.axhline(
        overall_mean,
        color="black",
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        label=f"Overall mean ({overall_mean:.1f}%)",
    )

    # Add per-group means as horizontal markers
    for i, ct in enumerate(ct_order):
        group_mean = customer_pass.loc[
            customer_pass["customer_type"] == ct, "pass_rate"
        ].mean()
        ax.hlines(
            group_mean,
            i - 0.3,
            i + 0.3,
            colors=palette[ct],
            linewidths=2.5,
            alpha=0.9,
        )

    ax.set_ylabel("Overall Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Customer Type", fontsize=12, fontweight="bold")
    ax.set_title(
        "Per-Customer Pass Rate by Customer Type\n(Average across AI Models)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Shorten x-axis labels
    short_labels = {
        "Controlled Agent Academia": "Controlled\nAcademia",
        "Controlled Agent Industry": "Controlled\nIndustry",
        "General Life Science Customers": "General Life\nScience",
        "Sanctioned Institution Customers": "Sanctioned\nInstitution",
    }
    ax.set_xticks(range(len(ct_order)))
    ax.set_xticklabels([short_labels.get(ct, ct) for ct in ct_order], fontsize=10)

    ax.legend(loc="lower left", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def write_outputs(customer_pass):
    """Write data and caption files."""
    data_path = output_dir / "new_19_per_customer_passrate_data.txt"
    with open(data_path, "w") as f:
        f.write("Per-Customer Overall Pass Rate by Customer Type\n")
        f.write("(averaged across AI models, human baseline dataset)\n")
        f.write("=" * 70 + "\n\n")

        for ct in sorted(customer_pass["customer_type"].unique()):
            subset = customer_pass[customer_pass["customer_type"] == ct]
            f.write(f"\n{ct} (n={len(subset)}):\n")
            f.write(f"  Mean: {subset['pass_rate'].mean():.1f}%\n")
            f.write(f"  Median: {subset['pass_rate'].median():.1f}%\n")
            f.write(f"  Std: {subset['pass_rate'].std():.1f}%\n")
            f.write(f"  Min: {subset['pass_rate'].min():.1f}%\n")
            f.write(f"  Max: {subset['pass_rate'].max():.1f}%\n")

        overall_mean = customer_pass["pass_rate"].mean()
        f.write(f"\nOverall mean: {overall_mean:.1f}%\n")

        f.write("\nPer-customer detail:\n")
        for _, row in customer_pass.sort_values("pass_rate").iterrows():
            f.write(f"  {row['customer_name']:40s}  {row['customer_type']:40s}  {row['pass_rate']:.1f}%\n")
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_19_per_customer_passrate.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Swarm plot of per-customer overall pass rates on the 40-profile human "
            "baseline subset, grouped by customer type and colored accordingly. Each "
            "dot represents one customer's average pass rate across all AI models. "
            "Horizontal colored bars show group means; the dashed black line shows "
            "the overall mean across all customers."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 19: Per-Customer Pass Rate by Customer Type")
    print("=" * 60)

    df = load_data()
    customer_pass = prepare_data(df)
    fig = create_figure(customer_pass)

    fig_path = output_dir / "new_19_per_customer_passrate.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(customer_pass)
    print("Done.")


if __name__ == "__main__":
    main()
