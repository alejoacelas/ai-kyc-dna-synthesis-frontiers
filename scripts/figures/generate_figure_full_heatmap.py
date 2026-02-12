#!/usr/bin/env python3
"""
Generate Figure S4: Pass rates heatmap (full dataset, 134 profiles).
Same as Figure 2 but using all 134 profiles and excluding human baseline.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

from style import (
    MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    shorten_model_label_no_time, setup_style
)

FIGURE_CATEGORY_LABELS = {
    "flag_accuracy": "Flag\nAccuracy",
    "claim_support": "Source\nFidelity",
    "source_reliability": "Source\nQuality",
    "work_relevance": "Work\nRelevance",
    "all_metrics": "All\nMetrics",
}


def load_data():
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)
    # Exclude human baselines
    df = df[~df['model_label'].str.contains('Human', case=False, na=False)].copy()
    print(f"Full dataset (AI only): {len(df):,} rows")
    return df


def create_figure(df):
    setup_style()

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="test_category", aggfunc="mean"
    ) * 100

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]

    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]
    pivot["all_metrics"] = pivot[categories].mean(axis=1)
    categories_with_all = categories + ["all_metrics"]

    n_at = len(at_models)
    n_w = len(w_models)

    gap_size = 0.7
    all_metrics_gap = 0.3

    fig, ax = plt.subplots(figsize=(6, 10))

    cmap = LinearSegmentedColormap.from_list('greens', ['#dcfce7', '#166534'])
    norm = Normalize(vmin=60, vmax=100)

    cell_width = 1.0
    cell_height = 1.0

    y_positions = {}
    annotation_positions = {}
    current_y = 0

    # W models at bottom
    annotation_positions['w'] = current_y + gap_size / 2
    current_y += gap_size
    for model in w_models:
        y_positions[model] = current_y
        current_y += cell_height

    # AT models at top
    annotation_positions['at'] = current_y + gap_size / 2
    current_y += gap_size
    for model in at_models:
        y_positions[model] = current_y
        current_y += cell_height

    models_display_order = w_models + at_models

    x_positions = {}
    for j, cat in enumerate(categories):
        x_positions[cat] = j * cell_width
    x_positions["all_metrics"] = len(categories) * cell_width + all_metrics_gap

    for model in models_display_order:
        y_pos = y_positions[model]
        for cat in categories_with_all:
            x_pos = x_positions[cat]
            if model in pivot.index and cat in pivot.columns:
                value = pivot.loc[model, cat]
                if pd.notna(value):
                    color = cmap(norm(value))
                    text_color = 'white' if value > 75 else 'black'
                    rect = plt.Rectangle((x_pos, y_pos), cell_width, cell_height,
                                          facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2, f"{value:.1f}",
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)

    ax.set_xlim(0, x_positions["all_metrics"] + cell_width)
    ax.set_ylim(0, current_y)

    y_ticks = [y_positions[m] + cell_height/2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label_no_time(m) for m in models_display_order], fontsize=11)

    x_ticks = [x_positions[cat] + cell_width/2 for cat in categories_with_all]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([FIGURE_CATEGORY_LABELS.get(cat, cat) for cat in categories_with_all], fontsize=11)
    tick_labels = ax.get_xticklabels()
    tick_labels[-1].set_fontweight('bold')

    total_width = x_positions["all_metrics"] + cell_width
    center_x = total_width / 2

    if n_w > 0:
        ax.text(center_x, annotation_positions['w'],
                "AI - Web Only (W)", ha='center', va='center',
                fontsize=11, fontweight='bold', color='black', style='italic')
    if n_at > 0:
        ax.text(center_x, annotation_positions['at'],
                "AI - All Tools (AT)", ha='center', va='center',
                fontsize=11, fontweight='bold', color='black', style='italic')

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Pass Rate (%)", fontsize=12)

    ax.set_title("Pass Rate by Screener and Test Category\n(Full Dataset, 134 Profiles)",
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Test Category", fontsize=12, fontweight='bold')
    ax.set_ylabel("Screener", fontsize=12, fontweight='bold')

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    return fig, pivot


def main():
    print("Generating Figure S4: Full dataset pass rates heatmap")
    print("=" * 60)

    df = load_data()
    fig, pivot = create_figure(df)

    extra_plots_dir = Path(__file__).parent.parent.parent / "paper" / "extra-plots"
    extra_plots_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(extra_plots_dir / "figure_S4_pass_rates_heatmap_full.png",
                dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to: {extra_plots_dir / 'figure_S4_pass_rates_heatmap_full.png'}")

    # Save data
    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]
    data_path = extra_plots_dir / "figure_S4_pass_rates_heatmap_full_data.txt"
    with open(data_path, "w") as f:
        f.write("Figure S4: Pass Rates by Screener and Test Category (Full Dataset, 134 Profiles)\n")
        f.write("=" * 70 + "\n\n")
        f.write(pivot[categories + ["all_metrics"]].round(1).to_string())
        f.write("\n")
    print(f"Data saved to: {data_path}")

    plt.close()


if __name__ == "__main__":
    main()
