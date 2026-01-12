#!/usr/bin/env python3
"""
Analyze data for Figure 2: Human vs AI comparison.
"""

import pandas as pd
import sys

def load_and_filter_data():
    """Load data and filter for human baseline dataset."""
    print("Loading data...")
    df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()

    print(f"Total rows in dataset: {len(df)}")
    print(f"Rows in human baseline dataset: {len(df_filtered)}")

    # Check what we have
    print("\nTest categories in human baseline dataset:")
    print(df_filtered['test_category'].value_counts())

    print("\nModel labels in human baseline dataset:")
    print(df_filtered['model_label'].value_counts())

    print("\nMetric names in human baseline dataset:")
    print(df_filtered['metric_name'].value_counts())

    return df_filtered

def main():
    try:
        df = load_and_filter_data()

        # Sample a few rows to see the data structure
        print("\nSample rows:")
        sample_cols = ['model_label', 'test_category', 'metric_name', 'pass', 'is_human_baseline']
        print(df[sample_cols].head(10))

        # Check for Human Baseline (30min) specifically
        human_30min = df[df['model_label'] == 'Human Baseline (30min)']
        print(f"\nHuman Baseline (30min) rows: {len(human_30min)}")

        if len(human_30min) > 0:
            print("Human Baseline (30min) test categories:")
            print(human_30min['test_category'].value_counts())

            print("Human Baseline (30min) metric names:")
            print(human_30min['metric_name'].value_counts())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()