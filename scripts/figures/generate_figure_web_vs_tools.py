#!/usr/bin/env python3
"""
Generate Figure S10: Web-only vs All-tools comparison by test category.
Paired bar chart showing average pass rates for web-only and all-tools configurations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    COLORS, CATEGORY_ORDER, CATEGORY_LABELS, setup_style
)


def load_data():
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)
    # Filter: AI models only, human baseline dataset
    df = df[
        (df["is_human_baseline_dataset"] == True) &
        (~df["model_label"].str.contains("Human", case=False, na=False))
    ].copy()
    print(f"Filtered rows (AI, human baseline dataset): {len(df):,}")
    return df


def create_figure(df):
    setup_style()

    # Calculate pass rates by model_type and test_category
    pivot = df.pivot_table(
        values="pass",
        index="test_category",
        columns="model_type",
        aggfunc="mean"
    ) * 100

    categories = [c for c in CATEGORY_ORDER if c in pivot.index]

    web_rates = [pivot.loc[c, "web_only"] for c in categories]
    at_rates = [pivot.loc[c, "all_tools"] for c in categories]
    diffs = [at - web for at, web in zip(at_rates, web_rates)]

    fig, ax = plt.subplots(figsize=(10, 7))

    x = np.arange(len(categories))
    width = 0.35

    bars_web = ax.bar(x - width/2, web_rates, width,
                      label="Web Only (W)", color=COLORS["web_only"], alpha=0.9)
    bars_at = ax.bar(x + width/2, at_rates, width,
                     label="All Tools (AT)", color=COLORS["all_tools"], alpha=0.9)

    # Add value labels
    for bar in bars_web:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar in bars_at:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Add difference annotations
    for i, diff in enumerate(diffs):
        sign = "+" if diff >= 0 else ""
        color = "#16a34a" if diff >= 0 else "#dc2626"
        y_pos = max(web_rates[i], at_rates[i]) + 2.5
        ax.text(x[i], y_pos, f"{sign}{diff:.1f} pp",
                ha="center", va="bottom", fontsize=10, fontweight="bold", color=color)

    ax.set_xticks(x)
    cat_labels = {
        "flag_accuracy": "Flag\nAccuracy",
        "claim_support": "Source\nFidelity",
        "source_reliability": "Source\nQuality",
        "work_relevance": "Work\nRelevance",
    }
    ax.set_xticklabels([cat_labels.get(c, c) for c in categories], fontsize=11)
    ax.set_xlabel("Test Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Effect of Specialized Tools on Pass Rates by Test Category",
                 fontsize=14, fontweight="bold", pad=15)

    ax.legend(loc="lower right", fontsize=10)

    # Y-axis from 70 to 100
    ax.set_ylim(70, 100)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    return fig, categories, web_rates, at_rates, diffs


def main():
    print("Generating Figure S10: Web vs Tools comparison")
    print("=" * 60)

    df = load_data()
    fig, categories, web_rates, at_rates, diffs = create_figure(df)

    extra_plots_dir = Path(__file__).parent.parent.parent / "paper" / "extra-plots"
    extra_plots_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(extra_plots_dir / "figure_S10_web_vs_tools.png",
                dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to: {extra_plots_dir / 'figure_S10_web_vs_tools.png'}")

    # Save data
    data_path = extra_plots_dir / "figure_S10_web_vs_tools_data.txt"
    cat_labels = {
        "flag_accuracy": "Flag Accuracy",
        "claim_support": "Source Fidelity",
        "source_reliability": "Source Quality",
        "work_relevance": "Work Relevance",
    }
    with open(data_path, "w") as f:
        f.write("Figure S10: Web-only vs All-tools Pass Rate Comparison\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'Category':<20s} {'Web Only %':>10s} {'All Tools %':>12s} {'Difference':>11s}\n")
        f.write("-" * 53 + "\n")
        for c, w, a, d in zip(categories, web_rates, at_rates, diffs):
            sign = "+" if d >= 0 else ""
            f.write(f"{cat_labels.get(c, c):<20s} {w:10.1f} {a:12.1f} {sign}{d:10.1f} pp\n")
    print(f"Data saved to: {data_path}")

    plt.close()


if __name__ == "__main__":
    main()
