.PHONY: all figures tables clean

all: figures tables

figures:
	uv run python scripts/generate_main_figures.py
	uv run python scripts/generate_model_performance.py
	uv run python scripts/generate_full_dataset.py
	uv run python scripts/generate_flag_accuracy.py
	uv run python scripts/generate_cost_latency.py
	uv run python scripts/generate_source_analysis.py

tables:
	uv run python scripts/compute_tables.py

clean:
	rm -f paper/figures/Figure[2-5].png paper/figures/Figure[E-I]*.png
