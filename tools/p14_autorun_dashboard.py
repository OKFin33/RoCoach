#!/usr/bin/env python3
"""Build the P14 autorun dashboard from one active batch.

The dashboard is a control gate, not a promotion tool. It separates the
volume lane from the promotion lane and only reads active source ids for the
batch, so stale inventory artifacts cannot bleed into PM review.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import DEFAULT_OUT_ROOT, DEFAULT_SOURCE_QUEUE, NoAliasDumper, REPO_ROOT, _relpath


DEFAULT_BATCH_ID = f"phase1_autorun_dashboard_{date.today().isoformat()}"
DEFAULT_MISSION_BOARD = DEFAULT_OUT_ROOT / "mission_board.yaml"
DEFAULT_FAMILY_REVIEW_LEDGER = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "review_state" / "family_review_ledger.yaml"
DEFAULT_REVIEWER_LEDGER = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "review_state" / "reviewer_ledger.yaml"
DEFAULT_SOURCE_RELIABILITY_LEDGER = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "review_state" / "source_reliability_ledger.yaml"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
DEFAULT_INVENTORY_DIR = DEFAULT_OUT_ROOT / "set_inventory"
DEFAULT_CONSOLIDATION_DIR = DEFAULT_OUT_ROOT / "set_inventory_consolidation"
DEFAULT_IDENTITY_AXIS_DIR = DEFAULT_OUT_ROOT / "identity_axis_binding"
IDENTITY_AXIS_DIRNAME = "identity_axis_binding"
AUTORUN_DIRNAME = "autorun"
TARGET_BATCH_MIN = 20
TARGET_BATCH_MAX = 30
FAMILY_REVIEW_MIN_CORE_MOVES = 3
SPECIES_REVIEW_MIN_STABLE_MOVES = 4
STATEFUL_FORM_MECHANISM_TERMS = ("萌化", "化茧")


@dataclass(frozen=True)
class ActiveScope:
    source_ids: list[str]
    consolidation_path: Path | None
    source: str


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _latest_identity_axis_binding(identity_axis_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    if not identity_axis_dir.exists():
        return None, {}
    paths = sorted(identity_axis_dir.glob("*.yaml"), key=lambda path: (path.stat().st_mtime, path.name))
    if not paths:
        return None, {}
    path = paths[-1]
    return path, _load_yaml(path)


def _accepted_axis_branch_index(reviewer_ledger: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    decisions = reviewer_ledger.get("pm_decisions") or {}
    resolutions = decisions.get("axis_branch_resolution") or {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(resolutions, dict):
        items = resolutions.items()
    else:
        items = []
    for species_name, resolution in items:
        if not isinstance(resolution, dict):
            continue
        axis_id = str(resolution.get("axis_id") or "")
        status = str(resolution.get("status") or "")
        if species_name and axis_id and status.startswith("pm_accepted"):
            index[(str(species_name), axis_id)] = resolution
    return index


def _as_source_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("source_id")): item for item in queue.get("sources") or [] if item.get("source_id")}


def _source_ids_from_latest_consolidation(queue: dict[str, Any]) -> ActiveScope:
    latest = queue.get("latest_set_inventory_consolidation") or {}
    source_ids = [str(item) for item in latest.get("source_ids") or [] if item]
    consolidation_path = _repo_path(latest.get("consolidation_path"))
    if source_ids:
        return ActiveScope(source_ids=source_ids, consolidation_path=consolidation_path, source="source_queue.latest_set_inventory_consolidation")

    latest_ingest = queue.get("latest_wingking_relation_ingest") or {}
    source_ids = [str(item) for item in latest_ingest.get("processed_source_ids") or [] if item]
    if source_ids:
        return ActiveScope(source_ids=source_ids, consolidation_path=None, source="source_queue.latest_wingking_relation_ingest")
    return ActiveScope(source_ids=[], consolidation_path=None, source="none")


def resolve_active_scope(
    *,
    queue: dict[str, Any],
    source_ids: set[str] | None,
    consolidation_path: Path | None,
) -> ActiveScope:
    if source_ids:
        return ActiveScope(source_ids=sorted(source_ids), consolidation_path=consolidation_path, source="cli.source_id")
    scope = _source_ids_from_latest_consolidation(queue)
    if consolidation_path:
        return ActiveScope(source_ids=scope.source_ids, consolidation_path=consolidation_path, source=f"{scope.source}+cli.consolidation_path")
    return scope


def _inventory_path(source_id: str, inventory_dir: Path) -> Path:
    return inventory_dir / f"{source_id}.source_inventory.yaml"


def _active_inventory_paths(active_source_ids: list[str], inventory_dir: Path) -> list[Path]:
    return [_inventory_path(source_id, inventory_dir) for source_id in active_source_ids]


def _ignored_stale_inventory_count(active_source_ids: list[str], inventory_dir: Path) -> int:
    active = set(active_source_ids)
    stale = [
        path
        for path in inventory_dir.glob("*.source_inventory.yaml")
        if path.name.split(".")[0] not in active
    ]
    return len(stale)


def _is_blocked_source(source: dict[str, Any]) -> bool:
    status = str(source.get("ingest_status") or "")
    subtitle_status = source.get("subtitle_status") or {}
    return (
        "blocked" in status
        or "transcript_unavailable" in status
        or bool(subtitle_status.get("asr_fallback_status"))
        and str(subtitle_status.get("transcript_method") or "") in {"", "none"}
    )


def _repair_required_count(source: dict[str, Any]) -> int:
    prior = source.get("source_quality_prior") or {}
    latest = prior.get("latest_evidence_foundation") or {}
    value = latest.get("repair_required_segments")
    if value is None:
        return 0
    if isinstance(value, list):
        return len(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _source_health(
    *,
    active_source_ids: list[str],
    source_map: dict[str, dict[str, Any]],
    inventory_dir: Path,
) -> dict[str, Any]:
    missing_source_rows = [source_id for source_id in active_source_ids if source_id not in source_map]
    missing_inventory_paths = [
        _relpath(path)
        for path in _active_inventory_paths(active_source_ids, inventory_dir)
        if not path.exists()
    ]
    active_sources = [source_map[source_id] for source_id in active_source_ids if source_id in source_map]
    blocked_sources = [source for source in active_sources if _is_blocked_source(source)]
    active_set = set(active_source_ids)
    known_blocked_sources = [
        source
        for source_id, source in source_map.items()
        if source_id not in active_set and _is_blocked_source(source)
    ]
    repair_required = [source for source in active_sources if _repair_required_count(source) > 0]
    subtitle_ok = [
        source
        for source in active_sources
        if (source.get("subtitle_status") or {}).get("chinese_subtitle_track") not in {None, "", "none"}
    ]
    queued_sources = [source for source in source_map.values() if str(source.get("ingest_status") or "queued") == "queued"]
    return {
        "active_source_count": len(active_source_ids),
        "source_rows_found_count": len(active_sources),
        "missing_source_rows": missing_source_rows,
        "missing_inventory_paths": missing_inventory_paths,
        "blocked_source_count": len(blocked_sources),
        "blocked_sources": [
            {
                "source_id": source.get("source_id"),
                "title": source.get("title"),
                "ingest_status": source.get("ingest_status"),
                "reason": (source.get("ingest_artifacts") or {}).get("asr_failure_reason")
                or (source.get("subtitle_status") or {}).get("asr_fallback_status")
                or "transcript_or_ingest_blocked",
            }
            for source in blocked_sources
        ],
        "known_blocked_source_count": len(known_blocked_sources),
        "known_blocked_sources": [
            {
                "source_id": source.get("source_id"),
                "title": source.get("title"),
                "ingest_status": source.get("ingest_status"),
                "reason": (source.get("ingest_artifacts") or {}).get("asr_failure_reason")
                or (source.get("subtitle_status") or {}).get("asr_fallback_status")
                or "transcript_or_ingest_blocked",
            }
            for source in known_blocked_sources
        ],
        "repair_required_source_count": len(repair_required),
        "repair_required_sources": [
            {"source_id": source.get("source_id"), "repair_required_segments": _repair_required_count(source)}
            for source in repair_required
        ],
        "subtitle_ok_count": len(subtitle_ok),
        "queued_source_count": len(queued_sources),
        "queued_source_ids": [str(source.get("source_id")) for source in queued_sources if source.get("source_id")],
        "ignored_stale_inventory_count": _ignored_stale_inventory_count(active_source_ids, inventory_dir),
    }


def _family_ledger_index(ledger: dict[str, Any]) -> dict[tuple[str, tuple[str, ...]], dict[str, Any]]:
    index: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for entry in ledger.get("entries") or []:
        proposed = entry.get("proposed_card") or {}
        species = str(proposed.get("canonical_species_name") or (entry.get("source_candidate") or {}).get("species_name") or "")
        core = tuple(sorted(str(move) for move in proposed.get("core_moves") or []))
        if species and core:
            index[(species, core)] = entry
    return index


def _species_id_index(battle_dex: Path) -> dict[str, list[dict[str, str]]]:
    if not battle_dex.exists():
        return {}
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(battle_dex)
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(species_form)").fetchall()}
        if not {"display_name", "species_id"}.issubset(columns):
            return {}
        optional_columns = [
            column
            for column in ("initial_species_name", "evolution_stage", "ability_name", "ability_effect_text")
            if column in columns
        ]
        select_columns = ["display_name", "species_id", *optional_columns]
        rows = conn.execute(f"SELECT {', '.join(select_columns)} FROM species_form").fetchall()
    except sqlite3.Error:
        return {}
    finally:
        if conn is not None:
            conn.close()
    index: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        record = {column: str(value or "") for column, value in zip(select_columns, row)}
        display_name = record.get("display_name")
        species_id = record.get("species_id")
        if display_name and species_id:
            index.setdefault(display_name, []).append(record)
    return index


def _candidate_key(species_name: str, family: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return species_name, tuple(sorted(str(move) for move in family.get("core_moves") or []))


def _full_core_primary_source_count(family: dict[str, Any]) -> int:
    core_moves = {str(move) for move in family.get("core_moves") or [] if move}
    if not core_moves:
        return 0
    primary_source_ids = {str(source_id) for source_id in family.get("primary_source_ids") or [] if source_id}
    count = 0
    for variant in family.get("alter_variants") or []:
        source_id = str(variant.get("source_id") or "")
        if primary_source_ids and source_id not in primary_source_ids:
            continue
        variant_moves = {str(move) for move in variant.get("moves") or [] if move}
        if core_moves.issubset(variant_moves):
            count += 1
    return count


def _ledger_entry_for_reviewed_core_boundary(
    *,
    family_ledger: dict[str, Any],
    species_name: str,
    candidate_core_moves: list[str],
) -> dict[str, Any] | None:
    candidate_core = {str(move) for move in candidate_core_moves if move}
    if not candidate_core:
        return None
    for entry in family_ledger.get("entries") or []:
        proposed = entry.get("proposed_card") or {}
        entry_species = str(proposed.get("canonical_species_name") or (entry.get("source_candidate") or {}).get("species_name") or "")
        if entry_species != species_name:
            continue
        reviewed_core = {str(move) for move in proposed.get("core_moves") or [] if move}
        reviewed_flex = {str(move) for move in proposed.get("flex_moves") or [] if move}
        if reviewed_core and candidate_core.issuperset(reviewed_core) and (candidate_core - reviewed_core).issubset(reviewed_flex):
            return entry
    return None


def _ledger_entry_for_reviewed_core_superset(
    *,
    family_ledger: dict[str, Any],
    species_name: str,
    candidate_core_moves: list[str],
) -> dict[str, Any] | None:
    candidate_core = {str(move) for move in candidate_core_moves if move}
    if not candidate_core:
        return None
    for entry in family_ledger.get("entries") or []:
        proposed = entry.get("proposed_card") or {}
        entry_species = str(proposed.get("canonical_species_name") or (entry.get("source_candidate") or {}).get("species_name") or "")
        if entry_species != species_name:
            continue
        reviewed_core = {str(move) for move in proposed.get("core_moves") or [] if move}
        if reviewed_core and candidate_core > reviewed_core:
            return entry
    return None


def _ambiguous_species_ids(species_name: str, species_index: dict[str, list[dict[str, str]]]) -> list[str]:
    records = species_index.get(species_name) or []
    ids = [
        str(record.get("species_id") or "") if isinstance(record, dict) else str(record)
        for record in records
    ]
    ids = [species_id for species_id in ids if species_id]
    return ids if len(ids) > 1 else []


def _is_final_evolution_stage(evolution_stage: str) -> bool:
    return "最终" in str(evolution_stage or "")


def _is_non_final_form(record: dict[str, str]) -> bool:
    evolution_stage = str(record.get("evolution_stage") or "")
    return bool(evolution_stage) and not _is_final_evolution_stage(evolution_stage)


def _stateful_form_context_terms(record: dict[str, Any]) -> list[str]:
    hits: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, str):
            for term in STATEFUL_FORM_MECHANISM_TERMS:
                if term in value:
                    hits.add(term)
            return
        if isinstance(value, dict):
            for nested in value.values():
                walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)

    for key in ("dossier_variants", "observed_moves", "set_family_candidates", "split_hypotheses"):
        walk(record.get(key))
    return [term for term in STATEFUL_FORM_MECHANISM_TERMS if term in hits]


def _stateful_form_evidence_defer_item(
    species_name: str,
    record: dict[str, Any],
    species_index: dict[str, list[dict[str, str]]],
) -> dict[str, Any] | None:
    species_forms = species_index.get(species_name) or []
    non_final_forms = [form for form in species_forms if _is_non_final_form(form)]
    if not non_final_forms:
        return None
    mechanism_terms = _stateful_form_context_terms(record)
    if not mechanism_terms:
        return None

    family_initial_names = {
        str(form.get("initial_species_name") or "")
        for form in non_final_forms
        if form.get("initial_species_name")
    }
    roster_candidates: list[str] = []
    for forms in species_index.values():
        for form in forms:
            display_name = str(form.get("display_name") or "")
            if not display_name or display_name == species_name:
                continue
            if str(form.get("initial_species_name") or "") not in family_initial_names:
                continue
            if not _is_final_evolution_stage(str(form.get("evolution_stage") or "")):
                continue
            if display_name not in roster_candidates:
                roster_candidates.append(display_name)

    return {
        "defer_reason": "possible_stateful_form_evidence_from_menghua",
        "recommended_action": "reclassify_as_stateful_form_evidence_candidate",
        "observed_battle_form": species_name,
        "roster_species_candidates": roster_candidates,
        "form_derivation_mechanism_terms": mechanism_terms,
        "a_layer_evolution_stages": sorted({str(form.get("evolution_stage") or "") for form in non_final_forms}),
    }


def _summarize_promotion_lane(
    consolidation: dict[str, Any],
    family_ledger: dict[str, Any],
    species_index: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    ledger_index = _family_ledger_index(family_ledger)
    family_review_candidates: list[dict[str, Any]] = []
    deferred_family_candidates: list[dict[str, Any]] = []
    already_reviewed: list[dict[str, Any]] = []
    species_review_candidates: list[dict[str, Any]] = []
    deferred_species_candidates: list[dict[str, Any]] = []

    for record in consolidation.get("species_records") or []:
        species_name = str(record.get("species_name") or "")
        record_family_candidates = list(record.get("family_review_candidates") or [])
        stable_moves = list(record.get("stable_moves") or [])
        ambiguous_ids = _ambiguous_species_ids(species_name, species_index)
        if record.get("state") == "review_candidate" and not record_family_candidates and len(stable_moves) <= 4:
            item = {
                "species_name": species_name,
                "stable_moves": stable_moves,
                "primary_source_count": record.get("primary_source_count", 0),
                "suggested_next_action": record.get("suggested_next_action"),
            }
            if ambiguous_ids:
                item["defer_reason"] = "ambiguous_a_layer_species_id"
                item["ambiguous_species_ids"] = ambiguous_ids
                item["recommended_action"] = "resolve_a_layer_species_identity_before_review"
                deferred_species_candidates.append(item)
            elif stateful_defer_item := _stateful_form_evidence_defer_item(species_name, record, species_index):
                item.update(stateful_defer_item)
                deferred_species_candidates.append(item)
            elif len(stable_moves) >= SPECIES_REVIEW_MIN_STABLE_MOVES:
                species_review_candidates.append(item)
            else:
                item["defer_reason"] = "stable_move_count_below_species_review_threshold"
                item["recommended_action"] = "continue_source_expansion_or_family_clustering"
                deferred_species_candidates.append(item)
        for family in record_family_candidates:
            key = _candidate_key(species_name, family)
            ledger_entry = ledger_index.get(key)
            ledger_match_kind = "exact_core" if ledger_entry else ""
            if not ledger_entry:
                ledger_entry = _ledger_entry_for_reviewed_core_boundary(
                    family_ledger=family_ledger,
                    species_name=species_name,
                    candidate_core_moves=list(family.get("core_moves") or []),
                )
                if ledger_entry:
                    ledger_match_kind = "reviewed_core_with_flex_promoted_by_extraction"
            reviewed_core_superset_entry = None
            if not ledger_entry:
                reviewed_core_superset_entry = _ledger_entry_for_reviewed_core_superset(
                    family_ledger=family_ledger,
                    species_name=species_name,
                    candidate_core_moves=list(family.get("core_moves") or []),
                )
            item = {
                "species_name": species_name,
                "family_id": family.get("family_id"),
                "core_moves": list(family.get("core_moves") or []),
                "flex_moves": list(family.get("flex_moves") or []),
                "primary_source_count": family.get("primary_source_count", 0),
                "primary_source_ids": list(family.get("primary_source_ids") or []),
                "core_cooccurrence_primary_source_count": family.get("core_cooccurrence_primary_source_count", 0),
                "full_core_primary_source_count": _full_core_primary_source_count(family),
                "runtime_allowed": False,
            }
            if ledger_entry:
                item["ledger_review_id"] = ledger_entry.get("review_id")
                item["ledger_review_status"] = (ledger_entry.get("review") or {}).get("review_status")
                item["ledger_match_kind"] = ledger_match_kind
                item["recommended_action"] = (
                    "ledger_update_only_reviewed_flex_not_auto_core"
                    if ledger_match_kind == "reviewed_core_with_flex_promoted_by_extraction"
                    else "ledger_update_only_no_pm_question"
                )
                already_reviewed.append(item)
            elif reviewed_core_superset_entry:
                reviewed_card = reviewed_core_superset_entry.get("proposed_card") or {}
                reviewed_core = list(reviewed_card.get("core_moves") or [])
                reviewed_flex = list(reviewed_card.get("flex_moves") or [])
                item["ledger_review_id"] = reviewed_core_superset_entry.get("review_id")
                item["ledger_review_status"] = (reviewed_core_superset_entry.get("review") or {}).get("review_status")
                item["ledger_match_kind"] = "reviewed_core_with_unreviewed_core_expansion"
                item["reviewed_core_moves"] = reviewed_core
                item["unreviewed_core_moves"] = sorted(set(item["core_moves"]) - set(reviewed_core) - set(reviewed_flex))
                item["defer_reason"] = "reviewed_core_with_unreviewed_core_expansion"
                item["recommended_action"] = "keep_as_candidate_evidence_do_not_reopen_pm_or_promote_core"
                deferred_family_candidates.append(item)
            elif ambiguous_ids:
                item["defer_reason"] = "ambiguous_a_layer_species_id"
                item["ambiguous_species_ids"] = ambiguous_ids
                item["recommended_action"] = "resolve_a_layer_species_identity_before_review"
                deferred_family_candidates.append(item)
            elif len(item["core_moves"]) < FAMILY_REVIEW_MIN_CORE_MOVES:
                item["defer_reason"] = "core_move_count_below_family_review_threshold"
                item["recommended_action"] = "continue_source_expansion_or_family_clustering"
                deferred_family_candidates.append(item)
            elif int(item.get("core_cooccurrence_primary_source_count") or 0) < 3:
                item["defer_reason"] = "core_cooccurrence_below_new_family_review_threshold"
                item["recommended_action"] = "collect_more_focused_sources_before_pm_review"
                deferred_family_candidates.append(item)
            elif len(item["core_moves"]) >= 3 and int(item.get("full_core_primary_source_count") or 0) == 0:
                item["defer_reason"] = "no_full_core_source_for_three_plus_core_family"
                item["recommended_action"] = "collect_or_recluster_sources_with_full_core_set_dossier_before_pm_review"
                deferred_family_candidates.append(item)
            else:
                item["recommended_action"] = "build_pm_review_packet"
                family_review_candidates.append(item)

    pm_attention_required_count = len(family_review_candidates) + len(species_review_candidates)
    return {
        "pm_attention_required_count": pm_attention_required_count,
        "family_review_candidates": family_review_candidates,
        "deferred_family_candidates": deferred_family_candidates,
        "species_review_candidates": species_review_candidates,
        "deferred_species_candidates": deferred_species_candidates,
        "already_reviewed_candidates": already_reviewed,
        "candidate_counts": {
            "new_family_review_candidates": len(family_review_candidates),
            "deferred_family_candidates": len(deferred_family_candidates),
            "new_species_review_candidates": len(species_review_candidates),
            "deferred_species_candidates": len(deferred_species_candidates),
            "already_reviewed_candidates": len(already_reviewed),
        },
    }


def _summarize_control_gate_lane(
    identity_axis_binding: dict[str, Any],
    identity_axis_path: Path | None,
    reviewer_ledger: dict[str, Any],
) -> dict[str, Any]:
    accepted_index = _accepted_axis_branch_index(reviewer_ledger)
    axis_branch_gates: list[dict[str, Any]] = []
    accepted_axis_branch_gates: list[dict[str, Any]] = []
    for report in identity_axis_binding.get("axis_reports") or []:
        species_name = str(report.get("species_name") or "")
        for candidate in report.get("axis_branch_candidates") or []:
            if candidate.get("status") != "candidate_for_pm_axis_branch_review":
                continue
            axis_id = str(candidate.get("axis_id") or "")
            gate = {
                "gate_type": "axis_branch_pm_review",
                "species_name": species_name,
                "axis_id": axis_id,
                "axis_label": candidate.get("axis_label"),
                "supported_branch_count": candidate.get("supported_branch_count"),
                "required_branch_count": candidate.get("required_branch_count"),
                "recommended_action": candidate.get("recommended_action"),
                "identity_axis_batch_id": identity_axis_binding.get("batch_id"),
                "identity_axis_path": _relpath(identity_axis_path) if identity_axis_path else "",
                "runtime_allowed": False,
            }
            accepted_resolution = accepted_index.get((species_name, axis_id))
            if accepted_resolution:
                gate["accepted_status"] = accepted_resolution.get("status")
                gate["accepted_at"] = accepted_resolution.get("accepted_at")
                gate["recommended_action"] = "use accepted axis boundary as control-plane policy only"
                accepted_axis_branch_gates.append(gate)
            else:
                axis_branch_gates.append(gate)
    return {
        "pm_attention_required_count": len(axis_branch_gates),
        "axis_branch_gates": axis_branch_gates,
        "accepted_axis_branch_gates": accepted_axis_branch_gates,
        "identity_axis_batch_id": identity_axis_binding.get("batch_id") if identity_axis_binding else "",
        "identity_axis_path": _relpath(identity_axis_path) if identity_axis_path else "",
    }


def _blocker_lane(consolidation: dict[str, Any], source_health: dict[str, Any]) -> dict[str, Any]:
    records = consolidation.get("species_records") or []
    split_blocked = [
        {
            "species_name": item.get("species_name"),
            "source_count": item.get("source_count"),
            "primary_source_count": item.get("primary_source_count"),
            "split_hypothesis_count": len(item.get("split_hypotheses") or []),
            "suggested_next_action": item.get("suggested_next_action"),
        }
        for item in records
        if item.get("state") == "split_blocked"
    ]
    needs_more = [
        {
            "species_name": item.get("species_name"),
            "observed_moves": [
                {
                    "move_name": move.get("move_name"),
                    "source_count": move.get("source_count"),
                    "primary_source_count": move.get("primary_source_count"),
                }
                for move in (item.get("observed_moves") or [])[:5]
            ],
            "suggested_next_action": item.get("suggested_next_action"),
        }
        for item in records
        if item.get("state") == "needs_more_source"
    ][:12]
    return {
        "split_blocked_species": split_blocked,
        "needs_more_source_species": needs_more,
        "transcript_blocked_sources": list(source_health.get("blocked_sources") or []),
        "known_transcript_blocked_sources": list(source_health.get("known_blocked_sources") or []),
        "missing_active_artifacts": {
            "missing_source_rows": list(source_health.get("missing_source_rows") or []),
            "missing_inventory_paths": list(source_health.get("missing_inventory_paths") or []),
        },
        "ignored_stale_inventory_count": source_health.get("ignored_stale_inventory_count", 0),
    }


def _next_action(
    source_health: dict[str, Any],
    control_gate_lane: dict[str, Any],
    promotion_lane: dict[str, Any],
    blocker_lane: dict[str, Any],
    *,
    remaining_volume_source_count: int = 0,
    volume_plan_selected_source_count: int = 0,
) -> dict[str, Any]:
    if source_health.get("missing_source_rows") or source_health.get("missing_inventory_paths"):
        return {
            "action": "repair_batch_artifacts_before_autorun",
            "reason": "active source ids are missing source queue rows or inventory artifacts",
            "pm_attention_required": False,
        }
    if control_gate_lane.get("pm_attention_required_count", 0) > 0:
        return {
            "action": "build_pm_axis_branch_review_packet",
            "reason": "axis-branch control-plane PM gate exists",
            "pm_attention_required": True,
        }
    if promotion_lane.get("pm_attention_required_count", 0) > 0:
        return {
            "action": "build_pm_review_packet_for_new_promotion_candidates",
            "reason": "new promotion-lane candidates exist",
            "pm_attention_required": True,
        }
    if 0 < volume_plan_selected_source_count < TARGET_BATCH_MIN and remaining_volume_source_count > 0:
        return {
            "action": "expand_source_discovery_before_volume_autorun",
            "reason": f"current volume batch plan selected only {volume_plan_selected_source_count} sources, below target batch size {TARGET_BATCH_MIN}-{TARGET_BATCH_MAX}",
            "pm_attention_required": False,
        }
    if remaining_volume_source_count > 0:
        action = "continue_volume_lane_and_queue_split_blockers" if blocker_lane.get("split_blocked_species") else "run_next_volume_batch"
        return {
            "action": action,
            "reason": f"current volume batch plan still has {remaining_volume_source_count} selected queued sources",
            "pm_attention_required": False,
        }
    queued_count = int(source_health.get("queued_source_count") or 0)
    if queued_count < TARGET_BATCH_MIN:
        return {
            "action": "expand_source_discovery_before_volume_autorun",
            "reason": f"queued source count {queued_count} is below target batch size {TARGET_BATCH_MIN}-{TARGET_BATCH_MAX}",
            "pm_attention_required": False,
        }
    if blocker_lane.get("split_blocked_species"):
        return {
            "action": "continue_volume_lane_and_queue_split_blockers",
            "reason": "split blockers exist, but no new PM decision is required yet",
            "pm_attention_required": False,
        }
    return {
        "action": "run_next_volume_batch",
        "reason": "source queue has enough capacity and no promotion-lane PM question is pending",
        "pm_attention_required": False,
    }


def build_dashboard(
    *,
    batch_id: str,
    queue: dict[str, Any],
    consolidation: dict[str, Any],
    family_ledger: dict[str, Any],
    reviewer_ledger: dict[str, Any],
    species_index: dict[str, list[str]],
    identity_axis_binding: dict[str, Any],
    identity_axis_path: Path | None,
    active_scope: ActiveScope,
    inventory_dir: Path,
) -> dict[str, Any]:
    source_map = _as_source_map(queue)
    source_health = _source_health(
        active_source_ids=active_scope.source_ids,
        source_map=source_map,
        inventory_dir=inventory_dir,
    )
    promotion_lane = _summarize_promotion_lane(consolidation, family_ledger, species_index)
    control_gate_lane = _summarize_control_gate_lane(identity_axis_binding, identity_axis_path, reviewer_ledger)
    blockers = _blocker_lane(consolidation, source_health)
    volume_batch_plan = queue.get("latest_volume_batch_plan") or {}
    selected_volume_source_ids = [str(item) for item in volume_batch_plan.get("selected_source_ids") or [] if item]
    remaining_volume_source_ids = [
        source_id
        for source_id in selected_volume_source_ids
        if str((source_map.get(source_id) or {}).get("ingest_status") or "queued") == "queued"
    ]
    completed_volume_source_ids = [
        source_id
        for source_id in selected_volume_source_ids
        if source_id not in remaining_volume_source_ids
    ]
    next_action = _next_action(
        source_health,
        control_gate_lane,
        promotion_lane,
        blockers,
        remaining_volume_source_count=len(remaining_volume_source_ids),
        volume_plan_selected_source_count=int(volume_batch_plan.get("selected_source_count") or len(selected_volume_source_ids) or 0),
    )
    state_counts = Counter(item.get("state") for item in consolidation.get("species_records") or [])
    latest_volume_ingest = queue.get("latest_volume_ingest") or {}
    queue_capacity_ready = int(source_health.get("queued_source_count") or 0) >= TARGET_BATCH_MIN
    volume_plan_has_remaining = bool(remaining_volume_source_ids)
    volume_plan_below_target = bool(volume_plan_has_remaining and 0 < int(volume_batch_plan.get("selected_source_count") or len(selected_volume_source_ids) or 0) < TARGET_BATCH_MIN)
    return {
        "schema_version": "p14.autorun_dashboard.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "scope": {
            "active_scope_source": active_scope.source,
            "consolidation_path": _relpath(active_scope.consolidation_path) if active_scope.consolidation_path else "",
            "target_batch_size": {"min": TARGET_BATCH_MIN, "max": TARGET_BATCH_MAX},
        },
        "active_source_ids": active_scope.source_ids,
        "source_health": source_health,
        "volume_batch_plan": {
            "batch_id": volume_batch_plan.get("batch_id"),
            "selected_source_count": volume_batch_plan.get("selected_source_count", 0),
            "selected_source_ids": list(volume_batch_plan.get("selected_source_ids") or []),
            "completed_selected_source_count": len(completed_volume_source_ids),
            "remaining_selected_source_count": len(remaining_volume_source_ids),
            "remaining_selected_source_ids": remaining_volume_source_ids,
            "plan_path": volume_batch_plan.get("plan_path"),
            "review_packet": volume_batch_plan.get("review_packet"),
            "latest_volume_ingest": {
                "batch_id": latest_volume_ingest.get("batch_id"),
                "processed_source_ids": list(latest_volume_ingest.get("processed_source_ids") or []),
                "blocked_source_ids": list(latest_volume_ingest.get("blocked_source_ids") or []),
                "review_packet": latest_volume_ingest.get("review_packet"),
            },
        },
        "consolidation_summary": consolidation.get("summary") or {},
        "state_counts": dict(sorted(state_counts.items())),
        "control_gate_lane": control_gate_lane,
        "promotion_lane": promotion_lane,
        "blocker_lane": blockers,
        "autorun_decision": {
            "volume_lane_ready": not bool(source_health.get("missing_source_rows") or source_health.get("missing_inventory_paths")),
            "control_gate_lane_has_new_pm_work": control_gate_lane.get("pm_attention_required_count", 0) > 0,
            "promotion_lane_has_new_pm_work": promotion_lane.get("pm_attention_required_count", 0) > 0,
            "queue_capacity_ready": queue_capacity_ready,
            "volume_plan_has_remaining": volume_plan_has_remaining,
            "volume_plan_below_target": volume_plan_below_target,
            "volume_lane_ready_to_continue": queue_capacity_ready or (volume_plan_has_remaining and not volume_plan_below_target),
            "next_action": next_action,
        },
    }


def render_dashboard_markdown(payload: dict[str, Any]) -> str:
    source_health = payload["source_health"]
    control_gates = payload.get("control_gate_lane") or {}
    promotion = payload["promotion_lane"]
    blockers = payload["blocker_lane"]
    decision = payload["autorun_decision"]
    volume_batch_plan = payload.get("volume_batch_plan") or {}
    next_action = decision["next_action"]
    summary = payload.get("consolidation_summary") or {}

    lines = [
        f"# P14 Autorun Dashboard: {payload['batch_id']}",
        "",
        "## 结论",
    ]
    total_pm_attention = int(control_gates.get("pm_attention_required_count") or 0) + int(
        promotion.get("pm_attention_required_count") or 0
    )
    if total_pm_attention == 0:
        if decision.get("volume_plan_below_target"):
            lines.append("- 这批没有新的 PM 必审项。当前 volume batch plan 低于 20 条可信批次下限，下一步应先自动扩源。")
        elif decision.get("volume_plan_has_remaining"):
            lines.append("- 这批没有新的 PM 必审项。当前 volume batch plan 还没跑完，先继续剩余源。")
        elif decision.get("queue_capacity_ready"):
            lines.append("- 这批没有新的 PM 必审项。不要继续手工精修单个 set，下一步应进入 volume lane 批跑。")
        else:
            lines.append("- 这批没有新的 PM 必审项。不要继续手工精修单个 set，下一步应先自动扩源。")
    else:
        if control_gates.get("pm_attention_required_count", 0) > 0:
            lines.append(f"- 有 {control_gates['pm_attention_required_count']} 个控制面 PM gate 需要先 review；先不要继续自动扩量或 promotion。")
        if promotion.get("pm_attention_required_count", 0) > 0:
            lines.append(f"- 有 {promotion['pm_attention_required_count']} 个新晋升候选需要单独 review；先不要自动 promotion。")
    if decision.get("volume_plan_below_target") and total_pm_attention == 0:
        lines.append(
            f"- 当前 volume batch plan 只选出 {volume_batch_plan.get('selected_source_count', 0)} 条 selected source，低于 20-30 条目标；先扩源，不用低多样性来源硬凑批次。"
        )
    elif decision.get("volume_plan_has_remaining"):
        if total_pm_attention > 0:
            lines.append(
                f"- 当前 volume batch plan 还剩 {volume_batch_plan.get('remaining_selected_source_count', 0)} 条 selected source；先停在 review gate，不继续自动跑。"
            )
        else:
            lines.append(f"- 当前 volume batch plan 还剩 {volume_batch_plan.get('remaining_selected_source_count', 0)} 条 selected source；先跑完这一批。")
    elif total_pm_attention > 0:
        lines.append(f"- 当前 queued source {source_health.get('queued_source_count', 0)} 条；控制面 gate 未处理前，先不扩源也不批跑。")
    elif decision.get("queue_capacity_ready"):
        lines.append("- 当前 queued source 数量足够跑 20-30 条量产批次。")
    else:
        lines.append(f"- 当前 queued source 只有 {source_health.get('queued_source_count', 0)} 条，不够 20-30 条；先自动找源扩队列。")
    lines.append(f"- 下一动作：`{next_action['action']}`。{next_action['reason']}。")

    lines.extend(
        [
            "",
            "## 批量 Lane 健康度",
            f"- Active sources：{source_health['active_source_count']} 条；字幕可用 {source_health['subtitle_ok_count']} 条。",
            f"- Active transcript blocked：{source_health['blocked_source_count']} 条；已知非本批 transcript blocked：{source_health.get('known_blocked_source_count', 0)} 条；repair-required source：{source_health['repair_required_source_count']} 条。",
            f"- 本轮只读取 active source ids；忽略 stale inventory artifacts：{source_health['ignored_stale_inventory_count']} 个。",
            f"- Consolidation：species {summary.get('species_count', 0)}，split_blocked {summary.get('split_blocked_count', 0)}，review_candidate {summary.get('review_candidate_count', 0)}，family_review_candidate {summary.get('family_review_candidate_count', 0)}。",
        ]
    )
    if volume_batch_plan.get("batch_id"):
        lines.append(
            f"- Latest volume batch plan：{volume_batch_plan.get('batch_id')}，selected {volume_batch_plan.get('selected_source_count', 0)} 条，已完成 {volume_batch_plan.get('completed_selected_source_count', 0)} 条，剩余 {volume_batch_plan.get('remaining_selected_source_count', 0)} 条。"
        )

    lines.extend(["", "## 控制面 Gate"])
    if control_gates.get("axis_branch_gates"):
        for item in control_gates["axis_branch_gates"]:
            lines.append(
                f"- axis_branch PM gate：{item.get('species_name')} `{item.get('axis_id')}`，{item.get('axis_label')}；支持分支 {item.get('supported_branch_count')}/{item.get('required_branch_count')}。"
            )
            if item.get("identity_axis_path"):
                lines.append(f"  - evidence packet：{item.get('identity_axis_path')}")
    else:
        lines.append("- 没有新的控制面 PM gate。")
    if control_gates.get("accepted_axis_branch_gates"):
        for item in control_gates["accepted_axis_branch_gates"]:
            lines.append(
                f"- 已接受 axis_branch：{item.get('species_name')} `{item.get('axis_id')}`，{item.get('axis_label')}；只作为控制面规则，不进 runtime。"
            )

    lines.extend(["", "## 晋升 Lane"])
    if promotion.get("family_review_candidates") or promotion.get("species_review_candidates"):
        for item in promotion.get("family_review_candidates") or []:
            core = " / ".join(item.get("core_moves") or []) or "无"
            lines.append(f"- 新 family review candidate：{item['species_name']} {item.get('family_id')}，core={core}，主证 {item.get('primary_source_count')} 条。")
        for item in promotion.get("species_review_candidates") or []:
            stable = " / ".join(item.get("stable_moves") or []) or "无"
            lines.append(f"- 新 species review candidate：{item['species_name']}，stable={stable}，主证 {item.get('primary_source_count')} 条。")
    else:
        lines.append("- 没有新的晋升候选需要你看。")
    if promotion.get("already_reviewed_candidates"):
        for item in promotion["already_reviewed_candidates"][:5]:
            core = " / ".join(item.get("core_moves") or []) or "无"
            note = "；含已审 flex，不自动升 core" if item.get("recommended_action") == "ledger_update_only_reviewed_flex_not_auto_core" else ""
            lines.append(f"- 已审候选只做 ledger/update：{item['species_name']} {item.get('family_id')}，core={core}，status={item.get('ledger_review_status')}{note}。")
    if promotion.get("deferred_family_candidates"):
        for item in promotion["deferred_family_candidates"][:5]:
            core = " / ".join(item.get("core_moves") or []) or "无"
            extra = ""
            if item.get("unreviewed_core_moves"):
                extra = f"；未审新增 core={' / '.join(item['unreviewed_core_moves'])}"
            lines.append(f"- 自动暂缓 family 候选：{item['species_name']} {item.get('family_id')}，core={core}，原因 {item.get('defer_reason')}{extra}。")
    if promotion.get("deferred_species_candidates"):
        for item in promotion["deferred_species_candidates"][:5]:
            stable = " / ".join(item.get("stable_moves") or []) or "无"
            lines.append(f"- 自动暂缓 species-level 候选：{item['species_name']}，stable={stable}，原因 {item.get('defer_reason')}。")

    lines.extend(["", "## Blocker Queue"])
    if blockers.get("split_blocked_species"):
        for item in blockers["split_blocked_species"][:8]:
            lines.append(f"- split_blocked：{item['species_name']}；主证 {item.get('primary_source_count')}；动作 {item.get('suggested_next_action')}。")
    else:
        lines.append("- 当前没有 split_blocked species。")
    if blockers.get("transcript_blocked_sources"):
        for item in blockers["transcript_blocked_sources"][:5]:
            lines.append(f"- transcript blocked：{item.get('source_id')}，原因 {item.get('reason')}。")
    if blockers.get("known_transcript_blocked_sources"):
        for item in blockers["known_transcript_blocked_sources"][:5]:
            lines.append(f"- known transcript blocked：{item.get('source_id')}，原因 {item.get('reason')}。")

    lines.extend(["", "## Agent 下一步"])
    if total_pm_attention > 0:
        if control_gates.get("pm_attention_required_count", 0) > 0:
            lines.append("- 先处理控制面 PM gate；不要继续跑剩余源，也不要做 graph/runtime promotion。")
            lines.append("- PM 未接受前，axis_branch 只作为审计候选，不进入 ledger 或 downstream promotion gate。")
        if promotion.get("pm_attention_required_count", 0) > 0:
            lines.append("- 先生成聚焦 PM review packet；不要继续跑剩余源，也不要做 runtime promotion。")
            lines.append("- PM 未接受前，新候选只留在 promotion lane，active candidate artifacts 继续 runtime-forbidden。")
    elif decision.get("volume_plan_below_target"):
        lines.append("- 先自动扩 source queue 到 20-30 条；不要用同一合集分页或低多样性来源硬凑 volume batch。")
        lines.append("- 扩源后重新生成 volume batch plan，再进入字幕/ASR 和 Set Inventory。")
    elif decision.get("volume_plan_has_remaining") or decision.get("queue_capacity_ready"):
        remaining_volume_ids = volume_batch_plan.get("remaining_selected_source_ids") or []
        if remaining_volume_ids:
            preview = " / ".join(remaining_volume_ids[:5])
            lines.append(f"- 继续当前 volume batch plan 的剩余源，下一段先跑：{preview}。")
        else:
            lines.append("- 当前 volume batch plan 已无剩余 queued 源；生成下一份 batch plan 后继续批跑。")
        if blockers.get("split_blocked_species"):
            lines.append("- split blockers 只进 blocker queue，用新来源验证，不要求 PM 当前决策。")
        lines.append("- 批量跑到 Set Inventory + consolidation + autorun dashboard。")
    else:
        lines.append("- 先自动扩 source queue 到 20-30 条，优先 team_explainer / matchup_counterplay，其次机制教程。")
        lines.append("- 扩源后批量跑到 Set Inventory + consolidation + autorun dashboard。")
    lines.append("- 只有 dashboard 出现新的晋升候选、schema 分叉、或高影响机制冲突时再叫 PM。")
    return "\n".join(lines) + "\n"


def _apply_queue_delta(queue_path: Path, queue: dict[str, Any], payload: dict[str, Any], dashboard_path: Path, packet_path: Path) -> None:
    # Dashboard generation can run near batch planning. Re-read before writing so
    # this metadata update does not clobber a newer source queue pointer.
    queue = _load_yaml(queue_path) or queue
    total_pm_attention = int((payload.get("control_gate_lane") or {}).get("pm_attention_required_count") or 0) + int(
        payload["promotion_lane"]["pm_attention_required_count"]
    )
    queue["latest_autorun_dashboard"] = {
        "batch_id": payload["batch_id"],
        "generated_at": payload["generated_at"],
        "dashboard_path": _relpath(dashboard_path),
        "review_packet": _relpath(packet_path),
        "active_source_count": payload["source_health"]["active_source_count"],
        "queued_source_count": payload["source_health"]["queued_source_count"],
        "pm_attention_required_count": total_pm_attention,
        "control_gate_pm_attention_required_count": (payload.get("control_gate_lane") or {}).get("pm_attention_required_count", 0),
        "promotion_pm_attention_required_count": payload["promotion_lane"]["pm_attention_required_count"],
        "next_action": payload["autorun_decision"]["next_action"]["action"],
        "runtime_allowed": False,
    }
    _write_yaml(queue_path, queue)


def run_autorun_dashboard(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    source_ids: set[str] | None = None,
    consolidation_path: Path | None = None,
    inventory_dir: Path = DEFAULT_INVENTORY_DIR,
    family_review_ledger: Path = DEFAULT_FAMILY_REVIEW_LEDGER,
    reviewer_ledger: Path | None = None,
    battle_dex: Path = DEFAULT_BATTLE_DEX,
    identity_axis_dir: Path | None = None,
    update_source_queue: bool = True,
) -> dict[str, Any]:
    queue = _load_yaml(source_queue)
    active_scope = resolve_active_scope(queue=queue, source_ids=source_ids, consolidation_path=consolidation_path)
    resolved_consolidation_path = active_scope.consolidation_path
    if not resolved_consolidation_path and source_ids:
        resolved_consolidation_path = None
    consolidation = _load_yaml(resolved_consolidation_path) if resolved_consolidation_path else {"species_records": [], "summary": {}}
    family_ledger = _load_yaml(family_review_ledger)
    reviewer_ledger = reviewer_ledger or family_review_ledger.parent / "reviewer_ledger.yaml"
    reviewer_state = _load_yaml(reviewer_ledger)
    species_index = _species_id_index(battle_dex)
    identity_axis_dir = identity_axis_dir or out_root / IDENTITY_AXIS_DIRNAME
    identity_axis_path, identity_axis_binding = _latest_identity_axis_binding(identity_axis_dir)
    payload = build_dashboard(
        batch_id=batch_id,
        queue=queue,
        consolidation=consolidation,
        family_ledger=family_ledger,
        reviewer_ledger=reviewer_state,
        species_index=species_index,
        identity_axis_binding=identity_axis_binding,
        identity_axis_path=identity_axis_path,
        active_scope=active_scope,
        inventory_dir=inventory_dir,
    )
    dashboard_path = out_root / AUTORUN_DIRNAME / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_autorun_dashboard.md"
    _write_yaml(dashboard_path, payload)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_dashboard_markdown(payload), encoding="utf-8")
    if update_source_queue:
        _apply_queue_delta(source_queue, queue, payload, dashboard_path, packet_path)
    total_pm_attention = int(payload["control_gate_lane"]["pm_attention_required_count"]) + int(
        payload["promotion_lane"]["pm_attention_required_count"]
    )
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "dashboard": _relpath(dashboard_path),
            "pm_dashboard": _relpath(packet_path),
            "source_queue": _relpath(source_queue),
        },
        "summary": {
            "active_source_count": payload["source_health"]["active_source_count"],
            "queued_source_count": payload["source_health"]["queued_source_count"],
            "pm_attention_required_count": total_pm_attention,
            "control_gate_pm_attention_required_count": payload["control_gate_lane"]["pm_attention_required_count"],
            "promotion_pm_attention_required_count": payload["promotion_lane"]["pm_attention_required_count"],
            "split_blocked_count": len(payload["blocker_lane"]["split_blocked_species"]),
            "transcript_blocked_count": len(payload["blocker_lane"]["transcript_blocked_sources"]),
            "known_transcript_blocked_count": len(payload["blocker_lane"]["known_transcript_blocked_sources"]),
            "next_action": payload["autorun_decision"]["next_action"]["action"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--consolidation-path", type=Path)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
    parser.add_argument("--family-review-ledger", type=Path, default=DEFAULT_FAMILY_REVIEW_LEDGER)
    parser.add_argument("--reviewer-ledger", type=Path)
    parser.add_argument("--battle-dex", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--identity-axis-dir", type=Path)
    parser.add_argument("--no-update-source-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_autorun_dashboard(
        source_queue=args.source_queue,
        out_root=args.out_root,
        batch_id=args.batch_id,
        source_ids=set(args.source_id) if args.source_id else None,
        consolidation_path=args.consolidation_path,
        inventory_dir=args.inventory_dir,
        family_review_ledger=args.family_review_ledger,
        reviewer_ledger=args.reviewer_ledger,
        battle_dex=args.battle_dex,
        identity_axis_dir=args.identity_axis_dir,
        update_source_queue=not args.no_update_source_queue,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"autorun dashboard: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
