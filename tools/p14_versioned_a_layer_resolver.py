#!/usr/bin/env python3
"""Resolve A-layer names against an S1 snapshot plus candidate S2 overlay.

This is a candidate-only resolver surface for P14 dataset work. It does not
write or promote runtime Battle Dex data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_MANIFEST = REPO_ROOT / "data" / "runtime" / "snapshots" / "s1_2026-05-20" / "manifest.yaml"
DEFAULT_OVERLAY_MANIFEST = (
    REPO_ROOT / "data" / "knowledge_graph" / "v0" / "a_layer_overlays" / "s2_2026-05-21" / "manifest.yaml"
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _repo_rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _repo_path(path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_base_names(base_db: Path) -> dict[str, set[str]]:
    conn = sqlite3.connect(base_db)
    try:
        species = {str(row[0]) for row in conn.execute("select display_name from species_form").fetchall()}
        moves = {str(row[0]) for row in conn.execute("select move_name from move").fetchall()}
    finally:
        conn.close()
    return {"species": species, "moves": moves}


def _overlay_names(overlay_path: Path) -> dict[str, dict[str, set[str]]]:
    payload = _load_yaml(overlay_path)
    species: dict[str, set[str]] = {}
    moves: dict[str, set[str]] = {}
    for group_name, entries in (payload.get("entries") or {}).items():
        for entry in entries or []:
            target = entry.get("target") or {}
            display_name = target.get("display_name")
            move_name = target.get("move_name") or entry.get("move_name")
            species_target = target.get("species") or {}
            move_target = target.get("move") or {}
            if species_target.get("display_name"):
                display_name = species_target.get("display_name")
            if move_target.get("move_name"):
                move_name = move_target.get("move_name")
            if display_name:
                species.setdefault(str(display_name), set()).add(str(group_name))
            if move_name:
                moves.setdefault(str(move_name), set()).add(str(group_name))
    return {"species": species, "moves": moves}


def build_resolver_contract(
    *,
    base_manifest_path: Path = DEFAULT_BASE_MANIFEST,
    overlay_manifest_path: Path = DEFAULT_OVERLAY_MANIFEST,
) -> dict[str, Any]:
    base_manifest = _load_yaml(base_manifest_path)
    overlay_manifest = _load_yaml(overlay_manifest_path)
    base_db = _repo_path(((base_manifest.get("snapshot") or {}).get("path")))
    overlay_path = _repo_path(overlay_manifest.get("overlay_ref"))
    if not base_db or not base_db.exists():
        raise FileNotFoundError(f"base snapshot DB not found: {base_db}")
    if not overlay_path or not overlay_path.exists():
        raise FileNotFoundError(f"S2 overlay not found: {overlay_path}")

    base_names = _load_base_names(base_db)
    overlay = _overlay_names(overlay_path)
    return {
        "schema_version": "p14.versioned_a_layer_resolver.v0",
        "resolver_id": "s1_2026-05-20_plus_s2_2026-05-21_candidate_overlay",
        "created_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "promotion_status": "candidate_only_reference_surface",
        "may_write_runtime_db": False,
        "base_snapshot": {
            "manifest_path": _repo_rel(base_manifest_path),
            "manifest_sha256": _sha256(base_manifest_path),
            "battle_dex_path": _repo_rel(base_db),
            "battle_dex_sha256": _sha256(base_db),
            "game_epoch": base_manifest.get("game_epoch"),
        },
        "overlay": {
            "manifest_path": _repo_rel(overlay_manifest_path),
            "manifest_sha256": _sha256(overlay_manifest_path),
            "overlay_path": _repo_rel(overlay_path),
            "overlay_sha256": _sha256(overlay_path),
            "game_epoch": overlay_manifest.get("game_epoch"),
            "promotion_status": overlay_manifest.get("promotion_status"),
            "may_write_runtime_db": overlay_manifest.get("may_write_runtime_db"),
            "requires_pm_review_before_runtime": overlay_manifest.get("requires_pm_review_before_runtime"),
            "requires_pm_review_before_a_layer_write": overlay_manifest.get("requires_pm_review_before_a_layer_write"),
        },
        "coverage_counts": {
            "base_species_count": len(base_names["species"]),
            "base_move_count": len(base_names["moves"]),
            "overlay_species_count": len(overlay["species"]),
            "overlay_move_count": len(overlay["moves"]),
        },
        "policy": {
            "can_reference_overlay_for_candidate_items": True,
            "can_promote_runtime": False,
            "can_accept_gold": False,
            "can_materialize_reviewed_graph": False,
            "blocker_for_s2_touched_candidates": "s2_a_layer_overlay_referenced_pm_review_gold_gate_required",
        },
    }


def resolve_entities(
    entities: list[str],
    *,
    base_manifest_path: Path = DEFAULT_BASE_MANIFEST,
    overlay_manifest_path: Path = DEFAULT_OVERLAY_MANIFEST,
) -> dict[str, Any]:
    contract = build_resolver_contract(
        base_manifest_path=base_manifest_path,
        overlay_manifest_path=overlay_manifest_path,
    )
    base_db = REPO_ROOT / contract["base_snapshot"]["battle_dex_path"]
    overlay_path = REPO_ROOT / contract["overlay"]["overlay_path"]
    base_names = _load_base_names(base_db)
    overlay = _overlay_names(overlay_path)
    rows = []
    for entity in sorted({str(item) for item in entities if str(item)}):
        base_kind = "species" if entity in base_names["species"] else "move" if entity in base_names["moves"] else "unresolved"
        overlay_groups = sorted((overlay["species"].get(entity) or set()) | (overlay["moves"].get(entity) or set()))
        rows.append(
            {
                "entity": entity,
                "base_resolution": base_kind,
                "overlay_resolution": "s2_overlay_target" if overlay_groups else "not_in_s2_overlay",
                "overlay_groups": overlay_groups,
                "runtime_allowed": False,
                "pm_review_required_before_runtime": bool(overlay_groups),
            }
        )
    return {**contract, "resolved_entities": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-manifest", type=Path, default=DEFAULT_BASE_MANIFEST)
    parser.add_argument("--overlay-manifest", type=Path, default=DEFAULT_OVERLAY_MANIFEST)
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = (
        resolve_entities(args.entity, base_manifest_path=args.base_manifest, overlay_manifest_path=args.overlay_manifest)
        if args.entity
        else build_resolver_contract(base_manifest_path=args.base_manifest, overlay_manifest_path=args.overlay_manifest)
    )
    if args.output:
        _write_yaml(args.output, payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif not args.output:
        print(yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper))


if __name__ == "__main__":
    main()
