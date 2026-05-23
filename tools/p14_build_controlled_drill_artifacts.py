#!/usr/bin/env python3
"""Build a candidate-only P14 controlled dataset drill packet.

This aggregates already-ingested source probes, set inventory, set candidates,
relation candidates, and consolidation output into one auditable drill bundle.
It writes no runtime graph data and never marks candidates reviewed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_ID = "phase48_controlled_pipeline_drill_2026-05-23"
DEFAULT_SOURCE_IDS = [
    "kgsrc_bili_bv16v9hbpenj",
    "kgsrc_bili_bv1dkoxbyezc",
    "kgsrc_bili_bv1kd5s6lecy",
    "kgsrc_bili_bv1r796brefs",
]
DEFAULT_KNOWLEDGE_OPS_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_KG_ROOT = REPO_ROOT / "data" / "knowledge_graph" / "v0"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
S2_PATCH_DATE = date(2026, 5, 21)
S2_RECONCILIATION_PATH = DEFAULT_KG_ROOT / "patch_deltas" / "s2_2026-05-21_a_layer_reconciliation_v0.yaml"
S2_PATCH_DELTA_PACK_PATH = DEFAULT_KG_ROOT / "patch_deltas" / "s2_2026-05-21_patch_delta_pack_v0.yaml"
S2_OFFICIAL_SOURCE_MANIFEST_PATH = (
    DEFAULT_KG_ROOT
    / "patch_deltas"
    / "s2_2026-05-20_official_balance_sources"
    / "s2_2026-05-20_official_balance_manifest.yaml"
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


def _repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", str(value).strip(), flags=re.UNICODE)
    return cleaned.strip("_") or "unknown"


def _first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def _load_first_yaml(paths: list[Path]) -> Any:
    path = _first_existing(paths)
    return _load_yaml(path) if path else {}


def _date_from_string(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _game_epoch(published_at: Any) -> str:
    published = _date_from_string(published_at)
    if not published:
        return "unknown_source_epoch"
    if published < S2_PATCH_DATE:
        return "pre_s2_source"
    if published == S2_PATCH_DATE:
        return "s2_boundary_source"
    return "post_s2_candidate"


def _artifact(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return {"path": _repo_rel(path), "sha256": _sha256(path)}


def _source_probe_dir(source_id: str) -> Path:
    return DEFAULT_KNOWLEDGE_OPS_ROOT / "source_probe" / source_id


def _source_artifacts(source_id: str) -> dict[str, dict[str, Any] | None]:
    probe = _source_probe_dir(source_id)
    foundation = probe / "evidence_foundation"
    source_manifest_v2_path = foundation / "source_manifest_v2.yaml"
    source_manifest_v2 = _load_yaml(source_manifest_v2_path) if source_manifest_v2_path.exists() else {}
    transcript_value = (((source_manifest_v2.get("ingest") or {}).get("artifacts") or {}).get("transcript_path"))
    transcript_path = REPO_ROOT / transcript_value if transcript_value else None
    subtitle = _first_existing([*sorted(probe.glob("*.srt")), *sorted(probe.glob("*.vtt"))])
    return {
        "raw_subtitle": _artifact(subtitle),
        "raw_transcript": _artifact(transcript_path),
        "source_manifest": _artifact(probe / "source_manifest.yaml"),
        "ab_refined_transcript": _artifact(probe / f"{source_id}.ab_refined.md"),
        "ab_refine_manifest": _artifact(probe / f"{source_id}.manifest.yaml"),
        "review_questions": _artifact(probe / f"{source_id}.review_questions.yaml"),
        "source_manifest_v2": _artifact(source_manifest_v2_path),
        "segments": _artifact(foundation / "segments.yaml"),
        "quality_gate": _artifact(foundation / "quality_gate.yaml"),
        "claim_atoms": _artifact(foundation / "claim_atoms.yaml"),
        "set_candidates": _artifact(DEFAULT_KNOWLEDGE_OPS_ROOT / "set_candidates" / f"{source_id}.candidate_sets.yaml"),
        "relation_candidates": _artifact(DEFAULT_KNOWLEDGE_OPS_ROOT / "relation_candidates" / f"{source_id}.candidate_edges.yaml"),
        "set_inventory": _artifact(DEFAULT_KNOWLEDGE_OPS_ROOT / "set_inventory" / f"{source_id}.source_inventory.yaml"),
    }


def _load_dex(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"species": set(), "moves": set(), "move_pools": {}}
    conn = sqlite3.connect(db_path)
    try:
        species = {str(row[0]) for row in conn.execute("select display_name from species_form").fetchall()}
        moves = {str(row[0]) for row in conn.execute("select move_name from move").fetchall()}
        rows = conn.execute(
            """
            SELECT sf.display_name, COALESCE(m.move_name, smp.move_name_raw) AS move_name
            FROM species_move_pool smp
            JOIN species_form sf ON sf.species_id = smp.species_id
            LEFT JOIN move m ON m.move_id = smp.move_id
            WHERE COALESCE(m.move_name, smp.move_name_raw) IS NOT NULL
            """
        ).fetchall()
    finally:
        conn.close()
    move_pools: dict[str, set[str]] = {}
    for species_name, move_name in rows:
        move_pools.setdefault(str(species_name), set()).add(str(move_name))
    return {"species": species, "moves": moves, "move_pools": move_pools}


def _load_s2_affected(path: Path) -> dict[str, set[str]]:
    payload = _load_yaml(path) if path.exists() else {}
    species: set[str] = set()
    moves: set[str] = set()
    for key in ("stat_overlays", "ability_overlays", "move_pool_additions"):
        for item in payload.get(key) or []:
            resolution = item.get("resolution") or {}
            species_payload = resolution.get("species") or {}
            if species_payload.get("display_name"):
                species.add(str(species_payload["display_name"]))
    for item in [*(payload.get("move_effect_entries") or []), *(payload.get("move_effect_overlays") or [])]:
        resolution = item.get("resolution") or item.get("move_resolution") or {}
        move_payload = resolution.get("move") or {}
        if move_payload.get("move_name"):
            moves.add(str(move_payload["move_name"]))
        if item.get("move_name"):
            moves.add(str(item["move_name"]))
    for item in payload.get("move_effects") or []:
        if item.get("move_name"):
            moves.add(str(item["move_name"]))
    return {"species": species, "moves": moves}


def _span_ref(source_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    segment_ids = list(evidence.get("segment_ids") or [])
    return {
        "source_id": source_id,
        "segment_ids": segment_ids,
        "source_span_id": f"{source_id}:{','.join(segment_ids)}" if segment_ids else f"{source_id}:unknown",
        "segments_path": _repo_rel(_source_probe_dir(source_id) / "evidence_foundation" / "segments.yaml"),
        "start_ms": evidence.get("start_ms"),
        "end_ms": evidence.get("end_ms"),
        "quote": evidence.get("quote"),
    }


def _field_provenance(
    *,
    status: str,
    source_id: str | None = None,
    evidence: dict[str, Any] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status}
    if source_id and evidence:
        payload["evidence"] = [_span_ref(source_id, evidence)]
    if note:
        payload["note"] = note
    return payload


def _first_evidence(record: dict[str, Any]) -> dict[str, Any] | None:
    refs = record.get("evidence_refs") or []
    return refs[0] if refs else None


def _move_evidence_map(dossier: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for window in (dossier.get("move_slots") or {}).get("move_signal_windows") or []:
        evidence = window.get("evidence") or {}
        for move in window.get("moves") or []:
            result.setdefault(str(move), []).append(evidence)
    return result


def _s2_blockers(species_name: str, moves: list[str], s2_affected: dict[str, set[str]], game_epoch: str) -> tuple[list[str], list[str]]:
    impacted = []
    if species_name in s2_affected["species"]:
        impacted.append(species_name)
    impacted.extend(move for move in moves if move in s2_affected["moves"])
    blockers: list[str] = []
    if impacted and game_epoch in {"post_s2_candidate", "s2_boundary_source", "unknown_source_epoch"}:
        blockers.append("s2_a_layer_reconciliation_required_before_runtime_or_gold")
    return sorted(set(blockers)), sorted(set(impacted))


def _s2_entity_blockers(entities: list[str], s2_affected: dict[str, set[str]], game_epoch: str) -> tuple[list[str], list[str]]:
    impacted = sorted({entity for entity in entities if entity in s2_affected["species"] or entity in s2_affected["moves"]})
    blockers: list[str] = []
    if impacted and game_epoch in {"post_s2_candidate", "s2_boundary_source", "unknown_source_epoch"}:
        blockers.append("s2_a_layer_reconciliation_required_before_runtime_or_gold")
    return blockers, impacted


def _s2_gate_refs() -> list[dict[str, Any]]:
    refs = []
    for label, path in [
        ("official_s2_balance_source_manifest", S2_OFFICIAL_SOURCE_MANIFEST_PATH),
        ("s2_patch_delta_pack", S2_PATCH_DELTA_PACK_PATH),
        ("s2_a_layer_reconciliation", S2_RECONCILIATION_PATH),
    ]:
        artifact = _artifact(path)
        if artifact:
            artifact["label"] = label
            refs.append(artifact)
    return refs


def _a_layer_entity_resolution(entities: list[str], dex: dict[str, Any]) -> dict[str, str]:
    resolution: dict[str, str] = {}
    for entity in sorted({str(item) for item in entities if str(item)}):
        if entity in dex["species"]:
            resolution[entity] = "resolved_species_exact"
        elif entity in dex["moves"]:
            resolution[entity] = "resolved_move_exact"
        else:
            resolution[entity] = "unresolved_or_source_phrase"
    return resolution


def _source_records(source_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        probe = _source_probe_dir(source_id)
        manifest = _load_yaml(probe / "source_manifest.yaml")
        source = manifest.get("source") or {}
        quality = _load_yaml(probe / "evidence_foundation" / "quality_gate.yaml")
        source_manifest_v2 = _load_yaml(probe / "evidence_foundation" / "source_manifest_v2.yaml")
        ingest = source_manifest_v2.get("ingest") or {}
        transcript_method = ingest.get("transcript_method") or "unknown"
        artifacts = {key: value for key, value in _source_artifacts(source_id).items() if value}
        rows.append(
            {
                "source_id": source_id,
                "url": source.get("url"),
                "title": source.get("title"),
                "uploader": source.get("uploader"),
                "published_at": source.get("published_at"),
                "source_type": source.get("source_type"),
                "target_entities": source.get("target_entities") or [],
                "game_epoch": _game_epoch(source.get("published_at")),
                "collection_status": "local_source_probe_ready_for_controlled_drill",
                "transcript_method": transcript_method,
                "subtitle_available": bool(artifacts.get("raw_subtitle")),
                "transcript_available": bool(artifacts.get("raw_transcript")),
                "reliability_initial": (
                    "primary_candidate_source"
                    if source.get("source_type") == "team_explainer"
                    else "supporting_counterplay_source"
                ),
                "quality": {
                    "segment_count": quality.get("segment_count"),
                    "claim_atom_count": quality.get("claim_atom_count"),
                    "repair_required_segments": len(quality.get("repair_required_segments") or []),
                    "quality_gate_counts": quality.get("quality_gate_counts") or {},
                },
                "artifacts": artifacts,
                "runtime_allowed": False,
            }
        )
    return rows


def _set_items(batch_id: str, source_ids: list[str], dex: dict[str, Any], s2_affected: dict[str, set[str]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source in _source_records(source_ids):
        source_id = source["source_id"]
        game_epoch = source["game_epoch"]
        inventory = _load_yaml(DEFAULT_KNOWLEDGE_OPS_ROOT / "set_inventory" / f"{source_id}.source_inventory.yaml")
        for dossier in inventory.get("set_dossiers") or []:
            species_name = str(dossier.get("species_name") or "")
            moves = list((dossier.get("move_slots") or {}).get("known_moves") or [])
            evidence = _first_evidence(dossier)
            move_evidence = _move_evidence_map(dossier)
            s2_blockers, impacted = _s2_blockers(species_name, moves, s2_affected, game_epoch)
            tactical_context = dossier.get("tactical_context") or {}
            teammate_relations = list(tactical_context.get("common_partners") or []) + list(
                tactical_context.get("combo_notes") or []
            )
            counter_relations = list(tactical_context.get("counterplay_claims") or []) + list(
                tactical_context.get("matchup_claims") or []
            )
            field_provenance: dict[str, Any] = {
                "species": _field_provenance(
                    status="source_span_bound_exact_a_layer" if species_name in dex["species"] else "unresolved",
                    source_id=source_id,
                    evidence=evidence,
                ),
                "moves": {
                    move: _field_provenance(
                        status=(
                            "source_span_bound_legal_a_layer_move"
                            if move in dex["moves"] and move in dex["move_pools"].get(species_name, set())
                            else "source_span_bound_a_layer_move_legality_blocked"
                        ),
                        source_id=source_id,
                        evidence=(move_evidence.get(move) or [evidence or {}])[0],
                    )
                    for move in moves
                }
                if moves
                else _field_provenance(status="not_observed", note="No legal move slots extracted for this source dossier."),
                "role_intent": _field_provenance(
                    status="source_keyword_candidate" if tactical_context.get("roles") else "not_observed",
                    source_id=source_id if tactical_context.get("roles") else None,
                    evidence=evidence if tactical_context.get("roles") else None,
                ),
                "nature": _field_provenance(status="not_observed"),
                "individual_values": _field_provenance(status="not_observed"),
                "bloodline": _field_provenance(status="not_observed"),
                "teammate_relations": _field_provenance(
                    status="source_phrase_candidate" if teammate_relations else "not_observed",
                    source_id=source_id if teammate_relations else None,
                    evidence=evidence if teammate_relations else None,
                ),
                "counter_relations": _field_provenance(
                    status="source_phrase_candidate" if counter_relations else "not_observed",
                    source_id=source_id if counter_relations else None,
                    evidence=evidence if counter_relations else None,
                ),
                "mechanism_dependencies": _field_provenance(
                    status="source_phrase_candidate"
                    if (dossier.get("configuration") or {}).get("mechanism_mentions")
                    else "not_observed",
                    source_id=source_id if (dossier.get("configuration") or {}).get("mechanism_mentions") else None,
                    evidence=evidence if (dossier.get("configuration") or {}).get("mechanism_mentions") else None,
                ),
            }
            source_span_ids = sorted(
                {
                    span["source_span_id"]
                    for field in field_provenance.values()
                    if isinstance(field, dict)
                    for span in field.get("evidence", [])
                }
            )
            blockers = sorted(set(["pm_review_required", *list(dossier.get("promotion_blockers") or []), *s2_blockers]))
            items.append(
                {
                    "item_id": f"candkg/{batch_id}/species_set/{_slug(source_id)}/{_slug(species_name)}",
                    "candidate_type": "species_set_candidate_from_source_inventory",
                    "review_status": "candidate_unreviewed",
                    "runtime_allowed": False,
                    "source_ids": [source_id],
                    "source_span_ids": source_span_ids,
                    "game_epoch": game_epoch,
                    "canonical_entities": {
                        "species": species_name,
                        "moves": moves,
                        "mechanisms": list((dossier.get("configuration") or {}).get("mechanism_mentions") or []),
                    },
                    "fields": {
                        "species": species_name,
                        "moves": moves,
                        "role_intent": (dossier.get("tactical_context") or {}).get("roles") or "unknown",
                        "nature": "unknown",
                        "individual_values": "unknown",
                        "bloodline": "unknown",
                        "teammate_relations": teammate_relations,
                        "counter_relations": counter_relations,
                        "mechanism_dependencies": (dossier.get("configuration") or {}).get("mechanism_mentions") or [],
                    },
                    "a_layer_resolution": {
                        "species_status": "resolved_exact" if species_name in dex["species"] else "unresolved",
                        "move_status": {
                            move: "legal_for_species"
                            if move in dex["move_pools"].get(species_name, set())
                            else "a_layer_move_but_not_legal_for_species"
                            for move in moves
                        },
                    },
                    "field_provenance": field_provenance,
                    "quality": {
                        "same_build_confidence": ((dossier.get("move_slots") or {}).get("same_build_confidence") or "low"),
                        "move_completeness": ((dossier.get("move_slots") or {}).get("completeness") or "unknown"),
                    },
                    "s2_affected_entities": impacted,
                    "blocked_by": blockers,
                    "transform_lineage": [
                        "source_probe",
                        "ab_refined_transcript",
                        "evidence_foundation_segments",
                        "p14_set_inventory_builder",
                        "controlled_drill_candidate_item",
                    ],
                }
            )
    return items


def _relation_items(batch_id: str, source_ids: list[str], s2_affected: dict[str, set[str]], dex: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source in _source_records(source_ids):
        source_id = source["source_id"]
        payload = _load_yaml(DEFAULT_KNOWLEDGE_OPS_ROOT / "relation_candidates" / f"{source_id}.candidate_edges.yaml")
        for edge in payload.get("candidate_edges") or []:
            evidence = edge.get("evidence") or {}
            entities = [str(edge.get("source_species_or_set") or ""), *[str(item) for item in edge.get("target_species_or_sets") or []]]
            s2_blockers, impacted = _s2_entity_blockers(entities, s2_affected, source["game_epoch"])
            items.append(
                {
                    "item_id": f"candkg/{batch_id}/relation/{_slug(source_id)}/{_slug(edge.get('candidate_id'))}",
                    "candidate_type": "relation_candidate",
                    "review_status": "candidate_unreviewed",
                    "runtime_allowed": False,
                    "source_ids": [source_id],
                    "source_span_ids": [_span_ref(source_id, evidence)["source_span_id"]],
                    "game_epoch": source["game_epoch"],
                    "canonical_entities": {
                        "source_species_or_set": edge.get("source_species_or_set"),
                        "target_species_or_sets": edge.get("target_species_or_sets") or [],
                    },
                    "fields": {
                        "relation_type": edge.get("edge_type"),
                        "source_phrase": edge.get("source_phrase"),
                        "mechanism_dependencies": edge.get("mechanism_refs_needed") or [],
                    },
                    "a_layer_resolution": {
                        "entity_status": _a_layer_entity_resolution(entities, dex),
                        "note": "Relation candidates may contain source phrases or set labels; unresolved labels stay blocked.",
                    },
                    "field_provenance": {
                        "relation": _field_provenance(
                            status="source_phrase_candidate",
                            source_id=source_id,
                            evidence=evidence,
                        )
                    },
                    "quality": {
                        "claim_risk": edge.get("claim_risk"),
                        "reasoning_quality": edge.get("reasoning_quality"),
                    },
                    "s2_affected_entities": impacted,
                    "blocked_by": sorted(set([*(edge.get("promotion_blockers") or []), *s2_blockers])),
                    "transform_lineage": [
                        "source_probe",
                        "ab_refined_transcript",
                        "evidence_foundation_segments",
                        "p14_set_pipeline_relation_candidates",
                        "controlled_drill_candidate_item",
                    ],
                }
            )
    return items


def _mechanism_dependency_items(batch_id: str, source_ids: list[str], s2_affected: dict[str, set[str]], dex: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for source in _source_records(source_ids):
        source_id = source["source_id"]
        payload = _load_yaml(DEFAULT_KNOWLEDGE_OPS_ROOT / "set_candidates" / f"{source_id}.candidate_sets.yaml")
        for candidate in payload.get("candidate_sets") or []:
            evidence = ((candidate.get("evidence_windows") or [{}])[0]) or {}
            center = str(evidence.get("center_segment_id") or "")
            for mechanism_ref in candidate.get("mechanism_refs_needed") or []:
                key = (source_id, str(candidate.get("species_name")), str(mechanism_ref), center)
                if key in seen:
                    continue
                seen.add(key)
                s2_blockers, impacted = _s2_entity_blockers(
                    [str(candidate.get("species_name") or ""), str(mechanism_ref or "")],
                    s2_affected,
                    source["game_epoch"],
                )
                items.append(
                    {
                        "item_id": f"candkg/{batch_id}/mechanism_dependency/{_slug(source_id)}/{_slug(candidate.get('species_name'))}/{_slug(mechanism_ref)}/{_slug(center)}",
                        "candidate_type": "mechanism_dependency_signal",
                        "review_status": "candidate_unreviewed",
                        "runtime_allowed": False,
                        "source_ids": [source_id],
                        "source_span_ids": [_span_ref(source_id, evidence)["source_span_id"]],
                        "game_epoch": source["game_epoch"],
                        "canonical_entities": {
                            "species": candidate.get("species_name"),
                            "mechanism_ref": mechanism_ref,
                        },
                        "fields": {
                            "mechanism_dependency": mechanism_ref,
                            "species_context": candidate.get("species_name"),
                            "role_intent": candidate.get("inferred_roles") or "unknown",
                        },
                        "a_layer_resolution": {
                            "entity_status": _a_layer_entity_resolution([str(candidate.get("species_name") or "")], dex),
                            "mechanism_ref_status": "requires_reviewed_b_layer_mechanism_rule",
                        },
                        "field_provenance": {
                            "mechanism_dependency": _field_provenance(
                                status="source_phrase_candidate_requires_reviewed_mechanism_rule",
                                source_id=source_id,
                                evidence=evidence,
                            )
                        },
                        "s2_affected_entities": impacted,
                        "blocked_by": sorted(
                            set(
                                [
                                    "mechanism_rule_not_reviewed",
                                    "pm_review_required",
                                    "single_evidence_window",
                                    *s2_blockers,
                                ]
                            )
                        ),
                        "transform_lineage": [
                            "source_probe",
                            "ab_refined_transcript",
                            "p14_set_pipeline_mechanism_refs_needed",
                            "controlled_drill_candidate_item",
                        ],
                    }
                )
    return items


def _field_evidence_index(candidate_items: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for item in candidate_items:
        for field_name, provenance in (item.get("field_provenance") or {}).items():
            if field_name == "moves" and isinstance(provenance, dict) and not provenance.get("status"):
                for move_name, move_provenance in provenance.items():
                    entries.append(
                        {
                            "item_id": item["item_id"],
                            "field": f"moves.{move_name}",
                            "status": move_provenance.get("status"),
                            "evidence": move_provenance.get("evidence") or [],
                        }
                    )
                continue
            entries.append(
                {
                    "item_id": item["item_id"],
                    "field": field_name,
                    "status": provenance.get("status") if isinstance(provenance, dict) else "unknown",
                    "evidence": provenance.get("evidence") if isinstance(provenance, dict) else [],
                }
            )
    return {
        "schema_version": "p14.field_evidence_index.v0",
        "runtime_allowed": False,
        "entry_count": len(entries),
        "entries": entries,
    }


def _dashboard(
    *,
    batch_id: str,
    source_records: list[dict[str, Any]],
    candidate_items: list[dict[str, Any]],
    set_audit: dict[str, Any],
    inventory_audit: dict[str, Any],
    consolidation: dict[str, Any],
    validation_status: str,
    validator_note: str,
) -> dict[str, Any]:
    blockers = Counter(blocker for item in candidate_items for blocker in item.get("blocked_by") or [])
    item_types = Counter(item["candidate_type"] for item in candidate_items)
    source_epochs = Counter(item["game_epoch"] for item in source_records)
    s2_impacted_item_count = sum(1 for item in candidate_items if item.get("s2_affected_entities"))
    unresolved = sum(
        1
        for item in candidate_items
        for provenance in (item.get("field_provenance") or {}).values()
        if isinstance(provenance, dict) and provenance.get("status") in {"not_observed", "unresolved"}
    )
    return {
        "schema_version": "p14.dataset_pipeline_dashboard.v0",
        "batch_id": batch_id,
        "generated_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "validation_status": validation_status,
        "validator_note": validator_note,
        "source_count": len(source_records),
        "source_ids": [item["source_id"] for item in source_records],
        "source_epoch_counts": dict(sorted(source_epochs.items())),
        "source_segment_count": sum(int((item.get("quality") or {}).get("segment_count") or 0) for item in source_records),
        "repair_required_segment_count": sum(int((item.get("quality") or {}).get("repair_required_segments") or 0) for item in source_records),
        "candidate_item_count": len(candidate_items),
        "candidate_item_counts_by_type": dict(item_types),
        "field_unresolved_or_not_observed_count": unresolved,
        "blocked_item_count": sum(1 for item in candidate_items if item.get("blocked_by")),
        "blocker_counts": dict(sorted(blockers.items())),
        "set_pipeline_summary": (set_audit.get("summary") or {}),
        "inventory_summary": (inventory_audit.get("summary") or {}),
        "review_candidate_count": 0,
        "upstream_consolidation_summary": {
            "scope": "upstream_global_pool_not_batch_review_gate",
            "note": (
                "These counts come from the upstream inventory/consolidation pool. "
                "They do not override this batch's candidate_item_count, "
                "blocked_item_count, or review_candidate_count."
            ),
            **(consolidation.get("summary") or {}),
        },
        "s2_status": {
            "patch_date": S2_PATCH_DATE.isoformat(),
            "pre_s2_source_count": sum(1 for item in source_records if item["game_epoch"] == "pre_s2_source"),
            "s2_boundary_source_count": sum(1 for item in source_records if item["game_epoch"] == "s2_boundary_source"),
            "post_s2_source_count": sum(1 for item in source_records if item["game_epoch"] == "post_s2_candidate"),
            "s2_impacted_candidate_count": s2_impacted_item_count,
            "s2_blocked_candidate_count": sum(
                1
                for item in candidate_items
                if "s2_a_layer_reconciliation_required_before_runtime_or_gold" in (item.get("blocked_by") or [])
            ),
            "s2_gate_refs": _s2_gate_refs(),
            "policy": "post-S2 or boundary candidates touching S2-affected species/moves remain candidate-only and blocked until reconciled A-layer snapshot plus review gates exist",
        },
    }


def _pm_packet(
    *,
    batch_id: str,
    source_records: list[dict[str, Any]],
    candidate_items: list[dict[str, Any]],
    dashboard: dict[str, Any],
) -> str:
    item_counts = dashboard["candidate_item_counts_by_type"]
    blockers = dashboard["blocker_counts"]
    epoch_counts = dashboard.get("source_epoch_counts") or {}
    papas_items = [
        item
        for item in candidate_items
        if "帕帕斯卡" in json.dumps(item.get("canonical_entities") or {}, ensure_ascii=False)
        or "帕帕斯卡" in json.dumps(item.get("fields") or {}, ensure_ascii=False)
    ]
    papas_post_s2 = [item for item in papas_items if item.get("game_epoch") == "post_s2_candidate"]
    papas_direct_sources = [
        item
        for item in source_records
        if "帕帕斯卡" in json.dumps({"title": item.get("title"), "target_entities": item.get("target_entities")}, ensure_ascii=False)
    ]
    thunder_items = [
        item
        for item in candidate_items
        if "雷暴" in json.dumps(item.get("canonical_entities") or {}, ensure_ascii=False)
        or "雷暴" in json.dumps(item.get("fields") or {}, ensure_ascii=False)
    ]
    beast_items = [
        item
        for item in candidate_items
        if "兽花蕾" in json.dumps(item.get("canonical_entities") or {}, ensure_ascii=False)
        or "兽花蕾" in json.dumps(item.get("fields") or {}, ensure_ascii=False)
    ]
    relation_edge_ready = [
        item
        for item in candidate_items
        if item.get("candidate_type") == "relation_candidate"
        and not set(item.get("blocked_by") or []).intersection({"source_phrase_only", "pm_review_required"})
    ]
    s2_status = dashboard.get("s2_status") or {}
    source_lines = [
        f"- `{item['source_id']}`：{item['title']}；{item['source_type']}；{item['game_epoch']}；method={item['transcript_method']}；segments={item['quality']['segment_count']}；repair_required={item['quality']['repair_required_segments']}。"
        for item in source_records
    ]
    need_pm = [
        f"1. `帕帕斯卡`：直接 post-S2 主源数={len(papas_direct_sources)}；包内顺带抽到的 post-S2 item 数={len(papas_post_s2)}。结论：这不是可入图谱的帕帕斯卡 set 主证，只说明它仍值得继续定向扩源。",
        f"2. `雷暴队/兽花蕾`：雷暴相关 item={len(thunder_items)}，兽花蕾相关 item={len(beast_items)}；relation edge ready={len(relation_edge_ready)}。默认仍只做 counterplay/relation 补证，不建图谱边。",
        f"3. S2 gate：S2 受影响候选={s2_status.get('s2_impacted_candidate_count', 0)}，已被 S2 blocker 拦截={s2_status.get('s2_blocked_candidate_count', 0)}；PM 只需复核是否有漏拦。",
    ]
    return "\n".join(
        [
            f"# P14 Controlled Dataset Drill PM Packet: {batch_id}",
            "",
            "## 结论",
            "- 本轮完成 source/transcript -> A/B refinement -> candidate extraction -> field evidence -> dashboard/snapshot 的受控演练。",
            "- 所有输出保持 candidate-only，`runtime_allowed=false`；没有 graph materialization、runtime promotion、A-layer overwrite 或 Gold accept。",
            f"- 产出 candidate items：{len(candidate_items)}；类型分布：{json.dumps(item_counts, ensure_ascii=False, sort_keys=True)}。",
            f"- 来源 epoch 分布：{json.dumps(epoch_counts, ensure_ascii=False, sort_keys=True)}。",
            "",
            "## 来源",
            *source_lines,
            "",
            "## 需要 PM 判断",
            *need_pm,
            "",
            "## 可自动接受（仅限 candidate/审计层）",
            "- 进入本包的来源都有本地 source_probe、transcript/subtitle、AB refined transcript、segments.yaml 和 hash，可回查。",
            f"- repair_required segments 总数={dashboard.get('repair_required_segment_count', 0)}；有噪声时只影响 extraction confidence，不自动进 reviewed。",
            "- 技能字段走 A-layer species move pool 过滤；非法近邻技能只保留在 blocked/excluded，不进 moves 字段。",
            "- S2 官方来源、patch delta pack、A-layer reconciliation 都作为 gate refs 写入 dashboard/provenance/snapshot，不授权 runtime 或 DB overwrite。",
            "",
            "## 被拦截",
            f"- Window set candidates 全部 quarantined；主要 blocker：{json.dumps(blockers, ensure_ascii=False, sort_keys=True)}。",
            "- `review_candidate_count=0`，没有任何候选可直接进 reviewed 或 Gold。",
            "- Dashboard 的 `upstream_consolidation_summary` 是上游全局聚合池口径，不是本轮 PM review 放行口径。",
            "- 所有机制依赖只生成 dependency signal；机制规则本身仍需独立 review。",
            "",
            "## 高污染风险",
            "- post-S2 当前赛季材料可以用于候选累积，但不能静默继承成 reviewed set 或 runtime 事实。",
            "- source-level 聚合仍可能把解说近邻技能误并成同一 set；本轮只使用 inventory dossier + field evidence，不做 runtime。",
            "- relation/counterplay 边的证据多数是短语级，不能当稳定克制关系。",
            "",
        ]
    )


def _snapshot_manifest(batch_id: str, paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in paths:
        if path.exists() and path.is_file():
            artifacts.append({"path": _repo_rel(path), "sha256": _sha256(path)})
    return {
        "schema_version": "p14.snapshot_manifest.v0",
        "snapshot_id": batch_id,
        "created_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "promotion_status": "candidate_only_drill_snapshot",
        "artifacts": artifacts,
    }


def build_controlled_drill(
    *,
    batch_id: str,
    source_ids: list[str],
    validation_status: str,
    validator_note: str,
    db_path: Path,
) -> dict[str, Any]:
    out_dir = DEFAULT_KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / batch_id
    data_dashboard_path = DEFAULT_KG_ROOT / "eval" / f"quality_dashboard_{batch_id}.yaml"
    snapshot_dir = DEFAULT_KG_ROOT / "snapshots" / "roco_kg_dataset_v0.1-dev" / batch_id
    snapshot_path = snapshot_dir / "manifest.yaml"

    dex = _load_dex(db_path)
    s2_affected = _load_s2_affected(S2_RECONCILIATION_PATH)
    source_records = _source_records(source_ids)
    set_audit = _load_first_yaml(
        [
            DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / f"{batch_id}_sets.yaml",
            DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / f"{batch_id}_set_pipeline.yaml",
        ]
    )
    inventory_audit = _load_first_yaml(
        [
            DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / f"{batch_id}_inventory.yaml",
            DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / f"{batch_id}_set_inventory.yaml",
        ]
    )
    consolidation = _load_yaml(DEFAULT_KNOWLEDGE_OPS_ROOT / "set_inventory_consolidation" / f"{batch_id}_consolidation.yaml")

    set_items = _set_items(batch_id, source_ids, dex, s2_affected)
    relation_items = _relation_items(batch_id, source_ids, s2_affected, dex)
    mechanism_items = _mechanism_dependency_items(batch_id, source_ids, s2_affected, dex)
    candidate_items = [*set_items, *relation_items, *mechanism_items]

    source_manifest = {
        "schema_version": "p14.controlled_source_bundle_manifest.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "sources": source_records,
    }
    provenance = {
        "schema_version": "p14.controlled_provenance_manifest.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_span_policy": "Every candidate field must point to evidence_foundation/segments.yaml or be explicit not_observed/unresolved.",
        "source_span_roots": sorted({_repo_rel(_source_probe_dir(source_id) / "evidence_foundation" / "segments.yaml") for source_id in source_ids}),
        "source_artifact_count": sum(len(item["artifacts"]) for item in source_records),
        "s2_gate_refs": _s2_gate_refs(),
        "sources": [
            {
                "source_id": item["source_id"],
                "game_epoch": item["game_epoch"],
                "artifacts": item["artifacts"],
            }
            for item in source_records
        ],
    }
    candidate_payload = {
        "schema_version": "p14.controlled_candidate_kg_items.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "review_status": "candidate_unreviewed",
        "candidate_items": candidate_items,
    }
    field_index = _field_evidence_index(candidate_items)
    dashboard = _dashboard(
        batch_id=batch_id,
        source_records=source_records,
        candidate_items=candidate_items,
        set_audit=set_audit,
        inventory_audit=inventory_audit,
        consolidation=consolidation,
        validation_status=validation_status,
        validator_note=validator_note,
    )
    pm_packet = _pm_packet(batch_id=batch_id, source_records=source_records, candidate_items=candidate_items, dashboard=dashboard)

    paths = {
        "source_bundle_manifest": out_dir / "source_bundle_manifest.yaml",
        "provenance_manifest": out_dir / "provenance_manifest.yaml",
        "candidate_items": out_dir / "candidate_kg_items.yaml",
        "field_evidence_index": out_dir / "field_evidence_index.yaml",
        "dashboard": out_dir / "dashboard.yaml",
        "pm_review_packet": out_dir / "pm_review_packet.md",
        "data_dashboard": data_dashboard_path,
        "snapshot_manifest": snapshot_path,
    }
    _write_yaml(paths["source_bundle_manifest"], source_manifest)
    _write_yaml(paths["provenance_manifest"], provenance)
    _write_yaml(paths["candidate_items"], candidate_payload)
    _write_yaml(paths["field_evidence_index"], field_index)
    _write_yaml(paths["dashboard"], dashboard)
    paths["pm_review_packet"].parent.mkdir(parents=True, exist_ok=True)
    paths["pm_review_packet"].write_text(pm_packet, encoding="utf-8")
    _write_yaml(paths["data_dashboard"], dashboard)
    snapshot = _snapshot_manifest(
        batch_id,
        [
            paths["source_bundle_manifest"],
            paths["provenance_manifest"],
            paths["candidate_items"],
            paths["field_evidence_index"],
            paths["dashboard"],
            paths["pm_review_packet"],
            paths["data_dashboard"],
            S2_OFFICIAL_SOURCE_MANIFEST_PATH,
            S2_PATCH_DELTA_PACK_PATH,
            S2_RECONCILIATION_PATH,
        ],
    )
    _write_yaml(paths["snapshot_manifest"], snapshot)

    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_count": len(source_records),
        "candidate_item_count": len(candidate_items),
        "paths": {key: _repo_rel(path) for key, path in paths.items()},
        "summary": {
            "candidate_item_counts_by_type": dashboard["candidate_item_counts_by_type"],
            "blocked_item_count": dashboard["blocked_item_count"],
            "field_unresolved_or_not_observed_count": dashboard["field_unresolved_or_not_observed_count"],
            "validation_status": validation_status,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--validation-status", default="not_run")
    parser.add_argument("--validator-note", default="validator not run yet")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build_controlled_drill(
        batch_id=args.batch_id,
        source_ids=args.source_id or DEFAULT_SOURCE_IDS,
        validation_status=args.validation_status,
        validator_note=args.validator_note,
        db_path=args.db_path,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"controlled drill: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
