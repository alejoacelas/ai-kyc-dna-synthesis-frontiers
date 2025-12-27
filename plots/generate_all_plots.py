#!/usr/bin/env python3
"""
Generate all analysis plots for KYC evaluation results.

This is the main entry point for generating all figures.
Run from the plots directory:
    python generate_all_plots.py
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from style import OUTPUT_DIR


def main():
    """Run all plot generation scripts."""
    print("=" * 60)
    print("KYC ANALYSIS PLOTS GENERATOR")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print()

    # Import and run each module
    print("1. Generating Pass Rate Plots...")
    print("-" * 40)
    import plot_pass_rates
    plot_pass_rates.main()
    print()

    print("2. Generating Cost & Latency Plots...")
    print("-" * 40)
    import plot_cost_latency
    plot_cost_latency.main()
    print()

    print("3. Generating Source Usage Plots...")
    print("-" * 40)
    import plot_sources
    plot_sources.main()
    print()

    print("4. Generating Model Comparison Plots...")
    print("-" * 40)
    import plot_model_comparison
    plot_model_comparison.main()
    print()

    print("5. Generating Advanced Analysis Plots...")
    print("-" * 40)
    import plot_advanced_analysis
    plot_advanced_analysis.main()
    print()

    # Summary
    print("=" * 60)
    print("ALL PLOTS GENERATED")
    print("=" * 60)

    # List generated files
    figures = list(OUTPUT_DIR.glob("*.png"))
    print(f"\nGenerated {len(figures)} figures:")
    for fig in sorted(figures):
        print(f"  - {fig.name}")

    print(f"\nFigures saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
