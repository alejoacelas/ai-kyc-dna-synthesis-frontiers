#!/usr/bin/env python3
"""
Compute statistical power analyses requested during revision:

- Wilson score 95% CIs on per-screener, per-metric pass rates (Figure 2 cells)
- Wilson CIs on overall per-screener pass rates (for Figure 4 / Discussion claims)
- McNemar's test for paired flag-accuracy comparison (best AI vs human baseline)
- Minimum detectable effect (MDE) at n = 41 profiles for paired proportion test
- Per-region flag-accuracy Wilson CIs (Figure 5)
- Supplementary forest plot of overall pass rates with 95% CIs

All numbers printed; forest plot saved to paper/figures/FigureJ1_forest_plot.png.

Run:
    uv run python scripts/compute_statistical_power.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.proportion import proportion_confint

import sys
sys.path.insert(0, str(Path(__file__).parent))
from style import (  # noqa: E402
    COLORS,
    MODEL_ORDER,
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    FIGURES_DIR,
    get_model_color,
    setup_style,
    shorten_model_label,
)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

BEST_AI = "Gemini 2.5 Pro (All Tools)"
HUMAN = "Human Baseline (30min)"


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    lo, hi = proportion_confint(successes, n, alpha=alpha, method="wilson")
    return float(lo), float(hi)


def fmt_pct(p: float) -> str:
    return f"{100*p:5.1f}%"


def fmt_ci(lo: float, hi: float) -> str:
    return f"[{100*lo:5.1f}%, {100*hi:5.1f}%]"


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------

def load_primary() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "tests.csv")
    # Primary 41-profile dataset (both humans and AI evaluated here)
    return df[df["is_human_baseline_dataset"]].copy()


# --------------------------------------------------------------------------
# (a) Per-screener, per-metric Wilson CIs
# --------------------------------------------------------------------------

def per_metric_cis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODEL_ORDER:
        sub = df[df["model_label"] == model]
        for cat in CATEGORY_ORDER:
            cat_sub = sub[sub["test_category"] == cat]
            n = len(cat_sub)
            if n == 0:
                continue
            k = int(cat_sub["pass"].sum())
            lo, hi = wilson_ci(k, n)
            rows.append({
                "model_label": model,
                "category": cat,
                "n": n,
                "passes": k,
                "rate": k / n,
                "ci_low": lo,
                "ci_high": hi,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (b) Overall pass rate per screener Wilson CIs
# --------------------------------------------------------------------------

def overall_cis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODEL_ORDER:
        sub = df[df["model_label"] == model]
        n = len(sub)
        if n == 0:
            continue
        k = int(sub["pass"].sum())
        lo, hi = wilson_ci(k, n)
        rows.append({
            "model_label": model,
            "n": n,
            "passes": k,
            "rate": k / n,
            "ci_low": lo,
            "ci_high": hi,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (c) McNemar on flag accuracy, best AI vs human baseline
# --------------------------------------------------------------------------

def profile_level_flag_accuracy(df: pd.DataFrame, model: str) -> pd.Series:
    """Profile-level flag-accuracy pass count (0-4) per profile for one screener."""
    sub = df[(df["model_label"] == model) & (df["test_category"] == "flag_accuracy")]
    # one row per (profile, flag criterion); aggregate pass count per profile
    return sub.groupby("customer_name")["pass"].sum()


def mcnemar_binary_full_pass(df: pd.DataFrame, model_a: str, model_b: str) -> dict:
    """Compare paired profile-level outcomes on flag accuracy.

    A profile is considered 'correct' when the screener passed all 4 flag
    criteria for that profile (the strictest binary summary).  We also
    report a 'majority' summary (>=3 of 4 passes) for robustness.
    """
    a_counts = profile_level_flag_accuracy(df, model_a)
    b_counts = profile_level_flag_accuracy(df, model_b)
    profiles = sorted(set(a_counts.index) & set(b_counts.index))
    a = (a_counts.loc[profiles] == 4).astype(int).values
    b = (b_counts.loc[profiles] == 4).astype(int).values
    # Contingency: rows = A (0/1), cols = B (0/1)
    table_full = np.array([
        [int(((a == 0) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())],
        [int(((a == 1) & (b == 0)).sum()), int(((a == 1) & (b == 1)).sum())],
    ])
    res_full = mcnemar(table_full, exact=True)

    a_maj = (a_counts.loc[profiles] >= 3).astype(int).values
    b_maj = (b_counts.loc[profiles] >= 3).astype(int).values
    table_maj = np.array([
        [int(((a_maj == 0) & (b_maj == 0)).sum()), int(((a_maj == 0) & (b_maj == 1)).sum())],
        [int(((a_maj == 1) & (b_maj == 0)).sum()), int(((a_maj == 1) & (b_maj == 1)).sum())],
    ])
    res_maj = mcnemar(table_maj, exact=True)

    # Also: test on the 164 paired flag-criterion outcomes (richer signal)
    merged = df[df["test_category"] == "flag_accuracy"].pivot_table(
        index=["customer_name", "metric_name"],
        columns="model_label",
        values="pass",
        aggfunc="first",
    )
    merged = merged.dropna(subset=[model_a, model_b])
    a_item = merged[model_a].astype(int).values
    b_item = merged[model_b].astype(int).values
    table_item = np.array([
        [int(((a_item == 0) & (b_item == 0)).sum()), int(((a_item == 0) & (b_item == 1)).sum())],
        [int(((a_item == 1) & (b_item == 0)).sum()), int(((a_item == 1) & (b_item == 1)).sum())],
    ])
    res_item = mcnemar(table_item, exact=True)

    return {
        "n_profiles": len(profiles),
        "a_rate_full": float(a.mean()),
        "b_rate_full": float(b.mean()),
        "table_full": table_full,
        "p_full": float(res_full.pvalue),
        "a_rate_maj": float(a_maj.mean()),
        "b_rate_maj": float(b_maj.mean()),
        "table_maj": table_maj,
        "p_maj": float(res_maj.pvalue),
        "n_items": int(merged.shape[0]),
        "a_item_rate": float(a_item.mean()),
        "b_item_rate": float(b_item.mean()),
        "table_item": table_item,
        "p_item": float(res_item.pvalue),
    }


# --------------------------------------------------------------------------
# (d) Minimum detectable effect at n = 41
# --------------------------------------------------------------------------

def mde_paired_proportion(n: int = 41, alpha: float = 0.05, power: float = 0.80,
                          p_baseline: float = 0.89) -> dict:
    """Solve for the smallest p_A - p_B detectable by an exact McNemar test.

    We use the standard normal-approximation formula for the discordant-pair
    test (sufficient for n >= 30).  Assuming the 'discordance rate' r = b + c
    (pairs that differ), and that p_A = p_B + d, the test statistic is
        z = |b - c| / sqrt(b + c) = |d| * n / sqrt(n * r).
    Power of 80% at alpha = 0.05 (two-sided) requires
        |d| * sqrt(n) / sqrt(r) >= z_{1-alpha/2} + z_{power}
    => MDE (d) = (z_a + z_b) * sqrt(r / n).
    We report MDE for several plausible discordance rates r.
    """
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    results = {}
    for r in (0.05, 0.10, 0.20, 0.30):
        mde = (z_a + z_b) * math.sqrt(r / n)
        results[r] = mde
    # Also: one-sample Wilson CI width at p = 0.89, n = 41 (useful for "89%" claim)
    lo, hi = wilson_ci(int(round(p_baseline * n)), n)
    results["wilson_width_at_p"] = (lo, hi)
    return results


# --------------------------------------------------------------------------
# (e) Per-region flag-accuracy CIs (Figure 5)
# --------------------------------------------------------------------------

def per_region_flag_cis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate flag-accuracy across all 10 AI model configurations, by region.

    Mirrors Figure 5 captions: rates computed as pass/total over all
    screener-profile-criterion rows within each region.
    """
    ai = df[(~df["is_human_baseline"]) & (df["test_category"] == "flag_accuracy")]
    rows = []
    for region, sub in ai.groupby("institution_country"):
        n = len(sub)
        k = int(sub["pass"].sum())
        lo, hi = wilson_ci(k, n)
        profs = sub["customer_name"].nunique()
        rows.append({
            "region": region,
            "profiles": profs,
            "n_obs": n,
            "passes": k,
            "rate": k / n,
            "ci_low": lo,
            "ci_high": hi,
        })
    return pd.DataFrame(rows).sort_values("rate", ascending=False)


