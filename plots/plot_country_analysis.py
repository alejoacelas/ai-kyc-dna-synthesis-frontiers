#!/usr/bin/env python3
"""
Country and flag error analysis plots for KYC evaluation results.

Generates:
- Pass rate by country for all tools models (on full dataset)
- Flag errors by ground truth flag for human baseline 30 min, and each all tools model
- Flag errors stratified by customer type (aggregated across models)
- Flag errors stratified by country (aggregated across models)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from style import (
    DATA_DIR, COLORS, MODEL_ORDER, COUNTRY_ORDER, FLAG_ORDER, FLAG_LABELS,
    get_model_color, shorten_model_label, save_figure, add_value_labels,
    setup_style
)

setup_style()


def load_tests_data():
    """Load the tests dataset."""
    df = pd.read_csv(DATA_DIR / "tests.csv")
    df["pass"] = df["pass"].astype(str) == "True"
    return df


def filter_all_tools_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to all tools models only."""
    return df[df["model_type"] == "all_tools"].copy()


def filter_full_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to full dataset (not human baseline subset)."""
    return df[df["is_human_baseline_dataset"] == False].copy()


def filter_hb_dataset_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to human baseline dataset subset only."""
    return df[df["is_human_baseline_dataset"] == True].copy()


def filter_flag_accuracy_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to flag accuracy tests only."""
    return df[df["test_category"] == "flag_accuracy"].copy()


def filter_30min_human_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 5min human baseline, keep only 30min."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def get_flag_from_metric(metric_name: str) -> str:
    """Extract flag type from metric name."""
    metric_upper = metric_name.upper()
    if "AFFILIATION" in metric_upper:
        return "affiliation"
    elif "INSTITUTION" in metric_upper:
        return "institution"
    elif "DOMAIN" in metric_upper:
        return "domain"
    elif "SANCTIONS" in metric_upper:
        return "sanctions"
    return "unknown"


def compute_flag_error_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute error rates for flag accuracy tests.

    Error = ground truth is FLAG or NO FLAG but model got it wrong.
    Excludes UNDETERMINED ground truth from error calculation.

    Adds columns:
    - error: True if model got it wrong
    - false_neg: True if ground truth was FLAG but model said NO FLAG
    - false_pos: True if ground truth was NO FLAG but model said FLAG
    """
    # Add flag type column
    df = df.copy()
    df["flag_type"] = df["metric_name"].apply(get_flag_from_metric)

    # Get ground truth column for each row
    def get_ground_truth(row):
        flag_type = row["flag_type"]
        col = f"ground_truth_{flag_type}"
        return row.get(col, "UNDETERMINED")

    df["ground_truth"] = df.apply(get_ground_truth, axis=1)

    # Filter out UNDETERMINED ground truth
    df_with_gt = df[df["ground_truth"] != "UNDETERMINED"].copy()

    # Error = not pass
    df_with_gt["error"] = ~df_with_gt["pass"]

    # False negative: ground truth was FLAG but model said NO FLAG (or other)
    # False positive: ground truth was NO FLAG but model said FLAG
    df_with_gt["false_neg"] = (
        (df_with_gt["ground_truth"] == "FLAG") & (~df_with_gt["pass"])
    )
    df_with_gt["false_pos"] = (
        (df_with_gt["ground_truth"] == "NO FLAG") & (~df_with_gt["pass"])
    )

    return df_with_gt


