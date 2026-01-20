#!/usr/bin/env python3
"""
Generate Figure 7: Cost vs Performance scatter plot.

Shows the trade-off between screening cost per customer and overall pass rate.
Color coded by model configuration type (web-only, all-tools).
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add plots directory to path for style imports
sys.path.append(str(Path(__file__).parent / "plots"))
from style import MODEL_ORDER, shorten_model_label, setup_style


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
    data_path = Path(__file__).parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def create_figure(df):
    """Create the cost vs performance scatter plot."""
    setup_style()

    # Filter AI models only
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Sum costs across both prompts (main + background_work) per customer per model
    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg({
        "total_cost": "sum",  # Sum both prompt costs per customer
        "num_assertions_passed": "sum",
        "num_assertions": "sum",
    }).reset_index()

    # Now calculate average cost per customer for each model
    agg = customer_costs.groupby("model_label").agg({
        "total_cost": "mean",  # Average across customers
        "num_assertions_passed": "sum",
        "num_assertions": "sum",
    })
    agg["pass_rate"] = agg["num_assertions_passed"] / agg["num_assertions"] * 100

    # Reorder
    models = [m for m in MODEL_ORDER if m in agg.index]
    agg = agg.loc[models]

    print("\nCost and pass rate by model:")
    for model in models:
        print(f"  {shorten_model_label(model)}: ${agg.loc[model, 'total_cost']:.3f}, {agg.loc[model, 'pass_rate']:.1f}%")

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot with Figure 3 colors
    colors = [get_figure_color(m) for m in models]
    ax.scatter(
        agg["total_cost"],
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
            (agg.loc[model, "total_cost"], agg.loc[model, "pass_rate"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    # Calculate R² coefficient
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        agg["total_cost"], agg["pass_rate"]
    )
    r_squared = r_value ** 2
    print(f"\nR² = {r_squared:.3f} (p = {p_value:.3f})")

    # Customize
    ax.set_xlabel("Average Screening Cost per Customer (USD)")
    ax.set_ylabel("Overall Pass Rate (%)")
    ax.set_title("Screening Cost vs Overall Pass Rate")

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

    plt.tight_layout()

    return fig


def main():
    """Main function to generate Figure 7."""
    print("Generating Figure 7: Cost vs Performance scatter plot")
    print("=" * 60)

    # Load data
    df = load_data()

    # Create the figure
    fig = create_figure(df)

    # Save the figure
    output_path = Path(__file__).parent / "paper" / "figures" / "figure7_cost_vs_performance.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    # Also save a copy in the plots directory
    plots_path = Path(__file__).parent / "plots" / "figures" / "figure7_cost_vs_performance.png"
    plots_path.parent.mkdir(exist_ok=True)
    fig.savefig(plots_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Copy saved to: {plots_path}")

    plt.close()

    print("\n" + "=" * 60)
    print("Caption:")
    print("Screening cost vs overall pass rate. Cost represents the average")
    print("total cost per customer (sum of main and background work prompts).")
    print("Color coding shows model configuration: light blue for web-only,")
    print("dark blue for all-tools.")


if __name__ == "__main__":
    main()
