"""
Exploratory plots for error categories from flag_error_comments.json.

Generates:
- Overall distribution of error categories
- Error categories by provider (AI vs Human)
- Error categories by flag type (task)
"""

import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
from collections import Counter

# Import shared style
from style import setup_style, COLORS, MODEL_LABELS, MODEL_LABELS_NO_TIME, MODEL_ORDER, FLAG_LABELS, FLAG_ORDER

setup_style()

# Paths
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "annotations" / "flag_error_comments.json"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "paper" / "wip"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Error category display names and colors
ERROR_LABELS = {
    "empty_response": "Empty Response",
    "flag_instructions_not_followed": "Instructions Not Followed",
    "information_not_found": "Information Not Found",
    "difference_in_judgment": "Judgment Difference",
    "factual_mistake": "Factual Mistake",
    None: "Uncategorized",
}

ERROR_COLORS = {
    "empty_response": "#e74c3c",           # Red
    "flag_instructions_not_followed": "#f39c12",  # Orange
    "information_not_found": "#3498db",     # Blue
    "difference_in_judgment": "#9b59b6",    # Purple
    "factual_mistake": "#2ecc71",           # Green
    None: "#95a5a6",                        # Gray
}

ERROR_ORDER = [
    "empty_response",
    "flag_instructions_not_followed",
    "information_not_found",
    "difference_in_judgment",
    "factual_mistake",
    None,
]


def load_data():
    """Load and parse the flag error comments JSON."""
    with open(DATA_PATH) as f:
        data = json.load(f)

    records = data["records"]
    df = pd.DataFrame(records)

    # Filter out 5-minute human baseline
    df = df[~df["provider"].str.contains("5min", case=False, na=False)]

    # Parse provider into model type
    df["is_human"] = df["provider"].str.contains("Human", case=False, na=False)
    df["model_type"] = df["provider"].apply(
        lambda x: "Human" if "Human" in x else ("All Tools" if "All Tools" in x else "Web Only")
    )

    return df


def plot_overall_distribution(df):
    """Plot overall distribution of error categories."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Count categories
    counts = df["errorCategory"].value_counts()

    # Reorder
    ordered_cats = [c for c in ERROR_ORDER if c in counts.index]
    counts = counts[ordered_cats]

    # Get colors and labels
    colors = [ERROR_COLORS.get(c, "#95a5a6") for c in ordered_cats]
    labels = [ERROR_LABELS.get(c, str(c)) for c in ordered_cats]

    bars = ax.bar(range(len(counts)), counts.values, color=colors)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Flag Error Categories")

    # Add value labels
    for bar, count in zip(bars, counts.values):
        ax.annotate(
            f"{count}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # Add percentage labels
    total = counts.sum()
    for bar, count in zip(bars, counts.values):
        pct = count / total * 100
        ax.annotate(
            f"({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color="gray",
        )

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "error_categories_overall.png", dpi=300, bbox_inches="tight")
    print(f"Saved: {OUTPUT_DIR / 'error_categories_overall.png'}")
    plt.close()


def plot_by_provider_type(df):
    """Plot error categories grouped by provider type (Human vs AI)."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create pivot table
    pivot = pd.crosstab(df["errorCategory"], df["model_type"])

    # Reorder rows
    ordered_cats = [c for c in ERROR_ORDER if c in pivot.index]
    pivot = pivot.loc[ordered_cats]

    # Calculate percentages within each provider type
    pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100

    # Plot grouped bars
    x = range(len(ordered_cats))
    width = 0.25

    provider_colors = {
        "Human": COLORS["human_baseline"],
        "All Tools": COLORS["all_tools"],
        "Web Only": COLORS["web_only"],
    }

    for i, ptype in enumerate(["Human", "All Tools", "Web Only"]):
        if ptype in pivot_pct.columns:
            offset = (i - 1) * width
            bars = ax.bar(
                [xi + offset for xi in x],
                pivot_pct[ptype],
                width,
                label=ptype,
                color=provider_colors[ptype],
                alpha=0.85,
            )

    ax.set_xticks(x)
    ax.set_xticklabels([ERROR_LABELS.get(c, str(c)) for c in ordered_cats], rotation=30, ha="right")
    ax.set_ylabel("Percentage of Errors (%)")
    ax.set_title("Error Categories by Provider Type")
    ax.legend(title="Provider Type")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "error_categories_by_provider_type.png", dpi=300, bbox_inches="tight")
    print(f"Saved: {OUTPUT_DIR / 'error_categories_by_provider_type.png'}")
    plt.close()


