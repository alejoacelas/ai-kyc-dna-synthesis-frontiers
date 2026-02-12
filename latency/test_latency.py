#!/usr/bin/env python3
"""
Test script to compare OpenRouter's reported latency with actual wall-clock time.

Runs test cases against multiple models and compares:
1. Wall-clock time (time from request sent to response received)
2. OpenRouter's reported latency from generation metadata

Usage:
    python test_latency.py                    # Run single model test
    python test_latency.py --all              # Run all models in parallel
    python test_latency.py --model "anthropic/claude-sonnet-4"  # Specific model
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tavily import TavilyClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.registry import execute_tool_with_id, get_openai_tools

# OpenRouter endpoints
OPENROUTER_RESPONSES_URL = "https://openrouter.ai/api/v1/responses"
OPENROUTER_GENERATION_URL = "https://openrouter.ai/api/v1/generation"

# Models from promptfooconfig.yaml
MODELS = [
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-pro",
    "x-ai/grok-4",
    "minimax/minimax-m2",
]

PROVIDER_MAP = {
    "anthropic": "Anthropic",
    "x-ai": "xAI",
    "google": "Google",
    "z-ai": "Z.AI",
    "minimax": "MiniMax",
}


@dataclass
class LatencyResult:
    """Results from a latency test."""
    model: str
    wall_clock_ms: float
    openrouter_latency_ms: Optional[float]
    num_iterations: int
    num_tool_calls: int
    input_tokens: int
    output_tokens: int
    error: Optional[str] = None


def get_provider(model: str) -> str:
    """Extract provider from model name."""
    if "/" in model:
        prefix = model.split("/")[0].lower()
        return PROVIDER_MAP.get(prefix, prefix.title())
    return ""


def load_test_case(dataset_path: str = "datasets/final-human-baseline.csv") -> Dict[str, str]:
    """Load a single test case from the dataset."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Return first row
        return next(reader)


def load_prompt_template(prompt_path: str = "prompts/background_work.txt") -> str:
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


def fetch_generation_metadata(
    generation_id: str,
    api_key: str,
    max_retries: int = 10,
    retry_delay: float = 0.5,
) -> Optional[Dict[str, Any]]:
    """Fetch generation metadata from OpenRouter."""
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                OPENROUTER_GENERATION_URL,
                headers=headers,
                params={"id": generation_id},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"]
        except Exception:
            pass
        time.sleep(retry_delay)

    return None


def run_single_test(
    model: str,
    prompt: str,
    tools: List[Dict[str, Any]],
    api_key: str,
    tavily_client: TavilyClient,
) -> LatencyResult:
    """
    Run a single test and measure latency.

    Returns both wall-clock time and OpenRouter's reported latency.
    """
    provider = get_provider(model)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/alejoacelas/kyc-evals",
        "X-Title": "KYC Evals Latency Test",
    }

    tool_outputs: Dict[str, Dict[str, Any]] = {}
    generation_ids: List[str] = []
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
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("id"):
                generation_ids.append(data["id"])

            output_items = data.get("output", [])
            function_calls = []

            for item in output_items:
                item_type = item.get("type")
                if item_type == "function_call":
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
        return LatencyResult(
            model=model,
            wall_clock_ms=(wall_end - wall_start) * 1000,
            openrouter_latency_ms=None,
            num_iterations=num_iterations,
            num_tool_calls=num_tool_calls,
            input_tokens=0,
            output_tokens=0,
            error=str(e),
        )

    # Stop wall-clock timer (BEFORE metadata fetching - we only want to measure the actual API calls)
    wall_end = time.perf_counter()
    wall_clock_ms = (wall_end - wall_start) * 1000

    # Fetch generation metadata for OpenRouter's reported latency (not included in wall-clock time)
    total_openrouter_latency_ms = 0.0
    total_input_tokens = 0
    total_output_tokens = 0

    for gen_id in generation_ids:
        meta = fetch_generation_metadata(gen_id, api_key)
        if meta:
            total_input_tokens += meta.get("tokens_prompt", 0)
            total_output_tokens += meta.get("tokens_completion", 0)

            latency = meta.get("latency")
            if latency is not None:
                if isinstance(latency, (int, float)):
                    total_openrouter_latency_ms += float(latency)
                elif isinstance(latency, dict):
                    total_openrouter_latency_ms += float(
                        latency.get("ms", latency.get("milliseconds", 0))
                    )

    return LatencyResult(
        model=model,
        wall_clock_ms=wall_clock_ms,
        openrouter_latency_ms=total_openrouter_latency_ms if total_openrouter_latency_ms > 0 else None,
        num_iterations=num_iterations,
        num_tool_calls=num_tool_calls,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
    )


