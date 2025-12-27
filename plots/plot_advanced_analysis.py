#!/usr/bin/env python3
"""
Advanced analysis plots for KYC evaluation results.

Generates:
- Heatmap of models (incl. human baseline) vs customer type
- Correlation matrix of pass rates between models
- Pass rate vs input token count scatter
- Pass rate vs cost scatter
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from style import (
    DATA_DIR, COLORS, MODEL_ORDER, CATEGORY_ORDER, CATEGORY_LABELS,
    get_model_color, shorten_model_label, save_figure,
    setup_style
)

setup_style()

# Random seed for reproducibility in sampling
RANDOM_SEED = 42


def load_data():
    """Load both datasets."""
    df_tests = pd.read_csv(DATA_DIR / "tests.csv")
    df_tests["pass"] = df_tests["pass"].astype(str) == "True"

    df_responses = pd.read_csv(DATA_DIR / "responses.csv")
    return df_tests, df_responses


def filter_hb_dataset_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to human baseline dataset subset only (for AI vs human comparisons)."""
    return df[df["is_human_baseline_dataset"] == True].copy()


def filter_30min_human_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out 5min human baseline, keep only 30min."""
    return df[df["model_label"] != "Human Baseline (5min)"].copy()


def filter_ai_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to AI models only (exclude human baseline)."""
    return df[df["model_type"] != "human_baseline"].copy()


# =============================================================================
# 1. Heatmap: Models vs Customer Type
# =============================================================================

def plot_model_vs_customer_heatmap(df: pd.DataFrame, suffix: str = ""):
    """Plot heatmap of pass rates by model and customer type."""
    # Customer type order
    CUSTOMER_ORDER = [
        "Controlled Agent Academia",
        "Controlled Agent Industry",
        "General Life Science Customers",
        "Sanctioned Institution Customers",
    ]

    # Shorter labels for customer types
    CUSTOMER_LABELS = {
        "Controlled Agent Academia": "Ctrl Academia",
        "Controlled Agent Industry": "Ctrl Industry",
        "General Life Science Customers": "General LifeSci",
        "Sanctioned Institution Customers": "Sanctioned Inst",
    }

    # Calculate pass rates
    pivot = df.pivot_table(
        values="pass",
        index="model_label",
        columns="customer_type",
        aggfunc="mean"
    ) * 100

    # Reorder
    models = [m for m in MODEL_ORDER if m in pivot.index]
    customers = [c for c in CUSTOMER_ORDER if c in pivot.columns]
    pivot = pivot.loc[models, customers]

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
        xticklabels=[CUSTOMER_LABELS.get(c, c) for c in customers],
    )

    ax.set_title("Pass Rate by Model and Customer Type")
    ax.set_xlabel("Customer Type")
    ax.set_ylabel("Model")

    plt.tight_layout()
    save_figure(fig, f"model_vs_customer_heatmap{suffix}")
    plt.close()


# =============================================================================
# 2. Correlation Matrix of Pass Rates Between Models
# =============================================================================

