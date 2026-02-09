"""
Hypothesis testing: Is the work relevance gap driven by Europe PMC replacing web search?

H1: Models that do more web searches in the all-tools condition have better relevance
H2: Responses with more epmc sources and fewer web sources have lower relevance
H3: Paired comparison — same customer, all-tools vs web-only
H4: Source characteristics when web-only wins vs when both pass
H5: Effect by customer type and country
"""
import pandas as pd
import numpy as np

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

# Get work relevance results and merge with response-level source counts
work_rel = tests[tests.metric_name == 'WORK-RELEVANCE'].copy()
work_rel_ai = work_rel[~work_rel.is_human_baseline].copy()

# Merge response-level data into test data
resp_bg = responses[responses.prompt_type == 'background_work'][[
    'result_id', 'num_sources', 'num_web_sources', 'num_epmc_sources',
    'num_orcid_sources', 'num_screen_sources', 'num_web_searches',
    'prompt_tokens', 'completion_tokens', 'total_tokens', 'response_length'
]].copy()
resp_bg.columns = ['result_id'] + ['r_' + c for c in resp_bg.columns[1:]]

work_rel_merged = work_rel_ai.merge(resp_bg, on='result_id', how='left')

# ============================================================
# H1: Within all-tools, does more web searching correlate with higher relevance?
# ============================================================
print("=" * 80)
print("H1: Within ALL-TOOLS, correlation between web searches and work relevance")
print("=" * 80)

at = work_rel_merged[work_rel_merged.model_type == 'all_tools'].copy()

at['web_search_bin'] = pd.cut(at['r_num_web_searches'], bins=[-0.5, 0.5, 1.5, 3.5, 100],
                               labels=['0', '1', '2-3', '4+'])
h1_result = at.groupby('web_search_bin', observed=True).agg(
    pass_rate=('pass', 'mean'),
    count=('pass', 'count'),
    avg_epmc=('r_num_epmc_sources', 'mean'),
    avg_web=('r_num_web_sources', 'mean'),
).reset_index()
print(h1_result.to_string(index=False))
print()

# Per model within all-tools
print("Per-model breakdown (all-tools): web search vs no web search")
for model in sorted(at.model_label.unique()):
    m = at[at.model_label == model]
    has_web = m[m.r_num_web_searches > 0]
    no_web = m[m.r_num_web_searches == 0]
    print(f"  {model}:")
    if len(has_web) > 0:
        print(f"    With web search (n={len(has_web)}): {has_web['pass'].mean():.3f}")
    else:
        print(f"    No instances with web search")
    if len(no_web) > 0:
        print(f"    Without web search (n={len(no_web)}): {no_web['pass'].mean():.3f}")
    else:
        print(f"    Always uses web search")
    print(f"    Avg web searches: {m['r_num_web_searches'].mean():.2f}, Avg epmc: {m['r_num_epmc_sources'].mean():.1f}")
print()

# ============================================================
# H2: Does higher epmc reliance (as share of total) predict lower relevance?
# ============================================================
print("=" * 80)
print("H2: Does epmc share predict lower relevance? (all-tools only)")
print("=" * 80)

at['epmc_share'] = at['r_num_epmc_sources'] / at['r_num_sources'].clip(lower=1)
at['epmc_share_bin'] = pd.cut(at['epmc_share'], bins=[-0.01, 0.01, 0.5, 0.8, 1.01],
                                labels=['0%', '1-50%', '51-80%', '81-100%'])
h2_result = at.groupby('epmc_share_bin', observed=True).agg(
    pass_rate=('pass', 'mean'),
    count=('pass', 'count'),
    avg_web_searches=('r_num_web_searches', 'mean'),
).reset_index()
print(h2_result.to_string(index=False))
print()

# ============================================================
# H3: Paired comparison — same customer, all-tools vs web-only
# ============================================================
print("=" * 80)
print("H3: Paired comparison — same customer, which condition wins?")
print("=" * 80)

work_rel_pivot = work_rel_ai.pivot_table(
    index=['customer_name', 'model_name'],
    columns='model_type',
    values='pass',
    aggfunc='first'
).dropna()

