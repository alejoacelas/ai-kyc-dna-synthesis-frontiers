#!/usr/bin/env python3
"""
Comprehensive latency benchmark for KYC evals.

Runs all model configurations from promptfooconfig.yaml on multiple prompts
and test cases, measuring wall-clock time for each.

Usage:
    python benchmark_latency.py                    # Run full benchmark
    python benchmark_latency.py --sample 5         # Use 5 customers instead of 10
    python benchmark_latency.py --output results.csv  # Custom output file
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

import requests
from tavily import TavilyClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.registry import execute_tool_with_id, get_openai_tools

# OpenRouter endpoints
OPENROUTER_RESPONSES_URL = "https://openrouter.ai/api/v1/responses"

# Model configurations from promptfooconfig.yaml
MODEL_CONFIGS = [
    {"label": "Claude Sonnet 4 (Web)", "model": "anthropic/claude-sonnet-4", "tools": ["search_web"]},
    {"label": "Claude Sonnet 4 (All Tools)", "model": "anthropic/claude-sonnet-4", "tools": ["all"]},
    {"label": "Gemini 2.5 Pro (Web)", "model": "google/gemini-2.5-pro", "tools": ["search_web"]},
    {"label": "Gemini 2.5 Pro (All Tools)", "model": "google/gemini-2.5-pro", "tools": ["all"]},
    {"label": "Grok 4 (Web)", "model": "x-ai/grok-4", "tools": ["search_web"]},
    {"label": "Grok 4 (All Tools)", "model": "x-ai/grok-4", "tools": ["all"]},
    {"label": "GLM 4.6 (Web)", "model": "z-ai/glm-4.6", "tools": ["search_web"]},
    {"label": "GLM 4.6 (All Tools)", "model": "z-ai/glm-4.6", "tools": ["all"]},
    {"label": "MiniMax M2 (Web)", "model": "minimax/minimax-m2", "tools": ["search_web"]},
    {"label": "MiniMax M2 (All Tools)", "model": "minimax/minimax-m2", "tools": ["all"]},
]

PROMPTS = {
    "background_work": "prompts/background_work.txt",
    "simple": "prompts/simple.txt",
}

PROVIDER_MAP = {
    "anthropic": "Anthropic",
    "x-ai": "xAI",
    "google": "Google",
    "z-ai": "Z.AI",
    "minimax": "MiniMax",
}


@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    model_label: str
    model: str
    tools: str
    prompt_name: str
    customer_name: str
    customer_idx: int
    wall_clock_ms: float
    num_iterations: int
    num_tool_calls: int
    error: Optional[str] = None


def get_provider(model: str) -> str:
    """Extract provider from model name."""
    if "/" in model:
        prefix = model.split("/")[0].lower()
        return PROVIDER_MAP.get(prefix, prefix.title())
    return ""


def load_test_cases(dataset_path: str, sample_size: int) -> List[Dict[str, str]]:
    """Load test cases from the dataset."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)
    return cases[:sample_size]


def load_prompt_template(prompt_path: str) -> str:
    """Load prompt template."""
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(template: str, test_case: Dict[str, str]) -> str:
    """Build prompt from template and test case."""
    return template.replace("{{customer_info}}", test_case.get("customer_info", ""))


