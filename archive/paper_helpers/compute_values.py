#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json
from sklearn.metrics import cohen_kappa_score

# Load data
print("Loading data...")
tests_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')
responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')
full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

# Load blind gradings
with open('/Users/alejo/Code/ai-kyc-results/data/blind_gradings.json') as f:
    blind_gradings = json.load(f)

print("Computing values...")

# N1: Count unique protein orders
n1_unique_orders = full_dataset_df['Order'].nunique()
print(f"N1 - Unique protein orders: {n1_unique_orders}")

# N2: Total profiles
n2_total_profiles = len(full_dataset_df)
print(f"N2 - Total profiles: {n2_total_profiles}")

# N3: Percentage with institutional email domains
# Count profiles where Email doesn't start with "Verified email at"
institutional_emails = full_dataset_df[full_dataset_df['Email'].str.contains('Verified email at', na=False)]
n3_pct = len(institutional_emails) / len(full_dataset_df) * 100
n3_count = len(institutional_emails)
print(f"N3 - Institutional emails: {n3_pct:.1f}% of profiles ({n3_count}/{n2_total_profiles})")

# Table 1: Update dataset composition
type_counts = full_dataset_df['Type'].value_counts()
print("\nTable 1 - Dataset composition:")
for type_name, count in type_counts.items():
    print(f"  {type_name}: {count}")

# N4: Cohen's kappa between original and blind gradings
print("\nComputing Cohen's kappa...")
# Match blind gradings to test results
blind_df = pd.DataFrame(blind_gradings)
print(f"Blind gradings loaded: {len(blind_df)} entries")
print(f"Available columns in blind_df: {blind_df.columns.tolist()}")
if len(blind_df) > 0:
    print(f"Sample blind grading keys: {list(blind_df.iloc[0].keys())}")

# Match by result_id (testId in blind_gradings corresponds to result_id in tests)
merged_for_kappa = blind_df.merge(
    tests_df[['result_id', 'pass']].drop_duplicates(),
    left_on='testId',
    right_on='result_id',
    how='inner'
)
print(f"Merged for kappa: {len(merged_for_kappa)} entries")

if len(merged_for_kappa) > 0:
    # Convert status to binary (pass/fail, exclude ungraded)
    graded_only = merged_for_kappa[merged_for_kappa['status'] != 'ungraded'].copy()
    print(f"Graded only: {len(graded_only)} entries")
    if len(graded_only) > 0:
        graded_only['blind_pass'] = graded_only['status'] == 'pass'
        n4_kappa = cohen_kappa_score(graded_only['pass'], graded_only['blind_pass'])
        print(f"N4 - Cohen's kappa: {n4_kappa:.3f}")
    else:
        print("N4 - No graded blind evaluations found")
else:
    print("N4 - Could not match blind gradings to test results")

# N6: Response time statistics
latency_seconds = responses_df['latency_ms'] / 1000
n6_mean = latency_seconds.mean()
n6_median = latency_seconds.median()
n6_std = latency_seconds.std()
print(f"N6 - Response time: Mean {n6_mean:.1f}s, Median {n6_median:.1f}s, Std {n6_std:.1f}s")

# N7, N11: Cost analysis
model_costs = responses_df.groupby('model_label')['total_cost'].mean()
# Filter out human baselines for cost ratio calculation
ai_costs = model_costs[~model_costs.index.str.contains('Human')]
min_ai_cost = ai_costs.min()
max_ai_cost = ai_costs.max()
human_cost = 27.0
n7_ratio = human_cost / min_ai_cost
print(f"N7 - Cost ratio (human/cheapest AI): 1/{n7_ratio:.0f}th")
print(f"N11 - AI cost range: ${min_ai_cost:.3f} to ${max_ai_cost:.3f}")

print("\nModel costs:")
for model, cost in model_costs.sort_values().items():
    if 'Human' in model:
        print(f"  {model}: $0.00 (simulated)")
    else:
        print(f"  {model}: ${cost:.3f}")

# N8: Overall pass rate
n8_pass_rate = tests_df['pass'].mean() * 100
print(f"N8 - Overall pass rate: {n8_pass_rate:.1f}%")

# N9: Best AI vs human flag accuracy
flag_accuracy_df = tests_df[tests_df['test_category'] == 'flag_accuracy']
if len(flag_accuracy_df) > 0:
    ai_flag_accuracy = flag_accuracy_df[~flag_accuracy_df['is_human_baseline']]['pass'].mean() * 100
    human_flag_accuracy = flag_accuracy_df[flag_accuracy_df['is_human_baseline']]['pass'].mean() * 100
    print(f"N9 - Flag accuracy: AI {ai_flag_accuracy:.1f}%, Human {human_flag_accuracy:.1f}%")
else:
    print("N9 - Flag accuracy data not found")

# N10: Pass rate variation across models
model_pass_rates = tests_df.groupby('model_label')['pass'].mean() * 100
pass_rate_range = model_pass_rates.max() - model_pass_rates.min()
print(f"N10 - Pass rate range across models: {pass_rate_range:.1f} percentage points")

# Table 2: Cost and time by model (tools version)
print("\nTable 2 - Cost and time by model:")
tools_models = responses_df[responses_df['model_type'] == 'all_tools']
table2_data = tools_models.groupby('model_label').agg({
    'total_cost': 'mean',
    'latency_ms': lambda x: x.mean() / 1000,  # Convert to seconds
}).round(3)

print("Human baseline (30 min): $27.00, ~30min")
for model, row in table2_data.iterrows():
    print(f"{model}: ${row['total_cost']:.3f}, {row['latency_ms']:.1f}s")

print("\nAll computed values ready for paper update.")