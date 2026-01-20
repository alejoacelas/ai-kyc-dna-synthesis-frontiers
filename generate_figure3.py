#!/usr/bin/env python3
"""
Generate Figure 3: Model rankings horizontal bar chart.

Shows overall pass rates by model sorted from lowest to highest performance.
Color coded by model configuration type (web-only, all-tools, human baseline).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

# Add plots directory to path for style imports
sys.path.append(str(Path(__file__).parent / "plots"))
from style import COLORS, MODEL_LABELS, get_model_color, setup_style

def load_and_filter_data():
    """Load test data and filter for human baseline dataset."""
    data_path = Path(__file__).parent / "processed" / "tests.csv"
    print(f"Loading data from: {data_path}")

    # Read the CSV file
    df = pd.read_csv(data_path)
    print(f"Total rows: {len(df):,}")

    # Filter for human baseline dataset
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()
    print(f"Rows after human baseline filter: {len(df_filtered):,}")

    print("Available models:", df_filtered['model_label'].unique())
    print("Available model types:", df_filtered['model_type'].unique())

    return df_filtered

def calculate_overall_pass_rates(df):
    """Calculate overall pass rate for each model across all test categories."""
    print("\nCalculating overall pass rates...")

    # Group by model and calculate pass rate
    model_stats = df.groupby(['model_label', 'model_type']).agg({
        'pass': ['sum', 'count']
    }).reset_index()

    # Flatten column names
    model_stats.columns = ['model_label', 'model_type', 'pass_count', 'total_count']

    # Calculate pass rate as percentage
    model_stats['pass_rate'] = (model_stats['pass_count'] / model_stats['total_count']) * 100

    # Sort by pass rate (ascending - worst to best)
    model_stats = model_stats.sort_values('pass_rate', ascending=True)

    print("Pass rates by model:")
    for _, row in model_stats.iterrows():
        print(f"  {row['model_label']}: {row['pass_rate']:.1f}% ({row['pass_count']}/{row['total_count']})")

    return model_stats

def create_figure(model_stats):
    """Create the horizontal bar chart."""
    setup_style()

    # Custom colors for better AI vs Human distinction
    # AI models: shades of blue (tech/digital feel) - more distinct shades
    # Human: warm orange/amber (organic/human feel)
    FIGURE3_COLORS = {
        'all_tools': '#1e40af',      # Dark blue for AI with all tools
        'web_only': '#93c5fd',       # Much lighter blue for AI web-only
        'human_baseline': '#f59e0b', # Amber/orange for human
    }

    # Create figure with appropriate size for horizontal bars
    fig, ax = plt.subplots(figsize=(12, 8))

    # Get colors for each model based on model type
    def get_figure3_color(model_type):
        return FIGURE3_COLORS.get(model_type, '#6b7280')

    colors = [get_figure3_color(mt) for mt in model_stats['model_type']]

    # Create horizontal bar chart
    bars = ax.barh(range(len(model_stats)), model_stats['pass_rate'], color=colors, alpha=0.9)

    # Customize y-axis (model labels)
    ax.set_yticks(range(len(model_stats)))
    # Use shortened labels for better readability
    short_labels = [MODEL_LABELS.get(label, label) for label in model_stats['model_label']]
    ax.set_yticklabels(short_labels)

    # Customize x-axis (pass rate)
    ax.set_xlabel('Pass Rate (%)', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 10))

    # Add title
    ax.set_title('Average Pass Rate by Screener Across All Tasks',
                fontsize=14, fontweight='bold', pad=20)

    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, model_stats['pass_rate'])):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{rate:.1f}%', va='center', fontsize=10, fontweight='bold')

    # Create legend with intuitive AI vs Human grouping
    legend_elements = []
    legend_labels = []

    # Add legend entries for each model type with new colors
    for model_type, color, label in [
        ('all_tools', FIGURE3_COLORS['all_tools'], 'AI - All Tools (AT)'),
        ('web_only', FIGURE3_COLORS['web_only'], 'AI - Web Only (W)'),
        ('human_baseline', FIGURE3_COLORS['human_baseline'], 'Human Baseline'),
    ]:
        if model_type in model_stats['model_type'].values:
            legend_elements.append(plt.Rectangle((0,0),1,1, fc=color, alpha=0.9))
            legend_labels.append(label)

    ax.legend(legend_elements, legend_labels,
             loc='lower right', frameon=True, framealpha=0.9)

    # Improve layout
    plt.tight_layout()

    return fig

def main():
    """Main function to generate Figure 3."""
    print("Generating Figure 3: Model rankings horizontal bar chart")
    print("=" * 60)

    # Load and filter data
    df = load_and_filter_data()

    # Calculate overall pass rates
    model_stats = calculate_overall_pass_rates(df)

    # Create the figure
    fig = create_figure(model_stats)

    # Save the figure
    output_path = Path(__file__).parent / "paper" / "figures" / "figure3_model_rankings.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    # Also save a copy in the plots directory for consistency
    plots_path = Path(__file__).parent / "plots" / "figures" / "figure3_model_rankings.png"
    plots_path.parent.mkdir(exist_ok=True)
    fig.savefig(plots_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Copy saved to: {plots_path}")

    print("\nCaption:")
    print("Overall pass rates by model sorted from lowest to highest performance.")
    print("Color coding shows model configuration: web-only (blue), all-tools (green),")
    print("and human baseline (red). Tool-augmented configurations show consistent")
    print("but modest improvements over web-only versions.")

    plt.show()

if __name__ == "__main__":
    main()