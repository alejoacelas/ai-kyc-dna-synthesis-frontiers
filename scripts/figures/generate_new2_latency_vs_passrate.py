#!/usr/bin/env python3
"""
Generate New Plot 2: Latency vs Pass Rate Scatter.

Scatter plot showing mean information gathering time per customer (x)
vs overall pass rate (y) for each AI model configuration.
Uses benchmark latency data.
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
    """Load benchmark latency and tests datasets."""
    base = Path(__file__).parent.parent.parent
    benchmark = pd.read_csv(base / "latency" / "benchmark_results_full.csv")
    benchmark = benchmark[benchmark["error"].isna()].copy()
    tests = pd.read_csv(base / "processed" / "tests.csv")
    print(f"Benchmark: {len(benchmark):,} rows | Tests: {len(tests):,} rows")
    return benchmark, tests


def prepare_data(benchmark, tests):
    """Compute mean latency and pass rate per model."""
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]

    # --- Latency from benchmark: sum both prompts per customer, then mean ---
    # Only include customers with both prompts (no partial errors)
    counts = benchmark.groupby(["customer_name", "model_label"]).size().reset_index(name="n_prompts")
    complete = counts[counts["n_prompts"] == 2][["customer_name", "model_label"]]
    bench_complete = benchmark.merge(complete, on=["customer_name", "model_label"])

    cust_lat = (
        bench_complete.groupby(["customer_name", "model_label"])["wall_clock_ms"]
        .sum()
        .reset_index()
    )
    cust_lat["time_min"] = cust_lat["wall_clock_ms"] / 60000.0
    mean_latency = cust_lat.groupby("model_label")["time_min"].mean()
    mean_latency.name = "mean_time_min"

    # --- Pass rate from tests (40-profile subset, AI only) ---
    tests_ai = tests[
        (tests["is_human_baseline_dataset"] == True)
        & (tests["model_type"] != "human_baseline")
    ].copy()

    pass_rate = tests_ai.groupby("model_label")["pass"].mean() * 100.0
    pass_rate.name = "pass_rate"

    # Combine
    combined = pd.DataFrame({"mean_time_min": mean_latency, "pass_rate": pass_rate})
    combined = combined.loc[combined.index.isin(ai_model_order)].dropna()

    return combined, ai_model_order


def create_figure(combined):
    """Create the scatter plot."""
    setup_style()

    fig, ax = plt.subplots(figsize=(11, 7))

    for model in combined.index:
        x = combined.loc[model, "mean_time_min"]
        y = combined.loc[model, "pass_rate"]
        color = get_model_color(model)
        ax.scatter(x, y, color=color, s=120, zorder=5, edgecolors="white", linewidth=0.8)

        label = MODEL_LABELS_NO_TIME.get(model, model)
        ax.annotate(
            label,
            (x, y),
            textcoords="offset points",
            xytext=(8, 5),
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    ax.set_xlabel("Mean Information Gathering Time per Customer (minutes)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Information Gathering Time vs Pass Rate by Model", fontsize=14, fontweight="bold", pad=15)

    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Legend for model types
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#2ecc71", label="All Tools"),
        Patch(facecolor="#3498db", label="Web Only"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    plt.tight_layout()
    return fig


def write_outputs(combined):
    """Write data and caption files."""
    out = combined.copy()
    out.index.name = "Model"
    out["Label"] = [MODEL_LABELS_NO_TIME.get(m, m) for m in out.index]
    out["mean_time_min"] = out["mean_time_min"].round(2)
    out["pass_rate"] = out["pass_rate"].round(2)
    out = out[["Label", "mean_time_min", "pass_rate"]]
    out.columns = ["Label", "Mean Time (min)", "Pass Rate (%)"]

    data_path = output_dir / "new_2_latency_vs_passrate_data.txt"
    with open(data_path, "w") as f:
        f.write(out.to_string())
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_2_latency_vs_passrate.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Scatter plot of mean information gathering time (wall-clock) per customer "
            "vs overall pass rate for each AI model. Latency data from dedicated benchmark "
            "across 41 customer profiles; pass rates from 40-profile human baseline subset."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 2: Latency vs Pass Rate")
    print("=" * 60)

    benchmark, tests = load_data()
    combined, _ = prepare_data(benchmark, tests)
    fig = create_figure(combined)

    fig_path = output_dir / "new_2_latency_vs_passrate.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(combined)
    print("Done.")


if __name__ == "__main__":
    main()
