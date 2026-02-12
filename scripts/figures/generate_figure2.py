#!/usr/bin/env python3
"""
Generate Figure 1: Pass rates heatmap by screener and test category.

Shows pass rates with models grouped into three blocks:
- AT (All Tools): AI screeners with full tool access
- W (Web-only): AI screeners with web search only
- Human: Human baseline screeners

Visual separation between groups emphasizes the different screener configurations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Import style from same directory
from style import (
    COLORS, MODEL_LABELS, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    get_model_color, shorten_model_label, setup_style
)


def load_and_filter_data():
    """Load test data and filter for human baseline dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()
    print(f"Rows after human baseline filter: {len(df_filtered):,}")

    return df_filtered


def create_figure(df):
    """Create the heatmap with three separated blocks."""
    setup_style()

    # Calculate pass rates
    pivot = df.pivot_table(
        values="pass",
        index="model_label",
        columns="test_category",
        aggfunc="mean"
    ) * 100

    # Group models by type: AT first, then W, then Human
    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and m in pivot.index]

    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]

    # Add "All Metrics" column as the average across all metrics
    pivot["all_metrics"] = pivot[categories].mean(axis=1)
    categories_with_all = categories + ["all_metrics"]

    n_at = len(at_models)
    n_w = len(w_models)
    n_human = len(human_models)

    print(f"AT models: {n_at}, W models: {n_w}, Human models: {n_human}")

    # Gap size between groups (for annotation text above each group)
    gap_size = 0.7

    # Gap size before "All Metrics" column
    all_metrics_gap = 0.3

    # Create figure (increased width to accommodate extra column with gap)
    fig, ax = plt.subplots(figsize=(6, 12))

    from matplotlib.colors import Normalize, LinearSegmentedColormap
    from matplotlib.cm import ScalarMappable

    # Green-only color palette (light to dark green)
    cmap = LinearSegmentedColormap.from_list('greens', ['#dcfce7', '#166534'])
    norm = Normalize(vmin=60, vmax=100)

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

    # Build x positions: regular categories, then gap, then "All Metrics"
    x_positions = {}
    for j, cat in enumerate(categories):
        x_positions[cat] = j * cell_width
    # Add gap before "All Metrics"
    x_positions["all_metrics"] = len(categories) * cell_width + all_metrics_gap

    # Draw cells
    for model in models_display_order:
        y_pos = y_positions[model]
        is_5min = "(5min)" in model
        for cat in categories_with_all:
            x_pos = x_positions[cat]
            if model in pivot.index and cat in pivot.columns:
                value = pivot.loc[model, cat]
                if pd.notna(value):
                    if is_5min:
                        # Gray out 5-minute human baseline
                        color = '#d1d5db'
                        text_color = '#6b7280'
                    else:
                        color = cmap(norm(value))
                        text_color = 'white' if value > 75 else 'black'
                    rect = plt.Rectangle((x_pos, y_pos), cell_width, cell_height,
                                          facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2, f"{value:.1f}",
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)

    # Set axis limits (account for gap before All Metrics)
    ax.set_xlim(0, x_positions["all_metrics"] + cell_width)
    ax.set_ylim(0, current_y)

    # Y-axis ticks and labels
    y_ticks = [y_positions[m] + cell_height/2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label(m) for m in models_display_order], fontsize=11)

    # X-axis ticks and labels (with line breaks and renamed categories)
    FIGURE1_CATEGORY_LABELS = {
        "flag_accuracy": "Flag\nAccuracy",
        "claim_support": "Source\nFidelity",
        "source_reliability": "Source\nQuality",
        "work_relevance": "Work\nRelevance",
        "all_metrics": "All\nMetrics",
    }
    x_ticks = [x_positions[cat] + cell_width/2 for cat in categories_with_all]
    ax.set_xticks(x_ticks)

    # Create labels, with "All Metrics" in bold
    x_labels = []
    for cat in categories_with_all:
        x_labels.append(FIGURE1_CATEGORY_LABELS.get(cat, cat))
    ax.set_xticklabels(x_labels, fontsize=11)

    # Bold the "All Metrics" label
    tick_labels = ax.get_xticklabels()
    tick_labels[-1].set_fontweight('bold')

    # Add centered section annotations ABOVE each group
    # Center is midpoint of total width including gap
    total_width = x_positions["all_metrics"] + cell_width
    center_x = total_width / 2

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

    ax.set_title("Pass Rate by Screener and Test Category", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Test Category", fontsize=12, fontweight='bold')
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
    """Main function to generate Figure 1."""
    print("Generating Figure 1: Pass rates heatmap with grouped screeners")
    print("=" * 60)

    # Load data
    df = load_and_filter_data()

    # Create the figure
    fig = create_figure(df)

    # Save the figure
    output_path = Path(__file__).parent.parent.parent / "paper" / "figures" / "figure2_pass_rates_heatmap.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    plt.close()

    print("\n" + "=" * 60)
    print("Caption:")
    print("Pass rates by screener and test category. Screeners are grouped into")
    print("three blocks: AT (All Tools) - AI with full tool access, W (Web-only) -")
    print("AI with web search only, and Human baseline screeners. Color intensity")
    print("indicates pass rate from 50% (red) to 100% (green).")


if __name__ == "__main__":
    main()
