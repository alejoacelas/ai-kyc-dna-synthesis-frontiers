#!/usr/bin/env python3
"""
Source usage analysis plots for KYC evaluation results.

Generates:
- Source type distribution
- Sources by model type
- Source count vs pass rate
- Web searches analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from style import (
    DATA_DIR, COLORS, MODEL_ORDER,
    get_model_color, shorten_model_label, save_figure,
    setup_style
)

setup_style()


def load_responses_data():
    """Load the responses dataset."""
    df = pd.read_csv(DATA_DIR / "responses.csv")
    return df


def load_tests_data():
    """Load the tests dataset."""
    df = pd.read_csv(DATA_DIR / "tests.csv")
    df["pass"] = df["pass"].astype(str) == "True"
    return df


def filter_30min_human_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 5min human baseline, keep only 30min."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def get_model_type_label(model_type: str) -> str:
    """Get display label for model type (30min human only for aggregated plots)."""
    labels = {
        "web_only": "Web Only",
        "all_tools": "All Tools",
        "human_baseline": "Human (30m)",
    }
    return labels.get(model_type, model_type.replace("_", " ").title())


def plot_source_type_distribution(df: pd.DataFrame):
    """Plot overall source type distribution."""
    # Calculate totals
    source_totals = {
        "Web": df["num_web_sources"].sum(),
        "EPMC": df["num_epmc_sources"].sum(),
        "ORCID": df["num_orcid_sources"].sum(),
        "Screen": df["num_screen_sources"].sum(),
    }

    # Filter out zeros
    source_totals = {k: v for k, v in source_totals.items() if v > 0}

    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 8))

    colors = [COLORS["web"], COLORS["epmc"], COLORS["orcid"], COLORS["screen"]]
    colors = colors[:len(source_totals)]

    wedges, texts, autotexts = ax.pie(
        source_totals.values(),
        labels=source_totals.keys(),
        autopct=lambda pct: f"{pct:.1f}%\n({int(pct/100*sum(source_totals.values())):,})",
        colors=colors,
        explode=[0.02] * len(source_totals),
        startangle=90,
        textprops={"fontsize": 11},
    )

    ax.set_title("Distribution of Source Types Used")

    plt.tight_layout()
    save_figure(fig, "source_type_distribution")
    plt.close()


def plot_sources_by_model_type(df: pd.DataFrame):
    """Plot source usage by model type."""
    # Calculate averages per model type
    source_cols = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    grouped = df.groupby("model_type")[source_cols].mean()

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    model_types = ["web_only", "all_tools", "human_baseline"]
    model_types = [m for m in model_types if m in grouped.index]
    x = np.arange(len(model_types))
    width = 0.5

    # Colors for source types
    colors = [COLORS["web"], COLORS["epmc"], COLORS["orcid"], COLORS["screen"]]
    labels = ["Web", "EPMC", "ORCID", "Screen"]

    bottom = np.zeros(len(model_types))
    for i, (col, color, label) in enumerate(zip(source_cols, colors, labels)):
        values = grouped.loc[model_types, col].values
        ax.bar(
            x, values, width,
            label=label,
            color=color,
            bottom=bottom,
            edgecolor="white",
        )
        bottom += values

    # Customize
    ax.set_xlabel("Model Type")
    ax.set_ylabel("Average Sources per Response")
    ax.set_title("Source Usage by Model Type (Human = 30min)")
    ax.set_xticks(x)
    ax.set_xticklabels([get_model_type_label(m) for m in model_types])
    ax.legend(title="Source Type")

    plt.tight_layout()
    save_figure(fig, "sources_by_model_type")
    plt.close()


def plot_sources_by_model(df: pd.DataFrame):
    """Plot source usage by model."""
    # Calculate averages per model
    source_cols = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    grouped = df.groupby("model_label")[source_cols].mean()

    # Reorder
    models = [m for m in MODEL_ORDER if m in grouped.index]
    grouped = grouped.loc[models]

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(models))
    width = 0.7

    colors = [COLORS["web"], COLORS["epmc"], COLORS["orcid"], COLORS["screen"]]
    labels = ["Web", "EPMC", "ORCID", "Screen"]

    bottom = np.zeros(len(models))
    for col, color, label in zip(source_cols, colors, labels):
        values = grouped[col].values
        ax.bar(
            x, values, width,
            label=label,
            color=color,
            bottom=bottom,
            edgecolor="white",
        )
        bottom += values

    # Customize
    ax.set_xlabel("Model")
    ax.set_ylabel("Average Sources per Response")
    ax.set_title("Source Usage by Model")
    ax.set_xticks(x)
    ax.set_xticklabels([shorten_model_label(m) for m in models], rotation=45, ha="right")
    ax.legend(title="Source Type", loc="upper right")

    plt.tight_layout()
    save_figure(fig, "sources_by_model")
    plt.close()


def plot_source_count_vs_pass_rate(df_tests: pd.DataFrame):
    """Plot source count vs pass rate."""
    # Bin source counts
    df_tests["source_bin"] = pd.cut(
        df_tests["num_sources_used"],
        bins=[0, 1, 3, 5, 10, 100],
        labels=["0", "1-2", "3-4", "5-9", "10+"],
    )

    # Calculate pass rate per bin
    pass_rates = df_tests.groupby("source_bin", observed=True)["pass"].mean() * 100
    counts = df_tests.groupby("source_bin", observed=True).size()

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(pass_rates))
    bars = ax.bar(x, pass_rates.values, color=COLORS["web"], edgecolor="white")

    # Add count labels
    for bar, count in zip(bars, counts.values):
        ax.annotate(
            f"n={count:,}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Customize
    ax.set_xlabel("Number of Sources Used")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("Pass Rate by Number of Sources")
    ax.set_xticks(x)
    ax.set_xticklabels(pass_rates.index)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    save_figure(fig, "source_count_vs_pass_rate")
    plt.close()


def plot_web_searches_distribution(df: pd.DataFrame):
    """Plot web search count distribution."""
    # Filter AI models
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Box plot by model type
    model_types = ["web_only", "all_tools"]
    data = [df_ai[df_ai["model_type"] == mt]["num_web_searches"] for mt in model_types]
    labels = [mt.replace("_", " ").title() for mt in model_types]

    bp = ax.boxplot(data, labels=labels, patch_artist=True)

    colors = [COLORS[mt] for mt in model_types]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel("Model Type")
    ax.set_ylabel("Number of Web Searches")
    ax.set_title("Web Search Count by Model Type")

    plt.tight_layout()
    save_figure(fig, "web_searches_distribution")
    plt.close()


def plot_source_types_heatmap(df: pd.DataFrame):
    """Plot heatmap of source types by model."""
    source_cols = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]
    col_labels = ["Web", "EPMC", "ORCID", "Screen"]

    # Calculate averages per model
    grouped = df.groupby("model_label")[source_cols].mean()

    # Reorder
    models = [m for m in MODEL_ORDER if m in grouped.index]
    grouped = grouped.loc[models]
    grouped.columns = col_labels

    # Create heatmap
    fig, ax = plt.subplots(figsize=(8, 8))

    sns.heatmap(
        grouped,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        ax=ax,
        cbar_kws={"label": "Avg Sources per Response"},
        yticklabels=[shorten_model_label(m) for m in models],
    )

    ax.set_title("Source Type Usage by Model")
    ax.set_xlabel("Source Type")
    ax.set_ylabel("Model")

    plt.tight_layout()
    save_figure(fig, "source_types_heatmap")
    plt.close()


def main():
    """Generate all source usage plots."""
    print("Loading data...")
    df_responses_raw = load_responses_data()
    df_tests_raw = load_tests_data()
    print(f"Loaded {len(df_responses_raw)} responses and {len(df_tests_raw)} tests")

    # Full data with both human baselines (for individual model plots)
    df_responses_all = df_responses_raw.copy()
    df_tests_all = df_tests_raw.copy()
    print(f"Full data (both human baselines): {len(df_responses_all)} responses, {len(df_tests_all)} tests")

    # 30min human only (for aggregated plots)
    df_responses_30min = filter_30min_human_only(df_responses_raw)
    print(f"30min human only: {len(df_responses_30min)} responses")

    print("\nGenerating plots...")
    # General distribution plots (use all data)
    plot_source_type_distribution(df_responses_all)
    plot_source_count_vs_pass_rate(df_tests_all)

    # Individual model plots (include both human baselines)
    plot_sources_by_model(df_responses_all)
    plot_source_types_heatmap(df_responses_all)

    # Aggregated plots (use 30min human only)
    plot_sources_by_model_type(df_responses_30min)
    plot_web_searches_distribution(df_responses_30min)

    print("\nDone!")


if __name__ == "__main__":
    main()
