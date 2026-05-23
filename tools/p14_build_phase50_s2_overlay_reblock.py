#!/usr/bin/env python3
"""Build Phase50 S2 overlay reblock and post-S2 expansion package.

This creates a derived candidate-only package from Phase48/49 plus a small
post-S2 expansion lane. It never edits Phase48/49 originals and never writes
runtime graph or Battle Dex data.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from tools.p14_build_controlled_drill_artifacts import (
    DEFAULT_BATTLE_DEX,
    DEFAULT_KG_ROOT,
    DEFAULT_KNOWLEDGE_OPS_ROOT,
    NoAliasDumper,
    _field_evidence_index,
    _load_dex,
    _load_s2_affected,
    _load_yaml,
    _mechanism_dependency_items,
    _relation_items,
    _repo_rel,
    _set_items,
    _source_artifacts,
    _source_records,
    _write_yaml,
)
from tools.p14_versioned_a_layer_resolver import build_resolver_contract, resolve_entities


REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = "phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23"
PHASE48_BATCH_ID = "phase48_controlled_pipeline_drill_2026-05-23"
PHASE49_BATCH_ID = "phase49_post_s2_targeted_ingest_2026-05-23"
PHASE48_DIR = DEFAULT_KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / PHASE48_BATCH_ID
PHASE49_DIR = DEFAULT_KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / PHASE49_BATCH_ID
S1_SNAPSHOT_DB = REPO_ROOT / "data" / "runtime" / "snapshots" / "s1_2026-05-20" / "battle_dex.sqlite"
S2_OVERLAY_MANIFEST = DEFAULT_KG_ROOT / "a_layer_overlays" / "s2_2026-05-21" / "manifest.yaml"
S2_OVERLAY = DEFAULT_KG_ROOT / "a_layer_overlays" / "s2_2026-05-21" / "overlay.yaml"
S2_RECONCILIATION = DEFAULT_KG_ROOT / "patch_deltas" / "s2_2026-05-21_a_layer_reconciliation_v0.yaml"
OLD_S2_BLOCKER = "s2_a_layer_reconciliation_required_before_runtime_or_gold"
NEW_S2_GATE = "s2_a_layer_overlay_referenced_pm_review_gold_gate_required"
PHASE48_EPOCH_BLOCKER = "pre_s2_historical_evidence_requires_post_s2_confirmation_or_pm_review"
DEFAULT_EXPANSION_SOURCE_IDS = ["kgsrc_bili_bv1q9lb6xeyv", "kgsrc_bili_bv1nwgb6uezi"]
PHASE48_SOURCE_IDS = [
    "kgsrc_bili_bv16v9hbpenj",
    "kgsrc_bili_bv1dkoxbyezc",
    "kgsrc_bili_bv1kd5s6lecy",
    "kgsrc_bili_bv1r796brefs",
]
PHASE49_SOURCE_IDS = [
    "kgsrc_bili_bv1upgt64ees",
    "kgsrc_bili_bv1cygb67eyu",
    "kgsrc_bili_bv15ygq6beu8",
    "kgsrc_bili_bv1fely6pe7g",
    "kgsrc_bili_bv1upgi6jenf",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {"path": _repo_rel(path), "sha256": _sha256(path)}


def _run_artifacts(run_dir: Path) -> list[dict[str, Any]]:
    names = [
        "candidate_kg_items.yaml",
        "dashboard.yaml",
        "field_evidence_index.yaml",
        "pm_review_packet.md",
        "provenance_manifest.yaml",
        "source_bundle_manifest.yaml",
    ]
    return [_artifact(run_dir / name) for name in names if (run_dir / name).exists()]


def _candidate_items(run_dir: Path) -> list[dict[str, Any]]:
    return list((_load_yaml(run_dir / "candidate_kg_items.yaml").get("candidate_items") or []))


def _overlay_entity_names() -> set[str]:
    payload = _load_yaml(S2_OVERLAY)
    names: set[str] = set()
    for entries in (payload.get("entries") or {}).values():
        for entry in entries or []:
            target = entry.get("target") or {}
            if target.get("display_name"):
                names.add(str(target["display_name"]))
            if target.get("move_name"):
                names.add(str(target["move_name"]))
            species = target.get("species") or {}
            move = target.get("move") or {}
            if species.get("display_name"):
                names.add(str(species["display_name"]))
            if move.get("move_name"):
                names.add(str(move["move_name"]))
    return names


def _rewrite_item_id(original_id: str, source_batch: str) -> str:
    marker = f"candkg/{source_batch}/"
    suffix = original_id[len(marker) :] if original_id.startswith(marker) else original_id.replace("/", "_")
    return f"candkg/{BATCH_ID}/reblocked/{source_batch}/{suffix}"


def _a_layer_refs(resolver_contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "resolver_id": resolver_contract["resolver_id"],
        "base_snapshot": resolver_contract["base_snapshot"],
        "overlay": resolver_contract["overlay"],
        "candidate_only": True,
        "runtime_allowed": False,
    }


def _reblock_items(
    items: list[dict[str, Any]],
    *,
    source_batch: str,
    resolver_contract: dict[str, Any],
    phase48_historical: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    derived: list[dict[str, Any]] = []
    migrations: list[dict[str, Any]] = []
    refs = _a_layer_refs(resolver_contract)
    for item in items:
        new_item = copy.deepcopy(item)
        original_id = str(item.get("item_id") or "")
        blockers = list(new_item.get("blocked_by") or [])
        changed = False
        if OLD_S2_BLOCKER in blockers:
            blockers = [NEW_S2_GATE if blocker == OLD_S2_BLOCKER else blocker for blocker in blockers]
            changed = True
            new_item["s2_overlay_reference"] = {
                **refs,
                "status": "s2_reference_surface_exists_candidate_only_pm_gold_runtime_gate_still_required",
            }
        if phase48_historical and PHASE48_EPOCH_BLOCKER not in blockers:
            blockers.append(PHASE48_EPOCH_BLOCKER)
            new_item["epoch_boundary_note"] = (
                "Phase48 is pre-S2 historical evidence. It requires post-S2 confirmation or PM review before "
                "reviewed, Gold, or runtime use."
            )
        new_item["item_id"] = _rewrite_item_id(original_id, source_batch)
        new_item["source_item_id"] = original_id
        new_item["source_run_id"] = source_batch
        new_item["review_status"] = "candidate_unreviewed"
        new_item["runtime_allowed"] = False
        new_item["blocked_by"] = sorted(set(blockers))
        new_item["phase50_lineage"] = [
            "historical_candidate_copy",
            "phase50_s2_overlay_reblock",
            "candidate_only_no_runtime_promotion",
        ]
        derived.append(new_item)
        if changed:
            migrations.append(
                {
                    "source_item_id": original_id,
                    "phase50_item_id": new_item["item_id"],
                    "source_run_id": source_batch,
                    "old_blocker": OLD_S2_BLOCKER,
                    "new_blocker": NEW_S2_GATE,
                    "s2_affected_entities": list(new_item.get("s2_affected_entities") or []),
                    "runtime_allowed": False,
                }
            )
    return derived, migrations


def _expansion_items(source_ids: list[str], resolver_contract: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dex = _load_dex(S1_SNAPSHOT_DB if S1_SNAPSHOT_DB.exists() else DEFAULT_BATTLE_DEX)
    s2_affected = _load_s2_affected(S2_RECONCILIATION)
    items = [
        *_set_items(BATCH_ID, source_ids, dex, s2_affected),
        *_relation_items(BATCH_ID, source_ids, s2_affected, dex),
        *_mechanism_dependency_items(BATCH_ID, source_ids, s2_affected, dex),
    ]
    refs = _a_layer_refs(resolver_contract)
    migrations: list[dict[str, Any]] = []
    for item in items:
        blockers = list(item.get("blocked_by") or [])
        if OLD_S2_BLOCKER in blockers:
            blockers = [NEW_S2_GATE if blocker == OLD_S2_BLOCKER else blocker for blocker in blockers]
            item["blocked_by"] = sorted(set(blockers))
            item["s2_overlay_reference"] = {
                **refs,
                "status": "s2_reference_surface_exists_candidate_only_pm_gold_runtime_gate_still_required",
            }
            migrations.append(
                {
                    "source_item_id": item["item_id"],
                    "phase50_item_id": item["item_id"],
                    "source_run_id": "phase50_expansion",
                    "old_blocker": OLD_S2_BLOCKER,
                    "new_blocker": NEW_S2_GATE,
                    "s2_affected_entities": list(item.get("s2_affected_entities") or []),
                    "runtime_allowed": False,
                }
            )
        item["review_status"] = "candidate_unreviewed"
        item["runtime_allowed"] = False
        item["phase50_lineage"] = [
            "post_s2_expansion_candidate",
            "phase50_s2_overlay_gate",
            "candidate_only_no_runtime_promotion",
        ]
    return items, migrations


def _assert_runtime_false(items: list[dict[str, Any]]) -> None:
    offenders = [item.get("item_id") for item in items if item.get("runtime_allowed") is not False]
    if offenders:
        raise RuntimeError(f"candidate runtime_allowed violation: {offenders[:5]}")


def _validate_s2_coverage(items: list[dict[str, Any]], overlay_names: set[str]) -> list[str]:
    exceeded: list[str] = []
    for item in items:
        for entity in item.get("s2_affected_entities") or []:
            if entity not in overlay_names:
                exceeded.append(str(entity))
    return sorted(set(exceeded))


def _source_bundle(
    *,
    batch_id: str,
    expansion_source_ids: list[str],
    queue_audits: list[Path],
    ingest_audit: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "p14.phase50_source_bundle_manifest.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "historical_inputs": [
            {"run_id": PHASE48_BATCH_ID, "source_ids": PHASE48_SOURCE_IDS, "artifacts": _run_artifacts(PHASE48_DIR)},
            {"run_id": PHASE49_BATCH_ID, "source_ids": PHASE49_SOURCE_IDS, "artifacts": _run_artifacts(PHASE49_DIR)},
        ],
        "expansion": {
            "source_ids": expansion_source_ids,
            "sources": _source_records(expansion_source_ids),
            "queue_audits": [_artifact(path) for path in queue_audits if path.exists()],
            "ingest_audit": _artifact(ingest_audit) if ingest_audit.exists() else None,
        },
    }


def _provenance_manifest(
    *,
    batch_id: str,
    expansion_source_ids: list[str],
    resolver_contract: dict[str, Any],
    queue_audits: list[Path],
    ingest_audit: Path,
    clustering_paths: list[Path],
) -> dict[str, Any]:
    return {
        "schema_version": "p14.phase50_provenance_manifest.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "policy": {
            "phase48_originals_edited": False,
            "phase49_originals_edited": False,
            "runtime_db_write": False,
            "reviewed_graph_materialization": False,
            "gold_auto_accept": False,
        },
        "historical_run_artifacts": {
            PHASE48_BATCH_ID: _run_artifacts(PHASE48_DIR),
            PHASE49_BATCH_ID: _run_artifacts(PHASE49_DIR),
        },
        "a_layer_resolver": _a_layer_refs(resolver_contract),
        "source_discovery_and_ingest": {
            "selected_candidates": _artifact(
                DEFAULT_KNOWLEDGE_OPS_ROOT
                / "source_candidates"
                / "phase50_s2_overlay_expansion_selected_2026-05-23_candidates.yaml"
            ),
            "queue_audits": [_artifact(path) for path in queue_audits if path.exists()],
            "ingest_audit": _artifact(ingest_audit) if ingest_audit.exists() else None,
            "expansion_source_artifacts": {
                source_id: {key: value for key, value in _source_artifacts(source_id).items() if value}
                for source_id in expansion_source_ids
            },
        },
        "clustering_refs": [_artifact(path) for path in clustering_paths if path.exists()],
    }


def _blocker_migration_report(
    *,
    phase49_items: list[dict[str, Any]],
    phase49_migrations: list[dict[str, Any]],
    expansion_migrations: list[dict[str, Any]],
    phase48_item_count: int,
) -> dict[str, Any]:
    old_count = sum(1 for item in phase49_items if OLD_S2_BLOCKER in (item.get("blocked_by") or []))
    if old_count != 5:
        raise RuntimeError(f"expected Phase49 S2 blocker count 5, got {old_count}")
    if len(phase49_migrations) != 5:
        raise RuntimeError(f"expected Phase49 migrated S2 gate count 5, got {len(phase49_migrations)}")
    return {
        "schema_version": "p14.phase50_blocker_migration_report.v0",
        "batch_id": BATCH_ID,
        "generated_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "phase48": {
            "item_count": phase48_item_count,
            "historical_blocker_added": PHASE48_EPOCH_BLOCKER,
            "policy": "pre-S2 evidence remains historical and requires post-S2 confirmation or PM review before reviewed/Gold/runtime use",
        },
        "phase49": {
            "old_s2_reference_surface_blocker": OLD_S2_BLOCKER,
            "new_s2_overlay_referenced_gate": NEW_S2_GATE,
            "old_s2_reference_surface_blocker_count": old_count,
            "new_s2_overlay_referenced_gate_count": len(phase49_migrations),
            "item_level_migrations": phase49_migrations,
        },
        "expansion": {
            "new_s2_overlay_referenced_gate_count": len(expansion_migrations),
            "item_level_migrations": expansion_migrations,
        },
        "review_candidate_count": 0,
        "runtime_allowed": False,
    }


def _gold_eval_labeling_packet(candidate_items: list[dict[str, Any]]) -> dict[str, Any]:
    s2_items = [item for item in candidate_items if item.get("s2_overlay_reference")]
    phase48_items = [item for item in candidate_items if item.get("source_run_id") == PHASE48_BATCH_ID]
    return {
        "schema_version": "p14.gold_eval_labeling_packet.v0",
        "batch_id": BATCH_ID,
        "runtime_allowed": False,
        "gold_acceptance_status": "not_accepted_pm_review_required",
        "candidate_gold_items": [
            {
                "label_id": "phase50_gold_negative_s2_overlay_not_runtime_truth",
                "gold_type": "gold_negative_case",
                "recommended_action": "defer_not_gold_until_pm_accepts",
                "why": "S2 overlay can be cited by candidate items, but cannot promote runtime/Gold/reviewed graph on its own.",
                "sample_item_ids": [item["item_id"] for item in s2_items[:3]],
                "runtime_allowed": False,
            },
            {
                "label_id": "phase50_gold_stateful_epoch_boundary_pre_s2",
                "gold_type": "gold_negative_case",
                "recommended_action": "defer_not_gold_until_pm_accepts",
                "why": "Phase48 pre-S2 evidence must not be silently treated as current post-S2 truth.",
                "sample_item_ids": [item["item_id"] for item in phase48_items[:3]],
                "runtime_allowed": False,
            },
        ],
        "pm_questions": [
            "Should the S2 overlay gate itself become a Gold negative case after PM review?",
            "Should pre-S2 historical evidence handling become a Gold negative case after PM review?",
        ],
    }


def _clustering_report(clustering_path: Path) -> dict[str, Any]:
    payload = _load_yaml(clustering_path) if clustering_path.exists() else {}
    records = payload.get("species_records") or []
    split_records = [item for item in records if item.get("state") == "split_blocked"]
    same_family_records = [
        item
        for item in records
        if (item.get("set_family_summary") or {}).get("decision") == "same_family_or_insufficient_split_evidence"
    ]
    alter_variant_count = sum(
        1
        for item in records
        for family in item.get("set_family_candidates") or []
        for variant in family.get("alter_variants") or []
        if variant.get("variant_type") == "alter_variant"
    )
    return {
        "schema_version": "p14.phase50_clustering_report.v0",
        "batch_id": BATCH_ID,
        "generated_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "source_consolidation_ref": _artifact(clustering_path) if clustering_path.exists() else None,
        "summary": payload.get("summary") or {},
        "decision_counts": {
            "same_family_or_insufficient_split_evidence": len(same_family_records),
            "alter_variant_observations": alter_variant_count,
            "split_blocked": len(split_records),
            "separate_set": 0,
            "family_review_candidate": int((payload.get("summary") or {}).get("family_review_candidate_count") or 0),
        },
        "policy": {
            "default_set_difference_handling": "same-family with alter variants until role/build-axis evidence supports a separate set",
            "separate_set_requires": "multiple aligned tactical-intent signals, not one or two move differences",
            "runtime_allowed": False,
        },
        "split_blocked_records": [
            {
                "species_name": item.get("species_name"),
                "stable_moves": item.get("stable_moves") or [],
                "split_hypotheses": item.get("split_hypotheses") or [],
                "suggested_next_action": item.get("suggested_next_action"),
                "runtime_allowed": False,
            }
            for item in split_records
        ],
        "pm_review_note": (
            "This report is an explicit Phase50 clustering artifact. It records the same-family / "
            "alter-variant / split-blocked boundary for this review gate, but does not promote set cards."
        ),
    }


def _dashboard(
    *,
    candidate_items: list[dict[str, Any]],
    source_bundle: dict[str, Any],
    blocker_report: dict[str, Any],
    clustering_report: dict[str, Any],
    validation_status: str,
    validator_note: str,
) -> dict[str, Any]:
    blockers = Counter(blocker for item in candidate_items for blocker in item.get("blocked_by") or [])
    types = Counter(str(item.get("candidate_type")) for item in candidate_items)
    source_ids = list(
        dict.fromkeys(
            [
                *source_bundle["historical_inputs"][0]["source_ids"],
                *source_bundle["historical_inputs"][1]["source_ids"],
                *source_bundle["expansion"]["source_ids"],
            ]
        )
    )
    source_records = _source_records(source_ids)
    epochs = Counter(str(item.get("game_epoch")) for item in source_records)
    return {
        "schema_version": "p14.dataset_pipeline_dashboard.v0",
        "batch_id": BATCH_ID,
        "generated_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "validation_status": validation_status,
        "validator_note": validator_note,
        "source_count": len(source_records),
        "source_ids": [item["source_id"] for item in source_records],
        "source_epoch_counts": dict(sorted(epochs.items())),
        "source_segment_count": sum(int((item.get("quality") or {}).get("segment_count") or 0) for item in source_records),
        "repair_required_segment_count": sum(int((item.get("quality") or {}).get("repair_required_segments") or 0) for item in source_records),
        "candidate_item_count": len(candidate_items),
        "candidate_item_counts_by_type": dict(sorted(types.items())),
        "blocked_item_count": sum(1 for item in candidate_items if item.get("blocked_by")),
        "review_candidate_count": 0,
        "blocker_counts": dict(sorted(blockers.items())),
        "phase50_reblock_summary": {
            "phase48_historical_item_count": blocker_report["phase48"]["item_count"],
            "phase49_old_s2_reference_surface_blocker_count": blocker_report["phase49"]["old_s2_reference_surface_blocker_count"],
            "phase49_new_s2_overlay_referenced_gate_count": blocker_report["phase49"]["new_s2_overlay_referenced_gate_count"],
            "expansion_s2_overlay_referenced_gate_count": blocker_report["expansion"]["new_s2_overlay_referenced_gate_count"],
            "runtime_allowed": False,
        },
        "clustering_summary": {
            "explicit_clustering_report": "artifacts/knowledge_ops/dataset_pipeline_runs/phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23/clustering_report.yaml",
            "decision_counts": clustering_report.get("decision_counts") or {},
            "runtime_allowed": False,
        },
        "expansion_summary": {
            "source_ids": source_bundle["expansion"]["source_ids"],
            "source_count": len(source_bundle["expansion"]["source_ids"]),
            "source_policy": "P1/P2 current-season PvP source expansion; failed source-boundary candidates are recorded in queue audit, not forced into evidence.",
        },
        "pm_attention_required": True,
        "stop_reasons": [],
    }


def _pm_packet(
    *,
    candidate_items: list[dict[str, Any]],
    dashboard: dict[str, Any],
    blocker_report: dict[str, Any],
    expansion_source_ids: list[str],
) -> str:
    source_records = _source_records(expansion_source_ids)
    migrated = blocker_report["phase49"]["item_level_migrations"]
    expansion_items = [item for item in candidate_items if "post_s2_expansion_candidate" in (item.get("phase50_lineage") or [])]
    s2_citing = [item for item in candidate_items if item.get("s2_overlay_reference")]
    source_lines = [
        f"- `{row['source_id']}`：{row['title']}；{row['source_type']}；{row['game_epoch']}；method={row['transcript_method']}；segments={row['quality']['segment_count']}；repair_required={row['quality']['repair_required_segments']}。"
        for row in source_records
    ]
    migrated_lines = [
        f"- `{item['source_item_id']}` -> `{item['phase50_item_id']}`；affected={', '.join(item.get('s2_affected_entities') or []) or 'unknown'}。"
        for item in migrated
    ]
    return "\n".join(
        [
            f"# P14 Phase50 PM Review Packet: {BATCH_ID}",
            "",
            "## 结论",
            "- Phase50 是派生包，不改 Phase48/49 原件。",
            f"- Phase49 的 `{OLD_S2_BLOCKER}` 已在派生候选里迁移为 `{NEW_S2_GATE}`。",
            "- 这只表示 S2 reference surface 已存在；不表示 reviewed、Gold 或 runtime 可用。",
            f"- 本包 candidate items={len(candidate_items)}；review_candidate_count=0；所有 `runtime_allowed=false`。",
            "",
            "## 1. What Changed / What Did Not Change",
            "- 变了：Phase49 S2 blocker 语义从“缺少 S2 reference surface”变为“已引用 S2 overlay，但 PM/Gold/runtime gate 仍然需要”。",
            "- 变了：Phase48 在派生包里显式标记为 pre-S2 historical evidence。",
            "- 变了：新增一个小的 S2 当前季扩源包，并生成 candidate-only items。",
            "- 没变：Phase48/49 原文件、runtime DB、reviewed graph、Gold manifest 都没有被写入或放行。",
            "",
            "## 2. Blocker Migration",
            f"- old: `{OLD_S2_BLOCKER}`",
            f"- new: `{NEW_S2_GATE}`",
            f"- Phase49 old count={blocker_report['phase49']['old_s2_reference_surface_blocker_count']}；new count={blocker_report['phase49']['new_s2_overlay_referenced_gate_count']}。",
            "",
            "## 3. Affected Phase49 Items",
            *migrated_lines,
            "",
            "## 4. Reviewed / Gold / Runtime?",
            "- No. 没有任何 item 进入 reviewed、Gold 或 runtime。",
            "- Gold/Eval 只有 labeling packet，状态是 `not_accepted_pm_review_required`。",
            "",
            "## 5. Added Sources",
            *source_lines,
            "",
            "## 6. New Expansion Candidate Items",
            f"- 新扩源 candidate items={len(expansion_items)}；类型分布={json.dumps(Counter(item.get('candidate_type') for item in expansion_items), ensure_ascii=False, sort_keys=True)}。",
            "- 这些 item 只用于证明 autorun 链路能继续产出 hashable candidate evidence，不做 promotion。",
            "",
            "## 7. S2 Overlay Citations",
            f"- 本包引用 S2 overlay 的 candidate items={len(s2_citing)}。",
            "- 它们只引用 `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/manifest.yaml` 作为 candidate-only reference surface。",
            "",
            "## 8. Residual Blockers",
            f"- blocker counts: {json.dumps(dashboard['blocker_counts'], ensure_ascii=False, sort_keys=True)}。",
            "- reviewed graph 仍缺 PM/reviewer review、跨源 consolidation、完整 move skeleton、机制规则 review。",
            "- runtime DB promotion 仍缺版本化 runtime DB build、promotion audit、回归测试和 PM approval。",
            "",
            "## 9. PM Should Review First",
            "1. 接受 Phase49 blocker wording migration 是否准确。",
            "2. 接受 Phase48 只作为 pre-S2 historical evidence。",
            "3. 查看新增扩源是否值得继续沿 S2 overlay entity/move 方向补源。",
            "4. 决定 Gold/Eval labeling packet 中两个 negative case 是否进入后续人工 Gold review。",
            "",
        ]
    )


def _validation_evidence(
    *,
    validation_status: str,
    validator_note: str,
    runtime_hash_before: str,
    runtime_hash_after: str,
    snapshot_self_check: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "p14.phase50_validation_evidence.v0",
        "batch_id": BATCH_ID,
        "generated_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "validation_status": validation_status,
        "validator_note": validator_note,
        "runtime_db_hash_before": runtime_hash_before,
        "runtime_db_hash_after": runtime_hash_after,
        "runtime_db_hash_unchanged": runtime_hash_before == runtime_hash_after,
        "snapshot_hash_self_check": snapshot_self_check or {"status": "pending_until_snapshot_manifest_written"},
        "forbidden_outputs_checked": {
            "runtime_db_modified": False,
            "reviewed_graph_materialized": False,
            "gold_auto_accepted": False,
        },
    }


def _snapshot_manifest(batch_id: str, paths: list[Path]) -> dict[str, Any]:
    artifacts = [_artifact(path) for path in paths if path.exists() and path.is_file()]
    return {
        "schema_version": "p14.snapshot_manifest.v0",
        "snapshot_id": batch_id,
        "created_at": datetime.now().astimezone().isoformat(),
        "runtime_allowed": False,
        "promotion_status": "candidate_only_phase50_reblock_snapshot",
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


def build_phase50_package(
    *,
    batch_id: str = BATCH_ID,
    expansion_source_ids: list[str] | None = None,
    validation_status: str = "not_run",
    validator_note: str = "validation not run yet",
) -> dict[str, Any]:
    if batch_id != BATCH_ID:
        raise ValueError("Phase50 tool currently uses the fixed spec batch id")
    expansion_source_ids = expansion_source_ids or DEFAULT_EXPANSION_SOURCE_IDS
    out_dir = DEFAULT_KNOWLEDGE_OPS_ROOT / "dataset_pipeline_runs" / batch_id
    dashboard_data_path = DEFAULT_KG_ROOT / "eval" / f"quality_dashboard_{batch_id}.yaml"
    snapshot_dir = DEFAULT_KG_ROOT / "snapshots" / "roco_kg_dataset_v0.1-dev" / batch_id
    snapshot_path = snapshot_dir / "manifest.yaml"
    runtime_hash_before = _sha256(DEFAULT_BATTLE_DEX)

    resolver_contract = build_resolver_contract()
    phase48_items = _candidate_items(PHASE48_DIR)
    phase49_items = _candidate_items(PHASE49_DIR)
    phase49_old_count = sum(1 for item in phase49_items if OLD_S2_BLOCKER in (item.get("blocked_by") or []))
    if phase49_old_count != 5:
        raise RuntimeError(f"expected Phase49 S2 blocker count 5, got {phase49_old_count}")

    phase48_derived, _ = _reblock_items(
        phase48_items,
        source_batch=PHASE48_BATCH_ID,
        resolver_contract=resolver_contract,
        phase48_historical=True,
    )
    phase49_derived, phase49_migrations = _reblock_items(
        phase49_items,
        source_batch=PHASE49_BATCH_ID,
        resolver_contract=resolver_contract,
    )
    expansion_items, expansion_migrations = _expansion_items(expansion_source_ids, resolver_contract)
    candidate_items = [*phase48_derived, *phase49_derived, *expansion_items]
    _assert_runtime_false(candidate_items)

    exceeded = _validate_s2_coverage(candidate_items, _overlay_entity_names())
    if exceeded:
        raise RuntimeError(f"S2 affected entities exceed overlay: {', '.join(exceeded)}")

    blocker_report = _blocker_migration_report(
        phase49_items=phase49_items,
        phase49_migrations=phase49_migrations,
        expansion_migrations=expansion_migrations,
        phase48_item_count=len(phase48_derived),
    )
    queue_audits = [
        DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / "phase50_s2_overlay_expansion_queue_2026-05-23.yaml",
        DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / "phase50_s2_overlay_expansion_queue_r2_2026-05-23.yaml",
    ]
    ingest_audit = DEFAULT_KNOWLEDGE_OPS_ROOT / "audits" / "phase50_s2_overlay_expansion_ingest_2026-05-23.yaml"
    clustering_paths = [
        DEFAULT_KNOWLEDGE_OPS_ROOT
        / "set_inventory_consolidation"
        / "phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23_clustering.yaml",
        DEFAULT_KNOWLEDGE_OPS_ROOT
        / "review_packets"
        / "phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23_clustering_pm_brief.md",
        DEFAULT_KNOWLEDGE_OPS_ROOT
        / "review_packets"
        / "phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23_clustering_family_review.md",
    ]
    source_bundle = _source_bundle(
        batch_id=batch_id,
        expansion_source_ids=expansion_source_ids,
        queue_audits=queue_audits,
        ingest_audit=ingest_audit,
    )
    provenance = _provenance_manifest(
        batch_id=batch_id,
        expansion_source_ids=expansion_source_ids,
        resolver_contract=resolver_contract,
        queue_audits=queue_audits,
        ingest_audit=ingest_audit,
        clustering_paths=clustering_paths,
    )
    field_index = _field_evidence_index(candidate_items)
    gold_packet = _gold_eval_labeling_packet(candidate_items)
    clustering_report = _clustering_report(clustering_paths[0])
    dashboard = _dashboard(
        candidate_items=candidate_items,
        source_bundle=source_bundle,
        blocker_report=blocker_report,
        clustering_report=clustering_report,
        validation_status=validation_status,
        validator_note=validator_note,
    )
    pm_packet = _pm_packet(
        candidate_items=candidate_items,
        dashboard=dashboard,
        blocker_report=blocker_report,
        expansion_source_ids=expansion_source_ids,
    )
    resolved_entities = sorted({entity for item in candidate_items for entity in item.get("s2_affected_entities") or []})
    resolver_output = resolve_entities(resolved_entities) if resolved_entities else resolver_contract

    candidate_payload = {
        "schema_version": "p14.phase50_candidate_kg_items.v0",
        "batch_id": batch_id,
        "runtime_allowed": False,
        "review_status": "candidate_unreviewed",
        "candidate_items": candidate_items,
    }

    paths = {
        "source_bundle_manifest": out_dir / "source_bundle_manifest.yaml",
        "provenance_manifest": out_dir / "provenance_manifest.yaml",
        "candidate_items": out_dir / "candidate_kg_items.yaml",
        "field_evidence_index": out_dir / "field_evidence_index.yaml",
        "dashboard": out_dir / "dashboard.yaml",
        "pm_review_packet": out_dir / "pm_review_packet.md",
        "blocker_migration_report": out_dir / "blocker_migration_report.yaml",
        "clustering_report": out_dir / "clustering_report.yaml",
        "gold_eval_labeling_packet": out_dir / "gold_eval_labeling_packet.yaml",
        "a_layer_resolver_contract": out_dir / "a_layer_resolver_contract.yaml",
        "validation_evidence": out_dir / "validation_evidence.yaml",
        "data_dashboard": dashboard_data_path,
        "snapshot_manifest": snapshot_path,
    }
    _write_yaml(paths["source_bundle_manifest"], source_bundle)
    _write_yaml(paths["provenance_manifest"], provenance)
    _write_yaml(paths["candidate_items"], candidate_payload)
    _write_yaml(paths["field_evidence_index"], field_index)
    _write_yaml(paths["dashboard"], dashboard)
    _write_yaml(paths["blocker_migration_report"], blocker_report)
    _write_yaml(paths["clustering_report"], clustering_report)
    _write_yaml(paths["gold_eval_labeling_packet"], gold_packet)
    _write_yaml(paths["a_layer_resolver_contract"], resolver_output)
    _write_yaml(paths["data_dashboard"], dashboard)
    paths["pm_review_packet"].parent.mkdir(parents=True, exist_ok=True)
    paths["pm_review_packet"].write_text(pm_packet, encoding="utf-8")

    runtime_hash_after = _sha256(DEFAULT_BATTLE_DEX)
    validation = _validation_evidence(
        validation_status=validation_status,
        validator_note=validator_note,
        runtime_hash_before=runtime_hash_before,
        runtime_hash_after=runtime_hash_after,
    )
    _write_yaml(paths["validation_evidence"], validation)

    snapshot = _snapshot_manifest(
        batch_id,
        [
            paths["source_bundle_manifest"],
            paths["provenance_manifest"],
            paths["candidate_items"],
            paths["field_evidence_index"],
            paths["dashboard"],
            paths["pm_review_packet"],
            paths["blocker_migration_report"],
            paths["clustering_report"],
            paths["gold_eval_labeling_packet"],
            paths["a_layer_resolver_contract"],
            paths["validation_evidence"],
            paths["data_dashboard"],
            *clustering_paths,
            S2_OVERLAY_MANIFEST,
            S2_OVERLAY,
        ],
    )
    _write_yaml(paths["snapshot_manifest"], snapshot)
    self_check = _self_check_snapshot(paths["snapshot_manifest"])
    validation = _validation_evidence(
        validation_status=validation_status,
        validator_note=validator_note,
        runtime_hash_before=runtime_hash_before,
        runtime_hash_after=runtime_hash_after,
        snapshot_self_check=self_check,
    )
    _write_yaml(paths["validation_evidence"], validation)
    snapshot = _snapshot_manifest(
        batch_id,
        [
            paths["source_bundle_manifest"],
            paths["provenance_manifest"],
            paths["candidate_items"],
            paths["field_evidence_index"],
            paths["dashboard"],
            paths["pm_review_packet"],
            paths["blocker_migration_report"],
            paths["clustering_report"],
            paths["gold_eval_labeling_packet"],
            paths["a_layer_resolver_contract"],
            paths["validation_evidence"],
            paths["data_dashboard"],
            *clustering_paths,
            S2_OVERLAY_MANIFEST,
            S2_OVERLAY,
        ],
    )
    _write_yaml(paths["snapshot_manifest"], snapshot)

    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_count": len(dashboard["source_ids"]),
        "candidate_item_count": len(candidate_items),
        "review_candidate_count": dashboard["review_candidate_count"],
        "phase49_old_s2_reference_surface_blocker_count": blocker_report["phase49"]["old_s2_reference_surface_blocker_count"],
        "phase49_new_s2_overlay_referenced_gate_count": blocker_report["phase49"]["new_s2_overlay_referenced_gate_count"],
        "expansion_source_ids": expansion_source_ids,
        "paths": {key: _repo_rel(path) for key, path in paths.items()},
        "summary": {
            "candidate_item_counts_by_type": dashboard["candidate_item_counts_by_type"],
            "blocker_counts": dashboard["blocker_counts"],
            "validation_status": validation_status,
            "snapshot_hash_self_check": self_check["status"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--validation-status", default="not_run")
    parser.add_argument("--validator-note", default="validation not run yet")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build_phase50_package(
        expansion_source_ids=args.source_ids or DEFAULT_EXPANSION_SOURCE_IDS,
        validation_status=args.validation_status,
        validator_note=args.validator_note,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"phase50 package: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
