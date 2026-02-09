"""
Investigating the paradox: within all-tools, models that DO web search have LOWER
pass rates than those that don't. This likely reflects a confound:

Models that resort to web search in the all-tools condition may be doing so because
EPMC didn't return useful results (i.e., web search is a fallback for harder cases).

Also: why do all-tools models that DO web search perform worse than web-only models?
Could be: epmc results dilute/distract from the more relevant web results, or the
models search differently when they have tools.
"""
import pandas as pd
import numpy as np

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

work_rel = tests[tests.metric_name == 'WORK-RELEVANCE'].copy()
work_rel_ai = work_rel[~work_rel.is_human_baseline].copy()
resp_bg = responses[responses.prompt_type == 'background_work'].copy()
resp_bg_ai = resp_bg[~resp_bg.is_human_baseline].copy()

# ============================================================
# 1. When all-tools models DO web search, how does it compare to web-only?
# ============================================================
print("=" * 80)
print("1. When all-tools models DO web search, do they search as thoroughly?")
print("=" * 80)

for model_name in sorted(resp_bg_ai.model_name.unique()):
    at = resp_bg_ai[(resp_bg_ai.model_name == model_name) & (resp_bg_ai.model_type == 'all_tools')]
    wo = resp_bg_ai[(resp_bg_ai.model_name == model_name) & (resp_bg_ai.model_type == 'web_only')]
    at_with_ws = at[at.num_web_searches > 0]

    if len(at_with_ws) > 0:
        print(f"  {model_name}:")
        print(f"    All-tools (when searching): {at_with_ws['num_web_searches'].mean():.2f} searches, {at_with_ws['num_web_sources'].mean():.1f} web src")
        print(f"    Web-only:                   {wo['num_web_searches'].mean():.2f} searches, {wo['num_web_sources'].mean():.1f} web src")
        print(f"    Ratio: {at_with_ws['num_web_searches'].mean() / max(wo['num_web_searches'].mean(), 0.01):.0%} of web-only search volume")
print()

# ============================================================
# 2. Customer-level analysis: for the SAME customer, is the gap
#    between all-tools-with-ws and web-only due to fewer searches?
# ============================================================
print("=" * 80)
print("2. Same customer: all-tools+ws vs web-only, paired analysis")
print("=" * 80)

at_wr = work_rel_ai[work_rel_ai.model_type == 'all_tools'].merge(
    resp_bg_ai[resp_bg_ai.model_type == 'all_tools'][['result_id', 'num_web_searches', 'num_epmc_sources', 'num_web_sources']].rename(
        columns={'num_web_searches': 'at_ws', 'num_epmc_sources': 'at_epmc', 'num_web_sources': 'at_web_src'}
    ), on='result_id', how='left'
)

wo_wr = work_rel_ai[work_rel_ai.model_type == 'web_only'].merge(
    resp_bg_ai[resp_bg_ai.model_type == 'web_only'][['result_id', 'num_web_searches', 'num_web_sources']].rename(
        columns={'num_web_searches': 'wo_ws', 'num_web_sources': 'wo_web_src'}
    ), on='result_id', how='left'
)

# Pair them
paired = at_wr[['customer_name', 'model_name', 'pass', 'at_ws', 'at_epmc', 'at_web_src']].rename(
    columns={'pass': 'at_pass'}
).merge(
    wo_wr[['customer_name', 'model_name', 'pass', 'wo_ws', 'wo_web_src']].rename(
        columns={'pass': 'wo_pass'}
    ), on=['customer_name', 'model_name']
)

# Cases where all-tools did web search
paired_ws = paired[paired.at_ws > 0]
paired_no_ws = paired[paired.at_ws == 0]

# Among cases where AT did web search: does searching MORE help?
paired_ws['ws_ratio'] = paired_ws['at_ws'] / paired_ws['wo_ws'].clip(lower=0.5)
paired_ws = paired_ws.copy()
paired_ws['at_pass'] = paired_ws['at_pass'].astype(bool)
paired_ws['wo_pass'] = paired_ws['wo_pass'].astype(bool)

paired_ws['outcome'] = 'both_pass'
paired_ws.loc[paired_ws.at_pass & ~paired_ws.wo_pass, 'outcome'] = 'at_wins'
paired_ws.loc[~paired_ws.at_pass & paired_ws.wo_pass, 'outcome'] = 'wo_wins'
paired_ws.loc[~paired_ws.at_pass & ~paired_ws.wo_pass, 'outcome'] = 'both_fail'

print("Among all-tools responses WITH web search:")
for outcome in ['both_pass', 'both_fail', 'at_wins', 'wo_wins']:
    sub = paired_ws[paired_ws.outcome == outcome]
    if len(sub) > 0:
        print(f"  {outcome} (n={len(sub)}): avg AT ws={sub['at_ws'].mean():.1f}, WO ws={sub['wo_ws'].mean():.1f}, AT epmc={sub['at_epmc'].mean():.1f}")