def filter_all_models_except_5min(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to all models except Human Baseline (5min)."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def plot_pass_rates_by_country_all_tools(df: pd.DataFrame):
    """Plot pass rates by country for all tools models on full dataset."""
    # Filter to all tools models on full dataset
    df_filtered = filter_all_tools_only(df)
    df_filtered = filter_full_dataset(df_filtered)

    # Calculate pass rates per country
    pass_rates = df_filtered.groupby("institution_country")["pass"].mean() * 100

    # Reorder by COUNTRY_ORDER
    countries = [c for c in COUNTRY_ORDER if c in pass_rates.index]
    pass_rates = pass_rates.loc[countries]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Create bars
    colors = [COLORS.get(c, "#95a5a6") for c in countries]
    x = np.arange(len(countries))
    bars = ax.bar(x, pass_rates.values, color=colors, edgecolor="white", linewidth=0.5)

    # Customize
    ax.set_xlabel("Institution Country")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Country - All Tools Models (Full Dataset)")
    ax.set_xticks(x)
    ax.set_xticklabels(countries)
    ax.set_ylim(0, 100)

    # Add value labels
    add_value_labels(ax, bars)

    # Add sample sizes
    counts = df_filtered.groupby("institution_country").size()
    for i, c in enumerate(countries):
        ax.annotate(
            f"n={counts.get(c, 0)}",
            xy=(i, 5),
            ha="center",
            va="bottom",
            fontsize=9,
            color="gray",
        )

    plt.tight_layout()
    save_figure(fig, "pass_rates_by_country_all_tools")
    plt.close()


def plot_flag_errors_by_ground_truth(df: pd.DataFrame):
    """
    Plot flag error rates by ground truth flag, aggregated across all models.

    Creates a grouped bar chart with stacked false positives and false negatives
    for each flag type.
    """
    # Filter to flag accuracy tests on HB dataset
    df_filtered = filter_flag_accuracy_tests(df)
    df_filtered = filter_hb_dataset_only(df_filtered)
    df_filtered = filter_all_models_except_5min(df_filtered)

    # Compute error rates
    df_errors = compute_flag_error_rates(df_filtered)

    # Calculate false neg and false pos rates per flag type (aggregated across all models)
    fn_rates = df_errors.groupby("flag_type")["false_neg"].mean() * 100
    fp_rates = df_errors.groupby("flag_type")["false_pos"].mean() * 100

    # Reorder flags
    flags = [f for f in FLAG_ORDER if f in fn_rates.index]
    fn_rates = fn_rates.loc[flags]
    fp_rates = fp_rates.loc[flags]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Bar positions
    x = np.arange(len(flags))
    width = 0.6

    # Plot stacked bars: false negatives on bottom, false positives on top
    bars_fn = ax.bar(
        x, fn_rates.values, width,
        label="False neg. (should FLAG)",
        color=COLORS["fail"],
        edgecolor="white",
        linewidth=0.5,
    )
    bars_fp = ax.bar(
        x, fp_rates.values, width,
        bottom=fn_rates.values,
        label="False pos. (should NOT FLAG)",
        color="#f39c12",  # Orange
        edgecolor="white",
        linewidth=0.5,
    )

    # Add value labels on bars
    for i, (fn, fp) in enumerate(zip(fn_rates.values, fp_rates.values)):
        total = fn + fp
        if total > 0:
            ax.annotate(
                f"{total:.1f}%",
                xy=(i, total + 1),
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Customize
    ax.set_xlabel("Flag Type")
    ax.set_ylabel("Error Rate (%)")
    ax.set_title("Flag Errors by Flag Type\n(All Models excl. 5min Human)")
    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in flags])
    max_val = (fn_rates + fp_rates).max()
    ax.set_ylim(0, max(max_val * 1.2, 20))
    ax.legend(loc="upper right")

    plt.tight_layout()
    save_figure(fig, "flag_errors_by_ground_truth")
    plt.close()


