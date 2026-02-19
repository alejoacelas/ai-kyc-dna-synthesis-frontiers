#!/usr/bin/env python3
"""
Generate extended model performance figures (FigureE1-FigureE8).

FigureE1: Pass rate with 95% Wilson confidence intervals
FigureE2: Model rankings sorted bar chart
FigureE3: Pass rates by task heatmap
FigureE4: Pass rates by customer type heatmap
FigureE5: Per-customer swarm plot
FigureE6: Flag vs non-flag pass rate scatter
FigureE7: Pairwise McNemar's test heatmap
FigureE8: Correlation matrix of test category pass rates
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch
from scipy.stats import chi2, pearsonr

from style import (
    DATA_DIR, FIGURES_DIR, COLORS, MODEL_LABELS, MODEL_LABELS_NO_TIME,
    MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS, FLAG_ORDER, FLAG_LABELS,
    COUNTRY_ORDER,
    setup_style, save_figure, get_model_color, get_model_colors,
    shorten_model_label, shorten_model_label_no_time,
)


def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


def load_responses():
    return pd.read_csv(DATA_DIR / "responses.csv")


# --- Constants ---

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

TASK_ORDER = ["affiliation", "institution", "domain", "sanctions", "work"]

TASK_LABELS = {
    "affiliation": "Institution\nAffiliation",
    "institution": "Institution\nType",
    "domain": "Email\nDomain",
    "sanctions": "Sanctions\nScreening",
    "work": "Relevant\nWork",
}


def extract_task(metric_name):
    """Extract task from metric_name."""
    metric_upper = metric_name.upper()
    if metric_upper.startswith("AFFILIATION"):
        return "affiliation"
    elif metric_upper.startswith("INSTITUTION"):
        return "institution"
    elif metric_upper.startswith("DOMAIN"):
        return "domain"
    elif metric_upper.startswith("SANCTIONS"):
        return "sanctions"
    elif "WORK" in metric_upper:
        return "work"
    return None


# ---------- FigureE1: Pass rate with Wilson CI ----------

def figure_e1(tests_df):
    """Pass rate with 95% Wilson confidence intervals (horizontal bar chart)."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    # Calculate pass rates and Wilson CI per model
    stats = df.groupby("model_label")["pass"].agg(["sum", "count"]).reset_index()
    stats.columns = ["model_label", "successes", "n"]
    stats["p_hat"] = stats["successes"] / stats["n"]

    z = 1.96
    stats["denom"] = 1 + z**2 / stats["n"]
    stats["center"] = (stats["p_hat"] + z**2 / (2 * stats["n"])) / stats["denom"]
    stats["margin"] = (
        z
        * np.sqrt((stats["p_hat"] * (1 - stats["p_hat"]) + z**2 / (4 * stats["n"])) / stats["n"])
        / stats["denom"]
    )
    stats["lower"] = stats["center"] - stats["margin"]
    stats["upper"] = stats["center"] + stats["margin"]

    # Convert to percentages
    stats["pass_rate"] = stats["p_hat"] * 100
    stats["ci_lower"] = stats["lower"] * 100
    stats["ci_upper"] = stats["upper"] * 100

    # Order by MODEL_ORDER
    models = [m for m in MODEL_ORDER if m in stats["model_label"].values]
    stats = stats.set_index("model_label").loc[models].reset_index()

    fig, ax = plt.subplots(figsize=(10, 8))

    y = np.arange(len(stats))
    colors = get_model_colors(stats["model_label"])

    # Error bars: asymmetric [lower_err, upper_err]
    lower_err = stats["pass_rate"].values - stats["ci_lower"].values
    upper_err = stats["ci_upper"].values - stats["pass_rate"].values

    ax.barh(
        y, stats["pass_rate"], color=colors, alpha=0.85, edgecolor="white", linewidth=0.5,
    )
    ax.errorbar(
        stats["pass_rate"], y,
        xerr=[lower_err, upper_err],
        fmt="none", ecolor="black", elinewidth=1.5, capsize=4,
    )

    ax.set_yticks(y)
    ax.set_yticklabels([shorten_model_label(m) for m in stats["model_label"]], fontsize=11)
    ax.set_xlabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")
    ax.set_title(
        "Overall Pass Rate with 95% Wilson Confidence Intervals",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlim(0, 100)

    # Legend
    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="AI - All Tools (AT)"),
        Patch(facecolor=COLORS["web_only"], label="AI - Web Only (W)"),
        Patch(facecolor=COLORS["human_baseline"], label="Human baseline"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureE1")
    plt.close()


# ---------- FigureE2: Model rankings sorted bar chart ----------

def figure_e2(tests_df):
    """Vertical bar chart of overall pass rates, sorted descending."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    stats = df.groupby("model_label")["pass"].agg(["sum", "count"]).reset_index()
    stats.columns = ["model_label", "pass_count", "total_count"]
    stats["pass_rate"] = stats["pass_count"] / stats["total_count"] * 100

    # Sort descending
    stats = stats.sort_values("pass_rate", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(stats))
    colors = get_model_colors(stats["model_label"])

    bars = ax.bar(x, stats["pass_rate"], color=colors, alpha=0.9, edgecolor="white", linewidth=0.5)

    # Value labels on top
    for bar, rate in zip(bars, stats["pass_rate"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{rate:.1f}%",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [shorten_model_label(m) for m in stats["model_label"]],
        rotation=45, ha="right", fontsize=10,
    )
    ax.set_ylabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Screener", fontsize=12, fontweight="bold")
    ax.set_title(
        "Overall Pass Rate by Screener (Sorted)",
        fontsize=14, fontweight="bold", pad=15,
    )

    max_rate = stats["pass_rate"].max()
    ax.set_ylim(0, max_rate * 1.08)

    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="AI - All Tools (AT)"),
        Patch(facecolor=COLORS["web_only"], label="AI - Web Only (W)"),
        Patch(facecolor=COLORS["human_baseline"], label="Human baseline"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureE2")
    plt.close()


# ---------- FigureE3: Pass rates by task heatmap ----------

def figure_e3(tests_df):
    """Pass rates heatmap with columns = task, three blocks (AT, W, Human)."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()
    df["task"] = df["metric_name"].apply(extract_task)
    df = df[df["task"].notna()]

    pivot = df.pivot_table(values="pass", index="model_label", columns="task", aggfunc="mean") * 100

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and m in pivot.index]

    tasks = [t for t in TASK_ORDER if t in pivot.columns]

    gap_size = 0.7
    cell_width = cell_height = 1.0

    fig, ax = plt.subplots(figsize=(6, 12))

    cmap = LinearSegmentedColormap.from_list("greens", ["#dcfce7", "#166534"])
    norm = Normalize(vmin=50, vmax=100)

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

    for model in models_display_order:
        y_pos = y_positions[model]
        for j, task in enumerate(tasks):
            if model in pivot.index and task in pivot.columns:
                value = pivot.loc[model, task]
                if pd.notna(value):
                    color = cmap(norm(value))
                    text_color = "white" if value > 75 else "black"
                    rect = plt.Rectangle(
                        (j, y_pos), cell_width, cell_height,
                        facecolor=color, edgecolor="white", linewidth=1,
                    )
                    ax.add_patch(rect)
                    ax.text(
                        j + cell_width / 2, y_pos + cell_height / 2,
                        f"{value:.1f}", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=text_color,
                    )

    ax.set_xlim(0, len(tasks))
    ax.set_ylim(0, current_y)

    y_ticks = [y_positions[m] + cell_height / 2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label_no_time(m) for m in models_display_order], fontsize=11)

    ax.set_xticks([i + cell_width / 2 for i in range(len(tasks))])
    ax.set_xticklabels([TASK_LABELS.get(t, t) for t in tasks], fontsize=11)

    center_x = len(tasks) / 2
    n_human, n_w, n_at = len(human_models), len(w_models), len(at_models)

    if n_human > 0:
        ax.text(center_x, annotation_positions["human"], "Human Baseline",
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

    ax.set_title("Pass Rate by Screener and Task", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Task", fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    save_figure(fig, "FigureE3")
    plt.close()


# ---------- FigureE4: Pass rates by customer type heatmap ----------

def figure_e4(tests_df):
    """Pass rates heatmap with columns = customer_type, three blocks (AT, W, Human)."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    pivot = df.pivot_table(
        values="pass", index="model_label", columns="customer_type", aggfunc="mean",
    ) * 100

    at_models = [m for m in MODEL_ORDER if "(All Tools)" in m and m in pivot.index]
    w_models = [m for m in MODEL_ORDER if "(Web)" in m and m in pivot.index]
    human_models = [m for m in MODEL_ORDER if "Human" in m and m in pivot.index]

    customer_types = [c for c in CUSTOMER_TYPE_ORDER if c in pivot.columns]

    gap_size = 0.7
    cell_width = cell_height = 1.0

    fig, ax = plt.subplots(figsize=(6, 12))

    cmap = LinearSegmentedColormap.from_list("greens", ["#dcfce7", "#166534"])
    norm = Normalize(vmin=50, vmax=100)

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

    for model in models_display_order:
        y_pos = y_positions[model]
        for j, ctype in enumerate(customer_types):
            if model in pivot.index and ctype in pivot.columns:
                value = pivot.loc[model, ctype]
                if pd.notna(value):
                    color = cmap(norm(value))
                    text_color = "white" if value > 75 else "black"
                    rect = plt.Rectangle(
                        (j, y_pos), cell_width, cell_height,
                        facecolor=color, edgecolor="white", linewidth=1,
                    )
                    ax.add_patch(rect)
                    ax.text(
                        j + cell_width / 2, y_pos + cell_height / 2,
                        f"{value:.1f}", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=text_color,
                    )

    ax.set_xlim(0, len(customer_types))
    ax.set_ylim(0, current_y)

    y_ticks = [y_positions[m] + cell_height / 2 for m in models_display_order]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([shorten_model_label_no_time(m) for m in models_display_order], fontsize=11)

    ax.set_xticks([i + cell_width / 2 for i in range(len(customer_types))])
    ax.set_xticklabels([CUSTOMER_TYPE_LABELS.get(c, c) for c in customer_types], fontsize=11)

    center_x = len(customer_types) / 2
    n_human, n_w, n_at = len(human_models), len(w_models), len(at_models)

    if n_human > 0:
        ax.text(center_x, annotation_positions["human"], "Human Baseline",
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

    ax.set_title("Pass Rate by Screener and Customer Type", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Customer Type", fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)

    plt.tight_layout()
    save_figure(fig, "FigureE4")
    plt.close()


# ---------- FigureE5: Per-customer swarm plot ----------

def figure_e5(tests_df):
    """Swarm plot of per-customer pass rates (averaged across AI models)."""
    setup_style()
    import seaborn as sns

    df = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    # Per-customer pass rate averaged across AI models
    customer_rates = (
        df.groupby(["customer_name", "customer_type"])["pass"]
        .mean()
        .reset_index()
    )
    customer_rates["pass_rate"] = customer_rates["pass"] * 100

    # Filter to known customer types and order
    customer_rates = customer_rates[customer_rates["customer_type"].isin(CUSTOMER_TYPE_ORDER)]

    fig, ax = plt.subplots(figsize=(10, 7))

    # Map colors
    palette = {ct: COLORS[ct] for ct in CUSTOMER_TYPE_ORDER if ct in COLORS}

    sns.stripplot(
        data=customer_rates, x="customer_type", y="pass_rate",
        hue="customer_type", order=CUSTOMER_TYPE_ORDER, palette=palette,
        size=8, alpha=0.6, jitter=0.25, legend=False, ax=ax,
    )

    # Overall mean line
    overall_mean = customer_rates["pass_rate"].mean()
    ax.axhline(overall_mean, color="black", linestyle="--", linewidth=1, alpha=0.7,
               label=f"Overall mean ({overall_mean:.1f}%)")

    # Per-group mean markers
    for i, ct in enumerate(CUSTOMER_TYPE_ORDER):
        group = customer_rates[customer_rates["customer_type"] == ct]
        if len(group) > 0:
            group_mean = group["pass_rate"].mean()
            ax.plot(i, group_mean, marker="D", color="black", markersize=10, zorder=5)
            ax.text(i + 0.15, group_mean, f"{group_mean:.1f}%", va="center", fontsize=9,
                    fontweight="bold")

    ax.set_xticks(range(len(CUSTOMER_TYPE_ORDER)))
    ax.set_xticklabels(
        [CUSTOMER_TYPE_LABELS.get(ct, ct) for ct in CUSTOMER_TYPE_ORDER], fontsize=11,
    )
    ax.set_xlabel("Customer Type", fontsize=12, fontweight="bold")
    ax.set_ylabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Per-Customer Pass Rate by Customer Type\n(Averaged Across AI Models)",
        fontsize=14, fontweight="bold", pad=15,
    )

    ax.legend(loc="lower left", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureE5")
    plt.close()


# ---------- FigureE6: Flag vs non-flag pass rate scatter ----------

def figure_e6(tests_df):
    """Scatter: per-customer flag vs non-flag pass rate (averaged across AI models)."""
    setup_style()

    df = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    # Split into flag and non-flag
    df_flag = df[df["test_category"] == "flag_accuracy"]
    df_nonflag = df[df["test_category"] != "flag_accuracy"]

    # Per-customer pass rates averaged across AI models
    flag_rates = (
        df_flag.groupby(["customer_name", "customer_type"])["pass"]
        .mean()
        .reset_index()
        .rename(columns={"pass": "flag_pass_rate"})
    )
    nonflag_rates = (
        df_nonflag.groupby(["customer_name", "customer_type"])["pass"]
        .mean()
        .reset_index()
        .rename(columns={"pass": "nonflag_pass_rate"})
    )

    merged = flag_rates.merge(nonflag_rates, on=["customer_name", "customer_type"])
    merged["flag_pass_rate"] *= 100
    merged["nonflag_pass_rate"] *= 100

    fig, ax = plt.subplots(figsize=(8, 8))

    # Color by customer type
    palette = {ct: COLORS.get(ct, "#95a5a6") for ct in CUSTOMER_TYPE_ORDER}

    for ct in CUSTOMER_TYPE_ORDER:
        subset = merged[merged["customer_type"] == ct]
        if len(subset) > 0:
            ax.scatter(
                subset["nonflag_pass_rate"], subset["flag_pass_rate"],
                c=palette[ct], s=80, alpha=0.7, edgecolors="white", linewidth=0.5,
                label=CUSTOMER_TYPE_LABELS.get(ct, ct).replace("\n", " "),
            )

    # Diagonal y=x reference
    lims = [0, 100]
    ax.plot(lims, lims, "k--", alpha=0.3, linewidth=1)

    # Pearson r
    r, p = pearsonr(merged["nonflag_pass_rate"], merged["flag_pass_rate"])
    ax.annotate(
        f"r = {r:.3f} (p = {p:.3f})",
        xy=(0.05, 0.95), xycoords="axes fraction",
        ha="left", va="top", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
    )

    ax.set_xlabel("Non-Flag Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Flag Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Flag vs Non-Flag Pass Rate per Customer\n(Averaged Across AI Models)",
        fontsize=14, fontweight="bold", pad=15,
    )

    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_figure(fig, "FigureE6")
    plt.close()


# ---------- FigureE7: Pairwise McNemar's test heatmap ----------

def figure_e7(tests_df):
    """Lower-triangle heatmap of McNemar's test p-values between AI model pairs."""
    setup_style()

    df = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    # Build aligned binary pass/fail arrays per model
    # Key: (customer_name, metric_name, prompt_type)
    df["key"] = df["customer_name"] + "|" + df["metric_name"] + "|" + df["prompt_type"]

    ai_models = [m for m in MODEL_ORDER if m in df["model_label"].unique() and "Human" not in m]
    n = len(ai_models)

    # Pivot to get pass/fail per key per model
    pivot = df.pivot_table(index="key", columns="model_label", values="pass", aggfunc="first")

    # Drop rows with any NaN across AI models (need aligned pairs)
    pivot_aligned = pivot[ai_models].dropna()

    p_matrix = np.ones((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            a = pivot_aligned[ai_models[i]].values.astype(int)
            b = pivot_aligned[ai_models[j]].values.astype(int)

            # McNemar's contingency: b_count = model_i wrong, model_j right
            #                         c_count = model_i right, model_j wrong
            b_count = int(((a == 0) & (b == 1)).sum())
            c_count = int(((a == 1) & (b == 0)).sum())

            bc_sum = b_count + c_count
            if bc_sum > 0:
                # McNemar's with continuity correction
                stat = (abs(b_count - c_count) - 1) ** 2 / bc_sum
                p_val = 1 - chi2.cdf(stat, df=1)
            else:
                p_val = 1.0

            p_matrix[i, j] = p_val
            p_matrix[j, i] = p_val

    # Plot lower triangle of -log10(p)
    neg_log_p = -np.log10(p_matrix + 1e-300)  # avoid log(0)

    # Mask upper triangle
    mask = np.triu(np.ones_like(neg_log_p, dtype=bool))

    fig, ax = plt.subplots(figsize=(10, 9))

    import seaborn as sns

    sns.heatmap(
        neg_log_p, mask=mask,
        xticklabels=[shorten_model_label(m) for m in ai_models],
        yticklabels=[shorten_model_label(m) for m in ai_models],
        cmap="YlOrRd", vmin=0,
        square=True, linewidths=0.5, linecolor="white",
        cbar_kws={"label": "$-\\log_{10}(p)$", "shrink": 0.7},
        ax=ax,
    )

    # Annotate with p-values and significance stars
    for i in range(n):
        for j in range(i + 1, n):
            p_val = p_matrix[i, j]  # Note: heatmap rows=i, cols=j but lower triangle means j,i
            sig = "*" if p_val < 0.05 else ""
            if p_val < 0.001:
                label = f"<.001{sig}"
            elif p_val < 0.01:
                label = f"{p_val:.3f}{sig}"
            else:
                label = f"{p_val:.2f}{sig}"
            # Lower triangle: row=j, col=i
            ax.text(
                i + 0.5, j + 0.5, label,
                ha="center", va="center", fontsize=8,
                color="white" if neg_log_p[j, i] > 2 else "black",
            )

    ax.set_title(
        "Pairwise McNemar's Test Between AI Models\n($-\\log_{10}$ p-value)",
        fontsize=14, fontweight="bold", pad=15,
    )

    plt.tight_layout()
    save_figure(fig, "FigureE7")
    plt.close()


# ---------- FigureE8: Correlation matrix of test category pass rates ----------

def figure_e8(tests_df):
    """Lower-triangle Pearson correlation heatmap of per-customer test category pass rates."""
    setup_style()
    import seaborn as sns

    df = tests_df[
        (tests_df["is_human_baseline_dataset"] == True)
        & (tests_df["model_type"] != "human_baseline")
    ].copy()

    categories = [c for c in CATEGORY_ORDER if c in df["test_category"].unique()]

    # Per-customer pass rate by test_category (averaged across AI models)
    customer_cat = (
        df.groupby(["customer_name", "test_category"])["pass"]
        .mean()
        .reset_index()
    )
    pivot = customer_cat.pivot_table(
        index="customer_name", columns="test_category", values="pass",
    )
    pivot = pivot[[c for c in categories if c in pivot.columns]]

    # Pearson correlation
    corr = pivot.corr()

    # Mask upper triangle
    mask = np.triu(np.ones_like(corr, dtype=bool))

    # Rename columns/index for display
    cat_display = {
        "flag_accuracy": "Flag\nAccuracy",
        "claim_support": "Source\nFidelity",
        "source_reliability": "Source\nQuality",
        "work_relevance": "Work\nRelevance",
    }
    corr_display = corr.rename(index=cat_display, columns=cat_display)

    fig, ax = plt.subplots(figsize=(8, 7))

    sns.heatmap(
        corr_display, mask=mask,
        cmap="RdBu_r", vmin=-1, vmax=1, center=0,
        annot=True, fmt=".2f", square=True,
        linewidths=0.5, linecolor="white",
        cbar_kws={"label": "Pearson r", "shrink": 0.7},
        ax=ax,
    )

    ax.set_title(
        "Correlation of Per-Customer Pass Rates\nAcross Test Categories",
        fontsize=14, fontweight="bold", pad=15,
    )

    plt.tight_layout()
    save_figure(fig, "FigureE8")
    plt.close()


# ---------- Main ----------

def main():
    print("Generating extended model performance figures (FigureE1-FigureE8)")
    print("=" * 60)

    tests_df = load_tests()

    figure_e1(tests_df)
    figure_e2(tests_df)
    figure_e3(tests_df)
    figure_e4(tests_df)
    figure_e5(tests_df)
    figure_e6(tests_df)
    figure_e7(tests_df)
    figure_e8(tests_df)

    print("\nDone. All extended figures saved to paper/figures/")


if __name__ == "__main__":
    main()
