#!/usr/bin/env python3
"""
Pass rate analysis plots for KYC evaluation results.

Generates:
- Overall pass rates by model
- Pass rates by test category
- Pass rates by model type (web vs all_tools vs human)
- Pass rates by prompt type
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from style import (
    DATA_DIR, COLORS, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    get_model_color, shorten_model_label, save_figure, add_value_labels,
    setup_style
)

setup_style()


def load_tests_data():
    """Load the tests dataset."""
    df = pd.read_csv(DATA_DIR / "tests.csv")
    df["pass"] = df["pass"].astype(str) == "True"
    return df


def filter_for_valid_ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter data to only include tests where ground truth is available.

    For flag_accuracy tests, ground truth is only available in the human baseline
    dataset subset. Other test categories can use all data.
    """
    # Split by test category
    flag_accuracy = df[df["test_category"] == "flag_accuracy"]
    other_tests = df[df["test_category"] != "flag_accuracy"]

    # For flag accuracy, only keep human baseline dataset subset
    flag_accuracy_filtered = flag_accuracy[flag_accuracy["is_human_baseline_dataset"] == True]

    # Combine back
    return pd.concat([other_tests, flag_accuracy_filtered], ignore_index=True)


def filter_hb_dataset_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to human baseline dataset subset only (for AI vs human comparisons)."""
    return df[df["is_human_baseline_dataset"] == True].copy()


def filter_30min_human_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 5min human baseline, keep only 30min."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def filter_ai_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to AI models only (exclude human baseline)."""
    return df[df["model_type"] != "human_baseline"].copy()


def plot_pass_rates_by_model(df: pd.DataFrame, suffix: str = ""):
    """Plot overall pass rates by model."""
    # Calculate pass rates per model
    pass_rates = df.groupby("model_label")["pass"].mean() * 100

    # Reorder by MODEL_ORDER (only include models present in data)
    models = [m for m in MODEL_ORDER if m in pass_rates.index]
    pass_rates = pass_rates.loc[models]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create bars with colors based on model type
    colors = [get_model_color(m) for m in models]
    x = np.arange(len(models))
    bars = ax.bar(x, pass_rates.values, color=colors, edgecolor="white", linewidth=0.5)

    # Customize
    ax.set_xlabel("Model")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Overall Pass Rate by Model")
    ax.set_xticks(x)
    ax.set_xticklabels([shorten_model_label(m) for m in models], rotation=45, ha="right")
    ax.set_ylim(0, 100)

    # Add value labels
    add_value_labels(ax, bars)

    # Add legend for model types (only include types present in data)
    from matplotlib.patches import Patch
    legend_elements = []
    model_types_present = df["model_type"].unique()
    if "web_only" in model_types_present:
        legend_elements.append(Patch(facecolor=COLORS["web_only"], label="Web Only"))
    if "all_tools" in model_types_present:
        legend_elements.append(Patch(facecolor=COLORS["all_tools"], label="All Tools"))
    if "human_baseline" in model_types_present:
        legend_elements.append(Patch(facecolor=COLORS["human_baseline"], label="Human Baseline"))
    if legend_elements:
        ax.legend(handles=legend_elements, loc="lower left")

    plt.tight_layout()
    save_figure(fig, f"pass_rates_by_model{suffix}")
    plt.close()


def plot_pass_rates_by_category(df: pd.DataFrame, suffix: str = ""):
    """Plot pass rates by test category."""
    # Calculate pass rates per category
    pass_rates = df.groupby("test_category")["pass"].mean() * 100

    # Reorder
    categories = [c for c in CATEGORY_ORDER if c in pass_rates.index]
    pass_rates = pass_rates.loc[categories]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Create bars
    colors = [COLORS[c] for c in categories]
    x = np.arange(len(categories))
    bars = ax.bar(x, pass_rates.values, color=colors, edgecolor="white", linewidth=0.5)

    # Customize
    ax.set_xlabel("Test Category")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Test Category")
    ax.set_xticks(x)
    ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
    ax.set_ylim(0, 100)

    # Add value labels
    add_value_labels(ax, bars)

    plt.tight_layout()
    save_figure(fig, f"pass_rates_by_category{suffix}")
    plt.close()


def plot_pass_rates_heatmap(df: pd.DataFrame, suffix: str = ""):
    """Plot heatmap of pass rates by model and category."""
    # Calculate pass rates
    pivot = df.pivot_table(
        values="pass",
        index="model_label",
        columns="test_category",
        aggfunc="mean"
    ) * 100

    # Reorder
    models = [m for m in MODEL_ORDER if m in pivot.index]
    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]
    pivot = pivot.loc[models, categories]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        vmin=50,
        vmax=100,
        center=75,
        ax=ax,
        cbar_kws={"label": "Pass Rate (%)"},
        yticklabels=[shorten_model_label(m) for m in models],
        xticklabels=[CATEGORY_LABELS.get(c, c) for c in categories],
    )

    ax.set_title("Pass Rate by Model and Test Category")
    ax.set_xlabel("Test Category")
    ax.set_ylabel("Model")

    plt.tight_layout()
    save_figure(fig, f"pass_rates_heatmap{suffix}")
    plt.close()


