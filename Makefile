.PHONY: figures metrics pipeline all

# Regenerate all figures from processed CSVs (no API key needed)
figures:
	uv run python scripts/figures/generate_figure2.py
	uv run python scripts/figures/generate_figure2b.py
	uv run python scripts/figures/generate_figure2c.py
	uv run python scripts/figures/generate_figure3.py
	uv run python scripts/figures/generate_figure4.py
	uv run python scripts/figures/generate_figure5.py
	uv run python scripts/figures/generate_figure_human_vs_ai.py
	uv run python scripts/figures/generate_figure_model_rankings.py
	uv run python scripts/figures/generate_figure_error_by_criterion.py

# Print paper metrics (Tables 1, 2, and inline statistics N1-N11)
metrics:
	uv run python scripts/figures/compute_paper_metrics.py

# Full pipeline from raw JSON (requires OPENROUTER_API_KEY)
pipeline:
	uv run python scripts/generate_datasets.py

all: pipeline figures metrics
