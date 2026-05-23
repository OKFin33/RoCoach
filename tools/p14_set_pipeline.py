#!/usr/bin/env python3
"""Run the P14 set-centric incremental pipeline on evidence foundations.

The output is candidate substrate only. It never promotes runtime graph data.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_BATCH_ID = f"phase1_set_centric_delta_{date.today().isoformat()}"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"

ROLE_KEYWORDS = {
    "首发": "lead",
    "起手": "lead",
    "切上": "pivot_in",
    "切出": "pivot_in",
    "联防": "defensive_pivot",
    "压制": "pressure",
    "平推": "cleaner",
    "推队": "cleaner",
    "收割": "cleaner",
    "强化": "setup",
    "传": "support_transfer",
    "保住": "preserve_resource",
}

ARCHETYPE_KEYWORDS = {
    "毒队": "poison",
    "水毒": "water_poison",
    "星陨": "starfall",
    "帕尔": "parr_starfall",
    "翼王": "wingking",
    "沙暴": "sandstorm",
    "格斗": "fighting",
    "光合": "photosynthesis",
}

SPECIES_ALIAS_HINTS = {
    "翼王": "圣羽翼王",
    "水刃翼王": "圣羽翼王",
}

EDGE_KEYWORDS = {
    "压制": "pressure",
    "克制": "counterplay",
    "针对": "counterplay",
    "防范": "counterplay",
    "抓": "counterplay",
    "秒杀": "threat",
    "打掉": "threat",
    "吃掉": "defensive_answer",
    "联防": "defensive_cover",
    "配合": "synergy",
    "传": "synergy",
}

MECHANISM_HINTS = {
    "星陨": "mechanism/starfall_mark/2026-s1",
    "星陨印记": "mechanism/starfall_mark/2026-s1",
    "印记": "mechanism/mark_unspecified/2026-s1",
    "灼烧": "mechanism/burn_status/2026-s1",
    "烧伤": "mechanism/burn_status/2026-s1",
    "能量": "mechanism/energy_window/2026-s1",
    "能耗": "mechanism/energy_cost/2026-s1",
    "沙暴": "mechanism/sandstorm/2026-s1",
    "天气": "mechanism/weather/2026-s1",
}

COSMETIC_DESCRIPTOR_POLICIES = {
    "黑白": {
        "meaning": "黑白色炫彩/外观描述",
        "not_an_archetype": True,
        "extraction_policy": "cosmetic_descriptor_only_without_source_mechanic_binding",
    }
}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


@dataclass(frozen=True)
class Segment:
    segment_id: str
    text: str
    start_ms: int | None
    end_ms: int | None
    quality_gate: str
    ab_hits: list[dict[str, Any]]


@dataclass(frozen=True)
class SourceBundle:
    source_id: str
    source_meta: dict[str, Any]
    foundation_dir: Path
    manifest: dict[str, Any]
    quality_gate: dict[str, Any]
    segments: list[Segment]


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def load_species_move_pools(db_path: Path = DEFAULT_BATTLE_DEX) -> dict[str, set[str]]:
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


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _ms_to_stamp(ms: Any) -> str:
    if ms is None:
        return "?:??"
    total = int(ms) // 1000
    minutes, seconds = divmod(total, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.UNICODE)
    return cleaned.strip("_") or "unknown"


def _hit_terms(segment: Segment, kinds: set[str]) -> list[str]:
    terms: list[str] = []
    for hit in segment.ab_hits:
        kind = str(hit.get("kind") or "")
        if kind in kinds and hit.get("term"):
            terms.append(str(hit["term"]))
    return _unique(terms)


def _source_context(source_meta: dict[str, Any]) -> str:
    return " ".join(
        [
            str(source_meta.get("title") or ""),
            str(source_meta.get("target_archetype") or ""),
            " ".join(str(value) for value in source_meta.get("target_entities") or []),
        ]
    )


def _source_alias_species(text: str, source_meta: dict[str, Any]) -> list[str]:
    context = _source_context(source_meta)
    species: list[str] = []
    for alias, canonical in SPECIES_ALIAS_HINTS.items():
        if alias in text and (alias in context or canonical in context):
            species.append(canonical)
    return _unique(species)


def _source_aliases_used(text: str, source_meta: dict[str, Any], species_name: str) -> list[str]:
    context = _source_context(source_meta)
    return [
        alias
        for alias, canonical in SPECIES_ALIAS_HINTS.items()
        if canonical == species_name and alias in text and (alias in context or canonical in context)
    ]


def _species(segment: Segment, source_meta: dict[str, Any] | None = None) -> list[str]:
    source_meta = source_meta or {}
    return _unique([*_hit_terms(segment, {"species", "species_initial"}), *_source_alias_species(segment.text, source_meta)])


def _moves(segment: Segment) -> list[str]:
    return _hit_terms(segment, {"move"})


def _abilities(segment: Segment) -> list[str]:
    return _hit_terms(segment, {"ability"})


def _mechanisms(segment: Segment) -> list[str]:
    return _hit_terms(segment, {"mechanism", "mechanism_heading"})


def _labels_from_text(text: str, mapping: dict[str, str]) -> list[dict[str, str]]:
    labels: list[dict[str, str]] = []
    seen: set[str] = set()
    for phrase, label in mapping.items():
        if phrase in text and label not in seen:
            labels.append({"label": label, "source_phrase": phrase})
            seen.add(label)
    return labels


def _cosmetic_descriptors_from_text(text: str) -> list[str]:
    return [term for term in COSMETIC_DESCRIPTOR_POLICIES if term in text]


def _render_cosmetic_descriptors(terms: list[str]) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for term in _unique(terms):
        policy = COSMETIC_DESCRIPTOR_POLICIES.get(term)
        if not policy:
            continue
        descriptors.append({"term": term, **policy})
    return descriptors


def _mechanism_refs(text: str, mechanisms: list[str]) -> list[str]:
    refs: list[str] = []
    haystack = text + " " + " ".join(mechanisms)
    for phrase, ref in MECHANISM_HINTS.items():
        if phrase in haystack:
            refs.append(ref)
    return _unique(refs)


def _is_overlapped_short_move(move: str, moves: list[str], text: str) -> bool:
    longer_hits = [candidate for candidate in moves if candidate != move and move in candidate]
    if not longer_hits:
        return False
    nested_count = sum(text.count(candidate) for candidate in longer_hits)
    return text.count(move) <= nested_count


def _filter_moves_for_species(
    species: str,
    moves: list[str],
    text: str,
    species_move_pools: dict[str, set[str]] | None,
) -> tuple[list[str], list[dict[str, str]]]:
    if not moves:
        return [], []
    legal_pool = species_move_pools.get(species) if species_move_pools is not None else None
    selected: list[str] = []
    excluded: list[dict[str, str]] = []
    for move in moves:
        reason = ""
        if _is_overlapped_short_move(move, moves, text):
            reason = "overlap_inside_longer_move"
        elif species_move_pools is not None and legal_pool is None:
            reason = "species_move_pool_missing"
        elif legal_pool is not None and move not in legal_pool:
            reason = "not_in_species_move_pool"

        if reason:
            excluded.append({"move_name": move, "reason": reason})
        else:
            selected.append(move)
    return _unique(selected), excluded


def load_ingested_sources(
    queue_path: Path = DEFAULT_SOURCE_QUEUE,
    *,
    source_ids: set[str] | None = None,
) -> list[SourceBundle]:
    queue = _load_yaml(queue_path)
    bundles: list[SourceBundle] = []
    for source in queue.get("sources") or []:
        source_id = str(source.get("source_id") or "")
        if source_ids and source_id not in source_ids:
            continue
        artifacts = source.get("ingest_artifacts") or {}
        foundation_dir = _repo_path(artifacts.get("evidence_foundation_dir"))
        if not foundation_dir or not foundation_dir.exists():
            continue
        manifest = _load_yaml(foundation_dir / "source_manifest_v2.yaml")
        quality = _load_yaml(foundation_dir / "quality_gate.yaml")
        segment_payload = _load_yaml(foundation_dir / "segments.yaml")
        segments = [
            Segment(
                segment_id=str(item.get("segment_id") or ""),
                text=_compact(str(item.get("refined_text") or item.get("raw_text") or "")),
                start_ms=item.get("start_ms"),
                end_ms=item.get("end_ms"),
                quality_gate=str(item.get("quality_gate") or "unknown"),
                ab_hits=list(item.get("ab_hits") or []),
            )
            for item in segment_payload.get("segments") or []
            if item.get("segment_id") and (item.get("refined_text") or item.get("raw_text"))
        ]
        bundles.append(
            SourceBundle(
                source_id=source_id,
                source_meta=source,
                foundation_dir=foundation_dir,
                manifest=manifest,
                quality_gate=quality,
                segments=segments,
            )
        )
    return bundles


def _window(segments: list[Segment], index: int, *, radius: int = 2) -> list[Segment]:
    start = max(0, index - radius)
    end = min(len(segments), index + radius + 1)
    return segments[start:end]


def _source_archetypes(bundle: SourceBundle) -> list[str]:
    values: list[str] = []
    for raw in [
        str(bundle.source_meta.get("target_archetype") or ""),
        " ".join(str(value) for value in bundle.source_meta.get("target_entities") or []),
        str((bundle.manifest.get("source") or {}).get("title") or ""),
    ]:
        values.extend(label["label"] for label in _labels_from_text(raw, ARCHETYPE_KEYWORDS))
    return _unique(values)


def build_set_candidates(
    bundle: SourceBundle,
    *,
    species_move_pools: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    source_archetypes = _source_archetypes(bundle)
    for index, segment in enumerate(bundle.segments):
        species_terms = _species(segment, bundle.source_meta)
        if not species_terms:
            continue
        window_segments = _window(bundle.segments, index, radius=1)
        window_text = " ".join(item.text for item in window_segments)
        moves = _unique([move for item in window_segments for move in _moves(item)])
        abilities = _unique([ability for item in window_segments for ability in _abilities(item)])
        mechanisms = _unique([mechanism for item in window_segments for mechanism in _mechanisms(item)])
        roles = _labels_from_text(window_text, ROLE_KEYWORDS)
        archetypes = _unique([*source_archetypes, *[label["label"] for label in _labels_from_text(window_text, ARCHETYPE_KEYWORDS)]])
        refs = _mechanism_refs(window_text, mechanisms)
        cosmetic_descriptor_terms = _cosmetic_descriptors_from_text(window_text)

        for species in species_terms:
            selected_moves, excluded_moves = _filter_moves_for_species(
                species,
                moves,
                window_text,
                species_move_pools,
            )
            candidate = {
                "candidate_id": f"cand/{bundle.source_id}/set/{_slug(species)}/{segment.segment_id}",
                "candidate_type": "species_set_window_candidate",
                "source_id": bundle.source_id,
                "species_name": species,
                "source_aliases_used": _source_aliases_used(window_text, bundle.source_meta, species),
                "state": "S2_set_candidate" if selected_moves else "S1_partial_set",
                "archetype_tags": archetypes,
                "cosmetic_descriptors": _render_cosmetic_descriptors(cosmetic_descriptor_terms),
                "inferred_roles": _unique([role["label"] for role in roles]),
                "selected_moves": selected_moves,
                "excluded_moves": excluded_moves,
                "mentioned_abilities": abilities,
                "mechanism_refs_needed": refs,
                "evidence_windows": [
                    {
                        "segment_ids": [item.segment_id for item in window_segments],
                        "center_segment_id": segment.segment_id,
                        "start_ms": window_segments[0].start_ms,
                        "end_ms": window_segments[-1].end_ms,
                        "quality_gates": sorted({item.quality_gate for item in window_segments}),
                        "quote": window_text[:260],
                        "extraction_note": "windowed_from_adjacent_subtitle_segments",
                    }
                ],
                "promotion_blockers": ["pm_review_required", "single_evidence_window"],
                "runtime_allowed": False,
            }
            blockers = set(candidate["promotion_blockers"])
            if cosmetic_descriptor_terms:
                blockers.add("cosmetic_descriptor_not_set_axis")
            if candidate["state"] != "S2_set_candidate":
                blockers.add("selected_moves_missing")
            if not candidate["inferred_roles"]:
                blockers.add("role_needs_review")
            if candidate["mechanism_refs_needed"]:
                blockers.add("mechanism_rule_not_reviewed")
            if len(candidate["selected_moves"]) > 4:
                blockers.add("window_too_broad")
            candidate["promotion_blockers"] = sorted(blockers)
            candidates.append(candidate)

    for candidate in candidates:
        blockers = set(candidate["promotion_blockers"])
        if candidate["state"] != "S2_set_candidate":
            blockers.add("selected_moves_missing")
        if not candidate.get("inferred_roles"):
            blockers.add("role_needs_review")
        if candidate.get("mechanism_refs_needed"):
            blockers.add("mechanism_rule_not_reviewed")
        candidate["promotion_blockers"] = sorted(blockers)

    candidates = sorted(
        candidates,
        key=lambda item: (
            item["state"] != "S2_set_candidate",
            item["species_name"],
            (item["evidence_windows"] or [{}])[0].get("center_segment_id", ""),
        ),
    )
    return {
        "schema_version": "p14.set_candidates.v0",
        "source_id": bundle.source_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "candidate_sets": candidates,
        "summary": {
            "candidate_count": len(candidates),
            "s2_count": sum(1 for item in candidates if item["state"] == "S2_set_candidate"),
            "species_count": len({item["species_name"] for item in candidates}),
        },
    }


def build_relation_candidates(bundle: SourceBundle) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for index, segment in enumerate(bundle.segments):
        window_segments = _window(bundle.segments, index)
        window_text = " ".join(item.text for item in window_segments)
        edge_hits = _labels_from_text(window_text, EDGE_KEYWORDS)
        species_terms = _unique([species for item in window_segments for species in _species(item, bundle.source_meta)])
        if len(species_terms) < 2 or not edge_hits:
            continue
        source = species_terms[0]
        targets = species_terms[1:4]
        edge_type = edge_hits[0]["label"]
        key = (source, ",".join(targets), edge_type)
        if key in seen:
            continue
        seen.add(key)
        mechanisms = _unique([mechanism for item in window_segments for mechanism in _mechanisms(item)])
        refs = _mechanism_refs(window_text, mechanisms)
        blockers = ["pm_review_required", "source_phrase_only"]
        if refs:
            blockers.append("mechanism_rule_not_reviewed")
        edges.append(
            {
                "candidate_id": f"cand/{bundle.source_id}/edge/{len(edges) + 1:03d}",
                "candidate_type": "relation_candidate",
                "source_id": bundle.source_id,
                "source_species_or_set": source,
                "target_species_or_sets": targets,
                "edge_type": edge_type,
                "source_phrase": edge_hits[0]["source_phrase"],
                "claim_risk": "high" if refs else "medium",
                "reasoning_quality": "source_phrase_only",
                "mechanism_refs_needed": refs,
                "evidence": {
                    "segment_ids": [item.segment_id for item in window_segments],
                    "start_ms": window_segments[0].start_ms,
                    "end_ms": window_segments[-1].end_ms,
                    "quote": window_text[:280],
                },
                "promotion_blockers": blockers,
                "runtime_allowed": False,
            }
        )

    return {
        "schema_version": "p14.relation_candidates.v0",
        "source_id": bundle.source_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "candidate_edges": edges,
        "summary": {
            "candidate_count": len(edges),
            "mechanism_dependent_count": sum(1 for item in edges if item["mechanism_refs_needed"]),
        },
    }


def _candidate_rank(candidate: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        0 if candidate["state"] == "S2_set_candidate" else 1,
        -len(candidate.get("evidence_windows") or []),
        -len(candidate.get("selected_moves") or []),
        candidate.get("species_name", ""),
    )


def _species_signal_summaries(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_species: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        species = str(candidate.get("species_name") or "")
        if not species:
            continue
        summary = by_species.setdefault(
            species,
            {
                "species_name": species,
                "candidate_count": 0,
                "s2_count": 0,
                "moves": Counter(),
                "roles": Counter(),
                "blockers": Counter(),
                "examples": [],
            },
        )
        summary["candidate_count"] += 1
        if candidate.get("state") == "S2_set_candidate":
            summary["s2_count"] += 1
        summary["moves"].update(candidate.get("selected_moves") or [])
        summary["roles"].update(candidate.get("inferred_roles") or [])
        summary["blockers"].update(candidate.get("promotion_blockers") or [])
        if len(summary["examples"]) < 2:
            summary["examples"].extend(candidate.get("evidence_windows") or [])

    result: list[dict[str, Any]] = []
    for summary in by_species.values():
        result.append(
            {
                "species_name": summary["species_name"],
                "candidate_count": summary["candidate_count"],
                "s2_count": summary["s2_count"],
                "top_moves": [item for item, _ in summary["moves"].most_common(5)],
                "top_roles": [item for item, _ in summary["roles"].most_common(4)],
                "top_blockers": [item for item, _ in summary["blockers"].most_common(4)],
                "examples": summary["examples"],
            }
        )
    return sorted(result, key=lambda item: (-item["s2_count"], -item["candidate_count"], item["species_name"]))


def render_pm_delta_packet(batch_id: str, set_payloads: list[dict[str, Any]], edge_payloads: list[dict[str, Any]]) -> str:
    all_sets = [item for payload in set_payloads for item in payload["candidate_sets"]]
    all_edges = [item for payload in edge_payloads for item in payload["candidate_edges"]]
    s2_sets = [item for item in all_sets if item["state"] == "S2_set_candidate"]
    blocked_sets = [item for item in all_sets if "mechanism_rule_not_reviewed" in item["promotion_blockers"]]
    species_summaries = _species_signal_summaries(s2_sets)[:10]

    lines = [
        f"# Phase 1 Set-Centric Delta Packet: {batch_id}",
        "",
        "这份 packet 只回答一个问题：自动增量链路现在能不能继续往下跑。下面是主文，附录可以不看。",
        "",
        "## 结论",
        "- 可以继续跑小批量，但不能自动 promotion。",
        "- 当前工具能从字幕证据窗口里生成 set/edge 候选，也能把它们全部挡在 runtime 外。",
        "- 这正是我们要的第一步：先证明自动增量链路会产出材料，也会拒绝把不稳材料升格。",
        "",
        "## 本轮产物",
        f"- 来源：{len(set_payloads)} 条。",
        f"- set 候选：{len(all_sets)} 个，其中带技能/动作证据的 S2 候选 {len(s2_sets)} 个。",
        f"- relation 候选：{len(all_edges)} 条。",
        f"- 被 quarantine / 不允许 promotion：{sum(1 for item in all_sets if 'single_evidence_window' in item.get('promotion_blockers', []))} 个。",
        f"- 因机制未 review 被挡住的 set 候选：{len(blocked_sets)} 个。",
        "",
        "## 覆盖信号，不是卡",
        "这些名字说明视频里有可追的 set 线索，但还不是可 review 的配招卡。",
    ]
    if species_summaries:
        for item in species_summaries[:6]:
            evidence = (item.get("examples") or [{}])[0]
            moves = "、".join(item.get("top_moves") or []) or "未抽到"
            roles = "、".join(item.get("top_roles") or []) or "待定"
            blockers = "、".join(item.get("top_blockers") or [])
            lines.append(
                f"- {item['species_name']}：{item['s2_count']} 个带技能词的证据窗口；同窗技能词 {moves}；角色线索 {roles}；主要挡板：{blockers}。"
            )
    else:
        lines.append("- 无。")

    lines.extend(
        [
            "",
            "## 现在自动 Agent 可以做什么",
            "- 继续按 source gap 抓 3-5 条视频。",
            "- 对每条源生成同样的 set/edge candidates。",
            "- 用 reviewer ledger 自动挡掉：单证据窗、当前对局状态、机制未 review、ASR 未解决。",
            "- 下一轮给你看的只应该是：重复出现的 set、来源冲突、必须你裁的边界。",
            "",
            "## 不能做什么",
            "- 不能把这些候选直接写入 runtime graph。",
            "- 不能把一个视频里临场提到的技能当成稳定配招。",
            "- 不能让机制 side-channel 变成主任务。",
            "",
            "## 附录：证据样例",
        ]
    )
    for item in species_summaries[:6]:
        evidence = (item.get("examples") or [{}])[0]
        lines.append(
            f"- {item['species_name']} {_ms_to_stamp(evidence.get('start_ms'))}：“{evidence.get('quote', '')}”"
        )

    lines.extend(["", "## 附录：关系候选样例"])
    if all_edges:
        for item in all_edges[:6]:
            evidence = item["evidence"]
            targets = "、".join(item["target_species_or_sets"])
            lines.append(
                f"- {item['source_species_or_set']} -> {targets}：{item['edge_type']}，风险 {item['claim_risk']}。例 {_ms_to_stamp(evidence.get('start_ms'))}：“{evidence.get('quote', '')}”"
            )
    else:
        lines.append("- 本轮没有抽到足够明确的关系候选。")

    lines.extend(
        [
            "",
            "## 下一步",
            "先做增量 audit：把本轮候选和历史候选按物种、技能、角色线索聚合，找跨来源重复和冲突。只有重复信号足够清楚时才进入 PM review；如果核心 gap 仍然缺证，再回到 source gap fill 补源。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_audit_payload(batch_id: str, set_payloads: list[dict[str, Any]], edge_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    all_sets = [item for payload in set_payloads for item in payload["candidate_sets"]]
    all_edges = [item for payload in edge_payloads for item in payload["candidate_edges"]]
    blocker_counts = Counter(blocker for item in all_sets for blocker in item.get("promotion_blockers") or [])
    blocker_counts.update(Counter(blocker for item in all_edges for blocker in item.get("promotion_blockers") or []))
    quarantined = []
    for item in all_sets:
        if (
            item["state"] != "S2_set_candidate"
            or "single_evidence_window" in item["promotion_blockers"]
            or "window_too_broad" in item["promotion_blockers"]
        ):
            quarantined.append(
                {
                    "candidate_id": item["candidate_id"],
                    "reason": "low_stability_or_window_only_candidate",
                    "runtime_allowed": False,
                }
            )
    return {
        "schema_version": "p14.incremental_audit.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "summary": {
            "set_candidate_count": len(all_sets),
            "s2_set_candidate_count": sum(1 for item in all_sets if item["state"] == "S2_set_candidate"),
            "relation_candidate_count": len(all_edges),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "quarantined_count": len(quarantined),
        },
        "quarantined_candidates": quarantined[:50],
    }


def run_set_pipeline(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    source_ids: set[str] | None = None,
    db_path: Path = DEFAULT_BATTLE_DEX,
) -> dict[str, Any]:
    bundles = load_ingested_sources(source_queue, source_ids=source_ids)
    species_move_pools = load_species_move_pools(db_path) or None
    set_payloads: list[dict[str, Any]] = []
    edge_payloads: list[dict[str, Any]] = []
    for bundle in bundles:
        set_payload = build_set_candidates(bundle, species_move_pools=species_move_pools)
        edge_payload = build_relation_candidates(bundle)
        set_payloads.append(set_payload)
        edge_payloads.append(edge_payload)
        _write_yaml(out_root / "set_candidates" / f"{bundle.source_id}.candidate_sets.yaml", set_payload)
        _write_yaml(out_root / "relation_candidates" / f"{bundle.source_id}.candidate_edges.yaml", edge_payload)

    audit = build_audit_payload(batch_id, set_payloads, edge_payloads)
    audit_path = out_root / "audits" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_delta.md"
    _write_yaml(audit_path, audit)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_pm_delta_packet(batch_id, set_payloads, edge_payloads), encoding="utf-8")
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_count": len(bundles),
        "paths": {
            "audit": _relpath(audit_path),
            "pm_delta_packet": _relpath(packet_path),
            "set_candidates_dir": _relpath(out_root / "set_candidates"),
            "relation_candidates_dir": _relpath(out_root / "relation_candidates"),
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

    result = run_set_pipeline(
        source_queue=args.source_queue,
        out_root=args.out_root,
        batch_id=args.batch_id,
        source_ids=set(args.source_id) if args.source_id else None,
        db_path=args.db_path,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"set pipeline: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
