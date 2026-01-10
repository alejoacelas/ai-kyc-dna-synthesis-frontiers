#!/usr/bin/env python3
"""
Merge blind grading results with original test data.

This script takes the blind_gradings.json file (output from the blind grading viewer)
and merges it with the original evaluation results to create a processed CSV file
that can be used for analysis.

Output columns:
- evalId: The evaluation ID
- testId: The test ID
- assertionIndex: The assertion index within the test
- originalIndex: The original index in the results array
- metricName: The metric being evaluated
- customerInfo: The customer information (Name, Institution, Email)
- provider: The model/provider used
- originalPass: Whether the original grading passed (true/false)
- blindGradingStatus: The blind grading status (pass/fail/ungraded)
- blindComment: Any comment added during blind grading
- timeSpentMs: Time spent on this grading (if recorded)
- agreement: Whether blind grading agrees with original (agree/disagree/ungraded)
"""

import json
import csv
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def extract_customer_name(customer_info: str) -> str:
    """Extract customer name from customer_info string."""
    for line in customer_info.split('\n'):
        if line.startswith('Name:'):
            return line.replace('Name:', '').strip()
    return 'Unknown'


def find_assertion_by_metric_name(component_results: list, metric_name: str) -> tuple[int, dict] | None:
    """Find an assertion by its metric name. Returns (index, assertion) or None."""
    for i, comp in enumerate(component_results):
        if comp.get('metricName', '') == metric_name:
            return (i, comp)
    return None


def main():
    # Paths
    data_dir = Path(__file__).parent.parent / 'data'
    results_dir = data_dir / 'results'
    blind_gradings_path = data_dir / 'blind_gradings.json'
    output_path = data_dir / 'processed' / 'blind_grading_results.csv'

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load blind gradings
    if not blind_gradings_path.exists():
        print(f"No blind gradings found at {blind_gradings_path}")
        print("Run the blind grading viewer first to create grading data.")
        return

    blind_gradings = load_json(blind_gradings_path)
    print(f"Loaded {len(blind_gradings)} blind grading records")

    # Find all result files and load them
    all_results: dict[str, dict] = {}
    for result_file in results_dir.glob('*.json'):
        try:
            results = load_json(result_file)
            eval_id = results.get('evalId', '')
            if eval_id:
                all_results[eval_id] = results
                print(f"Loaded results from {result_file.name}: evalId={eval_id}")
        except Exception as e:
            print(f"Error loading {result_file}: {e}")

    # Build the merged output
    rows = []
    for grading in blind_gradings:
        eval_id = grading['evalId']
        test_id = grading['testId']
        assertion_index = grading['assertionIndex']
        metric_name = grading.get('metricName', '')  # New field for reliable matching

        # Find the original result
        if eval_id not in all_results:
            print(f"Warning: Could not find results for evalId={eval_id}")
            continue

        results_data = all_results[eval_id]
        test_results = results_data.get('results', {}).get('results', [])

        # Find the test by ID
        original_test = None
        for test in test_results:
            if test.get('id') == test_id:
                original_test = test
                break

        if not original_test:
            print(f"Warning: Could not find test with id={test_id}")
            continue

        component_results = original_test.get('gradingResult', {}).get('componentResults', [])

        # Try to match by metricName first (new reliable method)
        assertion = None
        original_assertion_index = -1

        if metric_name:
            result = find_assertion_by_metric_name(component_results, metric_name)
            if result:
                original_assertion_index, assertion = result
            else:
                print(f"Warning: Could not find assertion with metricName={metric_name} for test {test_id}")
                continue
        else:
            # Fallback for old records without metricName: use assertionIndex
            # Filter out FLAG-ACCURACY metrics (same logic as old viewer)
            filtered_results = [
                (i, comp) for i, comp in enumerate(component_results)
                if 'FLAG-ACCURACY' not in comp.get('metricName', '').upper()
            ]

            if assertion_index >= len(filtered_results):
                print(f"Warning: Assertion index {assertion_index} out of range for test {test_id}")
                continue

            original_assertion_index, assertion = filtered_results[assertion_index]

        # Get customer info
        customer_info = original_test.get('vars', {}).get('customer_info', '')
        customer_name = extract_customer_name(customer_info)

        # Get provider
        provider = original_test.get('provider', {}).get('label', 'Unknown')

        # Get original pass status
        original_pass = assertion.get('pass', False)

        # Get blind grading status
        blind_status = grading.get('status', 'ungraded')

        # Determine agreement
        if blind_status == 'ungraded':
            agreement = 'ungraded'
        elif (blind_status == 'pass' and original_pass) or (blind_status == 'fail' and not original_pass):
            agreement = 'agree'
        else:
            agreement = 'disagree'

        row = {
            'evalId': eval_id,
            'testId': test_id,
            'assertionIndex': assertion_index,
            'originalIndex': grading.get('originalIndex', -1),
            'metricName': assertion.get('metricName', ''),
            'customerName': customer_name,
            'customerInfo': customer_info.replace('\n', ' | '),
            'provider': provider,
            'originalPass': str(original_pass).lower(),
            'blindGradingStatus': blind_status,
            'blindComment': grading.get('comment', ''),
            'timeSpentMs': grading.get('timeSpentMs', ''),
            'agreement': agreement,
            'timestamp': grading.get('timestamp', ''),
        }
        rows.append(row)

    # Sort by evalId, testId, assertionIndex
    rows.sort(key=lambda r: (r['evalId'], r['testId'], r['assertionIndex']))

    # Write to CSV
    if rows:
        fieldnames = [
            'evalId', 'testId', 'assertionIndex', 'originalIndex',
            'metricName', 'customerName', 'customerInfo', 'provider',
            'originalPass', 'blindGradingStatus', 'blindComment',
            'timeSpentMs', 'agreement', 'timestamp'
        ]

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nWrote {len(rows)} rows to {output_path}")

        # Print summary
        agree_count = sum(1 for r in rows if r['agreement'] == 'agree')
        disagree_count = sum(1 for r in rows if r['agreement'] == 'disagree')
        ungraded_count = sum(1 for r in rows if r['agreement'] == 'ungraded')
        print(f"\nSummary:")
        print(f"  Agree: {agree_count}")
        print(f"  Disagree: {disagree_count}")
        print(f"  Ungraded: {ungraded_count}")
        if agree_count + disagree_count > 0:
            agreement_rate = agree_count / (agree_count + disagree_count) * 100
            print(f"  Agreement rate: {agreement_rate:.1f}%")
    else:
        print("No rows to write - no matching gradings found")


if __name__ == '__main__':
    main()