def compute_model_pass_rate_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute correlation of pass rates between models.

    For each customer (eval_id), compute binary pass/fail for each model,
    then compute correlation across all customers.
    """
    # Pivot to get pass/fail per eval_id and model
    pivot = df.pivot_table(
        values="pass",
        index=["eval_id", "metric_name"],  # Unique test instance
        columns="model_label",
        aggfunc="mean"  # Should be 0 or 1 for binary pass
    )

    # Calculate correlation between models
    corr = pivot.corr()
    return corr


def plot_model_correlation_matrices(df: pd.DataFrame, suffix: str = ""):
    """
    Plot correlation matrices of pass rates between models.

    Creates a single figure with:
    - Overall correlation (all tests)
    - Correlation for each test category
    """
    categories = [c for c in CATEGORY_ORDER if c in df["test_category"].unique()]
    n_plots = 1 + len(categories)  # Overall + each category

    # Determine grid layout
    if n_plots <= 3:
        nrows, ncols = 1, n_plots
    else:
        ncols = 3
        nrows = (n_plots + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    axes = np.array(axes).flatten()  # Ensure it's always iterable

    # Get models present in data (in order)
    models_present = [m for m in MODEL_ORDER if m in df["model_label"].unique()]
    short_labels = [shorten_model_label(m) for m in models_present]

    # Plot overall correlation
    corr_overall = compute_model_pass_rate_correlation(df)
    corr_overall = corr_overall.loc[models_present, models_present]

    sns.heatmap(
        corr_overall,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        center=0,
        ax=axes[0],
        xticklabels=short_labels,
        yticklabels=short_labels,
        square=True,
        cbar_kws={"shrink": 0.8},
    )
    axes[0].set_title("All Tests", fontsize=12, fontweight="bold")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].tick_params(axis="y", rotation=0)

    # Plot correlation for each category
    for i, cat in enumerate(categories, start=1):
        df_cat = df[df["test_category"] == cat]
        corr_cat = compute_model_pass_rate_correlation(df_cat)

        # Reorder to match overall
        models_in_cat = [m for m in models_present if m in corr_cat.index]
        corr_cat = corr_cat.loc[models_in_cat, models_in_cat]
        short_labels_cat = [shorten_model_label(m) for m in models_in_cat]

        sns.heatmap(
            corr_cat,
            annot=True,
            fmt=".2f",
            cmap="RdBu_r",
            vmin=-1,
            vmax=1,
            center=0,
            ax=axes[i],
            xticklabels=short_labels_cat,
            yticklabels=short_labels_cat,
            square=True,
            cbar_kws={"shrink": 0.8},
        )
        axes[i].set_title(CATEGORY_LABELS.get(cat, cat), fontsize=12, fontweight="bold")
        axes[i].tick_params(axis="x", rotation=45)
        axes[i].tick_params(axis="y", rotation=0)

    # Hide unused axes
    for j in range(n_plots, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Pass Rate Correlation Between Models", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_figure(fig, f"model_correlation_matrices{suffix}")
    plt.close()


# =============================================================================
# 3. Pass Rate vs Input Token Count (Scatter)
# =============================================================================

def plot_pass_rate_vs_tokens(df_tests: pd.DataFrame, df_responses: pd.DataFrame,
                              sample_size: int = 200, suffix: str = ""):
    """
    Plot pass rate vs input token count.

    Uses a random sample to avoid cluttering.
    Colored by model.
    """
    # Filter to AI models only (human baseline has no tokens)
    df_responses_ai = df_responses[df_responses["model_type"] != "human_baseline"].copy()

    # Merge to get pass rate per response
    # For each response, calculate pass rate across all tests
    response_pass_rates = df_tests.groupby("result_id").agg({
        "pass": "mean",
        "model_label": "first",
    }).reset_index()
    response_pass_rates.columns = ["result_id", "pass_rate", "model_label"]
    response_pass_rates["pass_rate"] *= 100

    # Merge with responses to get token counts
    df_merged = df_responses_ai.merge(response_pass_rates[["result_id", "pass_rate"]],
                                       on="result_id", how="inner")

    # Random sample
    if len(df_merged) > sample_size:
        df_sample = df_merged.sample(n=sample_size, random_state=RANDOM_SEED)
    else:
        df_sample = df_merged

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Get unique models in order
    models_in_data = [m for m in MODEL_ORDER if m in df_sample["model_label"].unique()]

    # Scatter plot for each model
    for model in models_in_data:
        df_model = df_sample[df_sample["model_label"] == model]
        color = get_model_color(model)
        ax.scatter(
            df_model["prompt_tokens"] / 1000,  # Convert to thousands
            df_model["pass_rate"],
            c=color,
            label=shorten_model_label(model),
            alpha=0.6,
            s=50,
            edgecolors="white",
            linewidth=0.5,
        )

    # Add trend line (overall)
    x = df_sample["prompt_tokens"] / 1000
    y = df_sample["pass_rate"]
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.7, linewidth=2,
            label=f"Trend (r={np.corrcoef(x, y)[0,1]:.2f})")

    # Customize
    ax.set_xlabel("Input Tokens (thousands)")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title(f"Pass Rate vs Input Token Count (n={len(df_sample)} samples)")
    ax.set_ylim(0, 105)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)

    plt.tight_layout()
    save_figure(fig, f"pass_rate_vs_tokens{suffix}")
    plt.close()


# =============================================================================
# 4. Pass Rate vs Cost (Scatter)
# =============================================================================

def plot_pass_rate_vs_cost(df_tests: pd.DataFrame, df_responses: pd.DataFrame,
                            sample_size: int = 200, suffix: str = ""):
    """
    Plot pass rate vs cost per response.

    Uses a random sample to avoid cluttering.
    Colored by model.
    """
    # Filter to AI models only (human baseline has no cost)
    df_responses_ai = df_responses[df_responses["model_type"] != "human_baseline"].copy()

    # Merge to get pass rate per response
    response_pass_rates = df_tests.groupby("result_id").agg({
        "pass": "mean",
        "model_label": "first",
    }).reset_index()
    response_pass_rates.columns = ["result_id", "pass_rate", "model_label"]
    response_pass_rates["pass_rate"] *= 100

    # Merge with responses to get cost
    df_merged = df_responses_ai.merge(response_pass_rates[["result_id", "pass_rate"]],
                                       on="result_id", how="inner")

    # Random sample
    if len(df_merged) > sample_size:
        df_sample = df_merged.sample(n=sample_size, random_state=RANDOM_SEED)
    else:
        df_sample = df_merged

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Get unique models in order
    models_in_data = [m for m in MODEL_ORDER if m in df_sample["model_label"].unique()]

    # Scatter plot for each model
    for model in models_in_data:
        df_model = df_sample[df_sample["model_label"] == model]
        color = get_model_color(model)
        ax.scatter(
            df_model["total_cost"],
            df_model["pass_rate"],
            c=color,
            label=shorten_model_label(model),
            alpha=0.6,
            s=50,
            edgecolors="white",
            linewidth=0.5,
        )

    # Add trend line (overall)
    x = df_sample["total_cost"]
    y = df_sample["pass_rate"]
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.7, linewidth=2,
            label=f"Trend (r={np.corrcoef(x, y)[0,1]:.2f})")

    # Customize
    ax.set_xlabel("Cost per Response ($)")
    ax.set_ylabel("Pass Rate (%)")
    ax.set_title(f"Pass Rate vs Cost (n={len(df_sample)} samples)")
    ax.set_ylim(0, 105)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)

    plt.tight_layout()
    save_figure(fig, f"pass_rate_vs_cost{suffix}")
    plt.close()


# =============================================================================
# Main
# =============================================================================

def main():
    """Generate all advanced analysis plots."""
    print("Loading data...")
    df_tests_raw, df_responses_raw = load_data()
    print(f"Loaded {len(df_tests_raw)} tests and {len(df_responses_raw)} responses")

    # Prepare filtered datasets
    # HB dataset subset with both human baselines
    df_tests_hb_all = filter_hb_dataset_only(df_tests_raw)
    df_responses_hb_all = filter_hb_dataset_only(df_responses_raw)
    print(f"HB dataset (both human baselines): {len(df_tests_hb_all)} tests")

    # AI only (for scatter plots that need token/cost data)
    df_tests_ai = filter_ai_only(df_tests_raw)
    df_responses_ai = filter_ai_only(df_responses_raw)
    print(f"AI models: {len(df_tests_ai)} tests, {len(df_responses_ai)} responses")

    print("\nGenerating plots...")

    # 1. Model vs Customer Type heatmap (include human baselines)
    print("  - Model vs Customer Type heatmap...")
    plot_model_vs_customer_heatmap(df_tests_hb_all, suffix="_hb_comparison")

    # 2. Correlation matrices (include human baselines)
    print("  - Model correlation matrices...")
    plot_model_correlation_matrices(df_tests_hb_all, suffix="_hb_comparison")

    # 3. Pass rate vs tokens (AI only)
    print("  - Pass rate vs tokens scatter...")
    plot_pass_rate_vs_tokens(df_tests_ai, df_responses_ai, sample_size=300)

    # 4. Pass rate vs cost (AI only)
    print("  - Pass rate vs cost scatter...")
    plot_pass_rate_vs_cost(df_tests_ai, df_responses_ai, sample_size=300)

    print("\nDone!")


if __name__ == "__main__":
    main()
