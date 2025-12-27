# KYC Evaluation Analysis

This directory contains all the code and data for analyzing the KYC (Know Your Customer) evaluation results.

## Directory Structure

```
analysis/
├── data/                           # Raw input data
│   ├── full-dataset.csv            # Full customer dataset (100 customers)
│   ├── final-human-baseline.csv    # Human baseline subset (30 customers)
│   ├── ground_truth_flags.json     # Ground truth flag values for each customer
│   ├── agreements.json             # Inter-rater agreement data
│   └── results/                    # Evaluation result JSON files
│       ├── full_dataset_main.json
│       ├── full_dataset_background_work.json
│       ├── human_baseline_subset_main.json
│       └── human_baseline_subset_background_work.json
├── processed/                      # Processed CSV datasets
│   ├── tests.csv                   # One row per test/assertion result
│   └── responses.csv               # One row per model response
├── scripts/                        # Data processing scripts
│   └── generate_analysis_datasets.py
├── plots/                          # Visualization code and outputs
│   ├── figures/                    # Generated plot images
│   ├── style.py                    # Common styling for plots
│   ├── plot_pass_rates.py
│   ├── plot_model_comparison.py
│   ├── plot_cost_latency.py
│   ├── plot_sources.py
│   ├── plot_advanced_analysis.py
│   ├── flag_accuracy_comparison.py
│   └── generate_all_plots.py
├── viewer/                         # Next.js app for browsing results
│   └── ...
└── README.md                       # This file
```

## Data Files

### Customer Datasets

#### `data/full-dataset.csv`
Contains >100 customer records for evaluation. Each row includes:
- `customer_info`: Full customer information text (Name, Institution, Email, etc.)
- `Name`: Customer name
- `Institution`: Affiliated institution
- `Type`: Customer category
- `Order`: Ordering/priority field

#### `data/final-human-baseline.csv`
A ~40-customer subset used for human baseline comparison. Same schema as full-dataset.csv.

### Result Files

The evaluation was run with two different prompts and on two different customer subsets:

| File | Prompt Type | Dataset | Description |
|------|-------------|---------|-------------|
| `full_dataset_main.json` | main | Full (100) | Main evaluation prompt on full dataset |
| `full_dataset_background_work.json` | background_work | Full (100) | Background work prompt on full dataset |
| `human_baseline_subset_main.json` | main | Subset (30) | Main prompt with human baseline comparison |
| `human_baseline_subset_background_work.json` | background_work | Subset (30) | Background work with human baseline |

Each JSON file contains:
- `evalId`: Unique evaluation identifier
- `results.results[]`: Array of evaluation results
  - `id`: Unique result ID
  - `vars`: Input variables (customer_info, work_url)
  - `provider`: Model/provider information
  - `response`: Model output and metadata
  - `gradingResult.componentResults[]`: Individual test/assertion results

### Ground Truth

#### `data/ground_truth_flags.json`
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
| `order` | Customer ordering |
| `work_url` | Work URL if applicable (background_work prompt) |
| `is_human_baseline_dataset` | Whether from human baseline subset |
| `model_label` | Human-readable model name |
| `model_name` | Technical model identifier |
| `model_type` | `human_baseline`, `web_only`, or `all_tools` |
| `is_human_baseline` | Whether this is a human baseline response |
| `prompt_type` | `main` or `background_work` |
| `metric_name` | Test/assertion name |
| `test_category` | `flag_accuracy`, `claim_support`, `source_reliability`, or `work_relevance` |
| `original_pass` | Original pass/fail value from evaluation |
| `pass` | Corrected pass/fail value (see corrections below) |
| `pass_correction_applied` | Description of any correction applied |
| `reason` | LLM-generated reasoning for the result |
| `extracted_section` | Extracted text section being evaluated |
| `num_sources_used` | Total sources used for this assertion |
| `num_web_sources` | Count of web search sources |
| `num_epmc_sources` | Count of Europe PMC (publication) sources |
| `num_orcid_sources` | Count of ORCID profile sources |
| `num_screen_sources` | Count of sanctions screening sources |
| `source_urls` | JSON array of source URLs |
| `sources_json` | Full source metadata as JSON |
| `ground_truth_*` | Ground truth flag values |
| `extracted_flag` | Extracted flag value from model response |
| `claims_json` | Extracted claims as JSON (for claim_support tests) |

### `processed/responses.csv`
One row per model response. Used for cost/latency analysis.

