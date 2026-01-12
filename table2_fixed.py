#!/usr/bin/env python3
"""
Fixed Table 2 analysis
"""

import pandas as pd

def compute_table2_fixed():
    """Complete Table 2 analysis with fixed aggregation"""
    responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')

    print("=== COMPLETE TABLE 2 ===")

    # Separate by model type
    all_tools = responses_df[responses_df['model_type'] == 'all_tools']
    web_only = responses_df[responses_df['model_type'] == 'web_only']

    print(f"All-tools responses: {len(all_tools)}")
    print(f"Web-only responses: {len(web_only)}")

    print("\n=== MODEL PERFORMANCE BY TYPE ===")
    print("Model Name                | Type      | Mean Cost | Mean Latency (s) | Count")
    print("-" * 75)

    for (model, model_type), group in responses_df.groupby(['model_name', 'model_type']):
        mean_cost = group['total_cost'].mean()
        mean_latency = group['latency_ms'].mean() / 1000
        count = len(group)
        print(f"{model:<25} | {model_type:<9} | ${mean_cost:<8.4f} | {mean_latency:<12.1f} | {count}")

    # Compute summary statistics correctly
    print("\n=== SUMMARY COMPARISON ===")

    all_tools_cost_mean = all_tools['total_cost'].mean()
    all_tools_cost_std = all_tools['total_cost'].std()
    all_tools_latency_mean = all_tools['latency_ms'].mean() / 1000
    all_tools_latency_std = all_tools['latency_ms'].std() / 1000

    web_only_cost_mean = web_only['total_cost'].mean()
    web_only_cost_std = web_only['total_cost'].std()
    web_only_latency_mean = web_only['latency_ms'].mean() / 1000
    web_only_latency_std = web_only['latency_ms'].std() / 1000

    print("All-tools models:")
    print(f"  Mean cost: ${all_tools_cost_mean:.4f} ± ${all_tools_cost_std:.4f}")
    print(f"  Mean latency: {all_tools_latency_mean:.1f}s ± {all_tools_latency_std:.1f}s")

    print("\nWeb-only models:")
    print(f"  Mean cost: ${web_only_cost_mean:.4f} ± ${web_only_cost_std:.4f}")
    print(f"  Mean latency: {web_only_latency_mean:.1f}s ± {web_only_latency_std:.1f}s")

    # Show cost comparison (all-tools vs web-only)
    print("\n=== COST COMPARISON (All-tools vs Web-only) ===")
    for model in responses_df['model_name'].unique():
        all_tools_cost = responses_df[(responses_df['model_name'] == model) &
                                     (responses_df['model_type'] == 'all_tools')]['total_cost'].mean()
        web_only_cost = responses_df[(responses_df['model_name'] == model) &
                                    (responses_df['model_type'] == 'web_only')]['total_cost'].mean()

        if pd.notna(all_tools_cost) and pd.notna(web_only_cost):
            diff = ((web_only_cost - all_tools_cost) / all_tools_cost) * 100
            print(f"{model}: All-tools ${all_tools_cost:.4f} vs Web-only ${web_only_cost:.4f} ({diff:+.1f}%)")

if __name__ == "__main__":
    compute_table2_fixed()