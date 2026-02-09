"""
Investigation: Why do all-tools AI models have lower work relevance scores than web-only models?

Step 1: Confirm the phenomenon and quantify the gap.
"""
import pandas as pd
import numpy as np

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

# ============================================================
# 1. Confirm the work relevance gap: all_tools vs web_only
# ============================================================
work_rel = tests[tests.metric_name == 'WORK-RELEVANCE'].copy()
# Exclude human baseline
work_rel_ai = work_rel[~work_rel.is_human_baseline]

print("=" * 80)
print("WORK RELEVANCE PASS RATES by model_type (AI only)")
print("=" * 80)
by_type = work_rel_ai.groupby('model_type')['pass'].mean()
print(by_type)
print()

print("=" * 80)
print("WORK RELEVANCE PASS RATES by model_label")
print("=" * 80)
by_model = work_rel_ai.groupby(['model_label', 'model_type'])['pass'].mean().reset_index()
by_model.columns = ['model_label', 'model_type', 'pass_rate']
by_model = by_model.sort_values(['model_type', 'model_label'])
print(by_model.to_string(index=False))
print()

# Also check on the human baseline subset only
print("=" * 80)
print("WORK RELEVANCE PASS RATES by model_type — human baseline subset only")
print("=" * 80)
work_rel_ai_hbs = work_rel_ai[work_rel_ai.is_human_baseline_dataset == True]
by_type_hbs = work_rel_ai_hbs.groupby('model_type')['pass'].mean()
print(by_type_hbs)
print()

by_model_hbs = work_rel_ai_hbs.groupby(['model_label', 'model_type'])['pass'].mean().reset_index()
by_model_hbs.columns = ['model_label', 'model_type', 'pass_rate']
by_model_hbs = by_model_hbs.sort_values(['model_type', 'model_label'])
print(by_model_hbs.to_string(index=False))
print()

# ============================================================
# 2. Compare OTHER background_work metrics too
# ============================================================
bg_metrics = tests[tests.prompt_type == 'background_work'].copy()
bg_ai = bg_metrics[~bg_metrics.is_human_baseline]

print("=" * 80)
print("ALL BACKGROUND_WORK METRICS by model_type (AI only)")
print("=" * 80)
by_type_metric = bg_ai.groupby(['metric_name', 'model_type'])['pass'].mean().unstack('model_type')
print(by_type_metric)
print()

# ============================================================
# 3. Look at source counts for background_work responses
# ============================================================
bg_responses = responses[responses.prompt_type == 'background_work'].copy()
bg_responses_ai = bg_responses[~bg_responses.is_human_baseline]

print("=" * 80)
print("BACKGROUND WORK RESPONSES: source counts by model_type")
print("=" * 80)
source_cols = ['num_sources', 'num_web_sources', 'num_epmc_sources', 'num_orcid_sources', 'num_screen_sources', 'num_web_searches']
by_type_sources = bg_responses_ai.groupby('model_type')[source_cols].mean()
print(by_type_sources)
print()

print("=" * 80)
print("BACKGROUND WORK RESPONSES: source counts by model_label")
print("=" * 80)
by_model_sources = bg_responses_ai.groupby(['model_label', 'model_type'])[source_cols].mean().reset_index()
by_model_sources = by_model_sources.sort_values(['model_type', 'model_label'])
print(by_model_sources.to_string(index=False))
print()

# ============================================================
# 4. Compare web search counts between conditions
# ============================================================
print("=" * 80)
print("WEB SEARCH COUNTS: background_work, by model_type")
print("=" * 80)
print(bg_responses_ai.groupby('model_type')['num_web_searches'].describe())
print()

# ============================================================
# 5. Compare token usage
# ============================================================
print("=" * 80)
print("TOKEN USAGE: background_work, by model_type")
print("=" * 80)
token_cols = ['prompt_tokens', 'completion_tokens', 'total_tokens', 'response_length']
by_type_tokens = bg_responses_ai.groupby('model_type')[token_cols].mean()
print(by_type_tokens)
print()

# ============================================================
# 6. Number of works reported in response (count rows in response table)
# ============================================================
def count_table_rows(response_text):
    """Count the number of data rows in a markdown table response."""
    if pd.isna(response_text):
        return 0
    lines = response_text.strip().split('\n')
    # Count lines that start with | and aren't headers or separators
    data_rows = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('|'):
            # Skip header row (first |) and separator (---|)
            if i >= 2 and '---' not in line:
                data_rows += 1
            elif i >= 2:
                continue
    return data_rows

bg_responses_ai['num_works_reported'] = bg_responses_ai['full_response'].apply(count_table_rows)

print("=" * 80)
print("NUMBER OF WORKS REPORTED: background_work, by model_type")
print("=" * 80)
print(bg_responses_ai.groupby('model_type')['num_works_reported'].describe())
print()

print("=" * 80)
print("NUMBER OF WORKS REPORTED: by model_label")
print("=" * 80)
works_by_model = bg_responses_ai.groupby(['model_label', 'model_type'])['num_works_reported'].mean().reset_index()
works_by_model = works_by_model.sort_values(['model_type', 'model_label'])
print(works_by_model.to_string(index=False))
