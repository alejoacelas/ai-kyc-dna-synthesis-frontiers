#!/usr/bin/env python3
import pandas as pd

# Load data
full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

# Personal domains typically used for non-institutional email
personal_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', '163.com', 'outlook.com', 'qq.com', 'rambler.ru', '126.com', 'sina.com']

def has_institutional_domain(email):
    if pd.isna(email):
        return False

    # Remove "Verified email at " prefix if present
    clean_email = email.replace('Verified email at ', '')

    # Check if it contains any personal domain
    for domain in personal_domains:
        if domain in clean_email.lower():
            return False

    # Check if it looks like an email (has @ symbol)
    if '@' not in clean_email:
        return False

    return True

# Count institutional domains
institutional_count = full_dataset_df['Email'].apply(has_institutional_domain).sum()
personal_count = len(full_dataset_df) - institutional_count

print(f"Total profiles: {len(full_dataset_df)}")
print(f"Institutional email domains: {institutional_count}")
print(f"Personal email domains: {personal_count}")
print(f"Percentage with institutional domains: {institutional_count / len(full_dataset_df) * 100:.1f}%")

# This should be close to the original 69% (94/136)
print(f"\nOriginal claim was 69% (94/136)")
print(f"Current result: {institutional_count/len(full_dataset_df)*100:.1f}% ({institutional_count}/{len(full_dataset_df)})")

# Show examples of personal domains found
personal_emails = full_dataset_df[~full_dataset_df['Email'].apply(has_institutional_domain)]['Email']
print(f"\nExamples of personal domain emails:")
for email in personal_emails.head(10):
    print(f"  {email}")