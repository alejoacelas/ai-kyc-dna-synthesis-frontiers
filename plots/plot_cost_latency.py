#!/usr/bin/env python3
"""
Cost and latency analysis plots for KYC evaluation results.

Generates:
- Cost distribution by model
- Latency distribution by model
- Cost vs performance scatter
- Token usage analysis
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


def filter_30min_human_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 5min human baseline, keep only 30min."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def plot_cost_by_model(df: pd.DataFrame):
    """Plot cost distribution by model."""
    # Filter out human baseline (cost = 0)
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Calculate mean cost per model
    cost_stats = df_ai.groupby("model_label")["total_cost"].agg(["mean", "std", "median"])

    # Reorder
    models = [m for m in MODEL_ORDER if m in cost_stats.index]
    cost_stats = cost_stats.loc[models]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create bars
    colors = [get_model_color(m) for m in models]
    x = np.arange(len(models))
    bars = ax.bar(
        x, cost_stats["mean"].values,
        yerr=cost_stats["std"].values,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        capsize=3,
        error_kw={"elinewidth": 1, "capthick": 1},
    )

    # Customize
    ax.set_xlabel("Model")
    ax.set_ylabel("Cost per Response ($)")
    ax.set_title("Average Cost per Response by Model")
    ax.set_xticks(x)
    ax.set_xticklabels([shorten_model_label(m) for m in models], rotation=45, ha="right")

    # Add value labels
    for bar, val in zip(bars, cost_stats["mean"].values):
        ax.annotate(
            f"${val:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    save_figure(fig, "cost_by_model")
    plt.close()


def plot_latency_by_model(df: pd.DataFrame):
    """Plot latency distribution by model."""
    # Calculate latency stats per model
    latency_stats = df.groupby("model_label")["latency_ms"].agg(["mean", "median", "std"])
    latency_stats["mean_sec"] = latency_stats["mean"] / 1000
    latency_stats["std_sec"] = latency_stats["std"] / 1000

    # Reorder
    models = [m for m in MODEL_ORDER if m in latency_stats.index]
    latency_stats = latency_stats.loc[models]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create bars
    colors = [get_model_color(m) for m in models]
    x = np.arange(len(models))
    bars = ax.bar(
        x, latency_stats["mean_sec"].values,
        yerr=latency_stats["std_sec"].values,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        capsize=3,
        error_kw={"elinewidth": 1, "capthick": 1},
    )

    # Customize
    ax.set_xlabel("Model")
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Average Response Latency by Model")
    ax.set_xticks(x)
    ax.set_xticklabels([shorten_model_label(m) for m in models], rotation=45, ha="right")

    # Add value labels
    for bar, val in zip(bars, latency_stats["mean_sec"].values):
        ax.annotate(
            f"{val:.1f}s",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
        Patch(facecolor=COLORS["human_baseline"], label="Human Baseline"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    save_figure(fig, "latency_by_model")
    plt.close()


def plot_cost_vs_performance(df: pd.DataFrame):
    """Plot cost vs pass rate scatter."""
    # Filter AI models only
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Calculate aggregates per model
    agg = df_ai.groupby("model_label").agg({
        "total_cost": "mean",
        "num_assertions_passed": "sum",
        "num_assertions": "sum",
    })
    agg["pass_rate"] = agg["num_assertions_passed"] / agg["num_assertions"] * 100

    # Reorder
    models = [m for m in MODEL_ORDER if m in agg.index]
    agg = agg.loc[models]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot
    colors = [get_model_color(m) for m in models]
    scatter = ax.scatter(
        agg["total_cost"],
        agg["pass_rate"],
        c=colors,
        s=150,
        edgecolors="white",
        linewidth=1.5,
        alpha=0.8,
    )

    # Add labels
    for i, model in enumerate(models):
        ax.annotate(
            shorten_model_label(model),
            (agg.loc[model, "total_cost"], agg.loc[model, "pass_rate"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    # Customize
    ax.set_xlabel("Average Cost per Response ($)")
    ax.set_ylabel("Overall Pass Rate (%)")
    ax.set_title("Cost vs Performance Trade-off")

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()
    save_figure(fig, "cost_vs_performance")
    plt.close()


def plot_token_usage(df: pd.DataFrame):
    """Plot token usage by model."""
    # Filter AI models
    df_ai = df[df["model_type"] != "human_baseline"].copy()

    # Calculate token stats per model
    token_stats = df_ai.groupby("model_label").agg({
        "prompt_tokens": "mean",
        "completion_tokens": "mean",
        "total_tokens": "mean",
    })

    # Reorder
    models = [m for m in MODEL_ORDER if m in token_stats.index]
    token_stats = token_stats.loc[models]

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(models))
    width = 0.6

    # Plot prompt and completion tokens as stacked bars
    bars1 = ax.bar(
        x, token_stats["prompt_tokens"] / 1000,
        width,
        label="Prompt Tokens",
        color="#3498db",
        edgecolor="white",
    )
    bars2 = ax.bar(
        x, token_stats["completion_tokens"] / 1000,
        width,
        bottom=token_stats["prompt_tokens"] / 1000,
        label="Completion Tokens",
        color="#2ecc71",
        edgecolor="white",
    )

    # Customize
    ax.set_xlabel("Model")
    ax.set_ylabel("Tokens (thousands)")
    ax.set_title("Average Token Usage per Response")
    ax.set_xticks(x)
    ax.set_xticklabels([shorten_model_label(m) for m in models], rotation=45, ha="right")
    ax.legend()

    plt.tight_layout()
    save_figure(fig, "token_usage")
    plt.close()


def plot_human_time_distribution(df: pd.DataFrame):
    """Plot time distribution for human baseline (both 5min and 30min conditions)."""
    # Filter human baseline with valid times
    df_human = df[df["model_type"] == "human_baseline"].copy()
    df_human = df_human[df_human["time_to_complete_minutes"].notna()]
    df_human["time_to_complete_minutes"] = pd.to_numeric(
        df_human["time_to_complete_minutes"], errors="coerce"
    )
    df_human = df_human.dropna(subset=["time_to_complete_minutes"])

    if len(df_human) == 0:
        print("No human baseline time data available")
        return

    # Ensure we have both conditions
    conditions = ["Human Baseline (5min)", "Human Baseline (30min)"]
    conditions = [c for c in conditions if c in df_human["model_label"].unique()]

    if len(conditions) < 2:
        print(f"Warning: Only found {len(conditions)} human baseline condition(s)")

    # Colors for each condition
    condition_colors = {
        "Human Baseline (5min)": "#e74c3c",   # Red
        "Human Baseline (30min)": "#c0392b",  # Darker red
    }

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Grouped histogram (split by condition)
    # Get data for each condition
    condition_data = {c: df_human[df_human["model_label"] == c]["time_to_complete_minutes"]
                      for c in conditions}

    # Create bins that work for both conditions
    all_times = df_human["time_to_complete_minutes"]
    bins = np.linspace(all_times.min(), all_times.max(), 20)

    # Plot histogram for each condition
    width = (bins[1] - bins[0]) * 0.4  # Width of each bar
    for i, c in enumerate(conditions):
        times = condition_data[c]
        counts, _ = np.histogram(times, bins=bins)
        offset = (i - 0.5) * width
        ax1.bar(
            bins[:-1] + offset + width/2,
            counts,
            width=width,
            label=f"{shorten_model_label(c)} (n={len(times)}, μ={times.mean():.1f}m)",
            color=condition_colors.get(c, COLORS["human_baseline"]),
            edgecolor="white",
            alpha=0.8,
        )

    ax1.set_xlabel("Time to Complete (minutes)")
    ax1.set_ylabel("Count")
    ax1.set_title("Human Baseline Time Distribution by Condition")
    ax1.legend()

    # Panel 2: Box plot by condition (5min vs 30min)
    data = [condition_data[c] for c in conditions]
    labels = [shorten_model_label(c) for c in conditions]

    bp = ax2.boxplot(data, labels=labels, patch_artist=True)
    for patch, c in zip(bp["boxes"], conditions):
        patch.set_facecolor(condition_colors.get(c, COLORS["human_baseline"]))
        patch.set_alpha(0.7)

    # Add mean markers
    for i, c in enumerate(conditions):
        mean_val = condition_data[c].mean()
        ax2.scatter([i + 1], [mean_val], marker='D', color='black', s=50, zorder=5)
        ax2.annotate(
            f"μ={mean_val:.1f}m",
            xy=(i + 1, mean_val),
            xytext=(10, 0),
            textcoords="offset points",
            fontsize=9,
            va="center",
        )

    ax2.set_xlabel("Condition")
    ax2.set_ylabel("Time to Complete (minutes)")
    ax2.set_title("Human Time by Condition")

    plt.tight_layout()
    save_figure(fig, "human_time_distribution")
    plt.close()


def plot_cost_breakdown(df: pd.DataFrame):
    """Plot cost breakdown (model vs web search)."""
    # Filter AI models with cost data
    df_ai = df[df["model_type"] != "human_baseline"].copy()
    df_ai["model_cost"] = pd.to_numeric(df_ai["model_cost"], errors="coerce").fillna(0)
    df_ai["web_search_cost"] = pd.to_numeric(df_ai["web_search_cost"], errors="coerce").fillna(0)

    # Calculate cost breakdown per model type
    cost_breakdown = df_ai.groupby("model_type").agg({
        "model_cost": "mean",
        "web_search_cost": "mean",
        "total_cost": "mean",
    })

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(8, 5))

    model_types = ["web_only", "all_tools"]
    model_types = [m for m in model_types if m in cost_breakdown.index]
    x = np.arange(len(model_types))
    width = 0.5

    bars1 = ax.bar(
        x, cost_breakdown.loc[model_types, "model_cost"],
        width,
        label="Model Cost",
        color="#3498db",
        edgecolor="white",
    )
    bars2 = ax.bar(
        x, cost_breakdown.loc[model_types, "web_search_cost"],
        width,
        bottom=cost_breakdown.loc[model_types, "model_cost"],
        label="Web Search Cost",
        color="#e74c3c",
        edgecolor="white",
    )

    # Customize
    ax.set_xlabel("Model Type")
    ax.set_ylabel("Average Cost ($)")
    ax.set_title("Cost Breakdown by Model Type")
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("_", " ").title() for m in model_types])
    ax.legend()

    plt.tight_layout()
    save_figure(fig, "cost_breakdown")
    plt.close()


def main():
    """Generate all cost and latency plots."""
    print("Loading data...")
    df_raw = load_responses_data()
    print(f"Loaded {len(df_raw)} responses")

    # Full data with both human baselines (for individual model plots)
    df_all = df_raw.copy()
    print(f"Full data (both human baselines): {len(df_all)} responses")

    # 30min human only (for aggregated plots)
    df_30min = filter_30min_human_only(df_raw)
    print(f"30min human only: {len(df_30min)} responses")

    print("\nGenerating plots...")
    # Individual model plots (include both human baselines)
    plot_cost_by_model(df_all)
    plot_latency_by_model(df_all)
    plot_cost_vs_performance(df_all)
    plot_token_usage(df_all)

    # Human time distribution (show both baselines in both panels)
    plot_human_time_distribution(df_all)

    # Aggregated plots (use 30min human only)
    plot_cost_breakdown(df_30min)

    print("\nDone!")


if __name__ == "__main__":
    main()
