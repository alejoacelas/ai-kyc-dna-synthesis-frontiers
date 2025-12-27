#!/usr/bin/env python3
"""
Model comparison plots for KYC evaluation results.

Generates:
- Overall model rankings
- Web-only vs All-Tools comparison
- AI vs Human comparison
- Performance radar chart
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from style import (
    DATA_DIR, COLORS, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    get_model_color, shorten_model_label, save_figure,
    setup_style
)

setup_style()


def get_model_type_label(model_type: str) -> str:
    """Get display label for model type (30min human only for aggregated plots)."""
    labels = {
        "web_only": "Web Only",
        "all_tools": "All Tools",
        "human_baseline": "Human (30m)",
    }
    return labels.get(model_type, model_type.replace("_", " ").title())


def load_data():
    """Load both datasets."""
    df_tests = pd.read_csv(DATA_DIR / "tests.csv")
    df_tests["pass"] = df_tests["pass"].astype(str) == "True"

    df_responses = pd.read_csv(DATA_DIR / "responses.csv")
    return df_tests, df_responses


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


def plot_model_rankings(df_tests: pd.DataFrame, df_responses: pd.DataFrame):
    """Plot overall model rankings with multiple metrics."""
    # Calculate metrics per model
    model_stats = []

    for model in df_tests["model_label"].unique():
        tests = df_tests[df_tests["model_label"] == model]
        responses = df_responses[df_responses["model_label"] == model]

        pass_rate = tests["pass"].mean() * 100
        avg_cost = responses["total_cost"].mean()
        avg_latency = responses["latency_ms"].mean() / 1000  # seconds
        avg_sources = responses["num_sources"].mean()

        model_stats.append({
            "model": model,
            "pass_rate": pass_rate,
            "avg_cost": avg_cost,
            "avg_latency": avg_latency,
            "avg_sources": avg_sources,
            "model_type": tests["model_type"].iloc[0],
        })

    df_stats = pd.DataFrame(model_stats)

    # Sort by pass rate
    df_stats = df_stats.sort_values("pass_rate", ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Horizontal bar chart
    y = np.arange(len(df_stats))
    colors = [get_model_color(m) for m in df_stats["model"]]

    bars = ax.barh(y, df_stats["pass_rate"], color=colors, edgecolor="white", height=0.7)

    # Add value labels
    for bar, row in zip(bars, df_stats.itertuples()):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{row.pass_rate:.1f}%",
            va="center",
            fontsize=10,
        )

    # Customize
    ax.set_xlabel("Overall Pass Rate (%)")
    ax.set_ylabel("Model")
    ax.set_title("Model Rankings by Pass Rate")
    ax.set_yticks(y)
    ax.set_yticklabels([shorten_model_label(m) for m in df_stats["model"]])
    ax.set_xlim(0, 100)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
        Patch(facecolor=COLORS["human_baseline"], label="Human Baseline"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()
    save_figure(fig, "model_rankings")
    plt.close()


def plot_web_vs_alltools(df_tests: pd.DataFrame):
    """Compare Web-Only vs All-Tools performance."""
    # Filter to just AI models
    df_ai = df_tests[df_tests["model_type"].isin(["web_only", "all_tools"])].copy()

    # Get unique model bases (without tool type suffix)
    df_ai["model_base"] = df_ai["model_label"].str.replace(r" \(.*\)", "", regex=True)

    # Calculate pass rates per model base and type
    comparison = df_ai.groupby(["model_base", "model_type"])["pass"].mean() * 100
    comparison = comparison.unstack(fill_value=0)

    if "web_only" not in comparison.columns or "all_tools" not in comparison.columns:
        print("Missing model types for comparison")
        return

    # Calculate improvement
    comparison["improvement"] = comparison["all_tools"] - comparison["web_only"]
    comparison = comparison.sort_values("improvement", ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    y = np.arange(len(comparison))
    height = 0.35

    bars1 = ax.barh(
        y - height/2,
        comparison["web_only"],
        height,
        label="Web Only",
        color=COLORS["web_only"],
        edgecolor="white",
    )
    bars2 = ax.barh(
        y + height/2,
        comparison["all_tools"],
        height,
        label="All Tools",
        color=COLORS["all_tools"],
        edgecolor="white",
    )

    # Add improvement annotations
    for i, (idx, row) in enumerate(comparison.iterrows()):
        improvement = row["improvement"]
        color = "green" if improvement > 0 else "red"
        sign = "+" if improvement > 0 else ""
        ax.annotate(
            f"{sign}{improvement:.1f}pp",
            xy=(max(row["web_only"], row["all_tools"]) + 1, i),
            fontsize=9,
            color=color,
            va="center",
        )

    # Customize
    ax.set_xlabel("Pass Rate (%)")
    ax.set_ylabel("Model")
    ax.set_title("Web-Only vs All-Tools Performance Comparison")
    ax.set_yticks(y)
    ax.set_yticklabels(comparison.index)
    ax.set_xlim(0, 100)
    ax.legend(loc="lower right")

    plt.tight_layout()
    save_figure(fig, "web_vs_alltools")
    plt.close()


def plot_ai_vs_human(df_tests: pd.DataFrame):
    """Compare AI models vs human baseline."""
    # Filter to human baseline dataset only
    df_hb = df_tests[df_tests["is_human_baseline_dataset"] == True].copy()

    if len(df_hb) == 0:
        print("No human baseline data available")
        return

    # Calculate pass rates by category and model type
    grouped = df_hb.groupby(["test_category", "model_type"])["pass"].mean() * 100
    grouped = grouped.unstack(fill_value=0)

    # Ensure we have all categories
    categories = [c for c in CATEGORY_ORDER if c in grouped.index]
    grouped = grouped.loc[categories]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(categories))
    width = 0.25

    model_types = ["web_only", "all_tools", "human_baseline"]
    model_types = [m for m in model_types if m in grouped.columns]

    for i, mt in enumerate(model_types):
        offset = (i - 1) * width
        ax.bar(
            x + offset,
            grouped[mt],
            width,
            label=get_model_type_label(mt),
            color=COLORS[mt],
            edgecolor="white",
        )

    # Customize
    ax.set_xlabel("Test Category")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title("AI vs Human Performance (Human = 30min)")
    ax.set_xticks(x)
    ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
    ax.set_ylim(0, 100)
    ax.legend(title="Model Type")

    plt.tight_layout()
    save_figure(fig, "ai_vs_human")
    plt.close()


def plot_performance_radar(df_tests: pd.DataFrame, df_responses: pd.DataFrame):
    """Create radar chart comparing top models."""
    # Calculate normalized metrics per model
    model_metrics = []

    for model in df_tests["model_label"].unique():
        tests = df_tests[df_tests["model_label"] == model]
        responses = df_responses[df_responses["model_label"] == model]

        # Get pass rates by category
        category_rates = {}
        for cat in CATEGORY_ORDER:
            cat_tests = tests[tests["test_category"] == cat]
            if len(cat_tests) > 0:
                category_rates[cat] = cat_tests["pass"].mean() * 100

        if len(category_rates) >= 3:  # Need at least 3 categories
            model_metrics.append({
                "model": model,
                "model_type": tests["model_type"].iloc[0],
                **category_rates,
            })

    df_metrics = pd.DataFrame(model_metrics)

    # Select top performing models (by average pass rate)
    categories = [c for c in CATEGORY_ORDER if c in df_metrics.columns]
    df_metrics["avg_pass"] = df_metrics[categories].mean(axis=1)
    df_metrics = df_metrics.nlargest(5, "avg_pass")

    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection="polar"))

    # Angles for each category
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    # Plot each model
    for _, row in df_metrics.iterrows():
        values = [row[cat] for cat in categories]
        values += values[:1]  # Complete the circle

        color = get_model_color(row["model"])
        ax.plot(angles, values, "o-", linewidth=2, label=shorten_model_label(row["model"]), color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    # Customize
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories])
    ax.set_ylim(0, 100)
    ax.set_title("Top 5 Models - Performance by Category", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    save_figure(fig, "performance_radar")
    plt.close()


def plot_efficiency_comparison(df_tests: pd.DataFrame, df_responses: pd.DataFrame):
    """Plot efficiency comparison (pass rate per dollar)."""
    # Calculate metrics per model
    model_stats = []

    for model in df_tests["model_label"].unique():
        tests = df_tests[df_tests["model_label"] == model]
        responses = df_responses[df_responses["model_label"] == model]

        pass_rate = tests["pass"].mean() * 100
        avg_cost = responses["total_cost"].mean()

        if avg_cost > 0:  # Exclude human baseline
            efficiency = pass_rate / avg_cost
            model_stats.append({
                "model": model,
                "pass_rate": pass_rate,
                "avg_cost": avg_cost,
                "efficiency": efficiency,
                "model_type": tests["model_type"].iloc[0],
            })

    df_stats = pd.DataFrame(model_stats)
    df_stats = df_stats.sort_values("efficiency", ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    y = np.arange(len(df_stats))
    colors = [get_model_color(m) for m in df_stats["model"]]

    bars = ax.barh(y, df_stats["efficiency"], color=colors, edgecolor="white", height=0.7)

    # Customize
    ax.set_xlabel("Efficiency (Pass Rate % per $)")
    ax.set_ylabel("Model")
    ax.set_title("Model Efficiency (Pass Rate per Dollar Spent)")
    ax.set_yticks(y)
    ax.set_yticklabels([shorten_model_label(m) for m in df_stats["model"]])

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()
    save_figure(fig, "efficiency_comparison")
    plt.close()


def main():
    """Generate all model comparison plots."""
    print("Loading data...")
    df_tests_raw, df_responses_raw = load_data()
    print(f"Loaded {len(df_tests_raw)} tests and {len(df_responses_raw)} responses")

    # Prepare filtered datasets
    # HB dataset subset with both human baselines (for individual model plots)
    df_tests_hb_all = filter_hb_dataset_only(df_tests_raw)
    df_responses_hb_all = filter_hb_dataset_only(df_responses_raw)
    print(f"HB dataset (both human baselines): {len(df_tests_hb_all)} tests, {len(df_responses_hb_all)} responses")

    # HB dataset subset with 30min human only (for aggregated plots)
    df_tests_hb_30min = filter_hb_dataset_only(df_tests_raw)
    df_tests_hb_30min = filter_30min_human_only(df_tests_hb_30min)
    print(f"HB dataset (30min human only): {len(df_tests_hb_30min)} tests")

    # AI only on full dataset (for efficiency comparison without human)
    df_tests_ai = filter_ai_only(df_tests_raw)
    df_tests_ai = filter_for_valid_ground_truth(df_tests_ai)
    df_responses_ai = filter_ai_only(df_responses_raw)
    print(f"AI models full dataset: {len(df_tests_ai)} tests, {len(df_responses_ai)} responses")

    print("\nGenerating plots...")
    # Individual model plots (use HB subset with both human baselines)
    plot_model_rankings(df_tests_hb_all, df_responses_hb_all)
    plot_performance_radar(df_tests_hb_all, df_responses_hb_all)

    # Aggregated plots (use HB subset with 30min human only)
    plot_ai_vs_human(df_tests_hb_30min)

    # AI-only comparisons
    plot_web_vs_alltools(df_tests_ai)
    plot_efficiency_comparison(df_tests_ai, df_responses_ai)

    print("\nDone!")


if __name__ == "__main__":
    main()
