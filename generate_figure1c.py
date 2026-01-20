#!/usr/bin/env python3
"""
Generate Figure 1c: Pass rates heatmap by screener and customer type.

Shows pass rates with models grouped into three blocks:
- AT (All Tools): AI screeners with full tool access
- W (Web-only): AI screeners with web search only
- Human: Human baseline screeners

X-axis shows customer types: Academic w/ SOC background, Industry w/ SOC background,
Sanctioned Academic, General Life Science.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

# Add plots directory to path for style imports
sys.path.append(str(Path(__file__).parent / "plots"))
from style import (
    COLORS, MODEL_LABELS, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    get_model_color, shorten_model_label, setup_style
)


# Customer type mapping from data values to display labels
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


def load_and_filter_data():
    """Load test data and filter for human baseline dataset."""
    data_path = Path(__file__).parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()
    print(f"Rows after human baseline filter: {len(df_filtered):,}")

    # Verify customer types
    print(f"Customer types in data: {df_filtered['customer_type'].unique()}")

    return df_filtered


def create_figure(df):
    """Create the heatmap with three separated blocks."""
    setup_style()

    # Calculate pass rates by model and customer type
    pivot = df.pivot_table(
        values="pass",
        index="model_label",
        columns="customer_type",
        aggfunc="mean"
    ) * 100

    # Group models by type: AT first, then W, then Human
    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and m in pivot.index]

    customer_types = [c for c in CUSTOMER_TYPE_ORDER if c in pivot.columns]

    n_at = len(at_models)
    n_w = len(w_models)
    n_human = len(human_models)

    print(f"AT models: {n_at}, W models: {n_w}, Human models: {n_human}")
    print(f"Customer types: {customer_types}")

    # Gap size between groups (for annotation text above each group)
    gap_size = 0.7

    # Create figure (adjusted width for 4 columns)
    fig, ax = plt.subplots(figsize=(6, 12))

    from matplotlib.colors import Normalize, LinearSegmentedColormap
    from matplotlib.cm import ScalarMappable

    # Green-only color palette (light to dark green)
    cmap = LinearSegmentedColormap.from_list('greens', ['#dcfce7', '#166534'])
    norm = Normalize(vmin=50, vmax=100)

    cell_width = 1.0
    cell_height = 1.0

    # Build y positions: AT at top, then gap, W in middle, then gap, Human at bottom
    # Each group has annotation space ABOVE it
    y_positions = {}
    annotation_positions = {}
    current_y = 0

    # Human models at bottom (with annotation space above)
    annotation_positions['human'] = current_y + gap_size / 2
    current_y += gap_size
    for i, model in enumerate(human_models):
        y_positions[model] = current_y
        current_y += cell_height

    # W models in middle (with annotation space above)
    annotation_positions['w'] = current_y + gap_size / 2
    current_y += gap_size
    for i, model in enumerate(w_models):
        y_positions[model] = current_y
        current_y += cell_height

    # AT models at top (with annotation space above)
    annotation_positions['at'] = current_y + gap_size / 2
    current_y += gap_size
    for i, model in enumerate(at_models):
        y_positions[model] = current_y
        current_y += cell_height

    # Order for display (bottom to top): Human, W, AT
    models_display_order = human_models + w_models + at_models

    # Draw cells
    for model in models_display_order:
        y_pos = y_positions[model]
        for j, ctype in enumerate(customer_types):
            if model in pivot.index and ctype in pivot.columns:
                value = pivot.loc[model, ctype]
                if pd.notna(value):
                    color = cmap(norm(value))
                    rect = plt.Rectangle((j, y_pos), cell_width, cell_height,
                                          facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    # Text color based on value (white on dark green, black on light green)
                    text_color = 'white' if value > 75 else 'black'
                    ax.text(j + cell_width/2, y_pos + cell_height/2, f"{value:.1f}",
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)

    # Set axis limits
    ax.set_xlim(0, len(customer_types))
    ax.set_ylim(0, current_y)

    # Y-axis ticks and labels
    y_ticks = [y_positions[m] + cell_height/2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label(m) for m in models_display_order], fontsize=11)

    # X-axis ticks and labels
    ax.set_xticks([i + cell_width/2 for i in range(len(customer_types))])
    ax.set_xticklabels([CUSTOMER_TYPE_LABELS.get(c, c) for c in customer_types], fontsize=11)

    # Add centered section annotations ABOVE each group
    center_x = len(customer_types) / 2

    if n_human > 0:
        ax.text(center_x, annotation_positions['human'],
                "Human Baseline",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    if n_w > 0:
        ax.text(center_x, annotation_positions['w'],
                "AI - Web Only (W)",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    if n_at > 0:
        ax.text(center_x, annotation_positions['at'],
                "AI - All Tools (AT)",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    # Add colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Pass Rate (%)", fontsize=12)

    ax.set_title("Pass Rate by Screener and Customer Type", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Customer Type", fontsize=12, fontweight='bold')
    ax.set_ylabel("Screener", fontsize=12, fontweight='bold')

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()

    return fig


def main():
    """Main function to generate Figure 1c."""
    print("Generating Figure 1c: Pass rates heatmap by customer type")
    print("=" * 60)

    # Load data
    df = load_and_filter_data()

    # Create the figure
    fig = create_figure(df)

    # Save the figure
    output_path = Path(__file__).parent / "paper" / "figures" / "figure1c_pass_rates_by_customer_type.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    plt.close()

    print("\n" + "=" * 60)
    print("Caption:")
    print("Pass rates by screener and customer type. Customer types include:")
    print("Academic w/ SOC background, Industry w/ SOC background, Sanctioned Academic,")
    print("and General Life Science.")


if __name__ == "__main__":
    main()
