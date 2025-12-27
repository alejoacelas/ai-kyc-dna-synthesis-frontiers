#!/usr/bin/env python3
"""
Generate analysis datasets for KYC paper from promptfoo evaluation results.

Creates two CSV datasets:
1. tests.csv - One row per test (assertion) result for accuracy/reliability analysis
2. responses.csv - One row per model response for cost/latency analysis
"""

import json
import csv
import re
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# File paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"
OUTPUT_DIR = BASE_DIR / "processed"

# Result files with their metadata
RESULT_FILES = {
    "full_dataset_background_work.json": {
        "prompt_type": "background_work",
        "is_human_baseline_dataset": False,
    },
    "full_dataset_main.json": {
        "prompt_type": "main",
        "is_human_baseline_dataset": False,
    },
    "human_baseline_subset_main.json": {
        "prompt_type": "main",
        "is_human_baseline_dataset": True,
    },
    "human_baseline_subset_background_work.json": {
        "prompt_type": "background_work",
        "is_human_baseline_dataset": True,
    },
}

# Reference datasets
FULL_DATASET = DATA_DIR / "full-dataset.csv"
HUMAN_BASELINE_DATASET = DATA_DIR / "final-human-baseline.csv"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth_flags.json"

# OpenRouter API
OPENROUTER_GENERATION_URL = "https://openrouter.ai/api/v1/generation"


def fetch_generation_metadata(generation_id: str, api_key: str) -> Optional[dict]:
    """
    Fetch generation metadata from OpenRouter API.

    Returns dict with latency, generation_time, tokens, etc. or None if failed.
    """
    try:
        response = requests.get(
            OPENROUTER_GENERATION_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"id": generation_id},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
    except Exception as e:
        print(f"  Warning: Failed to fetch generation {generation_id}: {e}")
    return None


def fetch_all_generation_latencies(
    all_results: list,
    max_workers: int = 20,
) -> dict[str, int]:
    """
    Fetch latency for all generation IDs from OpenRouter API in parallel.

    Args:
        all_results: List of result dicts containing generation_ids in metadata.
        max_workers: Number of parallel threads.

    Returns:
        Dict mapping result_id -> total latency in ms (summed across all generations).
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("  Warning: OPENROUTER_API_KEY not set, skipping latency fetch")
        return {}

    # Collect all unique generation IDs and map them to result IDs
    generation_to_results: dict[str, list[str]] = {}  # gen_id -> [result_ids]
    result_generation_ids: dict[str, list[str]] = {}  # result_id -> [gen_ids]

    for result_info in all_results:
        result = result_info["result"]
        result_id = result.get("id", "")
        response_meta = result.get("response", {}).get("metadata", {})
        gen_ids = response_meta.get("generation_ids", [])

        if result_id and gen_ids:
            result_generation_ids[result_id] = gen_ids
            for gen_id in gen_ids:
                if gen_id not in generation_to_results:
                    generation_to_results[gen_id] = []
                generation_to_results[gen_id].append(result_id)

    unique_gen_ids = list(generation_to_results.keys())
    if not unique_gen_ids:
        print("  No generation IDs found in results")
        return {}

    print(f"  Fetching latency for {len(unique_gen_ids)} generations...")

    # Fetch all generation metadata in parallel
    generation_latencies: dict[str, int] = {}  # gen_id -> latency_ms

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_gen_id = {
            executor.submit(fetch_generation_metadata, gen_id, api_key): gen_id
            for gen_id in unique_gen_ids
        }

        completed = 0
        for future in as_completed(future_to_gen_id):
            gen_id = future_to_gen_id[future]
            completed += 1

            if completed % 50 == 0:
                print(f"    Progress: {completed}/{len(unique_gen_ids)}")

            try:
                metadata = future.result()
                if metadata and "latency" in metadata:
                    generation_latencies[gen_id] = metadata["latency"]
            except Exception as e:
                print(f"  Warning: Exception fetching {gen_id}: {e}")

    print(f"  Fetched {len(generation_latencies)} latencies")

    # Aggregate latencies per result (sum across multiple generations for tool calls)
    result_latencies: dict[str, int] = {}
    for result_id, gen_ids in result_generation_ids.items():
        total_latency = 0
        for gen_id in gen_ids:
            if gen_id in generation_latencies:
                total_latency += generation_latencies[gen_id]
        if total_latency > 0:
            result_latencies[result_id] = total_latency

    return result_latencies


def load_json(filepath: Path) -> dict:
    """Load a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_as_dict(filepath: Path) -> dict:
    """Load a CSV file and return as dict keyed by customer_info."""
    result = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer_info = row.get("customer_info", "").strip()
            if customer_info:
                result[customer_info] = row
    return result


