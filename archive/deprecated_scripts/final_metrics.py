#!/usr/bin/env python3
"""
Final refined metrics computation for the paper
"""

import pandas as pd
import json
import numpy as np
from sklearn.metrics import cohen_kappa_score
import re

def load_data():
    """Load all required datasets"""
    tests_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')
    responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')
    full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

    with open('/Users/alejo/Code/ai-kyc-results/data/blind_gradings.json', 'r') as f:
        blind_gradings = json.load(f)

    return tests_df, responses_df, full_dataset_df, blind_gradings

def compute_refined_kappa(tests_df, blind_gradings):
    """Compute Cohen's kappa with corrected mapping"""
    # Create mapping from blind gradings using correct field names
    blind_grades_map = {}

    for entry in blind_gradings:
        eval_id = entry.get('evalId')
        test_id = entry.get('testId')
        status = entry.get('status')

        if eval_id and test_id and status in ['pass', 'fail']:
            # Map status to boolean
            blind_pass = (status == 'pass')
            key = (eval_id, test_id)
            blind_grades_map[key] = blind_pass

    # Match with original results using result_id (which should match testId)
    original_passes = []
    blind_passes = []

    for _, row in tests_df.iterrows():
        eval_id = row['eval_id']
        result_id = row['result_id']  # This should match testId from blind grading
        original_pass = row['original_pass']

        key = (eval_id, result_id)
        if key in blind_grades_map:
            original_passes.append(original_pass)
            blind_passes.append(blind_grades_map[key])

    print(f"Found {len(original_passes)} matching entries for kappa calculation")

    if len(original_passes) > 0:
        kappa = cohen_kappa_score(original_passes, blind_passes)
        return kappa
    else:
        return None

def compute_refined_institutional_emails(full_dataset_df):
    """Better institutional email detection"""
    def is_institutional_email(email):
        if pd.isna(email) or email == '' or email == 'Not provided':
            return False

        email_lower = email.lower()

        # Handle "Verified email at domain.com" format
        if 'verified email at ' in email_lower:
            domain = email_lower.split('verified email at ')[-1].strip()
        elif '@' in email:
            domain = email.split('@')[-1].lower()
        else:
            return False

        # Institutional domain patterns
        institutional_patterns = [
            r'\.edu($|/)',           # US educational
            r'\.ac\.[a-z]{2,3}$',    # Academic domains (uk, in, etc.)
            r'\.gov($|/)',           # Government
            r'university',           # University in name
            r'institut',             # Institute variations
            r'\.org($|/)',           # Many research orgs use .org
            r'research',             # Research in domain
            r'tiho-hannover\.de$',   # Specific research institutions
            r'scripps\.edu$',        # Known research institutions
            r'biols\.ac\.cn$',       # Chinese academic
            r'im\.ac\.cn$',          # Chinese academic
            r'pucrs\.br$',           # Brazilian academic
            r'iitk\.ac\.in$',        # Indian academic
        ]

        for pattern in institutional_patterns:
            if re.search(pattern, domain):
                return True

        return False

    institutional_count = full_dataset_df['Email'].apply(is_institutional_email).sum()
    total = len(full_dataset_df)
    percentage = (institutional_count / total) * 100

    return institutional_count, total, percentage

