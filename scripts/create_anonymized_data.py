#!/usr/bin/env python3
"""
Create an anonymized copy of all data needed to reproduce paper figures and metrics.

Produces data_anonymized/ with:
  - data/customers/{full_dataset,human_baseline_subset}.csv  (PII hashed/dropped)
  - data/annotations/*.json  (PII fields stripped where present)
  - data/token_pricing.yaml  (copied as-is)
  - processed/tests.csv      (PII columns hashed/dropped)
  - processed/responses.csv  (PII columns hashed/dropped)

Excluded entirely:
  - data/raw_results/  (886 MB of full AI response transcripts)
  - processed/blind_grading/  (contains AI response text with customer names)

Usage:
    uv run python scripts/create_anonymized_data.py
"""

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent.parent
OUT_DIR = BASE_DIR / "data_anonymized"


def hash_value(value: str, prefix: str = "anon") -> str:
    """Deterministic hash: sha256(value.strip().lower()) → prefix_<first 12 hex chars>."""
    if pd.isna(value) or str(value).strip() == "":
        return ""
    normalized = str(value).strip().lower().encode()
    digest = hashlib.sha256(normalized).hexdigest()[:12]
    return f"{prefix}_{digest}"


def anonymize_email(email: str) -> str:
    """Strip user part, keep domain for institutional classification (N3).

    Handles formats:
      - user@domain.edu        → @domain.edu
      - Verified email at x.ac → Verified email at x.ac  (already domain-only)
      - Not provided           → Not provided
    """
    if pd.isna(email) or str(email).strip() == "":
        return ""
    email = str(email).strip()
    if "@" in email:
        domain = email.split("@")[-1]
        return f"@{domain}"
    # "Verified email at ..." and "Not provided" — no user-level PII
    return email


def anonymize_customer_csv(src: Path, dst: Path) -> None:
    """Anonymize a customer CSV (full_dataset or human_baseline_subset)."""
    df = pd.read_csv(src)
    df["Name"] = df["Name"].apply(lambda v: hash_value(v, "anon"))
    df["Email"] = df["Email"].apply(anonymize_email)
    df["Institution"] = df["Institution"].apply(lambda v: hash_value(v, "inst"))
    # Drop columns with PII
    df = df.drop(columns=["work_url", "customer_info"], errors="ignore")
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False)
    print(f"  {dst.relative_to(OUT_DIR)}  ({len(df)} rows)")


def anonymize_tests_csv(src: Path, dst: Path) -> None:
    """Anonymize processed/tests.csv."""
    df = pd.read_csv(src, low_memory=False)
    df["customer_name"] = df["customer_name"].apply(lambda v: hash_value(v, "anon"))
    df["customer_institution"] = df["customer_institution"].apply(
        lambda v: hash_value(v, "inst")
    )
    drop_cols = [
        "work_url",
        "reason",
        "extracted_section",
        "source_urls",
        "sources_json",
        "claims_json",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False)
    print(f"  {dst.relative_to(OUT_DIR)}  ({len(df)} rows)")


def anonymize_responses_csv(src: Path, dst: Path) -> None:
    """Anonymize processed/responses.csv."""
    df = pd.read_csv(src, low_memory=False)
    df["customer_name"] = df["customer_name"].apply(lambda v: hash_value(v, "anon"))
    df["customer_institution"] = df["customer_institution"].apply(
        lambda v: hash_value(v, "inst")
    )
    drop_cols = ["order", "full_response", "source_urls", "sources_json"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False)
    print(f"  {dst.relative_to(OUT_DIR)}  ({len(df)} rows)")


def anonymize_ground_truth_flags(src: Path, dst: Path) -> None:
    """Strip customerInfoPreview and notes from ground_truth_flags.json."""
    with open(src) as f:
        data = json.load(f)
    for _key, record in data.get("records", {}).items():
        record.pop("customerInfoPreview", None)
        record.pop("notes", None)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w") as f:
        json.dump(data, f, indent=2)
    n = len(data.get("records", {}))
    print(f"  {dst.relative_to(OUT_DIR)}  ({n} records)")


def anonymize_flag_error_comments(src: Path, dst: Path) -> None:
    """Strip PII fields from flag_error_comments.json records."""
    with open(src) as f:
        data = json.load(f)

    keep_keys = {
        "id",
        "timestamp",
        "lastUpdated",
        "provider",
        "flagType",
        "extractedFlag",
        "groundTruthFlag",
        "metricName",
        "errorCategory",
        "isCorrectProvider",
    }
    cleaned = []
    for record in data.get("records", []):
        cleaned.append({k: v for k, v in record.items() if k in keep_keys})
    data["records"] = cleaned

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  {dst.relative_to(OUT_DIR)}  ({len(cleaned)} records)")


def copy_file(src: Path, dst: Path) -> None:
    """Copy a file as-is."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {dst.relative_to(OUT_DIR)}  (copied)")


def main() -> None:
    print(f"Creating anonymized data in {OUT_DIR}/\n")

    # Clean output directory
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    # Customer CSVs
    print("Customer CSVs:")
    anonymize_customer_csv(
        BASE_DIR / "data" / "customers" / "full_dataset.csv",
        OUT_DIR / "data" / "customers" / "full_dataset.csv",
    )
    anonymize_customer_csv(
        BASE_DIR / "data" / "customers" / "human_baseline_subset.csv",
        OUT_DIR / "data" / "customers" / "human_baseline_subset.csv",
    )

    # Processed CSVs
    print("\nProcessed CSVs:")
    anonymize_tests_csv(
        BASE_DIR / "processed" / "tests.csv",
        OUT_DIR / "processed" / "tests.csv",
    )
    anonymize_responses_csv(
        BASE_DIR / "processed" / "responses.csv",
        OUT_DIR / "processed" / "responses.csv",
    )

    # Annotations
    print("\nAnnotations:")
    anonymize_ground_truth_flags(
        BASE_DIR / "data" / "annotations" / "ground_truth_flags.json",
        OUT_DIR / "data" / "annotations" / "ground_truth_flags.json",
    )
    anonymize_flag_error_comments(
        BASE_DIR / "data" / "annotations" / "flag_error_comments.json",
        OUT_DIR / "data" / "annotations" / "flag_error_comments.json",
    )
    copy_file(
        BASE_DIR / "data" / "annotations" / "blind_gradings.json",
        OUT_DIR / "data" / "annotations" / "blind_gradings.json",
    )
    copy_file(
        BASE_DIR / "data" / "annotations" / "agreements.json",
        OUT_DIR / "data" / "annotations" / "agreements.json",
    )

    # Token pricing
    print("\nOther:")
    copy_file(
        BASE_DIR / "data" / "token_pricing.yaml",
        OUT_DIR / "data" / "token_pricing.yaml",
    )

    print("\nDone. Verify with:")
    print("  1. Temporarily swap data/ and processed/ with anonymized versions")
    print("  2. make figures && make metrics")
    print("  3. Restore originals")


if __name__ == "__main__":
    main()
