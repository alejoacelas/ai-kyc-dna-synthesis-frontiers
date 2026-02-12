#!/usr/bin/env python3
"""
Generate New Plot 29: Forest Plot of Pass Rate with Wilson Confidence Intervals.

Horizontal forest plot with one row per model showing point estimate and 95% Wilson CI.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import (
    setup_style,
    MODEL_ORDER,
    MODEL_LABELS_NO_TIME,
    get_model_color,
)

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def wilson_ci(p, n, z=1.96):
    """
    Wilson score confidence interval for a proportion.
    p: observed proportion
    n: sample size
    z: z-score (1.96 for 95% CI)
    Returns (lower, upper).
    """
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    spread = z * np.sqrt((p * (1 - p) / n + z ** 2 / (4 * n ** 2))) / denom
    return max(0, center - spread), min(1, center + spread)


def load_data():
    """Load tests.csv and filter."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    df = df[df["is_human_baseline_dataset"] == True].copy()
    print(f"Baseline rows: {len(df):,}")

    return df


def compute_cis(df):
    """Compute pass rate and Wilson CIs per model."""
    models = [m for m in MODEL_ORDER if m in df["model_label"].unique()]
    results = []

    for m in models:
        subset = df[df["model_label"] == m]
        n = len(subset)
        p = subset["pass"].mean()
        lo, hi = wilson_ci(p, n)
        results.append({
            "model": m,
            "short": MODEL_LABELS_NO_TIME.get(m, m),
            "n": n,
            "pass_rate": p * 100,
            "ci_low": lo * 100,
            "ci_high": hi * 100,
        })

    return pd.DataFrame(results)


def create_figure(results_df):
    """Create forest plot."""
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 7))

    n_models = len(results_df)
    y_pos = np.arange(n_models)

    for i, row in results_df.iterrows():
        color = get_model_color(row["model"])
        ax.plot(
            [row["ci_low"], row["ci_high"]],
            [i, i],
            color=color,
            linewidth=2.5,
            solid_capstyle="round",
        )
        ax.plot(row["pass_rate"], i, "o", color=color, markersize=8, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(results_df["short"], fontsize=10)
    ax.set_xlabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Overall Pass Rate with 95% Wilson Confidence Intervals",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    # Invert y-axis so first model is at top
    ax.invert_yaxis()

    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#2ecc71", linewidth=2.5, marker="o", label="All Tools"),
        Line2D([0], [0], color="#3498db", linewidth=2.5, marker="o", label="Web Only"),
        Line2D([0], [0], color="#e74c3c", linewidth=2.5, marker="o", label="Human Baseline"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    plt.tight_layout()
    return fig


def write_outputs(results_df):
    """Write data and caption files."""
    data_path = output_dir / "new_29_passrate_confidence_intervals_data.txt"
    with open(data_path, "w") as f:
        f.write("Plot 29: Pass Rate with 95% Wilson Confidence Intervals\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'Model':<17s} {'N':>6s} {'Rate':>7s} {'CI Low':>8s} {'CI High':>8s}\n")
        f.write("-" * 50 + "\n")
        for _, row in results_df.iterrows():
            f.write(
                f"{row['short']:<17s} {row['n']:>6.0f} {row['pass_rate']:>6.1f}% "
                f"{row['ci_low']:>7.1f}% {row['ci_high']:>7.1f}%\n"
            )
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_29_passrate_confidence_intervals.txt"
    with open(caption_path, "w") as f:
        f.write(
            "Forest plot of overall pass rate per model with 95% Wilson score confidence intervals "
            "on the 40-profile human baseline subset. Dots indicate point estimates; horizontal "
            "lines show confidence intervals. Green = All Tools, blue = Web Only, red = Human Baseline."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 29: Pass Rate Confidence Intervals")
    print("=" * 60)

    df = load_data()
    results_df = compute_cis(df)
    print("\nResults:")
    print(results_df[["short", "n", "pass_rate", "ci_low", "ci_high"]].to_string(index=False))

    fig = create_figure(results_df)

    fig_path = output_dir / "new_29_passrate_confidence_intervals.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(results_df)
    print("Done.")


if __name__ == "__main__":
    main()