def main():
    """Compute final refined metrics"""
    print("=== FINAL REFINED METRICS ===\n")

    tests_df, responses_df, full_dataset_df, blind_gradings = load_data()

    # N1: Unique protein orders
    n1 = full_dataset_df['Order'].nunique()

    # N2: Total profiles
    n2 = len(full_dataset_df)

    # N3: Institutional emails (refined)
    n3_count, n3_total, n3_pct = compute_refined_institutional_emails(full_dataset_df)

    # N4: Cohen's kappa (refined)
    n4 = compute_refined_kappa(tests_df, blind_gradings)

    # N6: Response times
    latency_stats = responses_df['latency_ms'].describe()
    n6_mean = latency_stats['mean'] / 1000
    n6_median = latency_stats['50%'] / 1000
    n6_std = latency_stats['std'] / 1000

    # N7: Cost ratio (excluding zeros)
    non_zero_costs = responses_df[responses_df['total_cost'] > 0]['total_cost']
    n7_min_cost = non_zero_costs.min()
    n7_ratio = n7_min_cost / 27.0

    # N8: Average pass rate
    n8_passes = tests_df['pass'].sum()
    n8_total = len(tests_df)
    n8_rate = (n8_passes / n8_total) * 100

    # N9: Best AI vs Human flag accuracy
    flag_tests = tests_df[tests_df['metric_name'].str.contains('FLAG', case=False, na=False)]
    if len(flag_tests) > 0:
        ai_model_performance = flag_tests[flag_tests['is_human_baseline'] == False].groupby('model_name')['pass'].mean()
        n9_best_ai = ai_model_performance.max() * 100
        n9_best_model = ai_model_performance.idxmax()

        human_flag_tests = flag_tests[flag_tests['is_human_baseline'] == True]
        if len(human_flag_tests) > 0:
            n9_human = human_flag_tests['pass'].mean() * 100
        else:
            n9_human = None
    else:
        n9_best_ai = n9_human = n9_best_model = None

    # N10: Pass rate range across models
    ai_tests = tests_df[tests_df['is_human_baseline'] == False]
    model_pass_rates = ai_tests.groupby('model_name')['pass'].mean() * 100
    n10_min = model_pass_rates.min()
    n10_max = model_pass_rates.max()
    n10_range = n10_max - n10_min

    # N11: Cost range
    n11_min = responses_df['total_cost'].min()
    n11_max = responses_df['total_cost'].max()

    # Table 1: Customer distribution
    table1_types = full_dataset_df['Type'].value_counts()

    # Table 2: Model performance (all-tools only)
    all_tools_stats = responses_df[responses_df['model_type'] == 'all_tools'].groupby('model_name').agg({
        'total_cost': 'mean',
        'latency_ms': lambda x: x.mean() / 1000  # Convert to seconds
    }).round(4)

    # Print results
    print("=== PAPER NUMERICAL CLAIMS ===")
    print(f"N1 (Line 45) - Unique protein orders: {n1}")
    print(f"N2 (Line 69) - Total profiles: {n2}")
    print(f"N3 (Line 77) - Institutional emails: {n3_count}/{n3_total} = {n3_pct:.1f}%")
    print(f"N4 (Line 138) - Cohen's kappa: {n4:.3f}" if n4 else "N4: Could not compute")
    print(f"N6 (Lines 152-153) - Response times: Mean {n6_mean:.1f}s, Median {n6_median:.1f}s, Std {n6_std:.1f}s")
    print(f"N7 (Line 171) - Cost ratio: 1/{1/n7_ratio:.0f} (${n7_min_cost:.4f} vs $27)")
    print(f"N8 (Line 182) - Average pass rate: {n8_passes}/{n8_total} = {n8_rate:.1f}%")

    if n9_best_ai:
        if n9_human:
            print(f"N9 (Lines 183-184) - Best AI vs Human flag accuracy: {n9_best_ai:.1f}% vs {n9_human:.1f}% ({n9_best_model})")
        else:
            print(f"N9 (Lines 183-184) - Best AI flag accuracy: {n9_best_ai:.1f}% ({n9_best_model})")

    print(f"N10 (Lines 203-204) - Pass rate range: {n10_min:.1f}% to {n10_max:.1f}% (span: {n10_range:.1f}%)")
    print(f"N11 (Line 207) - Cost range: ${n11_min:.4f} to ${n11_max:.4f}")

    print("\n=== TABLE 1 VERIFICATION ===")
    print("Customer Type Distribution:")
    for customer_type, count in table1_types.items():
        print(f"  {customer_type}: {count}")

    print("\n=== TABLE 2 (All-tools models) ===")
    print("Model performance (mean cost, mean latency in seconds):")
    print(all_tools_stats)

if __name__ == "__main__":
    main()