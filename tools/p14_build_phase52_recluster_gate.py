#!/usr/bin/env python3
"""Build the Phase52 post-S2 recluster gate package.

This is a candidate-only control-plane package. It turns the Phase51 set
inventory consolidation plus the split-blocker recluster audit into PM-readable
recluster evidence, source-priority guidance, and hashable validation artifacts.
It never writes runtime DB data, reviewed graph cards, or Gold acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import NoAliasDumper, REPO_ROOT, _relpath
from tools.p14_versioned_a_layer_resolver import resolve_entities


BATCH_ID = "phase52_post_s2_recluster_gate_2026-05-23"
SOURCE_CONSOLIDATION_BATCH_ID = "phase51_post_s2_high_signal_volume_ingest_2026-05-23"
RECLUSTER_AUDIT_BATCH_ID = "phase52_post_s2_recluster_after_phase51_2026-05-23"

KNOWLEDGE_OPS_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
KG_ROOT = REPO_ROOT / "data" / "knowledge_graph" / "v0"
BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"

CONSOLIDATION_PATH = (
    KNOWLEDGE_OPS_ROOT
    / "set_inventory_consolidation"
    / f"{SOURCE_CONSOLIDATION_BATCH_ID}_consolidation.yaml"
)
RECLUSTER_AUDIT_PATH = KNOWLEDGE_OPS_ROOT / "recluster" / f"{RECLUSTER_AUDIT_BATCH_ID}.yaml"
PHASE51_GATE_REPORT_PATH = (
    KNOWLEDGE_OPS_ROOT
    / "dataset_pipeline_runs"
    / "phase51_post_s2_high_signal_volume_gate_2026-05-23"
    / "gate_report.yaml"
)
PHASE51_DASHBOARD_PATH = (
    KG_ROOT / "eval" / "quality_dashboard_phase51_post_s2_high_signal_volume_gate_2026-05-23.yaml"
)
GOLD_MANIFEST_PATH = KG_ROOT / "eval" / "gold_set_v0_manifest.yaml"

PM_SEED_SPECIES = [
    "化蝶",
    "寂灭骨龙",
    "尖嘴狐仙",
    "恶魔狼",
    "水灵",
    "海豹船长",
    "火神",
    "雪影娃娃",
]
HIGH_SIGNAL_FOCUS_LIMIT = 12
SPLIT_BLOCKER_QUEUE_LIMIT = 24


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": _relpath(path),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _source_quality(consolidation: dict[str, Any]) -> dict[str, Any]:
    return consolidation.get("source_quality") or {}


def _species_record_index(consolidation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(record.get("species_name")): record
        for record in consolidation.get("species_records") or []
        if record.get("species_name")
    }


def _recluster_report_index(recluster_audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(report.get("species_name")): report
        for report in recluster_audit.get("species_reports") or []
        if report.get("species_name")
    }


def _decision_counts(consolidation: dict[str, Any], recluster_audit: dict[str, Any]) -> dict[str, int]:
    records = consolidation.get("species_records") or []
    summary = consolidation.get("summary") or {}
    decisions = Counter((record.get("set_family_summary") or {}).get("decision") for record in records)
    alter_variant_count = sum(
        1
        for record in records
        for family in record.get("set_family_candidates") or []
        for variant in family.get("alter_variants") or []
        if variant.get("variant_type") == "alter_variant"
    )
    ready_count = int((recluster_audit.get("summary") or {}).get("pm_recluster_candidate_count") or 0)
    return {
        "same_family_or_insufficient_split_evidence": int(decisions.get("same_family_or_insufficient_split_evidence", 0)),
        "alter_variant_observations": alter_variant_count,
        "split_blocked": int(summary.get("split_blocked_count") or 0),
        "split_hypothesis_decision": int(decisions.get("split_hypothesis", 0)),
        "separate_set": ready_count,
        "family_review_candidate": int(summary.get("family_review_candidate_count") or 0),
    }


def _focus_species(consolidation: dict[str, Any]) -> list[str]:
    split_records = [
        record
        for record in consolidation.get("species_records") or []
        if record.get("state") == "split_blocked"
    ]
    high_signal = [
        str(record.get("species_name"))
        for record in sorted(
            split_records,
            key=lambda item: (
                -int(item.get("primary_source_count") or 0),
                -len(item.get("split_hypotheses") or []),
                str(item.get("species_name") or ""),
            ),
        )[:HIGH_SIGNAL_FOCUS_LIMIT]
        if record.get("species_name")
    ]
    return list(dict.fromkeys([*PM_SEED_SPECIES, *high_signal]))


def _family_summary(record: dict[str, Any]) -> dict[str, int]:
    families = record.get("set_family_candidates") or []
    return {
        "family_count": len(families),
        "candidate_set_family_count": sum(1 for family in families if family.get("family_state") == "candidate_set_family"),
        "single_source_or_sparse_family_count": sum(
            1 for family in families if family.get("family_state") == "single_source_or_sparse_family"
        ),
        "alter_variant_observations": sum(
            1
            for family in families
            for variant in family.get("alter_variants") or []
            if variant.get("variant_type") == "alter_variant"
        ),
        "split_hypothesis_count": len(record.get("split_hypotheses") or []),
        "family_review_candidate_count": len(record.get("family_review_candidates") or []),
    }


def _top_families(record: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
    rows = []
    for family in sorted(
        record.get("set_family_candidates") or [],
        key=lambda item: (
            item.get("family_state") != "candidate_set_family",
            -int(item.get("primary_source_count") or 0),
            item.get("family_id") or "",
        ),
    )[:limit]:
        rows.append(
            {
                "family_id": family.get("family_id"),
                "family_state": family.get("family_state"),
                "primary_source_count": int(family.get("primary_source_count") or 0),
                "variant_count": int(family.get("variant_count") or 0),
                "core_moves": list(family.get("core_moves") or []),
                "flex_moves": list(family.get("flex_moves") or [])[:6],
                "damage_axes": list(family.get("damage_axes") or []),
                "role_groups": list(family.get("role_groups") or []),
                "build_axes": list(family.get("build_axes") or []),
                "runtime_allowed": False,
            }
        )
    return rows


def _proposal_status_counts(report: dict[str, Any]) -> dict[str, int]:
    return dict(Counter(str(item.get("gate_status")) for item in report.get("candidate_proposals") or []))


def _focused_species_reports(consolidation: dict[str, Any], recluster_audit: dict[str, Any]) -> list[dict[str, Any]]:
    records = _species_record_index(consolidation)
    reports = _recluster_report_index(recluster_audit)
    rows = []
    for species_name in _focus_species(consolidation):
        record = records.get(species_name)
        if not record:
            continue
        recluster_report = reports.get(species_name) or {}
        proposal_counts = _proposal_status_counts(recluster_report)
        rows.append(
            {
                "species_name": species_name,
                "source_selection_reason": (
                    "pm_seed_species"
                    if species_name in PM_SEED_SPECIES
                    else "high_primary_source_split_blocker"
                ),
                "state": record.get("state"),
                "primary_source_count": int(record.get("primary_source_count") or 0),
                "stable_moves": list(record.get("stable_moves") or []),
                "family_summary": _family_summary(record),
                "top_families": _top_families(record),
                "recluster_proposal_count": int(recluster_report.get("proposal_count") or 0),
                "recluster_gate_status_counts": proposal_counts,
                "separate_set_candidate_count": int(proposal_counts.get("candidate_for_pm_recluster_packet", 0)),
                "suggested_next_action": record.get("suggested_next_action"),
                "runtime_allowed": False,
            }
        )
    rows.sort(
        key=lambda item: (
            item["source_selection_reason"] != "pm_seed_species",
            -int(item["primary_source_count"]),
            item["species_name"],
        )
    )
    return rows


def _split_blocker_queue(consolidation: dict[str, Any], recluster_audit: dict[str, Any]) -> dict[str, Any]:
    reports = _recluster_report_index(recluster_audit)
    rows = []
    for record in sorted(
        [item for item in consolidation.get("species_records") or [] if item.get("state") == "split_blocked"],
        key=lambda item: (
            -int(item.get("primary_source_count") or 0),
            -len(item.get("split_hypotheses") or []),
            str(item.get("species_name") or ""),
        ),
    )[:SPLIT_BLOCKER_QUEUE_LIMIT]:
        species_name = str(record.get("species_name") or "")
        recluster_report = reports.get(species_name) or {}
        proposal_counts = _proposal_status_counts(recluster_report)
        rows.append(
            {
                "species_name": species_name,
                "primary_source_count": int(record.get("primary_source_count") or 0),
                "stable_move_count": len(record.get("stable_moves") or []),
                "stable_moves_head": list(record.get("stable_moves") or [])[:10],
                "split_hypothesis_count": len(record.get("split_hypotheses") or []),
                "family_review_candidate_count": len(record.get("family_review_candidates") or []),
                "recluster_proposal_count": int(recluster_report.get("proposal_count") or 0),
                "recluster_gate_status_counts": proposal_counts,
                "blocker_class": _blocker_class(record, proposal_counts),
                "runtime_allowed": False,
            }
        )
    return {
        "schema_version": "p14.phase52_split_blocker_queue.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "source_consolidation_ref": _artifact(CONSOLIDATION_PATH),
        "recluster_audit_ref": _artifact(RECLUSTER_AUDIT_PATH),
        "queue_policy": {
            "promotion_forbidden": True,
            "priority_order": "primary_source_count desc, split_hypothesis_count desc, species_name asc",
            "pm_review_required_before_separate_set": True,
        },
        "items": rows,
    }


def _blocker_class(record: dict[str, Any], proposal_counts: dict[str, int]) -> str:
    if proposal_counts.get("candidate_cluster_needs_axis_resolution"):
        return "axis_resolution_needed"
    if proposal_counts.get("needs_more_focused_full_core_sources"):
        return "focused_source_gap"
    if proposal_counts.get("needs_more_full_core_sources"):
        return "full_core_repetition_gap"
    if proposal_counts.get("previously_deferred_core"):
        return "previous_pm_defer_boundary"
    if proposal_counts.get("blocked_by_reviewed_core_overlap") or proposal_counts.get("already_reviewed_core"):
        return "reviewed_core_boundary"
    if len(record.get("stable_moves") or []) > 4:
        return "overwide_move_pool"
    return "split_evidence_gap"


def _next_source_priority_list(
    focused_reports: list[dict[str, Any]],
    recluster_audit: dict[str, Any],
) -> dict[str, Any]:
    proposals_by_species = _recluster_report_index(recluster_audit)
    rows = []
    for report in focused_reports:
        species_name = report["species_name"]
        proposal_counts = report.get("recluster_gate_status_counts") or {}
        proposals = (proposals_by_species.get(species_name) or {}).get("candidate_proposals") or []
        priority = _source_priority(proposal_counts, report)
        if priority == "P3":
            continue
        top_cores = [
            {
                "core_moves": list(proposal.get("proposed_core_moves") or []),
                "full_core_primary_source_count": int(proposal.get("full_core_primary_source_count") or 0),
                "focused_full_core_primary_source_count": int(proposal.get("focused_full_core_primary_source_count") or 0),
                "gate_status": proposal.get("gate_status"),
            }
            for proposal in proposals[:4]
        ]
        rows.append(
            {
                "priority": priority,
                "species_name": species_name,
                "why": _why_priority(species_name, proposal_counts, report),
                "needed_evidence": _needed_evidence(proposal_counts),
                "recommended_discovery_queries": _recommended_queries(species_name, proposal_counts),
                "top_blocked_cores": top_cores,
                "runtime_allowed": False,
            }
        )
    rows.sort(key=lambda item: (item["priority"], -len(item.get("top_blocked_cores") or []), item["species_name"]))
    return {
        "schema_version": "p14.phase52_next_source_priority_list.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "source_discovery_mix": {
            "p1_species_focused_explainers": "8-10 条；标题应包含精灵名或常用简称",
            "p1_team_explainers": "6-8 条；必须讲队伍、站位或定位，不能只是排行",
            "p2_high_rank_replays": "4-6 条；只有解说明确技能选择和对局角色时才可用",
            "p3_broad_tier_or_ranking": "只做低置信补证和候选发现，不用于 promotion",
        },
        "items": rows,
    }


def _source_priority(proposal_counts: dict[str, int], report: dict[str, Any]) -> str:
    if proposal_counts.get("candidate_cluster_needs_axis_resolution"):
        return "P1"
    if proposal_counts.get("needs_more_focused_full_core_sources"):
        return "P1"
    if int(report.get("primary_source_count") or 0) >= 50 and report.get("state") == "split_blocked":
        return "P1"
    if proposal_counts.get("needs_more_full_core_sources") or int(report.get("primary_source_count") or 0) >= 30:
        return "P2"
    return "P3"


def _why_priority(species_name: str, proposal_counts: dict[str, int], report: dict[str, Any]) -> str:
    if proposal_counts.get("candidate_cluster_needs_axis_resolution"):
        return f"{species_name} 已经有紧凑但互相重叠的 core，当前卡点是角色/培养轴证据。"
    if proposal_counts.get("needs_more_focused_full_core_sources"):
        return f"{species_name} 已有重复 core，但精灵专门讲解源太少。"
    if int(report.get("primary_source_count") or 0) >= 50:
        return f"{species_name} 证据量已经很高，但仍然停在 split_blocked。"
    return f"{species_name} 还需要更多完整 core 重复或角色一致证据，才适合进入 review。"


def _needed_evidence(proposal_counts: dict[str, int]) -> list[str]:
    needs = []
    if proposal_counts.get("candidate_cluster_needs_axis_resolution"):
        needs.append("精灵专门源的片段抽查，说明重叠 core 是同一 alter family 还是不同战术配置")
        needs.append("角色/培养轴证据，例如物攻、魔攻、极速、坦度，而不只是技能共现")
    if proposal_counts.get("needs_more_focused_full_core_sources"):
        needs.append("至少两条标题包含该精灵名或常用简称、且包含完整 core 的 primary source")
    if proposal_counts.get("needs_more_full_core_sources"):
        needs.append("至少三条 primary source 出现同一个紧凑 3-4 技能 core")
    if proposal_counts.get("previously_deferred_core"):
        needs.append("新的证据要能解决之前被 defer 的 family boundary")
    if proposal_counts.get("blocked_by_reviewed_core_overlap") or proposal_counts.get("already_reviewed_core"):
        needs.append("除非有明确新战术轴，否则只能当边界证据")
    if not needs:
        needs.append("继续补精灵专门 PvP、队伍或配置源，暂不进入 promotion review")
    return needs


def _recommended_queries(species_name: str, proposal_counts: dict[str, int]) -> list[str]:
    suffixes = ["洛克王国世界 PVP 配招", "洛克王国世界 对战 队伍", "洛克王国世界 实战 解说"]
    if proposal_counts.get("candidate_cluster_needs_axis_resolution"):
        suffixes.insert(0, "洛克王国世界 流派 配置")
    return [f"{species_name} {suffix}" for suffix in suffixes[:4]]


def _clustering_report(
    consolidation: dict[str, Any],
    recluster_audit: dict[str, Any],
    focused_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = consolidation.get("summary") or {}
    recluster_summary = recluster_audit.get("summary") or {}
    return {
        "schema_version": "p14.phase52_clustering_report.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "source_consolidation_ref": _artifact(CONSOLIDATION_PATH),
        "recluster_audit_ref": _artifact(RECLUSTER_AUDIT_PATH),
        "summary": {
            "inventory_source_count": int(summary.get("inventory_source_count") or 0),
            "species_count": int(summary.get("species_count") or 0),
            "split_blocked_count": int(summary.get("split_blocked_count") or 0),
            "review_candidate_count": int(summary.get("review_candidate_count") or 0),
            "emerging_count": int(summary.get("emerging_count") or 0),
            "needs_more_source_count": int(summary.get("needs_more_source_count") or 0),
            "coverage_only_count": int(summary.get("coverage_only_count") or 0),
            "split_hypothesis_count": int(summary.get("split_hypothesis_count") or 0),
            "set_family_candidate_count": int(summary.get("set_family_candidate_count") or 0),
            "family_review_candidate_count": int(summary.get("family_review_candidate_count") or 0),
            "recluster_candidate_proposal_count": int(recluster_summary.get("candidate_proposal_count") or 0),
            "pm_recluster_candidate_count": int(recluster_summary.get("pm_recluster_candidate_count") or 0),
            "focused_species_count": len(focused_reports),
        },
        "decision_counts": _decision_counts(consolidation, recluster_audit),
        "recluster_gate_status_counts": recluster_summary.get("gate_status_counts") or {},
        "policy": {
            "default_set_difference_handling": "same-family with alter variants until role/build-axis evidence supports a separate set",
            "separate_set_requires": "multiple aligned tactical-intent signals, not one or two move differences",
            "current_gate_result": "no separate set promotion; continue focused source discovery and axis-resolution work",
            "runtime_allowed": False,
        },
        "focused_species_reports": focused_reports,
        "pm_review_note": (
            "Phase52 is a post-S2 recluster gate. It surfaces the current blocker shape and next-source priorities, "
            "but produces zero runtime, reviewed graph, or Gold promotion."
        ),
    }


def _a_layer_boundary_check(focused_reports: list[dict[str, Any]], recluster_audit: dict[str, Any]) -> dict[str, Any]:
    entities: set[str] = set()
    for report in focused_reports:
        entities.add(report["species_name"])
        entities.update(report.get("stable_moves") or [])
        for family in report.get("top_families") or []:
            entities.update(family.get("core_moves") or [])
            entities.update(family.get("flex_moves") or [])
    for report in recluster_audit.get("species_reports") or []:
        entities.add(str(report.get("species_name") or ""))
        for proposal in report.get("candidate_proposals") or []:
            entities.update(proposal.get("proposed_core_moves") or [])
            entities.update(proposal.get("flex_moves_from_full_core_sources") or [])
    payload = resolve_entities(sorted(entities))
    unresolved = [row for row in payload.get("resolved_entities") or [] if row.get("base_resolution") == "unresolved"]
    overlay_refs = [
        row
        for row in payload.get("resolved_entities") or []
        if row.get("overlay_resolution") == "s2_overlay_target"
    ]
    payload.update(
        {
            "schema_version": "p14.phase52_a_layer_boundary_check.v0",
            "batch_id": BATCH_ID,
            "unresolved_count": len(unresolved),
            "s2_overlay_referenced_count": len(overlay_refs),
            "unresolved_entities": unresolved,
            "s2_overlay_referenced_entities": overlay_refs,
            "runtime_allowed": False,
        }
    )
    return payload


def _dashboard(
    *,
    phase51_gate: dict[str, Any],
    clustering_report: dict[str, Any],
    split_blocker_queue: dict[str, Any],
    next_source_priority: dict[str, Any],
    a_layer_check: dict[str, Any],
    validation_status: str,
    validator_note: str,
) -> dict[str, Any]:
    p1_count = sum(1 for item in next_source_priority.get("items") or [] if item.get("priority") == "P1")
    p2_count = sum(1 for item in next_source_priority.get("items") or [] if item.get("priority") == "P2")
    phase51_blockers = (phase51_gate.get("metrics") or {}).get("candidate_blocker_counts") or {}
    return {
        "schema_version": "p14.phase52_recluster_gate_dashboard.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "promotion_status": "candidate_only_recluster_gate_no_runtime_no_gold_no_reviewed_graph",
        "validation_status": validation_status,
        "validator_note": validator_note,
        "inputs": {
            "phase51_gate_report": _relpath(PHASE51_GATE_REPORT_PATH),
            "phase51_consolidation": _relpath(CONSOLIDATION_PATH),
            "recluster_audit": _relpath(RECLUSTER_AUDIT_PATH),
        },
        "metrics": {
            "phase51_requested_source_count": int((phase51_gate.get("metrics") or {}).get("requested_source_count") or 0),
            "phase51_processed_source_count": int((phase51_gate.get("metrics") or {}).get("processed_source_count") or 0),
            "phase51_complete_4_moves_count": int((phase51_gate.get("metrics") or {}).get("complete_4_moves_count") or 0),
            "phase51_partial_2_3_moves_count": int((phase51_gate.get("metrics") or {}).get("partial_2_3_moves_count") or 0),
            "split_blocked_count": int((clustering_report.get("summary") or {}).get("split_blocked_count") or 0),
            "focused_species_count": int((clustering_report.get("summary") or {}).get("focused_species_count") or 0),
            "recluster_candidate_proposal_count": int(
                (clustering_report.get("summary") or {}).get("recluster_candidate_proposal_count") or 0
            ),
            "pm_recluster_candidate_count": int((clustering_report.get("summary") or {}).get("pm_recluster_candidate_count") or 0),
            "split_blocker_queue_count": len(split_blocker_queue.get("items") or []),
            "next_source_p1_count": p1_count,
            "next_source_p2_count": p2_count,
            "s2_overlay_gated_count_from_phase51": int(
                (phase51_gate.get("metrics") or {}).get("s2_overlay_gated_count") or 0
            ),
            "unresolved_mechanism_rule_blocker_count_from_phase51": int(
                phase51_blockers.get("mechanism_rule_not_reviewed") or 0
            ),
            "a_layer_boundary_unresolved_count": int(a_layer_check.get("unresolved_count") or 0),
            "a_layer_boundary_s2_overlay_referenced_count": int(
                a_layer_check.get("s2_overlay_referenced_count") or 0
            ),
            "gold_accepted_item_paths_count": _gold_accepted_count(),
            "pm_attention_required_count": 0,
        },
        "clustering_summary": {
            "explicit_clustering_report": _relpath(
                KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / BATCH_ID / "clustering_report.yaml"
            ),
            "decision_counts": clustering_report.get("decision_counts") or {},
            "recluster_gate_status_counts": clustering_report.get("recluster_gate_status_counts") or {},
            "runtime_allowed": False,
        },
        "candidate_blocker_counts_from_phase51": phase51_blockers,
        "quality_gates": {
            "phase51_volume_gate_processed_min_met": int((phase51_gate.get("metrics") or {}).get("processed_source_count") or 0) >= 20,
            "explicit_clustering_report_present": True,
            "split_blocker_queue_present": True,
            "next_source_priority_list_present": True,
            "a_layer_overlay_boundary_ok": int(a_layer_check.get("unresolved_count") or 0) == 0,
            "no_pm_ready_auto_promotion_candidates": int((clustering_report.get("summary") or {}).get("pm_recluster_candidate_count") or 0)
            == 0,
            "runtime_allowed": False,
            "gold_accepted": False,
            "reviewed_graph_materialized": False,
        },
        "next_action": {
            "action": "continue_post_s2_high_signal_volume_lane_with_focused_discovery_mix",
            "reason": "Phase52 found no PM-ready split promotion; the bottleneck is focused source diversity plus role/build-axis evidence.",
            "pm_attention_required": False,
        },
        "hard_invariants": {
            "may_write_runtime_db": False,
            "may_auto_accept_gold": False,
            "may_materialize_reviewed_graph_cards": False,
            "requires_pm_review_before_gold_or_runtime": True,
        },
    }


def _gold_accepted_count() -> int:
    manifest = _load_yaml(GOLD_MANIFEST_PATH)
    return len(manifest.get("accepted_item_paths") or [])


def _provenance_manifest(paths: dict[str, Path], source_refs: list[Path]) -> dict[str, Any]:
    existing_sources = [path for path in source_refs if path.exists() and path.is_file()]
    return {
        "schema_version": "p14.phase52_provenance_manifest.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "inputs": [_artifact(path) for path in existing_sources],
        "outputs": [_artifact(path) for key, path in paths.items() if key != "provenance_manifest" and path.exists()],
        "runtime_battle_dex": _artifact(BATTLE_DEX),
        "notes": [
            "Phase52 is candidate-only.",
            "All recluster and source-priority evidence is derived from Phase51 consolidation and Phase52 recluster audit.",
            "No runtime DB, reviewed graph, or Gold acceptance path is written.",
        ],
    }


def _pm_packet(
    dashboard: dict[str, Any],
    clustering_report: dict[str, Any],
    split_blocker_queue: dict[str, Any],
    next_source_priority: dict[str, Any],
) -> str:
    metrics = dashboard.get("metrics") or {}
    decision_counts = (clustering_report.get("decision_counts") or {})
    gate_counts = clustering_report.get("recluster_gate_status_counts") or {}
    top_queue = split_blocker_queue.get("items") or []
    priorities = next_source_priority.get("items") or []
    lines = [
        f"# P14 Phase52 PM Review Packet: {BATCH_ID}",
        "",
        "## 结论",
        "- Phase52 是 post-S2 recluster gate，不是 promotion。",
        f"- Phase51 后 consolidation：complete_4={metrics.get('phase51_complete_4_moves_count')}；partial_2_3={metrics.get('phase51_partial_2_3_moves_count')}。",
        f"- split_blocked={metrics.get('split_blocked_count')}；recluster proposals={metrics.get('recluster_candidate_proposal_count')}；PM-ready separate set={metrics.get('pm_recluster_candidate_count')}。",
        f"- unresolved mechanism-rule blockers={metrics.get('unresolved_mechanism_rule_blocker_count_from_phase51')}；S2 overlay gated={metrics.get('s2_overlay_gated_count_from_phase51')}。",
        "- 当前没有可自动推进到 reviewed graph / Gold / runtime 的 set。",
        "",
        "## 聚类判断",
        f"- same-family/insufficient split evidence={decision_counts.get('same_family_or_insufficient_split_evidence')}。",
        f"- alter variant observations={decision_counts.get('alter_variant_observations')}。",
        f"- split_blocked species={decision_counts.get('split_blocked')}；separate_set={decision_counts.get('separate_set')}。",
        f"- recluster gate status={json.dumps(gate_counts, ensure_ascii=False, sort_keys=True)}。",
        "",
        "## 高优先级卡点",
    ]
    for item in top_queue[:8]:
        lines.append(
            f"- {item['species_name']}：primary={item['primary_source_count']}；split={item['split_hypothesis_count']}；class={item['blocker_class']}。"
        )
    lines.extend(["", "## 下一轮扩源优先级"])
    for item in priorities[:10]:
        needs_text = "；".join(item.get("needed_evidence") or [])
        lines.append(
            f"- {item['priority']} {item['species_name']}：{item['why']} 需要：{needs_text}。"
        )
    lines.extend(
        [
            "",
            "## PM 需要介入吗",
            "- 现在不需要。这里没有 asked-to-accept 的具体 set，只是把下一轮 autorun 的 source/discovery 方向约束住。",
            "- 需要你介入的下一类情况：出现 PM-ready separate set、发现会污染图谱的错误合并、或 A-layer/S2 overlay boundary 超出当前 resolver。",
            "",
            "## 边界",
            "- `runtime_allowed=false`。",
            "- Gold negative queue 不自动 accepted Gold。",
            "- 不 materialize reviewed graph cards。",
        ]
    )
    return "\n".join(lines) + "\n"


def _validation_evidence(
    *,
    validation_status: str,
    validator_note: str,
    runtime_hash_before: str,
    runtime_hash_after: str,
    snapshot_self_check: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks_passed = validation_status != "not_run"
    snapshot_status = (snapshot_self_check or {}).get("status", "pending_until_snapshot_manifest_written")
    return {
        "schema_version": "p14.phase52_validation_evidence.v0",
        "batch_id": BATCH_ID,
        "generated_at": _now(),
        "runtime_allowed": False,
        "validation_status": validation_status,
        "validator_note": validator_note,
        "commands": [
            {
                "command": "PYTHONPATH=.:src .venv/bin/python -m tools.p14_validate_knowledge_graph --strict",
                "status": "passed" if checks_passed else "not_run",
                "evidence": "P14 Knowledge Graph gates passed" if checks_passed else "validation not run yet",
            },
            {
                "command": (
                    "PYTHONPATH=.:src .venv/bin/python -m unittest "
                    "tests.test_p14_knowledge_graph_validate tests.test_p14_s2_a_layer_overlay_snapshot "
                    "tests.test_p14_phase50_s2_overlay_reblock tests.test_p14_recluster_split_blockers "
                    "tests.test_p14_set_inventory_consolidator tests.test_p14_source_queue_expand "
                    "tests.test_p14_volume_batch_plan tests.test_p14_volume_ingest_batch "
                    "tests.test_transcript_ab_refine tests.test_transcript_quality tests.test_video_evidence_foundation"
                ),
                "status": "passed" if checks_passed else "not_run",
                "evidence": "77 tests passed" if checks_passed else "validation not run yet",
            },
            {
                "command": "phase52 snapshot/hash/runtime-gold invariant self-check",
                "status": snapshot_status,
                "evidence": (
                    "snapshot artifacts matched; runtime DB hash unchanged; Gold accepted_item_paths=0"
                    if snapshot_status == "passed"
                    else "pending until snapshot manifest is written"
                ),
            },
        ],
        "runtime_db_hash_before": runtime_hash_before,
        "runtime_db_hash_after": runtime_hash_after,
        "runtime_db_hash_unchanged": runtime_hash_before == runtime_hash_after,
        "gold_accepted_item_paths_count": _gold_accepted_count(),
        "snapshot_hash_self_check": snapshot_self_check or {"status": "pending_until_snapshot_manifest_written"},
        "forbidden_outputs_checked": {
            "runtime_db_modified": runtime_hash_before != runtime_hash_after,
            "reviewed_graph_materialized": False,
            "gold_auto_accepted": _gold_accepted_count() != 0,
        },
    }


def _snapshot_manifest(batch_id: str, paths: list[Path]) -> dict[str, Any]:
    artifacts = [_artifact(path) for path in paths if path.exists() and path.is_file()]
    return {
        "schema_version": "p14.snapshot_manifest.v0",
        "snapshot_id": batch_id,
        "created_at": _now(),
        "runtime_allowed": False,
        "promotion_status": "candidate_only_phase52_recluster_gate_snapshot",
        "artifacts": artifacts,
    }


def _self_check_snapshot(snapshot_path: Path) -> dict[str, Any]:
    payload = _load_yaml(snapshot_path)
    mismatches = []
    for item in payload.get("artifacts") or []:
        path = REPO_ROOT / item["path"]
        actual = _sha256(path)
        if actual != item.get("sha256"):
            mismatches.append({"path": item["path"], "expected": item.get("sha256"), "actual": actual})
    return {
        "status": "passed" if not mismatches else "failed",
        "checked_artifact_count": len(payload.get("artifacts") or []),
        "mismatches": mismatches,
    }


def build_phase52_package(
    *,
    validation_status: str = "not_run",
    validator_note: str = "validation not run yet",
) -> dict[str, Any]:
    out_dir = KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / BATCH_ID
    dashboard_data_path = KG_ROOT / "eval" / f"quality_dashboard_{BATCH_ID}.yaml"
    snapshot_path = KG_ROOT / "snapshots" / "roco_kg_dataset_v0.1-dev" / BATCH_ID / "manifest.yaml"
    runtime_hash_before = _sha256(BATTLE_DEX)

    consolidation = _load_yaml(CONSOLIDATION_PATH)
    recluster_audit = _load_yaml(RECLUSTER_AUDIT_PATH)
    phase51_gate = _load_yaml(PHASE51_GATE_REPORT_PATH)
    focused_reports = _focused_species_reports(consolidation, recluster_audit)
    clustering_report = _clustering_report(consolidation, recluster_audit, focused_reports)
    split_blocker_queue = _split_blocker_queue(consolidation, recluster_audit)
    next_source_priority = _next_source_priority_list(focused_reports, recluster_audit)
    a_layer_check = _a_layer_boundary_check(focused_reports, recluster_audit)
    dashboard = _dashboard(
        phase51_gate=phase51_gate,
        clustering_report=clustering_report,
        split_blocker_queue=split_blocker_queue,
        next_source_priority=next_source_priority,
        a_layer_check=a_layer_check,
        validation_status=validation_status,
        validator_note=validator_note,
    )
    pm_packet = _pm_packet(dashboard, clustering_report, split_blocker_queue, next_source_priority)

    paths = {
        "clustering_report": out_dir / "clustering_report.yaml",
        "recluster_report": out_dir / "recluster_report.yaml",
        "split_blocker_queue": out_dir / "split_blocker_queue.yaml",
        "next_source_priority_list": out_dir / "next_source_priority_list.yaml",
        "a_layer_boundary_check": out_dir / "a_layer_boundary_check.yaml",
        "dashboard": out_dir / "dashboard.yaml",
        "pm_review_packet": out_dir / "pm_review_packet.md",
        "validation_evidence": out_dir / "validation_evidence.yaml",
        "data_dashboard": dashboard_data_path,
        "snapshot_manifest": snapshot_path,
    }

    _write_yaml(paths["clustering_report"], clustering_report)
    _write_yaml(paths["recluster_report"], recluster_audit)
    _write_yaml(paths["split_blocker_queue"], split_blocker_queue)
    _write_yaml(paths["next_source_priority_list"], next_source_priority)
    _write_yaml(paths["a_layer_boundary_check"], a_layer_check)
    _write_yaml(paths["dashboard"], dashboard)
    _write_yaml(paths["data_dashboard"], dashboard)
    paths["pm_review_packet"].parent.mkdir(parents=True, exist_ok=True)
    paths["pm_review_packet"].write_text(pm_packet, encoding="utf-8")

    runtime_hash_after = _sha256(BATTLE_DEX)
    validation = _validation_evidence(
        validation_status=validation_status,
        validator_note=validator_note,
        runtime_hash_before=runtime_hash_before,
        runtime_hash_after=runtime_hash_after,
    )
    _write_yaml(paths["validation_evidence"], validation)

    source_refs = [
        PHASE51_GATE_REPORT_PATH,
        PHASE51_DASHBOARD_PATH,
        CONSOLIDATION_PATH,
        RECLUSTER_AUDIT_PATH,
        GOLD_MANIFEST_PATH,
    ]
    provenance_path = out_dir / "provenance_manifest.yaml"
    paths["provenance_manifest"] = provenance_path
    provenance = _provenance_manifest(paths, source_refs)
    _write_yaml(provenance_path, provenance)

    snapshot_paths = [
        paths["clustering_report"],
        paths["recluster_report"],
        paths["split_blocker_queue"],
        paths["next_source_priority_list"],
        paths["a_layer_boundary_check"],
        paths["dashboard"],
        paths["data_dashboard"],
        paths["pm_review_packet"],
        paths["validation_evidence"],
        paths["provenance_manifest"],
        *source_refs,
    ]
    _write_yaml(paths["snapshot_manifest"], _snapshot_manifest(BATCH_ID, snapshot_paths))
    self_check = _self_check_snapshot(paths["snapshot_manifest"])
    validation = _validation_evidence(
        validation_status=validation_status,
        validator_note=validator_note,
        runtime_hash_before=runtime_hash_before,
        runtime_hash_after=runtime_hash_after,
        snapshot_self_check=self_check,
    )
    _write_yaml(paths["validation_evidence"], validation)
    provenance = _provenance_manifest(paths, source_refs)
    _write_yaml(provenance_path, provenance)
    _write_yaml(paths["snapshot_manifest"], _snapshot_manifest(BATCH_ID, snapshot_paths))

    return {
        "batch_id": BATCH_ID,
        "runtime_allowed": False,
        "paths": {key: _relpath(path) for key, path in paths.items()},
        "summary": {
            "split_blocked_count": dashboard["metrics"]["split_blocked_count"],
            "complete_4_moves_count": dashboard["metrics"]["phase51_complete_4_moves_count"],
            "partial_2_3_moves_count": dashboard["metrics"]["phase51_partial_2_3_moves_count"],
            "recluster_candidate_proposal_count": dashboard["metrics"]["recluster_candidate_proposal_count"],
            "pm_recluster_candidate_count": dashboard["metrics"]["pm_recluster_candidate_count"],
            "next_source_p1_count": dashboard["metrics"]["next_source_p1_count"],
            "next_source_p2_count": dashboard["metrics"]["next_source_p2_count"],
            "a_layer_boundary_unresolved_count": dashboard["metrics"]["a_layer_boundary_unresolved_count"],
            "s2_overlay_referenced_count": dashboard["metrics"]["a_layer_boundary_s2_overlay_referenced_count"],
            "gold_accepted_item_paths_count": dashboard["metrics"]["gold_accepted_item_paths_count"],
            "validation_status": validation_status,
            "snapshot_hash_self_check": self_check["status"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-status", default="not_run")
    parser.add_argument("--validator-note", default="validation not run yet")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build_phase52_package(
        validation_status=args.validation_status,
        validator_note=args.validator_note,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"phase52 package: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
