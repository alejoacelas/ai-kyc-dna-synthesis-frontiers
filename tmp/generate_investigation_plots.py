"""
Generate plots illustrating why all-tools models have lower work relevance scores.

Produces 4 figure pairs (full dataset + human baseline subset):
  A. Web search substitution: avg web searches by model, all-tools vs web-only
  B. Source composition: stacked bars showing web vs epmc sources per model
  C. Work relevance gap by customer type
  D. Per-model relevance gap decomposition (epmc-only vs epmc+web vs web-only)
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scripts.figures.style import (
    setup_style, COLORS, MODEL_LABELS, save_figure
)

setup_style()

tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

# Short model names for x-axis (base name only)
BASE_NAMES = {
    'anthropic/claude-sonnet-4': 'Claude',
    'google/gemini-2.5-pro': 'Gemini',
    'minimax/minimax-m2': 'MiniMax',
    'x-ai/grok-4': 'Grok',
    'z-ai/glm-4.6': 'GLM',
}
BASE_ORDER = ['Claude', 'Gemini', 'GLM', 'Grok', 'MiniMax']

CUSTOMER_TYPE_SHORT = {
    'Controlled Agent Academia': 'Academic\nSOC',
    'Controlled Agent Industry': 'Industry\nSOC',
    'General Life Science Customers': 'General\nLife Sci.',
    'Sanctioned Institution Customers': 'Sanctioned\nInstitution',
}
CUSTOMER_TYPE_ORDER = [
    'Controlled Agent Academia',
    'Controlled Agent Industry',
    'General Life Science Customers',
    'Sanctioned Institution Customers',
]

C_WEB = COLORS['web_only']      # Blue
C_AT = COLORS['all_tools']      # Green
C_EPMC = COLORS['epmc']         # Purple


def filter_data(df, hbs_only):
    """Filter to AI-only, optionally to human baseline subset."""
    out = df[~df.is_human_baseline].copy()
    if hbs_only:
        out = out[out.is_human_baseline_dataset == True]
    return out


def plot_A_web_search_substitution(hbs_only=False):
    """
    Figure A: Average web searches per background_work response,
    all-tools vs web-only, per model.
    """
    bg = filter_data(responses[responses.prompt_type == 'background_work'], hbs_only)
    bg['base_model'] = bg['model_name'].map(BASE_NAMES)

    grouped = bg.groupby(['base_model', 'model_type'])['num_web_searches'].mean().unstack('model_type')
    grouped = grouped.reindex(BASE_ORDER)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(BASE_ORDER))
    w = 0.35

    bars_wo = ax.bar(x - w/2, grouped['web_only'], w, color=C_WEB, label='Web-only', edgecolor='white', linewidth=0.5)
    bars_at = ax.bar(x + w/2, grouped['all_tools'], w, color=C_AT, label='All tools', edgecolor='white', linewidth=0.5)

    # Add value labels
    for bars in [bars_wo, bars_at]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}', xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 4), textcoords='offset points',
                        ha='center', va='bottom', fontsize=9)

    # Add reduction % annotations
    for i, model in enumerate(BASE_ORDER):
        wo_val = grouped.loc[model, 'web_only']
        at_val = grouped.loc[model, 'all_tools']
        reduction = (1 - at_val / wo_val) * 100 if wo_val > 0 else 0
        ax.annotate(f'{reduction:.0f}% fewer',
                    xy=(x[i] + w/2, at_val),
                    xytext=(20, 14), textcoords='offset points',
                    ha='center', va='bottom', fontsize=8, color='#555',
                    arrowprops=dict(arrowstyle='->', color='#999', lw=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(BASE_ORDER)
    ax.set_ylabel('Avg. web searches per response')
    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    ax.set_title(f'Web search substitution in background work task{subset_label}')
    ax.legend(loc='upper right')
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)

    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_A_web_search_substitution{suffix}.png', dpi=200)
    print(f'Saved tmp/plot_A_web_search_substitution{suffix}.png')
    plt.close(fig)


def plot_B_source_composition(hbs_only=False):
    """
    Figure B: Stacked bar chart of source types (web vs epmc) for background_work,
    per model, comparing all-tools vs web-only.
    """
    bg = filter_data(responses[responses.prompt_type == 'background_work'], hbs_only)
    bg['base_model'] = bg['model_name'].map(BASE_NAMES)

    grouped = bg.groupby(['base_model', 'model_type'])[
        ['num_web_sources', 'num_epmc_sources']
    ].mean()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    x = np.arange(len(BASE_ORDER))
    w = 0.6

    for ax, mtype, title in zip(axes, ['web_only', 'all_tools'], ['Web-only', 'All tools']):
        data = grouped.loc[(slice(None), mtype), :].droplevel('model_type').reindex(BASE_ORDER)

        bars_web = ax.bar(x, data['num_web_sources'], w, color=C_WEB, label='Web sources', edgecolor='white', linewidth=0.5)
        bars_epmc = ax.bar(x, data['num_epmc_sources'], w, bottom=data['num_web_sources'],
                           color=C_EPMC, label='Europe PMC sources', edgecolor='white', linewidth=0.5)

        # Total label on top
        for i in range(len(BASE_ORDER)):
            total = data.iloc[i].sum()
            ax.text(x[i], total + 0.5, f'{total:.0f}', ha='center', va='bottom', fontsize=9, color='#555')

        ax.set_xticks(x)
        ax.set_xticklabels(BASE_ORDER)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_ylabel('Avg. sources per response' if mtype == 'web_only' else '')
        ax.legend(loc='upper right')

    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    fig.suptitle(f'Source composition for background work task{subset_label}',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_B_source_composition{suffix}.png', dpi=200, bbox_inches='tight')
    print(f'Saved tmp/plot_B_source_composition{suffix}.png')
    plt.close(fig)


def plot_C_relevance_by_customer_type(hbs_only=False):
    """
    Figure C: Work relevance pass rate by customer type, all-tools vs web-only.
    Highlights the industry gap.
    """
    wr = filter_data(tests[tests.metric_name == 'WORK-RELEVANCE'], hbs_only)

    grouped = wr.groupby(['customer_type', 'model_type'])['pass'].mean().unstack('model_type')
    grouped = grouped.reindex(CUSTOMER_TYPE_ORDER)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(CUSTOMER_TYPE_ORDER))
    w = 0.35

    bars_wo = ax.bar(x - w/2, grouped['web_only'] * 100, w, color=C_WEB, label='Web-only', edgecolor='white', linewidth=0.5)
    bars_at = ax.bar(x + w/2, grouped['all_tools'] * 100, w, color=C_AT, label='All tools', edgecolor='white', linewidth=0.5)

    # Value labels
    for bars in [bars_wo, bars_at]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=9)

    # Highlight the industry gap
    gap_idx = CUSTOMER_TYPE_ORDER.index('Controlled Agent Industry')
    wo_val = grouped.loc['Controlled Agent Industry', 'web_only'] * 100
    at_val = grouped.loc['Controlled Agent Industry', 'all_tools'] * 100
    gap = at_val - wo_val

    # Draw bracket between the two industry bars
    mid_x = x[gap_idx]
    ax.annotate('', xy=(mid_x - w/2, at_val - 1), xytext=(mid_x + w/2 + w, at_val - 1),
                arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=1.5))
    ax.text(mid_x + w/2 + w/2, at_val - 4, f'{gap:+.1f}pp',
            ha='center', va='top', fontsize=11, fontweight='bold', color='#c0392b')

    labels = [CUSTOMER_TYPE_SHORT[ct] for ct in CUSTOMER_TYPE_ORDER]
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Work relevance pass rate (%)')
    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    ax.set_title(f'Work relevance by customer type{subset_label}')
    ax.legend(loc='lower right')
    ax.set_ylim(0, 105)

    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_C_relevance_by_customer_type{suffix}.png', dpi=200)
    print(f'Saved tmp/plot_C_relevance_by_customer_type{suffix}.png')
    plt.close(fig)


def plot_D_per_model_decomposition(hbs_only=False):
    """
    Figure D: Per-model work relevance pass rate, split by:
      - Web-only condition
      - All-tools with web search (epmc + web)
      - All-tools without web search (epmc only)
    Shows that models relying solely on epmc sometimes match web-only,
    but the "epmc + web" cases (fallback) actually perform worst.
    """
    wr = filter_data(tests[tests.metric_name == 'WORK-RELEVANCE'], hbs_only)
    bg_resp = filter_data(responses[responses.prompt_type == 'background_work'], hbs_only)

    # Merge web search info into work relevance tests
    at_info = bg_resp[bg_resp.model_type == 'all_tools'][['result_id', 'num_web_searches']].copy()
    at_info.columns = ['result_id', 'r_ws']

    wr_at = wr[wr.model_type == 'all_tools'].merge(at_info, on='result_id', how='left')
    wr_at['search_mode'] = np.where(wr_at['r_ws'] > 0, 'All tools\n(with web search)', 'All tools\n(EPMC only)')
    wr_wo = wr[wr.model_type == 'web_only'].copy()
    wr_wo['search_mode'] = 'Web-only'

    combined = pd.concat([wr_wo, wr_at])
    combined['base_model'] = combined['model_name'].map(BASE_NAMES)

    grouped = combined.groupby(['base_model', 'search_mode'])['pass'].agg(['mean', 'count']).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5.5))

    modes = ['Web-only', 'All tools\n(EPMC only)', 'All tools\n(with web search)']
    mode_colors = [C_WEB, C_EPMC, '#27ae60']  # blue, purple, darker green
    x = np.arange(len(BASE_ORDER))
    w = 0.25

    for j, (mode, color) in enumerate(zip(modes, mode_colors)):
        vals = []
        counts = []
        for model in BASE_ORDER:
            row = grouped[(grouped.base_model == model) & (grouped.search_mode == mode)]
            vals.append(row['mean'].values[0] * 100 if len(row) > 0 else 0)
            counts.append(int(row['count'].values[0]) if len(row) > 0 else 0)
        bars = ax.bar(x + (j - 1) * w, vals, w, color=color, label=mode, edgecolor='white', linewidth=0.5)

        for i, (bar, v, n) in enumerate(zip(bars, vals, counts)):
            ax.annotate(f'{v:.0f}%', xy=(bar.get_x() + bar.get_width()/2, v),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8)
            # Show n below bar
            ax.text(bar.get_x() + bar.get_width()/2, 2, f'n={n}',
                    ha='center', va='bottom', fontsize=6.5, color='#777', rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels(BASE_ORDER)
    ax.set_ylabel('Work relevance pass rate (%)')
    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    ax.set_title(f'Work relevance by model and search mode{subset_label}')
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(0, 108)

    # Add annotation explaining the pattern
    ax.annotate('Models that fall back to web search\nin all-tools often searched less\nthoroughly than in web-only mode',
                xy=(0.98, 0.55), xycoords='axes fraction',
                fontsize=8.5, ha='right', va='top', color='#555',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#f9f9f9', edgecolor='#ddd'))

    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_D_per_model_decomposition{suffix}.png', dpi=200)
    print(f'Saved tmp/plot_D_per_model_decomposition{suffix}.png')
    plt.close(fig)


# Generate all plots in both versions
for hbs in [False, True]:
    label = "human baseline subset" if hbs else "full dataset"
    print(f"\n--- Generating plots for {label} ---")
    plot_A_web_search_substitution(hbs_only=hbs)
    plot_B_source_composition(hbs_only=hbs)
    plot_C_relevance_by_customer_type(hbs_only=hbs)
    plot_D_per_model_decomposition(hbs_only=hbs)

print("\nDone! All plots saved in tmp/")
