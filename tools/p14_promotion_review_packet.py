#!/usr/bin/env python3
"""Build focused PM packets for P14 promotion-lane review candidates.

The packet is review substrate only. It never promotes graph/runtime data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import DEFAULT_OUT_ROOT, DEFAULT_SOURCE_QUEUE, NoAliasDumper, REPO_ROOT, _relpath


DEFAULT_BATCH_ID = f"p14_promotion_review_{date.today().isoformat()}"
DEFAULT_CONSOLIDATION_DIR = DEFAULT_OUT_ROOT / "set_inventory_consolidation"


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


def _latest_consolidation_path(consolidation_dir: Path = DEFAULT_CONSOLIDATION_DIR) -> Path | None:
    paths = sorted(consolidation_dir.glob("*.yaml"), key=lambda path: (path.stat().st_mtime, path.name))
    return paths[-1] if paths else None


def _source_map(source_queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("source_id")): item for item in source_queue.get("sources") or [] if item.get("source_id")}


def _source_summary(source_id: str, sources_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = sources_by_id.get(source_id, {})
    subtitle = source.get("subtitle_status") or {}
    foundation = ((source.get("source_quality_prior") or {}).get("latest_evidence_foundation") or {})
    return {
        "source_id": source_id,
        "title": str(source.get("title") or source_id),
        "url": str(source.get("url") or ""),
        "source_type": str(source.get("source_type") or ""),
        "ingest_status": str(source.get("ingest_status") or ""),
        "transcript_method": str(subtitle.get("transcript_method") or ""),
        "segment_count": foundation.get("segment_count"),
        "claim_atom_count": foundation.get("claim_atom_count"),
    }


def _find_species_record(consolidation: dict[str, Any], species_name: str) -> dict[str, Any]:
    for record in consolidation.get("species_records") or []:
        if str(record.get("species_name") or "") == species_name:
            return record
    raise ValueError(f"species record not found: {species_name}")


def _move_support(record: dict[str, Any], stable_moves: list[str]) -> list[dict[str, Any]]:
    observed = {str(item.get("move_name") or ""): item for item in record.get("observed_moves") or []}
    rows: list[dict[str, Any]] = []
    for move in stable_moves:
        item = observed.get(move, {})
        rows.append(
            {
                "move_name": move,
                "primary_source_count": int(item.get("primary_source_count") or 0),
                "source_count": int(item.get("source_count") or 0),
                "source_ids": [str(source_id) for source_id in item.get("sources") or []],
            }
        )
    return rows


def _variant_rows(
    record: dict[str, Any],
    stable_moves: list[str],
    sources_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    stable = set(stable_moves)
    rows: list[dict[str, Any]] = []
    for variant in record.get("dossier_variants") or []:
        source_id = str(variant.get("source_id") or "")
        moves = [str(move) for move in variant.get("moves") or []]
        core_overlap = [move for move in moves if move in stable]
        if not core_overlap:
            continue
        source = _source_summary(source_id, sources_by_id)
        rows.append(
            {
                "source_id": source_id,
                "title": source["title"],
                "url": source["url"],
                "source_type": str(variant.get("source_type") or source["source_type"]),
                "transcript_method": source["transcript_method"],
                "moves": moves,
                "core_overlap_moves": core_overlap,
                "core_overlap_count": len(core_overlap),
                "completeness": str(variant.get("completeness") or ""),
                "roles": [str(role) for role in variant.get("roles") or []],
                "role_groups": [str(role) for role in variant.get("role_groups") or []],
                "damage_axis": str(variant.get("damage_axis") or ""),
                "build_axes": [str(axis) for axis in variant.get("build_axes") or []],
                "mention_count": int(variant.get("mention_count") or 0),
                "segment_count": source["segment_count"],
                "claim_atom_count": source["claim_atom_count"],
            }
        )
    rows.sort(key=lambda row: (-row["core_overlap_count"], -row["mention_count"], row["source_id"]))
    return rows


def _cooccurrence_stats(stable_moves: list[str], variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stable_count = len(stable_moves)
    overlap_counts = Counter(int(row.get("core_overlap_count") or 0) for row in variant_rows)
    max_overlap = max(overlap_counts.keys(), default=0)
    return {
        "stable_move_count": stable_count,
        "max_core_moves_in_one_source": max_overlap,
        "source_count_with_full_core": sum(1 for row in variant_rows if int(row.get("core_overlap_count") or 0) >= stable_count),
        "source_count_with_3plus_core": sum(1 for row in variant_rows if int(row.get("core_overlap_count") or 0) >= 3),
        "source_count_with_2plus_core": sum(1 for row in variant_rows if int(row.get("core_overlap_count") or 0) >= 2),
        "source_count_with_single_core": overlap_counts.get(1, 0),
    }


def _recommended_decision(record: dict[str, Any], stats: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if record.get("split_hypotheses"):
        reasons.append("该物种已经有分流派假设，recluster 前不要接受物种级 set 卡。")
        return "defer", reasons
    if stats["source_count_with_full_core"] >= 2:
        reasons.append("至少两条来源同源支持完整稳定技能核心。")
        return "accept_as_species_set_candidate", reasons
    if stats["source_count_with_3plus_core"] >= 2:
        reasons.append("至少两条来源同源支持 3 个以上稳定技能，可以作为缺槽候选。")
        return "accept_as_species_set_candidate_with_missing_slot_caveat", reasons
    if stats["source_count_with_3plus_core"] == 1:
        reasons.append("只有一条来源同源支持 3 个以上稳定技能，还需要补证。")
        return "defer_until_more_same-core_evidence", reasons
    if stats["source_count_with_2plus_core"] > 0:
        reasons.append("当前证据是跨源聚合，同一来源最多只支持 2 个核心技能。")
    else:
        reasons.append("当前证据只有跨源单技能支持。")
    reasons.append("不要把重复出现的孤立技能名直接升成 reviewed set。")
    return "defer_until_more_same-core_evidence", reasons


def build_species_review_packet(
    *,
    consolidation_path: Path,
    species_name: str,
    source_queue_path: Path = DEFAULT_SOURCE_QUEUE,
    batch_id: str = DEFAULT_BATCH_ID,
    out_root: Path = DEFAULT_OUT_ROOT,
) -> dict[str, Any]:
    consolidation = _load_yaml(consolidation_path)
    source_queue = _load_yaml(source_queue_path)
    sources_by_id = _source_map(source_queue)
    record = _find_species_record(consolidation, species_name)
    stable_moves = [str(move) for move in record.get("stable_moves") or []]
    variants = _variant_rows(record, stable_moves, sources_by_id)
    stats = _cooccurrence_stats(stable_moves, variants)
    decision, reasons = _recommended_decision(record, stats)

    packet = {
        "schema_version": "p14.promotion_review_packet.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "review_scope": "species_review_candidate",
        "source_consolidation": _relpath(consolidation_path),
        "candidate": {
            "species_name": species_name,
            "state": record.get("state"),
            "stable_moves": stable_moves,
            "top_roles": record.get("top_roles") or [],
            "primary_source_count": record.get("primary_source_count"),
            "source_count": record.get("source_count"),
            "suggested_next_action": record.get("suggested_next_action"),
            "promotion_blockers": record.get("promotion_blockers") or [],
        },
        "evidence_shape": {
            **stats,
            "move_support": _move_support(record, stable_moves),
            "supporting_variants": variants,
            "set_family_summary": record.get("set_family_summary") or {},
            "set_family_candidates": record.get("set_family_candidates") or [],
            "split_hypotheses": record.get("split_hypotheses") or [],
        },
        "recommendation": {
            "recommended_decision": decision,
            "reasons": reasons,
            "pm_options": [
                "accept_as_candidate_only",
                "defer_until_more_same-core_evidence",
                "reject_as_false_cluster",
            ],
        },
    }

    yaml_path = out_root / "review_packets" / f"{batch_id}_promotion_review.yaml"
    md_path = out_root / "review_packets" / f"{batch_id}_promotion_review.md"
    _write_yaml(yaml_path, packet)
    md_path.write_text(render_markdown(packet), encoding="utf-8")
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "packet": _relpath(yaml_path),
            "pm_review": _relpath(md_path),
        },
        "summary": {
            "species_name": species_name,
            "recommended_decision": decision,
            "primary_source_count": record.get("primary_source_count"),
            "max_core_moves_in_one_source": stats["max_core_moves_in_one_source"],
            "source_count_with_3plus_core": stats["source_count_with_3plus_core"],
            "source_count_with_full_core": stats["source_count_with_full_core"],
        },
    }


def _join(items: list[Any], empty: str = "无") -> str:
    values = [str(item) for item in items if str(item)]
    return " / ".join(values) if values else empty


def render_markdown(packet: dict[str, Any]) -> str:
    candidate = packet["candidate"]
    evidence = packet["evidence_shape"]
    recommendation = packet["recommendation"]
    lines = [
        f"# P14 PM Review Packet: {candidate['species_name']}",
        "",
        "## 你需要判断",
        f"- 是否接受 `{candidate['species_name']}` 作为 species-level set 候选。",
        f"- 我的建议：`{recommendation['recommended_decision']}`。",
        f"- runtime_allowed：`{str(packet['runtime_allowed']).lower()}`；这不是 runtime promotion。",
        "",
        "## 候选摘要",
        f"- 物种：{candidate['species_name']}",
        f"- 稳定技能：{_join(candidate.get('stable_moves') or [])}",
        f"- 主证来源数：{candidate.get('primary_source_count')}；总来源数：{candidate.get('source_count')}",
        f"- 角色信号：{_join(candidate.get('top_roles') or [])}",
        f"- promotion blockers：{_join(candidate.get('promotion_blockers') or [])}",
        "",
        "## 证据形状",
        f"- 同一来源最多同时支持 {evidence.get('max_core_moves_in_one_source')} 个稳定技能。",
        f"- 完整核心同源数：{evidence.get('source_count_with_full_core')}。",
        f"- 3+ 核心同源数：{evidence.get('source_count_with_3plus_core')}。",
        f"- 2+ 核心同源数：{evidence.get('source_count_with_2plus_core')}。",
        f"- 单技能来源数：{evidence.get('source_count_with_single_core')}。",
        "",
        "## 我的判断",
    ]
    for reason in recommendation.get("reasons") or []:
        lines.append(f"- {reason}")
    lines.extend(["", "## 技能支持"])
    for row in evidence.get("move_support") or []:
        source_ids = row.get("source_ids") or []
        sample = ", ".join(source_ids[:4])
        extra = f" 等 {len(source_ids)} 条" if len(source_ids) > 4 else ""
        lines.append(
            f"- {row.get('move_name')}：主证 {row.get('primary_source_count')}；来源 {sample}{extra}"
        )
    lines.extend(["", "## 同源证据 Top"])
    for row in (evidence.get("supporting_variants") or [])[:12]:
        title = row.get("title") or row.get("source_id")
        moves = _join(row.get("moves") or [])
        overlap = _join(row.get("core_overlap_moves") or [])
        lines.append(
            f"- {row.get('source_id')}：{title}；同源核心 {row.get('core_overlap_count')} 个（{overlap}）；记录技能 {moves}；source_type={row.get('source_type')}"
        )
    lines.extend(["", "## PM 选项", "- `accept_as_candidate_only`：只接受为候选，不进 runtime。", "- `defer_until_more_same-core_evidence`：继续补同源核心证据。", "- `reject_as_false_cluster`：认为这是跨源误聚类，后续加入 quarantine/规则。"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a P14 PM promotion review packet.")
    parser.add_argument("--species-name", required=True)
    parser.add_argument("--consolidation-path", type=Path)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    consolidation_path = args.consolidation_path or _latest_consolidation_path(args.out_root / "set_inventory_consolidation")
    if not consolidation_path:
        raise SystemExit("No consolidation YAML found")
    result = build_species_review_packet(
        consolidation_path=consolidation_path,
        species_name=args.species_name,
        source_queue_path=args.source_queue,
        batch_id=args.batch_id,
        out_root=args.out_root,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["paths"]["pm_review"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
