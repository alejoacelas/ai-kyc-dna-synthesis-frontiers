"""
Generate plots using source-type-in-passing-works data to strengthen
the causal story about why all-tools models have lower work relevance.

Plot E: Share of passing works by source type, per customer type
Plot F: For industry customers, per-model breakdown of passing source types
        alongside pass rate gap
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scripts.figures.style import setup_style, COLORS

setup_style()

df = pd.read_csv('tmp/work_relevance_source_types.csv')
tests = pd.read_csv('processed/tests.csv')
responses = pd.read_csv('processed/responses.csv')

C_WEB = COLORS['web_only']   # Blue
C_EPMC = COLORS['epmc']      # Purple
C_AT = COLORS['all_tools']   # Green
C_UNK = '#bdc3c7'            # Light gray

CUSTOMER_TYPE_SHORT = {
    'Controlled Agent Academia': 'Academic SOC',
    'Controlled Agent Industry': 'Industry SOC',
    'General Life Science Customers': 'General Life Sci.',
    'Sanctioned Institution Customers': 'Sanctioned Inst.',
}
CUSTOMER_TYPE_ORDER = [
    'Controlled Agent Academia',
    'Controlled Agent Industry',
    'General Life Science Customers',
    'Sanctioned Institution Customers',
]

BASE_NAMES = {
    'anthropic/claude-sonnet-4': 'Claude',
    'google/gemini-2.5-pro': 'Gemini',
    'minimax/minimax-m2': 'MiniMax',
    'x-ai/grok-4': 'Grok',
    'z-ai/glm-4.6': 'GLM',
}
BASE_ORDER = ['Claude', 'Gemini', 'GLM', 'Grok', 'MiniMax']


def filter_hbs(d, hbs_only):
    if hbs_only:
        return d[d.is_human_baseline_dataset == True]
    return d


def plot_E_source_type_share(hbs_only=False):
    """
    Stacked bar: share of passing works from web vs epmc vs unknown,
    by customer type, all-tools vs web-only side by side.
    """
    data = filter_hbs(df, hbs_only)
    passing = data[data.wr_pass == True]

    fig, ax = plt.subplots(figsize=(10, 5.5))

    x = np.arange(len(CUSTOMER_TYPE_ORDER))
    w = 0.35
    offsets = {'all_tools': w/2, 'web_only': -w/2}
    mtype_labels = {'web_only': 'Web-only', 'all_tools': 'All tools'}

    for mtype, offset in offsets.items():
        web_shares = []
        epmc_shares = []
        unk_shares = []
        for ctype in CUSTOMER_TYPE_ORDER:
            sub = passing[(passing.model_type == mtype) & (passing.customer_type == ctype)]
            total = sub.n_pass_total.sum()
            if total > 0:
                web_shares.append(sub.n_pass_web.sum() / total * 100)
                epmc_shares.append(sub.n_pass_epmc.sum() / total * 100)
                unk_shares.append((sub.n_pass_unknown.sum() + sub.n_pass_orcid.sum()) / total * 100)
            else:
                web_shares.append(0)
                epmc_shares.append(0)
                unk_shares.append(0)

        b1 = ax.bar(x + offset, web_shares, w, color=C_WEB, edgecolor='white', linewidth=0.5)
        b2 = ax.bar(x + offset, epmc_shares, w, bottom=web_shares, color=C_EPMC, edgecolor='white', linewidth=0.5)
        bottoms = [a + b for a, b in zip(web_shares, epmc_shares)]
        b3 = ax.bar(x + offset, unk_shares, w, bottom=bottoms, color=C_UNK, edgecolor='white', linewidth=0.5)

        # Label the condition
        for i in range(len(CUSTOMER_TYPE_ORDER)):
            ax.text(x[i] + offset, -4, mtype_labels[mtype],
                    ha='center', va='top', fontsize=7.5, color='#555')

    # Custom legend
    patches = [
        mpatches.Patch(color=C_WEB, label='Web sources'),
        mpatches.Patch(color=C_EPMC, label='Europe PMC sources'),
        mpatches.Patch(color=C_UNK, label='Unknown/other'),
    ]
    ax.legend(handles=patches, loc='upper right', fontsize=9)

    labels = [CUSTOMER_TYPE_SHORT[ct] for ct in CUSTOMER_TYPE_ORDER]
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Share of relevant works (%)')
    ax.set_ylim(-8, 108)
    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    ax.set_title(f'Source types of works passing relevance threshold{subset_label}')

    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_E_source_type_share{suffix}.png', dpi=200)
    print(f'Saved tmp/plot_E_source_type_share{suffix}.png')
    plt.close(fig)


def plot_F_industry_mechanism(hbs_only=False):
    """
    Combined figure for industry customers showing the full causal chain:
    Panel 1: Web searches (all-tools vs web-only) per model
    Panel 2: Source type share of passing works per model
    Panel 3: Work relevance pass rate per model
    """
    data = filter_hbs(df, hbs_only)
    resp_bg = responses[responses.prompt_type == 'background_work'].copy()
    resp_bg = resp_bg[~resp_bg.is_human_baseline]
    if hbs_only:
        resp_bg = resp_bg[resp_bg.is_human_baseline_dataset == True]

    industry_df = data[data.customer_type == 'Controlled Agent Industry']
    industry_resp = resp_bg[resp_bg.customer_type == 'Controlled Agent Industry']

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    industry_df = industry_df.copy()
    industry_df['base_model'] = industry_df['model_name'].map(BASE_NAMES)
    industry_resp = industry_resp.copy()
    industry_resp['base_model'] = industry_resp['model_name'].map(BASE_NAMES)

    x = np.arange(len(BASE_ORDER))
    w = 0.35

    # --- Panel 1: Web searches ---
    ax = axes[0]
    for mtype, offset, color, label in [
        ('web_only', -w/2, C_WEB, 'Web-only'),
        ('all_tools', w/2, C_AT, 'All tools'),
    ]:
        vals = []
        for model in BASE_ORDER:
            sub = industry_resp[(industry_resp.base_model == model) & (industry_resp.model_type == mtype)]
            vals.append(sub.num_web_searches.mean() if len(sub) > 0 else 0)
        bars = ax.bar(x + offset, vals, w, color=color, label=label, edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.annotate(f'{v:.1f}', xy=(bar.get_x() + bar.get_width()/2, v),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(BASE_ORDER, fontsize=9)
    ax.set_ylabel('Avg. web searches')
    ax.set_title('1. Web search usage', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8)

    # --- Panel 2: Source type share of passing works ---
    ax = axes[1]
    for mtype, offset, label in [('web_only', -w/2, 'Web-only'), ('all_tools', w/2, 'All tools')]:
        web_pcts = []
        epmc_pcts = []
        other_pcts = []
        for model in BASE_ORDER:
            sub = industry_df[(industry_df.base_model == model) & (industry_df.model_type == mtype) & (industry_df.wr_pass == True)]
            total = sub.n_pass_total.sum()
            if total > 0:
                web_pcts.append(sub.n_pass_web.sum() / total * 100)
                epmc_pcts.append(sub.n_pass_epmc.sum() / total * 100)
                other_pcts.append(100 - web_pcts[-1] - epmc_pcts[-1])
            else:
                web_pcts.append(0)
                epmc_pcts.append(0)
                other_pcts.append(0)

        ax.bar(x + offset, web_pcts, w, color=C_WEB, edgecolor='white', linewidth=0.5)
        ax.bar(x + offset, epmc_pcts, w, bottom=web_pcts, color=C_EPMC, edgecolor='white', linewidth=0.5)
        bottoms = [a + b for a, b in zip(web_pcts, epmc_pcts)]
        ax.bar(x + offset, other_pcts, w, bottom=bottoms, color=C_UNK, edgecolor='white', linewidth=0.5)

        # Condition label
        for i in range(len(BASE_ORDER)):
            ax.text(x[i] + offset, -5, label, ha='center', va='top', fontsize=6.5, color='#555')

    patches = [
        mpatches.Patch(color=C_WEB, label='Web'),
        mpatches.Patch(color=C_EPMC, label='EPMC'),
        mpatches.Patch(color=C_UNK, label='Other'),
    ]
    ax.legend(handles=patches, fontsize=8, loc='upper right')
    ax.set_xticks(x)
    ax.set_xticklabels(BASE_ORDER, fontsize=9)
    ax.set_ylabel('Share of relevant works (%)')
    ax.set_title('2. Source types of relevant works', fontsize=12, fontweight='bold')
    ax.set_ylim(-8, 108)

    # --- Panel 3: Pass rate ---
    ax = axes[2]
    for mtype, offset, color, label in [
        ('web_only', -w/2, C_WEB, 'Web-only'),
        ('all_tools', w/2, C_AT, 'All tools'),
    ]:
        vals = []
        for model in BASE_ORDER:
            sub = industry_df[(industry_df.base_model == model) & (industry_df.model_type == mtype)]
            vals.append(sub.wr_pass.mean() * 100 if len(sub) > 0 else 0)
        bars = ax.bar(x + offset, vals, w, color=color, label=label, edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.annotate(f'{v:.0f}%', xy=(bar.get_x() + bar.get_width()/2, v),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(BASE_ORDER, fontsize=9)
    ax.set_ylabel('Work relevance pass rate (%)')
    ax.set_title('3. Work relevance pass rate', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 105)

    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    fig.suptitle(f'Industry customers: causal chain from web search to relevance{subset_label}',
                 fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_F_industry_mechanism{suffix}.png', dpi=200, bbox_inches='tight')
    print(f'Saved tmp/plot_F_industry_mechanism{suffix}.png')
    plt.close(fig)


def plot_G_epmc_vs_web_relevance_rate(hbs_only=False):
    """
    For all-tools: fraction of sources that pass relevance threshold,
    broken down by source type (web vs epmc).
    Shows whether epmc sources are inherently less relevant for certain customer types.
    """
    data = filter_hbs(df, hbs_only)
    at = data[data.model_type == 'all_tools']

    fig, ax = plt.subplots(figsize=(9, 5))

    x = np.arange(len(CUSTOMER_TYPE_ORDER))
    w = 0.35

    web_rates = []
    epmc_rates = []
    for ctype in CUSTOMER_TYPE_ORDER:
        sub = at[at.customer_type == ctype]
        total_web = sub.n_pass_web.sum() + sub.n_fail_web.sum()
        total_epmc = sub.n_pass_epmc.sum() + sub.n_fail_epmc.sum()
        web_rates.append(sub.n_pass_web.sum() / total_web * 100 if total_web > 0 else 0)
        epmc_rates.append(sub.n_pass_epmc.sum() / total_epmc * 100 if total_epmc > 0 else 0)

    bars_web = ax.bar(x - w/2, web_rates, w, color=C_WEB, label='Web sources', edgecolor='white', linewidth=0.5)
    bars_epmc = ax.bar(x + w/2, epmc_rates, w, color=C_EPMC, label='EPMC sources', edgecolor='white', linewidth=0.5)

    for bars in [bars_web, bars_epmc]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(f'{h:.0f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                            xytext=(0, 3), textcoords='offset points',
                            ha='center', va='bottom', fontsize=9)

    labels = [CUSTOMER_TYPE_SHORT[ct] for ct in CUSTOMER_TYPE_ORDER]
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('% of cited sources passing relevance threshold')
    subset_label = ' (human baseline subset)' if hbs_only else ' (full dataset)'
    ax.set_title(f'Relevance rate of cited sources by type (all-tools condition){subset_label}')
    ax.legend()
    ax.set_ylim(0, 105)

    fig.tight_layout()
    suffix = '_hbs' if hbs_only else '_full'
    fig.savefig(f'tmp/plot_G_source_relevance_rate{suffix}.png', dpi=200)
    print(f'Saved tmp/plot_G_source_relevance_rate{suffix}.png')
    plt.close(fig)


# Generate all
for hbs in [False, True]:
    label = "human baseline subset" if hbs else "full dataset"
    print(f"\n--- Generating plots for {label} ---")
    plot_E_source_type_share(hbs_only=hbs)
    plot_F_industry_mechanism(hbs_only=hbs)
    plot_G_epmc_vs_web_relevance_rate(hbs_only=hbs)

print("\nDone!")
