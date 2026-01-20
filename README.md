# KYC Evaluation Analysis

This repository contains all the code and data for analyzing the KYC (Know Your Customer) evaluation results comparing AI models against human experts on customer screening tasks.

## Quick Start

To get context on the results:

- See the paper draft at `paper/paper_draft.md`
- Run `cd viewer && npm install && npm run dev` to browse the raw responses
- Read the prompts at `prompts/`
- Explore the processed datasets at `processed/`

Because the JSON results are large files (886MB total), you may need to run `git lfs pull` to download them.

## Repository Structure

```
ai-kyc-results/
├── data/
│   ├── customers/               # Customer profile datasets
│   │   ├── full_dataset.csv     # 134 customer profiles
│   │   └── human_baseline_subset.csv  # 40-customer subset for human comparison
│   ├── annotations/             # Human annotations and ground truth
│   │   ├── ground_truth_flags.json
│   │   ├── blind_gradings.json
│   │   └── agreements.json
│   ├── raw_results/             # PromptFoo evaluation outputs (886MB)
│   │   └── *.json
│   └── token_pricing.yaml
│
├── processed/                   # Derived analysis datasets
│   ├── tests.csv                # One row per test assertion (233k rows)
│   ├── responses.csv            # One row per model response (54k rows)
│   └── blind_grading/           # Blind grading analysis
│
├── scripts/
│   ├── generate_datasets.py     # Main data processing pipeline
│   ├── merge_blind_gradings.py  # Merge blind grading results
│   └── figures/                 # Figure generation scripts
│       ├── generate_figure1.py  # Pass rates heatmap
│       ├── generate_figure2.py  # Human vs AI comparison
│       ├── generate_figure3.py  # Model rankings
│       ├── generate_figure6.py  # Geographic error breakdown
│       └── style.py             # Shared plotting styles
│
├── paper/
│   ├── paper_draft.md           # Paper manuscript
│   ├── figures/                 # Figures referenced in paper
│   └── supplementary/           # Additional figures for appendix
│
├── prompts/                     # Prompt templates and test definitions
│
├── viewer/                      # Next.js app for browsing responses
│
└── archive/                     # Historical/one-time scripts
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

Requires `OPENROUTER_API_KEY` environment variable for latency fetching.

### Generate Figures

```bash
uv run python scripts/figures/generate_figure1.py
uv run python scripts/figures/generate_figure2.py
uv run python scripts/figures/generate_figure3.py
uv run python scripts/figures/generate_figure6.py
```

### Run the Viewer App

```bash
cd viewer
npm install
npm run dev
```

Then open http://localhost:3000

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

### Python
- pandas
- matplotlib
- seaborn
- requests
- python-dotenv
- scikit-learn

### Node.js (viewer app)
- Next.js 14
- React
- TailwindCSS
- shadcn/ui components