| Field | Description |
|-------|-------------|
| `eval_id` | Evaluation run identifier |
| `result_id` | Unique result identifier |
| `customer_name` | Customer name |
| `customer_institution` | Customer institution |
| `customer_type` | Customer category |
| `order` | Customer ordering |
| `is_human_baseline_dataset` | Whether from human baseline subset |
| `model_label` | Human-readable model name |
| `model_name` | Technical model identifier |
| `model_type` | `human_baseline`, `web_only`, or `all_tools` |
| `is_human_baseline` | Whether this is a human baseline response |
| `prompt_type` | `main` or `background_work` |
| `full_response` | Complete model response (thinking blocks stripped) |
| `response_length` | Character count of response |
| `latency_ms` | Total latency in milliseconds (from OpenRouter API) |
| `total_cost` | Total cost in USD |
| `model_cost` | Model inference cost |
| `web_search_cost` | Web search API cost |
| `num_web_searches` | Number of web searches performed |
| `prompt_tokens` | Input token count |
| `completion_tokens` | Output token count |
| `total_tokens` | Total token count |
| `num_sources` | Total number of sources used |
| `num_*_sources` | Breakdown by source type |
| `source_urls` | JSON array of source URLs |
| `sources_json` | Full source metadata as JSON |
| `num_assertions` | Number of test assertions |
| `num_assertions_passed` | Number of passing assertions |
| `time_to_complete_minutes` | Time for human baseline (if applicable) |

## Data Processing and Corrections

### Flag Accuracy Corrections

The `pass` field in tests.csv has corrections applied to the original evaluation results:

1. **Ground Truth UNDETERMINED**: If ground truth is `UNDETERMINED`, any extracted value passes
   - Correction type: `gt_undetermined_pass`

2. **Exact Match Required**: If ground truth is NOT `UNDETERMINED`, require exact match
   - `FLAG` must match `FLAG`, `NO FLAG` must match `NO FLAG`
   - Correction type: `exact_match_pass` or `exact_match_fail`

### Human Baseline Corrections

Additional corrections applied only to human baseline responses on the human baseline dataset:

1. **Empty Evidence Fail**: Claim support tests now deterministically fail if no sources/evidence provided
   - Correction type: `empty_evidence_fail`
   - Logic: Parses Table 1 (for criteria) or Table 3 (for background work) in the response

2. **Sanctions Exact Match**: Sanctions claim support passes if the sanctions flag passes as well (to fix the case where human reviewers cited the CSL API but the link did not contain information specific to the customer/institution)
   - Correction type: `sanctions_exact_match`

### Source Extraction

Sources are extracted from tool outputs and categorized by type:
- `web`: Web search results (URLs, titles)
- `epmc`: Europe PMC publications (DOI, authors, journal, citations)
- `orcid`: ORCID profiles (name, emails, works)
- `orcworks`: ORCID works search results
- `screen`: Sanctions screening results

### Latency Calculation

To route around some issues with timing cached responses, latency is fetched from the OpenRouter API by:

1. Extracting `generation_ids` from each response's metadata
2. Fetching individual generation metadata from OpenRouter API in parallel
3. Summing latencies across multiple generations (for tool-use responses with multiple API calls)

Falls back to PromptFoo's `latencyMs` if OpenRouter fetch fails.

## Test Categories

### Flag Accuracy (`flag_accuracy`)
Tests whether the model correctly identified each flag:
- Affiliation with Prohibited Regions
- Institution Verification
- Domain/Email Verification
- Sanctions Screening

### Claim Support (`claim_support`)
Tests whether claims in the response are supported by cited sources.

### Source Reliability (`source_reliability`)
Tests whether sources used are reliable and authoritative.

### Work Relevance (`work_relevance`)
Tests whether identified background work is relevant to the customer.

## Model Types

- `human_baseline`: Human expert responses
- `web_only`: Models using only web search tools
- `all_tools`: Models using full tool suite (web, ORCID, EPMC, sanctions screening)

## Running the Scripts

### Generate Processed Datasets

```bash
cd scripts
python generate_analysis_datasets.py
```

Requires:
- `OPENROUTER_API_KEY` environment variable for latency fetching

### Generate Plots

```bash
cd plots
python generate_all_plots.py
```

Or run individual plot scripts:
```bash
python plot_pass_rates.py
python plot_model_comparison.py
python plot_cost_latency.py
python plot_sources.py
python plot_advanced_analysis.py
```

### Run the Viewer App

```bash
cd viewer
npm install
npm run dev
```

Then open http://localhost:3000

## Dependencies

### Python
- pandas
- matplotlib
- seaborn
- requests
- python-dotenv

### Node.js (viewer app)
- Next.js 14
- React
- TailwindCSS
- shadcn/ui components
