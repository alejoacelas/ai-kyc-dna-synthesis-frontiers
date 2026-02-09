# Investigation: Why do all-tools models have lower work relevance scores?

## The Phenomenon

- All-tools models: **82.4%** work relevance pass rate
- Web-only models: **85.1%** work relevance pass rate
- Gap: **-2.7 percentage points**
- Gap is larger on the human baseline subset: 80.5% vs 87.8% (-7.3pp)

## Summary of Findings

The gap is driven by **two complementary mechanisms**, with industry customers being the main locus:

### Mechanism 1: Europe PMC crowds out web search

When models have access to the Europe PMC API, they dramatically reduce their use of web search for the background work task:

| Model | Web search reduction | % with 0 web searches (all-tools) |
|-------|---------------------|-----------------------------------|
| GLM 4.6 | 94% | 86% |
| Gemini 2.5 Pro | 90% | 87% |
| Claude Sonnet 4 | 79% | 39% |
| MiniMax M2 | 77% | 67% |
| Grok 4 | 63% | 41% |

- All-tools models average **0.72 web searches** vs **3.98 for web-only** (5.5x reduction)
- 64% of all-tools background_work responses use **zero web searches**
- Even when all-tools models DO web search, they search less thoroughly (34-78% of web-only volume)

### Mechanism 2: Europe PMC is less useful for industry customers

Europe PMC indexes academic papers, not patents or company news. For industry customers whose relevant work is in patents or corporate announcements, this creates a systematic gap:

| Customer type | All-tools | Web-only | Gap |
|---------------|-----------|----------|-----|
| Industry SOC | 64.6% | 78.9% | **-14.3pp** |
| Sanctioned | 88.1% | 93.1% | -5.0pp |
| Academic SOC | 88.6% | 89.2% | -0.6pp |
| General Life Sci | 82.2% | 76.1% | +6.1pp |

**Industry customers alone account for -2.86pp of the -2.7pp total gap** (they overexplain it; other types partly compensate).

### Mechanism 3: Models search less even when they DO use web search

When all-tools models fall back to web search, they don't search as thoroughly as web-only models. Paired analysis shows:

- In cases where web-only wins, the all-tools responses had avg **2.6 web searches** with **7.4 epmc sources** vs web-only's **4.4 web searches**
- In cases where both pass, all-tools had **1.7 web searches** with **22.0 epmc sources** vs web-only's **4.2 web searches**

The key signature of failure: low epmc AND low web search — the model didn't find much on EPMC and also didn't compensate with enough web searching.

## Model-Specific Effects

The gap varies dramatically by model:

| Model | Gap | Main driver |
|-------|-----|-------------|
| GLM 4.6 | **-9.7pp** | 94% web search reduction; -31pp on industry |
| Grok 4 | **-4.6pp** | Many 0-epmc cases where it didn't search web |
| MiniMax M2 | -0.6pp | Modest reduction; compensates somewhat |
| Gemini 2.5 Pro | 0.0pp | Near-complete substitution but epmc works ok for its cases |
| Claude Sonnet 4 | +1.1pp | Still does web search 61% of the time |

Claude is the exception: it maintains web search usage and actually slightly improves with tools.

## Key Evidence Against Alternative Hypotheses

### "Zero-epmc cases are just harder customers"
- **Rejected**: Customers who get 0 epmc results in all-tools actually have a **higher** web-only pass rate (87.7%) than the average (85.8%). They're not inherently harder — they just need web search to find relevant work.

### "ORCID/other tools cause noise"
- **Minor effect**: ORCID is only used in 20% of cases, and responses with ORCID actually have higher pass rates (89.7% vs 80.6%).

### "Models find fewer works in all-tools"
- **Rejected**: All-tools models report slightly more works (5.04 vs 4.90) — the issue isn't quantity of works reported, it's the relevance of the works found.

## Causal Story

1. When models have Europe PMC available, they preferentially use it over web search for the background work task
2. Europe PMC is effective for finding academic papers by researchers, which is why high-epmc responses actually have good relevance
3. But for industry customers, the relevant work (patents, company R&D) isn't in Europe PMC
4. Models don't adequately compensate with web search when EPMC returns less relevant results
5. GLM and Grok are worst affected because they reduce web search most aggressively (or have more 0-epmc failure cases)
6. The overall -2.7pp gap is dominated by the -14.3pp gap on industry customers

## Source-Type Evidence (from 07/08 scripts)

Parsed the LLM judge's `provided_source_analysis` blocks to determine which source types (web vs epmc) contributed works that crossed the relevance threshold. Type resolution rate: 90.5% (713/7478 unknown).

### Passing works are overwhelmingly from whatever source type the model has access to

- **Web-only passing works**: 92.7% from web, 0% from EPMC
- **All-tools passing works**: 78.9% from EPMC, 10.7% from web

This confirms models heavily rely on EPMC when available — even among the works the judge deems relevant, EPMC dominates.

### Industry customers: web sources are critical but under-used in all-tools

For industry customers specifically:

- **Web-only**: 90.4% of passing works come from web sources
- **All-tools**: 67.9% from EPMC, only 17.2% from web

Industry relevant work lives on the web (patents, company sites, news), not in Europe PMC. When models substitute EPMC for web search, they lose access to the most relevant material for these customers.

### Per-source relevance rate (all-tools condition, full dataset)

| Customer type | Web sources | EPMC sources |
|---|---|---|
| Academic SOC | 78% | 61% |
| Industry SOC | 64% | 64% |
| General Life Sci. | 81% | 84% |
| Sanctioned Inst. | 79% | 86% |

For industry, web and EPMC sources have the same per-source relevance rate (64%). The issue isn't that EPMC returns worse results — it's that it returns fewer relevant results and models don't supplement with enough web search to fill the gap.

### Predictive power: having any passing web source

- **All-tools**: Responses with at least one passing web source have 100% relevance pass rate (n=94); without: 80.3% (n=781)
- **All-tools**: Responses with at least one passing EPMC source have 99.7% pass rate (n=637); without: 36.1% (n=238)

When neither source type yields a relevant hit, the response almost always fails.

## Plots

**Plots A-D** (from `generate_investigation_plots.py`):

- A: Web search substitution per model (all-tools vs web-only)
- B: Source composition (stacked web/epmc per model)
- C: Work relevance gap by customer type
- D: Per-model decomposition (web-only vs EPMC-only vs EPMC+web)

**Plots E-G** (from `08_source_type_plots.py`):

- E: Share of relevant works by source type, per customer type
- F: Industry causal chain (3-panel: web searches, source types of relevant works, pass rate)
- G: Per-source relevance rate (web vs EPMC) by customer type

All plots generated in `_full` and `_hbs` variants.

## Scripts

- `01_initial_exploration.py` — Confirmed phenomenon, showed source composition shift
- `02_hypothesis_testing.py` — Tested H1-H5: web search correlation, epmc share, paired comparison, customer type
- `03_deep_dive_epmc_relevance.py` — Model composition in search bins, confound analysis, 0-epmc cases
- `04_industry_and_model_effects.py` — Industry deep dive, Grok case study, customer difficulty test
- `05_final_analysis.py` — Per-model decomposition, counterfactual analysis
- `06_web_search_paradox.py` — Why models that DO web search in all-tools still underperform web-only
- `07_source_type_in_passing_works.py` — Parsed judge output to extract source types of works passing relevance threshold
- `08_source_type_plots.py` — Plots E, F, G using source-type data
- `generate_investigation_plots.py` — Plots A, B, C, D
