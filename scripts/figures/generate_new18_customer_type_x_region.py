#!/usr/bin/env python3
"""
Generate New Plot 18: Pass Rate Heatmap for Customer Type x Region.

Two side-by-side heatmaps: left = 40-profile human baseline subset,
right = full 134-profile dataset. Each cell shows pass rate and
customer count in parentheses.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

from style import setup_style, COUNTRY_ORDER

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load tests dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def prepare_pivot(df, label):
    """Create pivot table and customer count matrix from a filtered dataframe."""
    # Pass rate pivot
    pivot = df.pivot_table(
        values="pass",
        index="customer_type",
        columns="institution_country",
        aggfunc="mean",
    ) * 100

    # Customer count: unique customers per cell
    count_pivot = df.groupby(["customer_type", "institution_country"])["customer_name"].nunique().unstack()

    # Reorder columns
    cols = [c for c in COUNTRY_ORDER if c in pivot.columns]
    pivot = pivot.reindex(columns=cols)
    count_pivot = count_pivot.reindex(columns=cols)

    # Sort rows alphabetically
    pivot = pivot.sort_index()
    count_pivot = count_pivot.reindex(index=pivot.index)

    print(f"\n{label} pivot shape: {pivot.shape}")
    print(f"  NaN cells: {pivot.isna().sum().sum()}")

    return pivot, count_pivot


def create_figure(pivot_40, count_40, pivot_full, count_full):
    """Create two side-by-side heatmaps."""
    setup_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 5.5))

    # Shared color range
    all_vals = pd.concat([pivot_40.stack(), pivot_full.stack()])
    vmin = all_vals.min() - 2
    vmax = all_vals.max() + 2
    cmap = sns.color_palette("Greens", as_cmap=True)

    for ax, pivot, counts, title in [
        (ax1, pivot_40, count_40, "40-Profile Subset"),
        (ax2, pivot_full, count_full, "Full Dataset (134 Profiles)"),
    ]:
        mask = pivot.isna()

        # Build annotation strings: "85.3\n(n=5)"
        annot_arr = np.full(pivot.shape, "", dtype=object)
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                if not mask.iloc[i, j]:
                    rate = pivot.iloc[i, j]
                    n = int(counts.iloc[i, j]) if pd.notna(counts.iloc[i, j]) else 0
                    annot_arr[i, j] = f"{rate:.1f}\n(n={n})"

        sns.heatmap(
            pivot,
            annot=annot_arr,
            fmt="",
            cmap=cmap,
            mask=mask,
            linewidths=1,
            linecolor="white",
            cbar_kws={"label": "Pass Rate (%)", "shrink": 0.8},
            ax=ax,
            vmin=vmin,
            vmax=vmax,
            annot_kws={"fontsize": 11, "fontweight": "bold"},
        )

        # Mark NaN cells
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                if mask.iloc[i, j]:
                    ax.text(
                        j + 0.5, i + 0.5, "N/A",
                        ha="center", va="center",
                        fontsize=10, color="#999999", style="italic",
                    )

        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Region", fontsize=11, fontweight="bold")
        ax.set_ylabel("Customer Type", fontsize=11, fontweight="bold")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=10)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)

    fig.suptitle(
        "Pass Rate by Customer Type and Region",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()
    return fig


def write_outputs(pivot_40, count_40, pivot_full, count_full):
    """Write data and caption files."""
    data_path = output_dir / "new_18_customer_type_x_region_data.txt"
    with open(data_path, "w") as f:
        f.write("Pass Rate (%) by Customer Type x Region\n")
        f.write("=" * 70 + "\n\n")

        f.write("--- 40-Profile Human Baseline Subset ---\n")
        f.write(pivot_40.to_string(float_format="%.1f", na_rep="N/A"))
        f.write("\n\nCustomer counts:\n")
        f.write(count_40.to_string(na_rep="0"))

        f.write("\n\n--- Full Dataset (134 Profiles) ---\n")
        f.write(pivot_full.to_string(float_format="%.1f", na_rep="N/A"))
        f.write("\n\nCustomer counts:\n")
        f.write(count_full.to_string(na_rep="0"))
        f.write("\n")
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_18_customer_type_x_region.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Side-by-side heatmaps of overall pass rates by customer type and region, "
            "averaged across AI models. Left: 40-profile human baseline subset. "
            "Right: full 134-profile dataset. Each cell shows the pass rate and "
            "number of customers (n) in that combination. N/A = no data."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 18: Customer Type x Region (Dual Heatmap)")
    print("=" * 60)

    df = load_data()

    # AI models only for both
    df_ai = df[df["model_type"] != "human_baseline"]

    # 40-profile subset
    df_40 = df_ai[df_ai["is_human_baseline_dataset"] == True]
    pivot_40, count_40 = prepare_pivot(df_40, "40-profile")

    # Full dataset
    pivot_full, count_full = prepare_pivot(df_ai, "Full dataset")

    fig = create_figure(pivot_40, count_40, pivot_full, count_full)

    fig_path = output_dir / "new_18_customer_type_x_region.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure saved to: {fig_path}")
    plt.close()

    write_outputs(pivot_40, count_40, pivot_full, count_full)
    print("Done.")


if __name__ == "__main__":
    main()