def extract_name_from_customer_info(customer_info: str) -> str:
    """Parse customer name from customer_info text."""
    match = re.search(r"Name:\s*(.+?)(?:\n|$)", customer_info)
    return match.group(1).strip() if match else ""


def extract_institution_from_customer_info(customer_info: str) -> str:
    """Parse institution from customer_info text."""
    match = re.search(r"Institution:\s*(.+?)(?:\n|$)", customer_info)
    return match.group(1).strip() if match else ""


def get_model_type(provider_label: str) -> str:
    """Derive model type from provider label."""
    label_upper = provider_label.upper()
    if "HUMAN BASELINE" in label_upper:
        return "human_baseline"
    elif "(WEB)" in label_upper:
        return "web_only"
    elif "(ALL TOOLS)" in label_upper:
        return "all_tools"
    return "unknown"


def is_human_baseline(provider_label: str) -> bool:
    """Check if provider is human baseline."""
    return "HUMAN BASELINE" in provider_label.upper()


def get_test_category(metric_name: str) -> str:
    """Derive test category from metric name."""
    metric_upper = metric_name.upper()
    if "WORK-RELEVANCE" in metric_upper:
        return "work_relevance"
    elif "SOURCE-RELIABILITY" in metric_upper:
        return "source_reliability"
    elif "CLAIM-SUPPORT" in metric_upper:
        return "claim_support"
    elif "FLAG-ACCURACY" in metric_upper:
        return "flag_accuracy"
    return "unknown"


def get_criterion_from_metric(metric_name: str) -> Optional[int]:
    """
    Map metric name to criterion number (1-4).

    Returns:
        1 = Affiliation
        2 = Institution
        3 = Domain
        4 = Sanctions
    """
    metric_upper = metric_name.upper()
    if "AFFILIATION" in metric_upper:
        return 1
    elif "INSTITUTION" in metric_upper:
        return 2
    elif "DOMAIN" in metric_upper:
        return 3
    elif "SANCTIONS" in metric_upper:
        return 4
    return None


def parse_human_baseline_table1(response_text: str) -> dict:
    """
    Parse human baseline Table 1 to extract evidence info per criterion.

    Returns dict mapping criterion number (1-4) to:
        - has_sources: bool (True if not "None")
        - has_evidence: bool (True if evidence text is not empty)
    """
    result = {1: {"has_sources": False, "has_evidence": False},
              2: {"has_sources": False, "has_evidence": False},
              3: {"has_sources": False, "has_evidence": False},
              4: {"has_sources": False, "has_evidence": False}}

    if not response_text:
        return result

    # Find Table 1 section
    table1_match = re.search(r"## Table 1.*?\n\|.*?\n\|[-|]+\n(.*?)(?=\n##|\Z)",
                             response_text, re.DOTALL)
    if not table1_match:
        return result

    table_rows = table1_match.group(1).strip()

    # Parse each row
    for line in table_rows.split("\n"):
        if not line.strip().startswith("|"):
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue

        criterion_text = parts[1]
        sources_text = parts[2]
        evidence_text = parts[3]

        # Determine criterion number
        crit_num = None
        if "1." in criterion_text or "Affiliation" in criterion_text:
            crit_num = 1
        elif "2." in criterion_text or "Institution" in criterion_text:
            crit_num = 2
        elif "3." in criterion_text or "Domain" in criterion_text or "Email" in criterion_text:
            crit_num = 3
        elif "4." in criterion_text or "Sanctions" in criterion_text:
            crit_num = 4

        if crit_num:
            result[crit_num]["has_sources"] = sources_text.lower() != "none" and bool(sources_text)
            result[crit_num]["has_evidence"] = bool(evidence_text.strip())

    return result


