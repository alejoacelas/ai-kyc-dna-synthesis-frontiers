#!/usr/bin/env python3
"""
Generate New Plot 26: Correlation Matrix of Test Category Pass Rates.

Heatmap showing the pairwise Pearson correlation between the four test
category pass rates (flag_accuracy, claim_support, source_reliability,
work_relevance) computed per customer and averaged across AI models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

from style import setup_style, CATEGORY_ORDER, CATEGORY_LABELS

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
    """Compute per-customer pass rates by test category, then correlation matrix."""
    df_ai = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()
    print(f"AI rows on baseline dataset: {len(df_ai):,}")

    # Per customer per test_category: mean pass rate across all AI models
    customer_cat = (
        df_ai.groupby(["customer_name", "test_category"])["pass"]
        .mean()
        .reset_index()
    )

    # Pivot: rows = customers, columns = test categories
    pivot = customer_cat.pivot_table(
        values="pass",
        index="customer_name",
        columns="test_category",
        aggfunc="mean",
    )

    # Reorder columns by CATEGORY_ORDER
    cols = [c for c in CATEGORY_ORDER if c in pivot.columns]
    pivot = pivot[cols]

    print(f"Customer x Category pivot shape: {pivot.shape}")
    print(f"NaN count: {pivot.isna().sum().sum()}")

    # Compute Pearson correlation matrix
    corr = pivot.corr(method="pearson")

    return pivot, corr


def create_figure(corr):
    """Create correlation matrix heatmap."""
    setup_style()

    fig, ax = plt.subplots(figsize=(8, 7))

    # Use CATEGORY_LABELS for display
    display_labels = [CATEGORY_LABELS.get(c, c) for c in corr.columns]

    # Rename for display
    corr_display = corr.copy()
    corr_display.index = display_labels
    corr_display.columns = display_labels

    # Diverging colormap: RdBu_r (red = negative, blue = positive)
    mask = np.triu(np.ones_like(corr_display, dtype=bool), k=1)

    sns.heatmap(
        corr_display,
        annot=True,
        fmt=".3f",
        cmap="RdBu_r",
        mask=mask,
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "Pearson Correlation", "shrink": 0.8},
        ax=ax,
        annot_kws={"fontsize": 13, "fontweight": "bold"},
    )

    ax.set_title(
        "Correlation of Test Category Pass Rates Across Customers\n(AI Models, Human Baseline Subset)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=11)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11)

    plt.tight_layout()
    return fig


def write_outputs(pivot, corr):
    """Write data and caption files."""
    data_path = output_dir / "new_26_metric_correlation_data.txt"
    with open(data_path, "w") as f:
        f.write("Pearson Correlation Matrix of Test Category Pass Rates\n")
        f.write("(Per-customer pass rates averaged across AI models)\n")
        f.write("=" * 60 + "\n\n")

        # Rename for display
        display_corr = corr.copy()
        display_corr.index = [CATEGORY_LABELS.get(c, c) for c in corr.index]
        display_corr.columns = [CATEGORY_LABELS.get(c, c) for c in corr.columns]
        f.write(display_corr.to_string(float_format="%.4f"))

        f.write("\n\nPer-customer pass rate summary (before correlation):\n")
        for col in pivot.columns:
            label = CATEGORY_LABELS.get(col, col)
            vals = pivot[col].dropna()
            f.write(
                f"  {label:25s}  mean={vals.mean():.3f}  std={vals.std():.3f}  "
                f"n={len(vals)}\n"
            )

        f.write(f"\nNumber of customers: {len(pivot)}\n")

    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_26_metric_correlation.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Pearson correlation matrix of per-customer pass rates across the four "
            "test categories (Flag Accuracy, Claim Support, Source Reliability, "
            "Work Relevance), computed on the 40-profile human baseline subset with "
            "pass rates averaged across all AI models. The lower triangle of the "
            "matrix is shown; color scale ranges from -1 (red) to +1 (blue)."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 26: Metric Correlation Matrix")
    print("=" * 60)

    df = load_data()
    pivot, corr = prepare_data(df)
    fig = create_figure(corr)

    fig_path = output_dir / "new_26_metric_correlation.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(pivot, corr)
    print("Done.")


if __name__ == "__main__":
    main()
