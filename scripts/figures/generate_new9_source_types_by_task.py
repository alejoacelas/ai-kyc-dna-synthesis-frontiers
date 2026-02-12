#!/usr/bin/env python3
"""
Generate New Plot 9: Source Types by Prompt Type (All-Tools Models Only).

Grouped bar chart showing average source type counts (web, EPMC, ORCID, screen)
broken down by prompt type (main screening vs background work) for all_tools models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import COLORS, setup_style

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def load_data():
    """Load responses dataset."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "responses.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")
    return df


def compute_source_by_prompt(df):
    """Compute mean source counts by type for each prompt type (all_tools models)."""
    # Filter: human baseline dataset, all_tools models only
    df_at = df[
        (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] == "all_tools")
    ].copy()

    source_cols = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    for col in source_cols:
        df_at[col] = df_at[col].fillna(0)

    print(f"Filtered rows (all_tools, baseline subset): {len(df_at):,}")
    print(f"Prompt types: {df_at['prompt_type'].value_counts().to_dict()}")

    # Mean per prompt_type across all models and customers
    prompt_sources = df_at.groupby("prompt_type")[source_cols].mean()

    print("\nMean source counts by prompt type:")
    print(prompt_sources.round(2).to_string())

    return prompt_sources


def create_figure(prompt_sources):
    """Create grouped bar chart of source types by prompt type."""
    setup_style()

    fig, ax = plt.subplots(figsize=(8, 6))

    source_types = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    source_labels = ["Web", "EPMC", "ORCID", "Screening DB"]
    source_colors = [COLORS["web"], COLORS["epmc"], COLORS["orcid"], COLORS["screen"]]

    # Prompt type display labels
    prompt_display = {"main": "Main Screening", "background_work": "Background Work"}
    prompts = [p for p in ["main", "background_work"] if p in prompt_sources.index]

    x = np.arange(len(prompts))
    n_sources = len(source_types)
    bar_width = 0.18
    offsets = np.arange(n_sources) - (n_sources - 1) / 2

    for i, (src_col, src_label, src_color) in enumerate(
        zip(source_types, source_labels, source_colors)
    ):
        values = [prompt_sources.loc[p, src_col] if p in prompt_sources.index else 0 for p in prompts]
        bars = ax.bar(
            x + offsets[i] * bar_width,
            values,
            bar_width,
            label=src_label,
            color=src_color,
            alpha=0.9,
            edgecolor="white",
            linewidth=0.5,
        )
        # Value labels on top of each bar
        for bar, val in zip(bars, values):
            if val > 0.01:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 0.05,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    # X-axis
    ax.set_xticks(x)
    ax.set_xticklabels([prompt_display.get(p, p) for p in prompts], fontsize=11)
    ax.set_xlabel("Prompt Type", fontsize=12, fontweight="bold")

    # Y-axis
    ax.set_ylabel("Mean Source Count", fontsize=12, fontweight="bold")

    # Title
    ax.set_title(
        "Source Types by Prompt Type (All-Tools Models)",
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


def save_outputs(prompt_sources):
    """Save data and caption files."""
    # Data file
    data_path = output_dir / "new_9_source_types_by_task_data.txt"
    with open(data_path, "w") as f:
        f.write("Mean Source Counts by Type and Prompt Type (All-Tools Models, Human Baseline Subset)\n")
        f.write("=" * 80 + "\n\n")
        display = prompt_sources.copy()
        display.columns = ["Web", "EPMC", "ORCID", "Screen"]
        display.index = display.index.map(
            {"main": "Main Screening", "background_work": "Background Work"}
        )
        display["Total"] = display.sum(axis=1)
        f.write(display.round(3).to_string())
        f.write("\n")
    print(f"Data saved to: {data_path}")

    # Caption file
    caption_path = output_dir / "new_9_source_types_by_task.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Mean source counts by type (web, EPMC, ORCID, screening DB) for main screening "
            "vs background work prompts across all-tools models on the 40-profile human baseline subset."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 9: Source Types by Prompt Type")
    print("=" * 60)

    df = load_data()
    prompt_sources = compute_source_by_prompt(df)

    fig = create_figure(prompt_sources)

    fig_path = output_dir / "new_9_source_types_by_task.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nFigure saved to: {fig_path}")

    plt.close()

    save_outputs(prompt_sources)

    print("\nDone.")


if __name__ == "__main__":
    main()
