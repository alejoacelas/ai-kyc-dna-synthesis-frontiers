#!/usr/bin/env python3
"""
Generate main manuscript figures (Figure2–Figure5).

Figure2: Pass rates heatmap by screener and test category
Figure3: Cost breakdown stacked bars
Figure4: Cost vs performance scatter
Figure5: Flag errors by task and region
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy import stats as scipy_stats
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch

from style import (
    DATA_DIR, FIGURES_DIR, COLORS, MODEL_LABELS, MODEL_LABELS_NO_TIME,
    MODEL_ORDER, CATEGORY_ORDER,
    shorten_model_label, setup_style, save_figure,
)


def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


def load_responses():
    return pd.read_csv(DATA_DIR / "responses.csv")


# ---------- Figure 2: Pass rates heatmap ----------

def figure2(tests_df):
    """Pass rates heatmap with three separated blocks (AT, W, Human)."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="test_category", aggfunc="mean"
    ) * 100

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and m in pivot.index]

    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]
    pivot["all_metrics"] = pivot[categories].mean(axis=1)
    categories_with_all = categories + ["all_metrics"]

    n_at, n_w, n_human = len(at_models), len(w_models), len(human_models)
    gap_size = 0.7
    all_metrics_gap = 0.3

    fig, ax = plt.subplots(figsize=(6, 12))

    cmap = LinearSegmentedColormap.from_list("greens", ["#dcfce7", "#166534"])
    norm = Normalize(vmin=60, vmax=100)
    cell_width = cell_height = 1.0

    y_positions = {}
    annotation_positions = {}
    current_y = 0

    # Human at bottom
    annotation_positions["human"] = current_y + gap_size / 2
    current_y += gap_size
    for model in human_models:
        y_positions[model] = current_y
        current_y += cell_height

    # W in middle
    annotation_positions["w"] = current_y + gap_size / 2
    current_y += gap_size
    for model in w_models:
        y_positions[model] = current_y
        current_y += cell_height

    # AT at top
    annotation_positions["at"] = current_y + gap_size / 2
    current_y += gap_size
    for model in at_models:
        y_positions[model] = current_y
        current_y += cell_height

    models_display_order = human_models + w_models + at_models

    x_positions = {}
    for j, cat in enumerate(categories):
        x_positions[cat] = j * cell_width
    x_positions["all_metrics"] = len(categories) * cell_width + all_metrics_gap

    for model in models_display_order:
        y_pos = y_positions[model]
        is_5min = "(5min)" in model
        for cat in categories_with_all:
            x_pos = x_positions[cat]
            if model in pivot.index and cat in pivot.columns:
                value = pivot.loc[model, cat]
                if pd.notna(value):
                    if is_5min:
                        color = "#d1d5db"
                        text_color = "#6b7280"
                    else:
                        color = cmap(norm(value))
                        text_color = "white" if value > 75 else "black"
                    rect = plt.Rectangle(
                        (x_pos, y_pos), cell_width, cell_height,
                        facecolor=color, edgecolor="white", linewidth=1,
                    )
                    ax.add_patch(rect)
                    ax.text(
                        x_pos + cell_width / 2, y_pos + cell_height / 2,
                        f"{value:.1f}", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=text_color,
                    )

    ax.set_xlim(0, x_positions["all_metrics"] + cell_width)
    ax.set_ylim(0, current_y)

    y_ticks = [y_positions[m] + cell_height / 2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label(m) for m in models_display_order], fontsize=11)

    FIGURE_CATEGORY_LABELS = {
        "flag_accuracy": "Flag\nAccuracy",
        "claim_support": "Source\nFidelity",
        "source_reliability": "Source\nQuality",
        "work_relevance": "Work\nRelevance",
        "all_metrics": "All\nMetrics",
    }
    x_ticks = [x_positions[cat] + cell_width / 2 for cat in categories_with_all]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(
        [FIGURE_CATEGORY_LABELS.get(cat, cat) for cat in categories_with_all], fontsize=11
    )
    tick_labels = ax.get_xticklabels()
    tick_labels[-1].set_fontweight("bold")

    total_width = x_positions["all_metrics"] + cell_width
    center_x = total_width / 2

    if n_human > 0:
        ax.text(center_x, annotation_positions["human"], "Human baseline",
                ha="center", va="center", fontsize=11, fontweight="bold", style="italic")
    if n_w > 0:
        ax.text(center_x, annotation_positions["w"], "AI - Web Only (W)",
                ha="center", va="center", fontsize=11, fontweight="bold", style="italic")
    if n_at > 0:
        ax.text(center_x, annotation_positions["at"], "AI - All Tools (AT)",
                ha="center", va="center", fontsize=11, fontweight="bold", style="italic")

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Pass Rate (%)", fontsize=12)

    ax.set_title("Pass Rate by Screener and Test Category", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Test Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    save_figure(fig, "Figure2")
    plt.close()


# ---------- Figure 3: Cost breakdown ----------

HUMAN_REVIEW_COST = 1.08
COST_COLORS = {
    "ai_tokens": "#6366f1",
    "web_search": "#14b8a6",
    "human_review": "#f59e0b",
}


def figure3(responses_df):
    """Cost breakdown stacked bar chart."""
    setup_style()

    df_ai = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg(
        {"model_cost": "sum", "web_search_cost": "sum"}
    ).reset_index()

    model_costs = customer_costs.groupby("model_label").agg(
        {"model_cost": "mean", "web_search_cost": "mean"}
    )
    model_costs["human_review_cost"] = HUMAN_REVIEW_COST
    model_costs["total_cost"] = (
        model_costs["model_cost"] + model_costs["web_search_cost"] + model_costs["human_review_cost"]
    )
    model_costs = model_costs.sort_values("total_cost", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 7))

    models = model_costs.index.tolist()
    x = np.arange(len(models))
    width = 0.7

    ai_costs = model_costs["model_cost"].values
    web_costs = model_costs["web_search_cost"].values
    human_costs = model_costs["human_review_cost"].values

    ax.bar(x, human_costs, width, label="Human review cost",
           color=COST_COLORS["human_review"], alpha=0.9)
    ax.bar(x, ai_costs, width, bottom=human_costs,
           label="AI tokens cost", color=COST_COLORS["ai_tokens"], alpha=0.9)
    ax.bar(x, web_costs, width, bottom=human_costs + ai_costs,
           label="Web search cost", color=COST_COLORS["web_search"], alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(
        [MODEL_LABELS_NO_TIME.get(m, m) for m in models], rotation=45, ha="right", fontsize=10
    )

    ax.set_ylabel("Cost per Customer (USD)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")

    for i, (ai, web, human) in enumerate(zip(ai_costs, web_costs, human_costs)):
        total = ai + web + human
        ax.text(i, total + 0.02, f"${total:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    max_total = max(ai_costs + web_costs + human_costs)
    ax.set_ylim(0, max_total * 1.12)

    ax.set_title("Screening Cost Breakdown by Model", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "Figure3")
    plt.close()


# ---------- Figure 4: Cost vs performance ----------

FIGURE4_COLORS = {
    "all_tools": "#1e40af",
    "web_only": "#93c5fd",
}


def figure4(responses_df):
    """Cost vs performance scatter plot (human baseline subset)."""
    setup_style()

    df_ai = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg({
        "model_cost": "sum", "web_search_cost": "sum",
        "num_assertions_passed": "sum", "num_assertions": "sum",
    }).reset_index()
    customer_costs["ai_cost"] = customer_costs["model_cost"] + customer_costs["web_search_cost"]

    agg = customer_costs.groupby("model_label").agg({
        "ai_cost": "mean", "num_assertions_passed": "sum", "num_assertions": "sum",
    })
    agg["pass_rate"] = agg["num_assertions_passed"] / agg["num_assertions"] * 100

    models = [m for m in MODEL_ORDER if m in agg.index]
    agg = agg.loc[models]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [FIGURE4_COLORS["all_tools"] if "(All Tools)" in m else FIGURE4_COLORS["web_only"] for m in models]
    ax.scatter(agg["ai_cost"], agg["pass_rate"], c=colors, s=150, edgecolors="white", linewidth=1.5, alpha=0.8)

    for model in models:
        ax.annotate(
            shorten_model_label(model),
            (agg.loc[model, "ai_cost"], agg.loc[model, "pass_rate"]),
            xytext=(5, 5), textcoords="offset points", fontsize=9,
        )

    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(
        agg["ai_cost"], agg["pass_rate"]
    )
    r_squared = r_value ** 2

    ax.set_xlabel("Average AI Screening Cost per Customer (USD)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("AI Screening Cost vs Overall Pass Rate", fontsize=12, fontweight="bold")

    x_max = agg["ai_cost"].max() * 1.15
    ax.set_xlim(0, x_max)
    ax.set_ylim(82, 92)

    # Axis break indicator
    kwargs = dict(transform=ax.transAxes, color="k", clip_on=False, linewidth=1.5)
    d, h, y_base, gap = 0.012, 0.02, 0.01, 0.008
    ax.plot([-d, d], [y_base, y_base + h], **kwargs)
    ax.plot([-d, d], [y_base + gap, y_base + h + gap], **kwargs)

    ax.annotate("0", xy=(0, 82), xytext=(-0.03, -0.06), textcoords="axes fraction",
                fontsize=10, ha="center", va="top")

    ax.annotate(f"$R^2$ = {r_squared:.3f}", xy=(0.95, 0.95), xycoords="axes fraction",
                ha="right", va="top", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8))

    legend_elements = [
        Patch(facecolor=FIGURE4_COLORS["web_only"], label="Web Only"),
        Patch(facecolor=FIGURE4_COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "Figure4")
    plt.close()


# ---------- Figure 5: Flag errors by task and region ----------

TASK_CONFIG = {
    "AFFILIATION-FLAG-ACCURACY": {"label": "Institutional\nAffiliation", "ground_truth_col": "ground_truth_affiliation", "order": 0},
    "INSTITUTION-FLAG-ACCURACY": {"label": "Institution\nType", "ground_truth_col": "ground_truth_institution", "order": 1},
    "DOMAIN-FLAG-ACCURACY": {"label": "Email\nDomain", "ground_truth_col": "ground_truth_domain", "order": 2},
    "SANCTIONS-FLAG-ACCURACY": {"label": "Sanctions\nScreening", "ground_truth_col": "ground_truth_sanctions", "order": 3},
}


def _classify_error(row):
    metric = row["metric_name"]
    if metric not in TASK_CONFIG:
        return None
    gt_col = TASK_CONFIG[metric]["ground_truth_col"]
    ground_truth = row[gt_col]
    extracted = row["extracted_flag"]
    if row["pass"]:
        return "correct"
    if extracted == "UNDETERMINED":
        return "undetermined"
    elif ground_truth == "FLAG" and extracted == "NO FLAG":
        return "missed_flag"
    elif ground_truth == "NO FLAG" and extracted == "FLAG":
        return "false_flag"
    else:
        return "other"


def figure5(tests_df):
    """Flag accuracy error breakdown by task and region."""
    setup_style()

    df_flag = tests_df[
        (tests_df["test_category"] == "flag_accuracy")
        & (tests_df["is_human_baseline"] == False)
        & (tests_df["is_human_baseline_dataset"] == True)
    ].copy()

    df_flag["error_type"] = df_flag.apply(_classify_error, axis=1)
    df_flag["task"] = df_flag["metric_name"].map(lambda x: TASK_CONFIG.get(x, {}).get("label", x))
    df_flag["task_order"] = df_flag["metric_name"].map(lambda x: TASK_CONFIG.get(x, {}).get("order", 99))
    df_flag["region"] = df_flag["institution_country"].replace({"Others": "Other countries"})

    error_types = ["missed_flag", "false_flag", "undetermined"]
    error_labels = {"missed_flag": "Missed Flag", "false_flag": "False Flag", "undetermined": "Undetermined"}

    tasks = sorted(df_flag["task"].unique(), key=lambda x: df_flag[df_flag["task"] == x]["task_order"].iloc[0])
    region_order = ["USA", "Europe + Australia", "China", "Other countries"]
    regions = [r for r in region_order if r in df_flag["region"].unique()]

    results = []
    for region in regions:
        for task in tasks:
            subset = df_flag[(df_flag["region"] == region) & (df_flag["task"] == task)]
            total = len(subset)
            if total > 0:
                for error_type in error_types:
                    count = (subset["error_type"] == error_type).sum()
                    rate = count / total * 100
                    results.append({"region": region, "task": task, "error_type": error_type, "error_rate": rate})

    results_df = pd.DataFrame(results)

    fig, axes = plt.subplots(1, len(tasks), figsize=(14, 6), sharey=True)

    error_colors = {"missed_flag": "#dc2626", "false_flag": "#f97316", "undetermined": "#6b7280"}
    bar_width = 0.25
    x = np.arange(len(regions))

    for idx, task in enumerate(tasks):
        ax = axes[idx]
        task_data = results_df[results_df["task"] == task]

        for i, error_type in enumerate(error_types):
            error_data = task_data[task_data["error_type"] == error_type]
            values = [
                error_data[error_data["region"] == r]["error_rate"].values[0]
                if len(error_data[error_data["region"] == r]) > 0
                else 0
                for r in regions
            ]
            offset = (i - 1) * bar_width
            bars = ax.bar(
                x + offset, values, bar_width,
                label=error_labels[error_type] if idx == 0 else "",
                color=error_colors[error_type], alpha=0.85, edgecolor="white", linewidth=0.5,
            )
            for bar, val in zip(bars, values):
                if val > 0.5:
                    ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 0.3,
                            f"{val:.1f}", ha="center", va="bottom", fontsize=8)

        ax.set_title(task, fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(
            [r.replace(" + ", "\n+ ").replace(" countries", "\ncountries") for r in regions],
            fontsize=9,
        )
        ax.set_ylim(0, max(results_df["error_rate"]) * 1.15)
        if idx == 0:
            ax.set_ylabel("Error Rate (%)", fontsize=12, fontweight="bold")
        ax.grid(True, axis="y", alpha=0.3, linestyle="-", linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, -0.02), frameon=True)

    fig.suptitle(
        "Flag Accuracy Error Rates by Task and Customer Region\n(Average across AI Models)",
        fontsize=14, fontweight="bold", y=1.02,
    )

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)
    save_figure(fig, "Figure5")
    plt.close()


# ---------- Main ----------

def main():
    print("Generating main manuscript figures (Figure2-Figure5)")
    print("=" * 60)

    tests_df = load_tests()
    responses_df = load_responses()

    figure2(tests_df)
    figure3(responses_df)
    figure4(responses_df)
    figure5(tests_df)

    print("\nDone. All main figures saved to paper/figures/")


if __name__ == "__main__":
    main()
