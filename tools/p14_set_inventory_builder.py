#!/usr/bin/env python3
"""Build source-level P14 Set Inventory dossiers from evidence foundations.

Inventory is volume-first candidate substrate. It aggregates evidence by
species/source into L1a coverage records and L1b/L2/L3 set dossiers. It never
promotes runtime graph data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import (
    DEFAULT_OUT_ROOT,
    DEFAULT_SOURCE_QUEUE,
    NoAliasDumper,
    REPO_ROOT,
    Segment,
    SourceBundle,
    _abilities,
    _cosmetic_descriptors_from_text,
    _labels_from_text,
    _mechanisms,
    _moves,
    _ms_to_stamp,
    _relpath,
    _render_cosmetic_descriptors,
    _source_aliases_used,
    _source_archetypes,
    _species,
    _unique,
    _window,
    load_ingested_sources,
    ROLE_KEYWORDS,
)


DEFAULT_BATCH_ID = f"phase1_set_inventory_{date.today().isoformat()}"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
CONFIG_KEYWORDS = {
    "性格": "nature",
    "个体": "individual_values",
    "血脉": "bloodline",
}
PARTNER_KEYWORDS = {
    "队友": "partner_claim",
    "搭配": "partner_claim",
    "配合": "combo_claim",
    "组合": "combo_claim",
    "联防": "combo_claim",
}
MATCHUP_KEYWORDS = {
    "克制": "counterplay_claim",
    "针对": "counterplay_claim",
    "防范": "counterplay_claim",
    "压制": "matchup_claim",
    "怕": "matchup_claim",
    "打不过": "matchup_claim",
}
ACQUISITION_CONTEXT_TERMS = (
    "解锁图鉴",
    "图鉴获得",
    "技能石获取",
    "获取技能石",
    "获得技能石",
    "抓取",
    "捕捉",
    "捕捉地点",
    "抓到",
)


def load_species_move_pools(db_path: Path = DEFAULT_BATTLE_DEX) -> dict[str, set[str]]:
    """Load A-layer legal move pools keyed by canonical species display name."""
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    try:
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
    pools: dict[str, set[str]] = {}
    for species_name, move_name in rows:
        pools.setdefault(str(species_name), set()).add(str(move_name))
    return pools


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _evidence_ref(segments: list[Segment], quote: str) -> dict[str, Any]:
    return {
        "segment_ids": [item.segment_id for item in segments],
        "start_ms": segments[0].start_ms,
        "end_ms": segments[-1].end_ms,
        "time": _ms_to_stamp(segments[0].start_ms),
        "quality_gates": sorted({item.quality_gate for item in segments}),
        "quote": quote[:280],
    }


def _attribution_segments(
    segments: list[Segment],
    index: int,
    species: str,
    source_meta: dict[str, Any],
    *,
    lookahead: int = 2,
) -> list[Segment]:
    selected: list[Segment] = []
    if index > 0 and species in _species(segments[index - 1], source_meta):
        selected.append(segments[index - 1])
    selected.append(segments[index])
    for next_index in range(index + 1, min(len(segments), index + lookahead + 1)):
        next_species = _species(segments[next_index], source_meta)
        if next_species and species not in next_species:
            break
        selected.append(segments[next_index])
    return selected


def _move_completeness(move_count: int, max_same_evidence_move_count: int) -> str:
    if move_count >= 4:
        if max_same_evidence_move_count >= 4:
            return "complete_4_moves"
        return "move_pool_4plus_unclustered"
    if move_count >= 2:
        return "partial_2_3_moves"
    if move_count == 1:
        return "single_move_signal"
    return "insufficient_moves"


def _is_overlapped_short_move(move: str, moves: list[str], text: str) -> bool:
    longer_hits = [candidate for candidate in moves if candidate != move and move in candidate]
    if not longer_hits:
        return False
    nested_count = sum(text.count(candidate) for candidate in longer_hits)
    return text.count(move) <= nested_count


def _filter_moves_for_species(
    *,
    species: str,
    moves: list[str],
    text: str,
    evidence: dict[str, Any],
    species_move_pools: dict[str, set[str]] | None,
) -> tuple[list[str], list[dict[str, Any]]]:
    if not moves:
        return [], []
    legal_pool = species_move_pools.get(species) if species_move_pools is not None else None
    filtered: list[str] = []
    excluded: list[dict[str, Any]] = []
    for move in moves:
        reason = ""
        if _is_overlapped_short_move(move, moves, text):
            reason = "overlap_inside_longer_move"
        elif species_move_pools is not None and legal_pool is None:
            reason = "species_move_pool_missing"
        elif legal_pool is not None and move not in legal_pool:
            reason = "not_in_species_move_pool"

        if reason:
            excluded.append({"move_name": move, "reason": reason, "evidence": evidence})
        else:
            filtered.append(move)
    return _unique(filtered), excluded


def _is_acquisition_or_unlock_context(text: str) -> bool:
    return any(term in text for term in ACQUISITION_CONTEXT_TERMS)


def _profile_source(bundle: SourceBundle) -> dict[str, Any]:
    source = bundle.manifest.get("source") or {}
    artifacts = bundle.source_meta.get("ingest_artifacts") or {}
    target_archetype = bundle.source_meta.get("target_archetype")
    descriptor_context = " ".join(
        [
            str(source.get("title") or bundle.source_meta.get("title") or ""),
            str(target_archetype or ""),
            " ".join(str(value) for value in bundle.source_meta.get("target_entities") or []),
        ]
    )
    source_descriptors = _cosmetic_descriptors_from_text(descriptor_context)
    profile = {
        "title": source.get("title") or bundle.source_meta.get("title"),
        "url": source.get("url") or bundle.source_meta.get("url"),
        "source_type": source.get("source_type") or bundle.source_meta.get("source_type"),
        "target_archetype": target_archetype,
        "target_entities": bundle.source_meta.get("target_entities") or [],
        "low_confidence_use": artifacts.get("low_confidence_use"),
    }
    if source_descriptors:
        profile["source_descriptors"] = _render_cosmetic_descriptors(source_descriptors)
        profile["target_archetype_normalization"] = {
            "raw": target_archetype,
            "usable_as_archetype": False,
            "reason": "contains_cosmetic_descriptor_without_source_mechanic_binding",
        }
    return profile


def _ensure_profile(profiles: dict[str, dict[str, Any]], species: str, bundle: SourceBundle) -> dict[str, Any]:
    return profiles.setdefault(
        species,
        {
            "species_name": species,
            "source_aliases_used": [],
            "archetype_tags": _source_archetypes(bundle),
            "mention_count": 0,
            "move_counter": Counter(),
            "ability_counter": Counter(),
            "mechanism_counter": Counter(),
            "role_counter": Counter(),
            "cosmetic_descriptor_counter": Counter(),
            "cosmetic_descriptor_refs": [],
            "move_signal_windows": [],
            "excluded_move_counter": Counter(),
            "excluded_move_mentions": [],
            "acquisition_context_refs": [],
            "configuration_signals": {
                "nature": [],
                "individual_values": [],
                "bloodline": [],
            },
            "partner_claims": [],
            "combo_notes": [],
            "matchup_claims": [],
            "counterplay_claims": [],
            "evidence_refs": [],
        },
    )


def _add_l3_claims(profile: dict[str, Any], window_text: str, evidence: dict[str, Any]) -> None:
    for phrase, kind in PARTNER_KEYWORDS.items():
        if phrase not in window_text:
            continue
        target = "partner_claims" if kind == "partner_claim" else "combo_notes"
        if len(profile[target]) < 6:
            profile[target].append({"source_phrase": phrase, "evidence": evidence})
    for phrase, kind in MATCHUP_KEYWORDS.items():
        if phrase not in window_text:
            continue
        target = "counterplay_claims" if kind == "counterplay_claim" else "matchup_claims"
        if len(profile[target]) < 6:
            profile[target].append({"source_phrase": phrase, "evidence": evidence})


def _add_config_signals(profile: dict[str, Any], window_text: str, evidence: dict[str, Any]) -> None:
    for phrase, key in CONFIG_KEYWORDS.items():
        if phrase in window_text and len(profile["configuration_signals"][key]) < 6:
            profile["configuration_signals"][key].append({"source_phrase": phrase, "evidence": evidence})


def build_inventory_for_source(
    bundle: SourceBundle,
    *,
    species_move_pools: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    profiles: dict[str, dict[str, Any]] = {}
    for index, segment in enumerate(bundle.segments):
        species_terms = _species(segment, bundle.source_meta)
        if not species_terms:
            continue
        for species in species_terms:
            attribution = _attribution_segments(bundle.segments, index, species, bundle.source_meta)
            attribution_text = " ".join(item.text for item in attribution)
            evidence = _evidence_ref(attribution, attribution_text)
            acquisition_context = _is_acquisition_or_unlock_context(attribution_text)
            raw_moves = [] if acquisition_context else _unique([move for item in attribution for move in _moves(item)])
            moves, excluded_moves = _filter_moves_for_species(
                species=species,
                moves=raw_moves,
                text=attribution_text,
                evidence=evidence,
                species_move_pools=species_move_pools,
            )
            abilities = [] if acquisition_context else _unique([ability for item in attribution for ability in _abilities(item)])
            mechanisms = [] if acquisition_context else _unique([mechanism for item in attribution for mechanism in _mechanisms(item)])
            roles = [] if acquisition_context else [role["label"] for role in _labels_from_text(attribution_text, ROLE_KEYWORDS)]
            cosmetic_descriptor_terms = _cosmetic_descriptors_from_text(attribution_text)
            profile = _ensure_profile(profiles, species, bundle)
            profile["mention_count"] += 1
            profile["source_aliases_used"] = _unique(
                [*profile["source_aliases_used"], *_source_aliases_used(attribution_text, bundle.source_meta, species)]
            )
            if acquisition_context and len(profile["acquisition_context_refs"]) < 8:
                profile["acquisition_context_refs"].append(evidence)
            profile["move_counter"].update(moves)
            profile["excluded_move_counter"].update(item["move_name"] for item in excluded_moves)
            for item in excluded_moves:
                if len(profile["excluded_move_mentions"]) >= 16:
                    break
                profile["excluded_move_mentions"].append(item)
            if moves and len(profile["move_signal_windows"]) < 12:
                profile["move_signal_windows"].append(
                    {
                        "moves": moves,
                        "evidence": evidence,
                    }
                )
            profile["ability_counter"].update(abilities)
            profile["mechanism_counter"].update(mechanisms)
            profile["role_counter"].update(roles)
            profile["cosmetic_descriptor_counter"].update(cosmetic_descriptor_terms)
            if cosmetic_descriptor_terms and len(profile["cosmetic_descriptor_refs"]) < 6:
                profile["cosmetic_descriptor_refs"].append(
                    {
                        "descriptors": _render_cosmetic_descriptors(cosmetic_descriptor_terms),
                        "evidence": evidence,
                    }
                )
            if len(profile["evidence_refs"]) < 8:
                profile["evidence_refs"].append(evidence)
            if not acquisition_context:
                _add_config_signals(profile, attribution_text, evidence)
                _add_l3_claims(profile, attribution_text, evidence)

    coverage_records: list[dict[str, Any]] = []
    set_dossiers: list[dict[str, Any]] = []
    for species, profile in sorted(profiles.items()):
        known_moves = [move for move, _ in profile["move_counter"].most_common(4)]
        move_count = len(known_moves)
        max_same_evidence_move_count = max((len(item["moves"]) for item in profile["move_signal_windows"]), default=0)
        completeness = _move_completeness(move_count, max_same_evidence_move_count)
        base = {
            "species_name": species,
            "source_aliases_used": profile["source_aliases_used"],
            "archetype_tags": profile["archetype_tags"],
            "cosmetic_descriptors": _render_cosmetic_descriptors(
                [item for item, _ in profile["cosmetic_descriptor_counter"].most_common()]
            ),
            "cosmetic_descriptor_refs": profile["cosmetic_descriptor_refs"][:4],
            "mention_count": profile["mention_count"],
            "evidence_refs": profile["evidence_refs"],
            "legality_filter": {
                "source": "A_layer_species_move_pool",
                "excluded_move_counts": dict(profile["excluded_move_counter"].most_common(8)),
                "excluded_move_mentions": profile["excluded_move_mentions"][:8],
                "acquisition_context_ref_count": len(profile["acquisition_context_refs"]),
                "acquisition_context_refs": profile["acquisition_context_refs"][:4],
            },
            "runtime_allowed": False,
        }
        if move_count == 0:
            coverage_records.append(
                {
                    **base,
                    "inventory_level": "L1a_coverage_record",
                    "status": "coverage_only",
                }
            )
            continue

        dossier = {
            **base,
            "inventory_level": "L1b_set_skeleton",
            "status": "l1b_set_skeleton",
            "move_slots": {
                "known_moves": known_moves,
                "known_move_count": move_count,
                "missing_move_slots": max(0, 4 - move_count),
                "max_same_evidence_move_count": max_same_evidence_move_count,
                "completeness": completeness,
                "same_build_confidence": "medium" if completeness == "complete_4_moves" else "low",
                "move_evidence_counts": dict(profile["move_counter"].most_common(8)),
                "move_signal_windows": profile["move_signal_windows"][:6],
            },
            "configuration": {
                "nature": profile["configuration_signals"]["nature"],
                "individual_values": profile["configuration_signals"]["individual_values"],
                "bloodline": profile["configuration_signals"]["bloodline"],
                "ability_mentions": [item for item, _ in profile["ability_counter"].most_common(8)],
                "mechanism_mentions": [item for item, _ in profile["mechanism_counter"].most_common(8)],
            },
            "tactical_context": {
                "roles": [item for item, _ in profile["role_counter"].most_common(6)],
                "common_partners": profile["partner_claims"],
                "combo_notes": profile["combo_notes"],
                "matchup_claims": profile["matchup_claims"],
                "counterplay_claims": profile["counterplay_claims"],
            },
            "promotion_blockers": [
                "source_inventory_not_reviewed",
                "cross_source_consolidation_required",
            ],
            "runtime_allowed": False,
        }
        if completeness != "complete_4_moves":
            if completeness == "move_pool_4plus_unclustered":
                dossier["promotion_blockers"].append("same_build_unverified")
            else:
                dossier["promotion_blockers"].append("incomplete_move_slots")
        if profile["cosmetic_descriptor_counter"]:
            dossier["promotion_blockers"].append("cosmetic_descriptor_not_set_axis")
        set_dossiers.append(dossier)

    completeness_counts = Counter(dossier["move_slots"]["completeness"] for dossier in set_dossiers)
    return {
        "schema_version": "p14.set_inventory.v0",
        "source_id": bundle.source_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source": _profile_source(bundle),
        "coverage_records": coverage_records,
        "set_dossiers": set_dossiers,
        "summary": {
            "coverage_record_count": len(coverage_records),
            "set_dossier_count": len(set_dossiers),
            "complete_4_moves_count": completeness_counts.get("complete_4_moves", 0),
            "move_pool_4plus_unclustered_count": completeness_counts.get("move_pool_4plus_unclustered", 0),
            "partial_2_3_moves_count": completeness_counts.get("partial_2_3_moves", 0),
            "single_move_signal_count": completeness_counts.get("single_move_signal", 0),
        },
    }


def _dossier_summaries(inventories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for inventory in inventories:
        for dossier in inventory.get("set_dossiers") or []:
            rows.append(
                {
                    "source_id": inventory["source_id"],
                    "species_name": dossier["species_name"],
                    "moves": dossier["move_slots"]["known_moves"],
                    "completeness": dossier["move_slots"]["completeness"],
                    "roles": dossier["tactical_context"]["roles"],
                    "mention_count": dossier["mention_count"],
                    "low_confidence_use": (inventory.get("source") or {}).get("low_confidence_use"),
                }
            )
    return sorted(
        rows,
        key=lambda item: (
            item["completeness"] != "complete_4_moves",
            item["completeness"] != "move_pool_4plus_unclustered",
            item["completeness"] != "partial_2_3_moves",
            -len(item["moves"]),
            item["species_name"],
        ),
    )


def _excluded_move_counts(inventories: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for inventory in inventories:
        records = [
            *(inventory.get("coverage_records") or []),
            *(inventory.get("set_dossiers") or []),
        ]
        for record in records:
            legality_filter = record.get("legality_filter") or {}
            counts.update(legality_filter.get("excluded_move_counts") or {})
    return counts


def render_pm_inventory_brief(batch_id: str, inventories: list[dict[str, Any]]) -> str:
    summaries = _dossier_summaries(inventories)
    excluded_counts = _excluded_move_counts(inventories)
    total_coverage = sum((item.get("summary") or {}).get("coverage_record_count", 0) for item in inventories)
    total_dossiers = sum((item.get("summary") or {}).get("set_dossier_count", 0) for item in inventories)
    total_partial = sum((item.get("summary") or {}).get("partial_2_3_moves_count", 0) for item in inventories)
    total_unclustered = sum((item.get("summary") or {}).get("move_pool_4plus_unclustered_count", 0) for item in inventories)
    total_single = sum((item.get("summary") or {}).get("single_move_signal_count", 0) for item in inventories)
    lines = [
        f"# Phase 1 Set Inventory Brief: {batch_id}",
        "",
        "## 结论",
        "- 主线已改成 Set Inventory：先铺 L1a/L1b 量，再做 consolidation/review。",
        "- 本轮输出是 source-level dossier，不是 runtime graph card。",
        "- 技能池已过 A 层物种技能合法性过滤；非法近邻技能只留在 audit，不进入 known_moves。",
        "- 可以用于小批量 autorun 的候选层试跑；不能 promotion。",
        "",
        "## 规模",
        f"- 来源：{len(inventories)} 条。",
        f"- L1a coverage records：{total_coverage} 个。",
        f"- L1b set dossiers：{total_dossiers} 个，其中同证据完整四技能 {sum((item.get('summary') or {}).get('complete_4_moves_count', 0) for item in inventories)} 个，4+ 技能池但未证明同一 build {total_unclustered} 个，2-3 技能 partial set {total_partial} 个，单技能信号 {total_single} 个。",
        f"- 被过滤的非法/重叠技能提及：{sum(excluded_counts.values())} 次；Top：{', '.join(f'{move} {count}' for move, count in excluded_counts.most_common(5)) or '无'}。",
        "",
        "## 候选 set dossier 样例",
    ]
    if summaries:
        for item in summaries[:10]:
            moves = " / ".join(item["moves"]) or "未抽到"
            roles = "、".join(item["roles"]) or "待定"
            caution = "；低置信补证" if item.get("low_confidence_use") else ""
            lines.append(
                f"- {item['species_name']} ({item['source_id']})：{moves}；{item['completeness']}；角色 {roles}；提及 {item['mention_count']} 次{caution}。"
            )
    else:
        lines.append("- 暂无。")
    lines.extend(
        [
            "",
            "## 下一步",
            "做 cross-source consolidation：按物种和技能组近似合并 dossier，找重复出现的 L1b set skeleton。4+ move pool 需要聚类确认同一 build，不能直接当标准 set；同物种多流派要分簇，不能硬合并。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_batch_audit(batch_id: str, inventories: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = _dossier_summaries(inventories)
    by_species = Counter(item["species_name"] for item in summaries)
    excluded_counts = _excluded_move_counts(inventories)
    return {
        "schema_version": "p14.set_inventory_batch_audit.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "summary": {
            "source_count": len(inventories),
            "coverage_record_count": sum((item.get("summary") or {}).get("coverage_record_count", 0) for item in inventories),
            "set_dossier_count": len(summaries),
            "complete_4_moves_count": sum(1 for item in summaries if item["completeness"] == "complete_4_moves"),
            "move_pool_4plus_unclustered_count": sum(1 for item in summaries if item["completeness"] == "move_pool_4plus_unclustered"),
            "partial_2_3_moves_count": sum(1 for item in summaries if item["completeness"] == "partial_2_3_moves"),
            "single_move_signal_count": sum(1 for item in summaries if item["completeness"] == "single_move_signal"),
            "excluded_move_mention_count": sum(excluded_counts.values()),
            "top_excluded_move_counts": dict(excluded_counts.most_common(20)),
            "species_with_multiple_source_or_dossier_signals": {
                species: count for species, count in sorted(by_species.items()) if count > 1
            },
        },
        "top_dossiers": summaries[:30],
    }


def run_set_inventory_builder(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    source_ids: set[str] | None = None,
    db_path: Path = DEFAULT_BATTLE_DEX,
) -> dict[str, Any]:
    bundles = load_ingested_sources(source_queue, source_ids=source_ids)
    species_move_pools = load_species_move_pools(db_path)
    inventories = [
        build_inventory_for_source(bundle, species_move_pools=species_move_pools)
        for bundle in bundles
    ]
    for inventory in inventories:
        _write_yaml(out_root / "set_inventory" / f"{inventory['source_id']}.source_inventory.yaml", inventory)
    audit = build_batch_audit(batch_id, inventories)
    audit_path = out_root / "audits" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    _write_yaml(audit_path, audit)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_pm_inventory_brief(batch_id, inventories), encoding="utf-8")
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_count": len(inventories),
        "paths": {
            "audit": _relpath(audit_path),
            "pm_brief": _relpath(packet_path),
            "set_inventory_dir": _relpath(out_root / "set_inventory"),
        },
        "summary": audit["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_set_inventory_builder(
        source_queue=args.source_queue,
        out_root=args.out_root,
        batch_id=args.batch_id,
        source_ids=set(args.source_id) if args.source_id else None,
        db_path=args.db_path,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"set inventory: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