def parse_human_baseline_table3(response_text: str) -> dict:
    """
    Parse human baseline Table 3 (Background Work) to check if it has content.

    Returns dict with:
        - has_work: bool (True if there's actual background work, not just "No background work found")
    """
    result = {"has_work": False}

    if not response_text:
        return result

    # Find Table 3 section
    table3_match = re.search(r"## Table 3.*?\n\|.*?\n\|[-|]+\n(.*?)(?=\n##|\Z)",
                             response_text, re.DOTALL)
    if not table3_match:
        return result

    table_content = table3_match.group(1).strip()

    # Check for empty indicators
    empty_indicators = [
        "No background work found",
        "N/A | N/A | None",
    ]

    # If any empty indicator is present, there's no work
    for indicator in empty_indicators:
        if indicator in table_content:
            return result

    # Check if there's at least one row with actual content
    for line in table_content.split("\n"):
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5:
            # Check if relevance level is a number (actual work entry)
            relevance = parts[1].strip()
            if relevance.isdigit() or relevance == "?":
                result["has_work"] = True
                break

    return result


def check_human_baseline_empty_claim_support(
    response_text: str,
    metric_name: str
) -> bool:
    """
    Check if a human baseline claim support test should be marked as FAIL
    due to empty evidence/sources.

    Returns True if the claim support should be overridden to FAIL.
    """
    metric_upper = metric_name.upper()

    # Handle background work separately - check Table 3
    if "BACKGROUND_WORK" in metric_upper:
        table3_info = parse_human_baseline_table3(response_text)
        # If no background work found, this should be FAIL
        return not table3_info.get("has_work", False)

    # For other criteria, check Table 1
    criterion = get_criterion_from_metric(metric_name)
    if criterion is None:
        return False

    table1_info = parse_human_baseline_table1(response_text)
    crit_info = table1_info.get(criterion, {})

    # If no sources and no evidence, this should be FAIL
    if not crit_info.get("has_sources") and not crit_info.get("has_evidence"):
        return True

    return False


def get_ground_truth_column_for_metric(metric_name: str) -> Optional[str]:
    """Map flag accuracy metric to its ground truth column name."""
    metric_upper = metric_name.upper()
    if "AFFILIATION" in metric_upper:
        return "ground_truth_affiliation"
    elif "INSTITUTION" in metric_upper:
        return "ground_truth_institution"
    elif "DOMAIN" in metric_upper:
        return "ground_truth_domain"
    elif "SANCTIONS" in metric_upper:
        return "ground_truth_sanctions"
    return None


def check_flag_accuracy_exact_match(
    extracted_flag: str,
    ground_truth: str
) -> tuple[bool, str]:
    """
    Check if flag accuracy should pass based on exact match logic.

    Rules:
    - If ground truth is UNDETERMINED → any extracted value passes
    - If ground truth is NOT UNDETERMINED → require exact match

    Returns:
        (should_pass, correction_type)
    """
    extracted = (extracted_flag or "").strip().upper()
    gt = (ground_truth or "").strip().upper()

    # If ground truth is UNDETERMINED, any value passes
    if gt == "UNDETERMINED":
        return True, "gt_undetermined_pass"

    # Otherwise, require exact match
    if extracted == gt:
        return True, "exact_match_pass"
    else:
        return False, "exact_match_fail"


