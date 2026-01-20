#!/usr/bin/env python3
"""
Generate Figure 6: Flag accuracy error breakdown by task and region.

Shows error rates by customer region and flag task (affiliation, domain,
institution, sanctions), split by error type:
- Missed flag: Should have flagged but didn't (False Negative)
- False flag: Should not have flagged but did (False Positive)
- Undetermined: Model returned undetermined flag
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


# Task mapping from metric_name to display label and ground truth column
TASK_CONFIG = {
    'AFFILIATION-FLAG-ACCURACY': {
        'label': 'Institutional\nAffiliation',
        'ground_truth_col': 'ground_truth_affiliation',
        'order': 0,
    },
    'INSTITUTION-FLAG-ACCURACY': {
        'label': 'Institution\nType',
        'ground_truth_col': 'ground_truth_institution',
        'order': 1,
    },
    'DOMAIN-FLAG-ACCURACY': {
        'label': 'Email\nDomain',
        'ground_truth_col': 'ground_truth_domain',
        'order': 2,
    },
    'SANCTIONS-FLAG-ACCURACY': {
        'label': 'Sanctions\nScreening',
        'ground_truth_col': 'ground_truth_sanctions',
        'order': 3,
    },
}


def classify_error(row):
    """Classify the type of error for a flag accuracy test."""
    metric = row['metric_name']
    if metric not in TASK_CONFIG:
        return None

    gt_col = TASK_CONFIG[metric]['ground_truth_col']
    ground_truth = row[gt_col]
    extracted = row['extracted_flag']

    # If passed, no error
    if row['pass']:
        return 'correct'

    # Classify error type
    if extracted == 'UNDETERMINED':
        return 'undetermined'
    elif ground_truth == 'FLAG' and extracted == 'NO FLAG':
        return 'missed_flag'  # False negative
    elif ground_truth == 'NO FLAG' and extracted == 'FLAG':
        return 'false_flag'  # False positive
    else:
        # Other cases (e.g., ground_truth is UNDETERMINED)
        return 'other'


def generate_figure6():
    # Read the data
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)

    # Filter for flag accuracy, AI models only, human baseline dataset
    df_flag = df[
        (df['test_category'] == 'flag_accuracy') &
        (df['is_human_baseline'] == False) &
        (df['is_human_baseline_dataset'] == True)
    ].copy()

    print(f"Total flag accuracy records: {len(df_flag)}")
    print(f"Records by metric: \n{df_flag['metric_name'].value_counts()}")
    print(f"Records by region: \n{df_flag['institution_country'].value_counts()}")

    # Classify each error
    df_flag['error_type'] = df_flag.apply(classify_error, axis=1)

    print(f"\nError type distribution:")
    print(df_flag['error_type'].value_counts())

    # Extract task from metric_name
    df_flag['task'] = df_flag['metric_name'].map(lambda x: TASK_CONFIG.get(x, {}).get('label', x))
    df_flag['task_order'] = df_flag['metric_name'].map(lambda x: TASK_CONFIG.get(x, {}).get('order', 99))

    # Rename regions
    df_flag['region'] = df_flag['institution_country'].replace({'Others': 'Other countries'})

    # Calculate error rates by region and task
    error_types = ['missed_flag', 'false_flag', 'undetermined']
    error_labels = {
        'missed_flag': 'Missed Flag',
        'false_flag': 'False Flag',
        'undetermined': 'Undetermined',
    }

    # Get unique tasks and regions
    tasks = sorted(df_flag['task'].unique(), key=lambda x: df_flag[df_flag['task'] == x]['task_order'].iloc[0])
    region_order = ['USA', 'Europe + Australia', 'China', 'Other countries']
    regions = [r for r in region_order if r in df_flag['region'].unique()]

    # Calculate error rates
    results = []
    for region in regions:
        for task in tasks:
            subset = df_flag[(df_flag['region'] == region) & (df_flag['task'] == task)]
            total = len(subset)
            if total > 0:
                for error_type in error_types:
                    count = (subset['error_type'] == error_type).sum()
                    rate = count / total * 100
                    results.append({
                        'region': region,
                        'task': task,
                        'error_type': error_type,
                        'error_rate': rate,
                        'count': count,
                        'total': total,
                    })

    results_df = pd.DataFrame(results)

    # Print summary
    print("\nError rates by region and task:")
    pivot = results_df.pivot_table(
        index=['region', 'task'],
        columns='error_type',
        values='error_rate',
        aggfunc='first'
    )
    print(pivot.round(1))

    # Create the plot
    fig, axes = plt.subplots(1, len(tasks), figsize=(14, 6), sharey=True)

    # Colors for error types
    error_colors = {
        'missed_flag': '#dc2626',    # Red - missed flags are serious
        'false_flag': '#f97316',     # Orange - false flags are less serious
        'undetermined': '#6b7280',   # Gray - undetermined
    }

    bar_width = 0.25
    x = np.arange(len(regions))

    for idx, task in enumerate(tasks):
        ax = axes[idx]
        task_data = results_df[results_df['task'] == task]

        for i, error_type in enumerate(error_types):
            error_data = task_data[task_data['error_type'] == error_type]
            values = [error_data[error_data['region'] == r]['error_rate'].values[0]
                     if len(error_data[error_data['region'] == r]) > 0 else 0
                     for r in regions]

            offset = (i - 1) * bar_width
            bars = ax.bar(x + offset, values, bar_width,
                         label=error_labels[error_type] if idx == 0 else '',
                         color=error_colors[error_type],
                         alpha=0.85,
                         edgecolor='white',
                         linewidth=0.5)

            # Add value labels on bars
            for bar, val in zip(bars, values):
                if val > 0.5:  # Only label if visible
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                           f'{val:.1f}', ha='center', va='bottom', fontsize=8)

        ax.set_title(task, fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([r.replace(' + ', '\n+ ').replace(' countries', '\ncountries')
                          for r in regions], fontsize=9)
        ax.set_ylim(0, max(results_df['error_rate']) * 1.15)

        if idx == 0:
            ax.set_ylabel('Error Rate (%)', fontsize=12, fontweight='bold')

        ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    # Add shared legend at bottom
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=10,
              bbox_to_anchor=(0.5, -0.02), frameon=True)

    fig.suptitle('Flag Accuracy Error Rates by Task and Customer Region\n(Average across AI Models)',
                fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)

    # Save the figure
    output_path = Path(__file__).parent.parent.parent / "paper" / "figures" / "figure6_flag_errors_by_task_region.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    # Overall error rates by type
    overall_by_type = results_df.groupby('error_type')['error_rate'].mean()
    print("\nOverall average error rates by type:")
    for error_type in error_types:
        print(f"  {error_labels[error_type].replace(chr(10), ' ')}: {overall_by_type[error_type]:.1f}%")

    # Error rates by region
    overall_by_region = results_df.groupby('region')['error_rate'].sum()
    print("\nTotal error rate by region:")
    for region in regions:
        print(f"  {region}: {overall_by_region[region]:.1f}%")

    # Error rates by task
    overall_by_task = results_df.groupby('task')['error_rate'].sum()
    print("\nTotal error rate by task:")
    for task in tasks:
        print(f"  {task.replace(chr(10), ' ')}: {overall_by_task[task]:.1f}%")

    plt.show()

    return results_df


if __name__ == "__main__":
    result = generate_figure6()
