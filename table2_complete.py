#!/usr/bin/env python3
"""
Complete Table 2 with web-only vs all-tools comparison
"""

import pandas as pd

def compute_table2_complete():
    """Complete Table 2 analysis"""
    responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')

    print("=== COMPLETE TABLE 2 ===")

    # Separate by model type
    all_tools = responses_df[responses_df['model_type'] == 'all_tools']
    web_only = responses_df[responses_df['model_type'] == 'web_only']

    print(f"All-tools responses: {len(all_tools)}")
    print(f"Web-only responses: {len(web_only)}")

    # Compute stats for each model and type
    model_stats = responses_df.groupby(['model_name', 'model_type']).agg({
        'total_cost': ['mean', 'count'],
        'latency_ms': 'mean'
    }).round(4)

    # Convert latency to seconds
    model_stats[('latency_ms', 'mean')] = model_stats[('latency_ms', 'mean')] / 1000

    print("\n=== MODEL PERFORMANCE BY TYPE ===")
    print("Format: Model Name | Type | Mean Cost | Mean Latency (s) | Count")
    print("-" * 70)

    for (model, model_type), group in responses_df.groupby(['model_name', 'model_type']):
        mean_cost = group['total_cost'].mean()
        mean_latency = group['latency_ms'].mean() / 1000
        count = len(group)
        print(f"{model:<25} | {model_type:<9} | ${mean_cost:<8.4f} | {mean_latency:<8.1f}s | {count}")

    # Compute summary statistics
    print("\n=== SUMMARY COMPARISON ===")
    all_tools_summary = all_tools.agg({
        'total_cost': ['mean', 'std'],
        'latency_ms': ['mean', 'std']
    })

    web_only_summary = web_only.agg({
        'total_cost': ['mean', 'std'],
        'latency_ms': ['mean', 'std']
    })

    print("All-tools models:")
    print(f"  Mean cost: ${all_tools_summary[('total_cost', 'mean')]:.4f} ± ${all_tools_summary[('total_cost', 'std')]:.4f}")
    print(f"  Mean latency: {all_tools_summary[('latency_ms', 'mean')]/1000:.1f}s ± {all_tools_summary[('latency_ms', 'std')]/1000:.1f}s")

    print("\nWeb-only models:")
    print(f"  Mean cost: ${web_only_summary[('total_cost', 'mean')]:.4f} ± ${web_only_summary[('total_cost', 'std')]:.4f}")
    print(f"  Mean latency: {web_only_summary[('latency_ms', 'mean')]/1000:.1f}s ± {web_only_summary[('latency_ms', 'std')]/1000:.1f}s")

    return model_stats

if __name__ == "__main__":
    compute_table2_complete()