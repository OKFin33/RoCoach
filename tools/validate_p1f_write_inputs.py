#!/usr/bin/env python3
"""Validate that a P1e importer dry-run is eligible for SQLite write-path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validate_p1e_importer_artifacts import iter_jsonl, load_json, validate_artifacts


ALLOWED_STRUCTURED_SUPPLEMENT_FORMATS = {"yaml", "yml", "json"}


def validate_write_inputs(importer_run_dir: Path) -> dict[str, Any]:
    validate_artifacts(importer_run_dir)
    manifest = load_json(importer_run_dir / "importer_run_manifest.json")

    supplement_format = manifest.get("supplement_format")
    if supplement_format not in ALLOWED_STRUCTURED_SUPPLEMENT_FORMATS:
        raise ValueError(
            f"Structured supplement required for write-path, got supplement_format={supplement_format!r}"
        )

    unresolved = iter_jsonl(importer_run_dir / "unresolved_entities.jsonl")
    if unresolved:
        raise ValueError("Write-path blocked: unresolved_entities.jsonl is not empty")

    excluded = iter_jsonl(importer_run_dir / "excluded_entities.jsonl")
    bad_exclusions = [
        row
        for row in excluded
        if row.get("resolution_status") != "excluded" or row.get("canonical_source_layer") != "manual_supplement"
    ]
    if bad_exclusions:
        raise ValueError("Write-path blocked: excluded entities must be policy-backed manual supplement exclusions")

    review_required = iter_jsonl(importer_run_dir / "review_required_entities.jsonl")
    review_keys = {(row["entity_type"], row["entity_key"]) for row in review_required}

    included_payloads = []
    for filename in ("resolved_species_forms.jsonl", "resolved_moves.jsonl", "resolved_derived_abilities.jsonl"):
        included_payloads.extend(iter_jsonl(importer_run_dir / filename))

    collisions = [
        (row["entity_type"], row["entity_key"])
        for row in included_payloads
        if (row["entity_type"], row["entity_key"]) in review_keys
    ]
    if collisions:
        raise ValueError(f"Write-path blocked: review-required entities leaked into included payloads: {collisions[:5]}")

    supplement_backed = iter_jsonl(importer_run_dir / "supplement_backed_entities.jsonl")
    for row in supplement_backed:
        if row.get("canonical_source_layer") != "manual_supplement":
            raise ValueError("Write-path blocked: supplement-backed row missing manual_supplement source layer")
        if not row.get("supplement_refs"):
            raise ValueError("Write-path blocked: supplement-backed row missing supplement_refs")

    return {
        "importer_run_dir": str(importer_run_dir),
        "importer_run_id": manifest["run_id"],
        "canonical_artifact_dir": manifest["canonical_artifact_dir"],
        "canonical_run_id": manifest["canonical_run_id"],
        "supplement_path": manifest["supplement_path"],
        "supplement_format": supplement_format,
        "counts": manifest["counts"],
        "eligible_for_write": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate P1e importer dry-run inputs for SQLite write-path.")
    parser.add_argument("importer_run_dir", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = validate_write_inputs(args.importer_run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
