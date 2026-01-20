#!/usr/bin/env python3

import re

# Read the updated paper
with open('/Users/alejo/Code/ai-kyc-results/paper/paper_draft.md', 'r') as f:
    content = f.read()

print("Verification of paper updates:")
print("=" * 50)

# Check key values
updates = [
    (r"26 proteins", "N1 - Unique protein orders"),
    (r"134.*total", "N2 - Total profiles"),
    (r"80\.6%.*\(108/134\)", "N3 - Institutional emails"),
    (r"Cohen's kappa: 0\.095", "N4 - Cohen's kappa"),
    (r"Mean response time was 28\.0 seconds", "N6 - Response time"),
    (r"1/818th", "N7 - Cost ratio"),
    (r"83\.4%", "N8 - Overall pass rate"),
    (r"93\.9%.*69\.2%", "N9 - Flag accuracy AI vs human"),
    (r"3\.4 percentage points", "N10 - Pass rate range"),
    (r"\$0\.033.*\$0\.343", "N11 - Cost range"),
]

for pattern, description in updates:
    matches = re.findall(pattern, content, re.IGNORECASE)
    if matches:
        print(f"✓ {description}: Found")
    else:
        print(f"✗ {description}: NOT FOUND")

# Check figure references
figures = [
    "figure1_pass_rates_heatmap.png",
    "figure2_human_vs_ai_comparison.png",
    "figure3_model_rankings.png",
    "figure4_web_vs_tools_comparison.png",
    "figure6_geographic_breakdown.png"
]

print("\nFigure references:")
for fig in figures:
    if fig in content:
        print(f"✓ {fig}: Referenced")
    else:
        print(f"✗ {fig}: NOT FOUND")

# Check for remaining placeholders
placeholders = re.findall(r'\[.*?PLACEHOLDER.*?\]', content)
if placeholders:
    print(f"\n⚠ Warning: {len(placeholders)} placeholders remain:")
    for p in placeholders:
        print(f"  - {p}")
else:
    print(f"\n✓ No placeholders remaining")

print(f"\nTotal paper length: {len(content.split())} words")