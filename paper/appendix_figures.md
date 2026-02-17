# Appendix: Supplementary Figures

This appendix presents supplementary analyses supporting the main results. Figures are organized into five sections: detailed model performance (Appendix E), full dataset validation (Appendix F), flag accuracy deep dive (Appendix G), cost and latency analysis (Appendix H), and source and tool usage (Appendix I).

All figures reference the 40-profile human baseline subset unless otherwise noted. AI models include five models (Claude Sonnet 4, Gemini 2.5 Pro, Grok 4, GLM 4.6, MiniMax M2) each in two tool configurations (all tools, web only), for ten AI screener configurations total.

---

## Appendix E: Detailed Model Performance

### E.1 Overall Pass Rates

![](new-plots/new_29_passrate_confidence_intervals.png)

**Figure E1: Overall pass rate per model with 95% Wilson score confidence intervals (40-profile subset).** Dots indicate point estimates; horizontal lines show confidence intervals. Green = all tools, blue = web only, red = human baseline.

![](new-plots/figure_S8_model_rankings.png)

**Figure E2: Overall pass rates by screener, sorted from lowest to highest (40-profile subset).** Horizontal bars show the average pass rate across all test categories. Dark blue = AI with all tools, light blue = AI with web search only, amber = human baseline.

### E.2 Pass Rate Breakdowns

![](new-plots/figure_S1_pass_rates_by_task.png)

**Figure E3: Pass rates by screener and task (40-profile subset).** Each cell shows the percentage of tests passed. Tasks include institutional affiliation verification, institution type classification, email domain validation, sanctions screening, and relevant work assessment. Screeners are grouped into AI with all tools (AT), AI with web search only (W), and human baseline.

![](new-plots/figure_S2_pass_rates_by_customer_type.png)

**Figure E4: Pass rates by screener and customer type (40-profile subset).** Each cell shows the percentage of tests passed across four customer categories: academic with substance-of-concern background, industry with substance-of-concern background, sanctioned academic institutions, and general life science customers.

### E.3 Per-Customer Performance

![](new-plots/new_19_per_customer_passrate.png)

**Figure E5: Per-customer overall pass rates (40-profile subset).** Swarm plot grouped by customer type and colored accordingly. Each dot represents one customer's average pass rate across all AI models. Horizontal colored bars show group means; the dashed black line shows the overall mean.

![](new-plots/new_10_flag_vs_overall_passrate.png)

**Figure E6: Flag accuracy vs non-flag pass rate per customer (40-profile subset).** Scatter plot with Pearson r = 0.38, averaged across AI models. Each point is one customer, colored by customer type. Dashed line indicates y = x.

### E.4 Statistical Comparisons

![](new-plots/new_27_pairwise_significance.png)

**Figure E7: Pairwise McNemar's test p-values across 10 AI models (40-profile subset).** 8 of 45 pairs show significant differences at p < 0.05 (continuity-corrected). Asterisks mark significant pairs.

![](new-plots/new_26_metric_correlation.png)

**Figure E8: Correlation matrix of per-customer pass rates across test categories (40-profile subset).** Pearson correlations computed with pass rates averaged across AI models. Color scale ranges from -1 (red) to +1 (blue).

---

## Appendix F: Full Dataset Validation

The main results are reported on the 40-profile subset where human baseline comparisons are available. To confirm that these findings generalize, we replicate key analyses on the full 134-profile dataset (AI models only; human screeners were not evaluated on the extended profiles).

### F.1 Full Dataset Replications

![](new-plots/figure_S4_pass_rates_heatmap_full.png)

**Figure F1: Pass rates by screener and test category on the full dataset (134 profiles, AI models only).** Replication of main-text Figure 2. Human baseline screeners are excluded as they were evaluated only on the 40-profile subset.

![](new-plots/figure_S5_pass_rates_by_task_full.png)

**Figure F2: Pass rates by screener and task on the full dataset (134 profiles, AI models only).** Task-level patterns remain consistent with the subset analysis, confirming that the 40-profile subset is representative of overall model behavior.

![](new-plots/figure_S6_pass_rates_by_customer_type_full.png)

**Figure F3: Pass rates by screener and customer type on the full dataset (134 profiles, AI models only).** The full dataset provides larger sample sizes per customer category and confirms patterns observed in the subset.

### F.2 Subset vs Full Dataset Comparison

![](new-plots/new_30_dataset_size_effect.png)

**Figure F4: Overall pass rates on the 40-profile subset vs the full 134-profile dataset for each AI model.** Mean difference: -1.5 percentage points, indicating slightly lower performance on the extended profiles.

### F.3 Performance by Customer Type and Region

![](new-plots/new_18_customer_type_x_region.png)

**Figure F5: Pass rates by customer type and region.** Side-by-side heatmaps averaged across AI models. Left: 40-profile subset. Right: full 134-profile dataset. Each cell shows the pass rate and number of customers (n) in that combination. N/A = no data for that combination.

---

## Appendix G: Flag Accuracy Deep Dive

Flag accuracy is the only manually graded metric and the most relevant for screening decisions. This section presents detailed analyses of flag prediction behavior, error patterns, and comparisons between human and AI screeners.

### G.1 Ground Truth Distribution

![](new-plots/new_14_ground_truth_prevalence.png)

**Figure G1: Ground truth flag distribution across the 40 profiles.** Each bar represents one flag criterion (affiliation, institution, domain, sanctions) divided into FLAG, NO FLAG, and UNDETERMINED segments, illustrating the class balance in the evaluation dataset.

### G.2 Model Predictions

![](new-plots/new_11_flag_distribution.png)

