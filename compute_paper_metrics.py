#!/usr/bin/env python3
"""
Compute all numerical claims for the AI KYC Results paper
"""

import pandas as pd
import json
import numpy as np
from sklearn.metrics import cohen_kappa_score
import re

def load_data():
    """Load all required datasets"""
    print("Loading data files...")

    # Load CSV files
    tests_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')
    responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')
    full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

    # Load JSON file
    with open('/Users/alejo/Code/ai-kyc-results/data/blind_gradings.json', 'r') as f:
        blind_gradings = json.load(f)

    print(f"Tests shape: {tests_df.shape}")
    print(f"Responses shape: {responses_df.shape}")
    print(f"Full dataset shape: {full_dataset_df.shape}")
    print(f"Blind gradings entries: {len(blind_gradings)}")

    return tests_df, responses_df, full_dataset_df, blind_gradings

def compute_n1_protein_orders(full_dataset_df):
    """N1 (Line 45): Count unique protein orders in full-dataset.csv Order column"""
    unique_orders = full_dataset_df['Order'].nunique()
    print(f"N1: {unique_orders} unique protein orders")
    return unique_orders

def compute_n2_profiles_count(full_dataset_df):
    """N2 (Line 69): Total profiles count"""
    total_profiles = len(full_dataset_df)
    print(f"N2: {total_profiles} total profiles")
    return total_profiles

def compute_n3_institutional_emails(full_dataset_df):
    """N3 (Line 77): Percentage with institutional email domains"""
    # Common institutional email patterns
    institutional_patterns = [
        r'\.edu($|\.)',  # .edu domains
        r'\.ac\.uk$',    # UK academic domains
        r'\.ac\.[a-z]{2}$',  # Other academic domains
        r'\.org($|\.)',  # .org domains (often research institutions)
        r'university',   # University in domain name
        r'\.gov($|\.)',  # Government domains
        r'institute',    # Institute in domain name
        r'research',     # Research in domain name
    ]

    def is_institutional_email(email):
        if pd.isna(email) or email == '':
            return False

        # Extract domain from email
        if '@' in email:
            domain = email.split('@')[-1].lower()
        elif 'at ' in email.lower():
            # Handle "Verified email at domain.com" format
            parts = email.lower().split('at ')
            if len(parts) > 1:
                domain = parts[-1].strip()
            else:
                return False
        else:
            return False

        # Check against institutional patterns
        for pattern in institutional_patterns:
            if re.search(pattern, domain):
                return True
        return False

    institutional_count = full_dataset_df['Email'].apply(is_institutional_email).sum()
    percentage = (institutional_count / len(full_dataset_df)) * 100
    print(f"N3: {institutional_count}/{len(full_dataset_df)} = {percentage:.1f}% institutional emails")
    return percentage

def compute_n4_cohens_kappa(tests_df, blind_gradings):
    """N4 (Line 138): Cohen's kappa between blind_gradings.json and original results"""
    # Create mapping from blind gradings
    blind_grades_map = {}
    for entry in blind_gradings:
        eval_id = entry.get('eval_id')
        metric = entry.get('metric_name')
        blind_pass = entry.get('blind_pass')

        if eval_id and metric and blind_pass is not None:
            key = (eval_id, metric)
            blind_grades_map[key] = blind_pass

    # Match with original results
    original_passes = []
    blind_passes = []

    for _, row in tests_df.iterrows():
        eval_id = row['eval_id']
        metric = row['metric_name']
        original_pass = row['original_pass']

        key = (eval_id, metric)
        if key in blind_grades_map:
            original_passes.append(original_pass)
            blind_passes.append(blind_grades_map[key])

    if len(original_passes) > 0:
        kappa = cohen_kappa_score(original_passes, blind_passes)
        print(f"N4: Cohen's kappa = {kappa:.3f} (n={len(original_passes)} comparisons)")
        return kappa
    else:
        print("N4: No matching entries found for kappa calculation")
        return None

