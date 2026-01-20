#!/usr/bin/env python3
"""
Generate Figure 2: Human vs AI comparison by verification task.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

def load_and_filter_data():
    """Load data and filter for human baseline dataset."""
    print("Loading data...")
    df = pd.read_csv('/Users/alejo/Code/ai-kyc-results/processed/tests.csv')

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()

    print(f"Total rows in dataset: {len(df)}")
    print(f"Rows in human baseline dataset: {len(df_filtered)}")

    return df_filtered

def map_test_categories(df):
    """Map test categories to task names and create task-specific subsets."""

    # Create a mapping of test categories to tasks
    task_mapping = {
        'flag_accuracy': ['affiliation', 'institution', 'domain', 'sanctions'],
        'work_relevance': ['work_relevance']
    }

    # For flag_accuracy, we need to look at the metric_name to determine specific task
    tasks_data = []

    for _, row in df.iterrows():
        if row['test_category'] == 'flag_accuracy':
            # Map metric names to tasks
            metric = row['metric_name']
            if 'AFFILIATION' in metric:
                task = 'affiliation'
            elif 'INSTITUTION' in metric:
                task = 'institution'
            elif 'DOMAIN' in metric:
                task = 'domain'
            elif 'SANCTIONS' in metric:
                task = 'sanctions'
            else:
                continue

            tasks_data.append({
                'task': task,
                'model_label': row['model_label'],
                'pass': row['pass'],
                'is_human_baseline': row['is_human_baseline']
            })

        elif row['test_category'] == 'work_relevance':
            tasks_data.append({
                'task': 'work_relevance',
                'model_label': row['model_label'],
                'pass': row['pass'],
                'is_human_baseline': row['is_human_baseline']
            })

    return pd.DataFrame(tasks_data)

def calculate_performance_metrics(df_tasks):
    """Calculate error rates by task and model."""

    # Group by task and model, calculate pass rates and error rates
    performance = df_tasks.groupby(['task', 'model_label'])['pass'].agg(['count', 'sum']).reset_index()
    performance['pass_rate'] = performance['sum'] / performance['count']
    performance['error_rate'] = 1 - performance['pass_rate']
    performance['error_rate_pct'] = performance['error_rate'] * 100

    return performance

def identify_best_worst_models(performance):
    """Identify best and worst performing AI models for each task."""

    results = {}

    for task in performance['task'].unique():
        task_data = performance[performance['task'] == task]

        # Get human baseline error rate
        human_data = task_data[task_data['model_label'] == 'Human Baseline (30min)']
        human_error = human_data['error_rate_pct'].iloc[0] if len(human_data) > 0 else None

        # Get AI models only (exclude human baselines)
        ai_data = task_data[~task_data['model_label'].str.contains('Human Baseline')]

        if len(ai_data) > 0:
            # Best model (lowest error rate)
            best_model = ai_data.loc[ai_data['error_rate_pct'].idxmin()]

            # Worst model (highest error rate)
            worst_model = ai_data.loc[ai_data['error_rate_pct'].idxmax()]

            results[task] = {
                'human_error': human_error,
                'best_model': best_model['model_label'],
                'best_error': best_model['error_rate_pct'],
                'worst_model': worst_model['model_label'],
                'worst_error': worst_model['error_rate_pct']
            }

    return results

def create_figure(results):
    """Create the grouped bar chart."""

    # Set up the plot with publication quality settings
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Define task order and clean labels
    task_order = ['affiliation', 'institution', 'domain', 'sanctions', 'work_relevance']
    task_labels = {
        'affiliation': 'Affiliation',
        'institution': 'Institution Type',
        'domain': 'Email Domain',
        'sanctions': 'Sanctions',
        'work_relevance': 'Work Relevance'
    }

    # Prepare data for plotting
    x_pos = np.arange(len(task_order))
    width = 0.25

    human_errors = []
    best_errors = []
    worst_errors = []

    for task in task_order:
        if task in results:
            human_errors.append(results[task]['human_error'])
            best_errors.append(results[task]['best_error'])
            worst_errors.append(results[task]['worst_error'])
        else:
            human_errors.append(0)
            best_errors.append(0)
            worst_errors.append(0)

    # Create the grouped bars
    bars1 = ax.bar(x_pos - width, human_errors, width,
                   label='Human Baseline (30 min)', color='#E74C3C', alpha=0.8)
    bars2 = ax.bar(x_pos, best_errors, width,
                   label='Best AI Model', color='#27AE60', alpha=0.8)
    bars3 = ax.bar(x_pos + width, worst_errors, width,
                   label='Worst AI Model', color='#95A5A6', alpha=0.8)

    # Customize the plot
    ax.set_xlabel('Verification Task', fontsize=12, fontweight='bold')
    ax.set_ylabel('Error Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Human vs AI Performance by Verification Task', fontsize=14, fontweight='bold', pad=20)

    # Set x-axis labels
    ax.set_xticks(x_pos)
    ax.set_xticklabels([task_labels[task] for task in task_order], rotation=45, ha='right')

    # Format y-axis
    ax.set_ylim(0, max(max(human_errors), max(best_errors), max(worst_errors)) * 1.1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))

    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=9)

    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)

    # Add legend
    ax.legend(loc='center right', fontsize=10)

    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)

    # Tight layout
    plt.tight_layout()

    return fig

def print_model_details(results):
    """Print which specific models were best/worst for each task."""
    print("\nBest and Worst AI Models by Task:")
    print("=" * 50)

    for task, data in results.items():
        print(f"\n{task.upper()}:")
        print(f"  Human Baseline (30min): {data['human_error']:.1f}% error rate")
        print(f"  Best AI Model: {data['best_model']} ({data['best_error']:.1f}% error rate)")
        print(f"  Worst AI Model: {data['worst_model']} ({data['worst_error']:.1f}% error rate)")

def main():
    """Main function to generate the figure."""

    # Load and process data
    df = load_and_filter_data()
    df_tasks = map_test_categories(df)

    print(f"\nTask breakdown:")
    print(df_tasks['task'].value_counts())

    print(f"\nModel breakdown:")
    print(df_tasks['model_label'].value_counts())

    # Calculate performance metrics
    performance = calculate_performance_metrics(df_tasks)

    # Identify best and worst models
    results = identify_best_worst_models(performance)

    # Print model details
    print_model_details(results)

    # Create and save figure
    fig = create_figure(results)

    # Create output directory if it doesn't exist
    output_dir = Path('/Users/alejo/Code/ai-kyc-results/paper/figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save figure
    output_path = output_dir / 'figure2_human_vs_ai_comparison.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    print(f"\nFigure saved to: {output_path}")

    # Also show the figure
    plt.show()

if __name__ == "__main__":
    main()