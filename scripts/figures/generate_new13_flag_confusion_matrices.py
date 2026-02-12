#!/usr/bin/env python3
"""
Generate New Plot 13: Confusion matrices for flag accuracy.

Four 3x3 confusion matrices (one per flag criterion), aggregated across
all AI models. Rows = ground truth, columns = extracted prediction.
Labels: FLAG, NO FLAG, UNDETERMINED.
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
)

# Mapping from metric_name to ground truth column and criterion key
METRIC_CONFIG = {
    "AFFILIATION-FLAG-ACCURACY": {
        "gt_col": "ground_truth_affiliation",
        "criterion": "affiliation",
    },
    "INSTITUTION-FLAG-ACCURACY": {
        "gt_col": "ground_truth_institution",
        "criterion": "institution",
    },
    "DOMAIN-FLAG-ACCURACY": {
        "gt_col": "ground_truth_domain",
        "criterion": "domain",
    },
    "SANCTIONS-FLAG-ACCURACY": {
        "gt_col": "ground_truth_sanctions",
        "criterion": "sanctions",
    },
}

FLAG_CATEGORIES = ["FLAG", "NO FLAG", "UNDETERMINED"]

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def get_ground_truth(row):
    """Return the ground truth value for the row's metric."""
    config = METRIC_CONFIG.get(row["metric_name"])
    if config is None:
        return None
    return row[config["gt_col"]]


def main():
    setup_style()

    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)

    # Filter: flag accuracy, human baseline dataset, AI models only
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    df_flag = df[
        (df["test_category"] == "flag_accuracy")
        & (df["is_human_baseline_dataset"] == True)
        & (df["model_label"].isin(ai_model_order))
    ].copy()

    # Map criterion and get ground truth
    df_flag["criterion"] = df_flag["metric_name"].map(
        {k: v["criterion"] for k, v in METRIC_CONFIG.items()}
    )
    df_flag["ground_truth"] = df_flag.apply(get_ground_truth, axis=1)

    print(f"Filtered rows: {len(df_flag)}")

    # Build confusion matrices per criterion
    confusion_matrices = {}
    for crit in FLAG_ORDER:
        subset = df_flag[df_flag["criterion"] == crit]
        # Create confusion matrix as DataFrame
        cm = pd.crosstab(
            subset["ground_truth"],
            subset["extracted_flag"],
            rownames=["Ground Truth"],
            colnames=["Predicted"],
        )
        # Reindex to ensure all categories are present in the correct order
        cm = cm.reindex(index=FLAG_CATEGORIES, columns=FLAG_CATEGORIES, fill_value=0)
        confusion_matrices[crit] = cm

    # Create figure: 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes_flat = axes.flatten()

    for idx, crit in enumerate(FLAG_ORDER):
        ax = axes_flat[idx]
        cm = confusion_matrices[crit]
        cm_values = cm.values

        # Compute percentages (per row, i.e., per ground truth class)
        row_sums = cm_values.sum(axis=1, keepdims=True)
        # Avoid division by zero
        row_sums_safe = np.where(row_sums == 0, 1, row_sums)
        cm_pct = cm_values / row_sums_safe * 100

        # Create annotations with count and percentage
        annot = np.empty_like(cm_values, dtype=object)
        for i in range(cm_values.shape[0]):
            for j in range(cm_values.shape[1]):
                annot[i, j] = f"{cm_values[i, j]}\n({cm_pct[i, j]:.1f}%)"

        sns.heatmap(
            cm_values,
            ax=ax,
            annot=annot,
            fmt="",
            cmap="Blues",
            xticklabels=FLAG_CATEGORIES,
            yticklabels=FLAG_CATEGORIES,
            linewidths=1,
            linecolor="white",
            cbar_kws={"shrink": 0.7},
            annot_kws={"fontsize": 10},
        )

        ax.set_title(FLAG_LABELS[crit], fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted", fontsize=11)
        if idx % 2 == 0:
            ax.set_ylabel("Ground Truth", fontsize=11)
        else:
            ax.set_ylabel("")
        ax.tick_params(axis="x", rotation=30)
        ax.tick_params(axis="y", rotation=0)

    fig.suptitle(
        "Flag Accuracy Confusion Matrices by Criterion\n"
        "(Aggregated Across All AI Models, Human Baseline Dataset)",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()

    # Save PNG
    png_path = output_dir / "new_13_flag_confusion_matrices.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved: {png_path}")

    # Save data file
    data_path_out = output_dir / "new_13_flag_confusion_matrices_data.txt"
    with open(data_path_out, "w") as f:
        f.write("New Plot 13: Flag Accuracy Confusion Matrices\n")
        f.write("=" * 70 + "\n")
        f.write("Aggregated across all AI models, human baseline dataset.\n")
        f.write("Rows = Ground Truth, Columns = Predicted (extracted_flag).\n\n")
        for crit in FLAG_ORDER:
            cm = confusion_matrices[crit]
            f.write(f"\n--- {FLAG_LABELS[crit]} ---\n")
            f.write("Counts:\n")
            f.write(cm.to_string())
            f.write("\n\nRow-normalized (%):\n")
            row_sums = cm.sum(axis=1).replace(0, 1)
            cm_pct = cm.div(row_sums, axis=0) * 100
            f.write(cm_pct.round(1).to_string())
            f.write("\n\n")
    print(f"Saved: {data_path_out}")

    # Save label/caption file
    label_path = output_dir / "new_13_flag_confusion_matrices.txt"
    with open(label_path, "w") as f:
        f.write(
            "Figure 13: Confusion matrices for flag accuracy across the four "
            "flag criteria (Affiliation, Institution, Domain, Sanctions), "
            "aggregated across all AI models on the 40-profile human baseline "
            "dataset. Rows represent the ground truth flag value; columns "
            "represent the model's extracted prediction. Each cell shows "
            "the count and the row-normalized percentage. Ideal performance "
            "would place all mass on the diagonal."
        )
    print(f"Saved: {label_path}")

    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