def compute_n6_response_times(responses_df):
    """N6 (Lines 152-153): Response time summary stats from latency_ms"""
    latency_stats = responses_df['latency_ms'].describe()

    # Convert to seconds
    mean_seconds = latency_stats['mean'] / 1000
    median_seconds = latency_stats['50%'] / 1000
    std_seconds = latency_stats['std'] / 1000

    print(f"N6: Response times - Mean: {mean_seconds:.1f}s, Median: {median_seconds:.1f}s, Std: {std_seconds:.1f}s")
    return {
        'mean': mean_seconds,
        'median': median_seconds,
        'std': std_seconds,
        'min': latency_stats['min'] / 1000,
        'max': latency_stats['max'] / 1000
    }

def compute_n7_cost_ratio(responses_df):
    """N7 (Line 171): Cheapest AI cost / $27 human cost ratio"""
    min_cost = responses_df['total_cost'].min()
    human_cost = 27.0  # $27 as stated in paper
    ratio = min_cost / human_cost

    print(f"N7: Cost ratio - Cheapest AI: ${min_cost:.4f}, Human: ${human_cost}, Ratio: 1/{1/ratio:.0f}")
    return ratio, min_cost

def compute_n8_average_pass_rate(tests_df):
    """N8 (Line 182): Average pass rate across all models/metrics"""
    total_tests = len(tests_df)
    total_passes = tests_df['pass'].sum()
    pass_rate = (total_passes / total_tests) * 100

    print(f"N8: Average pass rate = {total_passes}/{total_tests} = {pass_rate:.1f}%")
    return pass_rate

def compute_n9_best_ai_vs_human(tests_df):
    """N9 (Lines 183-184): Best AI vs 30min human flag accuracy comparison"""
    # Filter for flag accuracy metrics
    flag_tests = tests_df[tests_df['metric_name'].str.contains('FLAG', case=False, na=False)]

    if len(flag_tests) > 0:
        # Get best performing model
        model_performance = flag_tests.groupby('model_name')['pass'].mean()
        best_model = model_performance.idxmax()
        best_accuracy = model_performance.max() * 100

        # Get human baseline performance for flag metrics
        human_flag_tests = flag_tests[flag_tests['is_human_baseline'] == True]
        if len(human_flag_tests) > 0:
            human_accuracy = human_flag_tests['pass'].mean() * 100
            print(f"N9: Best AI ({best_model}): {best_accuracy:.1f}% vs Human: {human_accuracy:.1f}% flag accuracy")
            return best_accuracy, human_accuracy, best_model
        else:
            print(f"N9: Best AI ({best_model}): {best_accuracy:.1f}% flag accuracy (no human baseline found)")
            return best_accuracy, None, best_model
    else:
        print("N9: No flag accuracy metrics found")
        return None, None, None

def compute_n10_pass_rate_range(tests_df):
    """N10 (Lines 203-204): Range of pass rates across models"""
    model_pass_rates = tests_df.groupby('model_name')['pass'].mean() * 100
    min_rate = model_pass_rates.min()
    max_rate = model_pass_rates.max()
    range_pct = max_rate - min_rate

    print(f"N10: Pass rate range - Min: {min_rate:.1f}%, Max: {max_rate:.1f}%, Range: {range_pct:.1f}%")
    return min_rate, max_rate, range_pct

def compute_n11_cost_range(responses_df):
    """N11 (Line 207): Per-customer cost range"""
    cost_stats = responses_df['total_cost'].describe()
    min_cost = cost_stats['min']
    max_cost = cost_stats['max']

    print(f"N11: Cost range - Min: ${min_cost:.4f}, Max: ${max_cost:.4f}")
    return min_cost, max_cost

