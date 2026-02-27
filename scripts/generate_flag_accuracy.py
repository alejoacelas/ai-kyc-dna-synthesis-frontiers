#!/usr/bin/env python3
"""
Generate flag accuracy appendix figures (FigureG1–FigureG9).

FigureG1: Ground truth flag distribution (stacked bar)
FigureG2: Extracted flag distribution (3 heatmaps)
FigureG3: FP/FN/Undetermined rates (2x2 subplot)
FigureG4: Confusion matrices (2x2 subplot)
FigureG5: Human vs AI error rates (grouped bars)
FigureG6: Error rate by criterion and screener type (grouped bars)
FigureG7: Error category by screener type (100% stacked bar)
FigureG8: Error category by criterion and screener type (100% stacked detailed)
FigureG9: Flag error rate by order (horizontal bar)
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Patch

from style import (
    DATA_DIR,
    COLORS,
    MODEL_LABELS_NO_TIME,
    MODEL_ORDER,
    FLAG_ORDER,
    FLAG_LABELS,
    setup_style,
    save_figure,
    shorten_model_label_no_time,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

GT_COLUMNS = {
    "affiliation": "ground_truth_affiliation",
    "institution": "ground_truth_institution",
    "domain": "ground_truth_domain",
    "sanctions": "ground_truth_sanctions",
}

METRIC_CONFIG = {
    "AFFILIATION-FLAG-ACCURACY": {"gt_col": "ground_truth_affiliation", "criterion": "affiliation"},
    "INSTITUTION-FLAG-ACCURACY": {"gt_col": "ground_truth_institution", "criterion": "institution"},
    "DOMAIN-FLAG-ACCURACY": {"gt_col": "ground_truth_domain", "criterion": "domain"},
    "SANCTIONS-FLAG-ACCURACY": {"gt_col": "ground_truth_sanctions", "criterion": "sanctions"},
}

METRIC_TO_CRITERION = {k: v["criterion"] for k, v in METRIC_CONFIG.items()}

FLAG_VALUE_COLORS = {"FLAG": "#e74c3c", "NO FLAG": "#27ae60", "UNDETERMINED": "#95a5a6"}
FLAG_VALUES = ["FLAG", "NO FLAG", "UNDETERMINED"]
FLAG_CATEGORIES = ["FLAG", "NO FLAG", "UNDETERMINED"]

ERROR_COLORS_FP_FN = {"FP": "#e74c3c", "FN": "#3498db", "UND": "#95a5a6"}

ERROR_LABELS_BY_CRITERION = {
    "empty_response": "Empty Response",
    "flag_instructions_not_followed": "Instructions Not Followed",
    "information_not_found": "Information Not Found",
    "difference_in_judgment": "Judgment Difference",
    "factual_mistake": "Factual Mistake",
    None: "Uncategorized",
}
ERROR_COLORS_BY_CRITERION = {
    "empty_response": "#66c2a5",
    "flag_instructions_not_followed": "#fc8d62",
    "information_not_found": "#8da0cb",
    "difference_in_judgment": "#e78ac3",
    "factual_mistake": "#a6d854",
    None: "#b3b3b3",
}
ERROR_ORDER = [
    "empty_response",
    "flag_instructions_not_followed",
    "information_not_found",
    "difference_in_judgment",
    "factual_mistake",
    None,
]

SCREENER_COLORS = {"Human": "#f59e0b", "All Tools": "#1e40af", "Web Only": "#93c5fd"}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


def _classify_provider_type(provider: str):
    """Map a provider / model_label string to a screener bucket."""
    if "Human" in provider and "5min" not in provider:
        return "Human"
    elif "Human" in provider and "5min" in provider:
        return None  # skip 5-min human baseline
    elif "(All Tools)" in provider:
        return "All Tools"
    else:
        return "Web Only"


def _metric_to_flag(metric: str):
    """Map a metric_name to its flag criterion key."""
    upper = metric.upper()
    if "AFFILIATION" in upper:
        return "affiliation"
    elif "INSTITUTION" in upper:
        return "institution"
    elif "DOMAIN" in upper:
        return "domain"
    elif "SANCTIONS" in upper:
        return "sanctions"
    return None


def _load_error_data(tests_df):
    """Load flag_error_comments.json and compute merged error rates.

    Returns (error_data, df_errors_filtered) where:
      * error_data has columns [flag_type, screener_type, errorCategory,
        error_count, total, error_rate]
      * df_errors_filtered is the DataFrame of individual error records with a
        ``screener_type`` column (5-min baseline removed).
    """
    error_path = DATA_DIR / "annotations" / "flag_error_comments.json"
    with open(error_path) as f:
        raw = json.load(f)
    df_errors = pd.DataFrame(raw["records"])

    # Remove 5-min human baseline
    df_errors = df_errors[~df_errors["provider"].str.contains("5min", case=False, na=False)].copy()
    df_errors["screener_type"] = df_errors["provider"].apply(_classify_provider_type)
    df_errors = df_errors[df_errors["screener_type"].notna()]

    # Totals from tests.csv
    df_flag_tests = tests_df[
        (tests_df["test_category"] == "flag_accuracy")
        & (tests_df["is_human_baseline_dataset"] == True)
    ].copy()
    df_flag_tests = df_flag_tests[~df_flag_tests["model_label"].str.contains("5min", case=False, na=False)]
    df_flag_tests["screener_type"] = df_flag_tests["model_label"].apply(_classify_provider_type)
    df_flag_tests["flag_type"] = df_flag_tests["metric_name"].apply(_metric_to_flag)
    df_flag_tests = df_flag_tests[df_flag_tests["flag_type"].notna()]

    total_counts = df_flag_tests.groupby(["flag_type", "screener_type"]).size().reset_index(name="total")

    error_counts = (
        df_errors.groupby(["flagType", "screener_type", "errorCategory"])
        .size()
        .reset_index(name="error_count")
        .rename(columns={"flagType": "flag_type"})
    )

    merged = error_counts.merge(total_counts, on=["flag_type", "screener_type"], how="left")
    merged["error_rate"] = merged["error_count"] / merged["total"] * 100

    return merged, df_errors


# ---------------------------------------------------------------------------
# FigureG1: Ground truth flag distribution (stacked bar)
# ---------------------------------------------------------------------------

def figure_g1(tests_df):
    setup_style()

    df_hb = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    # Deduplicate: pick the most frequent model to get one row per customer
    sample_model = df_hb["model_label"].value_counts().idxmax()
    df_unique = df_hb[df_hb["model_label"] == sample_model].copy()
    df_flags = df_unique[df_unique["test_category"] == "flag_accuracy"].copy()

    metric_map = {
        "affiliation": "AFFILIATION-FLAG-ACCURACY",
        "institution": "INSTITUTION-FLAG-ACCURACY",
        "domain": "DOMAIN-FLAG-ACCURACY",
        "sanctions": "SANCTIONS-FLAG-ACCURACY",
    }

    records = []
    for crit in FLAG_ORDER:
        gt_col = GT_COLUMNS[crit]
        crit_data = df_flags[df_flags["metric_name"] == metric_map[crit]]
        value_counts = crit_data[gt_col].value_counts()
        for fv in FLAG_VALUES:
            records.append({
                "criterion": crit,
                "flag_value": fv,
                "count": value_counts.get(fv, 0),
            })

    results_df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(FLAG_ORDER))
    bar_width = 0.55
    bottom = np.zeros(len(FLAG_ORDER))

    for fv in FLAG_VALUES:
        counts = np.array([
            results_df.loc[
                (results_df["criterion"] == crit) & (results_df["flag_value"] == fv), "count"
            ].values[0]
            for crit in FLAG_ORDER
        ])
        bars = ax.bar(
            x, counts, bar_width, bottom=bottom, label=fv,
            color=FLAG_VALUE_COLORS[fv], alpha=0.85, edgecolor="white", linewidth=0.5,
        )
        for bar, count, bot in zip(bars, counts, bottom):
            if count > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bot + count / 2,
                    str(int(count)), ha="center", va="center",
                    fontsize=11, fontweight="bold",
                    color="white" if fv != "UNDETERMINED" else "black",
                )
        bottom += counts

    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS[c] for c in FLAG_ORDER], fontsize=12)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Profiles", fontsize=12, fontweight="bold")
    ax.set_title("Ground Truth Flag Distribution Across 40 Profiles",
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureG1")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG2: Extracted flag distribution (3 heatmaps)
# ---------------------------------------------------------------------------

def figure_g2(tests_df):
    setup_style()

    df_flag = tests_df[
        (tests_df["test_category"] == "flag_accuracy")
        & (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    df_flag["criterion"] = df_flag["metric_name"].map(METRIC_TO_CRITERION)

    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    df_flag = df_flag[df_flag["model_label"].isin(ai_model_order)]

    flag_titles = ["FLAG (%)", "NO FLAG (%)", "UNDETERMINED (%)"]
    cmaps = ["Reds", "Greens", "Greys"]

    pivots = {}
    for fv in FLAG_VALUES:
        records = []
        for model in ai_model_order:
            for crit in FLAG_ORDER:
                subset = df_flag[
                    (df_flag["model_label"] == model) & (df_flag["criterion"] == crit)
                ]
                total = len(subset)
                count = (subset["extracted_flag"] == fv).sum()
                pct = (count / total * 100) if total > 0 else 0.0
                records.append({
                    "model": shorten_model_label_no_time(model),
                    "criterion": FLAG_LABELS[crit],
                    "pct": pct,
                })
        pivot = pd.DataFrame(records).pivot(index="model", columns="criterion", values="pct")
        row_order = [shorten_model_label_no_time(m) for m in ai_model_order]
        col_order = [FLAG_LABELS[c] for c in FLAG_ORDER]
        pivot = pivot.reindex(index=row_order, columns=col_order)
        pivots[fv] = pivot

    fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)

    for idx, (fv, title, cmap) in enumerate(zip(FLAG_VALUES, flag_titles, cmaps)):
        ax = axes[idx]
        sns.heatmap(
            pivots[fv], ax=ax, annot=True, fmt=".1f", cmap=cmap,
            vmin=0, vmax=100, linewidths=0.5, linecolor="white",
            cbar_kws={"label": "%", "shrink": 0.8}, annot_kws={"fontsize": 9},
        )
        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("")
        ax.set_ylabel("Model" if idx == 0 else "", fontsize=12)
        ax.tick_params(axis="x", rotation=0)
        ax.tick_params(axis="y", rotation=0)

    fig.suptitle(
        "Distribution of Extracted Flag Values by Model and Criterion\n"
        "(AI Models, Human Baseline Dataset)",
        fontsize=14, fontweight="bold", y=1.03,
    )

    plt.tight_layout()
    save_figure(fig, "FigureG2")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG3: FP/FN/Undetermined rates (2x2 subplot)
# ---------------------------------------------------------------------------

def _classify_fp_fn(row):
    """Classify a flag-accuracy row into FP, FN, UND, or correct."""
    config = METRIC_CONFIG.get(row["metric_name"])
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


def figure_g3(tests_df):
    setup_style()

    df_flag = tests_df[
        (tests_df["test_category"] == "flag_accuracy")
        & (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    df_flag["criterion"] = df_flag["metric_name"].map(METRIC_TO_CRITERION)
    df_flag["error_type"] = df_flag.apply(_classify_fp_fn, axis=1)

    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]
    df_flag = df_flag[df_flag["model_label"].isin(ai_model_order)]

    error_types = ["FP", "FN", "UND"]
    error_labels = {"FP": "False Positive", "FN": "False Negative", "UND": "Undetermined"}

    # Compute rates
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
                results.append({
                    "model": model,
                    "model_short": shorten_model_label_no_time(model),
                    "criterion": crit,
                    "error_type": et,
                    "rate": rate,
                })

    results_df = pd.DataFrame(results)

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
            rates = []
            for model in ai_model_order:
                row = et_data[et_data["model"] == model]
                rates.append(row["rate"].values[0] if len(row) > 0 else 0.0)

            offset = (et_idx - 1) * bar_width
            bars = ax.bar(
                x + offset, rates, bar_width, label=error_labels[et],
                color=ERROR_COLORS_FP_FN[et], alpha=0.85, edgecolor="white", linewidth=0.5,
            )
            for bar, val in zip(bars, rates):
                if val > 1.0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        f"{val:.1f}", ha="center", va="bottom", fontsize=7,
                    )

        ax.set_title(FLAG_LABELS[crit], fontsize=13, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(short_labels, fontsize=8, rotation=45, ha="right")
        ax.set_ylabel("Rate (%)")
        ax.grid(True, axis="y", alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if idx == 0:
            ax.legend(fontsize=9, loc="upper right")

    fig.suptitle(
        "False Positive, False Negative, and Undetermined Rates per Model\n"
        "(By Flag Criterion, AI Models, Human Baseline Dataset)",
        fontsize=14, fontweight="bold", y=1.02,
    )

    plt.tight_layout()
    save_figure(fig, "FigureG3")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG4: Confusion matrices (2x2 subplot)
# ---------------------------------------------------------------------------

def _get_ground_truth(row):
    config = METRIC_CONFIG.get(row["metric_name"])
    if config is None:
        return None
    return row[config["gt_col"]]


def figure_g4(tests_df):
    setup_style()

    ai_model_order = [m for m in MODEL_ORDER if "Human" not in m]

    df_flag = tests_df[
        (tests_df["test_category"] == "flag_accuracy")
        & (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_label"].isin(ai_model_order))
    ].copy()

    df_flag["criterion"] = df_flag["metric_name"].map(METRIC_TO_CRITERION)
    df_flag["ground_truth"] = df_flag.apply(_get_ground_truth, axis=1)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes_flat = axes.flatten()

    for idx, crit in enumerate(FLAG_ORDER):
        ax = axes_flat[idx]
        subset = df_flag[df_flag["criterion"] == crit]

        cm = pd.crosstab(
            subset["ground_truth"], subset["extracted_flag"],
            rownames=["Ground Truth"], colnames=["Predicted"],
        )
        cm = cm.reindex(index=FLAG_CATEGORIES, columns=FLAG_CATEGORIES, fill_value=0)
        cm_values = cm.values

        row_sums = cm_values.sum(axis=1, keepdims=True)
        row_sums_safe = np.where(row_sums == 0, 1, row_sums)
        cm_pct = cm_values / row_sums_safe * 100

        annot = np.empty_like(cm_values, dtype=object)
        for i in range(cm_values.shape[0]):
            for j in range(cm_values.shape[1]):
                annot[i, j] = f"{cm_values[i, j]}\n({cm_pct[i, j]:.1f}%)"

        sns.heatmap(
            cm_values, ax=ax, annot=annot, fmt="", cmap="Blues",
            xticklabels=FLAG_CATEGORIES, yticklabels=FLAG_CATEGORIES,
            linewidths=1, linecolor="white",
            cbar_kws={"shrink": 0.7}, annot_kws={"fontsize": 10},
        )
        ax.set_title(FLAG_LABELS[crit], fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("Ground Truth" if idx % 2 == 0 else "", fontsize=11)
        ax.tick_params(axis="x", rotation=30)
        ax.tick_params(axis="y", rotation=0)

    fig.suptitle(
        "Flag Accuracy Confusion Matrices by Criterion\n"
        "(Aggregated Across All AI Models, Human Baseline Dataset)",
        fontsize=14, fontweight="bold", y=1.02,
    )

    plt.tight_layout()
    save_figure(fig, "FigureG4")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG5: Human vs AI error rates (grouped bars)
# ---------------------------------------------------------------------------

def figure_g5(tests_df):
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    # Map metric_name to flag task
    task_map = {
        "AFFILIATION-FLAG-ACCURACY": "affiliation",
        "INSTITUTION-FLAG-ACCURACY": "institution",
        "DOMAIN-FLAG-ACCURACY": "domain",
        "SANCTIONS-FLAG-ACCURACY": "sanctions",
    }

    tasks_data = []
    for _, row in df.iterrows():
        task = task_map.get(row["metric_name"])
        if task is None:
            continue
        tasks_data.append({
            "task": task,
            "model_label": row["model_label"],
            "pass": row["pass"],
            "is_human_baseline": row["is_human_baseline"],
        })
    df_tasks = pd.DataFrame(tasks_data)

    # Performance per (task, model)
    perf = df_tasks.groupby(["task", "model_label"])["pass"].agg(["count", "sum"]).reset_index()
    perf["error_rate_pct"] = (1 - perf["sum"] / perf["count"]) * 100

    # Best / worst AI per task
    results = {}
    for task in perf["task"].unique():
        td = perf[perf["task"] == task]
        human = td[td["model_label"] == "Human Baseline (30min)"]
        human_err = human["error_rate_pct"].iloc[0] if len(human) > 0 else 0.0
        ai = td[~td["model_label"].str.contains("Human Baseline")]
        if len(ai) == 0:
            continue
        results[task] = {
            "human_error": human_err,
            "best_error": ai["error_rate_pct"].min(),
            "worst_error": ai["error_rate_pct"].max(),
        }

    task_order = ["affiliation", "institution", "domain", "sanctions"]
    task_labels = {
        "affiliation": "Institutional\nAffiliation",
        "institution": "Institution\nType",
        "domain": "Email\nDomain",
        "sanctions": "Sanctions",
    }

    x_pos = np.arange(len(task_order))
    width = 0.35

    human_errors = [results.get(t, {}).get("human_error", 0) for t in task_order]
    best_errors = [results.get(t, {}).get("best_error", 0) for t in task_order]
    worst_errors = [results.get(t, {}).get("worst_error", 0) for t in task_order]
    ai_range = [w - b for w, b in zip(worst_errors, best_errors)]

    fig, ax = plt.subplots(figsize=(12, 8))

    bars_human = ax.bar(
        x_pos - width / 2, human_errors, width,
        label="Human baseline", color=SCREENER_COLORS["Human"], alpha=0.9,
    )
    bars_best = ax.bar(
        x_pos + width / 2, best_errors, width,
        label="Lowest Error from AI Screener", color=SCREENER_COLORS["All Tools"], alpha=0.9,
    )
    ax.bar(
        x_pos + width / 2, ai_range, width, bottom=best_errors,
        label="Highest Error from AI Screener", color=SCREENER_COLORS["Web Only"], alpha=0.9,
    )

    ax.set_xlabel("Flag Accuracy Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Error Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Human vs AI Error Rates by Flag Accuracy Criterion",
                 fontsize=14, fontweight="bold", pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([task_labels[t] for t in task_order], rotation=45, ha="right")

    max_error = max(max(human_errors), max(worst_errors))
    ax.set_ylim(0, max_error * 1.15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val:.0f}%"))

    for bar in bars_human:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    for i, bar_best in enumerate(bars_best):
        bv, wv = best_errors[i], worst_errors[i]
        ax.text(bar_best.get_x() + bar_best.get_width() / 2, wv + 0.5,
                f"{bv:.1f}-{wv:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.3, axis="y")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureG5")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG6: Error rate by criterion and screener type (grouped bars)
# ---------------------------------------------------------------------------

def figure_g6(error_data):
    setup_style()

    fig, ax = plt.subplots(figsize=(10, 6))

    screener_types = ["Human", "All Tools", "Web Only"]
    n_flags = len(FLAG_ORDER)
    bar_width = 0.25
    x = np.arange(n_flags)

    for s_idx, screener in enumerate(screener_types):
        error_rates = []
        for flag in FLAG_ORDER:
            subset = error_data[
                (error_data["flag_type"] == flag) & (error_data["screener_type"] == screener)
            ]
            error_rates.append(subset["error_rate"].sum())

        offset = (s_idx - 1) * bar_width
        bars = ax.bar(
            x + offset, error_rates, bar_width,
            label=screener if screener != "Human" else "Human baseline",
            color=SCREENER_COLORS[screener], alpha=0.85, edgecolor="white", linewidth=0.5,
        )
        for bar, rate in zip(bars, error_rates):
            if rate > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        f"{rate:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in FLAG_ORDER], fontsize=11)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Error Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 22)
    ax.set_title("Error Rate by Flag Criterion and Screener Type",
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureG6")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG7: Error category by screener type (100% stacked bar)
# ---------------------------------------------------------------------------

def figure_g7(df_errors):
    setup_style()

    fig, ax = plt.subplots(figsize=(8, 6))

    screener_types = ["Human", "All Tools", "Web Only"]
    screener_labels = ["Human\nbaseline", "All Tools", "Web Only"]

    ordered_cats = [c for c in ERROR_ORDER if c in df_errors["errorCategory"].unique()]

    pivot = pd.crosstab(df_errors["screener_type"], df_errors["errorCategory"])
    pivot = pivot.loc[[s for s in screener_types if s in pivot.index]]
    pivot = pivot[[c for c in ordered_cats if c in pivot.columns]]
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    x = np.arange(len(screener_types))
    bar_width = 0.5
    bottom = np.zeros(len(screener_types))

    for cat in ordered_cats:
        if cat in pivot_pct.columns:
            values = pivot_pct[cat].values
            ax.bar(
                x, values, bar_width, bottom=bottom,
                label=ERROR_LABELS_BY_CRITERION.get(cat, str(cat)),
                color=ERROR_COLORS_BY_CRITERION.get(cat, "#6b7280"),
                alpha=0.85, edgecolor="white", linewidth=0.5,
            )
            bottom += values

    ax.set_xticks(x)
    ax.set_xticklabels(screener_labels, fontsize=11)
    ax.set_xlabel("Screener Type", fontsize=12, fontweight="bold")
    ax.set_ylabel("Percentage of Errors (%)", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_title("Error Category Distribution by Screener Type",
                 fontsize=14, fontweight="bold", pad=15)

    error_legend = [
        Patch(facecolor=ERROR_COLORS_BY_CRITERION.get(cat, "#b3b3b3"),
              label=ERROR_LABELS_BY_CRITERION.get(cat, str(cat)), alpha=0.85)
        for cat in ordered_cats if cat in pivot_pct.columns
    ]
    ax.legend(
        handles=error_legend, loc="center left", bbox_to_anchor=(1.02, 0.5),
        fontsize=9, title="Error Category", title_fontsize=10, frameon=True,
    )

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureG7")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG8: Error category by criterion and screener type (100% stacked detailed)
# ---------------------------------------------------------------------------

def figure_g8(df_errors):
    setup_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    screener_types = ["Human", "All Tools", "Web Only"]
    n_flags = len(FLAG_ORDER)
    bar_width = 0.25
    x = np.arange(n_flags)

    ordered_cats = [c for c in ERROR_ORDER if c in df_errors["errorCategory"].unique()]

    for s_idx, screener in enumerate(screener_types):
        screener_data = df_errors[df_errors["screener_type"] == screener]
        pivot = pd.crosstab(screener_data["flagType"], screener_data["errorCategory"])

        full_pivot = pd.DataFrame(0, index=FLAG_ORDER, columns=ordered_cats)
        for f in FLAG_ORDER:
            for c in ordered_cats:
                if f in pivot.index and c in pivot.columns:
                    full_pivot.loc[f, c] = pivot.loc[f, c]

        row_sums = full_pivot.sum(axis=1)
        pivot_pct = full_pivot.div(row_sums.replace(0, 1), axis=0) * 100

        offset = (s_idx - 1) * bar_width
        bottom = np.zeros(n_flags)

        for cat_idx, cat in enumerate(ordered_cats):
            values = pivot_pct[cat].values
            label = ERROR_LABELS_BY_CRITERION.get(cat, str(cat)) if s_idx == 0 else None
            ax.bar(
                x + offset, values, bar_width, bottom=bottom, label=label,
                color=ERROR_COLORS_BY_CRITERION.get(cat, "#95a5a6"),
                alpha=0.85, edgecolor="white", linewidth=0.5,
            )
            bottom += values

    # Screener type labels above bars
    for f_idx in range(n_flags):
        for s_idx, screener in enumerate(screener_types):
            offset = (s_idx - 1) * bar_width
            short_label = "H" if screener == "Human" else ("AT" if screener == "All Tools" else "W")
            ax.text(
                x[f_idx] + offset, 103, short_label,
                ha="center", va="bottom", fontsize=8,
                color=SCREENER_COLORS[screener], fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels([FLAG_LABELS.get(f, f) for f in FLAG_ORDER], fontsize=11)
    ax.set_xlabel("Flag Criterion", fontsize=12, fontweight="bold")
    ax.set_ylabel("Percentage of Errors (%)", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 115)
    ax.set_title("Error Category Distribution by Flag Criterion and Screener Type",
                 fontsize=14, fontweight="bold", pad=15)

    error_legend = [
        Patch(facecolor=ERROR_COLORS_BY_CRITERION.get(cat, "#b3b3b3"),
              label=ERROR_LABELS_BY_CRITERION.get(cat, str(cat)), alpha=0.85)
        for cat in ordered_cats
    ]
    ax.legend(
        handles=error_legend, loc="upper left", fontsize=9,
        title="Error Category", title_fontsize=10,
    )

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureG8")
    plt.close()


# ---------------------------------------------------------------------------
# FigureG9: Flag error rate by order (horizontal bar)
# ---------------------------------------------------------------------------

def figure_g9(tests_df):
    setup_style()

    df_flag = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
        & (tests_df["test_category"] == "flag_accuracy")
    ].copy()

    order_error = df_flag.groupby("order")["pass"].mean().reset_index()
    order_error["error_rate"] = (1 - order_error["pass"]) * 100
    order_error = order_error.sort_values("error_rate", ascending=True).reset_index(drop=True)

    n = len(order_error)
    fig, ax = plt.subplots(figsize=(10, max(6, n * 0.45)))

    cmap = LinearSegmentedColormap.from_list("reds", ["#f5b7b1", "#c0392b", "#7b241c"])
    vmax = max(order_error["error_rate"].max() + 2, 10)
    norm = Normalize(vmin=0, vmax=vmax)

    colors = [cmap(norm(v)) for v in order_error["error_rate"]]

    bars = ax.barh(
        range(n), order_error["error_rate"],
        color=colors, edgecolor="white", linewidth=0.5, height=0.75,
    )

    for i, (bar, val) in enumerate(zip(bars, order_error["error_rate"])):
        ax.text(
            bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", ha="left", va="center", fontsize=9,
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels(order_error["order"].values, fontsize=9)
    ax.set_xlabel("Flag Error Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Flag Accuracy Error Rate by Order\n(Average across AI Models)",
        fontsize=14, fontweight="bold", pad=15,
    )

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.02)
    cbar.set_label("Error Rate (%)", fontsize=10)

    ax.set_xlim(0, order_error["error_rate"].max() + 5)
    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureG9")
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating flag accuracy appendix figures (FigureG1-FigureG9)")
    print("=" * 60)

    tests_df = load_tests()

    figure_g1(tests_df)
    figure_g2(tests_df)
    figure_g3(tests_df)
    figure_g4(tests_df)
    figure_g5(tests_df)

    # G6-G8 share the same error data
    error_data, df_errors = _load_error_data(tests_df)
    figure_g6(error_data)
    figure_g7(df_errors)
    figure_g8(df_errors)

    figure_g9(tests_df)

    print("\nDone. All flag accuracy figures saved.")


if __name__ == "__main__":
    main()
