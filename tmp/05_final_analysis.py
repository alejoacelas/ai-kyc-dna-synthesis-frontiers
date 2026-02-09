"""
Final analysis: synthesizing the causal story.

Key finding so far: In the all-tools condition, models substitute web search with
Europe PMC API calls. This generally works well (high epmc -> high relevance), but:
1. When epmc finds nothing relevant, the model often doesn't fall back to web search
2. Industry customers are hurt most because their work is in patents/news, not papers
3. GLM shows the biggest industry gap (-31pp)

This script does final quantitative checks to nail down the story.
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
# 1. The substitution effect: web search reduction per model
# ============================================================
print("=" * 80)
print("1. Web search reduction: background_work task, per model")
print("=" * 80)

for model_name in sorted(resp_bg_ai.model_name.unique()):
    at = resp_bg_ai[(resp_bg_ai.model_name == model_name) & (resp_bg_ai.model_type == 'all_tools')]
    wo = resp_bg_ai[(resp_bg_ai.model_name == model_name) & (resp_bg_ai.model_type == 'web_only')]
    if len(at) == 0 or len(wo) == 0:
        continue
    reduction = 1 - at['num_web_searches'].mean() / max(wo['num_web_searches'].mean(), 0.01)
    print(f"  {model_name}:")
    print(f"    All-tools: {at['num_web_searches'].mean():.2f} web searches, {at['num_epmc_sources'].mean():.1f} epmc sources")
    print(f"    Web-only:  {wo['num_web_searches'].mean():.2f} web searches")
    print(f"    Web search reduction: {reduction:.0%}")
    # Pct with 0 web searches
    print(f"    % with 0 web searches: {(at['num_web_searches'] == 0).mean():.0%} (all-tools) vs {(wo['num_web_searches'] == 0).mean():.0%} (web-only)")
print()

# ============================================================
# 2. Direct test: does the web search reduction explain the relevance gap?
#    Control for model and customer, compare pass rates by web search usage
# ============================================================
print("=" * 80)
print("2. Controlling for model: does having tools hurt if you ALSO do web search?")
print("=" * 80)

# For each model: compare all-tools-with-web-search vs web-only
at_merged = work_rel_ai[work_rel_ai.model_type == 'all_tools'].merge(
    resp_bg_ai[resp_bg_ai.model_type == 'all_tools'][['result_id', 'num_web_searches', 'num_epmc_sources']].rename(
        columns={'num_web_searches': 'r_ws', 'num_epmc_sources': 'r_epmc'}
    ),
    on='result_id', how='left'
)

for model_name in sorted(work_rel_ai.model_name.unique()):
    at_model = at_merged[at_merged.model_name == model_name]
    wo_model = work_rel_ai[(work_rel_ai.model_name == model_name) & (work_rel_ai.model_type == 'web_only')]

    at_with_ws = at_model[at_model.r_ws > 0]
    at_no_ws = at_model[at_model.r_ws == 0]

    print(f"  {model_name}:")
    print(f"    Web-only pass rate:              {wo_model['pass'].mean():.3f} (n={len(wo_model)})")
    print(f"    All-tools + web search pass:     {at_with_ws['pass'].mean():.3f} (n={len(at_with_ws)})" if len(at_with_ws) > 0 else "    All-tools + web search: N/A")
    print(f"    All-tools + NO web search pass:  {at_no_ws['pass'].mean():.3f} (n={len(at_no_ws)})" if len(at_no_ws) > 0 else "    All-tools + NO web search: N/A")
print()

# ============================================================
# 3. The industry effect in detail
# ============================================================
print("=" * 80)
print("3. Industry effect: why is the gap so large?")
print("=" * 80)

# Industry customers have work in patents, not papers
# Europe PMC mainly indexes academic papers
# So epmc returns less relevant material for industry customers

industry_at = at_merged[at_merged.customer_type == 'Controlled Agent Industry']
industry_wo = work_rel_ai[(work_rel_ai.customer_type == 'Controlled Agent Industry') & (work_rel_ai.model_type == 'web_only')]

print(f"Industry - all-tools: {industry_at['pass'].mean():.3f} (n={len(industry_at)})")
print(f"Industry - web-only:  {industry_wo['pass'].mean():.3f} (n={len(industry_wo)})")
print(f"Industry - all-tools with ws:   {industry_at[industry_at.r_ws > 0]['pass'].mean():.3f} (n={(industry_at.r_ws > 0).sum()})")
print(f"Industry - all-tools without ws: {industry_at[industry_at.r_ws == 0]['pass'].mean():.3f} (n={(industry_at.r_ws == 0).sum()})")
print()

# Check: do industry customers get fewer epmc results?
print("Avg epmc sources by customer type (all-tools):")
for ctype in at_merged.customer_type.unique():
    ct = at_merged[at_merged.customer_type == ctype]
    print(f"  {ctype}: {ct['r_epmc'].mean():.1f} epmc sources, {ct['r_ws'].mean():.2f} web searches")
print()

# ============================================================
# 4. Alternative explanation: ORCID/other tools producing noise?
# ============================================================
print("=" * 80)
print("4. Do ORCID or screening tools contribute to lower relevance?")
print("=" * 80)

at_with_orcid = at_merged.merge(
    resp_bg_ai[resp_bg_ai.model_type == 'all_tools'][['result_id', 'num_orcid_sources']].rename(
        columns={'num_orcid_sources': 'r_orcid'}
    ),
    on='result_id', how='left'
)

has_orcid = at_with_orcid[at_with_orcid.r_orcid > 0]
no_orcid = at_with_orcid[at_with_orcid.r_orcid == 0]
print(f"All-tools with ORCID sources: pass={has_orcid['pass'].mean():.3f} (n={len(has_orcid)})")
print(f"All-tools without ORCID: pass={no_orcid['pass'].mean():.3f} (n={len(no_orcid)})")
print(f"(ORCID is used in only {len(has_orcid)}/{len(at_with_orcid)} = {len(has_orcid)/len(at_with_orcid):.0%} of cases)")
print()

# ============================================================
# 5. Quantify how much of the gap is explained by reduced web search
# ============================================================
print("=" * 80)
print("5. Decomposing the relevance gap")
print("=" * 80)

overall_at = work_rel_ai[work_rel_ai.model_type == 'all_tools']['pass'].mean()
overall_wo = work_rel_ai[work_rel_ai.model_type == 'web_only']['pass'].mean()
gap = overall_at - overall_wo

# Counterfactual: what if all-tools cases that did 0 web searches
# had the same pass rate as web-only?
at_no_ws_count = (at_merged.r_ws == 0).sum()
at_total = len(at_merged)
at_ws_pass = at_merged[at_merged.r_ws > 0]['pass'].mean() if (at_merged.r_ws > 0).any() else 0
at_no_ws_pass = at_merged[at_merged.r_ws == 0]['pass'].mean() if (at_merged.r_ws == 0).any() else 0

print(f"Overall gap: {gap:.4f} ({gap*100:.1f}pp)")
print(f"All-tools pass rate: {overall_at:.4f}")
print(f"Web-only pass rate:  {overall_wo:.4f}")
print()
print(f"All-tools with web search: pass={at_ws_pass:.4f}, n={at_total - at_no_ws_count}")
print(f"All-tools without web search: pass={at_no_ws_pass:.4f}, n={at_no_ws_count}")
print()

# Counterfactual: if no-web-search cases matched overall web-only pass rate
counterfactual_pass = (at_ws_pass * (at_total - at_no_ws_count) + overall_wo * at_no_ws_count) / at_total
print(f"Counterfactual (no-ws cases get web-only pass rate): {counterfactual_pass:.4f}")
print(f"This would close {(counterfactual_pass - overall_at) / abs(gap) * 100:.0f}% of the gap")
print()

# Better: within each model
print("Per-model gap decomposition:")
for model_name in sorted(work_rel_ai.model_name.unique()):
    m_at = at_merged[at_merged.model_name == model_name]
    m_wo = work_rel_ai[(work_rel_ai.model_name == model_name) & (work_rel_ai.model_type == 'web_only')]
    m_gap = m_at['pass'].mean() - m_wo['pass'].mean()

    m_no_ws = m_at[m_at.r_ws == 0]
    m_ws = m_at[m_at.r_ws > 0]

    # What if no-ws cases had web-only pass rate?
    if len(m_no_ws) > 0 and len(m_ws) > 0:
        cf = (m_ws['pass'].mean() * len(m_ws) + m_wo['pass'].mean() * len(m_no_ws)) / len(m_at)
        explained = (cf - m_at['pass'].mean()) / abs(m_gap) * 100 if m_gap != 0 else 0
    else:
        cf = m_at['pass'].mean()
        explained = 0

    print(f"  {model_name}: gap={m_gap*100:+.1f}pp, counterfactual closes {explained:.0f}% of gap")
    print(f"    No-ws fraction: {len(m_no_ws)/len(m_at):.0%}, no-ws pass: {m_no_ws['pass'].mean():.3f}" if len(m_no_ws) > 0 else "")
