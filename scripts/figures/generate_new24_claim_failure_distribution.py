#!/usr/bin/env python3
"""
Generate New Plot 24: Distribution of Failed Claims per Customer.

Among claim_support assertions, histogram of how many failed per customer,
aggregated across AI models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from style import setup_style, COLORS

output_dir = Path(__file__).parent.parent.parent / "paper" / "new-plots"
output_dir.mkdir(parents=True, exist_ok=True)


def load_and_prepare():
    """Load tests.csv, count failed claim_support assertions per customer per model."""
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    # Filter: claim_support, baseline, AI only
    df = df[
        (df["test_category"] == "claim_support")
        & (df["is_human_baseline_dataset"] == True)
        & (df["model_type"] != "human_baseline")
    ].copy()
    print(f"Claim support rows (AI, baseline): {len(df):,}")

    # Count failed claims per customer per model
    failed = df[df["pass"] == False].groupby(["customer_name", "model_label"]).size().reset_index(name="num_failed")

    # Also include customers with zero failures
    all_combos = df[["customer_name", "model_label"]].drop_duplicates()
    merged = all_combos.merge(failed, on=["customer_name", "model_label"], how="left")
    merged["num_failed"] = merged["num_failed"].fillna(0).astype(int)

    print(f"Customer-model pairs: {len(merged):,}")
    print(f"Pairs with >0 failures: {(merged['num_failed'] > 0).sum()}")
    print(f"Mean failed per customer-model: {merged['num_failed'].mean():.2f}")

    return merged


def create_figure(merged):
    """Create histogram of failed claims count."""
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 6))

    counts = merged["num_failed"]
    max_val = int(counts.max())

    bins = np.arange(-0.5, max_val + 1.5, 1)
    ax.hist(
        counts,
        bins=bins,
        color=COLORS["fail"],
        alpha=0.75,
        edgecolor="white",
        linewidth=0.5,
    )

    mean_val = counts.mean()
    median_val = counts.median()

    ax.axvline(mean_val, color="#3498db", linestyle="--", linewidth=2, label=f"Mean: {mean_val:.1f}")
    ax.axvline(median_val, color="#f39c12", linestyle="-", linewidth=2, label=f"Median: {median_val:.0f}")

    ax.set_xlabel("Number of Failed Claim Assertions", fontsize=12, fontweight="bold")
    ax.set_ylabel("Count (Customer-Model Pairs)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Distribution of Failed Claim-Support Assertions per Customer",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    stats_text = (
        f"n = {len(counts)} pairs\n"
        f"Mean = {mean_val:.1f}\n"
        f"Median = {median_val:.0f}\n"
        f"Max = {max_val}\n"
        f"Zero failures: {(counts == 0).sum()} ({(counts == 0).mean() * 100:.0f}%)"
    )
    ax.text(
        0.95,
        0.95,
        stats_text,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#cccccc", alpha=0.9),
        family="monospace",
    )

    ax.legend(loc="upper center", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def write_outputs(merged):
    """Write data and caption files."""
    counts = merged["num_failed"]
    data_path = output_dir / "new_24_claim_failure_distribution_data.txt"
    with open(data_path, "w") as f:
        f.write("Plot 24: Failed Claim-Support Assertions per Customer\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total customer-model pairs: {len(counts)}\n")
        f.write(f"Mean failed claims: {counts.mean():.2f}\n")
        f.write(f"Median failed claims: {counts.median():.0f}\n")
        f.write(f"Max failed claims: {counts.max()}\n\n")
        f.write("Distribution:\n")
        vc = counts.value_counts().sort_index()
        f.write(f"{'Failed':>8s} {'Count':>8s} {'Pct':>8s}\n")
        f.write("-" * 26 + "\n")
        for val, cnt in vc.items():
            f.write(f"{val:>8d} {cnt:>8d} {cnt / len(counts) * 100:>7.1f}%\n")
    print(f"Data saved to: {data_path}")

    caption_path = output_dir / "new_24_claim_failure_distribution.txt"
    with open(caption_path, "w") as f:
        f.write(
            f"Distribution of failed claim-support assertions per customer across {len(counts)} "
            f"customer-model pairs (AI models, 40-profile subset). "
            f"{(counts == 0).sum()} pairs ({(counts == 0).mean() * 100:.0f}%) had zero failures."
        )
    print(f"Caption saved to: {caption_path}")


def main():
    print("Generating New Plot 24: Claim Failure Distribution")
    print("=" * 60)

    merged = load_and_prepare()
    fig = create_figure(merged)

    fig_path = output_dir / "new_24_claim_failure_distribution.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figure saved to: {fig_path}")
    plt.close()

    write_outputs(merged)
    print("Done.")


if __name__ == "__main__":
    main()
