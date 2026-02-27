# Evaluating AI-assisted customer verification for DNA synthesis screening

Replication package for the Frontiers manuscript. Contains anonymized data, figure generation scripts, and LaTeX source.

## Quick start

```bash
# Install dependencies
uv sync

# Generate all figures (outputs to paper/figures/)
make figures

# Compute table values and inline statistics
make tables
```

## Repository structure

```
frontiers-results/
├── data/
│   ├── tests.csv                       # One row per test assertion
│   ├── responses.csv                   # One row per model response
│   ├── token_pricing.yaml              # Per-token pricing by model
│   ├── customers/
│   │   ├── full_dataset.csv            # 134 anonymized customer profiles
│   │   └── human_baseline_subset.csv   # 40-profile subset for human comparison
│   └── annotations/
│       ├── ground_truth_flags.json     # Verified flag determinations
│       ├── blind_gradings.json         # Blind re-grading for validation
│       ├── agreements.json             # Inter-rater agreement
│       └── flag_error_comments.json    # Human notes on flag errors
│
├── scripts/
│   ├── style.py                        # Shared colors, labels, matplotlib config
│   ├── generate_main_figures.py        # Figures 2-5
│   ├── generate_model_performance.py   # Figures E1-E8
│   ├── generate_full_dataset.py        # Figures F1-F5
│   ├── generate_flag_accuracy.py       # Figures G1-G9
│   ├── generate_cost_latency.py        # Figures H1-H7
│   ├── generate_source_analysis.py     # Figures I1-I6
│   └── compute_tables.py              # Tables 1-2, inline statistics N1-N11
│
├── paper/
│   ├── main.tex                        # Main manuscript (Frontiers template)
│   ├── supplementary.tex               # Supplementary material
│   ├── references.bib                  # Bibliography
│   └── figures/                        # Generated figures (+ static Figure1.png)
│
├── prompts/
│   ├── screening.txt                   # Main screening prompt
│   ├── background_work.txt             # Background work prompt
│   └── evaluation/                     # Test definitions
│       ├── claim_support.yaml
│       ├── extraction.yaml
│       ├── source_reliability.yaml
│       └── work_relevance.yaml
│
├── Makefile
└── pyproject.toml
```

## Data

### tests.csv

One row per test assertion. Key columns:

| Column | Description |
|--------|-------------|
| `model_label` | Human-readable model name (e.g., "Gemini 2.5 Pro (All Tools)") |
| `model_type` | `web_only`, `all_tools`, or `human_baseline` |
| `test_category` | `flag_accuracy`, `claim_support`, `source_reliability`, or `work_relevance` |
| `pass` | Corrected pass/fail result |
| `customer_type` | Customer category |
| `institution_country` | Region grouping |

### responses.csv

One row per model response. Key columns:

| Column | Description |
|--------|-------------|
| `model_label` | Human-readable model name |
| `total_cost` | Total cost in USD |
| `latency_ms` | Response latency in milliseconds |
| `num_web_searches` | Number of web searches performed |

## Figures

| Script | Outputs | Description |
|--------|---------|-------------|
| `generate_main_figures.py` | Figure2-5 | Pass rates heatmap, cost breakdown, cost vs performance, flag errors |
| `generate_model_performance.py` | FigureE1-E8 | Confidence intervals, rankings, per-task/customer analysis, pairwise tests |
| `generate_full_dataset.py` | FigureF1-F5 | Full dataset validation, subset comparison |
| `generate_flag_accuracy.py` | FigureG1-G9 | Ground truth, confusion matrices, human vs AI errors |
| `generate_cost_latency.py` | FigureH1-H7 | Token costs, latency, human vs AI time |
| `generate_source_analysis.py` | FigureI1-I6 | Web searches, source types, tool effects |

## Dependencies

Python >= 3.12, managed with [uv](https://docs.astral.sh/uv/). Run `uv sync` to install.

## License

See [LICENSE](LICENSE).