def strip_thinking_blocks(text: str) -> str:
    """Remove <thinking>...</thinking> blocks from text."""
    if not text:
        return ""
    return re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL).strip()


def get_source_urls_from_tool_outputs(tool_outputs: dict) -> list:
    """Extract source URLs from tool_outputs dict."""
    urls = []
    if isinstance(tool_outputs, dict):
        for key, value in tool_outputs.items():
            if isinstance(value, dict) and "url" in value:
                urls.append(value["url"])
    return urls


def extract_tool_sources(tool_outputs: dict, tool_result_ids: list = None) -> list:
    """
    Extract comprehensive source information from all tool types.

    Returns a list of dicts with normalized source info:
    - type: 'web', 'epmc', 'orcid', 'orcworks', 'screen', 'human_provided', 'other'
    - id: tool result ID (web1, epmc2, etc.)
    - url: URL if available
    - title: title/name of the source
    - Additional type-specific fields
    """
    sources = []

    if not isinstance(tool_outputs, dict):
        return sources

    # If tool_result_ids provided, only extract those; otherwise extract all
    keys_to_process = tool_result_ids if tool_result_ids else list(tool_outputs.keys())

    for key in keys_to_process:
        if key not in tool_outputs:
            continue

        value = tool_outputs[key]
        if not isinstance(value, dict):
            continue

        source = {"id": key}

        # Determine source type from key prefix
        if key.startswith("web"):
            source["type"] = "web"
            source["url"] = value.get("url", "")
            source["title"] = value.get("title", "")
            # Don't include full content - too large

        elif key.startswith("epmc"):
            source["type"] = "epmc"
            source["title"] = value.get("title", "")
            source["authors"] = value.get("author_string", "")
            source["doi"] = value.get("doi", "")
            source["journal"] = value.get("journal", "")
            source["pub_year"] = value.get("pub_year", "")
            source["cited_by_count"] = value.get("cited_by_count", "")
            # Construct URL from DOI if available
            if value.get("doi"):
                source["url"] = f"https://doi.org/{value['doi']}"
            # Extract matching authors info
            matching = value.get("matching_authors", [])
            if matching:
                source["matching_authors"] = [
                    {
                        "name": f"{a.get('first_name', '')} {a.get('last_name', '')}".strip(),
                        "orcid": a.get("orcid", ""),
                    }
                    for a in matching if isinstance(a, dict)
                ]

        elif key.startswith("orcworks"):
            source["type"] = "orcworks"
            source["orcid_id"] = value.get("orcid_id", "")
            source["url"] = f"https://orcid.org/{value.get('orcid_id', '')}" if value.get("orcid_id") else ""
            source["keywords"] = value.get("keywords", [])
            source["matching_works_count"] = value.get("matching_works_count", 0)
            matching_works = value.get("matching_works", [])
            if matching_works:
                source["matching_works"] = [
                    {"title": w.get("title", ""), "url": w.get("url", "")}
                    for w in matching_works[:5] if isinstance(w, dict)
                ]

        elif key.startswith("orcid"):
            source["type"] = "orcid"
            source["orcid_id"] = value.get("orcid_id", "")
            source["url"] = value.get("orcid_url", "")
            source["name"] = f"{value.get('given_name', '')} {value.get('family_name', '')}".strip()
            source["emails"] = value.get("emails", [])
            source["total_works"] = value.get("total_works_count", 0)
            # Include a few works
            works = value.get("works", [])
            if works:
                source["works"] = [
                    {"title": w.get("title", ""), "url": w.get("url", ""), "year": w.get("publication_date", "")}
                    for w in works[:5] if isinstance(w, dict)
                ]

        elif key.startswith("screen"):
            source["type"] = "screen"
            source["name"] = value.get("name", "")
            source["programs"] = value.get("programs", [])
            source["source"] = value.get("source", "")

        else:
            # Human-provided or other
            source["type"] = value.get("type", "other")
            source["url"] = value.get("url", "")
            source["title"] = value.get("title", "")

        sources.append(source)

    return sources


