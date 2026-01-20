#!/usr/bin/env python3
import pandas as pd
import re

# Load data
full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')
print(f"Total profiles: {len(full_dataset_df)}")

# Count different email types
verified_emails = full_dataset_df['Email'].str.contains('Verified email at', na=False).sum()
direct_emails = (~full_dataset_df['Email'].str.contains('Verified email at', na=False)).sum()

print(f"\nEmail breakdown:")
print(f"  Verified email at [domain]: {verified_emails}")
print(f"  Direct email addresses: {direct_emails}")

# The original paper says 69% (94/136) had matching domains
# This suggests they were looking at institutional vs personal domains
# Let's count institutional-looking domains (not gmail, hotmail, 163.com etc)

personal_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', '163.com', 'outlook.com', 'qq.com']

def is_institutional_email(email):
    if pd.isna(email):
        return False
    if 'Verified email at' in email:
        return True  # These are institutional
    # Check if it's a personal domain
    for domain in personal_domains:
        if domain in email:
            return False
    return True  # Assume other domains are institutional

institutional_count = full_dataset_df['Email'].apply(is_institutional_email).sum()
print(f"\nInstitutional emails (verified + non-personal domains): {institutional_count}")
print(f"Percentage: {institutional_count / len(full_dataset_df) * 100:.1f}%")

# Show some examples of each type
print(f"\nExamples of verified emails:")
verified = full_dataset_df[full_dataset_df['Email'].str.contains('Verified email at', na=False)]['Email']
for i, email in enumerate(verified.head(5)):
    print(f"  {email}")

print(f"\nExamples of direct emails:")
direct = full_dataset_df[~full_dataset_df['Email'].str.contains('Verified email at', na=False)]['Email']
for i, email in enumerate(direct.head(5)):
    print(f"  {email}")