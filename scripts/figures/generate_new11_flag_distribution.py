#!/usr/bin/env python3
"""
Generate New Plot 11: Flag distribution heatmap.

Shows the proportion of FLAG / NO FLAG / UNDETERMINED predictions
by model and flag criterion (AI models only, human baseline dataset).
Three side-by-side heatmaps (one per extracted_flag value).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

from style import (
    setup_style,
    MODEL_ORDER,
    FLAG_ORDER,
    FLAG_LABELS,
    shorten_model_label_no_time,
)

# Mapping from metric_name to criterion key
METRIC_TO_CRITERION = {
    "AFFILIATION-FLAG-ACCURACY": "affiliation",
    "INSTITUTION-FLAG-ACCURACY": "institution",
    "DOMAIN-FLAG-ACCURACY": "domain",
    "SANCTIONS-FLAG-ACCURACY": "sanctions",
}

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def main():
    setup_style()

    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)

    # Filter: flag accuracy, human baseline dataset, AI models only
    df_flag = df[
        (df["test_category"] == "flag_accuracy")
        & (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()

    # Map metric_name to criterion
    df_flag["criterion"] = df_flag["metric_name"].map(METRIC_TO_CRITERION)

    # Keep only models in MODEL_ORDER that are not human baselines
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    df_flag = df_flag[df_flag["model_label"].isin(ai_model_order)]

    print(f"Filtered flag accuracy rows: {len(df_flag)}")
    print(f"Models: {df_flag['model_label'].unique()}")
    print(f"Criteria: {df_flag['criterion'].unique()}")

    # Compute distribution of extracted_flag per model x criterion
    flag_values = ["FLAG", "NO FLAG", "UNDETERMINED"]
    flag_titles = ["FLAG (%)", "NO FLAG (%)", "UNDETERMINED (%)"]
    cmaps = ["Reds", "Greens", "Greys"]

    # Build pivot tables: one per flag value
    pivots = {}
    for fv in flag_values:
        records = []
        for model in ai_model_order:
            for crit in FLAG_ORDER:
                subset = df_flag[
                    (df_flag["model_label"] == model) & (df_flag["criterion"] == crit)
                ]
                total = len(subset)
                count = (subset["extracted_flag"] == fv).sum()
                pct = (count / total * 100) if total > 0 else 0.0
                records.append(
                    {
                        "model": shorten_model_label_no_time(model),
                        "criterion": FLAG_LABELS[crit],
                        "pct": pct,
                    }
                )
        pivot = pd.DataFrame(records).pivot(
            index="model", columns="criterion", values="pct"
        )
        # Reorder rows and columns
        row_order = [shorten_model_label_no_time(m) for m in ai_model_order]
        col_order = [FLAG_LABELS[c] for c in FLAG_ORDER]
        pivot = pivot.reindex(index=row_order, columns=col_order)
        pivots[fv] = pivot

    # Create figure with 3 subplots side by side
    fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)

    for idx, (fv, title, cmap) in enumerate(zip(flag_values, flag_titles, cmaps)):
        ax = axes[idx]
        pivot = pivots[fv]
        sns.heatmap(
            pivot,
            ax=ax,
            annot=True,
            fmt=".1f",
            cmap=cmap,
            vmin=0,
            vmax=100,
            linewidths=0.5,
            linecolor="white",
            cbar_kws={"label": "%", "shrink": 0.8},
            annot_kws={"fontsize": 9},
        )
        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("")
        if idx == 0:
            ax.set_ylabel("Model", fontsize=12)
        else:
            ax.set_ylabel("")
        ax.tick_params(axis="x", rotation=0)
        ax.tick_params(axis="y", rotation=0)

    fig.suptitle(
        "Distribution of Extracted Flag Values by Model and Criterion\n"
        "(AI Models, Human Baseline Dataset)",
        fontsize=14,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    # Save PNG
    png_path = output_dir / "new_11_flag_distribution.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved: {png_path}")

    # Save data file
    data_path_out = output_dir / "new_11_flag_distribution_data.txt"
    with open(data_path_out, "w") as f:
        f.write("New Plot 11: Flag Distribution by Model and Criterion\n")
        f.write("=" * 70 + "\n\n")
        for fv in flag_values:
            f.write(f"\n--- {fv} (%) ---\n")
            f.write(pivots[fv].round(1).to_string())
            f.write("\n")
    print(f"Saved: {data_path_out}")

    # Save label/caption file
    label_path = output_dir / "new_11_flag_distribution.txt"
    with open(label_path, "w") as f:
        f.write(
            "Figure 11: Distribution of extracted flag values (FLAG, NO FLAG, "
            "UNDETERMINED) across AI models and flag criteria. Each heatmap panel "
            "shows the percentage of responses for one flag value. Rows represent "
            "AI models; columns represent the four flag criteria (Affiliation, "
            "Institution, Domain, Sanctions). Only AI models evaluated on the "
            "40-profile human baseline dataset are included."
        )
    print(f"Saved: {label_path}")

    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