# --------------------------------------------------------------------------
# Forest plot
# --------------------------------------------------------------------------

def forest_plot(overall: pd.DataFrame, outpath: Path) -> None:
    setup_style()
    df = overall.set_index("model_label").reindex(MODEL_ORDER).dropna(how="all").reset_index()
    # Drop 5-min baseline for the main panel - show as a separate marker.
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ys = np.arange(len(df))[::-1]
    for y, (_, row) in zip(ys, df.iterrows()):
        color = get_model_color(row["model_label"])
        ax.errorbar(
            row["rate"] * 100,
            y,
            xerr=[[(row["rate"] - row["ci_low"]) * 100], [(row["ci_high"] - row["rate"]) * 100]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.6,
            capsize=3,
            markersize=7,
        )
        ax.text(
            row["ci_high"] * 100 + 0.6,
            y,
            f"{row['rate']*100:.1f}% [{row['ci_low']*100:.1f}, {row['ci_high']*100:.1f}]",
            va="center",
            fontsize=9,
        )
    ax.set_yticks(ys)
    ax.set_yticklabels([shorten_model_label(m) for m in df["model_label"]], fontsize=10)
    ax.set_xlabel("Overall pass rate (all metrics pooled)")
    ax.set_xlim(40, 110)
    ax.axvline(df.loc[df["model_label"] == HUMAN, "rate"].iloc[0] * 100,
               color=COLORS["human_baseline"], linestyle=":", alpha=0.5, zorder=0)
    ax.set_title("Per-screener overall pass rate with 95% Wilson CIs\n"
                 "(41 profiles × 15 measurements = 615 binary outcomes per screener)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(outpath, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved forest plot: {outpath}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def print_table(title: str, df: pd.DataFrame, columns: list[str]) -> None:
    print(f"\n=== {title} ===")
    print(df[columns].to_string(index=False))


def main() -> None:
    df = load_primary()
    print(f"Loaded primary dataset: {len(df)} rows, "
          f"{df['customer_name'].nunique()} profiles, "
          f"{df['model_label'].nunique()} screeners.")

    # (a) per-metric
    per_metric = per_metric_cis(df)
    per_metric["rate_ci"] = per_metric.apply(
        lambda r: f"{100*r['rate']:.1f}% [{100*r['ci_low']:.1f}, {100*r['ci_high']:.1f}]", axis=1
    )
    print("\n=== (a) Per-screener per-metric Wilson 95% CIs ===")
    wide = per_metric.pivot(index="model_label", columns="category", values="rate_ci")
    wide = wide.reindex(MODEL_ORDER).reindex(columns=CATEGORY_ORDER)
    wide.columns = [CATEGORY_LABELS[c] for c in wide.columns]
    print(wide.to_string())

    # (b) overall
    overall = overall_cis(df)
    print("\n=== (b) Per-screener overall Wilson 95% CIs ===")
    overall_fmt = overall.copy()
    overall_fmt["ci"] = overall_fmt.apply(
        lambda r: f"[{100*r['ci_low']:.1f}%, {100*r['ci_high']:.1f}%]", axis=1
    )
    overall_fmt["rate_pct"] = overall_fmt["rate"].apply(lambda x: f"{100*x:.1f}%")
    print(overall_fmt[["model_label", "passes", "n", "rate_pct", "ci"]].to_string(index=False))

    # (c) McNemar
    print("\n=== (c) McNemar's paired test: best AI vs human baseline (flag accuracy) ===")
    res = mcnemar_binary_full_pass(df, BEST_AI, HUMAN)
    print(f"Profile-level, 'all 4 criteria correct':")
    print(f"  Best AI rate = {res['a_rate_full']*100:.1f}%, Human rate = {res['b_rate_full']*100:.1f}%")
    print(f"  2x2 table (rows=AI, cols=Human):\n{res['table_full']}")
    print(f"  Exact McNemar p = {res['p_full']:.3f}  (n={res['n_profiles']} paired profiles)")
    print(f"Profile-level, '>=3 of 4 criteria correct':")
    print(f"  Best AI rate = {res['a_rate_maj']*100:.1f}%, Human rate = {res['b_rate_maj']*100:.1f}%")
    print(f"  2x2 table:\n{res['table_maj']}")
    print(f"  Exact McNemar p = {res['p_maj']:.3f}")
    print(f"Criterion-level, paired on (profile × criterion):")
    print(f"  Best AI rate = {res['a_item_rate']*100:.1f}%, Human rate = {res['b_item_rate']*100:.1f}%")
    print(f"  2x2 table:\n{res['table_item']}")
    print(f"  Exact McNemar p = {res['p_item']:.3f}  (n={res['n_items']} paired items)")

    # (d) MDE
    print("\n=== (d) Minimum detectable effect at n=41 (paired McNemar, a=0.05, power=0.80) ===")
    mdes = mde_paired_proportion()
    for r in (0.05, 0.10, 0.20, 0.30):
        print(f"  Discordance rate {r:.2f}: MDE = {100*mdes[r]:.1f} percentage points")
    lo, hi = mdes["wilson_width_at_p"]
    print(f"  For comparison, Wilson CI at p=0.89, n=41: "
          f"[{100*lo:.1f}%, {100*hi:.1f}%] (half-width ~{100*(hi-lo)/2:.1f} pp)")

    # (e) region CIs
    print("\n=== (e) Per-region flag-accuracy Wilson CIs (pooled over AI models) ===")
    region = per_region_flag_cis(df)
    region["ci"] = region.apply(
        lambda r: f"[{100*r['ci_low']:.1f}%, {100*r['ci_high']:.1f}%]", axis=1
    )
    region["rate_pct"] = region["rate"].apply(lambda x: f"{100*x:.1f}%")
    print(region[["region", "profiles", "n_obs", "passes", "rate_pct", "ci"]].to_string(index=False))

    # Forest plot
    forest_plot(overall, FIGURES_DIR / "FigureJ1_forest_plot.png")


if __name__ == "__main__":
    main()
