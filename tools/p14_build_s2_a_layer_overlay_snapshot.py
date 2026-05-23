#!/usr/bin/env python3
"""Build the candidate-only S2 A-layer overlay snapshot package.

This tool freezes the current S1 Battle Dex as a byte-for-byte copy and writes
a candidate-only S2 overlay from the official S2 reconciliation artifacts. It
never writes to the runtime Battle Dex and never promotes overlay data.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DB = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
DEFAULT_S1_DIR = REPO_ROOT / "data" / "runtime" / "snapshots" / "s1_2026-05-20"
DEFAULT_OVERLAY_DIR = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "a_layer_overlays" / "s2_2026-05-21"
DEFAULT_PATCH_DELTA = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "patch_deltas" / "s2_2026-05-21_patch_delta_pack_v0.yaml"
DEFAULT_RECONCILIATION = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "patch_deltas" / "s2_2026-05-21_a_layer_reconciliation_v0.yaml"
DEFAULT_OFFICIAL_SOURCE = (
    REPO_ROOT
    / "data"
    / "knowledge_graph"
    / "v0"
    / "patch_deltas"
    / "s2_2026-05-20_official_balance_sources"
    / "s2_2026-05-20_official_balance_manifest.yaml"
)
DEFAULT_DASHBOARD = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "eval" / "quality_dashboard_s2_a_layer_overlay_snapshot_2026-05-23.yaml"


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_rel(path: Path, *, repo_root: Path = REPO_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _artifact(path: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return {
        "path": _repo_rel(path, repo_root=repo_root),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _timestamp(value: str | None) -> str:
    return value or datetime.now().astimezone().isoformat()


def write_s1_snapshot(
    *,
    runtime_db: Path,
    snapshot_dir: Path,
    created_at: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if not runtime_db.exists():
        raise FileNotFoundError(runtime_db)
    snapshot_db = snapshot_dir / "battle_dex.sqlite"
    source_hash = _sha256(runtime_db)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    if snapshot_db.exists():
        existing_hash = _sha256(snapshot_db)
        if existing_hash != source_hash:
            raise RuntimeError(
                f"existing S1 snapshot hash differs from runtime DB: {existing_hash} != {source_hash}"
            )
    else:
        shutil.copy2(runtime_db, snapshot_db)
    snapshot_hash = _sha256(snapshot_db)
    manifest = {
        "schema_version": "p14.a_layer_base_snapshot.v0",
        "id": "s1_2026-05-20_battle_dex_freeze",
        "created_at": created_at,
        "game_epoch": "s1_2026-05-20",
        "runtime_allowed": False,
        "promotion_status": "immutable_historical_baseline",
        "immutable": True,
        "source": _artifact(runtime_db, repo_root=repo_root),
        "snapshot": _artifact(snapshot_db, repo_root=repo_root),
        "byte_identical_to_source": snapshot_hash == source_hash,
        "may_write_runtime_db": False,
        "note": "Frozen S1 baseline for candidate-only S2 overlay construction; this copy is not a runtime promotion.",
    }
    _write_yaml(snapshot_dir / "manifest.yaml", manifest)
    return manifest


def _species_target(resolution: dict[str, Any]) -> dict[str, Any]:
    species = resolution.get("species") or {}
    return {
        "species_id": species.get("species_id"),
        "display_name": species.get("display_name"),
        "initial_species_name": species.get("initial_species_name"),
        "form_name": species.get("form_name"),
        "regional_form_name": species.get("regional_form_name"),
        "resolution_status": resolution.get("status"),
        "canonical_query": resolution.get("canonical_query"),
        "alias_notes": resolution.get("alias_notes") or [],
    }


def _move_target(resolution: dict[str, Any]) -> dict[str, Any]:
    move = resolution.get("move") or {}
    return {
        "move_id": move.get("move_id"),
        "move_name": move.get("move_name"),
        "move_type": move.get("move_type"),
        "category_raw": move.get("category_raw"),
        "current_power": move.get("power"),
        "current_energy_cost": move.get("energy_cost"),
        "current_effect_text": move.get("effect_text"),
        "resolution_status": resolution.get("status"),
        "canonical_query": resolution.get("canonical_query"),
        "alias_notes": resolution.get("alias_notes") or [],
    }


def _ability_target(resolution: dict[str, Any]) -> dict[str, Any]:
    ability = resolution.get("ability") or {}
    return {
        "ability_id": ability.get("ability_id"),
        "ability_name": ability.get("ability_name"),
        "current_effect_text": ability.get("effect_text"),
        "resolution_status": resolution.get("status"),
        "canonical_query": resolution.get("canonical_query"),
        "alias_notes": resolution.get("alias_notes") or [],
    }


def _signed_int(value: str) -> int:
    return int(value.replace("−", "-"))


def _response_state_energy_reduction(old_text: str | None, new_text: str | None) -> dict[str, Any] | None:
    if not old_text or not new_text:
        return None
    if "应对状态" not in old_text or "应对状态" not in new_text:
        return None
    pattern = r"本技能能耗永久\s*([+-]?\d+|−\d+)"
    old_match = re.search(pattern, old_text)
    new_match = re.search(pattern, new_text)
    if not old_match or not new_match:
        return None
    return {
        "field": "response_state_attached_effect_energy_reduction",
        "old": _signed_int(old_match.group(1)),
        "new": _signed_int(new_match.group(1)),
        "base_energy_cost_change": False,
        "interpretation": "Attached effect under 应对状态; do not write this as move.energy_cost.",
    }


def semantic_move_effect_changes(item: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    old_text = item.get("patch_old_text")
    new_text = item.get("patch_new_text")
    response_state_energy = _response_state_energy_reduction(old_text, new_text)
    if response_state_energy:
        changes.append(response_state_energy)
    for check in item.get("field_checks") or []:
        changes.append(
            {
                "field": check.get("field"),
                "current_a_layer": check.get("current_a_layer"),
                "patch_old": check.get("patch_old"),
                "patch_new": check.get("patch_new"),
                "old_matches_current_a_layer": check.get("old_matches_current_a_layer"),
                "base_energy_cost_change": check.get("field") == "energy_cost",
            }
        )
    for structured in item.get("structured_changes") or []:
        changes.append({"field": structured.get("field"), "structured_change": structured})
    return changes


def build_overlay_payload(
    *,
    reconciliation: dict[str, Any],
    base_snapshot_ref: str,
    patch_delta_ref: str,
    reconciliation_ref: str,
    official_source_ref: str,
    created_at: str,
) -> dict[str, Any]:
    unresolved = reconciliation.get("unresolved_or_non_dex_items") or []
    stat_overlays = []
    for item in reconciliation.get("stat_overlays") or []:
        stat_overlays.append(
            {
                "entry_id": f"stat/{(item.get('resolution') or {}).get('species', {}).get('species_id')}/{item.get('source_image_id')}",
                "runtime_allowed": False,
                "status": item.get("status"),
                "source_image_id": item.get("source_image_id"),
                "overlay_action": "update_species_base_stats_candidate",
                "target": _species_target(item.get("resolution") or {}),
                "changes": item.get("changes") or [],
                "pm_review_note": item.get("pm_review_note"),
            }
        )

    ability_overlays = []
    for item in reconciliation.get("ability_overlays") or []:
        ability = _ability_target(item.get("ability_resolution") or {})
        species = _species_target(item.get("species_resolution") or {})
        ability_overlays.append(
            {
                "entry_id": f"ability/{species.get('species_id')}/{ability.get('ability_id')}/{item.get('source_image_id')}",
                "runtime_allowed": False,
                "status": item.get("status"),
                "source_image_id": item.get("source_image_id"),
                "overlay_action": "update_species_ability_effect_candidate",
                "target": {"species": species, "ability": ability},
                "patch_old_effect": item.get("patch_old_effect"),
                "patch_new_effect": item.get("patch_new_effect"),
                "pm_review_note": item.get("pm_review_note"),
            }
        )

    move_pool_additions = []
    for item in reconciliation.get("move_pool_additions") or []:
        species = _species_target(item.get("species_resolution") or {})
        move = _move_target(item.get("move_resolution") or {})
        action = "add_species_move_pool_candidate"
        if item.get("status") == "already_present_in_current_a_layer":
            action = "no_op_already_present_reference"
        move_pool_additions.append(
            {
                "entry_id": f"move_pool/{species.get('species_id')}/{move.get('move_id')}/{item.get('source_image_id')}",
                "runtime_allowed": False,
                "status": item.get("status"),
                "source_image_id": item.get("source_image_id"),
                "overlay_action": action,
                "species_label": item.get("species_label"),
                "target": {"species": species, "move": move},
                "current_a_layer_entries": item.get("current_a_layer_entries") or [],
            }
        )

    move_effect_overlays = []
    for item in reconciliation.get("move_effect_overlays") or []:
        move = _move_target(item.get("move_resolution") or {})
        semantic_changes = semantic_move_effect_changes(item)
        move_effect_overlays.append(
            {
                "entry_id": f"move_effect/{move.get('move_id')}/{item.get('source_image_id')}",
                "runtime_allowed": False,
                "status": item.get("status"),
                "source_image_id": item.get("source_image_id"),
                "overlay_action": "update_move_effect_candidate",
                "target": {"move": move},
                "patch_old_text": item.get("patch_old_text"),
                "patch_new_text": item.get("patch_new_text"),
                "semantic_changes": semantic_changes,
                "field_checks": item.get("field_checks") or [],
                "structured_changes": item.get("structured_changes") or [],
            }
        )

    wording_updates = []
    mechanism_concept_routes = []
    for item in reconciliation.get("wording_updates") or []:
        record = {
            "entry_id": f"wording/{item.get('entity_type')}/{item.get('source_image_id')}/{(item.get('resolution') or {}).get('canonical_query')}",
            "runtime_allowed": False,
            "status": item.get("status"),
            "source_image_id": item.get("source_image_id"),
            "entity_type": item.get("entity_type"),
            "current_a_layer_text": item.get("current_a_layer_text"),
            "patch_old_text": item.get("patch_old_text"),
            "patch_new_text": item.get("patch_new_text"),
            "pm_review_note": item.get("pm_review_note"),
        }
        if item.get("entity_type") == "ability":
            record["target"] = {"ability": _ability_target(item.get("resolution") or {})}
        elif item.get("entity_type") == "move":
            record["target"] = {"move": _move_target(item.get("resolution") or {})}
        else:
            record["target"] = {"concept": (item.get("resolution") or {}).get("canonical_query")}
        if item.get("status") == "routed_to_mechanism_concept_candidate":
            record["overlay_action"] = "route_to_b_layer_mechanism_concept_candidate"
            record["mechanism_route_note"] = item.get("mechanism_route_note")
            mechanism_concept_routes.append(record)
        else:
            record["overlay_action"] = "update_wording_candidate"
            wording_updates.append(record)

    waterblade_entries = [
        item
        for item in move_effect_overlays
        if ((item.get("target") or {}).get("move") or {}).get("move_name") == "水刃"
    ]
    waterblade_ok = any(
        change.get("field") == "response_state_attached_effect_energy_reduction"
        and change.get("old") == -4
        and change.get("new") == -3
        and change.get("base_energy_cost_change") is False
        for entry in waterblade_entries
        for change in entry.get("semantic_changes") or []
    )

    summary = dict(reconciliation.get("summary") or {})
    summary.update(
        {
            "overlay_stat_entries": len(stat_overlays),
            "overlay_ability_entries": len(ability_overlays),
            "overlay_move_pool_entries": len(move_pool_additions),
            "overlay_move_effect_entries": len(move_effect_overlays),
            "overlay_wording_entries": len(wording_updates),
            "mechanism_concept_route_entries": len(mechanism_concept_routes),
            "unresolved_or_non_dex_items": len(unresolved),
            "waterblade_response_state_energy_reduction_ok": waterblade_ok,
        }
    )

    blockers = [
        "pm_review_required_before_runtime_or_a_layer_write",
        "runtime_db_snapshot_required_before_runtime_promotion",
        "do_not_overwrite_data_runtime_battle_dex_sqlite",
    ]
    if mechanism_concept_routes:
        blockers.append("b_layer_mechanism_concept_review_required_for_routed_wording_items")
    if unresolved:
        blockers.append("unresolved_or_non_dex_items_require_resolution_before_overlay_use")
    if not waterblade_ok:
        blockers.append("waterblade_response_state_energy_reduction_semantics_missing")

    return {
        "schema_version": "p14.a_layer_overlay.v0",
        "id": "s2_2026-05-21_a_layer_overlay_candidate_v0",
        "created_at": created_at,
        "game_epoch": "s2_2026-05-21_candidate",
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "base_snapshot_ref": base_snapshot_ref,
        "patch_delta_ref": patch_delta_ref,
        "reconciliation_ref": reconciliation_ref,
        "official_source_ref": official_source_ref,
        "may_write_runtime_db": False,
        "requires_pm_review_before_runtime": True,
        "requires_pm_review_before_a_layer_write": True,
        "summary": summary,
        "remaining_blockers": blockers,
        "entries": {
            "stat_overlays": stat_overlays,
            "ability_overlays": ability_overlays,
            "move_pool_additions": move_pool_additions,
            "move_effect_overlays": move_effect_overlays,
            "wording_updates": wording_updates,
            "mechanism_concept_routes": mechanism_concept_routes,
        },
        "unresolved_or_non_dex_items": unresolved,
    }


def _reconciliation_summary(reconciliation: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "p14.a_layer_overlay_reconciliation_summary.v0",
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "reconciliation_id": reconciliation.get("id"),
        "reconciliation_summary": reconciliation.get("summary") or {},
        "overlay_summary": overlay.get("summary") or {},
        "unresolved_or_non_dex_items": reconciliation.get("unresolved_or_non_dex_items") or [],
        "remaining_blockers": overlay.get("remaining_blockers") or [],
    }


def _validation_evidence(
    *,
    validation_status: str,
    validation_note: str,
    runtime_db_sha_before: str | None,
    runtime_db_sha_after: str | None,
    runtime_db_current_sha: str,
) -> dict[str, Any]:
    return {
        "schema_version": "p14.a_layer_overlay_validation_evidence.v0",
        "runtime_allowed": False,
        "validation_status": validation_status,
        "validation_note": validation_note,
        "runtime_db_sha256_before": runtime_db_sha_before or runtime_db_current_sha,
        "runtime_db_sha256_after": runtime_db_sha_after or runtime_db_current_sha,
        "runtime_db_sha256_current": runtime_db_current_sha,
        "runtime_db_byte_identical_before_after": (runtime_db_sha_before or runtime_db_current_sha)
        == (runtime_db_sha_after or runtime_db_current_sha)
        == runtime_db_current_sha,
        "commands": [
            {
                "command": "PYTHONPATH=.:src .venv/bin/python tools/p14_reconcile_s2_patch_delta.py",
                "required": True,
            },
            {
                "command": "PYTHONPATH=.:src .venv/bin/python -m tools.p14_validate_knowledge_graph --strict",
                "required": True,
            },
            {
                "command": "PYTHONPATH=.:src .venv/bin/python -m unittest tests.test_import_battle_dex_sqlite tests.test_import_battle_dex_dry_run tests.test_p14_knowledge_graph_validate tests.test_p14_s2_a_layer_overlay_snapshot",
                "required": True,
            },
            {
                "command": "snapshot manifest hash self-check",
                "required": True,
            },
        ],
    }


def _dashboard(
    *,
    overlay: dict[str, Any],
    s1_manifest: dict[str, Any],
    manifest_ref: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    summary = overlay.get("summary") or {}
    return {
        "schema_version": "p14.a_layer_overlay_dashboard.v0",
        "id": "quality_dashboard_s2_a_layer_overlay_snapshot_2026-05-23",
        "generated_at": overlay.get("created_at"),
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "s1_freeze_exists": bool(s1_manifest.get("byte_identical_to_source")),
        "s1_snapshot_ref": "data/runtime/snapshots/s1_2026-05-20/manifest.yaml",
        "s2_overlay_exists": True,
        "s2_overlay_manifest_ref": manifest_ref,
        "post_s2_candidates_may_reference_overlay": summary.get("unresolved_or_non_dex_items", 0) == 0
        and summary.get("waterblade_response_state_energy_reduction_ok") is True,
        "reference_scope": "candidate_only_version_surface",
        "runtime_promotion_blocked": True,
        "gold_auto_accept_blocked": True,
        "reviewed_graph_materialization_blocked": True,
        "a_layer_db_overwrite_blocked": True,
        "unresolved_or_non_dex_items": summary.get("unresolved_or_non_dex_items", 0),
        "waterblade_response_state_energy_reduction_ok": summary.get("waterblade_response_state_energy_reduction_ok"),
        "remaining_blockers": overlay.get("remaining_blockers") or [],
        "validation": validation,
    }


def _pm_packet(
    *,
    overlay_dir: Path,
    s1_manifest: dict[str, Any],
    overlay: dict[str, Any],
    manifest_path: Path,
    dashboard_path: Path,
    validation: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> str:
    summary = overlay.get("summary") or {}
    runtime_hash_ok = validation.get("runtime_db_byte_identical_before_after") is True
    can_reference = summary.get("unresolved_or_non_dex_items", 0) == 0 and summary.get(
        "waterblade_response_state_energy_reduction_ok"
    ) is True
    return "\n".join(
        [
            "# P14 S2 A-layer Overlay Snapshot PM Packet",
            "",
            "## 结论",
            "- 已冻结 S1 Battle Dex，并生成 S2 candidate-only A-layer overlay。",
            "- 没有修改 `data/runtime/battle_dex.sqlite`，没有 runtime promotion、Gold auto-accept、reviewed graph materialization。",
            f"- runtime DB 前后 hash 一致：{runtime_hash_ok}。",
            f"- S2 reconciliation unresolved/non-dex items：{summary.get('unresolved_or_non_dex_items', 0)}。",
            f"- `水刃` 已按应对状态附加效果处理：{summary.get('waterblade_response_state_energy_reduction_ok')}; 不是 base energy_cost 变更。",
            "",
            "## Decision Table",
            "| Decision | Recommendation | Why | Forbidden Follow-through |",
            "|---|---|---|---|",
            f"| Accept S1 freeze | Accept | runtime DB 与冻结副本 hash 一致：{runtime_hash_ok} | 不代表切换 runtime DB |",
            f"| Accept S2 overlay as reference surface | Accept candidate-only | unresolved/non-dex={summary.get('unresolved_or_non_dex_items', 0)}，且 official/patch/reconciliation/base refs 都 hashable | 不得写回 `data/runtime/battle_dex.sqlite` |",
            f"| Let Phase48/Phase49 candidates cite overlay | Accept with blocker | can_reference={can_reference}，只作为 versioned A-layer reference | 不得解除 runtime/Gold/review blocker |",
            "| Promote S2 A-layer to production | Reject for this run | 本包没有构建 runtime DB，也没有 PM promotion audit | 不得 runtime promotion |",
            "| Auto-accept Gold/reviewed graph | Reject | 本包只处理 A-layer candidate overlay，不处理 Gold 或 graph card review | 不得 Gold auto-accept / graph materialization |",
            "",
            "## 文件",
            f"- S1 snapshot manifest: `{_repo_rel(DEFAULT_S1_DIR / 'manifest.yaml', repo_root=repo_root)}`",
            f"- S1 frozen DB copy: `{s1_manifest.get('snapshot', {}).get('path')}`",
            f"- S2 overlay: `{_repo_rel(overlay_dir / 'overlay.yaml', repo_root=repo_root)}`",
            f"- S2 overlay manifest: `{_repo_rel(manifest_path, repo_root=repo_root)}`",
            f"- Reconciliation summary: `{_repo_rel(overlay_dir / 'reconciliation_summary.yaml', repo_root=repo_root)}`",
            f"- Dashboard: `{_repo_rel(dashboard_path, repo_root=repo_root)}`",
            f"- Validation evidence: `{_repo_rel(overlay_dir / 'validation_evidence.yaml', repo_root=repo_root)}`",
            "",
            "## S1 Freeze 证明了什么",
            f"- 当前 runtime DB hash：`{s1_manifest.get('source', {}).get('sha256')}`。",
            f"- 冻结副本 hash：`{s1_manifest.get('snapshot', {}).get('sha256')}`。",
            "- 两者 byte-identical；S1 作为历史 baseline 保留，不代表切换 runtime。",
            "",
            "## S2 Overlay 包含什么",
            f"- stat overlays：{summary.get('overlay_stat_entries', 0)}。",
            f"- ability overlays：{summary.get('overlay_ability_entries', 0)}。",
            f"- move-pool additions：{summary.get('overlay_move_pool_entries', 0)}。",
            f"- move-effect overlays：{summary.get('overlay_move_effect_entries', 0)}。",
            f"- wording updates：{summary.get('overlay_wording_entries', 0)}。",
            f"- B-layer mechanism concept routes：{summary.get('mechanism_concept_route_entries', 0)}。",
            "",
            "## 仍然禁止",
            "- 禁止把 overlay 写回 `data/runtime/battle_dex.sqlite`。",
            "- 禁止把 overlay 当作 production A-layer truth。",
            "- 禁止由此自动放行 Gold、reviewed graph card、runtime answer。",
            "- 先手/先手度这类被路由到 B-layer 的概念仍需要机制规则复审。",
            "",
            "## PM 判断",
            f"- Phase48/Phase49 candidate-only items 可以引用这个 S2 overlay surface：{can_reference}。",
            "- 它们只能用来解释为什么 S2 受影响候选继续 blocked，不能据此进入 reviewed/runtime。",
            "- 真正 S2 runtime DB promotion 之前，还需要 PM review、版本化 runtime/A-layer DB 构建、回归测试和 promotion audit。",
            "",
            "## Validation",
            f"- status: `{validation.get('validation_status')}`",
            f"- note: {validation.get('validation_note')}",
            "",
        ]
    )


def build_snapshot_package(
    *,
    runtime_db: Path = DEFAULT_RUNTIME_DB,
    s1_dir: Path = DEFAULT_S1_DIR,
    overlay_dir: Path = DEFAULT_OVERLAY_DIR,
    patch_delta: Path = DEFAULT_PATCH_DELTA,
    reconciliation_path: Path = DEFAULT_RECONCILIATION,
    official_source: Path = DEFAULT_OFFICIAL_SOURCE,
    dashboard_path: Path = DEFAULT_DASHBOARD,
    created_at: str | None = None,
    validation_status: str = "pending_validation",
    validation_note: str = "validation not run yet",
    runtime_db_sha_before: str | None = None,
    runtime_db_sha_after: str | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    created = _timestamp(created_at)
    source_hash = _sha256(runtime_db)
    if runtime_db_sha_before and runtime_db_sha_before != source_hash:
        raise RuntimeError(f"runtime DB hash changed before package build: {runtime_db_sha_before} != {source_hash}")
    if runtime_db_sha_after and runtime_db_sha_after != source_hash:
        raise RuntimeError(f"runtime DB hash changed after validation: {runtime_db_sha_after} != {source_hash}")

    s1_manifest = write_s1_snapshot(runtime_db=runtime_db, snapshot_dir=s1_dir, created_at=created, repo_root=repo_root)
    reconciliation = _load_yaml(reconciliation_path)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    s1_manifest_ref = _repo_rel(s1_dir / "manifest.yaml", repo_root=repo_root)
    overlay = build_overlay_payload(
        reconciliation=reconciliation,
        base_snapshot_ref=s1_manifest_ref,
        patch_delta_ref=_repo_rel(patch_delta, repo_root=repo_root),
        reconciliation_ref=_repo_rel(reconciliation_path, repo_root=repo_root),
        official_source_ref=_repo_rel(official_source, repo_root=repo_root),
        created_at=created,
    )

    overlay_path = overlay_dir / "overlay.yaml"
    summary_path = overlay_dir / "reconciliation_summary.yaml"
    validation_path = overlay_dir / "validation_evidence.yaml"
    pm_packet_path = overlay_dir / "pm_review_packet.md"
    manifest_path = overlay_dir / "manifest.yaml"

    _write_yaml(overlay_path, overlay)
    _write_yaml(summary_path, _reconciliation_summary(reconciliation, overlay))
    validation = _validation_evidence(
        validation_status=validation_status,
        validation_note=validation_note,
        runtime_db_sha_before=runtime_db_sha_before,
        runtime_db_sha_after=runtime_db_sha_after,
        runtime_db_current_sha=source_hash,
    )
    _write_yaml(validation_path, validation)
    dashboard = _dashboard(
        overlay=overlay,
        s1_manifest=s1_manifest,
        manifest_ref=_repo_rel(manifest_path, repo_root=repo_root),
        validation=validation,
    )
    _write_yaml(dashboard_path, dashboard)
    pm_packet_path.write_text(
        _pm_packet(
            overlay_dir=overlay_dir,
            s1_manifest=s1_manifest,
            overlay=overlay,
            manifest_path=manifest_path,
            dashboard_path=dashboard_path,
            validation=validation,
            repo_root=repo_root,
        ),
        encoding="utf-8",
    )

    manifest = {
        "schema_version": "p14.a_layer_overlay_manifest.v0",
        "id": "s2_2026-05-21_a_layer_overlay_snapshot_manifest_v0",
        "created_at": created,
        "game_epoch": "s2_2026-05-21_candidate",
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "base_snapshot_ref": s1_manifest_ref,
        "base_snapshot_sha256": _sha256(s1_dir / "manifest.yaml"),
        "base_battle_dex_sha256": s1_manifest["snapshot"]["sha256"],
        "patch_delta_ref": _repo_rel(patch_delta, repo_root=repo_root),
        "patch_delta_sha256": _sha256(patch_delta),
        "reconciliation_ref": _repo_rel(reconciliation_path, repo_root=repo_root),
        "reconciliation_sha256": _sha256(reconciliation_path),
        "official_source_ref": _repo_rel(official_source, repo_root=repo_root),
        "official_source_sha256": _sha256(official_source),
        "overlay_ref": _repo_rel(overlay_path, repo_root=repo_root),
        "overlay_sha256": _sha256(overlay_path),
        "reconciliation_summary_ref": _repo_rel(summary_path, repo_root=repo_root),
        "reconciliation_summary_sha256": _sha256(summary_path),
        "dashboard_ref": _repo_rel(dashboard_path, repo_root=repo_root),
        "dashboard_sha256": _sha256(dashboard_path),
        "pm_review_packet_ref": _repo_rel(pm_packet_path, repo_root=repo_root),
        "pm_review_packet_sha256": _sha256(pm_packet_path),
        "validation_evidence_ref": _repo_rel(validation_path, repo_root=repo_root),
        "validation_evidence_sha256": _sha256(validation_path),
        "may_write_runtime_db": False,
        "requires_pm_review_before_runtime": True,
        "requires_pm_review_before_a_layer_write": True,
        "remaining_blockers": overlay.get("remaining_blockers") or [],
    }
    _write_yaml(manifest_path, manifest)

    return {
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "s1_snapshot_manifest": s1_manifest_ref,
        "s2_overlay_manifest": _repo_rel(manifest_path, repo_root=repo_root),
        "s2_overlay": _repo_rel(overlay_path, repo_root=repo_root),
        "dashboard": _repo_rel(dashboard_path, repo_root=repo_root),
        "pm_review_packet": _repo_rel(pm_packet_path, repo_root=repo_root),
        "validation_evidence": _repo_rel(validation_path, repo_root=repo_root),
        "summary": overlay.get("summary") or {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-db", type=Path, default=DEFAULT_RUNTIME_DB)
    parser.add_argument("--s1-dir", type=Path, default=DEFAULT_S1_DIR)
    parser.add_argument("--overlay-dir", type=Path, default=DEFAULT_OVERLAY_DIR)
    parser.add_argument("--patch-delta", type=Path, default=DEFAULT_PATCH_DELTA)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    parser.add_argument("--official-source", type=Path, default=DEFAULT_OFFICIAL_SOURCE)
    parser.add_argument("--dashboard-path", type=Path, default=DEFAULT_DASHBOARD)
    parser.add_argument("--created-at")
    parser.add_argument("--validation-status", default="pending_validation")
    parser.add_argument("--validation-note", default="validation not run yet")
    parser.add_argument("--runtime-db-sha-before")
    parser.add_argument("--runtime-db-sha-after")
    args = parser.parse_args()

    result = build_snapshot_package(
        runtime_db=args.runtime_db,
        s1_dir=args.s1_dir,
        overlay_dir=args.overlay_dir,
        patch_delta=args.patch_delta,
        reconciliation_path=args.reconciliation,
        official_source=args.official_source,
        dashboard_path=args.dashboard_path,
        created_at=args.created_at,
        validation_status=args.validation_status,
        validation_note=args.validation_note,
        runtime_db_sha_before=args.runtime_db_sha_before,
        runtime_db_sha_after=args.runtime_db_sha_after,
    )
    print(yaml.dump(result, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper).strip())


if __name__ == "__main__":
    main()
