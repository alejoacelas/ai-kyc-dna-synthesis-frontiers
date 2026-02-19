#!/usr/bin/env python3
"""
Generate full-dataset figures (FigureF1--FigureF5).

FigureF1: Full dataset pass rates heatmap by test category
FigureF2: Full dataset pass rates heatmap by task
FigureF3: Full dataset pass rates heatmap by customer type
FigureF4: Subset vs full comparison grouped bar chart
FigureF5: Customer type x region dual heatmap
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

from style import (
    DATA_DIR, COLORS, MODEL_LABELS_NO_TIME, MODEL_ORDER, CATEGORY_ORDER, COUNTRY_ORDER,
    setup_style, save_figure, shorten_model_label_no_time,
)


def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


# ---------- Shared constants ----------

FIGURE_CATEGORY_LABELS = {
    "flag_accuracy": "Flag\nAccuracy",
    "claim_support": "Source\nFidelity",
    "source_reliability": "Source\nQuality",
    "work_relevance": "Work\nRelevance",
    "all_metrics": "All\nMetrics",
}

TASK_ORDER = ["affiliation", "institution", "domain", "sanctions", "work"]

TASK_LABELS = {
    "affiliation": "Institution\nAffiliation",
    "institution": "Institution\nType",
    "domain": "Email\nDomain",
    "sanctions": "Sanctions\nScreening",
    "work": "Relevant\nWork",
}

CUSTOMER_TYPE_ORDER = [
    "Controlled Agent Academia",
    "Controlled Agent Industry",
    "Sanctioned Institution Customers",
    "General Life Science Customers",
]

CUSTOMER_TYPE_LABELS = {
    "Controlled Agent Academia": "Academic w/\nSOC backg.",
    "Controlled Agent Industry": "Industry w/\nSOC backg.",
    "Sanctioned Institution Customers": "Sanctioned\nAcademic",
    "General Life Science Customers": "General\nLife Science",
}


def _extract_task(metric_name):
    """Extract task from metric_name."""
    upper = metric_name.upper()
    if upper.startswith("AFFILIATION"):
        return "affiliation"
    elif upper.startswith("INSTITUTION"):
        return "institution"
    elif upper.startswith("DOMAIN"):
        return "domain"
    elif upper.startswith("SANCTIONS"):
        return "sanctions"
    elif "WORK" in upper:
        return "work"
    return None


def _filter_ai_full(df):
    """Filter to AI models only (exclude human baselines), full 134-profile dataset."""
    return df[df["model_type"] != "human_baseline"].copy()


def _draw_heatmap(pivot, columns, column_labels, title, xlabel, figure_name,
                  vmin, vmax, has_all_metrics_col=False, all_metrics_gap=0.3):
    """
    Draw a Rectangle-patch heatmap with AT and W model groups.

    Parameters
    ----------
    pivot : DataFrame with model_label index and the requested columns.
    columns : list of column keys to plot (in order).
    column_labels : dict mapping column key -> display label.
    title : figure title.
    xlabel : x-axis label.
    figure_name : name passed to save_figure().
    vmin, vmax : colorbar range.
    has_all_metrics_col : if True, the last column ("all_metrics") gets an extra gap.
    all_metrics_gap : width of the gap before the all_metrics column.
    """
    setup_style()

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]

    n_at = len(at_models)
    n_w = len(w_models)
    gap_size = 0.7

    fig, ax = plt.subplots(figsize=(6, 8))

    cmap = LinearSegmentedColormap.from_list("greens", ["#dcfce7", "#166534"])
    norm = Normalize(vmin=vmin, vmax=vmax)
    cell_width = 1.0
    cell_height = 1.0

    # Build y positions: W at bottom, AT at top
    y_positions = {}
    annotation_positions = {}
    current_y = 0

    # W models at bottom
    annotation_positions["w"] = current_y + gap_size / 2
    current_y += gap_size
    for model in w_models:
        y_positions[model] = current_y
        current_y += cell_height

    # AT models at top
    annotation_positions["at"] = current_y + gap_size / 2
    current_y += gap_size
    for model in at_models:
        y_positions[model] = current_y
        current_y += cell_height

    models_display_order = w_models + at_models

    # Build x positions
    x_positions = {}
    if has_all_metrics_col:
        regular_cols = columns[:-1]
        for j, col in enumerate(regular_cols):
            x_positions[col] = j * cell_width
        x_positions[columns[-1]] = len(regular_cols) * cell_width + all_metrics_gap
    else:
        for j, col in enumerate(columns):
            x_positions[col] = j * cell_width

    # Draw cells
    for model in models_display_order:
        y_pos = y_positions[model]
        for col in columns:
            x_pos = x_positions[col]
            if model in pivot.index and col in pivot.columns:
                value = pivot.loc[model, col]
                if pd.notna(value):
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

    # Axis limits
    last_col = columns[-1]
    ax.set_xlim(0, x_positions[last_col] + cell_width)
    ax.set_ylim(0, current_y)

    # Y-axis
    y_ticks = [y_positions[m] + cell_height / 2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(
        [shorten_model_label_no_time(m) for m in models_display_order], fontsize=11,
    )

    # X-axis
    x_ticks = [x_positions[col] + cell_width / 2 for col in columns]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(
        [column_labels.get(col, col) for col in columns], fontsize=11,
    )
    if has_all_metrics_col:
        tick_labels = ax.get_xticklabels()
        tick_labels[-1].set_fontweight("bold")

    # Section annotations
    total_width = x_positions[last_col] + cell_width
    center_x = total_width / 2

    if n_w > 0:
        ax.text(center_x, annotation_positions["w"], "AI - Web Only (W)",
                ha="center", va="center", fontsize=11, fontweight="bold", style="italic")
    if n_at > 0:
        ax.text(center_x, annotation_positions["at"], "AI - All Tools (AT)",
                ha="center", va="center", fontsize=11, fontweight="bold", style="italic")

    # Colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label("Pass Rate (%)", fontsize=12)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel(xlabel, fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    save_figure(fig, figure_name)
    plt.close()


# ---------- FigureF1: Full dataset pass rates heatmap ----------

def figure_f1(tests_df):
    """Pass rates heatmap by test category (full 134-profile, AI only)."""
    df = _filter_ai_full(tests_df)

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="test_category", aggfunc="mean",
    ) * 100

    categories = [c for c in CATEGORY_ORDER if c in pivot.columns]
    pivot["all_metrics"] = pivot[categories].mean(axis=1)
    columns = categories + ["all_metrics"]

    _draw_heatmap(
        pivot, columns, FIGURE_CATEGORY_LABELS,
        title="Pass Rate by Screener and Test Category (Full Dataset)",
        xlabel="Test Category",
        figure_name="FigureF1",
        vmin=60, vmax=100,
        has_all_metrics_col=True,
    )


# ---------- FigureF2: Full dataset by task heatmap ----------

def figure_f2(tests_df):
    """Pass rates heatmap by task (full 134-profile, AI only)."""
    df = _filter_ai_full(tests_df)
    df["task"] = df["metric_name"].apply(_extract_task)
    df = df[df["task"].notna()]

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="task", aggfunc="mean",
    ) * 100

    columns = [t for t in TASK_ORDER if t in pivot.columns]

    _draw_heatmap(
        pivot, columns, TASK_LABELS,
        title="Pass Rate by Screener and Task (Full Dataset)",
        xlabel="Task",
        figure_name="FigureF2",
        vmin=50, vmax=100,
    )


# ---------- FigureF3: Full dataset by customer type heatmap ----------

def figure_f3(tests_df):
    """Pass rates heatmap by customer type (full 134-profile, AI only)."""
    df = _filter_ai_full(tests_df)

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="customer_type", aggfunc="mean",
    ) * 100

    columns = [c for c in CUSTOMER_TYPE_ORDER if c in pivot.columns]

    _draw_heatmap(
        pivot, columns, CUSTOMER_TYPE_LABELS,
        title="Pass Rate by Screener and Customer Type (Full Dataset)",
        xlabel="Customer Type",
        figure_name="FigureF3",
        vmin=50, vmax=100,
    )


# ---------- FigureF4: Subset vs full comparison ----------

def figure_f4(tests_df):
    """Grouped bar chart: 40-profile subset vs full 134-profile dataset pass rates."""
    setup_style()

    # 40-profile subset, AI only
    df_subset = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ]
    subset_rates = df_subset.groupby("model_label")["pass"].mean() * 100

    # Full dataset, AI only
    df_full = tests_df[tests_df["model_type"] != "human_baseline"]
    full_rates = df_full.groupby("model_label")["pass"].mean() * 100

    # Order models
    models = [m for m in MODEL_ORDER if "Human" not in m and m in subset_rates.index and m in full_rates.index]

    subset_vals = [subset_rates[m] for m in models]
    full_vals = [full_rates[m] for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 7))

    bars_subset = ax.bar(
        x - width / 2, subset_vals, width,
        label="40-profile subset", color="#3498db", alpha=0.9,
    )
    bars_full = ax.bar(
        x + width / 2, full_vals, width,
        label="Full dataset (134)", color="#2c3e50", alpha=0.9,
    )

    # Value labels
    for bar in bars_subset:
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold",
        )
    for bar in bars_full:
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [shorten_model_label_no_time(m) for m in models], rotation=45, ha="right", fontsize=10,
    )

    all_vals = subset_vals + full_vals
    y_min = min(all_vals) - 5
    y_max = max(all_vals) + 3
    ax.set_ylim(y_min, y_max)

    ax.set_ylabel("Overall Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title("Pass Rate: 40-Profile Subset vs Full Dataset", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureF4")
    plt.close()


# ---------- FigureF5: Customer type x region dual heatmap ----------

def figure_f5(tests_df):
    """Side-by-side heatmaps: customer type x region, 40-profile vs full 134."""
    setup_style()

    # Prepare both panels
    df_ai = tests_df[tests_df["model_type"] != "human_baseline"].copy()
    df_subset = df_ai[df_ai["is_human_baseline_dataset"] == True]
    df_full = df_ai

    customer_types = [c for c in CUSTOMER_TYPE_ORDER if c in df_ai["customer_type"].unique()]
    countries = [c for c in COUNTRY_ORDER if c in df_ai["institution_country"].unique()]

    def _build_matrix(df):
        """Build pass-rate and count matrices."""
        rate_matrix = pd.DataFrame(index=customer_types, columns=countries, dtype=float)
        count_matrix = pd.DataFrame(index=customer_types, columns=countries, dtype=float)
        for ct in customer_types:
            for co in countries:
                subset = df[(df["customer_type"] == ct) & (df["institution_country"] == co)]
                if len(subset) > 0:
                    rate_matrix.loc[ct, co] = subset["pass"].mean() * 100
                    count_matrix.loc[ct, co] = len(subset)
                else:
                    rate_matrix.loc[ct, co] = np.nan
                    count_matrix.loc[ct, co] = 0
        return rate_matrix.astype(float), count_matrix.astype(float)

    rate_sub, count_sub = _build_matrix(df_subset)
    rate_full, count_full = _build_matrix(df_full)

    # Shared vmin/vmax
    all_vals = pd.concat([rate_sub.stack(), rate_full.stack()]).dropna()
    vmin = max(0, all_vals.min() - 5)
    vmax = min(100, all_vals.max() + 5)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    for ax, rate_mat, count_mat, panel_title in [
        (ax1, rate_sub, count_sub, "40-Profile Subset"),
        (ax2, rate_full, count_full, "Full Dataset (134)"),
    ]:
        # Build annotation strings
        annot = rate_mat.copy().astype(object)
        for ct in customer_types:
            for co in countries:
                val = rate_mat.loc[ct, co]
                cnt = count_mat.loc[ct, co]
                if pd.isna(val) or cnt == 0:
                    annot.loc[ct, co] = "N/A"
                else:
                    annot.loc[ct, co] = f"{val:.1f}\n(n={int(cnt)})"

        # Use short labels for y-axis
        display_rate = rate_mat.copy()
        display_rate.index = [CUSTOMER_TYPE_LABELS.get(c, c) for c in customer_types]
        annot.index = display_rate.index

        sns.heatmap(
            display_rate, annot=annot, fmt="", cmap="Greens",
            vmin=vmin, vmax=vmax, ax=ax, linewidths=0.5, linecolor="white",
            cbar_kws={"label": "Pass Rate (%)"},
        )
        ax.set_title(panel_title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Region", fontsize=11, fontweight="bold")
        ax.set_ylabel("Customer Type", fontsize=11, fontweight="bold")
        ax.tick_params(axis="y", rotation=0)

    fig.suptitle(
        "Pass Rate by Customer Type and Region (AI Models Only)",
        fontsize=14, fontweight="bold", y=1.02,
    )

    plt.tight_layout()
    save_figure(fig, "FigureF5")
    plt.close()


# ---------- Main ----------

def main():
    print("Generating full-dataset figures (FigureF1-FigureF5)")
    print("=" * 60)

    tests_df = load_tests()

    figure_f1(tests_df)
    figure_f2(tests_df)
    figure_f3(tests_df)
    figure_f4(tests_df)
    figure_f5(tests_df)

    print("\nDone. All full-dataset figures saved.")


if __name__ == "__main__":
    main()
