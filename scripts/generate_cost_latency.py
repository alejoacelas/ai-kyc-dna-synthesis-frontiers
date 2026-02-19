#!/usr/bin/env python3
"""
Generate cost and latency supplementary figures (FigureH1–FigureH7).

FigureH1: Token cost decomposition (stacked bar)
FigureH2: Cost vs pass rate (full 134-profile dataset)
FigureH3: Human vs AI screening time (horizontal bar)
FigureH4: Latency distribution (boxplot)
FigureH5: Latency vs pass rate (scatter)
FigureH6: Token consumption (grouped bar)
FigureH7: Response length vs pass rate (scatter)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy import stats as scipy_stats
from matplotlib.patches import Patch

from style import (
    DATA_DIR, COLORS, MODEL_LABELS_NO_TIME, MODEL_ORDER,
    setup_style, save_figure, get_model_color, shorten_model_label_no_time,
)

# Module-level constants
COST_COLORS = {"input": "#6366f1", "output": "#fb7185", "web_search": "#2dd4bf"}
TOKEN_COLORS = {"prompt": "#3498db", "completion": "#f39c12"}

# Map model_name (from responses.csv) to pricing keys in token_pricing.yaml
MODEL_PRICING_MAP = {
    "anthropic/claude-sonnet-4": ("claude", "sonnet"),
    "minimax/minimax-m2": ("minimax", "m2"),
    "z-ai/glm-4.6": ("zhipu", "glm-4.6"),
    "google/gemini-2.5-pro": ("gemini", "gemini-2.5-pro"),
    "x-ai/grok-4": ("grok", "grok-4"),
}


def load_tests():
    return pd.read_csv(DATA_DIR / "tests.csv")


def load_responses():
    return pd.read_csv(DATA_DIR / "responses.csv")


def load_token_pricing():
    with open(DATA_DIR / "token_pricing.yaml") as f:
        return yaml.safe_load(f)


def _get_pricing(pricing, model_name):
    """Look up (input_price, output_price) per million tokens for a model."""
    key = MODEL_PRICING_MAP.get(model_name)
    if key is None:
        return None, None
    provider, variant = key
    entry = pricing.get(provider, {}).get(variant, {})
    return entry.get("input"), entry.get("output")


# ---------- FigureH1: Token cost decomposition (stacked bar) ----------

def figure_h1(responses_df):
    """Token cost decomposition into input, output, and web search costs."""
    setup_style()
    pricing = load_token_pricing()

    df = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    # Compute per-row input and output costs from token counts and pricing
    input_costs = []
    output_costs = []
    for _, row in df.iterrows():
        inp_price, out_price = _get_pricing(pricing, row["model_name"])
        if inp_price is not None and out_price is not None:
            input_costs.append(row["prompt_tokens"] * inp_price / 1e6)
            output_costs.append(row["completion_tokens"] * out_price / 1e6)
        else:
            input_costs.append(0.0)
            output_costs.append(0.0)

    df["input_cost"] = input_costs
    df["output_cost"] = output_costs

    # Sum per customer per model, then mean per model
    customer_agg = df.groupby(["customer_name", "model_label"]).agg(
        {"input_cost": "sum", "output_cost": "sum", "web_search_cost": "sum"}
    ).reset_index()

    model_agg = customer_agg.groupby("model_label").agg(
        {"input_cost": "mean", "output_cost": "mean", "web_search_cost": "mean"}
    )
    model_agg["total"] = model_agg["input_cost"] + model_agg["output_cost"] + model_agg["web_search_cost"]
    models = [m for m in MODEL_ORDER if m in model_agg.index and "Human" not in m]
    model_agg = model_agg.loc[models]
    model_agg = model_agg.sort_values("total", ascending=False)
    models = model_agg.index.tolist()

    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(models))
    width = 0.7

    inp = model_agg["input_cost"].values
    out = model_agg["output_cost"].values
    web = model_agg["web_search_cost"].values

    ax.bar(x, inp, width, label="Input tokens", color=COST_COLORS["input"], alpha=0.9)
    ax.bar(x, out, width, bottom=inp, label="Output tokens", color=COST_COLORS["output"], alpha=0.9)
    ax.bar(x, web, width, bottom=inp + out, label="Web search", color=COST_COLORS["web_search"], alpha=0.9)

    for i, total in enumerate(model_agg["total"].values):
        ax.text(i, total + 0.002, f"${total:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(
        [MODEL_LABELS_NO_TIME.get(m, m) for m in models], rotation=45, ha="right", fontsize=10
    )
    ax.set_ylabel("Mean Cost per Customer (USD)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title("Token Cost Decomposition by Model", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylim(0, model_agg["total"].max() * 1.15)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureH1")
    plt.close()


# ---------- FigureH2: Cost vs pass rate (full dataset) ----------

SCATTER_COLORS = {
    "all_tools": "#1e40af",
    "web_only": "#93c5fd",
}


def figure_h2(responses_df, tests_df):
    """Cost vs pass rate scatter for the full 134-profile dataset."""
    setup_style()

    # Cost from responses (full dataset, AI only)
    df_ai = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == False)
    ].copy()

    customer_costs = df_ai.groupby(["customer_name", "model_label"]).agg(
        {"model_cost": "sum", "web_search_cost": "sum"}
    ).reset_index()
    customer_costs["ai_cost"] = customer_costs["model_cost"] + customer_costs["web_search_cost"]

    cost_agg = customer_costs.groupby("model_label")["ai_cost"].mean()

    # Pass rate from tests (full dataset, AI only)
    tests_full = tests_df[
        (tests_df["is_human_baseline"] == False)
        & (tests_df["is_human_baseline_dataset"] == False)
    ]
    pass_agg = tests_full.groupby("model_label")["pass"].mean() * 100

    models = [m for m in MODEL_ORDER if m in cost_agg.index and m in pass_agg.index and "Human" not in m]
    costs = cost_agg.loc[models]
    rates = pass_agg.loc[models]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [SCATTER_COLORS["all_tools"] if "(All Tools)" in m else SCATTER_COLORS["web_only"] for m in models]
    ax.scatter(costs, rates, c=colors, s=150, edgecolors="white", linewidth=1.5, alpha=0.8)

    for model in models:
        ax.annotate(
            shorten_model_label_no_time(model),
            (costs[model], rates[model]),
            xytext=(5, 5), textcoords="offset points", fontsize=9,
        )

    # Linear regression
    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(costs, rates)
    r_squared = r_value ** 2
    x_line = np.linspace(costs.min() * 0.9, costs.max() * 1.1, 100)
    ax.plot(x_line, slope * x_line + intercept, "--", color="gray", alpha=0.5, linewidth=1)

    ax.annotate(
        f"$R^2$ = {r_squared:.3f}",
        xy=(0.95, 0.95), xycoords="axes fraction", ha="right", va="top", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
    )

    legend_elements = [
        Patch(facecolor=SCATTER_COLORS["web_only"], label="Web Only"),
        Patch(facecolor=SCATTER_COLORS["all_tools"], label="All Tools"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    ax.set_xlabel("Average AI Screening Cost per Customer (USD)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Cost vs Pass Rate (Full 134-Profile Dataset)", fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureH2")
    plt.close()


# ---------- FigureH3: Human vs AI screening time (horizontal bar) ----------

def figure_h3(responses_df):
    """Horizontal bar chart comparing screening time per customer."""
    setup_style()

    df = responses_df[responses_df["is_human_baseline_dataset"] == True].copy()

    # AI models: sum latency_ms across prompts per customer, convert to minutes
    df_ai = df[df["model_type"] != "human_baseline"].copy()
    df_ai["latency_min"] = df_ai["latency_ms"] / 60000.0

    ai_customer = df_ai.groupby(["customer_name", "model_label"])["latency_min"].sum().reset_index()
    ai_model_time = ai_customer.groupby("model_label")["latency_min"].mean()

    # Human baselines: sum time_to_complete_minutes across prompts per customer
    df_human = df[df["model_type"] == "human_baseline"].copy()
    human_customer = df_human.groupby(["customer_name", "model_label"])["time_to_complete_minutes"].sum().reset_index()
    human_model_time = human_customer.groupby("model_label")["time_to_complete_minutes"].mean()

    # Combine
    all_times = pd.concat([ai_model_time.rename("time_min"), human_model_time.rename("time_min")])

    models = [m for m in MODEL_ORDER if m in all_times.index]
    times = all_times.loc[models]

    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(models))

    bar_colors = [get_model_color(m) for m in models]
    bars = ax.barh(y, times.values, color=bar_colors, alpha=0.85, edgecolor="white", height=0.7)

    # Value labels
    for i, (bar, val) in enumerate(zip(bars, times.values)):
        ax.text(val + times.max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f} min", ha="left", va="center", fontsize=9, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels([MODEL_LABELS_NO_TIME.get(m, m) for m in models], fontsize=10)
    ax.set_xlabel("Mean Screening Time per Customer (minutes)", fontsize=12, fontweight="bold")
    ax.set_title("Screening Time: Human vs AI", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, times.max() * 1.2)
    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    legend_elements = [
        Patch(facecolor=COLORS["all_tools"], label="All Tools (AT)"),
        Patch(facecolor=COLORS["web_only"], label="Web Only (W)"),
        Patch(facecolor=COLORS["human_baseline"], label="Human Baseline"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    plt.tight_layout()
    save_figure(fig, "FigureH3")
    plt.close()


# ---------- FigureH4: Latency distribution (boxplot) ----------

def figure_h4(responses_df):
    """Boxplot of per-customer total latency for AI models."""
    setup_style()

    df = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    df["latency_min"] = df["latency_ms"] / 60000.0

    # Total latency per customer = sum across both prompts
    customer_latency = df.groupby(["customer_name", "model_label"])["latency_min"].sum().reset_index()

    models = [m for m in MODEL_ORDER if m in customer_latency["model_label"].unique() and "Human" not in m]
    box_data = [customer_latency[customer_latency["model_label"] == m]["latency_min"].values for m in models]
    box_colors = [get_model_color(m) for m in models]

    fig, ax = plt.subplots(figsize=(12, 7))
    bp = ax.boxplot(
        box_data, patch_artist=True, widths=0.6,
        medianprops=dict(color="black", linewidth=1.5),
        flierprops=dict(marker="o", markersize=4, alpha=0.5),
    )

    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    ax.set_xticks(range(1, len(models) + 1))
    ax.set_xticklabels(
        [MODEL_LABELS_NO_TIME.get(m, m) for m in models], rotation=45, ha="right", fontsize=10
    )
    ax.set_ylabel("Total Latency per Customer (minutes)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title("Latency Distribution by Model", fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureH4")
    plt.close()


# ---------- FigureH5: Latency vs pass rate (scatter) ----------

def figure_h5(responses_df, tests_df):
    """Latency vs pass rate scatter for AI models on human baseline dataset."""
    setup_style()

    df_ai = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    df_ai["latency_min"] = df_ai["latency_ms"] / 60000.0
    customer_latency = df_ai.groupby(["customer_name", "model_label"])["latency_min"].sum().reset_index()
    latency_agg = customer_latency.groupby("model_label")["latency_min"].mean()

    # Pass rate
    tests_sub = tests_df[
        (tests_df["is_human_baseline"] == False)
        & (tests_df["is_human_baseline_dataset"] == True)
    ]
    pass_agg = tests_sub.groupby("model_label")["pass"].mean() * 100

    models = [m for m in MODEL_ORDER if m in latency_agg.index and m in pass_agg.index and "Human" not in m]
    latencies = latency_agg.loc[models]
    rates = pass_agg.loc[models]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [SCATTER_COLORS["all_tools"] if "(All Tools)" in m else SCATTER_COLORS["web_only"] for m in models]
    ax.scatter(latencies, rates, c=colors, s=150, edgecolors="white", linewidth=1.5, alpha=0.8)

    for model in models:
        ax.annotate(
            shorten_model_label_no_time(model),
            (latencies[model], rates[model]),
            xytext=(5, 5), textcoords="offset points", fontsize=9,
        )

    legend_elements = [
        Patch(facecolor=SCATTER_COLORS["web_only"], label="Web Only (W)"),
        Patch(facecolor=SCATTER_COLORS["all_tools"], label="All Tools (AT)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    ax.set_xlabel("Mean Latency per Customer (minutes)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Latency vs Pass Rate", fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureH5")
    plt.close()


# ---------- FigureH6: Token consumption (grouped bar) ----------

def figure_h6(responses_df):
    """Grouped bar chart of prompt and completion tokens per model."""
    setup_style()

    df = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    # Sum across prompts per customer, then mean across customers
    customer_tokens = df.groupby(["customer_name", "model_label"]).agg(
        {"prompt_tokens": "sum", "completion_tokens": "sum"}
    ).reset_index()

    model_tokens = customer_tokens.groupby("model_label").agg(
        {"prompt_tokens": "mean", "completion_tokens": "mean"}
    )

    models = [m for m in MODEL_ORDER if m in model_tokens.index and "Human" not in m]
    model_tokens = model_tokens.loc[models]

    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(models))
    width = 0.35

    bars_prompt = ax.bar(
        x - width / 2, model_tokens["prompt_tokens"].values, width,
        label="Prompt tokens", color=TOKEN_COLORS["prompt"], alpha=0.85,
    )
    bars_completion = ax.bar(
        x + width / 2, model_tokens["completion_tokens"].values, width,
        label="Completion tokens", color=TOKEN_COLORS["completion"], alpha=0.85,
    )

    # Value labels rotated 90 degrees
    for bar in bars_prompt:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + model_tokens["prompt_tokens"].max() * 0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=8, rotation=90,
        )
    for bar in bars_completion:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + model_tokens["prompt_tokens"].max() * 0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=8, rotation=90,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [MODEL_LABELS_NO_TIME.get(m, m) for m in models], rotation=45, ha="right", fontsize=10
    )
    ax.set_ylabel("Mean Tokens per Customer", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax.set_title("Token Consumption by Model", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Leave headroom for rotated labels
    max_val = max(model_tokens["prompt_tokens"].max(), model_tokens["completion_tokens"].max())
    ax.set_ylim(0, max_val * 1.25)

    plt.tight_layout()
    save_figure(fig, "FigureH6")
    plt.close()


# ---------- FigureH7: Response length vs pass rate (scatter) ----------

def figure_h7(responses_df, tests_df):
    """Response length vs pass rate scatter for AI models."""
    setup_style()

    df_ai = responses_df[
        (responses_df["model_type"] != "human_baseline")
        & (responses_df["is_human_baseline_dataset"] == True)
    ].copy()

    # Mean response length per customer (sum across prompts, then mean across customers)
    customer_len = df_ai.groupby(["customer_name", "model_label"])["response_length"].sum().reset_index()
    length_agg = customer_len.groupby("model_label")["response_length"].mean()

    # Pass rate
    tests_sub = tests_df[
        (tests_df["is_human_baseline"] == False)
        & (tests_df["is_human_baseline_dataset"] == True)
    ]
    pass_agg = tests_sub.groupby("model_label")["pass"].mean() * 100

    models = [m for m in MODEL_ORDER if m in length_agg.index and m in pass_agg.index and "Human" not in m]
    lengths = length_agg.loc[models]
    rates = pass_agg.loc[models]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [SCATTER_COLORS["all_tools"] if "(All Tools)" in m else SCATTER_COLORS["web_only"] for m in models]
    ax.scatter(lengths, rates, c=colors, s=150, edgecolors="white", linewidth=1.5, alpha=0.8)

    for model in models:
        ax.annotate(
            shorten_model_label_no_time(model),
            (lengths[model], rates[model]),
            xytext=(5, 5), textcoords="offset points", fontsize=9,
        )

    legend_elements = [
        Patch(facecolor=SCATTER_COLORS["web_only"], label="Web Only (W)"),
        Patch(facecolor=SCATTER_COLORS["all_tools"], label="All Tools (AT)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    ax.set_xlabel("Mean Response Length per Customer (chars)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Overall Pass Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Response Length vs Pass Rate", fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_figure(fig, "FigureH7")
    plt.close()


# ---------- Main ----------

def main():
    print("Generating cost and latency figures (FigureH1-FigureH7)")
    print("=" * 60)

    tests_df = load_tests()
    responses_df = load_responses()

    figure_h1(responses_df)
    figure_h2(responses_df, tests_df)
    figure_h3(responses_df)
    figure_h4(responses_df)
    figure_h5(responses_df, tests_df)
    figure_h6(responses_df)
    figure_h7(responses_df, tests_df)

    print("\nDone. All cost/latency figures saved to paper/figures/")


if __name__ == "__main__":
    main()
