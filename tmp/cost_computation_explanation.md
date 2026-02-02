# Cost Computation Explanation

## Overview

This document explains how screening costs are computed for the figure and proposes an updated Table 2 that aligns with the figure methodology.

---

## Figure Cost Breakdown Computation

**Script:** `scripts/figures/generate_figure_cost_breakdown.py`

**Formula per customer:**

```text
Total Cost = model_cost + web_search_cost + $1.08 (human review)
```

**How it's computed:**

1. **Filter:** AI models only, human baseline subset (40 profiles)
2. **Aggregate:** Sum `model_cost` and `web_search_cost` across BOTH prompts (main + background_work) per customer per model
3. **Average:** Calculate mean cost per customer for each model
4. **Add human review:** Add flat $1.08 per screening for human review step

**Verification:** `total_cost = model_cost + web_search_cost` (confirmed, max diff < $0.000001)

---

## Updated Table 2 (Both Prompts + Human Review)

| Model | Model Cost | Web Search | AI Total | + Human Review ($1.08) |
| ----- | ---------- | ---------- | -------- | ---------------------- |
| Claude Sonnet 4 (Web) | $0.603 | $0.077 | $0.681 | **$1.76** |
| Claude Sonnet 4 (All Tools) | $0.624 | $0.036 | $0.660 | **$1.74** |
| Grok 4 (Web) | $0.206 | $0.048 | $0.255 | **$1.33** |
| Grok 4 (All Tools) | $0.190 | $0.023 | $0.214 | **$1.29** |
| GLM 4.6 (Web) | $0.098 | $0.091 | $0.189 | **$1.27** |
| GLM 4.6 (All Tools) | $0.091 | $0.032 | $0.123 | **$1.20** |
| MiniMax M2 (Web) | $0.043 | $0.077 | $0.120 | **$1.20** |
| Gemini 2.5 Pro (Web) | $0.087 | $0.026 | $0.112 | **$1.19** |
| Gemini 2.5 Pro (All Tools) | $0.088 | $0.012 | $0.099 | **$1.18** |
| MiniMax M2 (All Tools) | $0.031 | $0.032 | $0.063 | **$1.14** |

**Summary:**

- Mean AI cost (both prompts): $0.251
- Mean total (with human review): $1.33

---

## Comparison: Original Table 2 vs Updated

The original Table 2 in the paper showed costs for the **main prompt only** without human review:

| Model | Original Table 2 | Updated (Both Prompts + Human) |
| ----- | ---------------- | ------------------------------ |
| Claude Sonnet 4 (AT) | $0.324 | $1.74 |
| Grok 4 (AT) | $0.112 | $1.29 |
| Gemini 2.5 Pro (AT) | $0.051 | $1.18 |
| GLM 4.6 (AT) | $0.059 | $1.20 |
| MiniMax M2 (AT) | $0.033 | $1.14 |

**Key differences:**

1. Original only included main prompt (~50% of AI cost)
2. Original excluded $1.08 human review cost
3. Both use the 40-profile human baseline subset

---

## Figure Values (After Update)

The figure now uses the human baseline subset and shows these totals:

| Model | Total Cost |
| ----- | ---------- |
| Claude (W) | $1.76 |
| Claude (AT) | $1.74 |
| Grok (W) | $1.33 |
| Grok (AT) | $1.29 |
| GLM (W) | $1.27 |
| GLM (AT) | $1.20 |
| MiniMax (W) | $1.20 |
| Gemini (W) | $1.19 |
| Gemini (AT) | $1.18 |
| MiniMax (AT) | $1.14 |

These values match the updated Table 2 above.

---

## Cost vs Performance Figures (Figure 7)

**Script:** `scripts/figures/generate_figure7.py`

Two versions generated with the same methodology:

**Full Dataset** (`paper/supplementary/figure7_cost_vs_performance_full.png`):

- 134 profiles
- R² = 0.013 (no correlation between cost and performance)

**Human Baseline Subset** (`paper/supplementary/figure7_cost_vs_performance_hbs.png`):

- 40 profiles
- R² = 0.055 (no correlation between cost and performance)

Both use:

- Sum of model_cost + web_search_cost across both prompts
- Plus $1.08 human review flat rate
