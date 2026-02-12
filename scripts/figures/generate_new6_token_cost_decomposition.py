#!/usr/bin/env python3
"""
Generate New Plot 6: Token Cost Decomposition.

Stacked bar chart showing input token cost, output token cost,
and web search cost per customer for each AI model.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
    setup_style,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)

COST_COLORS = {
    "input": "#6366f1",     # Indigo
    "output": "#e74c3c",    # Coral
    "web_search": "#14b8a6",  # Teal
}

# Pricing per million tokens, from data/token_pricing.yaml
TOKEN_PRICING = {
    "claude": {"input": 3.00, "output": 15.00},
    "minimax": {"input": 0.30, "output": 1.20},
    "zhipu": {"input": 0.60, "output": 2.20},
    "gemini": {"input": 1.25, "output": 10.00},
    "grok": {"input": 3.00, "output": 15.00},
}


def load_data():
    """Load responses dataset."""
    base = Path(__file__).parent.parent.parent
    data_path = base / "processed" / "responses.csv"

    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    return df


def map_pricing(model_name):
    """Map model_name to (input_price_per_million, output_price_per_million)."""
    if pd.isna(model_name):
        return (0.0, 0.0)

    mn = model_name.lower()
    if "claude" in mn:
        p = TOKEN_PRICING["claude"]
    elif "minimax" in mn:
        p = TOKEN_PRICING["minimax"]
    elif "glm" in mn or "zhipu" in mn:
        p = TOKEN_PRICING["zhipu"]
    elif "gemini" in mn:
        p = TOKEN_PRICING["gemini"]
    elif "grok" in mn:
        p = TOKEN_PRICING["grok"]
    else:
        return (0.0, 0.0)

    return (p["input"], p["output"])


def prepare_data(df):
    """Compute mean cost components per model."""
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]

    df_ai = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()

    # Compute per-row input and output token costs
    price_tuples = df_ai["model_name"].apply(map_pricing)
    df_ai["input_price"] = price_tuples.apply(lambda t: t[0])
    df_ai["output_price"] = price_tuples.apply(lambda t: t[1])

    df_ai["input_cost"] = df_ai["prompt_tokens"].fillna(0) * df_ai["input_price"] / 1_000_000
    df_ai["output_cost"] = df_ai["completion_tokens"].fillna(0) * df_ai["output_price"] / 1_000_000

    # Sum per customer per model
    cust_costs = (
        df_ai.groupby(["customer_name", "model_label"])
        .agg({
            "input_cost": "sum",
            "output_cost": "sum",
            "web_search_cost": "sum",
        })
        .reset_index()
    )

    # Mean per model
    model_costs = cust_costs.groupby("model_label").agg({
        "input_cost": "mean",
        "output_cost": "mean",
        "web_search_cost": "mean",
    })

    # Order
    model_costs = model_costs.reindex(
        [m for m in ai_model_order if m in model_costs.index]
    )

    # Total for sorting/labels
    model_costs["total_cost"] = (
        model_costs["input_cost"]
        + model_costs["output_cost"]
        + model_costs["web_search_cost"]
    )

    return model_costs


def create_figure(model_costs):
    """Create stacked bar chart."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    models = model_costs.index.tolist()
    x = np.arange(len(models))
    width = 0.65

    input_vals = model_costs["input_cost"].values
    output_vals = model_costs["output_cost"].values
    web_vals = model_costs["web_search_cost"].values

    ax.bar(
        x, input_vals, width,
        label="Input Token Cost",
        color=COST_COLORS["input"],
        alpha=0.9,
    )
    ax.bar(
        x, output_vals, width,
        bottom=input_vals,
        label="Output Token Cost",
        color=COST_COLORS["output"],
        alpha=0.9,
    )
    ax.bar(
        x, web_vals, width,
        bottom=input_vals + output_vals,
        label="Web Search Cost",
        color=COST_COLORS["web_search"],
        alpha=0.9,
    )

    # Total labels on top
    for i, total in enumerate(model_costs["total_cost"]):
        ax.text(
            i, total + 0.002, f"${total:.3f}",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)

    ax.set_ylabel("Cost per Customer (USD)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Token Cost Decomposition by Model",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    max_total = model_costs["total_cost"].max()
    ax.set_ylim(0, max_total * 1.15)

    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def write_outputs(model_costs):
    """Write data and caption files."""
    out = model_costs.copy()
    out.index.name = "Model"
    out["Label"] = [MODEL_LABELS_NO_TIME.get(m, m) for m in out.index]
    for col in ["input_cost", "output_cost", "web_search_cost", "total_cost"]:
        out[col] = out[col].round(4)
    out = out[["Label", "input_cost", "output_cost", "web_search_cost", "total_cost"]]
    out.columns = [
        "Label",
        "Input Token Cost ($)",
        "Output Token Cost ($)",
        "Web Search Cost ($)",
        "Total Cost ($)",
    ]

    data_path = output_dir / "new_6_token_cost_decomposition_data.txt"
    with open(data_path, "w") as f:
        f.write(out.to_string())
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_6_token_cost_decomposition.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Token cost decomposition per customer for each AI model: input token cost (indigo), "
            "output token cost (coral), and web search cost (teal) on the 40-profile human baseline subset."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 6: Token Cost Decomposition")
    print("=" * 60)

    df = load_data()
    model_costs = prepare_data(df)
    fig = create_figure(model_costs)

    fig_path = output_dir / "new_6_token_cost_decomposition.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(model_costs)
    print("Done.")


if __name__ == "__main__":
    main()