**Figure G2: Distribution of extracted flag values across AI models and flag criteria.** Each heatmap panel shows the percentage of responses for one flag value (FLAG, NO FLAG, UNDETERMINED). Rows = AI models; columns = four flag criteria.

![](new-plots/new_12_fp_fn_per_model.png)

**Figure G3: False positive, false negative, and undetermined rates per model across flag criteria.** A false positive occurs when the model predicts FLAG but ground truth is NO FLAG; a false negative when the model predicts NO FLAG but ground truth is FLAG; undetermined when the model returns UNDETERMINED regardless of ground truth.

![](new-plots/new_13_flag_confusion_matrices.png)

**Figure G4: Confusion matrices for flag accuracy across four criteria, aggregated across all AI models (40-profile subset).** Rows = ground truth; columns = model prediction. Each cell shows the count and row-normalized percentage.

### G.3 Human vs AI Error Comparison

![](new-plots/figure_S9_human_vs_ai.png)

**Figure G5: Human versus AI error rates by flag criterion (40-profile subset).** Amber bars show the 30-minute human baseline error rate. Blue stacked bars show the range of AI model error rates (dark = lowest, light = highest). Lower bars indicate better performance.

![](new-plots/figure_S11_error_by_criterion.png)

**Figure G6: Error rates by flag criterion and screener type (40-profile subset).** Grouped bars show total error rates for each criterion broken down by screener type: human baseline (amber), all tools (dark blue), and web only (light blue).

### G.4 Error Categories

![](new-plots/figure_S12_error_categories_by_screener.png)

**Figure G7: Error category distribution by screener type (40-profile subset).** 100% stacked bars show the proportion of each error category (empty response, instructions not followed, information not found, judgment difference, factual mistake) within each screener type.

![](new-plots/figure_S13_error_categories_by_criterion.png)

**Figure G8: Error category distribution by flag criterion and screener type (40-profile subset).** 100% stacked bars for each combination of criterion and screener type (H = Human, AT = All Tools, W = Web Only), revealing how error patterns differ across criteria and configurations.

### G.5 Flag Errors by Gene/Protein Product

![](new-plots/new_17_flag_errors_by_order.png)

**Figure G9: Flag accuracy error rate by gene/protein product (40-profile subset).** Error rate is 1 minus the mean pass rate for flag accuracy tests, averaged across all AI models. Darker red indicates higher error rates.

---

## Appendix H: Cost and Latency Analysis

### H.1 Cost Decomposition

![](new-plots/new_6_token_cost_decomposition.png)

**Figure H1: Token cost decomposition per customer for each AI model (40-profile subset).** Stacked bars show input token cost (indigo), output token cost (coral), and web search cost (teal).

![](new-plots/figure_S7_cost_vs_performance_full.png)

**Figure H2: Cost vs pass rate on the full dataset (134 profiles).** Each point represents a model configuration. Cost includes AI token and web search costs (excluding human review). Light blue = web only, dark blue = all tools.

### H.2 Time and Latency

![](new-plots/new_3_human_vs_ai_time.png)

**Figure H3: Human vs AI screening time per customer.** Human baselines show total time including information gathering and review. AI times show wall-clock information gathering time only (from dedicated latency benchmark). Note that AI times exclude the subsequent human review step.

![](new-plots/new_1_latency_distribution.png)

**Figure H4: Wall-clock latency distribution by model.** Boxplots of information gathering time per customer (summed across both prompts). Data from dedicated latency benchmark across 41 customer profiles. Green = all tools, blue = web only.

![](new-plots/new_2_latency_vs_passrate.png)

**Figure H5: Information gathering time vs pass rate.** Scatter plot of mean wall-clock time per customer vs overall pass rate. Latency data from dedicated benchmark; pass rates from 40-profile subset.

### H.3 Token and Response Characteristics

![](new-plots/new_4_token_consumption.png)

**Figure H6: Token consumption by model (40-profile subset).** Mean prompt and completion tokens per customer, summed across both prompts.

![](new-plots/new_5_response_length_vs_passrate.png)

**Figure H7: Response length vs pass rate.** Scatter plot of mean total response length per customer vs overall pass rate for each AI model (40-profile subset).

---

## Appendix I: Source and Tool Usage

### I.1 Source Composition

![](new-plots/figure_S3_web_searches.png)

**Figure I1: Web searches per customer by model (40-profile subset).** Searches summed across both prompts, then averaged per model. Green = all tools, blue = web only. Models with specialized tool access perform fewer web searches.

![](new-plots/new_7_source_type_composition.png)

**Figure I2: Source types per customer by model (40-profile subset).** Mean number of sources by type (web, EuropePMC, ORCID, screening database), summed across both prompts.

![](new-plots/new_9_source_types_by_task.png)

**Figure I3: Source types by task for all-tools models (40-profile subset).** Mean source counts by type for main screening vs background work prompts, showing which tools are used for which tasks.

### I.2 Sources and Performance

![](new-plots/new_8_sources_vs_passrate.png)

**Figure I4: Sources vs pass rate.** Scatter plot of mean total sources per customer vs overall pass rate for each AI model (40-profile subset).

### I.3 Tool Configuration Effects

![](new-plots/figure_S10_web_vs_tools.png)

**Figure I5: Effect of specialized tools on pass rates by test category (40-profile subset).** Paired bars show average AI model performance for web-only vs all-tools configurations. Annotations show the percentage point difference. Sanctions screening benefits most from tool access.

### I.4 Claim Support Analysis

![](new-plots/new_24_claim_failure_distribution.png)

**Figure I6: Distribution of failed claim-support assertions (40-profile subset).** Histogram across 410 customer-model pairs (AI models only). 207 pairs (50%) had zero claim failures.
