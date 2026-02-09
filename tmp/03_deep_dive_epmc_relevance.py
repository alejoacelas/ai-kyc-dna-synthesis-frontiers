"""
Deep dive: The surprising finding that MORE web searches correlates with LOWER relevance
in the all-tools condition, and that high epmc share correlates with HIGHER relevance.

This seems counterintuitive. Let's investigate:
1. Is this a confound (e.g., models do web searches BECAUSE epmc didn't find enough)?
2. What happens in the 0% epmc bin — are these cases with no sources at all?
3. Is there a model composition effect in each bin?
4. What do the actual web-search-heavy all-tools responses look like?
"""
import pandas as pd
import numpy as np

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

work_rel = tests[tests.metric_name == 'WORK-RELEVANCE'].copy()
work_rel_ai = work_rel[~work_rel.is_human_baseline].copy()

resp_bg = responses[responses.prompt_type == 'background_work'][[
    'result_id', 'num_sources', 'num_web_sources', 'num_epmc_sources',
    'num_web_searches', 'model_label', 'model_type', 'full_response',
    'response_length', 'customer_name'
]].copy()

work_rel_merged = work_rel_ai.merge(
    resp_bg[['result_id', 'num_sources', 'num_web_sources', 'num_epmc_sources', 'num_web_searches', 'response_length']],
    on='result_id', how='left', suffixes=('', '_r')
)
at = work_rel_merged[work_rel_merged.model_type == 'all_tools'].copy()

# ============================================================
# 1. Model composition in each web search bin
# ============================================================
print("=" * 80)
print("1. Model composition in each web search bin (all-tools)")
print("=" * 80)

at['web_search_bin'] = pd.cut(at['num_web_searches'], bins=[-0.5, 0.5, 1.5, 3.5, 100],
                               labels=['0', '1', '2-3', '4+'])
model_comp = pd.crosstab(at['web_search_bin'], at['model_label'])
print(model_comp)
print()

# ============================================================
# 2. Look at the 0% epmc cases — what's going on?
# ============================================================
print("=" * 80)
print("2. Cases with 0 epmc sources in all-tools condition")
print("=" * 80)
no_epmc = at[at['num_epmc_sources'] == 0]
print(f"Total cases with 0 epmc: {len(no_epmc)}")
print(f"Pass rate: {no_epmc['pass'].mean():.3f}")
print(f"Avg web searches: {no_epmc['num_web_searches'].mean():.2f}")
print(f"Avg web sources: {no_epmc['num_web_sources'].mean():.1f}")
print(f"Avg total sources: {no_epmc['num_sources'].mean():.1f}")
print(f"\nModel breakdown:")
print(no_epmc.groupby('model_label').agg(
    n=('pass', 'count'),
    pass_rate=('pass', 'mean'),
    avg_web_searches=('num_web_searches', 'mean'),
    avg_total_sources=('num_sources', 'mean'),
).to_string())
print()

# Also check: how many of these have 0 total sources?
print(f"Cases with 0 total sources: {(no_epmc['num_sources'] == 0).sum()}")
print(f"Cases with >0 total sources but 0 epmc: {(no_epmc['num_sources'] > 0).sum()}")
print()

# ============================================================
# 3. Confound analysis: do models fall back to web search when epmc fails?
# ============================================================
print("=" * 80)
print("3. Confound: do models use web search as fallback when epmc returns little?")
print("=" * 80)
# If models do web search BECAUSE epmc returned few results, then high web search
# + low epmc would indicate harder cases, explaining the lower pass rate.

# Look at correlation between epmc and web search
print("Correlation between num_epmc_sources and num_web_searches (all-tools):")
print(f"  Pearson r: {at['num_epmc_sources'].corr(at['num_web_searches']):.3f}")
print()

# For each model, show whether web searches happen more when epmc returns few results
print("Per-model: avg web searches when epmc < median vs >= median")
for model in sorted(at.model_label.unique()):
    m = at[at.model_label == model]
    med = m['num_epmc_sources'].median()
    low = m[m['num_epmc_sources'] < med]
    high = m[m['num_epmc_sources'] >= med]
    print(f"  {model} (median epmc={med:.0f}):")
    print(f"    Low epmc (n={len(low)}): avg web search={low['num_web_searches'].mean():.2f}, pass={low['pass'].mean():.3f}")
    print(f"    High epmc (n={len(high)}): avg web search={high['num_web_searches'].mean():.2f}, pass={high['pass'].mean():.3f}")
print()

# ============================================================
# 4. The key test: WITHIN models, same customer — does epmc-only do worse?
# ============================================================
print("=" * 80)
print("4. Same model, same customer: comparing all-tools (epmc-heavy) vs web-only")
print("   Broken down by whether the all-tools version used web search")
print("=" * 80)