print(f"Total paired comparisons: {len(work_rel_pivot)}")
both_pass = (work_rel_pivot['all_tools'] == True) & (work_rel_pivot['web_only'] == True)
both_fail = (work_rel_pivot['all_tools'] == False) & (work_rel_pivot['web_only'] == False)
at_better = (work_rel_pivot['all_tools'] == True) & (work_rel_pivot['web_only'] == False)
wo_better = (work_rel_pivot['all_tools'] == False) & (work_rel_pivot['web_only'] == True)

print(f"Both pass:      {both_pass.sum()} ({both_pass.mean():.1%})")
print(f"Both fail:      {both_fail.sum()} ({both_fail.mean():.1%})")
print(f"All-tools wins: {at_better.sum()} ({at_better.mean():.1%})")
print(f"Web-only wins:  {wo_better.sum()} ({wo_better.mean():.1%})")
print()

work_rel_pivot_reset = work_rel_pivot.reset_index()
wo_wins = work_rel_pivot_reset[(work_rel_pivot_reset['all_tools'] == False) & (work_rel_pivot_reset['web_only'] == True)]
print("Web-only wins by model:")
print(wo_wins['model_name'].value_counts().to_string())
print()

# ============================================================
# H4: Source characteristics of web-only wins vs both-pass cases
# ============================================================
print("=" * 80)
print("H4: Source characteristics when web-only wins vs when both pass")
print("=" * 80)

resp_bg_full = responses[responses.prompt_type == 'background_work'][[
    'result_id', 'model_type', 'customer_name', 'model_name',
    'num_web_sources', 'num_epmc_sources', 'num_web_searches', 'num_sources'
]].copy()

# All-tools responses for cases where web-only won
wo_win_cases = wo_wins[['customer_name', 'model_name']].copy()
at_for_wo_wins = wo_win_cases.merge(
    resp_bg_full[resp_bg_full.model_type == 'all_tools'],
    on=['customer_name', 'model_name']
)
print("All-tools responses for cases where WEB-ONLY WON:")
print(f"  n={len(at_for_wo_wins)}")
print(f"  Avg web searches: {at_for_wo_wins['num_web_searches'].mean():.2f}")
print(f"  Avg web sources: {at_for_wo_wins['num_web_sources'].mean():.1f}")
print(f"  Avg epmc sources: {at_for_wo_wins['num_epmc_sources'].mean():.1f}")
print(f"  Avg total sources: {at_for_wo_wins['num_sources'].mean():.1f}")
print()

both_pass_cases = work_rel_pivot_reset[both_pass.values][['customer_name', 'model_name']]
at_for_both_pass = both_pass_cases.merge(
    resp_bg_full[resp_bg_full.model_type == 'all_tools'],
    on=['customer_name', 'model_name']
)
print("All-tools responses for cases where BOTH PASSED:")
print(f"  n={len(at_for_both_pass)}")
print(f"  Avg web searches: {at_for_both_pass['num_web_searches'].mean():.2f}")
print(f"  Avg web sources: {at_for_both_pass['num_web_sources'].mean():.1f}")
print(f"  Avg epmc sources: {at_for_both_pass['num_epmc_sources'].mean():.1f}")
print(f"  Avg total sources: {at_for_both_pass['num_sources'].mean():.1f}")
print()

# ============================================================
# H5: Is the effect driven by specific customer types?
# ============================================================
print("=" * 80)
print("H5: Work relevance gap by customer_type")
print("=" * 80)
by_ctype = work_rel_ai.groupby(['customer_type', 'model_type'])['pass'].mean().unstack('model_type')
by_ctype['gap'] = by_ctype['all_tools'] - by_ctype['web_only']
print(by_ctype)
print()

print("=" * 80)
print("H5b: Work relevance gap by institution_country")
print("=" * 80)
by_country = work_rel_ai.groupby(['institution_country', 'model_type'])['pass'].mean().unstack('model_type')
by_country['gap'] = by_country['all_tools'] - by_country['web_only']
by_country = by_country.sort_values('gap')
print(by_country)
