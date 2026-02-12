#!/usr/bin/env python3
"""
Generate New Plot 14: Ground truth flag prevalence.

Stacked bar chart showing the distribution of FLAG / NO FLAG / UNDETERMINED
in the ground truth labels for each flag criterion, across the 40 profiles
in the human baseline dataset.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    setup_style,
    FLAG_ORDER,
    FLAG_LABELS,
)

# Ground truth column for each criterion
GT_COLUMNS = {
    "affiliation": "ground_truth_affiliation",
    "institution": "ground_truth_institution",
    "domain": "ground_truth_domain",
    "sanctions": "ground_truth_sanctions",
}

# Colors for each flag value
FLAG_VALUE_COLORS = {
    "FLAG": "#e74c3c",          # Red
    "NO FLAG": "#27ae60",       # Green
    "UNDETERMINED": "#95a5a6",  # Gray
}

FLAG_VALUES = ["FLAG", "NO FLAG", "UNDETERMINED"]

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"


def main():
    setup_style()

    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)

    # Filter: human baseline dataset only
    df_hb = df[df["is_human_baseline_dataset"] == True].copy()

    # For ground truth, we only need unique customers. Ground truth is the same
    # regardless of model, so pick one model to deduplicate.
    # Use any AI model that is present for all customers.
    sample_model = df_hb["model_label"].value_counts().idxmax()
    df_unique = df_hb[df_hb["model_label"] == sample_model].copy()

    # Further deduplicate by customer (one row per customer per criterion).
    # flag_accuracy test_category gives us 4 rows per customer (one per criterion).
    df_flags = df_unique[df_unique["test_category"] == "flag_accuracy"].copy()

    print(f"Using model '{sample_model}' for ground truth deduplication")
    print(f"Unique customers: {df_flags['customer_name'].nunique()}")

    # Count ground truth values per criterion
    records = []
    for crit in FLAG_ORDER:
        gt_col = GT_COLUMNS[crit]
        # Get one row per customer for this criterion
        # metric_name mapping
        metric_map = {
            "affiliation": "AFFILIATION-FLAG-ACCURACY",
            "institution": "INSTITUTION-FLAG-ACCURACY",
            "domain": "DOMAIN-FLAG-ACCURACY",
            "sanctions": "SANCTIONS-FLAG-ACCURACY",
        }
        crit_data = df_flags[df_flags["metric_name"] == metric_map[crit]]
        value_counts = crit_data[gt_col].value_counts()
        for fv in FLAG_VALUES:
            count = value_counts.get(fv, 0)
            records.append(
                {
                    "criterion": crit,
                    "criterion_label": FLAG_LABELS[crit],
                    "flag_value": fv,
                    "count": count,
                }
            )

    results_df = pd.DataFrame(records)

    # Print summary
    print("\nGround truth distribution:")
    pivot = results_df.pivot(
        index="criterion_label", columns="flag_value", values="count"
    )
    pivot = pivot.reindex(
        index=[FLAG_LABELS[c] for c in FLAG_ORDER], columns=FLAG_VALUES
    )
    print(pivot)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.arange(len(FLAG_ORDER))
    bar_width = 0.55
    bottom = np.zeros(len(FLAG_ORDER))

    for fv in FLAG_VALUES:
        counts = []
        for crit in FLAG_ORDER:
            row = results_df[
                (results_df["criterion"] == crit) & (results_df["flag_value"] == fv)
            ]
            counts.append(row["count"].values[0] if len(row) > 0 else 0)
        counts = np.array(counts)

        bars = ax.bar(
            x,
            counts,
            bar_width,
            bottom=bottom,
            label=fv,
            color=FLAG_VALUE_COLORS[fv],
            alpha=0.85,
            edgecolor="white",
            linewidth=0.5,
        )

        # Add count labels inside bars if count > 0
        for bar, count, bot in zip(bars, counts, bottom):
            if count > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bot + count / 2,
                    str(int(count)),
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white" if fv != "UNDETERMINED" else "black",
                )

        bottom += counts

    # Customize axes
    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS[c] for c in FLAG_ORDER], fontsize=12)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Profiles", fontsize=12, fontweight="bold")

    ax.set_title(
        "Ground Truth Flag Distribution Across 40 Profiles",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    # Save PNG
    png_path = output_dir / "new_14_ground_truth_prevalence.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nSaved: {png_path}")

    # Save data file
    data_path_out = output_dir / "new_14_ground_truth_prevalence_data.txt"
    with open(data_path_out, "w") as f:
        f.write("New Plot 14: Ground Truth Flag Prevalence\n")
        f.write("=" * 70 + "\n\n")
        f.write("Number of profiles per flag value per criterion:\n\n")
        f.write(pivot.to_string())
        f.write("\n\n")
        total = pivot.sum(axis=1)
        f.write("Total profiles per criterion:\n")
        for crit_label, t in total.items():
            f.write(f"  {crit_label}: {int(t)}\n")
    print(f"Saved: {data_path_out}")

    # Save label/caption file
    label_path = output_dir / "new_14_ground_truth_prevalence.txt"
    with open(label_path, "w") as f:
        f.write(
            "Figure 14: Ground truth flag distribution across the 40 profiles in "
            "the human baseline dataset. Each bar represents one flag criterion "
            "(Affiliation, Institution, Domain, Sanctions) and is divided into "
            "FLAG (red), NO FLAG (green), and UNDETERMINED (gray) segments. "
            "This illustrates the class balance (or imbalance) in the evaluation "
            "dataset for each criterion."
        )
    print(f"Saved: {label_path}")

    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
