"""
Deep dive into:
1. Industry customers: why the 14pp gap?
2. Grok's specific problem with 0-epmc cases
3. What types of works are found via web but not via epmc?
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

# ============================================================
# 1. Industry: is the gap because industry work is in patents not papers?
# ============================================================
print("=" * 80)
print("1. Industry: source composition, all-tools vs web-only")
print("=" * 80)

industry_resp = resp_bg[resp_bg.customer_type == 'Controlled Agent Industry']
industry_resp_ai = industry_resp[~industry_resp.is_human_baseline]

print("Source counts by model_type for INDUSTRY customers:")
source_cols = ['num_sources', 'num_web_sources', 'num_epmc_sources', 'num_web_searches']
print(industry_resp_ai.groupby('model_type')[source_cols].mean())
print()

# Compare with academic customers
academic_resp = resp_bg[resp_bg.customer_type == 'Controlled Agent Academia']
academic_resp_ai = academic_resp[~academic_resp.is_human_baseline]

print("Source counts by model_type for ACADEMIC customers:")
print(academic_resp_ai.groupby('model_type')[source_cols].mean())
print()

# Key insight: for industry, epmc may return fewer relevant results because
# industry people publish less and patent more
print("Avg epmc sources, industry vs academic (all-tools):")
print(f"  Industry:  {industry_resp_ai[industry_resp_ai.model_type=='all_tools']['num_epmc_sources'].mean():.1f}")
print(f"  Academic:  {academic_resp_ai[academic_resp_ai.model_type=='all_tools']['num_epmc_sources'].mean():.1f}")
print()

# ============================================================
# 2. Per-model relevance gap by customer type
# ============================================================
print("=" * 80)
print("2. Per-model relevance gap by customer type")
print("=" * 80)

pivot = work_rel_ai.groupby(['model_name', 'customer_type', 'model_type'])['pass'].mean().unstack('model_type')
pivot['gap'] = pivot['all_tools'] - pivot['web_only']
pivot = pivot.reset_index()
print(pivot.pivot_table(index='model_name', columns='customer_type', values='gap'))
print()

# ============================================================
# 3. Grok deep dive: why does it have most web-only wins?
# ============================================================
print("=" * 80)
print("3. Grok deep dive")
print("=" * 80)

grok_at = work_rel_ai[(work_rel_ai.model_name == 'x-ai/grok-4') & (work_rel_ai.model_type == 'all_tools')]
grok_wo = work_rel_ai[(work_rel_ai.model_name == 'x-ai/grok-4') & (work_rel_ai.model_type == 'web_only')]

# Merge response info
grok_at_resp = resp_bg[(resp_bg.model_name == 'x-ai/grok-4') & (resp_bg.model_type == 'all_tools')]
print(f"Grok all-tools: {grok_at['pass'].mean():.3f}, avg epmc: {grok_at_resp['num_epmc_sources'].mean():.1f}, avg web: {grok_at_resp['num_web_sources'].mean():.1f}")
print(f"Grok web-only:  {grok_wo['pass'].mean():.3f}")
print()

# Look at customers where Grok fails in all-tools but passes in web-only
grok_paired = work_rel_ai[work_rel_ai.model_name == 'x-ai/grok-4'].pivot_table(
    index='customer_name',
    columns='model_type',
    values='pass',
    aggfunc='first'
).dropna()
grok_wo_wins = grok_paired[(grok_paired['all_tools'] == False) & (grok_paired['web_only'] == True)]
print(f"Grok: web-only wins on {len(grok_wo_wins)} customers:")
for customer in grok_wo_wins.index[:10]:
    # Get the response info
    at_r = grok_at_resp[grok_at_resp.customer_name == customer].iloc[0]
    wo_r = resp_bg[(resp_bg.model_name == 'x-ai/grok-4') & (resp_bg.model_type == 'web_only') & (resp_bg.customer_name == customer)].iloc[0]
    ctype = at_r['customer_type']
    print(f"  {customer} ({ctype}): AT epmc={at_r['num_epmc_sources']}, web_src={at_r['num_web_sources']}, web_search={at_r['num_web_searches']} | WO web_src={wo_r['num_web_sources']}, web_search={wo_r['num_web_searches']}")
print()

# ============================================================
# 4. Critical test: are zero-epmc all-tools cases harder customers?
#    If the customer also fails for web-only, it's a hard customer.
#    If it passes for web-only, epmc failure hurt the all-tools model.
# ============================================================
print("=" * 80)
print("4. Zero-epmc all-tools cases: are they inherently harder?")
print("=" * 80)

# For all-tools responses with 0 epmc sources, check web-only pass rate on same customer+model
at_resp_info = resp_bg[resp_bg.model_type == 'all_tools'][['result_id', 'num_epmc_sources', 'num_web_searches']].copy()
at_resp_info.columns = ['result_id', 'r_epmc', 'r_web_searches']
at_resp_merged = work_rel_ai[work_rel_ai.model_type == 'all_tools'].merge(
    at_resp_info, on='result_id', how='left'
)

zero_epmc_customers = at_resp_merged[at_resp_merged['r_epmc'] == 0][['customer_name', 'model_name']].copy()
nonzero_epmc_customers = at_resp_merged[at_resp_merged['r_epmc'] > 0][['customer_name', 'model_name']].copy()

# Get web-only pass rates for these same customer-model pairs
wo_results = work_rel_ai[work_rel_ai.model_type == 'web_only'][['customer_name', 'model_name', 'pass']].copy()
wo_results.columns = ['customer_name', 'model_name', 'wo_pass']

zero_epmc_wo = zero_epmc_customers.merge(wo_results, on=['customer_name', 'model_name'], how='inner')
nonzero_epmc_wo = nonzero_epmc_customers.merge(wo_results, on=['customer_name', 'model_name'], how='inner')

print(f"Zero-epmc cases: web-only pass rate = {zero_epmc_wo['wo_pass'].mean():.3f} (n={len(zero_epmc_wo)})")
print(f"Non-zero-epmc cases: web-only pass rate = {nonzero_epmc_wo['wo_pass'].mean():.3f} (n={len(nonzero_epmc_wo)})")
print()
print("This tells us whether customers that get 0 epmc results are inherently harder.")
print()

# ============================================================
# 5. Summary: the main mechanism
# ============================================================
print("=" * 80)
print("5. Summary statistics for the causal pathway")
print("=" * 80)

# How many all-tools bg responses had 0 web searches?
at_bg = resp_bg[(resp_bg.model_type == 'all_tools') & (~resp_bg.is_human_baseline)]
wo_bg = resp_bg[(resp_bg.model_type == 'web_only') & (~resp_bg.is_human_baseline)]

print(f"All-tools background_work responses with 0 web searches: {(at_bg['num_web_searches'] == 0).sum()}/{len(at_bg)} = {(at_bg['num_web_searches'] == 0).mean():.1%}")
print(f"Web-only background_work responses with 0 web searches: {(wo_bg['num_web_searches'] == 0).sum()}/{len(wo_bg)} = {(wo_bg['num_web_searches'] == 0).mean():.1%}")
print()
print(f"All-tools: avg web searches = {at_bg['num_web_searches'].mean():.2f}")
print(f"Web-only:  avg web searches = {wo_bg['num_web_searches'].mean():.2f}")
print()

# For the "main" prompt (not background_work), is the pattern the same?
main_resp_at = responses[(responses.prompt_type == 'main') & (responses.model_type == 'all_tools') & (~responses.is_human_baseline)]
main_resp_wo = responses[(responses.prompt_type == 'main') & (responses.model_type == 'web_only') & (~responses.is_human_baseline)]
print("For comparison — MAIN prompt web searches:")
print(f"  All-tools: avg {main_resp_at['num_web_searches'].mean():.2f}")
print(f"  Web-only:  avg {main_resp_wo['num_web_searches'].mean():.2f}")
