#!/usr/bin/env python3
"""
Generate Cost Breakdown Figure: Stacked bar chart showing cost components by model.

Shows cost breakdown for all 10 AI models with three components:
- AI tokens cost (model inference cost)
- Web search cost
- Human review cost ($1.08 flat rate)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Import style from same directory
from style import MODEL_ORDER, MODEL_LABELS_NO_TIME, setup_style

# Human review cost per screening (flat rate)
HUMAN_REVIEW_COST = 1.08

# Colors for cost components
COST_COLORS = {
    "ai_tokens": "#6366f1",     # Indigo/purple for AI inference
    "web_search": "#14b8a6",    # Teal for web search
    "human_review": "#f59e0b",  # Amber for human review (kept as requested)
}


def load_data():
    """Load the responses dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def calculate_costs(df):
    """Calculate average cost per customer for each model."""
    # Filter AI models only
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Sum costs across both prompts (main + background_work) per customer per model
    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg({
        "model_cost": "sum",
        "web_search_cost": "sum",
    }).reset_index()

    # Calculate average cost per customer for each model
    model_costs = customer_costs.groupby("model_label").agg({
        "model_cost": "mean",
        "web_search_cost": "mean",
    })

    # Add human review cost (flat rate per screening)
    model_costs["human_review_cost"] = HUMAN_REVIEW_COST

    # Calculate total cost and sort by descending total cost
    model_costs["total_cost"] = (
        model_costs["model_cost"] +
        model_costs["web_search_cost"] +
        model_costs["human_review_cost"]
    )
    model_costs = model_costs.sort_values("total_cost", ascending=False)

    print("\nCost breakdown by model:")
    for model in model_costs.index:
        ai = model_costs.loc[model, "model_cost"]
        web = model_costs.loc[model, "web_search_cost"]
        human = model_costs.loc[model, "human_review_cost"]
        total = ai + web + human
        print(f"  {MODEL_LABELS_NO_TIME.get(model, model)}: "
              f"AI=${ai:.3f}, Web=${web:.3f}, Human=${human:.2f}, Total=${total:.2f}")

    return model_costs


def create_figure(model_costs):
    """Create the stacked bar chart."""
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 7))

    models = model_costs.index.tolist()
    x = np.arange(len(models))
    width = 0.7

    # Create stacked bars
    ai_costs = model_costs["model_cost"].values
    web_costs = model_costs["web_search_cost"].values
    human_costs = model_costs["human_review_cost"].values

    # Stack: Human review at base, AI tokens in middle, web search on top
    bars_human = ax.bar(x, human_costs, width,
                        label="Human review cost",
                        color=COST_COLORS["human_review"],
                        alpha=0.9)

    bars_ai = ax.bar(x, ai_costs, width,
                     bottom=human_costs,
                     label="AI tokens cost",
                     color=COST_COLORS["ai_tokens"],
                     alpha=0.9)

    bars_web = ax.bar(x, web_costs, width,
                      bottom=human_costs + ai_costs,
                      label="Web search cost",
                      color=COST_COLORS["web_search"],
                      alpha=0.9)

    # Customize x-axis
    ax.set_xticks(x)
    short_labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)

    # Customize y-axis
    ax.set_ylabel("Cost per Customer (USD)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")

    # Add total cost labels on top of bars
    for i, (ai, web, human) in enumerate(zip(ai_costs, web_costs, human_costs)):
        total = ai + web + human
        ax.text(i, total + 0.02, f"${total:.2f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Set y-axis limit to accommodate labels
    max_total = max(ai_costs + web_costs + human_costs)
    ax.set_ylim(0, max_total * 1.12)

    # Add title
    ax.set_title("Screening Cost Breakdown by Model",
                 fontsize=14, fontweight="bold", pad=15)

    # Add legend
    ax.legend(loc="upper right", fontsize=10)

    # Add grid for readability
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    return fig


def main():
    """Main function to generate the cost breakdown figure."""
    print("Generating Cost Breakdown Figure: Stacked bar chart")
    print("=" * 60)

    # Load data
    df = load_data()

    # Calculate costs
    model_costs = calculate_costs(df)

    # Create the figure
    fig = create_figure(model_costs)

    # Save the figure
    output_path = Path(__file__).parent.parent.parent / "paper" / "figures" / "figure_cost_breakdown.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure saved to: {output_path}")

    plt.close()

    print("\n" + "=" * 60)
    print("Caption:")
    print("Cost breakdown per customer screening by model, ordered by total cost.")
    print("Each bar shows three components: human review (amber, at base),")
    print("AI token costs (indigo), and web search costs (teal).")
    print(f"Human review is a fixed ${HUMAN_REVIEW_COST:.2f} per screening.")


if __name__ == "__main__":
    main()
