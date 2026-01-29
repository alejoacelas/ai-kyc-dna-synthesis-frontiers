#!/usr/bin/env python3
"""
Generate Error Rate by Flag Criterion Figures.

Generates two plots:
1. Error rates by flag criterion and screener type (grouped bars)
2. Error category breakdown by flag criterion (100% stacked bars)
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Import style from same directory
from style import (
    setup_style, COLORS, FLAG_ORDER, FLAG_LABELS,
)

# Error category display names and colors
ERROR_LABELS = {
    "empty_response": "Empty Response",
    "flag_instructions_not_followed": "Instructions Not Followed",
    "information_not_found": "Information Not Found",
    "difference_in_judgment": "Judgment Difference",
    "factual_mistake": "Factual Mistake",
    None: "Uncategorized",
}

# Error category colors - pastel palette
ERROR_COLORS = {
    "empty_response": "#66c2a5",           # Teal
    "flag_instructions_not_followed": "#fc8d62",  # Orange
    "information_not_found": "#8da0cb",     # Purple
    "difference_in_judgment": "#e78ac3",    # Pink
    "factual_mistake": "#a6d854",           # Green
    None: "#b3b3b3",                        # Gray
}

ERROR_ORDER = [
    "empty_response",
    "flag_instructions_not_followed",
    "information_not_found",
    "difference_in_judgment",
    "factual_mistake",
    None,
]

# Screener type colors (matching Figure 3)
SCREENER_COLORS = {
    "Human": "#f59e0b",      # Amber
    "All Tools": "#1e40af",  # Dark blue
    "Web Only": "#93c5fd",   # Light blue
}


def load_data():
    """Load error comments and test data."""
    # Load error comments
    error_path = Path(__file__).parent.parent.parent / "data" / "annotations" / "flag_error_comments.json"
    with open(error_path) as f:
        error_data = json.load(f)
    df_errors = pd.DataFrame(error_data["records"])

    # Load test data for total counts
    test_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df_tests = pd.read_csv(test_path)

    return df_errors, df_tests


def classify_provider_type(provider):
    """Classify provider into Human, All Tools, or Web Only."""
    if "Human" in provider and "5min" not in provider:
        return "Human"
    elif "Human" in provider and "5min" in provider:
        return None  # Skip 5min human baseline
    elif "(All Tools)" in provider:
        return "All Tools"
    else:
        return "Web Only"


def calculate_error_data(df_errors, df_tests):
    """Calculate error rates and category breakdowns."""
    # Filter out 5-minute human baseline from errors
    df_errors = df_errors[~df_errors["provider"].str.contains("5min", case=False, na=False)].copy()

    # Add screener type
    df_errors["screener_type"] = df_errors["provider"].apply(classify_provider_type)
    df_errors = df_errors[df_errors["screener_type"].notna()]

    # Get flag accuracy tests from test data (for total counts)
    df_flag_tests = df_tests[
        (df_tests["test_category"] == "flag_accuracy") &
        (df_tests["is_human_baseline_dataset"] == True)
    ].copy()

    # Filter out 5min human baseline
    df_flag_tests = df_flag_tests[~df_flag_tests["model_label"].str.contains("5min", case=False, na=False)]

    # Add screener type to tests
    df_flag_tests["screener_type"] = df_flag_tests["model_label"].apply(classify_provider_type)

    # Map metric_name to flag_type
    def metric_to_flag(metric):
        if "AFFILIATION" in metric.upper():
            return "affiliation"
        elif "INSTITUTION" in metric.upper():
            return "institution"
        elif "DOMAIN" in metric.upper():
            return "domain"
        elif "SANCTIONS" in metric.upper():
            return "sanctions"
        return None

    df_flag_tests["flag_type"] = df_flag_tests["metric_name"].apply(metric_to_flag)
    df_flag_tests = df_flag_tests[df_flag_tests["flag_type"].notna()]

    # Calculate total tests per flag type and screener type
    total_counts = df_flag_tests.groupby(["flag_type", "screener_type"]).size().reset_index(name="total")

    # Calculate error counts per flag type, screener type, and error category
    error_counts = df_errors.groupby(
        ["flagType", "screener_type", "errorCategory"]
    ).size().reset_index(name="error_count")
    error_counts = error_counts.rename(columns={"flagType": "flag_type"})

    # Merge to get error rates
    merged = error_counts.merge(total_counts, on=["flag_type", "screener_type"], how="left")
    merged["error_rate"] = merged["error_count"] / merged["total"] * 100

    return merged, df_errors


def create_figure_error_rates(error_data):
    """Create grouped bar chart of error rates by flag criterion and screener type."""
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 6))

    flag_types = FLAG_ORDER
    screener_types = ["Human", "All Tools", "Web Only"]

    n_flags = len(flag_types)
    n_screeners = len(screener_types)
    bar_width = 0.25

    # X positions for each flag type
    x = np.arange(n_flags)

    # Calculate total error rate per flag/screener
    for s_idx, screener in enumerate(screener_types):
        error_rates = []
        for flag in flag_types:
            subset = error_data[
                (error_data["flag_type"] == flag) &
                (error_data["screener_type"] == screener)
            ]
            total_rate = subset["error_rate"].sum()
            error_rates.append(total_rate)

        offset = (s_idx - 1) * bar_width
        bars = ax.bar(
            x + offset,
            error_rates,
            bar_width,
            label=screener if screener != "Human" else "Human baseline",
            color=SCREENER_COLORS[screener],
            alpha=0.85,
            edgecolor="white",
            linewidth=0.5,
        )

        # Add value labels
        for bar, rate in zip(bars, error_rates):
            if rate > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    f"{rate:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

    # Customize axes
    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in flag_types], fontsize=11)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Error Rate (%)", fontsize=12, fontweight="bold")

    # Set y-axis limit
    ax.set_ylim(0, 22)

    # Title
    ax.set_title("Error Rate by Flag Criterion and Screener Type",
                 fontsize=14, fontweight="bold", pad=15)

    # Legend
    ax.legend(loc="upper right", fontsize=10)

    # Grid
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    return fig


def create_figure_error_categories_simple(df_errors):
    """Create 100% stacked bar chart of error categories by screener type only."""
    setup_style()

    fig, ax = plt.subplots(figsize=(8, 6))

    screener_types = ["Human", "All Tools", "Web Only"]
    screener_labels = ["Human\nbaseline", "All Tools", "Web Only"]

    # Get ordered categories present in data
    ordered_cats = [c for c in ERROR_ORDER if c in df_errors["errorCategory"].unique()]

    # Calculate error category breakdown per screener type
    pivot = pd.crosstab(df_errors["screener_type"], df_errors["errorCategory"])

    # Reorder
    pivot = pivot.loc[[s for s in screener_types if s in pivot.index]]
    pivot = pivot[[c for c in ordered_cats if c in pivot.columns]]

    # Convert to percentages (each row sums to 100%)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # X positions
    x = np.arange(len(screener_types))
    bar_width = 0.5

    # Plot stacked bars
    bottom = np.zeros(len(screener_types))
    for cat in ordered_cats:
        if cat in pivot_pct.columns:
            values = pivot_pct[cat].values
            ax.bar(
                x,
                values,
                bar_width,
                bottom=bottom,
                label=ERROR_LABELS.get(cat, str(cat)),
                color=ERROR_COLORS.get(cat, "#6b7280"),
                alpha=0.85,
                edgecolor="white",
                linewidth=0.5,
            )
            bottom += values

    # Customize axes
    ax.set_xticks(x)
    ax.set_xticklabels(screener_labels, fontsize=11)
    ax.set_xlabel("Screener Type", fontsize=12, fontweight="bold")
    ax.set_ylabel("Percentage of Errors (%)", fontsize=12, fontweight="bold")

    # Set y-axis limit
    ax.set_ylim(0, 100)

    # Title
    ax.set_title("Error Category Distribution by Screener Type",
                 fontsize=14, fontweight="bold", pad=15)

    # Legend (outside right)
    from matplotlib.patches import Patch
    error_legend = [
        Patch(facecolor=ERROR_COLORS.get(cat, "#b3b3b3"), label=ERROR_LABELS.get(cat, str(cat)), alpha=0.85)
        for cat in ordered_cats if cat in pivot_pct.columns
    ]
    ax.legend(
        handles=error_legend,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=9,
        title="Error Category",
        title_fontsize=10,
        frameon=True
    )

    # Grid
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    return fig


def create_figure_error_categories_detailed(df_errors):
    """Create 100% stacked bar chart of error categories by flag criterion and screener type (supplementary)."""
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    flag_types = FLAG_ORDER
    screener_types = ["Human", "All Tools", "Web Only"]

    n_flags = len(flag_types)
    n_screeners = len(screener_types)
    bar_width = 0.25

    # X positions for each flag type group
    x = np.arange(n_flags)

    # Get ordered categories present in data
    ordered_cats = [c for c in ERROR_ORDER if c in df_errors["errorCategory"].unique()]

    # For each screener type, create stacked bars
    for s_idx, screener in enumerate(screener_types):
        # Filter data for this screener
        screener_data = df_errors[df_errors["screener_type"] == screener]

        # Calculate error category breakdown per flag type for this screener
        pivot = pd.crosstab(screener_data["flagType"], screener_data["errorCategory"])

        # Reorder and fill missing
        ordered_flags = [f for f in flag_types if f in pivot.index]

        # Create full pivot with all flags (fill missing with 0)
        full_pivot = pd.DataFrame(0, index=flag_types, columns=ordered_cats)
        for f in ordered_flags:
            for c in ordered_cats:
                if c in pivot.columns:
                    full_pivot.loc[f, c] = pivot.loc[f, c] if f in pivot.index else 0

        # Convert to percentages (each row sums to 100%)
        row_sums = full_pivot.sum(axis=1)
        pivot_pct = full_pivot.div(row_sums.replace(0, 1), axis=0) * 100

        # X position offset for this screener
        offset = (s_idx - 1) * bar_width

        # Plot stacked bars for this screener
        bottom = np.zeros(n_flags)
        for cat_idx, cat in enumerate(ordered_cats):
            values = pivot_pct[cat].values

            # Only add label for first screener to avoid duplicate legend entries
            label = ERROR_LABELS.get(cat, str(cat)) if s_idx == 0 else None

            ax.bar(
                x + offset,
                values,
                bar_width,
                bottom=bottom,
                label=label,
                color=ERROR_COLORS.get(cat, "#95a5a6"),
                alpha=0.85,
                edgecolor="white",
                linewidth=0.5,
            )
            bottom += values

    # Add screener type labels above each bar
    for f_idx in range(n_flags):
        for s_idx, screener in enumerate(screener_types):
            offset = (s_idx - 1) * bar_width
            short_label = "H" if screener == "Human" else ("AT" if screener == "All Tools" else "W")
            ax.text(
                x[f_idx] + offset,
                103,
                short_label,
                ha="center",
                va="bottom",
                fontsize=8,
                color=SCREENER_COLORS[screener],
                fontweight="bold",
            )

    # Customize axes
    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in flag_types], fontsize=11)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Percentage of Errors (%)", fontsize=12, fontweight="bold")

    # Set y-axis limit (with space for labels above)
    ax.set_ylim(0, 115)

    # Title
    ax.set_title("Error Category Distribution by Flag Criterion and Screener Type",
                 fontsize=14, fontweight="bold", pad=15)

    # Error category legend (top left)
    from matplotlib.patches import Patch
    error_legend = [
        Patch(facecolor=ERROR_COLORS.get(cat, "#b3b3b3"), label=ERROR_LABELS.get(cat, str(cat)), alpha=0.85)
        for cat in ordered_cats
    ]
    ax.legend(
        handles=error_legend,
        loc="upper left",
        fontsize=9,
        title="Error Category",
        title_fontsize=10,
    )

    # Grid
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    return fig


def main():
    """Main function to generate the figures."""
    print("Generating Error Rate by Flag Criterion Figures")
    print("=" * 60)

    # Load data
    df_errors, df_tests = load_data()
    print(f"Loaded {len(df_errors)} error records and {len(df_tests):,} test records")

    # Calculate error data
    error_data, df_errors_filtered = calculate_error_data(df_errors, df_tests)

    print("\nError rates by flag criterion and screener type:")
    summary = error_data.groupby(["flag_type", "screener_type"])["error_rate"].sum().unstack()
    print(summary.round(1))

    # Create and save Figure 1: Error rates by screener type (main figures)
    fig1 = create_figure_error_rates(error_data)
    output_path1 = Path(__file__).parent.parent.parent / "paper" / "figures" / "figure_error_by_criterion.png"
    fig1.savefig(output_path1, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure 1 saved to: {output_path1}")
    plt.close(fig1)

    # Create and save Figure 2: Simple error category breakdown by screener (main figures)
    fig2 = create_figure_error_categories_simple(df_errors_filtered)
    output_path2 = Path(__file__).parent.parent.parent / "paper" / "figures" / "figure_error_categories_by_screener.png"
    fig2.savefig(output_path2, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure 2 saved to: {output_path2}")
    plt.close(fig2)

    # Create and save Figure 3: Detailed error category breakdown (supplementary)
    fig3 = create_figure_error_categories_detailed(df_errors_filtered)
    output_path3 = Path(__file__).parent.parent.parent / "paper" / "supplementary" / "figure_error_categories_by_criterion.png"
    fig3.savefig(output_path3, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure 3 (supplementary) saved to: {output_path3}")
    plt.close(fig3)

    print("\n" + "=" * 60)
    print("Captions:")
    print("\nFigure 1 (Error rates by criterion):")
    print("Error rates by flag criterion and screener type. Bar colors indicate")
    print("screener type: Human baseline (amber), All Tools (dark blue), Web Only (light blue).")
    print("\nFigure 2 (Error categories by screener):")
    print("Distribution of error categories by screener type. Each bar shows the")
    print("percentage breakdown of errors into categories (summing to 100%).")
    print("\nFigure 3 (Supplementary - Error categories by criterion):")
    print("Detailed distribution of error categories by flag criterion and screener type.")
    print("H = Human baseline, AT = All Tools, W = Web Only.")


if __name__ == "__main__":
    main()
