#!/usr/bin/env python3
"""
Generate New Plot 5: Response Length vs Pass Rate Scatter.

Scatter plot of mean response_length per customer (x) vs overall pass rate (y)
for each AI model configuration.
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
    """Load responses and tests datasets."""
    base = Path(__file__).parent.parent.parent / "processed"
    responses = pd.read_csv(base / "responses.csv")
    tests = pd.read_csv(base / "tests.csv")
    print(f"Responses: {len(responses):,} rows | Tests: {len(tests):,} rows")
    return responses, tests


def prepare_data(responses, tests):
    """Compute mean response length and pass rate per model."""
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]

    # --- Response length ---
    resp_ai = responses[
        (responses["is_human_baseline_dataset"] == True)
        & (responses["model_type"] != "human_baseline")
    ].copy()

    # Sum response_length across both prompts per customer per model, then mean per model
    cust_len = (
        resp_ai.groupby(["customer_name", "model_label"])["response_length"]
        .sum()
        .reset_index()
    )
    mean_len = cust_len.groupby("model_label")["response_length"].mean()
    mean_len.name = "mean_response_length"

    # --- Pass rate ---
    tests_ai = tests[
        (tests["is_human_baseline_dataset"] == True)
        & (tests["model_type"] != "human_baseline")
    ].copy()

    pass_rate = tests_ai.groupby("model_label")["pass"].mean() * 100.0
    pass_rate.name = "pass_rate"

    # Combine
    combined = pd.DataFrame(
        {"mean_response_length": mean_len, "pass_rate": pass_rate}
    )
    combined = combined.loc[combined.index.isin(ai_model_order)].dropna()

    return combined


def create_figure(combined):
    """Create scatter plot."""
    setup_style()

    fig, ax = plt.subplots(figsize=(11, 7))

    for model in combined.index:
        x = combined.loc[model, "mean_response_length"]
        y = combined.loc[model, "pass_rate"]
        color = get_model_color(model)
        ax.scatter(
            x, y, color=color, s=120, zorder=5, edgecolors="white", linewidth=0.8
        )

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

    ax.set_xlabel(
        "Mean Response Length per Customer (chars)", fontsize=12, fontweight="bold"
    )
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Response Length vs Pass Rate", fontsize=14, fontweight="bold", pad=15
    )

    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

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
    out["mean_response_length"] = out["mean_response_length"].round(0).astype(int)
    out["pass_rate"] = out["pass_rate"].round(2)
    out = out[["Label", "mean_response_length", "pass_rate"]]
    out.columns = ["Label", "Mean Response Length (chars)", "Pass Rate (%)"]

    data_path = output_dir / "new_5_response_length_vs_passrate_data.txt"
    with open(data_path, "w") as f:
        f.write(out.to_string())
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_5_response_length_vs_passrate.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Scatter plot of mean total response length per customer vs overall pass rate "
            "for each AI model on the 40-profile human baseline subset."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 5: Response Length vs Pass Rate")
    print("=" * 60)

    responses, tests = load_data()
    combined = prepare_data(responses, tests)
    fig = create_figure(combined)

    fig_path = output_dir / "new_5_response_length_vs_passrate.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(combined)
    print("Done.")


if __name__ == "__main__":
    main()
