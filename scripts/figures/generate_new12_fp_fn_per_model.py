#!/usr/bin/env python3
"""
Generate New Plot 12: False positive, false negative, and undetermined rates
per model per flag criterion.

Four subplots (one per criterion), each with grouped bars showing:
- False Positive rate (red): extracted FLAG when ground truth is NO FLAG
- False Negative rate (blue): extracted NO FLAG when ground truth is FLAG
- Undetermined rate (gray): extracted UNDETERMINED regardless of ground truth
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    setup_style,
    MODEL_ORDER,
    FLAG_ORDER,
    FLAG_LABELS,
    shorten_model_label_no_time,
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

# Error type colors
ERROR_COLORS = {
    "FP": "#e74c3c",   # Red
    "FN": "#3498db",   # Blue
    "UND": "#95a5a6",  # Gray
}
ERROR_LABELS = {
    "FP": "False Positive",
    "FN": "False Negative",
    "UND": "Undetermined",
}

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def classify_error(row):
    """Classify a flag accuracy row into FP, FN, UND, or correct."""
    metric = row["metric_name"]
    config = METRIC_CONFIG.get(metric)
    if config is None:
        return "other"
    gt = row[config["gt_col"]]
    pred = row["extracted_flag"]

    if pred == "UNDETERMINED":
        return "UND"
    elif gt == "NO FLAG" and pred == "FLAG":
        return "FP"
    elif gt == "FLAG" and pred == "NO FLAG":
        return "FN"
    else:
        return "correct"


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

    # Map criterion
    df_flag["criterion"] = df_flag["metric_name"].map(
        {k: v["criterion"] for k, v in METRIC_CONFIG.items()}
    )

    # Classify errors
    df_flag["error_type"] = df_flag.apply(classify_error, axis=1)

    # AI model order
    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    df_flag = df_flag[df_flag["model_label"].isin(ai_model_order)]

    print(f"Filtered rows: {len(df_flag)}")
    print(f"Error distribution:\n{df_flag['error_type'].value_counts()}")

    # Compute rates per model per criterion
    error_types = ["FP", "FN", "UND"]
    results = []
    for model in ai_model_order:
        for crit in FLAG_ORDER:
            subset = df_flag[
                (df_flag["model_label"] == model) & (df_flag["criterion"] == crit)
            ]
            total = len(subset)
            for et in error_types:
                count = (subset["error_type"] == et).sum()
                rate = (count / total * 100) if total > 0 else 0.0
                results.append(
                    {
                        "model": model,
                        "model_short": shorten_model_label_no_time(model),
                        "criterion": crit,
                        "error_type": et,
                        "rate": rate,
                        "count": count,
                        "total": total,
                    }
                )

    results_df = pd.DataFrame(results)

    # Create figure: 2x2 subplots, one per criterion
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes_flat = axes.flatten()

    short_labels = [shorten_model_label_no_time(m) for m in ai_model_order]
    x = np.arange(len(ai_model_order))
    bar_width = 0.25

    for idx, crit in enumerate(FLAG_ORDER):
        ax = axes_flat[idx]
        crit_data = results_df[results_df["criterion"] == crit]

        for et_idx, et in enumerate(error_types):
            et_data = crit_data[crit_data["error_type"] == et]
            # Ensure order matches ai_model_order
            rates = []
            for model in ai_model_order:
                row = et_data[et_data["model"] == model]
                rates.append(row["rate"].values[0] if len(row) > 0 else 0.0)

            offset = (et_idx - 1) * bar_width
            bars = ax.bar(
                x + offset,
                rates,
                bar_width,
                label=ERROR_LABELS[et],
                color=ERROR_COLORS[et],
                alpha=0.85,
                edgecolor="white",
                linewidth=0.5,
            )

            # Add value labels on bars > 1%
            for bar, val in zip(bars, rates):
                if val > 1.0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f"{val:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                    )

        ax.set_title(FLAG_LABELS[crit], fontsize=13, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(short_labels, fontsize=8, rotation=45, ha="right")
        ax.set_ylabel("Rate (%)")
        ax.grid(True, axis="y", alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Only show legend on first subplot
        if idx == 0:
            ax.legend(fontsize=9, loc="upper right")

    fig.suptitle(
        "False Positive, False Negative, and Undetermined Rates per Model\n"
        "(By Flag Criterion, AI Models, Human Baseline Dataset)",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()

    # Save PNG
    png_path = output_dir / "new_12_fp_fn_per_model.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved: {png_path}")

    # Save data file
    data_path_out = output_dir / "new_12_fp_fn_per_model_data.txt"
    with open(data_path_out, "w") as f:
        f.write("New Plot 12: FP / FN / Undetermined Rates per Model per Criterion\n")
        f.write("=" * 70 + "\n\n")
        for crit in FLAG_ORDER:
            f.write(f"\n--- {FLAG_LABELS[crit]} ---\n")
            crit_data = results_df[results_df["criterion"] == crit]
            pivot = crit_data.pivot(
                index="model_short", columns="error_type", values="rate"
            )
            pivot = pivot.reindex(
                index=[shorten_model_label_no_time(m) for m in ai_model_order],
                columns=error_types,
            )
            f.write(pivot.round(1).to_string())
            f.write("\n")
    print(f"Saved: {data_path_out}")

    # Save label/caption file
    label_path = output_dir / "new_12_fp_fn_per_model.txt"
    with open(label_path, "w") as f:
        f.write(
            "Figure 12: False positive rate, false negative rate, and undetermined "
            "rate for each AI model across the four flag criteria. A false positive "
            "occurs when the model predicts FLAG but the ground truth is NO FLAG; "
            "a false negative occurs when the model predicts NO FLAG but the ground "
            "truth is FLAG; undetermined means the model returned UNDETERMINED "
            "regardless of the ground truth. Rates are computed as the proportion "
            "of total assertions per model and criterion. Only AI models on the "
            "40-profile human baseline dataset are shown."
        )
    print(f"Saved: {label_path}")

    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
