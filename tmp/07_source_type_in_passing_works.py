"""
Extract which source types (web, epmc, orcid, screen) contributed to works
that passed the relevance threshold, per response.

Strategy:
1. Parse sources_json to build a mapping from source title -> source type
2. Parse the 'reason' field of WORK-RELEVANCE tests to extract each
   provided_source_analysis block and its PASS/FAIL result
3. Match each analyzed source back to its type via the sources_json mapping
4. Aggregate: for each response, how many PASS sources came from web vs epmc?
"""
import pandas as pd
import numpy as np
import json
import re

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

wr = tests[tests.metric_name == 'WORK-RELEVANCE'].copy()
wr_ai = wr[~wr.is_human_baseline].copy()


def parse_sources_map(sources_json_str):
    """Build a mapping from source id and title fragments -> source type."""
    if pd.isna(sources_json_str):
        return {}
    try:
        sources = json.loads(sources_json_str)
    except (json.JSONDecodeError, TypeError):
        return {}
    mapping = {}
    for s in sources:
        sid = s.get('id', '')
        stype = s.get('type', 'unknown')
        stitle = s.get('title', '')
        mapping[sid] = stype
        # Also map by title prefix for matching against reason text
        if stitle:
            # Use first 50 chars of title as key (reason text truncates titles)
            mapping[stitle[:50].strip().rstrip('.')] = stype
    return mapping


def parse_source_results(reason_str, sources_map):
    """
    Parse provided_source_analysis blocks from the reason field.
    Returns list of dicts with source_id, source_type, result (PASS/FAIL).
    """
    if pd.isna(reason_str):
        return []

    results = []
    # Match each provided_source_analysis block
    pattern = r'<provided_source_analysis id="([^"]*)">(.*?)</provided_source_analysis>'
    for match in re.finditer(pattern, reason_str, re.DOTALL):
        source_id_or_title = match.group(1).strip()
        block = match.group(2)

        # Extract result
        result_match = re.search(r'Source Result:\s*(PASS|FAIL)', block)
        result = result_match.group(1) if result_match else 'UNKNOWN'

        # Determine source type from sources_map
        source_type = 'unknown'
        # Try direct id match first
        if source_id_or_title in sources_map:
            source_type = sources_map[source_id_or_title]
        else:
            # Try matching by title prefix
            title_key = source_id_or_title[:50].strip().rstrip('.')
            if title_key in sources_map:
                source_type = sources_map[title_key]
            else:
                # Try fuzzy: check if any key starts with the same prefix
                for key, stype in sources_map.items():
                    if len(key) > 10 and (key.startswith(title_key[:30]) or title_key[:30].startswith(key[:30])):
                        source_type = stype
                        break

        results.append({
            'source_id': source_id_or_title,
            'source_type': source_type,
            'result': result,
        })

    return results


# Process all work relevance rows
records = []
for idx, row in wr_ai.iterrows():
    sources_map = parse_sources_map(row.sources_json)
    source_results = parse_source_results(row.reason, sources_map)

    n_pass_web = sum(1 for s in source_results if s['result'] == 'PASS' and s['source_type'] == 'web')
    n_pass_epmc = sum(1 for s in source_results if s['result'] == 'PASS' and s['source_type'] == 'epmc')
    n_pass_orcid = sum(1 for s in source_results if s['result'] == 'PASS' and s['source_type'] == 'orcid')
    n_pass_unknown = sum(1 for s in source_results if s['result'] == 'PASS' and s['source_type'] == 'unknown')
    n_pass_total = sum(1 for s in source_results if s['result'] == 'PASS')

    n_fail_web = sum(1 for s in source_results if s['result'] == 'FAIL' and s['source_type'] == 'web')
    n_fail_epmc = sum(1 for s in source_results if s['result'] == 'FAIL' and s['source_type'] == 'epmc')

    n_analyzed = len(source_results)
    n_unknown_type = sum(1 for s in source_results if s['source_type'] == 'unknown')

    records.append({
        'result_id': row.result_id,
        'model_label': row.model_label,
        'model_name': row.model_name,
        'model_type': row.model_type,
        'customer_name': row.customer_name,
        'customer_type': row.customer_type,
        'institution_country': row.institution_country,
        'is_human_baseline_dataset': row.is_human_baseline_dataset,
        'wr_pass': row['pass'],
        'n_analyzed': n_analyzed,
        'n_pass_total': n_pass_total,
        'n_pass_web': n_pass_web,
        'n_pass_epmc': n_pass_epmc,
        'n_pass_orcid': n_pass_orcid,
        'n_pass_unknown': n_pass_unknown,
        'n_fail_web': n_fail_web,
        'n_fail_epmc': n_fail_epmc,
        'n_unknown_type': n_unknown_type,
    })

df = pd.DataFrame(records)

# ============================================================
# Validation: check type resolution quality
# ============================================================
print("=" * 80)
print("VALIDATION: source type resolution")
print("=" * 80)
total_analyzed = df.n_analyzed.sum()
total_unknown = df.n_unknown_type.sum()
print(f"Total sources analyzed by judge: {total_analyzed}")
print(f"Unknown type: {total_unknown} ({total_unknown/total_analyzed*100:.1f}%)")
print(f"Known type: {total_analyzed - total_unknown} ({(total_analyzed - total_unknown)/total_analyzed*100:.1f}%)")
print()

