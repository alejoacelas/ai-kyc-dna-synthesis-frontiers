#!/usr/bin/env python3
"""
Generate New Plot 8: Sources vs Pass Rate Scatter.

Scatter plot showing the relationship between mean total sources per customer (x)
and overall pass rate (y) for each AI model, using the human baseline subset.
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
    shorten_model_label_no_time,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def load_data():
    """Load responses and tests datasets."""
    base = Path(__file__).parent.parent.parent / "processed"
    responses = pd.read_csv(base / "responses.csv")
    tests = pd.read_csv(base / "tests.csv")
    print(f"Responses: {len(responses):,} rows")
    print(f"Tests: {len(tests):,} rows")
    return responses, tests


def compute_metrics(responses, tests):
    """Compute mean sources and pass rate per model."""
    # Filter: human baseline dataset, AI models only
    resp_ai = responses[
        (responses["is_human_baseline_dataset"] == True)
        & (responses["model_type"] != "human_baseline")
    ].copy()
    test_ai = tests[
        (tests["is_human_baseline_dataset"] == True)
        & (tests["model_type"] != "human_baseline")
    ].copy()

    resp_ai["num_sources"] = resp_ai["num_sources"].fillna(0)

    # Sources: sum per customer per model (across both prompts), then mean per model
    customer_sources = (
        resp_ai.groupby(["customer_name", "model_label"])["num_sources"]
        .sum()
        .reset_index()
    )
    mean_sources = customer_sources.groupby("model_label")["num_sources"].mean()

    # Pass rate: mean of pass column per model, as percentage
    pass_rate = test_ai.groupby("model_label")["pass"].mean() * 100

    # Combine into a DataFrame
    metrics = pd.DataFrame(
        {"mean_sources": mean_sources, "pass_rate": pass_rate}
    ).dropna()

    # Order by MODEL_ORDER (AI only)
    ai_order = [m for m in MODEL_ORDER if m in metrics.index]
    metrics = metrics.loc[ai_order]

    print("\nModel metrics (sources vs pass rate):")
    for model in metrics.index:
        s = metrics.loc[model, "mean_sources"]
        p = metrics.loc[model, "pass_rate"]
        print(f"  {shorten_model_label_no_time(model)}: {s:.1f} sources, {p:.1f}% pass rate")

    return metrics


def create_figure(metrics):
    """Create scatter plot of sources vs pass rate."""
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 7))

    for model in metrics.index:
        x = metrics.loc[model, "mean_sources"]
        y = metrics.loc[model, "pass_rate"]
        color = get_model_color(model)
        label = shorten_model_label_no_time(model)

        ax.scatter(x, y, s=120, c=color, edgecolors="white", linewidths=1.0, zorder=3)

        # Text label with slight offset to avoid overlap
        ax.annotate(
            label,
            (x, y),
            textcoords="offset points",
            xytext=(8, 6),
            fontsize=9,
            ha="left",
            va="bottom",
        )

    # Axis labels
    ax.set_xlabel("Mean Total Sources per Customer", fontsize=12, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=12, fontweight="bold")

    # Title
    ax.set_title(
        "Sources Used vs Overall Pass Rate by Model",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Grid
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add some padding to axes
    x_range = metrics["mean_sources"].max() - metrics["mean_sources"].min()
    y_range = metrics["pass_rate"].max() - metrics["pass_rate"].min()
    ax.set_xlim(
        metrics["mean_sources"].min() - x_range * 0.15,
        metrics["mean_sources"].max() + x_range * 0.25,
    )
    ax.set_ylim(
        metrics["pass_rate"].min() - y_range * 0.1,
        metrics["pass_rate"].max() + y_range * 0.1,
    )

    plt.tight_layout()
    return fig


def save_outputs(metrics):
    """Save data and caption files."""
    # Data file
    data_path = output_dir / "new_8_sources_vs_passrate_data.txt"
    with open(data_path, "w") as f:
        f.write("Mean Total Sources per Customer vs Overall Pass Rate by Model\n")
        f.write("(Human Baseline Subset, AI Models Only)\n")
        f.write("=" * 70 + "\n\n")
        display = metrics.copy()
        display.index = [shorten_model_label_no_time(m) for m in display.index]
        display.columns = ["Mean Sources", "Pass Rate (%)"]
        f.write(display.round(2).to_string())
        f.write("\n")
    print(f"Data saved to: {data_path}")

    # Caption file
    caption_path = output_dir / "new_8_sources_vs_passrate.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Scatter plot of mean total sources per customer vs overall pass rate "
            "for each AI model on the 40-profile human baseline subset."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 8: Sources vs Pass Rate Scatter")
    print("=" * 60)

    responses, tests = load_data()
    metrics = compute_metrics(responses, tests)

    fig = create_figure(metrics)

    fig_path = output_dir / "new_8_sources_vs_passrate.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure saved to: {fig_path}")

    plt.close()

    save_outputs(metrics)

    print("\nDone.")


if __name__ == "__main__":
    main()