def run_test_for_model(
    model: str,
    prompt: str,
    tools: List[Dict[str, Any]],
    api_key: str,
    tavily_key: str,
) -> LatencyResult:
    """Run test for a single model (thread-safe)."""
    tavily_client = TavilyClient(tavily_key)
    print(f"Starting test for {model}...")
    result = run_single_test(model, prompt, tools, api_key, tavily_client)
    return result


def print_results(results: List[LatencyResult]) -> None:
    """Print results in a formatted table."""
    print("\n" + "=" * 100)
    print("LATENCY COMPARISON RESULTS")
    print("=" * 100)

    print(f"\n{'Model':<35} {'Wall Clock':<15} {'OR Latency':<15} {'Diff':<12} {'Iters':<6} {'Tools':<6}")
    print("-" * 100)

    for r in results:
        wall = f"{r.wall_clock_ms:.0f}ms"

        if r.error:
            or_latency = "ERROR"
            diff = "-"
        elif r.openrouter_latency_ms is not None:
            or_latency = f"{r.openrouter_latency_ms:.0f}ms"
            diff_ms = r.wall_clock_ms - r.openrouter_latency_ms
            diff_pct = (diff_ms / r.wall_clock_ms) * 100 if r.wall_clock_ms > 0 else 0
            diff = f"+{diff_ms:.0f}ms ({diff_pct:.1f}%)"
        else:
            or_latency = "N/A"
            diff = "-"

        print(f"{r.model:<35} {wall:<15} {or_latency:<15} {diff:<12} {r.num_iterations:<6} {r.num_tool_calls:<6}")

        if r.error:
            print(f"  Error: {r.error}")

    print("-" * 100)
    print("\nNotes:")
    print("- Wall Clock: Total time from first request to final response")
    print("  (includes tool execution, excludes metadata fetching)")
    print("- OR Latency: Sum of latencies reported by OpenRouter generation metadata")
    print("  (model inference time only, as reported by OpenRouter)")
    print("- Diff: Overhead = Wall Clock - OR Latency")
    print("  (network round-trips + tool execution + serialization)")
    print("- Iters: Number of API round-trips (initial + tool result submissions)")
    print("- Tools: Number of tool calls executed")


def main():
    parser = argparse.ArgumentParser(description="Test OpenRouter latency measurement")
    parser.add_argument("--all", action="store_true", help="Run all models in parallel")
    parser.add_argument("--model", type=str, help="Specific model to test")
    parser.add_argument("--tools", type=str, default="search_web",
                        help="Tools to use (comma-separated or 'all')")
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

    # Load test case and prompt
    print("Loading test case and prompt template...")
    test_case = load_test_case()
    template = load_prompt_template()
    prompt = build_prompt(template, test_case)

    # Build tools
    tool_names = None if args.tools == "all" else args.tools.split(",")
    tools = build_tools(tool_names)

    print(f"Test case: {test_case.get('Name', 'Unknown')}")
    print(f"Tools: {[t['name'] for t in tools]}")
    print(f"Prompt length: {len(prompt)} chars")

    # Determine which models to test
    if args.model:
        models = [args.model]
    elif args.all:
        models = MODELS
    else:
        # Default: single model (Claude Sonnet)
        models = ["anthropic/claude-sonnet-4"]

    print(f"\nTesting {len(models)} model(s): {models}")

    results: List[LatencyResult] = []

    if len(models) == 1:
        # Single model - run directly
        result = run_test_for_model(models[0], prompt, tools, api_key, tavily_key)
        results.append(result)
    else:
        # Multiple models - run in parallel
        print("\nRunning tests in parallel...")
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(
                    run_test_for_model, model, prompt, tools, api_key, tavily_key
                ): model
                for model in models
            }

            for future in as_completed(futures):
                model = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  Completed: {model} ({result.wall_clock_ms:.0f}ms)")
                except Exception as e:
                    print(f"  Failed: {model} - {e}")
                    results.append(LatencyResult(
                        model=model,
                        wall_clock_ms=0,
                        openrouter_latency_ms=None,
                        num_iterations=0,
                        num_tool_calls=0,
                        input_tokens=0,
                        output_tokens=0,
                        error=str(e),
                    ))

    # Sort by model name for consistent output
    results.sort(key=lambda r: r.model)

    print_results(results)


if __name__ == "__main__":
    main()
