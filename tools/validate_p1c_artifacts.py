#!/usr/bin/env python3
"""Validate P1c/P1d dry-run artifact shape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


REQUIRED_FILES = {
    "run_manifest.json": "json",
    "source_pages.jsonl": "jsonl",
    "raw_template_snapshots.jsonl": "jsonl",
    "species_form_candidates.jsonl": "jsonl",
    "move_candidates.jsonl": "jsonl",
    "derived_ability_candidates.jsonl": "jsonl",
    "species_move_pool_candidates.jsonl": "jsonl",
    "validation_events.jsonl": "jsonl",
    "rejected_fields.jsonl": "jsonl",
    "dry_run_diff.json": "json",
    "summary.md": "text",
}

REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "started_at",
    "finished_at",
    "run_mode",
    "api_base_url",
    "parser_version",
    "schema_version",
    "field_alignment_matrix_version",
    "scopes",
    "limits",
    "artifact_files",
    "counts",
    "validation_summary",
    "hard_reject_count",
    "warning_count",
    "status",
    "failure_reason",
    "fetch_strategy",
}

REQUIRED_FIELDS = {
    "source_pages.jsonl": {
        "run_id",
        "source_page_id",
        "entity_hint",
        "page_title",
        "page_url",
        "revision_id",
        "revision_timestamp",
        "fetched_at",
        "content_sha256",
        "content_length",
        "parser_version",
        "fetch_status",
    },
    "raw_template_snapshots.jsonl": {
        "run_id",
        "snapshot_id",
        "source_page_id",
        "template_name",
        "raw_fields",
        "field_order",
        "extraction_warnings",
    },
    "species_form_candidates.jsonl": {
        "run_id",
        "species_id",
        "display_name",
        "initial_species_name",
        "form_name",
        "regional_form_name",
        "evolution_stage",
        "primary_type",
        "secondary_type",
        "base_stats",
        "ability_name",
        "ability_effect_text",
        "source_page_id",
        "raw_snapshot_id",
        "confidence",
        "normalization_warnings",
    },
    "move_candidates.jsonl": {
        "run_id",
        "move_id",
        "move_name",
        "move_type",
        "category_raw",
        "power",
        "energy_cost",
        "effect_text",
        "description_text",
        "source_version",
        "source_page_id",
        "raw_snapshot_id",
        "confidence",
        "normalization_warnings",
    },
    "derived_ability_candidates.jsonl": {
        "run_id",
        "ability_id",
        "ability_name",
        "effect_text",
        "source_species_ids",
        "source_page_ids",
        "derivation_status",
        "confidence",
        "normalization_warnings",
    },
    "species_move_pool_candidates.jsonl": {
        "run_id",
        "species_id",
        "move_name_raw",
        "move_id",
        "access_channel",
        "unlock_level",
        "source_field",
        "source_page_id",
        "raw_snapshot_id",
        "confidence",
        "normalization_warnings",
    },
    "validation_events.jsonl": {
        "run_id",
        "severity",
        "code",
        "entity_type",
        "record_id",
        "source_page_id",
        "field_name",
        "message",
        "action_taken",
    },
    "rejected_fields.jsonl": {
        "run_id",
        "source_page_id",
        "entity_type",
        "source_label",
        "normalized_candidate",
        "reason",
        "policy_basis",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def validate_artifacts(output_dir: Path) -> dict[str, Any]:
    missing = [filename for filename in REQUIRED_FILES if not (output_dir / filename).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required artifact files: {missing}")

    counts: dict[str, int] = {}
    for filename, kind in REQUIRED_FILES.items():
        path = output_dir / filename
        if kind == "json":
            load_json(path)
            counts[filename] = 1
        elif kind == "jsonl":
            rows = iter_jsonl(path)
            required = REQUIRED_FIELDS[filename]
            for index, row in enumerate(rows, start=1):
                missing_fields = required.difference(row)
                if missing_fields:
                    raise ValueError(f"{filename}:{index} missing fields: {sorted(missing_fields)}")
            counts[filename] = len(rows)
        else:
            if not path.read_text(encoding="utf-8").strip():
                raise ValueError(f"{filename} is empty")
            counts[filename] = 1

    manifest = load_json(output_dir / "run_manifest.json")
    missing_manifest_fields = REQUIRED_MANIFEST_FIELDS.difference(manifest)
    if missing_manifest_fields:
        raise ValueError(f"run_manifest.json missing fields: {sorted(missing_manifest_fields)}")
    if manifest.get("run_mode") != "dry_run":
        raise ValueError("run_manifest.json must have run_mode=dry_run")
    return {"output_dir": str(output_dir), "counts": counts, "manifest_status": manifest.get("status")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate P1c/P1d dry-run artifact files.")
    parser.add_argument("output_dir", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = validate_artifacts(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
