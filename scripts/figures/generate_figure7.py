#!/usr/bin/env python3
"""
Generate Figure 7: Cost vs Performance scatter plot.

Shows the trade-off between screening cost per customer and overall pass rate.
Color coded by model configuration type (web-only, all-tools).

Generates two versions:
- Full dataset (134 profiles)
- Human baseline subset (40 profiles)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Import style from same directory
from style import MODEL_ORDER, shorten_model_label, setup_style

# Human review cost per screening (flat rate)
HUMAN_REVIEW_COST = 1.08

# Custom colors matching Figure 3 palette
FIGURE_COLORS = {
    'all_tools': '#1e40af',      # Dark blue for AI with all tools
    'web_only': '#93c5fd',       # Light blue for AI web-only
    'human_baseline': '#f59e0b', # Amber/orange for human
}


def get_figure_color(model_label):
    """Get color based on model label."""
    if "(All Tools)" in model_label:
        return FIGURE_COLORS['all_tools']
    elif "(Web)" in model_label:
        return FIGURE_COLORS['web_only']
    else:
        return FIGURE_COLORS['human_baseline']


def load_data():
    """Load the responses dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def create_figure(df, use_human_baseline_subset=False):
    """Create the cost vs performance scatter plot.

    Args:
        df: DataFrame with responses data
        use_human_baseline_subset: If True, filter to 40-profile subset only
    """
    setup_style()

    # Filter AI models only
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Optionally filter to human baseline subset
    if use_human_baseline_subset:
        df_ai = df_ai[df_ai["is_human_baseline_dataset"] == True]
        dataset_label = "Human Baseline Subset (40 profiles)"
    else:
        dataset_label = "Full Dataset (134 profiles)"

    print(f"\nUsing: {dataset_label}")
    print(f"Filtered rows: {len(df_ai):,}")

    # Sum costs across both prompts (main + background_work) per customer per model
    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg({
        "model_cost": "sum",
        "web_search_cost": "sum",
        "num_assertions_passed": "sum",
        "num_assertions": "sum",
    }).reset_index()

    # Calculate total AI cost per customer (NO human review cost)
    customer_costs["ai_cost"] = customer_costs["model_cost"] + customer_costs["web_search_cost"]

    # Now calculate average cost per customer for each model
    agg = customer_costs.groupby("model_label").agg({
        "ai_cost": "mean",
        "num_assertions_passed": "sum",
        "num_assertions": "sum",
    })

    agg["pass_rate"] = agg["num_assertions_passed"] / agg["num_assertions"] * 100

    # Reorder
    models = [m for m in MODEL_ORDER if m in agg.index]
    agg = agg.loc[models]

    print("\nCost and pass rate by model (AI cost only, no human review):")
    for model in models:
        print(f"  {shorten_model_label(model)}: ${agg.loc[model, 'ai_cost']:.3f}, {agg.loc[model, 'pass_rate']:.1f}%")

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot with Figure 3 colors
    colors = [get_figure_color(m) for m in models]
    ax.scatter(
        agg["ai_cost"],
        agg["pass_rate"],
        c=colors,
        s=150,
        edgecolors="white",
        linewidth=1.5,
        alpha=0.8,
    )

    # Add labels
    for model in models:
        ax.annotate(
            shorten_model_label(model),
            (agg.loc[model, "ai_cost"], agg.loc[model, "pass_rate"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    # Calculate R² coefficient
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        agg["ai_cost"], agg["pass_rate"]
    )
    r_squared = r_value ** 2
    print(f"\nR² = {r_squared:.3f} (p = {p_value:.3f})")

    # Customize axes
    ax.set_xlabel("Average AI Screening Cost per Customer (USD)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")

    # Simple title without dataset info
    ax.set_title("AI Screening Cost vs Overall Pass Rate", fontsize=12, fontweight="bold")

    # Set axis limits: x starts at 0, y starts at 82
    x_max = agg["ai_cost"].max() * 1.15
    ax.set_xlim(0, x_max)
    ax.set_ylim(82, 92)

    # Add axis break indicator on y-axis (double slash style)
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False, linewidth=1.5)

    # Draw two parallel diagonal lines to indicate axis break
    d = 0.012  # Width
    h = 0.02   # Height
    y_base = 0.01
    gap = 0.008  # Gap between the two lines

    # First slash
    ax.plot([-d, d], [y_base, y_base + h], **kwargs)
    # Second slash (offset)
    ax.plot([-d, d], [y_base + gap, y_base + h + gap], **kwargs)

    # Add "0" annotation at corner to indicate y-axis cutoff
    ax.annotate(
        "0",
        xy=(0, 82),
        xytext=(-0.03, -0.06),
        textcoords="axes fraction",
        fontsize=10,
        ha="center",
        va="top",
    )

    # Add R² annotation in top right corner
    ax.annotate(
        f"$R^2$ = {r_squared:.3f}",
        xy=(0.95, 0.95),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
    )

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=FIGURE_COLORS["web_only"], label="Web Only"),
        Patch(facecolor=FIGURE_COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    # Add grid
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()

    return fig


def main():
    """Main function to generate both versions of Figure 7."""
    print("Generating Figure 7: Cost vs Performance scatter plots")
    print("=" * 60)

    # Load data
    df = load_data()

    # Output directories
    figures_dir = Path(__file__).parent.parent.parent / "paper" / "figures"
    supplementary_dir = Path(__file__).parent.parent.parent / "paper" / "supplementary"

    # Generate full dataset version (supplementary)
    print("\n" + "-" * 60)
    print("Creating FULL DATASET version...")
    fig_full = create_figure(df, use_human_baseline_subset=False)
    output_path_full = supplementary_dir / "figure7_cost_vs_performance_full.png"
    fig_full.savefig(output_path_full, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved to: {output_path_full}")
    plt.close()

    # Generate human baseline subset version (main figures)
    print("\n" + "-" * 60)
    print("Creating HUMAN BASELINE SUBSET version...")
    fig_hbs = create_figure(df, use_human_baseline_subset=True)
    output_path_hbs = figures_dir / "figure7_cost_vs_performance.png"
    fig_hbs.savefig(output_path_hbs, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved to: {output_path_hbs}")
    plt.close()

    print("\n" + "=" * 60)
    print("Caption:")
    print("AI screening cost vs overall pass rate. Cost includes:")
    print("  - AI token costs (model inference)")
    print("  - Web search costs ($0.08/query)")
    print("Does NOT include human review cost.")
    print("Both prompts (main + background_work) summed per customer.")
    print("Y-axis starts at 82% (break indicated at origin).")
    print("Color coding: light blue = web-only, dark blue = all-tools.")


if __name__ == "__main__":
    main()
