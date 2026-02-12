#!/usr/bin/env python3
"""
Generate New Plot 7: Source Type Composition by Model.

Stacked bar chart showing the average number of sources by type
(web, EPMC, ORCID, screen) per customer for each AI model.
Data is from the human baseline subset, summed across both prompts per customer.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
    COLORS,
    setup_style,
    shorten_model_label_no_time,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def load_data():
    """Load responses dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def compute_source_composition(df):
    """Compute mean source counts by type per model."""
    # Filter: human baseline dataset, AI models only
    df_ai = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()

    # Fill NaN source counts with 0
    source_cols = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    for col in source_cols:
        df_ai[col] = df_ai[col].fillna(0)

    # Sum across both prompts per customer per model
    customer_sources = (
        df_ai.groupby(["customer_name", "model_label"])[source_cols]
        .sum()
        .reset_index()
    )

    # Mean per model
    model_sources = customer_sources.groupby("model_label")[source_cols].mean()

    # Order by MODEL_ORDER (AI only)
    ai_order = [m for m in MODEL_ORDER if m in model_sources.index]
    model_sources = model_sources.loc[ai_order]

    print("\nMean source counts per customer by model:")
    print(model_sources.round(2).to_string())

    return model_sources


def create_figure(model_sources):
    """Create stacked bar chart of source type composition."""
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 7))

    models = model_sources.index.tolist()
    x = np.arange(len(models))
    width = 0.7

    web = model_sources["num_web_sources"].values
    epmc = model_sources["num_epmc_sources"].values
    orcid = model_sources["num_orcid_sources"].values
    screen = model_sources["num_screen_sources"].values

    # Stacked bars: web at bottom, then epmc, orcid, screen on top
    bars_web = ax.bar(x, web, width, label="Web", color=COLORS["web"], alpha=0.9)
    bars_epmc = ax.bar(
        x, epmc, width, bottom=web, label="EPMC", color=COLORS["epmc"], alpha=0.9
    )
    bars_orcid = ax.bar(
        x, orcid, width, bottom=web + epmc, label="ORCID", color=COLORS["orcid"], alpha=0.9
    )
    bars_screen = ax.bar(
        x,
        screen,
        width,
        bottom=web + epmc + orcid,
        label="Screening DB",
        color=COLORS["screen"],
        alpha=0.9,
    )

    # X-axis labels
    short_labels = [shorten_model_label_no_time(m) for m in models]
    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)

    # Axis labels
    ax.set_ylabel("Mean Sources per Customer", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")

    # Total count labels on top of bars
    totals = web + epmc + orcid + screen
    for i, total in enumerate(totals):
        ax.text(
            i,
            total + 0.3,
            f"{total:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    # Y-axis limit
    ax.set_ylim(0, max(totals) * 1.12)

    # Title
    ax.set_title(
        "Source Type Composition by Model",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Legend
    ax.legend(loc="upper right", fontsize=10)

    # Grid
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    return fig


def save_outputs(model_sources):
    """Save data and caption files."""
    # Data file
    data_path = output_dir / "new_7_source_type_composition_data.txt"
    with open(data_path, "w") as f:
        f.write("Mean Source Counts per Customer by Model (Human Baseline Subset, AI Models Only)\n")
        f.write("=" * 90 + "\n\n")
        display = model_sources.copy()
        display.index = [shorten_model_label_no_time(m) for m in display.index]
        display.columns = ["Web", "EPMC", "ORCID", "Screen"]
        display["Total"] = display.sum(axis=1)
        f.write(display.round(2).to_string())
        f.write("\n")
    print(f"Data saved to: {data_path}")

    # Caption file
    caption_path = output_dir / "new_7_source_type_composition.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Mean number of sources per customer by type (web, EPMC, ORCID, screening DB) "
            "for each AI model on the 40-profile human baseline subset, summed across both prompts."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 7: Source Type Composition by Model")
    print("=" * 60)

    df = load_data()
    model_sources = compute_source_composition(df)

    fig = create_figure(model_sources)

    fig_path = output_dir / "new_7_source_type_composition.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure saved to: {fig_path}")

    plt.close()

    save_outputs(model_sources)

    print("\nDone.")


if __name__ == "__main__":
    main()
