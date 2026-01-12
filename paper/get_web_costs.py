#!/usr/bin/env python3
import pandas as pd

# Load data
responses_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/responses.csv')

print("Web-search-only model costs:")
web_only_models = responses_df[responses_df['model_type'] == 'web_only']
web_costs = web_only_models.groupby('model_label').agg({
    'total_cost': 'mean',
    'latency_ms': lambda x: x.mean() / 1000,  # Convert to seconds
}).round(3)

for model, row in web_costs.iterrows():
    if 'Human' not in model:
        print(f"{model}: ${row['total_cost']:.3f}, {row['latency_ms']:.1f}s")