print()

# ============================================================
# 3. Are the cases where AT does web search inherently harder?
#    Check if the customer's overall pass rate (across all models) is lower
# ============================================================
print("=" * 80)
print("3. Customer difficulty: are web-search cases in all-tools harder customers?")
print("=" * 80)

# Customer overall pass rate across all models and conditions
customer_difficulty = work_rel_ai.groupby('customer_name')['pass'].mean()

at_ws_customers = at_wr[at_wr.at_ws > 0].customer_name.unique()
at_no_ws_customers = at_wr[at_wr.at_ws == 0].customer_name.unique()

# Note: some customers appear in both sets (web search for some models, not others)
ws_only = set(at_ws_customers) - set(at_no_ws_customers)
no_ws_only = set(at_no_ws_customers) - set(at_ws_customers)
both_sets = set(at_ws_customers) & set(at_no_ws_customers)

print(f"Customers with web search in some all-tools runs: {len(at_ws_customers)}")
print(f"Customers without web search in some all-tools runs: {len(at_no_ws_customers)}")
print(f"  Only in ws set: {len(ws_only)}")
print(f"  Only in no-ws set: {len(no_ws_only)}")
print(f"  In both: {len(both_sets)}")
print()

if len(ws_only) > 0:
    print(f"Avg overall pass rate for ws-only customers: {customer_difficulty[list(ws_only)].mean():.3f}")
if len(no_ws_only) > 0:
    print(f"Avg overall pass rate for no-ws-only customers: {customer_difficulty[list(no_ws_only)].mean():.3f}")
print()

# ============================================================
# 4. The simplest version of the story: per-model, per-customer-type
# ============================================================
print("=" * 80)
print("4. Industry customers: pass rate by model and tool condition")
print("=" * 80)

industry_wr = work_rel_ai[work_rel_ai.customer_type == 'Controlled Agent Industry']
pivot = industry_wr.pivot_table(
    index='model_name',
    columns='model_type',
    values='pass',
    aggfunc='mean'
)
pivot['gap'] = pivot['all_tools'] - pivot['web_only']
pivot = pivot.sort_values('gap')
print(pivot)
print()

# ============================================================
# 5. Count how many all-tools industry responses have >0 epmc
#    and check if their epmc results are from the RIGHT organism
# ============================================================
print("=" * 80)
print("5. Industry all-tools: epmc source presence")
print("=" * 80)

ind_at_resp = resp_bg_ai[(resp_bg_ai.model_type == 'all_tools') & (resp_bg_ai.customer_type == 'Controlled Agent Industry')]
print(f"Industry all-tools responses: {len(ind_at_resp)}")
print(f"  With 0 epmc sources: {(ind_at_resp['num_epmc_sources'] == 0).sum()} ({(ind_at_resp['num_epmc_sources'] == 0).mean():.0%})")
print(f"  With >0 epmc sources: {(ind_at_resp['num_epmc_sources'] > 0).sum()} ({(ind_at_resp['num_epmc_sources'] > 0).mean():.0%})")
print(f"  Avg epmc when >0: {ind_at_resp[ind_at_resp['num_epmc_sources'] > 0]['num_epmc_sources'].mean():.1f}")
print()

ind_wo_resp = resp_bg_ai[(resp_bg_ai.model_type == 'web_only') & (resp_bg_ai.customer_type == 'Controlled Agent Industry')]
print(f"Industry web-only responses:")
print(f"  Avg web searches: {ind_wo_resp['num_web_searches'].mean():.2f}")
print(f"  Avg web sources: {ind_wo_resp['num_web_sources'].mean():.1f}")
print()

# ============================================================
# 6. The full picture: where does the gap come from numerically?
# ============================================================
print("=" * 80)
print("6. Full decomposition by customer type")
print("=" * 80)

for ctype in work_rel_ai.customer_type.unique():
    sub = work_rel_ai[work_rel_ai.customer_type == ctype]
    at_pass = sub[sub.model_type == 'all_tools']['pass'].mean()
    wo_pass = sub[sub.model_type == 'web_only']['pass'].mean()
    n = len(sub[sub.model_type == 'all_tools'])
    gap = at_pass - wo_pass
    weighted_contribution = gap * n / len(work_rel_ai[work_rel_ai.model_type == 'all_tools'])
    print(f"  {ctype} (n={n}): gap={gap*100:+.1f}pp, contributes {weighted_contribution*100:+.2f}pp to overall gap")

total_gap = work_rel_ai[work_rel_ai.model_type=='all_tools']['pass'].mean() - work_rel_ai[work_rel_ai.model_type=='web_only']['pass'].mean()
print(f"\n  Total gap: {total_gap*100:.1f}pp")
