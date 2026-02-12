# Evaluating AI-Assisted Customer Verification for DNA Synthesis Screening

This repository contains the code and data for analyzing KYC (Know Your Customer) evaluation results comparing AI models against human experts on customer screening tasks.

See the full manuscript at `paper/paper_draft.md`.

## Reproducing the Paper

The processed datasets (`processed/tests.csv` and `processed/responses.csv`) are committed via Git LFS, so you can regenerate all figures and metrics without running the full data pipeline.

```bash
# 1. Clone and pull LFS data
git clone <repo-url>
git lfs pull

# 2. Install dependencies
uv sync

# 3. Regenerate all figures
make figures

# 4. Compute paper metrics (Tables 1, 2, inline statistics N1–N11)
make metrics
```

To re-run the full data pipeline from raw JSON (requires `OPENROUTER_API_KEY`; see `.env.example`):

```bash
uv run python scripts/generate_datasets.py
```

Use `--skip-latency` and `--skip-country` to skip API-dependent steps.

## Repository Structure

```
ai-kyc-results/
├── data/
│   ├── customers/                  # Customer profile datasets
│   │   ├── full_dataset.csv        # 134 customer profiles
│   │   └── human_baseline_subset.csv  # 40-customer subset for human comparison
│   ├── annotations/                # Human annotations and ground truth
│   │   ├── ground_truth_flags.json
│   │   ├── blind_gradings.json
│   │   ├── agreements.json
│   │   └── flag_error_comments.json
│   ├── raw_results/                # PromptFoo evaluation outputs (886MB, Git LFS)
│   │   └── *.json
│   └── token_pricing.yaml
│
├── processed/                      # Derived analysis datasets (Git LFS)
│   ├── tests.csv                   # One row per test assertion (~234k rows)
│   ├── responses.csv               # One row per model response (~55k rows)
│   └── blind_grading/              # Blind grading analysis
│
├── scripts/
│   ├── generate_datasets.py        # Main data processing pipeline
│   ├── merge_blind_gradings.py     # Merge blind grading results
│   ├── match_blind_gradings.py     # Match blind gradings to assertion-level results
│   └── figures/                    # Figure and metric generation scripts
│       ├── style.py                # Shared colors, model labels, ordering
│       ├── compute_paper_metrics.py  # Tables 1, 2, and inline stats N1–N11
│       ├── generate_figure2.py     # Figure 2: pass rates heatmap
│       ├── generate_figure2b.py    # Supplementary: pass rates by task
│       ├── generate_figure2c.py    # Supplementary: pass rates by customer type
│       ├── generate_figure3.py     # Figure 3: cost breakdown by model
│       ├── generate_figure4.py     # Figure 4: cost vs performance scatter
│       ├── generate_figure5.py     # Figure 5: flag errors by region and task
│       ├── generate_figure_human_vs_ai.py     # Supplementary: human vs AI comparison
│       ├── generate_figure_model_rankings.py  # Supplementary: model rankings
│       └── generate_figure_error_by_criterion.py  # Supplementary: error by criterion
│
├── paper/
│   ├── paper_draft.md              # Paper manuscript
│   ├── figures/                    # Main figures referenced in paper
│   └── supplementary/              # Appendix figures
│
├── prompts/                        # Prompt templates and test definitions
│   ├── simple.txt                  # Main screening prompt
│   ├── background_work.txt         # Background work search prompt
│   └── tests/                      # Evaluation test definitions
│       ├── claim_support.yaml
│       ├── source_reliability.yaml
│       └── work_relevance.yaml
│
├── archive/                        # Historical/one-time scripts
├── Makefile                        # One-command reproduction targets
└── pyproject.toml
```

## Data Files

### Customer Datasets

#### `data/customers/full_dataset.csv`
Contains 134 customer records for evaluation. Each row includes:
- `customer_info`: Full customer information text (Name, Institution, Email, etc.)
- `Name`: Customer name
- `Institution`: Affiliated institution
- `Type`: Customer category
- `Order`: Ordering/priority field

