#!/usr/bin/env python3
"""
Generate Figure S3: Web search counts by model configuration.
Bar chart showing average number of web searches per customer for each model.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    MODEL_ORDER, MODEL_LABELS_NO_TIME, COLORS,
    get_model_color, setup_style
)


def load_data():
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    df = pd.read_csv(data_path)
    # Filter AI models only, human baseline dataset
    df = df[
        (df["model_type"] != "human_baseline") &
        (df["is_human_baseline_dataset"] == True)
    ].copy()
    print(f"Filtered rows (AI, human baseline dataset): {len(df):,}")
    return df


def create_figure(df):
    setup_style()

    # Sum web searches across both prompts per customer per model
    customer_searches = df.groupby(["customer_name", "model_label"])["num_web_searches"].sum().reset_index()

    # Average across customers per model
    model_searches = customer_searches.groupby("model_label")["num_web_searches"].mean()

    # Order by MODEL_ORDER
    models = [m for m in MODEL_ORDER if m in model_searches.index]
    values = [model_searches[m] for m in models]
    colors = [get_model_color(m) for m in models]
    short_labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]

    fig, ax = plt.subplots(figsize=(12, 7))

    bars = ax.bar(range(len(models)), values, color=colors, alpha=0.9,
                  edgecolor='white', linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Web Searches per Customer", fontsize=12, fontweight="bold")
    ax.set_title("Average Web Searches per Customer by Model", fontsize=14, fontweight="bold", pad=15)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="All Tools (AT)", alpha=0.9),
        Patch(facecolor=COLORS["web_only"], label="Web Only (W)", alpha=0.9),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_val = max(values) if values else 10
    ax.set_ylim(0, max_val * 1.12)

    plt.tight_layout()
    return fig, models, values


def main():
    print("Generating Figure S3: Web search counts by model")
    print("=" * 60)

    df = load_data()
    fig, models, values = create_figure(df)

    extra_plots_dir = Path(__file__).parent.parent.parent / "paper" / "extra-plots"
    extra_plots_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(extra_plots_dir / "figure_S3_web_searches.png",
                dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to: {extra_plots_dir / 'figure_S3_web_searches.png'}")

    # Save data
    data_path = extra_plots_dir / "figure_S3_web_searches_data.txt"
    with open(data_path, "w") as f:
        f.write("Figure S3: Average Web Searches per Customer by Model\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'Model':<45s} {'Avg Web Searches':>16s}\n")
        f.write("-" * 61 + "\n")
        for m, v in zip(models, values):
            f.write(f"{m:<45s} {v:16.1f}\n")
    print(f"Data saved to: {data_path}")

    plt.close()


if __name__ == "__main__":
    main()
