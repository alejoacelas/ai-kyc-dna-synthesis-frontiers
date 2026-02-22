#!/usr/bin/env python3
"""
Generate extended model performance figures (FigureE1, FigureE5, FigureE6, FigureE8).

FigureE1: Pass rate with 95% Wilson confidence intervals (horizontal dot chart, sorted)
FigureE5: Per-customer swarm plot
FigureE6: Flag vs non-flag pass rate scatter
FigureE8: Correlation matrix of test category pass rates
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy.stats import pearsonr

from style import (
    DATA_DIR, COLORS,
    MODEL_ORDER, CATEGORY_ORDER,
    setup_style, save_figure, get_model_color,
    shorten_model_label,
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


# ---------- Helper function for clustered Wilson CIs ----------

def compute_design_effect(model_df):
    """Compute design effect for clustered data (tests clustered within customers)."""
    # Per-customer pass rates
    customer_rates = model_df.groupby('customer_name')['pass'].agg(['mean', 'count'])

    # Overall pass rate and sample info
    p_overall = model_df['pass'].mean()
    n_total = len(model_df)
    k = len(customer_rates)  # number of clusters (customers)
    n_j = customer_rates['count'].values  # tests per customer

    # Compute ICC using one-way ANOVA decomposition
    p_j = customer_rates['mean'].values
    SSB = np.sum(n_j * (p_j - p_overall)**2)
    SSW = np.sum(n_j * p_j * (1 - p_j))

    MSB = SSB / (k - 1)
    MSW = SSW / (n_total - k)

    # Effective cluster size for unbalanced design
    n_0 = (n_total - np.sum(n_j**2) / n_total) / (k - 1)

    # ICC (bounded below by 0)
    ICC = max(0, (MSB - MSW) / (MSB + (n_0 - 1) * MSW))

    # Design effect
    avg_cluster_size = n_total / k
    DEFF = 1 + (avg_cluster_size - 1) * ICC

    return DEFF, ICC


# ---------- FigureE1: Pass rate with Wilson CI (horizontal dot chart, sorted) ----------

def figure_e1(tests_df):
    """Horizontal dot chart of overall pass rates with 95% Wilson CIs, sorted descending."""
    setup_style()

    df = tests_df[tests_df["is_human_baseline_dataset"] == True].copy()

    # Calculate pass rates and cluster-adjusted Wilson CI per model
    stats = df.groupby("model_label")["pass"].agg(["sum", "count"]).reset_index()
    stats.columns = ["model_label", "successes", "n"]
    stats["p_hat"] = stats["successes"] / stats["n"]

    # Compute design effects and effective sample sizes
    stats["design_effect"] = 0.0
    stats["n_eff"] = 0.0

    for i, model in enumerate(stats["model_label"]):
        model_df = df[df["model_label"] == model]
        deff, icc = compute_design_effect(model_df)
        stats.loc[i, "design_effect"] = deff
        stats.loc[i, "n_eff"] = stats.loc[i, "n"] / deff

    # Wilson CI using effective sample sizes
    z = 1.96
    stats["denom"] = 1 + z**2 / stats["n_eff"]
    stats["center"] = (stats["p_hat"] + z**2 / (2 * stats["n_eff"])) / stats["denom"]
    stats["margin"] = (
        z
        * np.sqrt((stats["p_hat"] * (1 - stats["p_hat"]) + z**2 / (4 * stats["n_eff"])) / stats["n_eff"])
        / stats["denom"]
    )
    stats["lower"] = stats["center"] - stats["margin"]
    stats["upper"] = stats["center"] + stats["margin"]

    # Convert to percentages
    stats["pass_rate"] = stats["p_hat"] * 100
    stats["ci_lower"] = stats["lower"] * 100
    stats["ci_upper"] = stats["upper"] * 100

    # Sort by pass_rate descending (top of chart = highest)
    stats = stats.sort_values("pass_rate", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    y = np.arange(len(stats))
    colors = [get_model_color(m) for m in stats["model_label"]]

    # Error bars: asymmetric [lower_err, upper_err]
    lower_err = stats["pass_rate"].values - stats["ci_lower"].values
    upper_err = stats["ci_upper"].values - stats["pass_rate"].values

    ax.errorbar(
        stats["pass_rate"], y,
        xerr=[lower_err, upper_err],
        fmt="none", ecolor="gray", elinewidth=1.5, capsize=4, zorder=3,
    )
    ax.scatter(
        stats["pass_rate"], y,
        c=colors, s=100, zorder=4, edgecolors="white", linewidth=0.5,
    )

    # Value labels next to each dot
    for i, (rate, label) in enumerate(zip(stats["pass_rate"], stats["model_label"])):
        ax.text(
            rate + upper_err[i] + 1.0, i, f"{rate:.1f}%",
            va="center", ha="left", fontsize=9, fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels([shorten_model_label(m) for m in stats["model_label"]], fontsize=11)
    ax.set_xlabel("Pass Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Screener", fontsize=12, fontweight="bold")
    ax.set_title(
        "Overall Pass Rate with 95% Cluster-Adjusted Wilson Confidence Intervals",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlim(0, 100)

    # Legend
    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="AI - All Tools"),
        Patch(facecolor=COLORS["web_only"], label="AI - Web Only"),
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

    # Per-group mean lines
    for i, ct in enumerate(CUSTOMER_TYPE_ORDER):
        group = customer_rates[customer_rates["customer_type"] == ct]
        if len(group) > 0:
            group_mean = group["pass_rate"].mean()
            group_color = palette.get(ct, "black")
            ax.hlines(group_mean, i - 0.3, i + 0.3, colors=group_color,
                      linewidth=2.5, zorder=5)
            ax.text(i + 0.35, group_mean, f"{group_mean:.1f}%", va="center", fontsize=9,
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
    print("Generating extended model performance figures (FigureE1, E5, E6, E8)")
    print("=" * 60)

    tests_df = load_tests()

    figure_e1(tests_df)
    figure_e5(tests_df)
    figure_e6(tests_df)
    figure_e8(tests_df)

    print("\nDone. All extended figures saved to paper/figures/")


if __name__ == "__main__":
    main()
