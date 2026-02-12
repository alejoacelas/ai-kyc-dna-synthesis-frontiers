#!/usr/bin/env python3
"""
Generate New Plot 30: Dataset Size Effect.

Grouped bar showing pass rate on 40-profile vs 134-profile dataset per AI model.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    setup_style,
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
    get_model_color,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load tests.csv."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def compute_rates(df):
    """Compute pass rates for both datasets per model."""
    ai_models = [m for m in MODEL_ORDER if "Human" not in m and m in df["model_label"].unique()]

    # 40-profile subset
    df_40 = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ]
    rates_40 = df_40.groupby("model_label")["pass"].mean() * 100

    # Full dataset (134 profiles) - AI models only
    df_full = df[df["model_type"] != "human_baseline"]
    rates_full = df_full.groupby("model_label")["pass"].mean() * 100

    results = []
    for m in ai_models:
        r40 = rates_40.get(m, np.nan)
        rfull = rates_full.get(m, np.nan)
        results.append({
            "model": m,
            "short": MODEL_LABELS_NO_TIME.get(m, m),
            "rate_40": r40,
            "rate_full": rfull,
            "diff": rfull - r40 if not (np.isnan(r40) or np.isnan(rfull)) else np.nan,
        })

    return pd.DataFrame(results)


def create_figure(results_df):
    """Create grouped bar chart."""
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(results_df))
    width = 0.35

    bars_40 = ax.bar(
        x - width / 2,
        results_df["rate_40"],
        width,
        label="40-profile subset",
        color="#3498db",
        alpha=0.8,
        edgecolor="white",
        linewidth=0.5,
    )
    bars_full = ax.bar(
        x + width / 2,
        results_df["rate_full"],
        width,
        label="Full dataset (134)",
        color="#2c3e50",
        alpha=0.8,
        edgecolor="white",
        linewidth=0.5,
    )

    # Add value labels
    for bars in [bars_40, bars_full]:
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.3,
                    f"{height:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                )

    ax.set_xticks(x)
    ax.set_xticklabels(results_df["short"], rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title(
        "Pass Rate: 40-Profile Subset vs Full Dataset",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Set y-axis to start from a reasonable value
    min_val = min(results_df["rate_40"].min(), results_df["rate_full"].min())
    ax.set_ylim(max(0, min_val - 5), 100)

    plt.tight_layout()
    return fig


def write_outputs(results_df):
    """Write data and caption files."""
    data_path = output_dir / "new_30_dataset_size_effect_data.txt"
    with open(data_path, "w") as f:
        f.write("Plot 30: Pass Rate by Dataset Size\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"{'Model':<15s} {'40-profile':>12s} {'Full (134)':>12s} {'Diff':>8s}\n")
        f.write("-" * 50 + "\n")
        for _, row in results_df.iterrows():
            diff_str = f"{row['diff']:+.1f}%" if not np.isnan(row["diff"]) else "N/A"
            f.write(
                f"{row['short']:<15s} {row['rate_40']:>11.1f}% {row['rate_full']:>11.1f}% {diff_str:>8s}\n"
            )
    print(f"Data saved to: {data_path}")

    mean_diff = results_df["diff"].mean()
    caption_path = output_dir / "new_30_dataset_size_effect.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Comparison of overall pass rates between the 40-profile human baseline subset "
            "and the full 134-profile dataset for each AI model. "
            f"Mean difference: {mean_diff:+.1f} percentage points."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 30: Dataset Size Effect")
    print("=" * 60)

    df = load_data()
    results_df = compute_rates(df)
    print("\nResults:")
    print(results_df[["short", "rate_40", "rate_full", "diff"]].to_string(index=False))

    fig = create_figure(results_df)

    fig_path = output_dir / "new_30_dataset_size_effect.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(results_df)
    print("Done.")


if __name__ == "__main__":
    main()
