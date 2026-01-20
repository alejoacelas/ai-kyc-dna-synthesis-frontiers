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
    data_path = Path(__file__).parent.parent.parent / "processed" / "tests.csv"
    df = pd.read_csv(data_path)

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()

    print(f"Total rows in dataset: {len(df)}")
    print(f"Rows in human baseline dataset: {len(df_filtered)}")

    return df_filtered

def map_metric_to_tasks(df):
    """Map metric names to flag accuracy criteria only."""
    tasks_data = []

    for _, row in df.iterrows():
        metric = row['metric_name']

        # Map metric names to the four flag accuracy criteria
        if metric == 'AFFILIATION-FLAG-ACCURACY':
            task = 'affiliation'
        elif metric == 'INSTITUTION-FLAG-ACCURACY':
            task = 'institution'
        elif metric == 'DOMAIN-FLAG-ACCURACY':
            task = 'domain'
        elif metric == 'SANCTIONS-FLAG-ACCURACY':
            task = 'sanctions'
        else:
            # Skip other metrics not relevant for this figure
            continue

        tasks_data.append({
            'task': task,
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
        task_data = performance[performance['task'] == task].copy()

        # Get human baseline error rate (30 min)
        human_data = task_data[task_data['model_label'] == 'Human Baseline (30min)']
        human_error = human_data['error_rate_pct'].iloc[0] if len(human_data) > 0 else None

        # Get AI models only (exclude human baselines)
        ai_data = task_data[~task_data['model_label'].str.contains('Human Baseline')]

        if len(ai_data) > 0:
            # Best model (lowest error rate)
            best_idx = ai_data['error_rate_pct'].idxmin()
            best_model = ai_data.loc[best_idx]

            # Worst model (highest error rate)
            worst_idx = ai_data['error_rate_pct'].idxmax()
            worst_model = ai_data.loc[worst_idx]

            results[task] = {
                'human_error': human_error,
                'human_count': human_data['count'].iloc[0] if len(human_data) > 0 else 0,
                'best_model': best_model['model_label'],
                'best_error': best_model['error_rate_pct'],
                'best_count': best_model['count'],
                'worst_model': worst_model['model_label'],
                'worst_error': worst_model['error_rate_pct'],
                'worst_count': worst_model['count']
            }

    return results

def create_figure(results):
    """Create the grouped bar chart with AI range bars."""

    # Set up the plot with publication quality settings
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Colors matching Figure 3 palette
    HUMAN_COLOR = '#f59e0b'      # Amber for human (same as Figure 3)
    AI_BEST_COLOR = '#1e40af'    # Dark blue for lowest AI error (same as Figure 3 AT)
    AI_RANGE_COLOR = '#93c5fd'   # Light blue for AI range extension (same as Figure 3 W)

    # Define task order and clean labels (flag accuracy criteria only)
    task_order = ['affiliation', 'institution', 'domain', 'sanctions']
    task_labels = {
        'affiliation': 'Institutional\nAffiliation',
        'institution': 'Institution\nType',
        'domain': 'Email\nDomain',
        'sanctions': 'Sanctions'
    }

    # Prepare data for plotting
    x_pos = np.arange(len(task_order))
    width = 0.35

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

    # Calculate the range (difference between worst and best)
    ai_range = [worst - best for worst, best in zip(worst_errors, best_errors)]

    # Create the bars: Human baseline and AI stacked range
    # Human baseline bar
    bars_human = ax.bar(x_pos - width/2, human_errors, width,
                        label='Human Baseline (30 min)', color=HUMAN_COLOR, alpha=0.9)

    # AI bars: base is lowest error rate (best), stacked is the range to highest (worst)
    bars_ai_best = ax.bar(x_pos + width/2, best_errors, width,
                          label='Lowest Error from AI Screener', color=AI_BEST_COLOR, alpha=0.9)
    bars_ai_range = ax.bar(x_pos + width/2, ai_range, width, bottom=best_errors,
                           label='Highest Error from AI Screener', color=AI_RANGE_COLOR, alpha=0.9)

    # Customize the plot
    ax.set_xlabel('Flag Accuracy Criterion', fontsize=12, fontweight='bold')
    ax.set_ylabel('Error Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Human vs AI Error Rates by Flag Accuracy Criterion', fontsize=14, fontweight='bold', pad=20)

    # Set x-axis labels
    ax.set_xticks(x_pos)
    ax.set_xticklabels([task_labels[task] for task in task_order], rotation=45, ha='right')

    # Format y-axis
    max_error = max(max(human_errors), max(worst_errors))
    ax.set_ylim(0, max_error * 1.15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

    # Add value labels on bars
    # Human bars - single value
    for bar in bars_human:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

    # AI bars - show range (best - worst)
    for i, (bar_best, bar_range) in enumerate(zip(bars_ai_best, bars_ai_range)):
        best_val = best_errors[i]
        worst_val = worst_errors[i]
        total_height = worst_val

        # Show range label at top
        ax.text(bar_best.get_x() + bar_best.get_width()/2., total_height + 0.5,
               f'{best_val:.1f}-{worst_val:.1f}%',
               ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Add legend
    ax.legend(loc='upper left', fontsize=10)

    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Tight layout
    plt.tight_layout()

    return fig

def print_model_details(results):
    """Print which specific models were best/worst for each criterion."""
    print("\nBest and Worst AI Models by Flag Accuracy Criterion:")
    print("=" * 60)

    task_labels = {
        'affiliation': 'Institutional Affiliation',
        'institution': 'Institution Type',
        'domain': 'Email Domain',
        'sanctions': 'Sanctions'
    }

    for task in ['affiliation', 'institution', 'domain', 'sanctions']:
        if task in results:
            data = results[task]
            print(f"\n{task_labels[task].upper()}:")
            print(f"  Human Baseline (30min): {data['human_error']:.1f}% error rate (n={data['human_count']})")
            print(f"  Best AI Model: {data['best_model']} ({data['best_error']:.1f}% error rate, n={data['best_count']})")
            print(f"  Worst AI Model: {data['worst_model']} ({data['worst_error']:.1f}% error rate, n={data['worst_count']})")

def main():
    """Main function to generate the figure."""

    # Load and process data
    df = load_and_filter_data()
    df_tasks = map_metric_to_tasks(df)

    print(f"\nTask breakdown:")
    print(df_tasks['task'].value_counts())

    print(f"\nModel breakdown for relevant tasks:")
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
    output_dir = Path(__file__).parent.parent.parent / "paper" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save figure
    output_path = output_dir / 'figure2_human_vs_ai_comparison.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    print(f"\nFigure saved to: {output_path}")

    # Print caption
    print("\nSuggested Caption:")
    print("Error rates by flag accuracy criterion comparing human baseline (30 min) with best and worst performing AI models. Lower bars indicate better performance. The stacked blue bars show the range of AI performance from lowest to highest error rate.")

    plt.close(fig)  # Close the figure to prevent display issues

if __name__ == "__main__":
    main()