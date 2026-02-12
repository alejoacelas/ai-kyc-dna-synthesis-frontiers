#!/usr/bin/env python3
"""
Generate New Plot 4: Token Consumption by Model.

Grouped bar chart showing mean prompt_tokens and completion_tokens
per customer for each AI model.
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

TOKEN_COLORS = {
    "prompt": "#3498db",       # Blue
    "completion": "#f39c12",   # Orange
}


def load_data():
    """Load responses dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def prepare_data(df):
    """Aggregate token counts per model."""
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]

    df_ai = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()

    # Sum tokens across both prompts per customer per model
    cust_tokens = (
        df_ai.groupby(["customer_name", "model_label"])
        .agg({"prompt_tokens": "sum", "completion_tokens": "sum"})
        .reset_index()
    )

    # Mean per model
    model_tokens = (
        cust_tokens.groupby("model_label")
        .agg({"prompt_tokens": "mean", "completion_tokens": "mean"})
    )

    # Keep only models in order
    model_tokens = model_tokens.reindex(
        [m for m in ai_model_order if m in model_tokens.index]
    )

    return model_tokens, ai_model_order


def create_figure(model_tokens):
    """Create the grouped bar chart."""
    setup_style()

    fig, ax = plt.subplots(figsize=(14, 7))

    models = model_tokens.index.tolist()
    x = np.arange(len(models))
    width = 0.35

    bars_prompt = ax.bar(
        x - width / 2,
        model_tokens["prompt_tokens"],
        width,
        label="Prompt Tokens",
        color=TOKEN_COLORS["prompt"],
        alpha=0.85,
    )
    bars_completion = ax.bar(
        x + width / 2,
        model_tokens["completion_tokens"],
        width,
        label="Completion Tokens",
        color=TOKEN_COLORS["completion"],
        alpha=0.85,
    )

    labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)

    ax.set_ylabel("Mean Tokens per Customer", fontsize=12, fontweight="bold")
    ax.set_title(
        "Token Consumption by Model",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Add value labels on bars
    for bar in bars_prompt:
        h = bar.get_height()
        if not np.isnan(h) and h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h,
                f"{h:,.0f}",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=90,
            )
    for bar in bars_completion:
        h = bar.get_height()
        if not np.isnan(h) and h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h,
                f"{h:,.0f}",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=90,
            )

    ax.legend(loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Extra headroom for rotated labels
    ymax = max(model_tokens["prompt_tokens"].max(), model_tokens["completion_tokens"].max())
    ax.set_ylim(0, ymax * 1.25)

    plt.tight_layout()
    return fig


def write_outputs(model_tokens):
    """Write data and caption files."""
    out = model_tokens.copy()
    out.index.name = "Model"
    out["Label"] = [MODEL_LABELS_NO_TIME.get(m, m) for m in out.index]
    out["prompt_tokens"] = out["prompt_tokens"].round(0).astype(int)
    out["completion_tokens"] = out["completion_tokens"].round(0).astype(int)
    out["total_tokens"] = out["prompt_tokens"] + out["completion_tokens"]
    out = out[["Label", "prompt_tokens", "completion_tokens", "total_tokens"]]
    out.columns = ["Label", "Prompt Tokens", "Completion Tokens", "Total Tokens"]

    data_path = output_dir / "new_4_token_consumption_data.txt"
    with open(data_path, "w") as f:
        f.write(out.to_string())
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_4_token_consumption.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Mean prompt and completion token consumption per customer for each AI model "
            "on the 40-profile human baseline subset, summed across both prompts."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 4: Token Consumption")
    print("=" * 60)

    df = load_data()
    model_tokens, _ = prepare_data(df)
    fig = create_figure(model_tokens)

    fig_path = output_dir / "new_4_token_consumption.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(model_tokens)
    print("Done.")


if __name__ == "__main__":
    main()
