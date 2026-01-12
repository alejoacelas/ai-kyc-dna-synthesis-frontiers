#!/usr/bin/env python3
"""
Generate Figure 6: Geographic breakdown by customer region
Shows pass rates by customer region and test category for AI models on human baseline dataset
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def generate_figure6():
    # Read the data
    df = pd.read_csv('processed/tests.csv')

    # Apply filters according to requirements
    # 1. Use human baseline subset only
    df_filtered = df[df['is_human_baseline_dataset'] == True].copy()

    # 2. Only include AI models (exclude human baselines)
    df_filtered = df_filtered[df_filtered['is_human_baseline'] == False].copy()

    print(f"Total records after filtering: {len(df_filtered)}")
    print(f"Records by region: \n{df_filtered['institution_country'].value_counts()}")
    print(f"Records by test category: \n{df_filtered['test_category'].value_counts()}")

    # Calculate average pass rate by institution_country and test_category
    pass_rates = df_filtered.groupby(['institution_country', 'test_category'])['pass'].mean() * 100
    pass_rates_df = pass_rates.reset_index()
    pass_rates_df.columns = ['region', 'test_category', 'pass_rate']

    # Map regions according to requirements (already correctly named in data)
    region_mapping = {
        'USA': 'USA',
        'Europe + Australia': 'Europe + Australia',
        'China': 'China',
        'Others': 'Others'
    }

    # Order regions and test categories
    region_order = ['USA', 'Europe + Australia', 'China', 'Others']
    test_category_order = ['flag_accuracy', 'claim_support', 'source_reliability', 'work_relevance']

    # Pivot data for plotting
    pivot_data = pass_rates_df.pivot(index='region', columns='test_category', values='pass_rate')
    pivot_data = pivot_data.reindex(region_order)[test_category_order]

    print("\nPass rates by region and test category:")
    print(pivot_data.round(1))

    # Set up the plot with high DPI
    plt.figure(figsize=(12, 8), dpi=300)

    # Define colors for each test category
    colors = ['#2E8B57', '#4682B4', '#CD853F', '#9932CC']  # Sea green, steel blue, peru, purple

    # Set up positions for grouped bars
    x = np.arange(len(region_order))
    width = 0.2

    # Create bars for each test category
    for i, test_cat in enumerate(test_category_order):
        offset = (i - 1.5) * width
        values = [pivot_data.loc[region, test_cat] if region in pivot_data.index else 0
                 for region in region_order]

        bars = plt.bar(x + offset, values, width, label=test_cat.replace('_', ' ').title(),
                      color=colors[i], alpha=0.8, edgecolor='black', linewidth=0.5)

        # Annotate bars with exact percentage values
        for j, (bar, value) in enumerate(zip(bars, values)):
            if value > 0:  # Only annotate if there's data
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{value:.1f}%', ha='center', va='bottom', fontsize=9,
                        fontweight='bold')

    # Customize the plot
    plt.xlabel('Customer Region', fontsize=14, fontweight='bold')
    plt.ylabel('Pass Rate (%)', fontsize=14, fontweight='bold')
    plt.title('Pass Rates by Customer Region and Test Category\n(AI Models on Human Baseline Dataset)',
              fontsize=16, fontweight='bold', pad=20)

    # Set y-axis from 0 to 105% to give room for bar labels
    plt.ylim(0, 105)

    # Set x-axis labels
    plt.xticks(x, region_order, fontsize=12)
    plt.yticks(fontsize=12)

    # Add legend (bottom right corner)
    plt.legend(title='Test Category', title_fontsize=12, fontsize=11,
              loc='lower right', frameon=True, fancybox=True, shadow=True)

    # Add grid for better readability
    plt.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)

    # Remove top spine to avoid overlap with bar number annotations
    ax = plt.gca()
    ax.spines['top'].set_visible(False)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the figure
    output_path = 'paper/figures/figure6_geographic_breakdown.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {output_path}")

    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    # Overall performance by region
    overall_by_region = pivot_data.mean(axis=1).sort_values(ascending=False)
    print(f"\nOverall average pass rates by region:")
    for region, rate in overall_by_region.items():
        print(f"  {region}: {rate:.1f}%")

    best_region = overall_by_region.index[0]
    worst_region = overall_by_region.index[-1]
    print(f"\nBest performing region: {best_region} ({overall_by_region[best_region]:.1f}%)")
    print(f"Worst performing region: {worst_region} ({overall_by_region[worst_region]:.1f}%)")

    # Performance range
    performance_range = overall_by_region.max() - overall_by_region.min()
    print(f"Performance range across regions: {performance_range:.1f} percentage points")

    # Test category patterns
    print(f"\nPerformance by test category (averaged across all regions):")
    overall_by_category = pivot_data.mean(axis=0).sort_values(ascending=False)
    for category, rate in overall_by_category.items():
        print(f"  {category.replace('_', ' ').title()}: {rate:.1f}%")

    # European vs Chinese comparison
    if 'Europe + Australia' in pivot_data.index and 'China' in pivot_data.index:
        europe_avg = pivot_data.loc['Europe + Australia'].mean()
        china_avg = pivot_data.loc['China'].mean()
        difference = europe_avg - china_avg
        print(f"\nEuropean vs Chinese customer performance:")
        print(f"  Europe + Australia average: {europe_avg:.1f}%")
        print(f"  China average: {china_avg:.1f}%")
        print(f"  Difference: {difference:.1f} percentage points in favor of Europe + Australia")

    # Category-specific regional patterns
    print(f"\nBest performing region by test category:")
    for category in test_category_order:
        if category in pivot_data.columns:
            best_region_for_category = pivot_data[category].idxmax()
            best_rate = pivot_data[category].max()
            print(f"  {category.replace('_', ' ').title()}: {best_region_for_category} ({best_rate:.1f}%)")

    plt.show()

    return pivot_data

if __name__ == "__main__":
    result = generate_figure6()