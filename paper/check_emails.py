#!/usr/bin/env python3
import pandas as pd

# Load data
full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')
print(f"Total profiles: {len(full_dataset_df)}")

# Check email pattern
print("\nEmail patterns:")
email_counts = full_dataset_df['Email'].value_counts()
for email, count in email_counts.head(10).items():
    print(f"  '{email}': {count}")

# Count institutional emails - those that have "Verified email at" prefix
institutional = full_dataset_df[full_dataset_df['Email'].str.contains('Verified email at', na=False)]
print(f"\nInstitutional emails (with 'Verified email at'): {len(institutional)}")
print(f"Percentage: {len(institutional) / len(full_dataset_df) * 100:.1f}%")

# Let's also check what the text originally said - 94/136 = 69%
print(f"\nOriginal text claim: 94/136 = {94/136*100:.1f}%")
print(f"Actual calculation: {len(institutional)}/{len(full_dataset_df)} = {len(institutional)/len(full_dataset_df)*100:.1f}%")