#!/usr/bin/env python3
"""
Generate Figure S6: Pass rates heatmap by screener and customer type (full dataset, 134 profiles).
Same as Figure S2/2c but using all 134 profiles and excluding human baseline.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

from style import (
    MODEL_ORDER, shorten_model_label_no_time, setup_style
)

CUSTOMER_TYPE_ORDER = [
    "Controlled Agent Academia",
    "Controlled Agent Industry",
    "Sanctioned Institution Customers",
    "General Life Science Customers",
]

CUSTOMER_TYPE_LABELS = {
    "Controlled Agent Academia": "Academic w/\nSOC backg.",
    "Controlled Agent Industry": "Industry w/\nSOC backg.",
    "Sanctioned Institution Customers": "Sanctioned\nAcademic",
    "General Life Science Customers": "General\nLife Science",
}


def load_data():
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)
    df = df[~df['model_label'].str.contains('Human', case=False, na=False)].copy()
    print(f"Full dataset (AI only): {len(df):,} rows")
    return df


def create_figure(df):
    setup_style()

    pivot = df.pivot_table(values="pass", index="model_label", columns="customer_type", aggfunc="mean") * 100

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    customer_types = [c for c in CUSTOMER_TYPE_ORDER if c in pivot.columns]

    gap_size = 0.7
    fig, ax = plt.subplots(figsize=(6, 10))

    cmap = LinearSegmentedColormap.from_list('greens', ['#dcfce7', '#166534'])
    norm = Normalize(vmin=50, vmax=100)

    cell_width = 1.0
    cell_height = 1.0

    y_positions = {}
    annotation_positions = {}
    current_y = 0

    annotation_positions['w'] = current_y + gap_size / 2
    current_y += gap_size
    for model in w_models:
        y_positions[model] = current_y
        current_y += cell_height

    annotation_positions['at'] = current_y + gap_size / 2
    current_y += gap_size
    for model in at_models:
        y_positions[model] = current_y
        current_y += cell_height

    models_display_order = w_models + at_models

    for model in models_display_order:
        y_pos = y_positions[model]
        for j, ctype in enumerate(customer_types):
            if model in pivot.index and ctype in pivot.columns:
                value = pivot.loc[model, ctype]
                if pd.notna(value):
                    color = cmap(norm(value))
                    text_color = 'white' if value > 75 else 'black'
                    rect = plt.Rectangle((j, y_pos), cell_width, cell_height,
                                          facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    ax.text(j + cell_width/2, y_pos + cell_height/2, f"{value:.1f}",
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)

    ax.set_xlim(0, len(customer_types))
    ax.set_ylim(0, current_y)

    y_ticks = [y_positions[m] + cell_height/2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label_no_time(m) for m in models_display_order], fontsize=11)

    ax.set_xticks([i + cell_width/2 for i in range(len(customer_types))])
    ax.set_xticklabels([CUSTOMER_TYPE_LABELS.get(c, c) for c in customer_types], fontsize=11)

    center_x = len(customer_types) / 2
    if w_models:
        ax.text(center_x, annotation_positions['w'],
                "AI - Web Only (W)", ha='center', va='center',
                fontsize=11, fontweight='bold', color='black', style='italic')
    if at_models:
        ax.text(center_x, annotation_positions['at'],
                "AI - All Tools (AT)", ha='center', va='center',
                fontsize=11, fontweight='bold', color='black', style='italic')

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Pass Rate (%)", fontsize=12)

    ax.set_title("Pass Rate by Screener and Customer Type\n(Full Dataset, 134 Profiles)",
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Customer Type", fontsize=12, fontweight='bold')
    ax.set_ylabel("Screener", fontsize=12, fontweight='bold')

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    return fig, pivot


def main():
    print("Generating Figure S6: Full dataset pass rates by customer type")
    print("=" * 60)

    df = load_data()
    fig, pivot = create_figure(df)

    extra_plots_dir = Path(__file__).parent.parent.parent / "paper" / "extra-plots"
    extra_plots_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(extra_plots_dir / "figure_S6_pass_rates_by_customer_type_full.png",
                dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to: {extra_plots_dir / 'figure_S6_pass_rates_by_customer_type_full.png'}")

    data_path = extra_plots_dir / "figure_S6_pass_rates_by_customer_type_full_data.txt"
    with open(data_path, "w") as f:
        f.write("Figure S6: Pass Rates by Screener and Customer Type (Full Dataset, 134 Profiles)\n")
        f.write("=" * 70 + "\n\n")
        f.write(pivot.round(1).to_string())
        f.write("\n")
    print(f"Data saved to: {data_path}")

    plt.close()


if __name__ == "__main__":
    main()
