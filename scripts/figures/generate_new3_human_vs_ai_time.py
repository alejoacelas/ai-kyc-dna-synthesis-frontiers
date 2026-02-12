#!/usr/bin/env python3
"""
Generate New Plot 3: Human vs AI Information Gathering Time.

Horizontal bar chart comparing human time_to_complete_minutes (from responses.csv)
and AI wall-clock time (from benchmark data, converted to minutes) per customer.
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
    """Load responses (for human times) and benchmark (for AI times)."""
    base = Path(__file__).parent.parent.parent
    responses = pd.read_csv(base / "processed" / "responses.csv")
    benchmark = pd.read_csv(base / "latency" / "benchmark_results_full.csv")
    benchmark = benchmark[benchmark["error"].isna()].copy()
    print(f"Responses: {len(responses):,} rows | Benchmark: {len(benchmark):,} rows")
    return responses, benchmark


def prepare_data(responses, benchmark):
    """Compute mean time per customer for all models."""
    results = {}

    # --- Human baselines: use time_to_complete_minutes from responses ---
    df_human = responses[
        (responses["is_human_baseline_dataset"] == True)
        & (responses["model_type"] == "human_baseline")
    ].copy()
    human_cust = (
        df_human.groupby(["customer_name", "model_label"])["time_to_complete_minutes"]
        .sum()
        .reset_index()
    )
    human_mean = human_cust.groupby("model_label")["time_to_complete_minutes"].mean()
    for model, val in human_mean.items():
        results[model] = val

    # --- AI models: use wall_clock_ms from benchmark ---
    # Only include customers with both prompts (no partial errors)
    counts = benchmark.groupby(["customer_name", "model_label"]).size().reset_index(name="n_prompts")
    complete = counts[counts["n_prompts"] == 2][["customer_name", "model_label"]]
    bench_complete = benchmark.merge(complete, on=["customer_name", "model_label"])

    cust_bench = (
        bench_complete.groupby(["customer_name", "model_label"])["wall_clock_ms"]
        .sum()
        .reset_index()
    )
    cust_bench["time_minutes"] = cust_bench["wall_clock_ms"] / 60000.0
    ai_mean = cust_bench.groupby("model_label")["time_minutes"].mean()
    for model, val in ai_mean.items():
        results[model] = val

    # Order by MODEL_ORDER
    ordered = []
    for model in MODEL_ORDER:
        if model in results:
            ordered.append({"model_label": model, "time_minutes": results[model]})

    return pd.DataFrame(ordered)


def create_figure(data):
    """Create horizontal bar chart."""
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 7))

    y_pos = np.arange(len(data))
    colors = [get_model_color(m) for m in data["model_label"]]
    labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in data["model_label"]]

    bars = ax.barh(y_pos, data["time_minutes"], color=colors, alpha=0.85, height=0.6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()

    ax.set_xlabel("Time per Customer (minutes)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Human vs AI Screening Time per Customer",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Add value labels at end of bars
    for bar, val in zip(bars, data["time_minutes"]):
        ax.text(
            bar.get_width() + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f} min",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # Extend x-axis for labels
    ax.set_xlim(0, data["time_minutes"].max() * 1.2)

    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#2ecc71", alpha=0.85, label="All Tools"),
        Patch(facecolor="#3498db", alpha=0.85, label="Web Only"),
        Patch(facecolor="#e74c3c", alpha=0.85, label="Human Baseline"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    plt.tight_layout()
    return fig


def write_outputs(data):
    """Write data and caption files."""
    out = data.copy()
    out["Label"] = [MODEL_LABELS_NO_TIME.get(m, m) for m in out["model_label"]]
    out["time_minutes"] = out["time_minutes"].round(2)
    out = out[["Label", "time_minutes"]]
    out.columns = ["Model", "Time per Customer (min)"]

    data_path = output_dir / "new_3_human_vs_ai_time_data.txt"
    with open(data_path, "w") as f:
        f.write(out.to_string(index=False))
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_3_human_vs_ai_time.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Comparison of screening time per customer: human baseline "
            "(time_to_complete_minutes from evaluation data) vs AI models "
            "(wall-clock information gathering time from dedicated latency benchmark). "
            "Human time includes both information gathering and review; AI time is "
            "information gathering only."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 3: Human vs AI Time Comparison")
    print("=" * 60)

    responses, benchmark = load_data()
    data = prepare_data(responses, benchmark)
    fig = create_figure(data)

    fig_path = output_dir / "new_3_human_vs_ai_time.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(data)
    print("Done.")


if __name__ == "__main__":
    main()
