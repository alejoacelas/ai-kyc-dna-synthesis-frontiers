#!/usr/bin/env python3
import pandas as pd

# Load data
full_dataset_df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/data/full-dataset.csv')

# Personal domains
personal_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', '163.com', 'outlook.com', 'qq.com', 'rambler.ru', '126.com', 'sina.com']

def has_institutional_domain(email):
    if pd.isna(email) or email == 'Not provided':
        return False

    # Handle "Verified email at domain" format
    if email.startswith('Verified email at '):
        domain = email.replace('Verified email at ', '')
        # These are institutional by definition of the verification process
        return True

    # For regular email addresses, check domain
    if '@' in email:
        domain = email.split('@')[1].lower()
        return domain not in personal_domains

    return False

# Count institutional domains
institutional_count = full_dataset_df['Email'].apply(has_institutional_domain).sum()
total_profiles = len(full_dataset_df)

print(f"Total profiles: {total_profiles}")
print(f"Institutional email domains: {institutional_count}")
print(f"Percentage with institutional domains: {institutional_count / total_profiles * 100:.1f}%")

# Break down by type
verified_count = full_dataset_df['Email'].str.startswith('Verified email at ', na=False).sum()
regular_institutional = institutional_count - verified_count

print(f"\nBreakdown:")
print(f"  'Verified email at' entries: {verified_count}")
print(f"  Regular institutional emails: {regular_institutional}")
print(f"  Total institutional: {institutional_count}")

# Show some examples of each category
print(f"\nExamples by category:")

# Verified emails
verified_emails = full_dataset_df[full_dataset_df['Email'].str.startswith('Verified email at ', na=False)]['Email']
print(f"Verified emails (first 5):")
for email in verified_emails.head(5):
    print(f"  {email}")

# Regular institutional emails
regular_emails = full_dataset_df[
    full_dataset_df['Email'].apply(lambda x: has_institutional_domain(x) and not (pd.notna(x) and x.startswith('Verified email at ')))
]['Email']
print(f"\nRegular institutional emails (first 5):")
for email in regular_emails.head(5):
    print(f"  {email}")

# Personal emails
personal_emails = full_dataset_df[~full_dataset_df['Email'].apply(has_institutional_domain)]['Email']
print(f"\nPersonal/non-institutional emails (first 5):")
for email in personal_emails.head(5):
    print(f"  {email}")