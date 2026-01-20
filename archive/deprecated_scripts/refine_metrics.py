#!/usr/bin/env python3
"""
Refine specific metric computations
"""

import pandas as pd
import json
import numpy as np
from sklearn.metrics import cohen_kappa_score

def fix_n4_kappa():
    """Fix N4 Cohen's kappa calculation"""
    tests_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')

    with open('/Users/alejo/Code/ai-kyc-results/data/blind_gradings.json', 'r') as f:
        blind_gradings = json.load(f)

    print("Blind grading structure sample:")
    for entry in blind_gradings[:3]:
        print(entry.keys())
        print(entry)
        print()

    print("Tests df columns:")
    print(tests_df.columns.tolist())
    print("\nSample test entry:")
    print(tests_df[['eval_id', 'metric_name', 'original_pass', 'pass']].head(3))

def fix_n7_cost_ratio():
    """Fix cost ratio calculation - exclude zero costs"""
    responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')

    print("Cost distribution:")
    print(responses_df['total_cost'].describe())
    print(f"\nZero costs: {(responses_df['total_cost'] == 0).sum()}")
    print(f"Non-zero costs: {(responses_df['total_cost'] > 0).sum()}")

    # Get minimum non-zero cost
    non_zero_costs = responses_df[responses_df['total_cost'] > 0]['total_cost']
    if len(non_zero_costs) > 0:
        min_cost = non_zero_costs.min()
        human_cost = 27.0
        ratio = min_cost / human_cost
        print(f"\nN7 CORRECTED: Cheapest AI (non-zero): ${min_cost:.4f}, Human: ${human_cost}, Ratio: 1/{1/ratio:.0f}")
    else:
        print("No non-zero costs found")

def check_institutional_emails():
    """Check institutional email classification"""
    full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

    print("Sample emails:")
    for i, email in enumerate(full_dataset_df['Email'].head(10)):
        print(f"{i+1}: {email}")

    # Count verified emails
    verified_count = full_dataset_df['Email'].str.contains('Verified email at', na=False).sum()
    print(f"\nVerified emails: {verified_count}/{len(full_dataset_df)}")

    # Check specific institutional domains
    educational_domains = full_dataset_df['Email'].str.contains(
        r'\.edu|\.ac\.|university|institute|\.gov', case=False, na=False
    ).sum()
    print(f"Educational/institutional patterns: {educational_domains}/{len(full_dataset_df)}")

def check_n2_discrepancy():
    """Check if paper claims 136 vs actual 134"""
    full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')
    tests_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')

    print(f"Full dataset profiles: {len(full_dataset_df)}")
    print(f"Unique customers in tests: {tests_df['customer_name'].nunique()}")

    # Check for any duplicates or issues
    print(f"Duplicate names in full dataset: {full_dataset_df['Name'].duplicated().sum()}")

if __name__ == "__main__":
    print("=== FIXING PROBLEMATIC METRICS ===\n")

    print("1. Checking N2 discrepancy:")
    check_n2_discrepancy()

    print("\n2. Refining N3 institutional emails:")
    check_institutional_emails()

    print("\n3. Debugging N4 kappa:")
    fix_n4_kappa()

    print("\n4. Fixing N7 cost ratio:")
    fix_n7_cost_ratio()