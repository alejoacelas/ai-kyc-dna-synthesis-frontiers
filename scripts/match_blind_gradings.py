#!/usr/bin/env python3
"""
Match blind gradings with test/assertions data from human_baseline_subset_main.json.

The blind gradings were generated using two different filters during annotation:
- Filter A (all_non_flag): !FLAG-ACCURACY only (shows all 8 non-FLAG assertions)
- Filter B (fail_only): !FLAG-ACCURACY && !pass (only shows failing non-FLAG assertions)

Entries WITH metricName use Filter B, entries WITHOUT metricName use Filter A.
"""

import json
from pathlib import Path
from collections import Counter
from typing import Any


def load_json(path: Path) -> Any:
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def is_flag_accuracy(metric_name: str) -> bool:
    """Check if metric is a FLAG-ACCURACY type."""
    return "FLAG-ACCURACY" in metric_name


def apply_filter_a(component_results: list[dict]) -> list[dict]:
    """Filter A: all_non_flag - exclude FLAG-ACCURACY, keep all others."""
    return [cr for cr in component_results if not is_flag_accuracy(cr.get("metricName", ""))]


def apply_filter_b(component_results: list[dict]) -> list[dict]:
    """Filter B: fail_only - exclude FLAG-ACCURACY AND passing results."""
    return [
        cr for cr in component_results
        if not is_flag_accuracy(cr.get("metricName", "")) and not cr.get("pass", True)
    ]