# ============================================================
# Key analysis: source types contributing to PASS works
# ============================================================
print("=" * 80)
print("SOURCE TYPES IN PASSING WORKS: all-tools vs web-only")
print("=" * 80)

for mtype in ['all_tools', 'web_only']:
    sub = df[df.model_type == mtype]
    passing = sub[sub.wr_pass == True]
    print(f"\n{mtype} (n={len(passing)} passing responses):")
    print(f"  Avg passing works per response: {passing.n_pass_total.mean():.2f}")
    print(f"  Avg passing web sources: {passing.n_pass_web.mean():.2f}")
    print(f"  Avg passing epmc sources: {passing.n_pass_epmc.mean():.2f}")
    print(f"  Avg passing orcid sources: {passing.n_pass_orcid.mean():.2f}")
    print(f"  Avg passing unknown sources: {passing.n_pass_unknown.mean():.2f}")

    # What fraction of passing works used web vs epmc?
    total_pass = passing.n_pass_total.sum()
    total_web = passing.n_pass_web.sum()
    total_epmc = passing.n_pass_epmc.sum()
    total_orcid = passing.n_pass_orcid.sum()
    total_unknown = passing.n_pass_unknown.sum()
    print(f"\n  Total passing works: {total_pass}")
    print(f"  From web: {total_web} ({total_web/total_pass*100:.1f}%)" if total_pass > 0 else "")
    print(f"  From epmc: {total_epmc} ({total_epmc/total_pass*100:.1f}%)" if total_pass > 0 else "")
    print(f"  From orcid: {total_orcid} ({total_orcid/total_pass*100:.1f}%)" if total_pass > 0 else "")
    print(f"  Unknown: {total_unknown} ({total_unknown/total_pass*100:.1f}%)" if total_pass > 0 else "")
print()

# ============================================================
# Key: by customer type
# ============================================================
print("=" * 80)
print("SOURCE TYPES IN PASSING WORKS: by customer type and model_type")
print("=" * 80)

for ctype in ['Controlled Agent Academia', 'Controlled Agent Industry',
              'General Life Science Customers', 'Sanctioned Institution Customers']:
    print(f"\n--- {ctype} ---")
    for mtype in ['all_tools', 'web_only']:
        sub = df[(df.model_type == mtype) & (df.customer_type == ctype)]
        passing = sub[sub.wr_pass == True]
        if len(passing) == 0:
            continue
        total_pass = passing.n_pass_total.sum()
        total_web = passing.n_pass_web.sum()
        total_epmc = passing.n_pass_epmc.sum()
        pct_web = total_web / total_pass * 100 if total_pass > 0 else 0
        pct_epmc = total_epmc / total_pass * 100 if total_pass > 0 else 0
        print(f"  {mtype}: {len(passing)} passing responses, avg {passing.n_pass_total.mean():.1f} passing works")
        print(f"    Web: {total_web}/{total_pass} ({pct_web:.1f}%), EPMC: {total_epmc}/{total_pass} ({pct_epmc:.1f}%)")
print()

# ============================================================
# For FAILING responses: what source types were used?
# ============================================================
print("=" * 80)
print("SOURCE TYPES IN FAILING RESPONSES: all-tools vs web-only")
print("=" * 80)

for mtype in ['all_tools', 'web_only']:
    failing = df[(df.model_type == mtype) & (df.wr_pass == False)]
    if len(failing) == 0:
        continue
    print(f"\n{mtype} (n={len(failing)} failing responses):")
    print(f"  Avg total analyzed: {failing.n_analyzed.mean():.2f}")
    print(f"  Avg passing web: {failing.n_pass_web.mean():.2f}")
    print(f"  Avg passing epmc: {failing.n_pass_epmc.mean():.2f}")
    print(f"  Avg failing web: {failing.n_fail_web.mean():.2f}")
    print(f"  Avg failing epmc: {failing.n_fail_epmc.mean():.2f}")
print()

# ============================================================
# Does having at least one passing web source predict overall pass?
# ============================================================
print("=" * 80)
print("PREDICTIVE: does having a passing web source help?")
print("=" * 80)

for mtype in ['all_tools', 'web_only']:
    sub = df[df.model_type == mtype]
    has_web_pass = sub[sub.n_pass_web > 0]
    no_web_pass = sub[sub.n_pass_web == 0]
    print(f"\n{mtype}:")
    print(f"  Has passing web source: wr_pass={has_web_pass.wr_pass.mean():.3f} (n={len(has_web_pass)})")
    print(f"  No passing web source:  wr_pass={no_web_pass.wr_pass.mean():.3f} (n={len(no_web_pass)})")

    has_epmc_pass = sub[sub.n_pass_epmc > 0]
    no_epmc_pass = sub[sub.n_pass_epmc == 0]
    print(f"  Has passing epmc source: wr_pass={has_epmc_pass.wr_pass.mean():.3f} (n={len(has_epmc_pass)})")
    print(f"  No passing epmc source:  wr_pass={no_epmc_pass.wr_pass.mean():.3f} (n={len(no_epmc_pass)})")

# Save for plotting
df.to_csv('tmp/work_relevance_source_types.csv', index=False)
print("\nSaved tmp/work_relevance_source_types.csv")