def plot_flag_errors_by_customer_type(df: pd.DataFrame):
    """
    Plot flag error rates stratified by customer type.

    Aggregates across all models (excluding 5min human baseline).
    Shows stacked false negatives and false positives.
    """
    # Filter to flag accuracy tests on HB dataset
    df_filtered = filter_flag_accuracy_tests(df)
    df_filtered = filter_hb_dataset_only(df_filtered)
    df_filtered = filter_all_models_except_5min(df_filtered)

    # Compute error rates
    df_errors = compute_flag_error_rates(df_filtered)

    # Calculate false neg and false pos rates per customer type
    fn_rates = df_errors.groupby("customer_type")["false_neg"].mean() * 100
    fp_rates = df_errors.groupby("customer_type")["false_pos"].mean() * 100

    # Get customer types (sorted by total error rate)
    total_errors = fn_rates + fp_rates
    customer_types = total_errors.sort_values(ascending=False).index.tolist()
    fn_rates = fn_rates.loc[customer_types]
    fp_rates = fp_rates.loc[customer_types]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Bar positions
    x = np.arange(len(customer_types))
    width = 0.6

    # Plot stacked bars
    bars_fn = ax.bar(
        x, fn_rates.values, width,
        label="False neg. (should FLAG)",
        color=COLORS["fail"],
        edgecolor="white",
        linewidth=0.5,
    )
    bars_fp = ax.bar(
        x, fp_rates.values, width,
        bottom=fn_rates.values,
        label="False pos. (should NOT FLAG)",
        color="#f39c12",
        edgecolor="white",
        linewidth=0.5,
    )

    # Add value labels on bars
    for i, (fn, fp) in enumerate(zip(fn_rates.values, fp_rates.values)):
        total = fn + fp
        if total > 0:
            ax.annotate(
                f"{total:.1f}%",
                xy=(i, total + 1),
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Customize
    ax.set_xlabel("Customer Type")
    ax.set_ylabel("Error Rate (%)")
    ax.set_title("Flag Errors by Customer Type\n(All Models excl. 5min Human)")
    ax.set_xticks(x)
    ax.set_xticklabels(customer_types, rotation=15, ha="right")
    max_val = (fn_rates + fp_rates).max()
    ax.set_ylim(0, max(max_val * 1.2, 20))
    ax.legend(loc="upper right")

    plt.tight_layout()
    save_figure(fig, "flag_errors_by_customer_type")
    plt.close()


def plot_flag_errors_by_country(df: pd.DataFrame):
    """
    Plot flag error rates stratified by country.

    Aggregates across all models (excluding 5min human baseline).
    Shows stacked false negatives and false positives.
    """
    # Filter to flag accuracy tests on HB dataset
    df_filtered = filter_flag_accuracy_tests(df)
    df_filtered = filter_hb_dataset_only(df_filtered)
    df_filtered = filter_all_models_except_5min(df_filtered)

    # Compute error rates
    df_errors = compute_flag_error_rates(df_filtered)

    # Calculate false neg and false pos rates per country
    fn_rates = df_errors.groupby("institution_country")["false_neg"].mean() * 100
    fp_rates = df_errors.groupby("institution_country")["false_pos"].mean() * 100

    # Reorder by COUNTRY_ORDER
    countries = [c for c in COUNTRY_ORDER if c in fn_rates.index]
    fn_rates = fn_rates.loc[countries]
    fp_rates = fp_rates.loc[countries]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Bar positions
    x = np.arange(len(countries))
    width = 0.6

    # Plot stacked bars
    bars_fn = ax.bar(
        x, fn_rates.values, width,
        label="False neg. (should FLAG)",
        color=COLORS["fail"],
        edgecolor="white",
        linewidth=0.5,
    )
    bars_fp = ax.bar(
        x, fp_rates.values, width,
        bottom=fn_rates.values,
        label="False pos. (should NOT FLAG)",
        color="#f39c12",
        edgecolor="white",
        linewidth=0.5,
    )

    # Add value labels on bars
    for i, (fn, fp) in enumerate(zip(fn_rates.values, fp_rates.values)):
        total = fn + fp
        if total > 0:
            ax.annotate(
                f"{total:.1f}%",
                xy=(i, total + 1),
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Customize
    ax.set_xlabel("Institution Country")
    ax.set_ylabel("Error Rate (%)")
    ax.set_title("Flag Errors by Country\n(All Models excl. 5min Human)")
    ax.set_xticks(x)
    ax.set_xticklabels(countries)
    max_val = (fn_rates + fp_rates).max()
    ax.set_ylim(0, max(max_val * 1.2, 20))
    ax.legend(loc="upper right")

    plt.tight_layout()
    save_figure(fig, "flag_errors_by_country")
    plt.close()


def plot_flag_errors_by_flag_and_country(df: pd.DataFrame):
    """
    Plot flag error rates by flag type and country (faceted).

    Creates a 2x2 grid of subplots, one per flag type, with countries on x-axis
    and stacked false neg/pos bars.
    """
    # Filter to flag accuracy tests on HB dataset
    df_filtered = filter_flag_accuracy_tests(df)
    df_filtered = filter_hb_dataset_only(df_filtered)
    df_filtered = filter_all_models_except_5min(df_filtered)

    # Compute error rates
    df_errors = compute_flag_error_rates(df_filtered)

    # Calculate false neg and false pos rates per flag type and country
    grouped = df_errors.groupby(["flag_type", "institution_country"]).agg({
        "false_neg": "mean",
        "false_pos": "mean",
    }) * 100

    # Create 2x2 figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    # Get countries in order
    countries = [c for c in COUNTRY_ORDER if c in df_errors["institution_country"].unique()]

    for idx, flag in enumerate(FLAG_ORDER):
        ax = axes[idx]

        if flag not in grouped.index.get_level_values(0):
            ax.set_visible(False)
            continue

        # Get data for this flag type
        flag_data = grouped.loc[flag]

        # Reorder by country order
        flag_countries = [c for c in countries if c in flag_data.index]
        fn_vals = [flag_data.loc[c, "false_neg"] if c in flag_data.index else 0 for c in flag_countries]
        fp_vals = [flag_data.loc[c, "false_pos"] if c in flag_data.index else 0 for c in flag_countries]

        x = np.arange(len(flag_countries))
        width = 0.6

        # Plot stacked bars
        ax.bar(
            x, fn_vals, width,
            label="False neg. (should FLAG)",
            color=COLORS["fail"],
            edgecolor="white",
            linewidth=0.5,
        )
        ax.bar(
            x, fp_vals, width,
            bottom=fn_vals,
            label="False pos. (should NOT FLAG)",
            color="#f39c12",
            edgecolor="white",
            linewidth=0.5,
        )

        # Add value labels
        for i, (fn, fp) in enumerate(zip(fn_vals, fp_vals)):
            total = fn + fp
            if total > 0:
                ax.annotate(
                    f"{total:.1f}%",
                    xy=(i, total + 0.5),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        # Customize subplot
        ax.set_title(FLAG_LABELS.get(flag, flag), fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(flag_countries, fontsize=10)
        ax.set_ylabel("Error Rate (%)")
        ax.set_ylim(0, max(max(fn + fp for fn, fp in zip(fn_vals, fp_vals)) * 1.3, 15))

        # Only show legend on first subplot
        if idx == 0:
            ax.legend(loc="upper right", fontsize=9)

    # Overall title
    fig.suptitle(
        "Flag Errors by Flag Type and Country\n(All Models excl. 5min Human)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    save_figure(fig, "flag_errors_by_flag_and_country")
    plt.close()


def main():
    """Generate all country and flag error analysis plots."""
    print("Loading data...")
    df = load_tests_data()
    print(f"Loaded {len(df)} test results")

    # Check if institution_country column exists
    if "institution_country" not in df.columns:
        print("ERROR: institution_country column not found in tests.csv")
        print("Please regenerate the datasets with: python scripts/generate_analysis_datasets.py")
        return

    print("\nGenerating plots...")

    # 1. Pass rate by country for all tools models
    print("  Pass rates by country (all tools, full dataset)...")
    plot_pass_rates_by_country_all_tools(df)

    # 2. Flag errors by ground truth flag
    print("  Flag errors by ground truth flag...")
    plot_flag_errors_by_ground_truth(df)

    # 3. Flag errors stratified by customer type
    print("  Flag errors by customer type...")
    plot_flag_errors_by_customer_type(df)

    # 4. Flag errors stratified by country
    print("  Flag errors by country...")
    plot_flag_errors_by_country(df)

    # 5. Flag errors by flag type and country (faceted)
    print("  Flag errors by flag type and country (faceted)...")
    plot_flag_errors_by_flag_and_country(df)

    print("\nDone!")


if __name__ == "__main__":
    main()