#### `data/customers/human_baseline_subset.csv`
A 40-customer subset used for human baseline comparison. Same schema as full_dataset.csv.

### Result Files

Located in `data/raw_results/`:

| File | Prompt Type | Dataset | Description |
|------|-------------|---------|-------------|
| `full_dataset_main.json` | main | Full (134) | Main evaluation prompt on full dataset |
| `full_dataset_background_work.json` | background_work | Full (134) | Background work prompt on full dataset |
| `human_baseline_subset_main.json` | main | Subset (40) | Main prompt with human baseline comparison |
| `human_baseline_subset_background_work.json` | background_work | Subset (40) | Background work with human baseline |

### Ground Truth

#### `data/annotations/ground_truth_flags.json`
Contains manually verified ground truth values for each customer's flags:
- `affiliation`: FLAG, NO FLAG, or UNDETERMINED
- `institution`: FLAG, NO FLAG, or UNDETERMINED
- `domain`: FLAG, NO FLAG, or UNDETERMINED
- `sanctions`: FLAG, NO FLAG, or UNDETERMINED

## Processed Datasets

### `processed/tests.csv`
One row per test (assertion) result. Used for accuracy/reliability analysis.

| Field | Description |
|-------|-------------|
| `eval_id` | Evaluation run identifier |
| `result_id` | Unique result identifier |
| `customer_name` | Customer name |
| `customer_institution` | Customer institution |
| `customer_type` | Customer category |
| `model_label` | Human-readable model name |
| `model_type` | `human_baseline`, `web_only`, or `all_tools` |
| `metric_name` | Test/assertion name |
| `test_category` | `flag_accuracy`, `claim_support`, `source_reliability`, or `work_relevance` |
| `original_pass` | Original pass/fail value from evaluation |
| `pass` | Corrected pass/fail value |
| `ground_truth_*` | Ground truth flag values |
| `extracted_flag` | Extracted flag value from model response |

### `processed/responses.csv`
One row per model response. Used for cost/latency analysis.

| Field | Description |
|-------|-------------|
| `eval_id` | Evaluation run identifier |
| `model_label` | Human-readable model name |
| `latency_ms` | Total latency in milliseconds |
| `total_cost` | Total cost in USD |
| `num_web_searches` | Number of web searches performed |
| `num_assertions_passed` | Number of passing assertions |

## Running the Scripts

### Generate Processed Datasets

```bash
uv run python scripts/generate_datasets.py
```

Options:
- `--skip-latency`: Use existing latencies from processed/responses.csv
- `--skip-country`: Use existing country classifications
- `--only-country`: Only update institution_country columns

Requires `OPENROUTER_API_KEY` environment variable for latency fetching (see `.env.example`).

### Generate Figures

```bash
make figures
```

Or individually:

```bash
uv run python scripts/figures/generate_figure2.py
uv run python scripts/figures/generate_figure3.py
# etc.
```

### Compute Paper Metrics

```bash
make metrics
```

## Data Processing and Corrections

### Flag Accuracy Corrections

The `pass` field in tests.csv has corrections applied:

1. **Ground Truth UNDETERMINED**: If ground truth is `UNDETERMINED`, any extracted value passes
2. **Exact Match Required**: If ground truth is determined, require exact match

### Human Baseline Corrections

1. **Empty Evidence Fail**: Claim support tests fail if no sources provided
2. **Sanctions Exact Match**: Sanctions claim support passes if the sanctions flag passes

## Test Categories

- **Flag Accuracy**: Whether the model correctly identified each flag
- **Claim Support**: Whether claims are supported by cited sources
- **Source Reliability**: Whether sources are reliable and authoritative
- **Work Relevance**: Whether background work is relevant to the customer

## Model Types

- `human_baseline`: Human expert responses
- `web_only`: Models using only web search tools
- `all_tools`: Models using full tool suite (web, ORCID, EPMC, sanctions screening)

## Dependencies

Managed via `uv`. Install with:

```bash
uv sync
```

See `pyproject.toml` for the full dependency list.
