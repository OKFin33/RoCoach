#!/usr/bin/env python3
"""Find compact recluster candidates inside P14 split blockers.

This is a control-plane audit. It reads the latest Set Inventory consolidation
and emits candidate family cores that have full-source cooccurrence evidence.
It does not update source_queue, review ledgers, graph cards, or runtime data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import DEFAULT_OUT_ROOT, DEFAULT_SOURCE_QUEUE, NoAliasDumper, REPO_ROOT, _relpath


DEFAULT_BATCH_ID = f"phase1_recluster_split_blockers_{date.today().isoformat()}"
DEFAULT_FAMILY_REVIEW_LEDGER = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "review_state" / "family_review_ledger.yaml"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
RECLUSTER_DIRNAME = "recluster"
MIN_FULL_CORE_SOURCES = 3
MIN_FOCUSED_FULL_CORE_SOURCES = 2
CORE_SIZE_MIN = 3
CORE_SIZE_MAX = 4


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


def _species_id_index(battle_dex: Path) -> dict[str, list[str]]:
    if not battle_dex.exists():
        return {}
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(battle_dex)
        rows = conn.execute("SELECT display_name, species_id FROM species_form").fetchall()
    except sqlite3.Error:
        return {}
    finally:
        if conn is not None:
            conn.close()
    index: dict[str, list[str]] = {}
    for display_name, species_id in rows:
        if display_name and species_id:
            index.setdefault(str(display_name), []).append(str(species_id))
    return index


def _latest_consolidation_from_queue(source_queue: Path) -> Path:
    queue = _load_yaml(source_queue)
    latest = queue.get("latest_set_inventory_consolidation") or {}
    path = _repo_path(latest.get("consolidation_path"))
    if path and path.exists():
        return path
    raise SystemExit(f"latest consolidation not found in {source_queue}")


def _reviewed_core_index(family_ledger: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in family_ledger.get("entries") or []:
        proposed = entry.get("proposed_card") or {}
        species_name = str(proposed.get("canonical_species_name") or "")
        core_moves = [str(move) for move in proposed.get("core_moves") or [] if move]
        if not species_name or not core_moves:
            continue
        index[species_name].append(
            {
                "review_id": entry.get("review_id"),
                "review_status": ((entry.get("review") or {}).get("review_status")),
                "family_name": proposed.get("proposed_family_name"),
                "core_moves": core_moves,
                "core_key": tuple(sorted(core_moves)),
            }
        )
    return index


def _combo_source_index(family: dict[str, Any]) -> dict[tuple[str, ...], list[str]]:
    primary_source_ids = {str(source_id) for source_id in family.get("primary_source_ids") or [] if source_id}
    combo_sources: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for variant in family.get("alter_variants") or []:
        source_id = str(variant.get("source_id") or "")
        if primary_source_ids and source_id not in primary_source_ids:
            continue
        if variant.get("low_confidence_use"):
            continue
        moves = sorted({str(move) for move in variant.get("moves") or [] if move})
        for size in range(CORE_SIZE_MIN, min(CORE_SIZE_MAX, len(moves)) + 1):
            for combo in combinations(moves, size):
                combo_sources[combo].append(source_id)
    return combo_sources


def _top_flex_moves(family: dict[str, Any], core: tuple[str, ...], source_ids: list[str], limit: int = 4) -> list[str]:
    core_set = set(core)
    source_set = set(source_ids)
    counts: Counter[str] = Counter()
    for variant in family.get("alter_variants") or []:
        if str(variant.get("source_id") or "") not in source_set:
            continue
        moves = {str(move) for move in variant.get("moves") or [] if move}
        if not core_set.issubset(moves):
            continue
        counts.update(move for move in moves if move not in core_set)
    return [move for move, _ in counts.most_common(limit)]


def _focused_species_source_ids(
    *,
    species_name: str,
    source_ids: list[str],
    source_quality: dict[str, Any],
) -> list[str]:
    if not source_quality:
        return list(source_ids)
    aliases = {species_name}
    if len(species_name) >= 3:
        aliases.add(species_name[-2:])
    focused: list[str] = []
    for source_id in source_ids:
        row = source_quality.get(source_id) or {}
        title = str(row.get("title") or "")
        if any(alias and alias in title for alias in aliases):
            focused.append(source_id)
    return focused


def _gate_candidate(
    *,
    species_name: str,
    core: tuple[str, ...],
    full_source_count: int,
    focused_source_count: int,
    reviewed_index: dict[str, list[dict[str, Any]]],
    ambiguous_species_ids: list[str],
) -> tuple[str, str, dict[str, Any]]:
    if ambiguous_species_ids:
        return (
            "blocked_by_ambiguous_species_id",
            "resolve A-layer species identity before PM review",
            {"ambiguous_species_ids": ambiguous_species_ids},
        )

    reviewed_entries = reviewed_index.get(species_name) or []
    core_set = set(core)
    for entry in reviewed_entries:
        reviewed_core = set(entry.get("core_moves") or [])
        if core_set == reviewed_core:
            if entry.get("review_status") != "pm_reviewed":
                return (
                    "previously_deferred_core",
                    "recheck the existing technical-defer entry before asking PM",
                    {"deferred_entry": entry},
                )
            return (
                "already_reviewed_core",
                "do not reopen PM review for an exact reviewed family core",
                {"reviewed_entry": entry},
            )

    overlap_entries: list[dict[str, Any]] = []
    for entry in reviewed_entries:
        if entry.get("review_status") != "pm_reviewed":
            continue
        reviewed_core = set(entry.get("core_moves") or [])
        overlap = sorted(core_set & reviewed_core)
        if len(overlap) >= 2:
            overlap_entries.append({**entry, "overlap_moves": overlap})
    if overlap_entries:
        return (
            "blocked_by_reviewed_core_overlap",
            "treat as boundary evidence; do not promote an unreviewed core expansion",
            {"overlap_reviewed_entries": overlap_entries},
        )

    if full_source_count < MIN_FULL_CORE_SOURCES:
        return (
            "needs_more_full_core_sources",
            f"requires at least {MIN_FULL_CORE_SOURCES} primary sources with the full core",
            {},
        )
    if focused_source_count < MIN_FOCUSED_FULL_CORE_SOURCES:
        return (
            "needs_more_focused_full_core_sources",
            f"requires at least {MIN_FOCUSED_FULL_CORE_SOURCES} focused sources whose title names this species or common short alias",
            {},
        )

    return (
        "candidate_for_pm_recluster_packet",
        "can become a focused PM packet after source-span spot check",
        {},
    )


def build_recluster_audit(
    *,
    batch_id: str,
    consolidation: dict[str, Any],
    family_ledger: dict[str, Any],
    species_index: dict[str, list[str]],
    max_candidates_per_species: int = 5,
) -> dict[str, Any]:
    reviewed_index = _reviewed_core_index(family_ledger)
    source_quality = consolidation.get("source_quality") or {}
    species_reports: list[dict[str, Any]] = []

    for record in consolidation.get("species_records") or []:
        if record.get("state") != "split_blocked":
            continue
        species_name = str(record.get("species_name") or "")
        ambiguous_species_ids = species_index.get(species_name) or []
        proposals: list[dict[str, Any]] = []
        seen: set[tuple[str, ...]] = set()
        for family in record.get("set_family_candidates") or []:
            combo_sources = _combo_source_index(family)
            for core, source_ids in combo_sources.items():
                unique_source_ids = sorted(set(source_ids))
                if len(unique_source_ids) < 2:
                    continue
                if core in seen:
                    continue
                seen.add(core)
                focused_source_ids = _focused_species_source_ids(
                    species_name=species_name,
                    source_ids=unique_source_ids,
                    source_quality=source_quality,
                )
                gate_status, recommended_action, extras = _gate_candidate(
                    species_name=species_name,
                    core=core,
                    full_source_count=len(unique_source_ids),
                    focused_source_count=len(focused_source_ids),
                    reviewed_index=reviewed_index,
                    ambiguous_species_ids=ambiguous_species_ids if len(ambiguous_species_ids) > 1 else [],
                )
                proposal = {
                    "species_name": species_name,
                    "source_family_id": family.get("family_id"),
                    "proposed_core_moves": list(core),
                    "core_size": len(core),
                    "full_core_primary_source_count": len(unique_source_ids),
                    "primary_source_ids": unique_source_ids,
                    "focused_full_core_primary_source_count": len(focused_source_ids),
                    "focused_primary_source_ids": focused_source_ids,
                    "flex_moves_from_full_core_sources": _top_flex_moves(family, core, unique_source_ids),
                    "gate_status": gate_status,
                    "recommended_action": recommended_action,
                    "runtime_allowed": False,
                }
                proposal.update(extras)
                proposals.append(proposal)

        _mark_overlapping_candidate_clusters(proposals)
        proposals.sort(
            key=lambda item: (
                item["gate_status"] != "candidate_for_pm_recluster_packet",
                -int(item["full_core_primary_source_count"]),
                -int(item["core_size"]),
                item["species_name"],
                tuple(item["proposed_core_moves"]),
            )
        )
        species_reports.append(
            {
                "species_name": species_name,
                "primary_source_count": record.get("primary_source_count", 0),
                "stable_moves": list(record.get("stable_moves") or []),
                "overwide_move_pool_blocked": bool((record.get("set_family_summary") or {}).get("overwide_move_pool_blocked")),
                "split_hypothesis_count": len(record.get("split_hypotheses") or []),
                "family_review_candidate_count": len(record.get("family_review_candidates") or []),
                "candidate_proposals": proposals[:max_candidates_per_species],
                "proposal_count": len(proposals),
                "runtime_allowed": False,
            }
        )

    all_proposals = [
        proposal
        for report in species_reports
        for proposal in report.get("candidate_proposals") or []
    ]
    gate_counts = Counter(proposal["gate_status"] for proposal in all_proposals)
    ready = [proposal for proposal in all_proposals if proposal["gate_status"] == "candidate_for_pm_recluster_packet"]
    species_reports.sort(
        key=lambda item: (
            not any(p["gate_status"] == "candidate_for_pm_recluster_packet" for p in item.get("candidate_proposals") or []),
            -int(item.get("primary_source_count") or 0),
            item.get("species_name") or "",
        )
    )
    return {
        "schema_version": "p14.split_recluster_audit.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source_consolidation_batch_id": consolidation.get("batch_id"),
        "policy": {
            "min_full_core_primary_sources": MIN_FULL_CORE_SOURCES,
            "min_focused_full_core_primary_sources": MIN_FOCUSED_FULL_CORE_SOURCES,
            "core_size_min": CORE_SIZE_MIN,
            "core_size_max": CORE_SIZE_MAX,
            "promotion_forbidden": True,
            "source_queue_updates": False,
        },
        "summary": {
            "split_blocked_species_count": len(species_reports),
            "candidate_proposal_count": len(all_proposals),
            "pm_recluster_candidate_count": len(ready),
            "gate_status_counts": dict(gate_counts),
            "recommended_next_action": (
                "build_focused_pm_recluster_packet_for_top_candidate"
                if ready
                else "continue_source_discovery_or_recluster_algorithm_work"
            ),
        },
        "species_reports": species_reports,
    }


def _mark_overlapping_candidate_clusters(proposals: list[dict[str, Any]]) -> None:
    ready_indices = [
        index
        for index, proposal in enumerate(proposals)
        if proposal.get("gate_status") == "candidate_for_pm_recluster_packet"
    ]
    clustered: set[int] = set()
    for left_pos, left_index in enumerate(ready_indices):
        left = proposals[left_index]
        left_core = set(left.get("proposed_core_moves") or [])
        for right_index in ready_indices[left_pos + 1 :]:
            right = proposals[right_index]
            if left.get("source_family_id") != right.get("source_family_id"):
                continue
            right_core = set(right.get("proposed_core_moves") or [])
            if len(left_core & right_core) >= CORE_SIZE_MIN - 1:
                clustered.add(left_index)
                clustered.add(right_index)

    for index in clustered:
        proposals[index]["gate_status"] = "candidate_cluster_needs_axis_resolution"
        proposals[index]["recommended_action"] = (
            "shared core overlaps another compact candidate; resolve as one alter-family axis before PM review"
        )


def render_recluster_brief(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    reports = payload.get("species_reports") or []
    ready = [
        proposal
        for report in reports
        for proposal in report.get("candidate_proposals") or []
        if proposal.get("gate_status") == "candidate_for_pm_recluster_packet"
    ]
    deferred = [
        proposal
        for report in reports
        for proposal in report.get("candidate_proposals") or []
        if proposal.get("gate_status") != "candidate_for_pm_recluster_packet"
    ]

    lines = [
        f"# P14 Split Blocker Recluster Audit: {payload['batch_id']}",
        "",
        "## 结论",
        "- 这是 split blocker 的技术审计，不是 promotion，也不会写 graph/runtime。",
        f"- 检查 {summary.get('split_blocked_species_count', 0)} 个 split_blocked species，找到 {summary.get('candidate_proposal_count', 0)} 条紧凑 core 候选。",
        f"- 可转成 focused PM packet 的候选：{summary.get('pm_recluster_candidate_count', 0)} 条。",
        f"- 下一动作：`{summary.get('recommended_next_action')}`。",
        "",
        "## 可转 PM Packet 的候选",
    ]
    if ready:
        for proposal in ready[:10]:
            core = " / ".join(proposal.get("proposed_core_moves") or [])
            flex = " / ".join(proposal.get("flex_moves_from_full_core_sources") or []) or "无"
            sources = ", ".join(proposal.get("primary_source_ids") or [])
            lines.append(
                f"- {proposal['species_name']} {proposal['source_family_id']}：core={core}；完整共现源 {proposal['full_core_primary_source_count']} 条，focused {proposal.get('focused_full_core_primary_source_count', 0)} 条；flex={flex}；sources={sources}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(["", "## 暂不问 PM 的候选"])
    if deferred:
        for proposal in deferred[:12]:
            core = " / ".join(proposal.get("proposed_core_moves") or [])
            lines.append(
                f"- {proposal['species_name']} {proposal['source_family_id']}：core={core}；完整共现源 {proposal['full_core_primary_source_count']}，focused {proposal.get('focused_full_core_primary_source_count', 0)}；原因 {proposal['gate_status']}；动作 {proposal['recommended_action']}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(["", "## 仍然卡住的高证据 Species"])
    for report in reports[:12]:
        stable = " / ".join((report.get("stable_moves") or [])[:8])
        lines.append(
            f"- {report['species_name']}：主证 {report.get('primary_source_count')}；稳定技能 {stable}；split {report.get('split_hypothesis_count')}；候选 {report.get('proposal_count')}。"
        )

    lines.extend(
        [
            "",
            "## 边界",
            "- 这些候选只说明“有多个 source 同时出现这些技能”，不等于 set 已成立。",
            "- 已审 core 的完全重复不会重新问 PM；与已审 core 高重叠的新 core 只作为边界证据。",
            "- A-layer 身份有歧义的 species 先修 identity，不进入 PM review。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_recluster_audit(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    consolidation_path: Path | None = None,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    family_review_ledger: Path = DEFAULT_FAMILY_REVIEW_LEDGER,
    battle_dex: Path = DEFAULT_BATTLE_DEX,
) -> dict[str, Any]:
    consolidation_path = consolidation_path or _latest_consolidation_from_queue(source_queue)
    consolidation = _load_yaml(consolidation_path)
    payload = build_recluster_audit(
        batch_id=batch_id,
        consolidation=consolidation,
        family_ledger=_load_yaml(family_review_ledger),
        species_index=_species_id_index(battle_dex),
    )
    payload["input"] = {
        "consolidation_path": _relpath(consolidation_path),
        "family_review_ledger": _relpath(family_review_ledger),
    }
    audit_path = out_root / RECLUSTER_DIRNAME / f"{batch_id}.yaml"
    brief_path = out_root / "review_packets" / f"{batch_id}_split_recluster.md"
    _write_yaml(audit_path, payload)
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(render_recluster_brief(payload), encoding="utf-8")
    return {
        "runtime_allowed": False,
        "paths": {"audit": _relpath(audit_path), "pm_brief": _relpath(brief_path)},
        "summary": payload["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--consolidation-path", type=Path)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--family-review-ledger", type=Path, default=DEFAULT_FAMILY_REVIEW_LEDGER)
    parser.add_argument("--battle-dex", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_recluster_audit(
        source_queue=args.source_queue,
        consolidation_path=args.consolidation_path,
        out_root=args.out_root,
        batch_id=args.batch_id,
        family_review_ledger=args.family_review_ledger,
        battle_dex=args.battle_dex,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {result['paths']['pm_brief']}")


if __name__ == "__main__":
    main()