def build_tools(tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Build tools in OpenRouter Responses API format."""
    if tool_names is None or tool_names == ["all"]:
        tool_names = None

    openai_tools = get_openai_tools(tool_names)

    responses_tools = []
    for tool in openai_tools:
        if tool.get("type") == "function":
            func = tool["function"]
            responses_tools.append({
                "type": "function",
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"],
            })

    return responses_tools


def run_single_benchmark(
    model_config: Dict[str, Any],
    prompt_name: str,
    prompt_template: str,
    test_case: Dict[str, str],
    customer_idx: int,
    api_key: str,
    tavily_client: TavilyClient,
) -> BenchmarkResult:
    """Run a single benchmark and measure wall-clock time."""
    model = model_config["model"]
    provider = get_provider(model)
    tools = build_tools(model_config["tools"])
    prompt = build_prompt(prompt_template, test_case)
    customer_name = test_case.get("Name", f"Customer {customer_idx}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/alejoacelas/kyc-evals",
        "X-Title": "KYC Evals Benchmark",
    }

    tool_outputs: Dict[str, Dict[str, Any]] = {}
    num_iterations = 0
    num_tool_calls = 0

    input_items: List[Dict[str, Any]] = [
        {"role": "user", "content": prompt}
    ]

    # Start wall-clock timer
    wall_start = time.perf_counter()

    max_iterations = 20
    try:
        for _ in range(max_iterations):
            num_iterations += 1

            payload: Dict[str, Any] = {
                "model": model,
                "input": input_items,
                "tools": tools,
                "tool_choice": "auto",
            }
            if provider:
                payload["provider"] = {"order": [provider]}

            response = requests.post(
                OPENROUTER_RESPONSES_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()

            output_items = data.get("output", [])
            function_calls = []

            for item in output_items:
                if item.get("type") == "function_call":
                    function_calls.append(item)

            if not function_calls:
                break

            for fc in function_calls:
                num_tool_calls += 1
                func_name = fc.get("name", "")
                call_id = fc.get("call_id", "")

                try:
                    args = json.loads(fc.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}

                result = execute_tool_with_id(
                    func_name,
                    args,
                    tool_outputs,
                    tavily_client=tavily_client,
                )

                input_items.append({
                    "type": "function_call",
                    "id": fc.get("id", call_id),
                    "call_id": call_id,
                    "name": func_name,
                    "arguments": fc.get("arguments", "{}"),
                    "status": "completed",
                })
                input_items.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result,
                })

    except Exception as e:
        wall_end = time.perf_counter()
        return BenchmarkResult(
            model_label=model_config["label"],
            model=model,
            tools=",".join(model_config["tools"]),
            prompt_name=prompt_name,
            customer_name=customer_name,
            customer_idx=customer_idx,
            wall_clock_ms=(wall_end - wall_start) * 1000,
            num_iterations=num_iterations,
            num_tool_calls=num_tool_calls,
            error=str(e),
        )

    # Stop wall-clock timer
    wall_end = time.perf_counter()
    wall_clock_ms = (wall_end - wall_start) * 1000

    return BenchmarkResult(
        model_label=model_config["label"],
        model=model,
        tools=",".join(model_config["tools"]),
        prompt_name=prompt_name,
        customer_name=customer_name,
        customer_idx=customer_idx,
        wall_clock_ms=wall_clock_ms,
        num_iterations=num_iterations,
        num_tool_calls=num_tool_calls,
    )


def run_benchmark_task(task: Dict[str, Any]) -> BenchmarkResult:
    """Run a single benchmark task (for parallel execution)."""
    tavily_client = TavilyClient(task["tavily_key"])
    return run_single_benchmark(
        model_config=task["model_config"],
        prompt_name=task["prompt_name"],
        prompt_template=task["prompt_template"],
        test_case=task["test_case"],
        customer_idx=task["customer_idx"],
        api_key=task["api_key"],
        tavily_client=tavily_client,
    )


def save_results(results: List[BenchmarkResult], output_path: str) -> None:
    """Save results to CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "model_label", "model", "tools", "prompt_name", "customer_name",
            "customer_idx", "wall_clock_ms", "num_iterations", "num_tool_calls", "error"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def calculate_statistics(results: List[BenchmarkResult]) -> Dict[str, Any]:
    """Calculate statistics by model config."""
    from collections import defaultdict

    # Group results by model_label and prompt_name
    by_model_prompt = defaultdict(list)
    by_model = defaultdict(list)

    for r in results:
        if r.error is None:
            by_model_prompt[(r.model_label, r.prompt_name)].append(r.wall_clock_ms)
            by_model[r.model_label].append(r.wall_clock_ms)

    stats = {
        "by_model_prompt": {},
        "by_model": {},
        "summary": [],
    }

    # Stats by model and prompt
    for (model_label, prompt_name), times in sorted(by_model_prompt.items()):
        key = f"{model_label} | {prompt_name}"
        mean_ms = sum(times) / len(times) if times else 0
        stats["by_model_prompt"][key] = {
            "mean_ms": mean_ms,
            "mean_s": mean_ms / 1000,
            "count": len(times),
            "total_ms": sum(times),
        }

    # Stats by model (sum of both prompts)
    for model_label, times in sorted(by_model.items()):
        mean_ms = sum(times) / len(times) if times else 0
        stats["by_model"][model_label] = {
            "mean_ms": mean_ms,
            "mean_s": mean_ms / 1000,
            "count": len(times),
            "total_ms": sum(times),
        }

    # Summary table data
    for model_label in sorted(set(r.model_label for r in results)):
        bg_times = [r.wall_clock_ms for r in results
                    if r.model_label == model_label and r.prompt_name == "background_work" and r.error is None]
        simple_times = [r.wall_clock_ms for r in results
                       if r.model_label == model_label and r.prompt_name == "simple" and r.error is None]

        bg_mean = sum(bg_times) / len(bg_times) if bg_times else 0
        simple_mean = sum(simple_times) / len(simple_times) if simple_times else 0
        combined_mean = bg_mean + simple_mean  # Sum of both prompt times

        stats["summary"].append({
            "model_label": model_label,
            "background_work_mean_s": bg_mean / 1000,
            "simple_mean_s": simple_mean / 1000,
            "combined_mean_s": combined_mean / 1000,
            "bg_count": len(bg_times),
            "simple_count": len(simple_times),
        })

    return stats


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print statistics in a formatted table."""
    print("\n" + "=" * 120)
    print("BENCHMARK RESULTS - MEAN WALL-CLOCK TIME BY MODEL AND PROMPT")
    print("=" * 120)

    print(f"\n{'Model':<35} {'Background Work':<18} {'Simple':<18} {'Total (BG+Simple)':<18}")
    print("-" * 120)

    for row in stats["summary"]:
        bg = f"{row['background_work_mean_s']:.1f}s ({row['bg_count']})"
        simple = f"{row['simple_mean_s']:.1f}s ({row['simple_count']})"
        combined = f"{row['combined_mean_s']:.1f}s"
        print(f"{row['model_label']:<35} {bg:<18} {simple:<18} {combined:<18}")

    print("-" * 120)
    print("\nNote: Times in seconds, (N) = number of successful runs")


def main():
    parser = argparse.ArgumentParser(description="Benchmark latency across models and prompts")
    parser.add_argument("--sample", type=int, default=10, help="Number of customers to sample")
    parser.add_argument("--output", type=str, default="benchmark_results.csv", help="Output CSV file")
    parser.add_argument("--parallel", type=int, default=5, help="Max parallel requests")
    args = parser.parse_args()

    # Check environment variables
    api_key = os.environ.get("OPENROUTER_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    if not tavily_key:
        print("Error: TAVILY_API_KEY environment variable not set")
        sys.exit(1)

    # Disable cache for accurate timing
    os.environ["KYC_CACHE_ENABLED"] = "false"

    # Load test cases
    print(f"Loading {args.sample} test cases...")
    test_cases = load_test_cases("datasets/final-human-baseline.csv", args.sample)
    print(f"Loaded {len(test_cases)} customers")

    # Load prompt templates
    print("Loading prompt templates...")
    prompt_templates = {}
    for name, path in PROMPTS.items():
        prompt_templates[name] = load_prompt_template(path)
    print(f"Loaded {len(prompt_templates)} prompts: {list(prompt_templates.keys())}")

    # Build all tasks
    tasks = []
    for model_config in MODEL_CONFIGS:
        for prompt_name, template in prompt_templates.items():
            for idx, test_case in enumerate(test_cases):
                tasks.append({
                    "model_config": model_config,
                    "prompt_name": prompt_name,
                    "prompt_template": template,
                    "test_case": test_case,
                    "customer_idx": idx,
                    "api_key": api_key,
                    "tavily_key": tavily_key,
                })

    total_tasks = len(tasks)
    print(f"\nTotal tasks: {total_tasks}", flush=True)
    print(f"  {len(MODEL_CONFIGS)} model configs × {len(prompt_templates)} prompts × {len(test_cases)} customers", flush=True)
    print(f"\nRunning with {args.parallel} parallel workers...", flush=True)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    results: List[BenchmarkResult] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(run_benchmark_task, task): task for task in tasks}

        for future in as_completed(futures):
            task = futures[future]
            completed += 1
            try:
                result = future.result()
                results.append(result)
                status = "OK" if result.error is None else f"ERR: {result.error[:30]}"
                print(f"  [{completed}/{total_tasks}] {result.model_label} | {result.prompt_name} | "
                      f"{result.customer_name[:20]} | {result.wall_clock_ms/1000:.1f}s | {status}")
            except Exception as e:
                print(f"  [{completed}/{total_tasks}] FAILED: {task['model_config']['label']} - {e}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Save results
    save_results(results, args.output)
    print(f"\nResults saved to: {args.output}")

    # Calculate and print statistics
    stats = calculate_statistics(results)
    print_statistics(stats)

    # Save stats as JSON
    stats_path = args.output.replace(".csv", "_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")


if __name__ == "__main__":
    main()