# Merge all-tools web search count into the paired comparison
at_search_info = at[['customer_name', 'model_name', 'num_web_searches', 'num_epmc_sources', 'num_web_sources']].copy()

paired = work_rel_ai.pivot_table(
    index=['customer_name', 'model_name'],
    columns='model_type',
    values='pass',
    aggfunc='first'
).dropna().reset_index()

paired = paired.merge(at_search_info, on=['customer_name', 'model_name'], how='inner')

# Split by whether all-tools used web search
paired_with_web = paired[paired['num_web_searches'] > 0]
paired_no_web = paired[paired['num_web_searches'] == 0]

print(f"Paired comparisons where all-tools DID web search (n={len(paired_with_web)}):")
print(f"  All-tools pass rate: {paired_with_web['all_tools'].mean():.3f}")
print(f"  Web-only pass rate:  {paired_with_web['web_only'].mean():.3f}")
print(f"  Gap: {paired_with_web['all_tools'].mean() - paired_with_web['web_only'].mean():.3f}")
print()

print(f"Paired comparisons where all-tools did NOT web search (n={len(paired_no_web)}):")
print(f"  All-tools pass rate: {paired_no_web['all_tools'].mean():.3f}")
print(f"  Web-only pass rate:  {paired_no_web['web_only'].mean():.3f}")
print(f"  Gap: {paired_no_web['all_tools'].mean() - paired_no_web['web_only'].mean():.3f}")
print()

# ============================================================
# 5. Industry customers — biggest gap (-14.3pp). What's different?
# ============================================================
print("=" * 80)
print("5. Industry customers deep dive (biggest relevance gap)")
print("=" * 80)
industry = work_rel_merged[work_rel_merged.customer_type == 'Controlled Agent Industry']
industry_at = industry[industry.model_type == 'all_tools']
industry_wo = industry[industry.model_type == 'web_only']

print("Industry - All tools:")
print(f"  n={len(industry_at)}, pass rate={industry_at['pass'].mean():.3f}")
print(f"  Avg web searches: {industry_at['num_web_searches'].mean():.2f}")
print(f"  Avg epmc: {industry_at['num_epmc_sources'].mean():.1f}")
print(f"  Avg web sources: {industry_at['num_web_sources'].mean():.1f}")
print()
print("Industry - Web only:")
print(f"  n={len(industry_wo)}, pass rate={industry_wo['pass'].mean():.3f}")
print(f"  Avg web searches: {industry_wo['num_web_searches'].mean():.2f}")
print(f"  Avg web sources: {industry_wo['num_web_sources'].mean():.1f}")
print()

# ============================================================
# 6. Hypothesis: epmc returns papers that ARE by the customer but less relevant to SOC
# ============================================================
print("=" * 80)
print("6. EPMC papers vs web sources: checking if issue is organism-relevance")
print("   (Looking at claim_support and source_reliability for background_work)")
print("=" * 80)

bg_all = tests[tests.prompt_type == 'background_work'].copy()
bg_ai = bg_all[~bg_all.is_human_baseline]

print("All background_work metrics, all-tools vs web-only:")
metric_comp = bg_ai.groupby(['metric_name', 'model_type'])['pass'].mean().unstack('model_type')
metric_comp['gap'] = metric_comp['all_tools'] - metric_comp['web_only']
print(metric_comp)
print()

# Merge source data for claim_support
bg_merged = bg_ai.merge(
    resp_bg[['result_id', 'num_epmc_sources', 'num_web_searches', 'num_web_sources']],
    on='result_id', how='left', suffixes=('', '_r')
)

# For work relevance specifically: do responses with high epmc share have the SAME
# claim support rate as those with low epmc?
wr_at = bg_merged[(bg_merged.model_type == 'all_tools') & (bg_merged.metric_name == 'WORK-RELEVANCE')]
wr_at = wr_at.copy()
wr_at['epmc_dominant'] = wr_at['num_epmc_sources'] > wr_at['num_web_sources']
print("Work relevance by epmc dominance (all-tools):")
print(wr_at.groupby('epmc_dominant')['pass'].agg(['mean', 'count']))
print()

# Same for claim support
cs_at = bg_merged[(bg_merged.model_type == 'all_tools') & (bg_merged.metric_name == 'BACKGROUND_WORK-CLAIM-SUPPORT')]
cs_at = cs_at.copy()
cs_at['epmc_dominant'] = cs_at['num_epmc_sources'] > cs_at['num_web_sources']
print("Claim support by epmc dominance (all-tools):")
print(cs_at.groupby('epmc_dominant')['pass'].agg(['mean', 'count']))
