"""
Shared plotting style configuration for KYC analysis.

Provides consistent colors, fonts, and styling across all plots.
"""

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)

# Data directory (processed CSVs)
DATA_DIR = Path(__file__).parent.parent / "processed"

# Color palette - consistent across all plots
COLORS = {
    # Model types
    "web_only": "#3498db",       # Blue
    "all_tools": "#2ecc71",      # Green
    "human_baseline": "#e74c3c", # Red

    # Test categories
    "work_relevance": "#9b59b6",      # Purple
    "source_reliability": "#1abc9c",  # Teal
    "claim_support": "#f39c12",       # Orange
    "flag_accuracy": "#e91e63",       # Pink

    # Pass/Fail
    "pass": "#27ae60",  # Green
    "fail": "#c0392b",  # Red

    # Source types
    "web": "#3498db",    # Blue
    "epmc": "#9b59b6",   # Purple
    "orcid": "#f39c12",  # Orange
    "screen": "#e74c3c", # Red

    # Prompt types
    "background_work": "#34495e",  # Dark gray
    "main": "#16a085",             # Teal

    # Customer types
    "Controlled Agent Academia": "#3498db",
    "Controlled Agent Industry": "#2ecc71",
    "General Life Science Customers": "#f39c12",
    "Sanctioned Institution Customers": "#e74c3c",
}

# Model display names (shorter for plots)
MODEL_LABELS = {
    "Gemini 2.5 Pro (All Tools)": "Gemini (AT)",
    "Gemini 2.5 Pro (Web)": "Gemini (W)",
    "GLM 4.6 (All Tools)": "GLM (AT)",
    "GLM 4.6 (Web)": "GLM (W)",
    "Claude Sonnet 4 (All Tools)": "Claude (AT)",
    "Claude Sonnet 4 (Web)": "Claude (W)",
    "Grok 4 (All Tools)": "Grok (AT)",
    "Grok 4 (Web)": "Grok (W)",
    "MiniMax M2 (All Tools)": "MiniMax (AT)",
    "MiniMax M2 (Web)": "MiniMax (W)",
    "Human Baseline (30min)": "Human (30m)",
    "Human Baseline (5min)": "Human (5m)",
}

# Model order for consistent plotting
MODEL_ORDER = [
    "Gemini 2.5 Pro (All Tools)",
    "Gemini 2.5 Pro (Web)",
    "GLM 4.6 (All Tools)",
    "GLM 4.6 (Web)",
    "Claude Sonnet 4 (All Tools)",
    "Claude Sonnet 4 (Web)",
    "Grok 4 (All Tools)",
    "Grok 4 (Web)",
    "MiniMax M2 (All Tools)",
    "MiniMax M2 (Web)",
    "Human Baseline (30min)",
    "Human Baseline (5min)",
]

# Category order
CATEGORY_ORDER = ["flag_accuracy", "claim_support", "source_reliability", "work_relevance"]

# Category display names
CATEGORY_LABELS = {
    "work_relevance": "Work Relevance",
    "source_reliability": "Source Reliability",
    "claim_support": "Claim Support",
    "flag_accuracy": "Flag Accuracy",
}


def setup_style():
    """Set up the matplotlib/seaborn style for all plots."""
    # Use seaborn style as base
    sns.set_theme(style="whitegrid", palette="deep")

    # Custom matplotlib parameters
    plt.rcParams.update({
        # Figure
        "figure.figsize": (10, 6),
        "figure.dpi": 150,
        "figure.facecolor": "white",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,

        # Font
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,

        # Axes
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",

        # Legend
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "0.8",
    })


def get_model_color(model_label: str) -> str:
    """Get color for a model based on its type."""
    if "Human" in model_label:
        return COLORS["human_baseline"]
    elif "(All Tools)" in model_label:
        return COLORS["all_tools"]
    else:
        return COLORS["web_only"]


def get_model_colors(model_labels: list) -> list:
    """Get colors for a list of models."""
    return [get_model_color(m) for m in model_labels]


def shorten_model_label(label: str) -> str:
    """Get shortened model label for plots."""
    return MODEL_LABELS.get(label, label)


def save_figure(fig, name: str, formats: list = None):
    """Save figure in multiple formats."""
    if formats is None:
        formats = ["png"]  # PNG only by default

    for fmt in formats:
        filepath = OUTPUT_DIR / f"{name}.{fmt}"
        fig.savefig(filepath)
        print(f"Saved: {filepath}")


def add_value_labels(ax, bars, fmt=".1f", suffix="%"):
    """Add value labels on top of bars."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:{fmt}}{suffix}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


# Initialize style when module is imported
setup_style()