def plot_by_flag_type(df):
    """Plot error categories by flag type (task)."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create pivot table
    pivot = pd.crosstab(df["errorCategory"], df["flagType"])

    # Reorder
    ordered_cats = [c for c in ERROR_ORDER if c in pivot.index]
    ordered_flags = [f for f in FLAG_ORDER if f in pivot.columns]
    pivot = pivot.loc[ordered_cats, ordered_flags]

    # Calculate percentages within each flag type
    pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100

    # Plot stacked bar chart
    bottom = [0] * len(ordered_flags)

    for cat in ordered_cats:
        values = pivot_pct.loc[cat].values
        ax.bar(
            range(len(ordered_flags)),
            values,
            bottom=bottom,
            label=ERROR_LABELS.get(cat, str(cat)),
            color=ERROR_COLORS.get(cat, "#95a5a6"),
        )
        bottom = [b + v for b, v in zip(bottom, values)]

    ax.set_xticks(range(len(ordered_flags)))
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in ordered_flags])
    ax.set_ylabel("Percentage of Errors (%)")
    ax.set_title("Error Categories by Flag Type (Task)")
    ax.legend(title="Error Category", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "error_categories_by_flag_type.png", dpi=300, bbox_inches="tight")
    print(f"Saved: {OUTPUT_DIR / 'error_categories_by_flag_type.png'}")
    plt.close()


def plot_heatmap(df):
    """Plot a heatmap of error categories by provider (counts), styled like figure1."""
    from matplotlib.colors import Normalize, LinearSegmentedColormap
    from matplotlib.cm import ScalarMappable

    # Create pivot table with counts
    pivot = pd.crosstab(df["provider"], df["errorCategory"])

    # Reorder columns
    ordered_cats = [c for c in ERROR_ORDER if c in pivot.columns]
    pivot = pivot[ordered_cats]

    # Group models by type using MODEL_ORDER
    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and "(5min)" not in m and m in pivot.index]

    # Orange color palette (light to dark) for counts
    cmap = LinearSegmentedColormap.from_list('oranges', ['#fef3c7', '#c2410c'])
    max_val = pivot.max().max()
    norm = Normalize(vmin=0, vmax=max_val)

    # Gap size between groups
    gap_size = 0.7
    cell_width = 1.0
    cell_height = 1.0

    # Build y positions: AT at top, then gap, W in middle, then gap, Human at bottom
    y_positions = {}
    annotation_positions = {}
    current_y = 0

    # Human models at bottom (with annotation space above)
    if human_models:
        annotation_positions['human'] = current_y + gap_size / 2
        current_y += gap_size
        for model in human_models:
            y_positions[model] = current_y
            current_y += cell_height

    # W models in middle (with annotation space above)
    if w_models:
        annotation_positions['w'] = current_y + gap_size / 2
        current_y += gap_size
        for model in w_models:
            y_positions[model] = current_y
            current_y += cell_height

    # AT models at top (with annotation space above)
    if at_models:
        annotation_positions['at'] = current_y + gap_size / 2
        current_y += gap_size
        for model in at_models:
            y_positions[model] = current_y
            current_y += cell_height

    # Order for display (bottom to top): Human, W, AT
    models_display_order = human_models + w_models + at_models

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 10))

    # Draw cells
    for model in models_display_order:
        y_pos = y_positions[model]
        for j, cat in enumerate(ordered_cats):
            if model in pivot.index and cat in pivot.columns:
                value = pivot.loc[model, cat]
                if pd.notna(value):
                    color = cmap(norm(value))
                    text_color = 'white' if value > max_val * 0.5 else 'black'
                    rect = plt.Rectangle((j, y_pos), cell_width, cell_height,
                                          facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    ax.text(j + cell_width/2, y_pos + cell_height/2, f"{int(value)}",
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)

    # Set axis limits
    ax.set_xlim(0, len(ordered_cats))
    ax.set_ylim(0, current_y)

    # Y-axis ticks and labels (no time indication for human baseline)
    y_ticks = [y_positions[m] + cell_height/2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([MODEL_LABELS_NO_TIME.get(m, m) for m in models_display_order], fontsize=11)

    # X-axis ticks and labels with line breaks
    ERROR_LABELS_MULTILINE = {
        "empty_response": "Empty\nResponse",
        "flag_instructions_not_followed": "Instructions\nNot Followed",
        "information_not_found": "Information\nNot Found",
        "difference_in_judgment": "Judgment\nDifference",
        "factual_mistake": "Factual\nMistake",
        None: "Uncategorized",
    }
    ax.set_xticks([i + cell_width/2 for i in range(len(ordered_cats))])
    ax.set_xticklabels([ERROR_LABELS_MULTILINE.get(c, str(c)) for c in ordered_cats], fontsize=10)

    # Add centered section annotations ABOVE each group
    center_x = len(ordered_cats) / 2

    if human_models:
        ax.text(center_x, annotation_positions['human'],
                "Human Baseline",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    if w_models:
        ax.text(center_x, annotation_positions['w'],
                "AI - Web Only (W)",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    if at_models:
        ax.text(center_x, annotation_positions['at'],
                "AI - All Tools (AT)",
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='black', style='italic')

    # Add colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Error Count", fontsize=12)

    ax.set_title("Error Category Counts by Provider", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Error Category", fontsize=12, fontweight='bold')
    ax.set_ylabel("Provider", fontsize=12, fontweight='bold')

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "error_categories_heatmap.png", dpi=300, bbox_inches="tight", facecolor='white')
    print(f"Saved: {OUTPUT_DIR / 'error_categories_heatmap.png'}")
    plt.close()


def print_summary(df):
    """Print summary statistics."""
    print("\n=== Error Category Summary ===\n")

    counts = df["errorCategory"].value_counts()
    total = len(df)

    print(f"Total error records: {total}\n")
    print("Category breakdown:")
    for cat in ERROR_ORDER:
        if cat in counts.index:
            count = counts[cat]
            pct = count / total * 100
            label = ERROR_LABELS.get(cat, str(cat))
            print(f"  {label}: {count} ({pct:.1f}%)")

    print("\n--- By Provider Type ---")
    for ptype in ["Human", "All Tools", "Web Only"]:
        subset = df[df["model_type"] == ptype]
        print(f"\n{ptype} ({len(subset)} errors):")
        ptype_counts = subset["errorCategory"].value_counts()
        for cat in ERROR_ORDER:
            if cat in ptype_counts.index:
                count = ptype_counts[cat]
                pct = count / len(subset) * 100
                label = ERROR_LABELS.get(cat, str(cat))
                print(f"  {label}: {count} ({pct:.1f}%)")


def main():
    print("Loading data...")
    df = load_data()

    print_summary(df)

    print("\nGenerating plots...")
    plot_overall_distribution(df)
    plot_by_provider_type(df)
    plot_by_flag_type(df)
    plot_heatmap(df)

    print("\nDone!")


if __name__ == "__main__":
    main()
