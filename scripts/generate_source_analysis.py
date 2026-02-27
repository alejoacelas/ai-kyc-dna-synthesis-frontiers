#!/usr/bin/env python3
"""
Generate source-analysis supplementary figures (FigureI1–FigureI6).

FigureI1: Web searches per customer (bar chart)
FigureI2: Source type composition (stacked bar)
FigureI3: Source types by prompt type (grouped bar)
FigureI4: Sources vs pass rate (scatter)
FigureI5: Effect of tools on pass rates (paired bar)
FigureI6: Claim failure distribution (histogram)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from style import (
    DATA_DIR, COLORS, MODEL_LABELS_NO_TIME, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    setup_style, save_figure, get_model_color, shorten_model_label_no_time,
)


def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


def load_responses():
    return pd.read_csv(DATA_DIR / "responses.csv")


# ---------- FigureI1: Web searches per customer ----------

def figure_i1(responses_df):
    """Bar chart of mean web searches per customer per model."""
    setup_style()

    df = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    # Sum across prompts per customer, then mean across customers
    customer_searches = (
        df.groupby(["customer_name", "model_label"])["num_web_searches"]
        .sum()
        .reset_index()
    )
    model_searches = customer_searches.groupby("model_label")["num_web_searches"].mean()

    models = [m for m in MODEL_ORDER if m in model_searches.index]
    values = [model_searches[m] for m in models]
    colors = [get_model_color(m) for m in models]
    short_labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]

    fig, ax = plt.subplots(figsize=(12, 7))

    bars = ax.bar(
        range(len(models)), values, color=colors, alpha=0.9,
        edgecolor="white", linewidth=0.5,
    )

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{val:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Web Searches per Customer", fontsize=12, fontweight="bold")
    ax.set_title("Average Web Searches per Customer by Model", fontsize=14, fontweight="bold", pad=15)

    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="All Tools (AT)", alpha=0.9),
        Patch(facecolor=COLORS["web_only"], label="Web Only (W)", alpha=0.9),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_val = max(values) if values else 10
    ax.set_ylim(0, max_val * 1.12)

    plt.tight_layout()
    save_figure(fig, "FigureI1")
    plt.close()


# ---------- FigureI2: Source type composition ----------

SOURCE_COLORS = {
    "num_web_sources": COLORS["web"],       # #3498db
    "num_epmc_sources": COLORS["epmc"],     # #9b59b6
    "num_orcid_sources": COLORS["orcid"],   # #f39c12
    "num_screen_sources": COLORS["screen"], # #e74c3c
}
SOURCE_LABELS = {
    "num_web_sources": "Web",
    "num_epmc_sources": "EPMC",
    "num_orcid_sources": "ORCID",
    "num_screen_sources": "Screening DB",
}
SOURCE_COLS = ["num_web_sources", "num_epmc_sources", "num_orcid_sources", "num_screen_sources"]


def figure_i2(responses_df):
    """Stacked bar chart of source type composition per model."""
    setup_style()

    df = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    for col in SOURCE_COLS:
        df[col] = df[col].fillna(0)

    # Sum across prompts per customer, then mean across customers
    customer_sources = (
        df.groupby(["customer_name", "model_label"])[SOURCE_COLS]
        .sum()
        .reset_index()
    )
    model_sources = customer_sources.groupby("model_label")[SOURCE_COLS].mean()

    models = [m for m in MODEL_ORDER if m in model_sources.index]
    model_sources = model_sources.loc[models]
    short_labels = [MODEL_LABELS_NO_TIME.get(m, m) for m in models]

    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(models))
    width = 0.7
    bottom = np.zeros(len(models))

    for col in SOURCE_COLS:
        vals = model_sources[col].values
        ax.bar(
            x, vals, width, bottom=bottom,
            label=SOURCE_LABELS[col], color=SOURCE_COLORS[col], alpha=0.9,
            edgecolor="white", linewidth=0.5,
        )
        bottom += vals

    # Total labels on top
    totals = model_sources[SOURCE_COLS].sum(axis=1).values
    for i, total in enumerate(totals):
        ax.text(
            i, total + 0.3, f"{total:.1f}",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Sources per Customer", fontsize=12, fontweight="bold")
    ax.set_title("Source Type Composition by Model", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_total = totals.max() if len(totals) > 0 else 10
    ax.set_ylim(0, max_total * 1.12)

    plt.tight_layout()
    save_figure(fig, "FigureI2")
    plt.close()


# ---------- FigureI3: Source types by prompt type ----------

def figure_i3(responses_df):
    """Grouped bar chart of source types by prompt type (all-tools models only)."""
    setup_style()

    df = responses_df[
        (responses_df["model_type"] == "all_tools")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    for col in SOURCE_COLS:
        df[col] = df[col].fillna(0)

    # Mean source counts by prompt type across all all-tools models
    prompt_means = df.groupby("prompt_type")[SOURCE_COLS].mean()

    prompt_types = ["main", "background_work"]
    prompt_labels = {"main": "Main Screening", "background_work": "Background Work"}
    prompt_means = prompt_means.loc[[p for p in prompt_types if p in prompt_means.index]]

    fig, ax = plt.subplots(figsize=(10, 7))

    n_sources = len(SOURCE_COLS)
    n_prompts = len(prompt_means)
    width = 0.18
    x = np.arange(n_prompts)

    for j, col in enumerate(SOURCE_COLS):
        offset = (j - (n_sources - 1) / 2) * width
        vals = prompt_means[col].values
        bars = ax.bar(
            x + offset, vals, width,
            label=SOURCE_LABELS[col], color=SOURCE_COLORS[col], alpha=0.9,
            edgecolor="white", linewidth=0.5,
        )
        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels([prompt_labels.get(p, p) for p in prompt_means.index], fontsize=11)
    ax.set_xlabel("Prompt Type", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Sources per Response", fontsize=12, fontweight="bold")
    ax.set_title(
        "Source Types by Prompt Type (All-Tools Models)",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.legend(loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureI3")
    plt.close()


# ---------- FigureI4: Sources vs pass rate ----------

def figure_i4(responses_df, tests_df):
    """Scatter plot of mean total sources vs overall pass rate."""
    setup_style()

    # --- sources from responses ---
    df_resp = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()
    df_resp["num_sources"] = df_resp["num_sources"].fillna(0)

    # Sum across prompts per customer, then mean across customers
    customer_sources = (
        df_resp.groupby(["customer_name", "model_label"])["num_sources"]
        .sum()
        .reset_index()
    )
    model_sources = customer_sources.groupby("model_label")["num_sources"].mean()

    # --- pass rate from tests ---
    df_tests = tests_df[
        (tests_df["model_type"] != "human_baseline")
        & (tests_df["is_human_baseline_dataset"] == True)
    ].copy()
    model_pass = df_tests.groupby("model_label")["pass"].mean() * 100

    # Intersect models
    models = [m for m in MODEL_ORDER if m in model_sources.index and m in model_pass.index]

    fig, ax = plt.subplots(figsize=(10, 6))

    xs = [model_sources[m] for m in models]
    ys = [model_pass[m] for m in models]
    colors = [get_model_color(m) for m in models]

    ax.scatter(xs, ys, c=colors, s=150, edgecolors="white", linewidth=1.5, alpha=0.8)

    for m, xv, yv in zip(models, xs, ys):
        ax.annotate(
            shorten_model_label_no_time(m),
            (xv, yv),
            xytext=(5, 5), textcoords="offset points", fontsize=9,
        )

    ax.set_xlabel("Average Total Sources per Customer", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Sources Used vs Overall Pass Rate", fontsize=12, fontweight="bold")

    legend_elements = [
        Patch(facecolor=COLORS["web_only"], label="Web Only"),
        Patch(facecolor=COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureI4")
    plt.close()


# ---------- FigureI5: Effect of tools on pass rates ----------

def figure_i5(tests_df):
    """Paired bar chart comparing web-only vs all-tools pass rates by category."""
    setup_style()

    df = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    pivot = df.pivot_table(
        values="pass", index="test_category", columns="model_type", aggfunc="mean",
    ) * 100

    categories = [c for c in CATEGORY_ORDER if c in pivot.index]

    web_rates = [pivot.loc[c, "web_only"] for c in categories]
    at_rates = [pivot.loc[c, "all_tools"] for c in categories]
    diffs = [at - web for at, web in zip(at_rates, web_rates)]

    cat_labels = {
        "flag_accuracy": "Flag\nAccuracy",
        "claim_support": "Source\nFidelity",
        "source_reliability": "Source\nQuality",
        "work_relevance": "Work\nRelevance",
    }

    fig, ax = plt.subplots(figsize=(10, 7))

    x = np.arange(len(categories))
    width = 0.35

    bars_web = ax.bar(
        x - width / 2, web_rates, width,
        label="Web Only (W)", color=COLORS["web_only"], alpha=0.9,
    )
    bars_at = ax.bar(
        x + width / 2, at_rates, width,
        label="All Tools (AT)", color=COLORS["all_tools"], alpha=0.9,
    )

    for bar in bars_web:
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{bar.get_height():.1f}%", ha="center", va="bottom",
            fontsize=9, fontweight="bold",
        )
    for bar in bars_at:
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{bar.get_height():.1f}%", ha="center", va="bottom",
            fontsize=9, fontweight="bold",
        )

    # Difference annotations
    for i, diff in enumerate(diffs):
        sign = "+" if diff >= 0 else ""
        color = "#16a34a" if diff >= 0 else "#dc2626"
        y_pos = max(web_rates[i], at_rates[i]) + 2.5
        ax.text(
            x[i], y_pos, f"{sign}{diff:.1f} pp",
            ha="center", va="bottom", fontsize=10, fontweight="bold", color=color,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([cat_labels.get(c, c) for c in categories], fontsize=11)
    ax.set_xlabel("Test Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Effect of Specialized Tools on Pass Rates by Test Category",
        fontsize=14, fontweight="bold", pad=15,
    )

    ax.legend(loc="lower right", fontsize=10)
    ax.set_ylim(70, 100)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureI5")
    plt.close()


# ---------- FigureI6: Claim failure distribution ----------

def figure_i6(tests_df):
    """Histogram of per-customer claim-support failures across AI models."""
    setup_style()

    df = tests_df[
        (tests_df["test_category"] == "claim_support")
        & (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    # Count failures per (customer_name, model_label)
    df["fail"] = ~df["pass"]
    fail_counts = (
        df.groupby(["customer_name", "model_label"])["fail"]
        .sum()
        .reset_index(name="num_failures")
    )

    vals = fail_counts["num_failures"].values
    mean_val = vals.mean()
    median_val = np.median(vals)

    fig, ax = plt.subplots(figsize=(10, 6))

    max_failures = int(vals.max())
    bins = np.arange(-0.5, max_failures + 1.5, 1)

    ax.hist(
        vals, bins=bins, color=COLORS["fail"], alpha=0.85,
        edgecolor="white", linewidth=0.8,
    )

    ax.axvline(mean_val, color="#2c3e50", linestyle="--", linewidth=2, label=f"Mean = {mean_val:.1f}")
    ax.axvline(median_val, color="#8e44ad", linestyle="-.", linewidth=2, label=f"Median = {median_val:.1f}")

    # Stats box
    stats_text = (
        f"N = {len(vals)}\n"
        f"Mean = {mean_val:.2f}\n"
        f"Median = {median_val:.1f}\n"
        f"Std = {vals.std():.2f}\n"
        f"Max = {int(vals.max())}"
    )
    ax.text(
        0.95, 0.95, stats_text,
        transform=ax.transAxes, ha="right", va="top", fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.9),
    )

    ax.set_xlabel("Number of Claim-Support Failures per Customer-Model", fontsize=11, fontweight="bold")
    ax.set_ylabel("Count", fontsize=11, fontweight="bold")
    ax.set_title(
        "Distribution of Claim-Support Failures per Customer",
        fontsize=14, fontweight="bold", pad=15,
    )

    ax.legend(loc="upper left", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureI6")
    plt.close()


# ---------- Main ----------

def main():
    print("Generating source-analysis figures (FigureI1-FigureI6)")
    print("=" * 60)

    tests_df = load_tests()
    responses_df = load_responses()

    figure_i1(responses_df)
    figure_i2(responses_df)
    figure_i3(responses_df)
    figure_i4(responses_df, tests_df)
    figure_i5(tests_df)
    figure_i6(tests_df)

    print("\nDone. All source-analysis figures saved.")


if __name__ == "__main__":
    main()
