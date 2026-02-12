#!/usr/bin/env python3
"""
Generate New Plot 27: Pairwise Significance Heatmap.

Heatmap of p-values from McNemar's test between all AI model pairs
on overall pass rate (40-profile subset).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
from scipy.stats import chi2

from style import (
    setup_style,
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load tests.csv and filter."""
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


def mcnemar_test(a_pass, b_pass):
    """
    McNemar's test for paired binary outcomes.
    a_pass, b_pass: boolean arrays of same length.
    Returns p-value.
    """
    # Discordant pairs
    b_correct_a_wrong = ((~a_pass) & b_pass).sum()  # b=1, a=0
    a_correct_b_wrong = (a_pass & (~b_pass)).sum()  # a=1, b=0

    n = b_correct_a_wrong + a_correct_b_wrong
    if n == 0:
        return 1.0

    # McNemar's chi-squared statistic (with continuity correction)
    stat = (abs(b_correct_a_wrong - a_correct_b_wrong) - 1) ** 2 / n
    p_value = 1 - chi2.cdf(stat, df=1)
    return p_value


def compute_pairwise(df):
    """Compute pairwise McNemar p-values."""
    ai_models = [m for m in MODEL_ORDER if "Human" not in m and m in df["model_label"].unique()]
    n = len(ai_models)

    # Create aligned pass/fail arrays per model
    # Key: (customer_name, metric_name, prompt_type) -> pass
    model_data = {}
    for m in ai_models:
        subset = df[df["model_label"] == m].copy()
        subset["key"] = subset["customer_name"] + "|" + subset["metric_name"] + "|" + subset["prompt_type"]
        model_data[m] = subset.set_index("key")["pass"]

    # Find common keys across all models
    common_keys = None
    for m in ai_models:
        keys = set(model_data[m].index)
        if common_keys is None:
            common_keys = keys
        else:
            common_keys = common_keys & keys
    common_keys = sorted(common_keys)
    print(f"Common assertion keys across all models: {len(common_keys)}")

    # Compute p-values
    p_matrix = np.ones((n, n))
    for i in range(n):
        a_pass = model_data[ai_models[i]].loc[common_keys].astype(bool).values
        for j in range(i + 1, n):
            b_pass = model_data[ai_models[j]].loc[common_keys].astype(bool).values
            p = mcnemar_test(a_pass, b_pass)
            p_matrix[i, j] = p
            p_matrix[j, i] = p

    labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in ai_models]
    p_df = pd.DataFrame(p_matrix, index=labels, columns=labels)

    return p_df, ai_models


def create_figure(p_df):
    """Create significance heatmap."""
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    # Use -log10(p) for visualization, but show actual p-values in annotations
    display_data = -np.log10(p_df.values.clip(min=1e-30))
    np.fill_diagonal(display_data, 0)

    # Create annotation strings
    annot = p_df.copy()
    for i in range(len(p_df)):
        for j in range(len(p_df)):
            if i == j:
                annot.iloc[i, j] = "-"
            else:
                p = p_df.iloc[i, j]
                if p < 0.001:
                    annot.iloc[i, j] = f"{p:.0e}*"
                elif p < 0.01:
                    annot.iloc[i, j] = f"{p:.3f}*"
                elif p < 0.05:
                    annot.iloc[i, j] = f"{p:.3f}*"
                else:
                    annot.iloc[i, j] = f"{p:.2f}"

    mask = np.triu(np.ones_like(p_df, dtype=bool), k=1)

    sns.heatmap(
        display_data,
        mask=mask,
        annot=annot.values,
        fmt="",
        cmap="YlOrRd",
        ax=ax,
        xticklabels=p_df.columns,
        yticklabels=p_df.index,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "-log10(p-value)"},
        vmin=0,
        vmax=max(5, display_data[~mask].max()),
    )

    ax.set_title(
        "Pairwise McNemar's Test (Overall Pass Rate)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    ax.text(
        0.5,
        -0.08,
        "* = significant at p < 0.05. Lower triangle shown. Continuity-corrected McNemar's test.",
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=9,
        color="#6b7280",
        style="italic",
    )

    plt.tight_layout()
    return fig


def write_outputs(p_df):
    """Write data and caption files."""
    data_path = output_dir / "new_27_pairwise_significance_data.txt"
    with open(data_path, "w") as f:
        f.write("Plot 27: Pairwise McNemar's Test P-Values\n")
        f.write("=" * 60 + "\n\n")
        f.write(p_df.to_string(float_format=lambda x: f"{x:.4f}"))
        f.write("\n\nSignificant pairs (p < 0.05):\n")
        for i in range(len(p_df)):
            for j in range(i + 1, len(p_df)):
                p = p_df.iloc[i, j]
                if p < 0.05:
                    f.write(f"  {p_df.index[i]} vs {p_df.columns[j]}: p = {p:.4f}\n")
    print(f"Data saved to: {data_path}")

    n_sig = sum(
        1
        for i in range(len(p_df))
        for j in range(i + 1, len(p_df))
        if p_df.iloc[i, j] < 0.05
    )
    n_pairs = len(p_df) * (len(p_df) - 1) // 2

    caption_path = output_dir / "new_27_pairwise_significance.txt"
    with open(caption_path, "w") as f:
        f.write(
            f"Pairwise McNemar's test p-values for overall pass rate across {len(p_df)} AI models "
            f"on the 40-profile subset. {n_sig} of {n_pairs} pairs show significant differences "
            f"at p < 0.05 (continuity-corrected). Asterisks mark significant pairs."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 27: Pairwise Significance")
    print("=" * 60)

    df = load_data()
    p_df, ai_models = compute_pairwise(df)

    fig = create_figure(p_df)

    fig_path = output_dir / "new_27_pairwise_significance.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(p_df)
    print("Done.")


if __name__ == "__main__":
    main()
