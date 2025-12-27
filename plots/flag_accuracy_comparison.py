"""
Compare flag accuracy between GLM 4.6 (All Tools) and Human Baseline (30min).
Creates PDF/image tables showing disagreements.

Uses the same criteria as plot_pass_rates.py:
- Uses the pre-computed 'pass' column
- Filters for is_human_baseline_dataset == True
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from pathlib import Path

from style import setup_style, OUTPUT_DIR, DATA_DIR, COLORS

setup_style()

# Load data (same as plot_pass_rates.py)
df = pd.read_csv(DATA_DIR / "tests.csv")
df["pass"] = df["pass"].astype(str) == "True"

# Filter for flag_accuracy tests only AND human baseline dataset (same as heatmap)
flag_df = df[
    (df["test_category"] == "flag_accuracy") &
    (df["is_human_baseline_dataset"] == True)
].copy()

print(f"Total flag_accuracy tests in HB dataset: {len(flag_df)}")

# Get the two models we're comparing
glm_label = "GLM 4.6 (All Tools)"
human_label = "Human Baseline (30min)"

# Filter for these models
cols_needed = ["customer_name", "customer_institution", "customer_type", "order",
               "pass", "extracted_flag", "metric_name",
               "ground_truth_affiliation", "ground_truth_institution",
               "ground_truth_domain", "ground_truth_sanctions"]
glm_df = flag_df[flag_df["model_label"] == glm_label][cols_needed].copy()
human_df = flag_df[flag_df["model_label"] == human_label][cols_needed].copy()

# Map metric to correct ground truth column
def get_ground_truth_for_metric(row):
    metric = row["metric_name"]
    if "AFFILIATION" in metric:
        return row["ground_truth_affiliation"]
    elif "INSTITUTION" in metric:
        return row["ground_truth_institution"]
    elif "DOMAIN" in metric:
        return row["ground_truth_domain"]
    elif "SANCTIONS" in metric:
        return row["ground_truth_sanctions"]
    return "UNDETERMINED"

glm_df["ground_truth"] = glm_df.apply(get_ground_truth_for_metric, axis=1)
human_df["ground_truth"] = human_df.apply(get_ground_truth_for_metric, axis=1)

print(f"GLM entries: {len(glm_df)}")
print(f"Human entries: {len(human_df)}")

# Check overall pass rates to verify they match the heatmap
glm_pass_rate = glm_df["pass"].mean() * 100
human_pass_rate = human_df["pass"].mean() * 100
print(f"\nOverall pass rates (should match heatmap):")
print(f"  GLM 4.6 (All Tools): {glm_pass_rate:.1f}%")
print(f"  Human Baseline (30min): {human_pass_rate:.1f}%")

# Rename columns for clarity
glm_df = glm_df.rename(columns={"pass": "glm_pass", "extracted_flag": "glm_flag"})
human_df = human_df.rename(columns={"pass": "human_pass", "extracted_flag": "human_flag"})

# Merge on customer_name, order, and metric_name to get exact test-level comparison
merged = pd.merge(
    glm_df[["customer_name", "customer_institution", "customer_type", "order",
            "metric_name", "glm_pass", "glm_flag", "ground_truth"]],
    human_df[["customer_name", "order", "metric_name", "human_pass", "human_flag"]],
    on=["customer_name", "order", "metric_name"],
    how="inner"
)

print(f"\nMerged entries (test-level): {len(merged)}")

# Find disagreements at test level
glm_right_human_wrong = merged[(merged["glm_pass"]) & (~merged["human_pass"])]
glm_wrong_human_right = merged[(~merged["glm_pass"]) & (merged["human_pass"])]

print(f"\nGLM passes, Human fails: {len(glm_right_human_wrong)}")
print(f"GLM fails, Human passes: {len(glm_wrong_human_right)}")


def create_table_figure(data, title, subtitle=""):
    """Create a nice table figure from dataframe."""
    if len(data) == 0:
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, "No entries found", ha='center', va='center', fontsize=14)
        ax.axis('off')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        return fig

    # Prepare display data
    display_cols = ["customer_name", "customer_type", "order", "metric_name", "glm_flag", "human_flag", "ground_truth"]
    display_df = data[display_cols].copy()

    # Truncate long strings
    def truncate(s, max_len=30):
        if pd.isna(s):
            return ""
        s = str(s)
        return s[:max_len] + "..." if len(s) > max_len else s

    # Shorten customer types
    def shorten_type(t):
        if pd.isna(t):
            return ""
        t = str(t)
        mapping = {
            "Controlled Agent Academia": "Academia",
            "Controlled Agent Industry": "Industry",
            "General Life Science Customers": "Life Science",
            "Sanctioned Institution Customers": "Sanctioned",
        }
        return mapping.get(t, t[:15])

    # Shorten metric names
    def shorten_metric(m):
        if pd.isna(m):
            return ""
        m = str(m)
        # Remove common suffixes/prefixes
        m = m.replace("-FLAG-ACCURACY", "").replace("FLAG-ACCURACY", "")
        return m[:12]

    display_df["customer_name"] = display_df["customer_name"].apply(lambda x: truncate(x, 20))
    display_df["customer_type"] = display_df["customer_type"].apply(shorten_type)
    display_df["order"] = display_df["order"].apply(lambda x: truncate(x, 30))
    display_df["metric_name"] = display_df["metric_name"].apply(shorten_metric)
    display_df["glm_flag"] = display_df["glm_flag"].apply(lambda x: truncate(x, 12))
    display_df["human_flag"] = display_df["human_flag"].apply(lambda x: truncate(x, 12))
    display_df["ground_truth"] = display_df["ground_truth"].apply(lambda x: truncate(x, 12))

    # Rename for display
    display_df.columns = ["Customer", "Type", "Order", "Metric", "GLM", "Human", "Truth"]

    # Calculate figure height based on rows
    n_rows = len(display_df)
    fig_height = max(3, 1.5 + n_rows * 0.5)
    fig_width = 16

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')

    # Add title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    if subtitle:
        ax.set_title(subtitle, fontsize=11, style='italic', pad=10)

    # Create table
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc='left',
        loc='center',
        colWidths=[0.15, 0.10, 0.25, 0.12, 0.12, 0.12, 0.12]
    )

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    # Style header
    for j, col in enumerate(display_df.columns):
        cell = table[(0, j)]
        cell.set_facecolor('#2C3E50')
        cell.set_text_props(color='white', fontweight='bold')

    # Alternate row colors
    for i in range(1, n_rows + 1):
        for j in range(len(display_df.columns)):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#F8F9FA')
            else:
                cell.set_facecolor('#FFFFFF')

    plt.tight_layout()
    return fig


# Create figures
fig1 = create_table_figure(
    glm_right_human_wrong,
    "GLM 4.6 (All Tools) Passes, Human Baseline (30min) Fails",
    f"Total: {len(glm_right_human_wrong)} test entries"
)

fig2 = create_table_figure(
    glm_wrong_human_right,
    "GLM 4.6 (All Tools) Fails, Human Baseline (30min) Passes",
    f"Total: {len(glm_wrong_human_right)} test entries"
)

# Save as PDF with both tables
pdf_path = OUTPUT_DIR / "flag_accuracy_glm_vs_human_comparison.pdf"
with PdfPages(pdf_path) as pdf:
    pdf.savefig(fig1, bbox_inches='tight')
    pdf.savefig(fig2, bbox_inches='tight')

print(f"\nSaved PDF: {pdf_path}")

# Also save as separate PNGs
png1_path = OUTPUT_DIR / "flag_accuracy_glm_right_human_wrong.png"
png2_path = OUTPUT_DIR / "flag_accuracy_glm_wrong_human_right.png"

fig1.savefig(png1_path, bbox_inches='tight', dpi=300)
fig2.savefig(png2_path, bbox_inches='tight', dpi=300)

print(f"Saved PNG: {png1_path}")
print(f"Saved PNG: {png2_path}")

plt.close('all')

# Print detailed info
print("\n" + "="*80)
print("DETAILED ENTRIES: GLM Passes, Human Fails")
print("="*80)
for idx, row in glm_right_human_wrong.iterrows():
    print(f"\n{row['customer_name']} | {row['customer_type']}")
    print(f"  Order: {row['order']}")
    print(f"  Metric: {row['metric_name']}")
    print(f"  GLM: {row['glm_flag']} (pass={row['glm_pass']}) | Human: {row['human_flag']} (pass={row['human_pass']}) | Truth: {row['ground_truth']}")

print("\n" + "="*80)
print("DETAILED ENTRIES: GLM Fails, Human Passes")
print("="*80)
for idx, row in glm_wrong_human_right.iterrows():
    print(f"\n{row['customer_name']} | {row['customer_type']}")
    print(f"  Order: {row['order']}")
    print(f"  Metric: {row['metric_name']}")
    print(f"  GLM: {row['glm_flag']} (pass={row['glm_pass']}) | Human: {row['human_flag']} (pass={row['human_pass']}) | Truth: {row['ground_truth']}")
