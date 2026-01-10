# Plan: Fact-Check and Complete Paper Results

## Overview
Catalog all results in `paper/paper_draft.md`, compute/verify each using `processed/` datasets, generate figures with descriptive captions, and update the paper.

**User Decisions:**
- Skip error classification breakdown (Figure 5 / N12)
- Compute Cohen's kappa between original and blind gradings
- Preferentially use heatmaps for model×category matrices, grouped bars for comparisons
- Include full prompts in appendices

---

## Data Sources

| File | Rows | Key Columns |
|------|------|-------------|
| `processed/tests.csv` | ~22K | `pass`, `test_category`, `metric_name`, `model_label`, `institution_country`, `ground_truth_*` |
| `processed/responses.csv` | ~3.6K | `total_cost`, `latency_ms`, `model_type`, `model_label`, `time_to_complete_minutes` |
| `data/full-dataset.csv` | 134 | `Type`, `Name`, `Institution`, `Email`, `Order` |
| `data/blind_gradings.json` | ~100 | `evalId`, `testId`, `status` (pass/fail/ungraded) |

---

## Results Catalog

### INLINE NUMERICAL CLAIMS

| ID | Line | Claim | Method |
|----|------|-------|--------|
| N1 | 45 | Unique protein orders count | `pd.unique(df['Order']).count()` |
| N2 | 69 | Total profiles = 136 (verify) | Count rows in `full-dataset.csv` |
| N3 | 77 | 69% have institutional email | Match email domain to institution |
| N4 | 138 | Cohen's kappa | Match `blind_gradings.json` to `tests.csv`, compute kappa |
| N5 | 150 | $27/30min human cost | External estimate (keep as-is) |
| N6 | 152-153 | Response time stats | `responses.csv`: mean, median, std of `latency_ms` |
| N7 | 171 | 1/500th cost | min(AI cost) / $27 |
| N8 | 182 | ~80% avg pass rate | `tests.csv['pass'].mean()` |
| N9 | 183-184 | Best AI vs 30min human flag accuracy | Filter `test_category='flag_accuracy'`, compare |
| N10 | 203-204 | Pass rates within X% | Range across models |
| N11 | 207 | $0.05-$0.28 per customer | Group by model, mean cost |

### TABLES

**Table 1 (Lines 67-76): Dataset Composition**
- Verify category counts: `df.groupby('Type').size()`
- Cross-tab: category × country
- Email domain matching

**Table 2 (Lines 160-168): Cost Comparison**
```
| Condition | Mean cost | Time |
| Human (30 min) | $27.00 | from time_to_complete_minutes |
| Claude Sonnet 4 (tools) | computed | latency_ms / 1000 |
| Grok 4 (tools) | computed | ... |
| Gemini 2.5 Pro (tools) | computed | ... |
| GLM 4.6 (tools) | computed | ... |
| MiniMax M2 (tools) | computed | ... |
```
Add row for web-search-only comparison.

### FIGURES

**Figure 1: Pass Rates Heatmap** (Line 177-179)
- Format: Heatmap, rows=models (12), columns=test categories (4)
- Color: Sequential (white→green), annotate %
- Caption: "Pass rates by model and test category on the 40-profile human baseline subset. Darker shading indicates higher accuracy."

**Figure 2: Human vs AI by Task** (Line 189)
- Format: Grouped bar chart
- X-axis: Tasks (affiliation, institution, domain, sanctions, work)
- Groups: Human 30min, Best AI model (at the task), Worst AI model (at the task)
- Caption: "Error rates by verification task. AI models match or exceed human baseline on most information-gathering tasks."

**Figure 3: Model Rankings** (Lines 203-205)
- Format: Horizontal bar chart
- Y-axis: Models sorted by overall pass rate
- Color-coded by model_type (web_only, all_tools)
- Caption: "Overall pass rates by model. Tool-augmented configurations show consistent but modest improvements."

**Figure 4: Web-Only vs Tools** (Line 213)
- Format: Paired bar chart or slope chart
- X-axis: Test categories
- Groups: Web-only, All-tools (averaged across models)
- Caption: "Effect of specialized tools on pass rates. Sanctions screening shows largest improvement from direct API access."

**Figure 5: SKIP** (per user decision)

**Figure 6: Geographic Breakdown** (Line 235)
- Format: Grouped bar chart
- X-axis: Regions (USA, Europe+Oceania, China, Other)
- Groups: Test categories
- Caption: "Pass rates by customer region. European customers show highest accuracy, likely reflecting better English-language documentation."

### APPENDICES

- **Appendix A:** List unique SOC proteins from `Order` column
- **Appendix B:** Copy `prompts/simple.txt` and `prompts/background_work.txt`
- **Appendix C:** Copy `prompts/tests/*.yaml` and format for paper

---

## Execution Plan

### Phase 1: Compute All Numbers
1. Load CSVs with pandas
2. Compute each inline metric (N1-N11)
3. Verify Table 1 against data
4. Complete Table 2 with model costs/times
5. Compute Cohen's kappa from blind_gradings.json

### Phase 2: Generate Figures
1. Create Figure 1: Pass rates heatmap
2. Create Figure 2: Human vs AI grouped bars
3. Create Figure 3: Model rankings horizontal bars
4. Create Figure 4: Web vs Tools comparison
5. Create Figure 6: Geographic breakdown
6. Save all to `paper/figures/` with descriptive filenames
7. Generate markdown figure captions

### Phase 3: Update Paper
1. Replace all PLACEHOLDER markers with computed values
2. Insert figure references and captions
3. Add appendix content (prompts)
4. Edit text to agree with tables and figures

---

## Files to Modify
- `paper/paper_draft.md` - main paper with all updates
- `paper/figures/` - new directory for generated figures

## Files to Read
- `processed/tests.csv`
- `processed/responses.csv`
- `data/full-dataset.csv`
- `data/blind_gradings.json`
- `prompts/simple.txt`
- `prompts/background_work.txt`
- `prompts/tests/*.yaml`