def get_model_type_label(model_type: str) -> str:
    """Get display label for model type (30min human only for aggregated plots)."""
    labels = {
        "web_only": "Web Only",
        "all_tools": "All Tools",
        "human_baseline": "Human (30m)",
    }
    return labels.get(model_type, model_type.replace("_", " ").title())


def plot_pass_rates_by_model_type(df: pd.DataFrame):
    """Plot pass rates comparing model types."""
    # Calculate pass rates per model type and category
    grouped = df.groupby(["model_type", "test_category"])["pass"].mean() * 100
    grouped = grouped.unstack(fill_value=0)

    # Reorder categories
    categories = [c for c in CATEGORY_ORDER if c in grouped.columns]
    grouped = grouped[categories]

    # Ensure model type order
    model_types = ["web_only", "all_tools", "human_baseline"]
    model_types = [m for m in model_types if m in grouped.index]
    grouped = grouped.loc[model_types]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Bar positions
    x = np.arange(len(categories))
    width = 0.25

    # Plot bars for each model type
    for i, mt in enumerate(model_types):
        offset = (i - 1) * width
        bars = ax.bar(
            x + offset,
            grouped.loc[mt].values,
            width,
            label=get_model_type_label(mt),
            color=COLORS[mt],
            edgecolor="white",
            linewidth=0.5,
        )

    # Customize
    ax.set_xlabel("Test Category")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Model Type and Test Category")
    ax.set_xticks(x)
    ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
    ax.set_ylim(0, 100)
    ax.legend(title="Model Type")

    plt.tight_layout()
    save_figure(fig, "pass_rates_by_model_type")
    plt.close()


def plot_pass_rates_by_prompt_type(df: pd.DataFrame):
    """Plot pass rates by prompt type (main vs background_work)."""
    # Calculate pass rates per prompt type and model type
    grouped = df.groupby(["prompt_type", "model_type"])["pass"].mean() * 100
    grouped = grouped.unstack(fill_value=0)

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    # Bar positions
    prompt_types = ["main", "background_work"]
    prompt_types = [p for p in prompt_types if p in grouped.index]
    x = np.arange(len(prompt_types))
    width = 0.25

    model_types = ["web_only", "all_tools", "human_baseline"]
    model_types = [m for m in model_types if m in grouped.columns]

    for i, mt in enumerate(model_types):
        offset = (i - 1) * width
        values = [grouped.loc[p, mt] if mt in grouped.columns else 0 for p in prompt_types]
        ax.bar(
            x + offset,
            values,
            width,
            label=get_model_type_label(mt),
            color=COLORS[mt],
            edgecolor="white",
            linewidth=0.5,
        )

    # Customize
    ax.set_xlabel("Prompt Type")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Prompt Type and Model Type (Human = 30min)")
    ax.set_xticks(x)
    ax.set_xticklabels(["Main Prompt", "Background Work"])
    ax.set_ylim(0, 100)
    ax.legend(title="Model Type")

    plt.tight_layout()
    save_figure(fig, "pass_rates_by_prompt_type")
    plt.close()


def plot_pass_rates_by_customer_type(df: pd.DataFrame):
    """Plot pass rates by customer type."""
    # Calculate pass rates per customer type
    pass_rates = df.groupby("customer_type")["pass"].mean() * 100
    pass_rates = pass_rates.sort_values(ascending=False)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Create bars
    colors = [COLORS.get(ct, "#95a5a6") for ct in pass_rates.index]
    x = np.arange(len(pass_rates))
    bars = ax.bar(x, pass_rates.values, color=colors, edgecolor="white", linewidth=0.5)

    # Customize
    ax.set_xlabel("Customer Type")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Customer Type")
    ax.set_xticks(x)
    ax.set_xticklabels(pass_rates.index, rotation=20, ha="right")
    ax.set_ylim(0, 100)

    # Add value labels
    add_value_labels(ax, bars)

    plt.tight_layout()
    save_figure(fig, "pass_rates_by_customer_type")
    plt.close()


