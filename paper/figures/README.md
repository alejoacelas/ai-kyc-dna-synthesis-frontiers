# Figures for Paper

This directory should contain the following figures referenced in the paper:

1. **figure1_pass_rates_heatmap.png** - Pass rates by model and test category heatmap
2. **figure2_human_vs_ai_comparison.png** - Error rates by verification task comparison
3. **figure3_model_rankings.png** - Overall pass rates by model horizontal bars
4. **figure4_web_vs_tools_comparison.png** - Web-only vs tools comparison
5. **figure6_geographic_breakdown.png** - Pass rates by customer region

## Data Source
All figures should be generated from `/Users/alejo/Code/ai-kyc-results/processed/tests.csv`

## Figure Specifications

### Figure 1 & 3: Screener Performance Overview
Figures 1 and 3 are presented together to provide a comprehensive view of screener performance.

**Figure 1: Pass Rates Heatmap**
- Format: Heatmap with three visually separated blocks
- Rows: Screeners grouped by type:
  - **AT (All Tools)**: AI screeners with full tool access (web search, databases, APIs)
  - **W (Web-only)**: AI screeners limited to web search capabilities
  - **Human**: Human baseline screeners (5min and 30min time allocations)
- Columns: Test categories (Flag Accuracy, Claim Support, Source Reliability, Work Relevance)
- Color: Sequential RdYlGn (red=50%→green=100%)
- Annotations: Pass rate percentage values

**Figure 3: Average Pass Rate by Screener**
- Format: Horizontal bar chart
- Shows overall pass rates across all tasks for each screener
- Color-coded by screener type (blue shades for AI, amber for human)

### Figure 2: Human vs AI Comparison
- Format: Grouped bar chart
- X-axis: Tasks (affiliation, institution, domain, sanctions, work)
- Groups: Human 30min, Best AI model per task, Worst AI model per task
- Y-axis: Error rates (%)

### Figure 3: Model Rankings
- Format: Horizontal bar chart
- Y-axis: Models sorted by overall pass rate
- Color-coded by model_type (web_only, all_tools)
- X-axis: Overall pass rate (%)

### Figure 4: Web vs Tools
- Format: Paired bar chart
- X-axis: Test categories
- Groups: Web-only average, All-tools average
- Y-axis: Pass rates (%)

### Figure 6: Geographic Breakdown
- Format: Grouped bar chart
- X-axis: Regions (USA, Europe+Oceania, China, Other)
- Groups: Test categories
- Y-axis: Pass rates (%)