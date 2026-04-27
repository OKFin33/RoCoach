#!/usr/bin/env python3
"""Validate P1e importer dry-run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = {
    "importer_run_manifest.json": "json",
    "resolved_species_forms.jsonl": "jsonl",
    "resolved_moves.jsonl": "jsonl",
    "resolved_derived_abilities.jsonl": "jsonl",
    "excluded_entities.jsonl": "jsonl",
    "review_required_entities.jsonl": "jsonl",
    "supplement_backed_entities.jsonl": "jsonl",
    "unresolved_entities.jsonl": "jsonl",
    "importer_diff_summary.md": "text",
}

REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "started_at",
    "finished_at",
    "run_mode",
    "canonical_artifact_dir",
    "canonical_run_id",
    "supplement_path",
    "supplement_format",
    "policy_mode",
    "output_files",
    "counts",
    "resolution_statuses",
    "sqlite_mutation",
}

BASE_FIELDS = {
    "entity_type",
    "entity_key",
    "resolution_status",
    "canonical_source_layer",
    "wiki_source_refs",
    "supplement_refs",
    "resolution_reason",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def validate_artifacts(output_dir: Path) -> dict:
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
            for index, row in enumerate(rows, start=1):
                missing_fields = BASE_FIELDS.difference(row)
                if missing_fields:
                    raise ValueError(f"{filename}:{index} missing fields: {sorted(missing_fields)}")
            counts[filename] = len(rows)
        else:
            if not path.read_text(encoding="utf-8").strip():
                raise ValueError(f"{filename} is empty")
            counts[filename] = 1

    manifest = load_json(output_dir / "importer_run_manifest.json")
    missing_manifest_fields = REQUIRED_MANIFEST_FIELDS.difference(manifest)
    if missing_manifest_fields:
        raise ValueError(f"importer_run_manifest.json missing fields: {sorted(missing_manifest_fields)}")
    if manifest.get("run_mode") != "dry_run":
        raise ValueError("importer_run_manifest.json must have run_mode=dry_run")
    if manifest.get("sqlite_mutation") is not False:
        raise ValueError("importer_run_manifest.json must set sqlite_mutation=false")
    return {"output_dir": str(output_dir), "counts": counts, "policy_mode": manifest.get("policy_mode")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate P1e importer dry-run artifact files.")
    parser.add_argument("output_dir", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = validate_artifacts(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