def compute_table1_verification(full_dataset_df):
    """Table 1 verification (Lines 67-76): Customer categories and regional distribution"""
    print("\n=== TABLE 1 VERIFICATION ===")

    # Customer category counts
    type_counts = full_dataset_df['Type'].value_counts()
    print("Customer Type Distribution:")
    for cat, count in type_counts.items():
        print(f"  {cat}: {count}")

    # Regional distribution (need to extract from Institution field)
    print("\nRegional Distribution Analysis:")
    # This would require parsing the Institution field for country information
    # For now, show unique values to understand the data
    institutions = full_dataset_df['Institution'].value_counts()
    print(f"Total unique institutions: {len(institutions)}")

    return type_counts

def compute_table2_completion(responses_df):
    """Table 2 completion (Lines 160-168): Mean cost and latency per model"""
    print("\n=== TABLE 2 COMPLETION ===")

    # Group by model and compute stats
    model_stats = responses_df.groupby(['model_name', 'model_type']).agg({
        'total_cost': ['mean', 'count'],
        'latency_ms': 'mean'
    }).round(4)

    print("Model Performance Stats:")
    print(model_stats)

    # Separate all-tools vs web-only
    all_tools_stats = responses_df[responses_df['model_type'] == 'all_tools'].groupby('model_name').agg({
        'total_cost': 'mean',
        'latency_ms': 'mean'
    })

    web_only_stats = responses_df[responses_df['model_type'] == 'web_only'].groupby('model_name').agg({
        'total_cost': 'mean',
        'latency_ms': 'mean'
    })

    print("\nAll-tools models:")
    print(all_tools_stats)
    print("\nWeb-only models:")
    print(web_only_stats)

    return model_stats

def main():
    """Main function to compute all metrics"""
    print("=== AI KYC RESULTS PAPER METRICS COMPUTATION ===\n")

    # Load data
    tests_df, responses_df, full_dataset_df, blind_gradings = load_data()

    print("\n=== COMPUTING NUMERICAL CLAIMS ===")

    # Compute all metrics
    n1 = compute_n1_protein_orders(full_dataset_df)
    n2 = compute_n2_profiles_count(full_dataset_df)
    n3 = compute_n3_institutional_emails(full_dataset_df)
    n4 = compute_n4_cohens_kappa(tests_df, blind_gradings)
    # N5 skipped (external estimate)
    n6 = compute_n6_response_times(responses_df)
    n7_ratio, n7_min_cost = compute_n7_cost_ratio(responses_df)
    n8 = compute_n8_average_pass_rate(tests_df)
    n9_ai, n9_human, n9_model = compute_n9_best_ai_vs_human(tests_df)
    n10_min, n10_max, n10_range = compute_n10_pass_rate_range(tests_df)
    n11_min, n11_max = compute_n11_cost_range(responses_df)

    # Verification tables
    table1 = compute_table1_verification(full_dataset_df)
    table2 = compute_table2_completion(responses_df)

    print("\n=== SUMMARY OF RESULTS ===")
    print(f"N1 (Protein orders): {n1}")
    print(f"N2 (Total profiles): {n2}")
    print(f"N3 (Institutional emails): {n3:.1f}%")
    print(f"N4 (Cohen's kappa): {n4:.3f}" if n4 else "N4: Not computed")
    print(f"N6 (Response time): Mean {n6['mean']:.1f}s, Median {n6['median']:.1f}s")
    print(f"N7 (Cost ratio): 1/{1/n7_ratio:.0f} (${n7_min_cost:.4f} vs $27)")
    print(f"N8 (Average pass rate): {n8:.1f}%")
    if n9_ai:
        print(f"N9 (Best AI vs Human): {n9_ai:.1f}% vs {n9_human:.1f}%" if n9_human else f"N9 (Best AI): {n9_ai:.1f}%")
    print(f"N10 (Pass rate range): {n10_min:.1f}% - {n10_max:.1f}% ({n10_range:.1f}% range)")
    print(f"N11 (Cost range): ${n11_min:.4f} - ${n11_max:.4f}")

if __name__ == "__main__":
    main()