def truncate_text(text: str, max_len: int = 500) -> str:
    """Truncate text with ellipsis if too long."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def compute_cohens_kappa(ai_labels: list[bool], human_labels: list[bool]) -> dict:
    """
    Compute Cohen's Kappa coefficient for inter-rater agreement.

    Returns dict with kappa value and contingency table counts.
    """
    if len(ai_labels) != len(human_labels):
        raise ValueError("Label lists must have same length")

    n = len(ai_labels)
    if n == 0:
        return {"kappa": None, "n": 0, "reason": "No samples to compare"}

    # Build contingency table
    # Rows = AI (pass/fail), Cols = Human (pass/fail)
    # true_pos: both pass, true_neg: both fail
    # ai_pass_human_fail, ai_fail_human_pass
    both_pass = sum(1 for a, h in zip(ai_labels, human_labels) if a and h)
    both_fail = sum(1 for a, h in zip(ai_labels, human_labels) if not a and not h)
    ai_pass_human_fail = sum(1 for a, h in zip(ai_labels, human_labels) if a and not h)
    ai_fail_human_pass = sum(1 for a, h in zip(ai_labels, human_labels) if not a and h)

    # Observed agreement
    po = (both_pass + both_fail) / n

    # Marginal sums
    ai_pass = both_pass + ai_pass_human_fail
    ai_fail = both_fail + ai_fail_human_pass
    human_pass = both_pass + ai_fail_human_pass
    human_fail = both_fail + ai_pass_human_fail

    # Expected agreement by chance
    pe = ((ai_pass * human_pass) + (ai_fail * human_fail)) / (n * n)

    # Cohen's Kappa
    if pe == 1:
        kappa = 1.0 if po == 1 else 0.0
    else:
        kappa = (po - pe) / (1 - pe)

    return {
        "kappa": round(kappa, 4),
        "n": n,
        "observed_agreement": round(po, 4),
        "expected_agreement": round(pe, 4),
        "contingency_table": {
            "both_pass": both_pass,
            "both_fail": both_fail,
            "ai_pass_human_fail": ai_pass_human_fail,
            "ai_fail_human_pass": ai_fail_human_pass
        },
        "marginals": {
            "ai_pass": ai_pass,
            "ai_fail": ai_fail,
            "human_pass": human_pass,
            "human_fail": human_fail
        }
    }


def main():
    # Define paths
    base_dir = Path(__file__).parent.parent
    blind_gradings_path = base_dir / "data" / "annotations" / "blind_gradings.json"
    results_path = base_dir / "data" / "raw_results" / "human_baseline_subset_main.json"
    output_path = base_dir / "data" / "processed" / "blind_gradings_matched.json"

    # Load data
    print("Loading data files...")
    blind_gradings = load_json(blind_gradings_path)
    results_data = load_json(results_path)

    results_array = results_data["results"]["results"]
    print(f"Loaded {len(blind_gradings)} blind gradings and {len(results_array)} results")

    # Process each blind grading entry
    matched_entries = []
    unmatched_entries = []

    # For Cohen's Kappa calculation (only on entries with pass/fail status, not ungraded)
    ai_labels = []
    human_labels = []

    # Counters
    filter_a_count = 0
    filter_b_count = 0

    for i, grading in enumerate(blind_gradings):
        original_idx = grading["originalIndex"]
        assertion_idx = grading["assertionIndex"]
        stored_metric = grading.get("metricName")
        status = grading.get("status", "ungraded")
        test_id = grading["testId"]

        # Get the result at originalIndex
        if original_idx >= len(results_array):
            unmatched_entries.append({
                "originalEntryIndex": i,
                "originalIndex": original_idx,
                "assertionIndex": assertion_idx,
                "reason": f"originalIndex {original_idx} exceeds results array length {len(results_array)}"
            })
            continue

        result = results_array[original_idx]
        component_results = result.get("gradingResult", {}).get("componentResults", [])

        # Apply appropriate filter based on whether metricName is present
        if stored_metric:
            # Filter B: fail_only
            filtered = apply_filter_b(component_results)
            filter_used = "fail_only"
            filter_b_count += 1
        else:
            # Filter A: all_non_flag
            filtered = apply_filter_a(component_results)
            filter_used = "all_non_flag"
            filter_a_count += 1

        # Check if assertionIndex is valid for filtered list
        if assertion_idx >= len(filtered):
            unmatched_entries.append({
                "originalEntryIndex": i,
                "originalIndex": original_idx,
                "assertionIndex": assertion_idx,
                "filterUsed": filter_used,
                "filteredLength": len(filtered),
                "reason": f"assertionIndex {assertion_idx} exceeds filtered range 0-{len(filtered)-1 if filtered else 0}"
            })
            continue

        # Get the matching component result
        component = filtered[assertion_idx]
        computed_metric = component.get("metricName", "")

        # Verify metricName matches (if stored)
        if stored_metric and stored_metric != computed_metric:
            unmatched_entries.append({
                "originalEntryIndex": i,
                "originalIndex": original_idx,
                "assertionIndex": assertion_idx,
                "filterUsed": filter_used,
                "storedMetricName": stored_metric,
                "computedMetricName": computed_metric,
                "reason": f"metricName mismatch: stored '{stored_metric}' != computed '{computed_metric}'"
            })
            continue

        # Extract test case info
        test_case = result.get("testCase", {})
        vars_data = test_case.get("vars", result.get("vars", {}))
        customer_name = vars_data.get("Name", "")
        test_type = vars_data.get("Type", "")

        # Extract provider
        provider_info = result.get("provider", {})
        provider = provider_info.get("label", provider_info.get("id", ""))

        # Extract response
        response_obj = result.get("response", {})
        model_response = response_obj.get("output", "")

        # Build matched entry
        entry = {
            "testId": test_id,
            "customerName": customer_name,
            "testType": test_type,
            "provider": provider,
            "metricName": computed_metric,
            "originalComponentIndex": component_results.index(component) if component in component_results else assertion_idx,
            "aiGradingPass": component.get("pass", False),
            "aiGradingReason": truncate_text(component.get("reason", ""), 300),
            "blindGradingStatus": status,
            "blindGradingComment": grading.get("comment", ""),
            "extractedModelResponse": truncate_text(model_response, 500),
            "timestamp": grading.get("timestamp", ""),
            "matchedUsing": filter_used,
            "originalIndex": original_idx,
            "assertionIndex": assertion_idx
        }
        matched_entries.append(entry)

        # Collect labels for Cohen's Kappa (only for pass/fail status, not ungraded)
        if status in ("pass", "fail"):
            ai_labels.append(component.get("pass", False))
            human_labels.append(status == "pass")

    # Compute statistics
    status_counts = Counter(e["blindGradingStatus"] for e in matched_entries)

    # Compute Cohen's Kappa
    kappa_result = compute_cohens_kappa(ai_labels, human_labels)

    # Build output
    output = {
        "entries": matched_entries,
        "unmatchedEntries": unmatched_entries,
        "summary": {
            "total": len(blind_gradings),
            "matched": len(matched_entries),
            "unmatched": len(unmatched_entries),
            "statusCounts": dict(status_counts),
            "filterCounts": {
                "all_non_flag": filter_a_count,
                "fail_only": filter_b_count
            },
            "cohensKappa": kappa_result
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults:")
    print(f"  Matched entries: {len(matched_entries)}")
    print(f"  Unmatched entries: {len(unmatched_entries)}")
    print(f"  Status counts: {dict(status_counts)}")
    print(f"  Filter A (all_non_flag): {filter_a_count}")
    print(f"  Filter B (fail_only): {filter_b_count}")
    print(f"\nCohen's Kappa (AI vs Human):")
    print(f"  Kappa: {kappa_result['kappa']}")
    print(f"  N (pass/fail only): {kappa_result['n']}")
    print(f"  Observed agreement: {kappa_result['observed_agreement']}")
    print(f"  Contingency table: {kappa_result['contingency_table']}")
    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