def plot_pass_rates_individual_tests_heatmap(df: pd.DataFrame, suffix: str = ""):
    """Plot heatmap of pass rates by model and individual test metrics."""
    # Calculate pass rates by model and metric_name
    pivot = df.pivot_table(
        values="pass",
        index="model_label",
        columns="metric_name",
        aggfunc="mean"
    ) * 100

    # Define metric order (grouped by category)
    METRIC_ORDER = [
        # Work Relevance
        "WORK-RELEVANCE",
        # Source Reliability
        "AFFILIATION-SOURCE-RELIABILITY",
        "INSTITUTION-SOURCE-RELIABILITY",
        "DOMAIN-SOURCE-RELIABILITY",
        "SANCTIONS-SOURCE-RELIABILITY",
        "BACKGROUND_WORK-SOURCE-RELIABILITY",
        # Claim Support
        "AFFILIATION-CLAIM-SUPPORT",
        "INSTITUTION-CLAIM-SUPPORT",
        "DOMAIN-CLAIM-SUPPORT",
        "SANCTIONS-CLAIM-SUPPORT",
        "BACKGROUND_WORK-CLAIM-SUPPORT",
        # Flag Accuracy
        "AFFILIATION-FLAG-ACCURACY",
        "INSTITUTION-FLAG-ACCURACY",
        "DOMAIN-FLAG-ACCURACY",
        "SANCTIONS-FLAG-ACCURACY",
    ]

    # Shorten metric names for display
    METRIC_LABELS = {
        "WORK-RELEVANCE": "Work Relevance",
        "AFFILIATION-SOURCE-RELIABILITY": "Affil. Source",
        "INSTITUTION-SOURCE-RELIABILITY": "Inst. Source",
        "DOMAIN-SOURCE-RELIABILITY": "Domain Source",
        "SANCTIONS-SOURCE-RELIABILITY": "Sanctions Source",
        "BACKGROUND_WORK-SOURCE-RELIABILITY": "BG Work Source",
        "AFFILIATION-CLAIM-SUPPORT": "Affil. Claims",
        "INSTITUTION-CLAIM-SUPPORT": "Inst. Claims",
        "DOMAIN-CLAIM-SUPPORT": "Domain Claims",
        "SANCTIONS-CLAIM-SUPPORT": "Sanctions Claims",
        "BACKGROUND_WORK-CLAIM-SUPPORT": "BG Work Claims",
        "AFFILIATION-FLAG-ACCURACY": "Affil. Flag",
        "INSTITUTION-FLAG-ACCURACY": "Inst. Flag",
        "DOMAIN-FLAG-ACCURACY": "Domain Flag",
        "SANCTIONS-FLAG-ACCURACY": "Sanctions Flag",
    }

    # Reorder
    models = [m for m in MODEL_ORDER if m in pivot.index]
    metrics = [m for m in METRIC_ORDER if m in pivot.columns]
    pivot = pivot.loc[models, metrics]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn",
        vmin=50,
        vmax=100,
        center=75,
        ax=ax,
        cbar_kws={"label": "Pass Rate (%)"},
        yticklabels=[shorten_model_label(m) for m in models],
        xticklabels=[METRIC_LABELS.get(m, m) for m in metrics],
    )

    ax.set_title("Pass Rate by Model and Individual Test Metric")
    ax.set_xlabel("Test Metric")
    ax.set_ylabel("Model")

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    save_figure(fig, f"pass_rates_individual_tests_heatmap{suffix}")
    plt.close()


def main():
    """Generate all pass rate plots."""
    print("Loading data...")
    df_raw = load_tests_data()
    print(f"Loaded {len(df_raw)} test results")

    # Prepare different filtered datasets
    # 1. Full dataset, AI only (for overall AI performance)
    df_ai_full = filter_ai_only(df_raw)
    df_ai_full = filter_for_valid_ground_truth(df_ai_full)
    print(f"AI models on full dataset: {len(df_ai_full)} tests")

    # 2. HB dataset subset, AI + both Human baselines (for individual model plots)
    df_hb_all_humans = filter_hb_dataset_only(df_raw)
    print(f"HB dataset (both human baselines): {len(df_hb_all_humans)} tests")

    # 3. HB dataset subset, AI + Human 30min only (for aggregated plots)
    df_hb_30min = filter_hb_dataset_only(df_raw)
    df_hb_30min = filter_30min_human_only(df_hb_30min)
    print(f"HB dataset (30min human only): {len(df_hb_30min)} tests")

    print("\nGenerating plots...")

    # Plots on full dataset (AI only)
    print("  [AI Full Dataset]")
    plot_pass_rates_by_model(df_ai_full, suffix="_ai_full")
    plot_pass_rates_by_category(df_ai_full, suffix="_ai_full")
    plot_pass_rates_heatmap(df_ai_full, suffix="_ai_full")
    plot_pass_rates_individual_tests_heatmap(df_ai_full, suffix="_ai_full")

    # Individual model plots on HB subset (include both human baselines)
    print("  [HB Subset - Individual Models (both human baselines)]")
    plot_pass_rates_by_model(df_hb_all_humans, suffix="_hb_comparison")
    plot_pass_rates_by_category(df_hb_all_humans, suffix="_hb_comparison")
    plot_pass_rates_heatmap(df_hb_all_humans, suffix="_hb_comparison")
    plot_pass_rates_individual_tests_heatmap(df_hb_all_humans, suffix="_hb_comparison")

    # Aggregated plots on HB subset (use 30min human only)
    print("  [HB Subset - Aggregated (30min human only)]")
    plot_pass_rates_by_model_type(df_hb_30min)
    plot_pass_rates_by_prompt_type(df_hb_30min)

    # Customer type uses full dataset
    plot_pass_rates_by_customer_type(filter_for_valid_ground_truth(df_raw))

    print("\nDone!")


if __name__ == "__main__":
    main()
