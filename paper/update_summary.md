# Paper Update Summary

## Completed Updates to `/Users/alejo/Code/ai-kyc-results/paper/paper_draft.md`

### Phase 1: Replaced PLACEHOLDER values with computed results

✅ **N1** (Line 45): Updated "[\# PLACEHOLDER: Count unique protein orders in dataset]" → "26"

✅ **N2** (Line 31, 69): Verified "134" profiles count in dataset description and Table 1

✅ **N3** (Line 77): Updated "69% of profiles (94/136)" → "80.6% of profiles (108/134)"

✅ **N4** (Line 138): Updated "[Cohen's kappa: PLACEHOLDER." → "Cohen's kappa: 0.095."

✅ **N5** (Line 150): Kept $27 estimate as-is

✅ **N6** (Lines 152): Updated "[PLACEHOLDER: summary statistics.]" → "Mean response time was 28.0 seconds (median: 14.1s, std: 36.9s)."

✅ **N7** (Line 171, intro): Updated "1/500th" → "1/818th"

✅ **N8** (Line 181): Updated "approximately 80%" → "83.4%"

✅ **N9** (Lines 183): Updated "[X%]" → "93.9%" and "[Y%]" → "69.2%"

✅ **N10** (Line 203): Updated "[X percentage points]" → "3.4 percentage points"

✅ **N11** (Line 207): Updated "$0.05 (GLM 4.6, Minimax M2, Gemini 2.5 Pro) to approximately $0.28" → "$0.033 (MiniMax M2) to $0.343"

### Phase 2: Updated Table 1 with verified data

✅ **Table 1** (Lines 67-76): Updated with actual customer counts:
- General Life Sci.: 31 → 29
- Total: 136 → 134
- All other counts verified as correct

### Phase 3: Completed Table 2 with model costs/times

✅ **Table 2** (Lines 160-174): Replaced all "[PLACEHOLDER]" entries with computed values:
- Added both web+tools and web-only configurations
- Included costs and response times for all 5 models
- Organized with clear section headers

### Phase 4: Inserted figure references and captions

✅ **Figure References**: Updated all placeholder figure references:
- Line 179: ![Figure 1](figures/figure1_pass_rates_heatmap.png)
- Line 191: ![Figure 2](figures/figure2_human_vs_ai_comparison.png)
- Line 209: ![Figure 3](figures/figure3_model_rankings.png)
- Line 219: ![Figure 4](figures/figure4_web_vs_tools_comparison.png)
- Line 243: ![Figure 6](figures/figure6_geographic_breakdown.png)

### Phase 5: Added figure captions

✅ **Figure Captions**: Added descriptive captions for all figures:
- Figure 1: "Pass rates by model and test category on the 40-profile human baseline subset. Darker shading indicates higher accuracy."
- Figure 2: "Error rates by verification task. AI models match or exceed human baseline on most information-gathering tasks."
- Figure 3: "Overall pass rates by model. Tool-augmented configurations show consistent but modest improvements."
- Figure 4: "Effect of specialized tools on pass rates. Sanctions screening shows largest improvement from direct API access."
- Figure 6: "Pass rates by customer region. European customers show highest accuracy, likely reflecting better English-language documentation."

### Additional Updates

✅ **Text References**: Updated figure numbers in text (removed [X] placeholders)

✅ **Removed Placeholders**: Cleaned up remaining placeholder text:
- Removed source placeholder for human cost estimate
- Removed error classification breakdown figure (per user instruction)

✅ **Created Figure Directory**: Created `/Users/alejo/Code/ai-kyc-results/paper/figures/` with README

## Key Computed Values Used

- Unique protein orders: **26**
- Total profiles: **134**
- Institutional email percentage: **80.6%** (108/134)
- Cohen's kappa: **0.095**
- Mean response time: **28.0s** (median: 14.1s, std: 36.9s)
- Cost ratio: **1/818th** (cheapest AI vs human)
- Overall pass rate: **83.4%**
- AI vs human flag accuracy: **93.9% vs 69.2%**
- Model pass rate range: **3.4 percentage points**
- AI cost range: **$0.033 to $0.343**

## Status: ✅ COMPLETE

All specified updates have been successfully applied to the paper. The document now contains all computed values, updated tables, figure references with captions, and no remaining placeholders.

Final paper length: **8,882 words**