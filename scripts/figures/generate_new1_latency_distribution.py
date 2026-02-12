#!/usr/bin/env python3
"""
Generate New Plot 1: Latency Distribution by Model.

Boxplot of total wall-clock time per customer (summed across both prompts)
for each AI model, colored by model type. Uses benchmark latency data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
    setup_style,
    get_model_color,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load benchmark latency dataset."""
    data_path = Path(__file__).parent.parent.parent / "latency" / "benchmark_results_full.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    # Drop rows with errors
    df = df[df["error"].isna()].copy()
    print(f"Total rows (no errors): {len(df):,}")
    return df


def prepare_data(df):
    """Aggregate wall-clock time per customer per model."""
    # Only include customers that have both prompts (no partial errors)
    counts = df.groupby(["customer_name", "model_label"]).size().reset_index(name="n_prompts")
    complete = counts[counts["n_prompts"] == 2][["customer_name", "model_label"]]
    df_complete = df.merge(complete, on=["customer_name", "model_label"])

    # Sum wall_clock_ms across both prompts per customer per model
    customer_latency = (
        df_complete.groupby(["customer_name", "model_label"])["wall_clock_ms"]
        .sum()
        .reset_index()
    )

    # Convert to minutes
    customer_latency["time_min"] = customer_latency["wall_clock_ms"] / 60000.0

    # Keep only models in MODEL_ORDER (AI only)
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    customer_latency = customer_latency[
        customer_latency["model_label"].isin(ai_model_order)
    ]

    return customer_latency, ai_model_order


def create_figure(customer_latency, ai_model_order):
    """Create the boxplot figure."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    # Prepare data for boxplot in model order
    box_data = []
    labels = []
    colors = []
    for model in ai_model_order:
        vals = customer_latency.loc[
            customer_latency["model_label"] == model, "time_min"
        ].dropna()
        if len(vals) > 0:
            box_data.append(vals.values)
            labels.append(MODEL_LABELS_NO_TIME.get(model, model))
            colors.append(get_model_color(model))

    bp = ax.boxplot(
        box_data,
        patch_artist=True,
        widths=0.6,
        medianprops=dict(color="black", linewidth=1.5),
        whiskerprops=dict(color="gray"),
        capprops=dict(color="gray"),
        flierprops=dict(marker="o", markersize=4, alpha=0.5),
    )

    # Color each box
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("Information Gathering Time per Customer (minutes)", fontsize=12, fontweight="bold")
    ax.set_title("Wall-Clock Latency Distribution by Model", fontsize=14, fontweight="bold", pad=15)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Legend for model types
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#2ecc71", alpha=0.8, label="All Tools"),
        Patch(facecolor="#3498db", alpha=0.8, label="Web Only"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()
    return fig


def write_outputs(customer_latency, ai_model_order):
    """Write data and caption files."""
    rows = []
    for model in ai_model_order:
        vals = customer_latency.loc[
            customer_latency["model_label"] == model, "time_min"
        ].dropna()
        if len(vals) > 0:
            rows.append(
                {
                    "Model": MODEL_LABELS_NO_TIME.get(model, model),
                    "N": len(vals),
                    "Mean (min)": f"{vals.mean():.2f}",
                    "Median (min)": f"{vals.median():.2f}",
                    "Min (min)": f"{vals.min():.2f}",
                    "Max (min)": f"{vals.max():.2f}",
                    "Std (min)": f"{vals.std():.2f}",
                }
            )
    stats_df = pd.DataFrame(rows)

    data_path = output_dir / "new_1_latency_distribution_data.txt"
    with open(data_path, "w") as f:
        f.write(stats_df.to_string(index=False))
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_1_latency_distribution.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Distribution of information gathering time (wall-clock) per customer "
            "(summed across both prompts) for each AI model, colored by model type. "
            "Data from dedicated latency benchmark across 41 customer profiles."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 1: Latency Distribution")
    print("=" * 60)

    df = load_data()
    customer_latency, ai_model_order = prepare_data(df)
    fig = create_figure(customer_latency, ai_model_order)

    fig_path = output_dir / "new_1_latency_distribution.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(customer_latency, ai_model_order)
    print("Done.")


if __name__ == "__main__":
    main()