def hash_customer_info(customer_info: str) -> str:
    """Create a hash of customer_info for matching with ground truth."""
    return hashlib.md5(customer_info.encode()).hexdigest()[:16]


def find_ground_truth_flags(customer_info: str, ground_truth: dict) -> dict:
    """Find ground truth flags for a customer."""
    default_flags = {
        "affiliation": "UNDETERMINED",
        "institution": "UNDETERMINED",
        "domain": "UNDETERMINED",
        "sanctions": "UNDETERMINED",
    }

    records = ground_truth.get("records", {})

    # Try to match by customerInfoPreview
    for record_key, record in records.items():
        preview = record.get("customerInfoPreview", "")
        # Match by prefix (first 50 chars without ellipsis)
        preview_prefix = preview[:50].replace("...", "").strip()
        if preview_prefix and preview_prefix in customer_info:
            return record.get("flags", default_flags)

    return default_flags


def generate_tests_csv(all_results: list, customer_data: dict, ground_truth: dict, output_path: Path):
    """Generate tests.csv with one row per test (assertion) result."""

    fieldnames = [
        "eval_id",
        "result_id",
        "customer_name",
        "customer_institution",
        "customer_type",
        "order",
        "work_url",
        "is_human_baseline_dataset",
        "model_label",
        "model_name",
        "model_type",
        "is_human_baseline",
        "prompt_type",
        "metric_name",
        "test_category",
        "original_pass",  # Original pass value before corrections
        "pass",           # Corrected pass value
        "pass_correction_applied",  # Description of any correction applied
        "reason",
        "extracted_section",
        "num_sources_used",
        "num_web_sources",
        "num_epmc_sources",
        "num_orcid_sources",
        "num_screen_sources",
        "source_urls",
        "sources_json",
        "ground_truth_affiliation",
        "ground_truth_institution",
        "ground_truth_domain",
        "ground_truth_sanctions",
        "extracted_flag",
        "claims_json",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result_info in all_results:
            result = result_info["result"]
            file_meta = result_info["file_meta"]

            customer_info = result.get("vars", {}).get("customer_info", "")
            customer_meta = customer_data.get(customer_info, {})
            gt_flags = find_ground_truth_flags(customer_info, ground_truth)

            provider_label = result.get("provider", {}).get("label", "")
            response = result.get("response", {})
            response_meta = response.get("metadata", {})
            response_text = response.get("output", "")

            # Get tool_outputs from response metadata
            tool_outputs = response_meta.get("tool_outputs", {})

            # Check if this is a human baseline response
            is_hb = is_human_baseline(provider_label)

            # For human baseline corrections: pre-compute sanctions flag accuracy pass
            # by finding it in the component results
            sanctions_flag_accuracy_pass = None
            component_results = result.get("gradingResult", {}).get("componentResults", [])
            for cr in component_results:
                metric_name = cr.get("metricName", "")
                if "SANCTIONS" in metric_name.upper() and "FLAG-ACCURACY" in metric_name.upper():
                    sanctions_flag_accuracy_pass = cr.get("pass", False)
                    break

            # Process each component result (assertion)
            for cr in component_results:
                metric_name = cr.get("metricName", "")

                # Get tool result IDs for this assertion
                tool_result_ids = cr.get("toolResultIds", [])

                # Extract comprehensive source info using the new function
                sources = extract_tool_sources(tool_outputs, tool_result_ids)

                # Also check toolResults in the component result itself
                tool_results = cr.get("toolResults", [])
                for tr in tool_results:
                    if isinstance(tr, dict):
                        tr_id = tr.get("id", "")
                        # Skip if already in sources
                        if any(s.get("id") == tr_id for s in sources):
                            continue
                        # Try to extract URL from nested result
                        result_data = tr.get("result", {})
                        if isinstance(result_data, dict):
                            url = result_data.get("url", "")
                            if url:
                                sources.append({
                                    "id": tr_id,
                                    "type": "web" if tr_id.startswith("web") else "other",
                                    "url": url,
                                    "title": result_data.get("title", ""),
                                })

                # Count sources by type
                num_web = sum(1 for s in sources if s.get("type") == "web")
                num_epmc = sum(1 for s in sources if s.get("type") == "epmc")
                num_orcid = sum(1 for s in sources if s.get("type") in ("orcid", "orcworks"))
                num_screen = sum(1 for s in sources if s.get("type") == "screen")

                # Extract just URLs for backward compatibility
                source_urls = [s.get("url") for s in sources if s.get("url")]

                # Last resort: try source_urls from metadata if we have nothing
                if not source_urls:
                    source_urls = response_meta.get("source_urls", [])

                # Get original pass value
                original_pass = cr.get("pass", False)
                corrected_pass = original_pass
                correction_applied = ""

                # Apply human baseline corrections (only on human baseline dataset subset)
                is_hb_dataset = file_meta["is_human_baseline_dataset"]
                if is_hb and is_hb_dataset:
                    # Correction for CLAIM-SUPPORT tests
                    if "CLAIM-SUPPORT" in metric_name.upper():
                        # Correction 1: Empty claim support fields should be FAIL
                        if check_human_baseline_empty_claim_support(response_text, metric_name):
                            corrected_pass = False
                            correction_applied = "empty_evidence_fail"

                        # Correction 2: Sanctions claim support should use exact match criteria
                        # (same logic as flag accuracy: exact match unless GT is UNDETERMINED)
                        if "SANCTIONS" in metric_name.upper():
                            # Find sanctions flag extracted value from component results
                            sanctions_extracted_flag = None
                            for cr_inner in component_results:
                                if "SANCTIONS" in cr_inner.get("metricName", "").upper() and \
                                   "FLAG-ACCURACY" in cr_inner.get("metricName", "").upper():
                                    sanctions_extracted_flag = cr_inner.get("extractedFlag", "")
                                    break

                            if sanctions_extracted_flag is not None:
                                gt_sanctions = gt_flags.get("sanctions", "UNDETERMINED")
                                sanctions_exact_pass, _ = check_flag_accuracy_exact_match(
                                    sanctions_extracted_flag, gt_sanctions
                                )
                                corrected_pass = sanctions_exact_pass
                                if corrected_pass != original_pass:
                                    correction_applied = "sanctions_exact_match"
                                elif correction_applied == "":
                                    correction_applied = "sanctions_exact_match_no_change"

                # Correction for FLAG-ACCURACY tests (applies to all models, all datasets)
                # Rules:
                # - If ground truth is UNDETERMINED → pass (no ground truth available)
                # - Otherwise, require exact match (FLAG=FLAG or NO FLAG=NO FLAG)
                if "FLAG-ACCURACY" in metric_name.upper():
                    # Get the ground truth column for this metric
                    gt_col = get_ground_truth_column_for_metric(metric_name)
                    if gt_col:
                        ground_truth_val = gt_flags.get(gt_col.replace("ground_truth_", ""), "UNDETERMINED")
                        extracted_flag = cr.get("extractedFlag", "")

                        # Apply exact match logic
                        corrected_pass, correction_applied = check_flag_accuracy_exact_match(
                            extracted_flag, ground_truth_val
                        )

                row = {
                    "eval_id": result_info["eval_id"],
                    "result_id": result.get("id", ""),
                    "customer_name": customer_meta.get("Name", extract_name_from_customer_info(customer_info)),
                    "customer_institution": customer_meta.get("Institution", extract_institution_from_customer_info(customer_info)),
                    "customer_type": customer_meta.get("Type", ""),
                    "order": customer_meta.get("Order", ""),
                    "work_url": result.get("vars", {}).get("work_url", ""),
                    "is_human_baseline_dataset": file_meta["is_human_baseline_dataset"],
                    "model_label": provider_label,
                    "model_name": response_meta.get("model", ""),
                    "model_type": get_model_type(provider_label),
                    "is_human_baseline": is_hb,
                    "prompt_type": file_meta["prompt_type"],
                    "metric_name": metric_name,
                    "test_category": get_test_category(metric_name),
                    "original_pass": original_pass,
                    "pass": corrected_pass,
                    "pass_correction_applied": correction_applied,
                    "reason": cr.get("reason", ""),
                    "extracted_section": cr.get("extractedSection", ""),
                    "num_sources_used": len(sources),
                    "num_web_sources": num_web,
                    "num_epmc_sources": num_epmc,
                    "num_orcid_sources": num_orcid,
                    "num_screen_sources": num_screen,
                    "source_urls": json.dumps(source_urls) if source_urls else "",
                    "sources_json": json.dumps(sources) if sources else "",
                    "ground_truth_affiliation": gt_flags.get("affiliation", "UNDETERMINED"),
                    "ground_truth_institution": gt_flags.get("institution", "UNDETERMINED"),
                    "ground_truth_domain": gt_flags.get("domain", "UNDETERMINED"),
                    "ground_truth_sanctions": gt_flags.get("sanctions", "UNDETERMINED"),
                    "extracted_flag": cr.get("extractedFlag", ""),
                    "claims_json": json.dumps(cr.get("claims", [])) if cr.get("claims") else "",
                }
                writer.writerow(row)

    print(f"Generated: {output_path}")


def generate_responses_csv(
    all_results: list,
    customer_data: dict,
    output_path: Path,
    result_latencies: Optional[dict[str, int]] = None,
):
    """Generate responses.csv with one row per model response."""
    result_latencies = result_latencies or {}

    fieldnames = [
        "eval_id",
        "result_id",
        "customer_name",
        "customer_institution",
        "customer_type",
        "order",
        "is_human_baseline_dataset",
        "model_label",
        "model_name",
        "model_type",
        "is_human_baseline",
        "prompt_type",
        "full_response",
        "response_length",
        "latency_ms",
        "total_cost",
        "model_cost",
        "web_search_cost",
        "num_web_searches",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "num_sources",
        "num_web_sources",
        "num_epmc_sources",
        "num_orcid_sources",
        "num_screen_sources",
        "source_urls",
        "sources_json",
        "num_assertions",
        "num_assertions_passed",
        "time_to_complete_minutes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result_info in all_results:
            result = result_info["result"]
            file_meta = result_info["file_meta"]

            customer_info = result.get("vars", {}).get("customer_info", "")
            customer_meta = customer_data.get(customer_info, {})

            provider_label = result.get("provider", {}).get("label", "")
            response = result.get("response", {})
            response_meta = response.get("metadata", {})
            token_usage = response.get("tokenUsage", {})

            # Get full response with thinking stripped
            full_response = strip_thinking_blocks(response.get("output", ""))

            # Get all sources using comprehensive extraction
            tool_outputs = response_meta.get("tool_outputs", {})
            sources = extract_tool_sources(tool_outputs)

            # Count by type
            num_web = sum(1 for s in sources if s.get("type") == "web")
            num_epmc = sum(1 for s in sources if s.get("type") == "epmc")
            num_orcid = sum(1 for s in sources if s.get("type") in ("orcid", "orcworks"))
            num_screen = sum(1 for s in sources if s.get("type") == "screen")

            # Extract URLs for backward compatibility
            source_urls = [s.get("url") for s in sources if s.get("url")]
            if not source_urls:
                source_urls = response_meta.get("source_urls", [])

            # Count assertions
            component_results = result.get("gradingResult", {}).get("componentResults", [])
            num_assertions = len(component_results)
            num_passed = sum(1 for cr in component_results if cr.get("pass", False))

            row = {
                "eval_id": result_info["eval_id"],
                "result_id": result.get("id", ""),
                "customer_name": customer_meta.get("Name", extract_name_from_customer_info(customer_info)),
                "customer_institution": customer_meta.get("Institution", extract_institution_from_customer_info(customer_info)),
                "customer_type": customer_meta.get("Type", ""),
                "order": customer_meta.get("Order", ""),
                "is_human_baseline_dataset": file_meta["is_human_baseline_dataset"],
                "model_label": provider_label,
                "model_name": response_meta.get("model", ""),
                "model_type": get_model_type(provider_label),
                "is_human_baseline": is_human_baseline(provider_label),
                "prompt_type": file_meta["prompt_type"],
                "full_response": full_response,
                "response_length": len(full_response),
                # Use fetched OpenRouter latency (accurate), fall back to PromptFoo latency
                "latency_ms": result_latencies.get(result.get("id", ""), None),
                "total_cost": result.get("cost", 0) or response.get("cost", 0),
                "model_cost": response.get("model_cost", ""),
                "web_search_cost": response.get("web_search_cost", ""),
                "num_web_searches": response_meta.get("num_web_searches", 0) or 0,
                "prompt_tokens": token_usage.get("prompt", 0),
                "completion_tokens": token_usage.get("completion", 0),
                "total_tokens": token_usage.get("total", 0),
                "num_sources": len(sources),
                "num_web_sources": num_web,
                "num_epmc_sources": num_epmc,
                "num_orcid_sources": num_orcid,
                "num_screen_sources": num_screen,
                "source_urls": json.dumps(source_urls) if source_urls else "",
                "sources_json": json.dumps(sources) if sources else "",
                "num_assertions": num_assertions,
                "num_assertions_passed": num_passed,
                "time_to_complete_minutes": response_meta.get("time_to_complete_minutes", ""),
            }
            writer.writerow(row)

    print(f"Generated: {output_path}")


def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()
    
    print("Loading reference datasets...")

    # Load customer metadata from both CSVs
    full_customers = load_csv_as_dict(FULL_DATASET)
    human_baseline_customers = load_csv_as_dict(HUMAN_BASELINE_DATASET)

    # Merge customer data (human baseline may have different customers)
    customer_data = {**full_customers, **human_baseline_customers}
    print(f"  Loaded {len(customer_data)} unique customers from reference CSVs")

    # Load ground truth flags
    ground_truth = load_json(GROUND_TRUTH_FILE)
    print(f"  Loaded {len(ground_truth.get('records', {}))} ground truth records")

    # Load all result files
    print("\nLoading result files...")
    all_results = []

    for filename, file_meta in RESULT_FILES.items():
        filepath = RESULTS_DIR / filename
        if not filepath.exists():
            print(f"  WARNING: {filename} not found, skipping")
            continue

        data = load_json(filepath)
        eval_id = data.get("evalId", "")
        results = data.get("results", {}).get("results", [])

        print(f"  {filename}: {len(results)} results")

        for result in results:
            all_results.append({
                "result": result,
                "eval_id": eval_id,
                "file_meta": file_meta,
            })

    print(f"\nTotal results to process: {len(all_results)}")

    # Fetch latencies from OpenRouter API in parallel
    print("\nFetching latencies from OpenRouter...")
    result_latencies = fetch_all_generation_latencies(all_results)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate datasets
    print("\nGenerating datasets...")
    generate_tests_csv(all_results, customer_data, ground_truth, OUTPUT_DIR / "tests.csv")
    generate_responses_csv(all_results, customer_data, OUTPUT_DIR / "responses.csv", result_latencies)

    print("\nDone!")


if __name__ == "__main__":
    main()
