#!/usr/bin/env python3
"""Rank queued P14 sources against current Set Graph coverage gaps.

This is planning substrate only. It selects the next ingest targets but never
promotes graph data.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_MISSION_BOARD = REPO_ROOT / "artifacts" / "knowledge_ops" / "mission_board.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_BATCH_ID = f"phase1_source_gap_fill_{date.today().isoformat()}"

PRIORITY_SCORE = {"high": 30, "medium": 18, "low": 5}
EXPECTED_VALUE_SCORE = {"high": 25, "medium": 14, "low": 3}
SOURCE_TYPE_SCORE = {
    "team_explainer": 24,
    "matchup_counterplay": 24,
    "mechanism_tutorial": 14,
    "gameplay_replay": 8,
    "tier_overview": 2,
}
QUALITY_PENALTIES = {
    "high_noise": -10,
    "older_meta_snapshot": -5,
    "self_declared_newbie": -9,
    "newbie_perspective": -5,
    "short_video_may_lack_reasoning": -5,
    "version_answer_framing": -3,
}

GAP_PROFILES = {
    "翼王 common sets": {
        "terms": ["翼王"],
        "preferred_source_types": ["team_explainer"],
        "intent": "common_set_coverage",
    },
    "沙暴/格斗 matchup": {
        "terms": ["沙暴", "格斗"],
        "preferred_source_types": ["matchup_counterplay", "gameplay_replay"],
        "intent": "matchup_edge_coverage",
    },
    "星陨 cross-source confirmation": {
        "terms": ["星陨", "帕尔"],
        "preferred_source_types": ["team_explainer", "mechanism_tutorial", "gameplay_replay"],
        "intent": "cross_source_confirmation",
    },
}

GAP_STOPWORDS = {
    "common",
    "set",
    "sets",
    "matchup",
    "cross",
    "source",
    "confirmation",
}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


@dataclass(frozen=True)
class SourceScore:
    source: dict[str, Any]
    gap: str
    score: int
    matched_terms: list[str]
    reasons: list[str]
    penalties: list[str]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _source_text(source: dict[str, Any]) -> str:
    fields: list[str] = [
        str(source.get("source_id") or ""),
        str(source.get("title") or ""),
        str(source.get("target_archetype") or ""),
        str(source.get("discovery_reason") or ""),
        " ".join(str(item) for item in source.get("target_entities") or []),
    ]
    return " ".join(fields)


def _gap_terms(gap: str) -> list[str]:
    profile = GAP_PROFILES.get(gap)
    if profile:
        return list(profile["terms"])
    terms = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]+", gap)
    result: list[str] = []
    for term in terms:
        if term.lower() in GAP_STOPWORDS:
            continue
        result.append(term)
    return result


def _gap_preferred_types(gap: str) -> list[str]:
    profile = GAP_PROFILES.get(gap) or {}
    return list(profile.get("preferred_source_types") or [])


def _gap_intent(gap: str) -> str:
    profile = GAP_PROFILES.get(gap) or {}
    return str(profile.get("intent") or "gap_coverage")


def _extract_target_gaps(mission_board: dict[str, Any]) -> list[str]:
    for experiment in mission_board.get("phase1_experiments") or []:
        if experiment.get("experiment_id") == "p14_e2_source_discovery_gap_fill":
            return [str(item) for item in experiment.get("target_gaps") or [] if item]
    return list(GAP_PROFILES)


def _is_queued(source: dict[str, Any]) -> bool:
    return str(source.get("ingest_status") or "queued") == "queued"


def _processed_terms(sources: list[dict[str, Any]]) -> set[str]:
    terms: set[str] = set()
    for source in sources:
        if _is_queued(source):
            continue
        text = _source_text(source)
        for gap in GAP_PROFILES:
            for term in _gap_terms(gap):
                if term in text:
                    terms.add(term)
    return terms


def _quality_penalties(source: dict[str, Any]) -> tuple[int, list[str]]:
    prior = source.get("source_quality_prior") or {}
    penalties: list[str] = []
    score = 0
    if prior.get("likely_noise") == "high":
        score += QUALITY_PENALTIES["high_noise"]
        penalties.append("likely_noise=high")
    for item in prior.get("promotion_bias") or []:
        key = str(item)
        if key in QUALITY_PENALTIES:
            score += QUALITY_PENALTIES[key]
            penalties.append(key)
    return score, penalties


def score_source_for_gap(source: dict[str, Any], gap: str, processed_gap_terms: set[str]) -> SourceScore:
    text = _source_text(source)
    text_lower = text.lower()
    terms = _gap_terms(gap)
    matched_terms = [term for term in terms if term in text or term.lower() in text_lower]
    reasons: list[str] = []
    penalties: list[str] = []

    if not matched_terms:
        return SourceScore(source=source, gap=gap, score=0, matched_terms=[], reasons=[], penalties=["no_gap_match"])

    score = 40 * len(matched_terms)
    if len(matched_terms) == len(terms):
        score += 18
        reasons.append("all_gap_terms_matched")
    else:
        reasons.append("partial_gap_match")

    priority = str(source.get("priority") or "low")
    expected_value = str(source.get("expected_value") or "low")
    source_type = str(source.get("source_type") or "")
    score += PRIORITY_SCORE.get(priority, 0)
    score += EXPECTED_VALUE_SCORE.get(expected_value, 0)
    score += SOURCE_TYPE_SCORE.get(source_type, 0)
    reasons.append(f"priority={priority}")
    reasons.append(f"expected_value={expected_value}")
    reasons.append(f"source_type={source_type}")

    preferred_types = _gap_preferred_types(gap)
    if source_type in preferred_types:
        score += 20
        reasons.append("preferred_source_type_for_gap")

    if _gap_intent(gap) == "cross_source_confirmation" and any(term in processed_gap_terms for term in matched_terms):
        score += 18
        reasons.append("adds_cross_source_confirmation")

    penalty_score, penalty_reasons = _quality_penalties(source)
    score += penalty_score
    penalties.extend(penalty_reasons)

    return SourceScore(
        source=source,
        gap=gap,
        score=max(score, 1),
        matched_terms=matched_terms,
        reasons=reasons,
        penalties=penalties,
    )


def _score_view(score: SourceScore, *, rank: int, recommendation: str) -> dict[str, Any]:
    source = score.source
    return {
        "rank": rank,
        "source_id": source.get("source_id"),
        "title": source.get("title"),
        "url": source.get("url"),
        "source_type": source.get("source_type"),
        "priority": source.get("priority"),
        "expected_value": source.get("expected_value"),
        "score": score.score,
        "matched_terms": score.matched_terms,
        "recommendation": recommendation,
        "reasons": score.reasons,
        "penalties": score.penalties,
    }


def _source_type_label(source_type: str | None) -> str:
    return {
        "team_explainer": "队伍/配招讲解",
        "matchup_counterplay": "对位反制讲解",
        "mechanism_tutorial": "机制讲解",
        "gameplay_replay": "实战解说",
        "tier_overview": "环境概览",
    }.get(str(source_type or ""), str(source_type or "未知类型"))


def _brief_reason(item: dict[str, Any]) -> str:
    source_type = _source_type_label(item.get("source_type"))
    priority = "高优先级" if item.get("priority") == "high" else "中优先级" if item.get("priority") == "medium" else "低优先级"
    value = "预期信息量高" if item.get("expected_value") == "high" else "预期信息量中等" if item.get("expected_value") == "medium" else "预期信息量低"
    matched = "、".join(item.get("matched_terms") or []) or "当前 gap"
    parts = [f"命中 {matched}", source_type, priority, value]
    if "adds_cross_source_confirmation" in (item.get("reasons") or []):
        parts.append("能给已处理主题补跨源确认")
    caution_map = {
        "version_answer_framing": "注意可能带版本答案口吻",
        "older_meta_snapshot": "注意发布时间较早",
        "short_video_may_lack_reasoning": "短视频可能缺少推理过程",
        "likely_noise=high": "字幕/表达噪声可能较高",
        "self_declared_newbie": "作者自称小白，只能当低置信补证",
        "newbie_perspective": "新手视角不能直接当高置信来源",
    }
    cautions = [caution_map[item] for item in item.get("penalties") or [] if item in caution_map]
    if cautions:
        parts.append("；".join(cautions))
    return "；".join(parts)


def _gap_label(gap: str | None) -> str:
    return {
        "翼王 common sets": "翼王常用 set",
        "沙暴/格斗 matchup": "沙暴/格斗对位",
        "星陨 cross-source confirmation": "星陨跨源确认",
    }.get(str(gap or ""), str(gap or "未知 gap"))


def rank_sources_by_gap(
    sources: list[dict[str, Any]],
    target_gaps: list[str],
) -> tuple[dict[str, list[SourceScore]], list[dict[str, Any]]]:
    queued = [source for source in sources if _is_queued(source)]
    processed_gap_terms = _processed_terms(sources)
    ranked: dict[str, list[SourceScore]] = {}
    for gap in target_gaps:
        scored = [
            score_source_for_gap(source, gap, processed_gap_terms)
            for source in queued
        ]
        scored = [item for item in scored if item.score > 0 and item.matched_terms]
        ranked[gap] = sorted(
            scored,
            key=lambda item: (
                -item.score,
                str(item.source.get("source_id") or ""),
            ),
        )

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for gap in target_gaps:
        if not ranked.get(gap):
            continue
        top = ranked[gap][0]
        source_id = str(top.source.get("source_id") or "")
        if source_id in selected_ids:
            continue
        selected_ids.add(source_id)
        selected.append(_score_view(top, rank=len(selected) + 1, recommendation="ingest_next"))

    extras: list[SourceScore] = []
    for gap, scores in ranked.items():
        for score in scores[1:]:
            source_id = str(score.source.get("source_id") or "")
            if source_id in selected_ids:
                continue
            if score.score < 85:
                continue
            extras.append(score)
    extras = sorted(extras, key=lambda item: (-item.score, item.gap, str(item.source.get("source_id") or "")))
    for extra in extras:
        if len(selected) >= 5:
            break
        source_id = str(extra.source.get("source_id") or "")
        if source_id in selected_ids:
            continue
        selected_ids.add(source_id)
        selected.append(_score_view(extra, rank=len(selected) + 1, recommendation="ingest_after_primary"))

    return ranked, selected


def build_gap_fill_audit(
    *,
    batch_id: str,
    queue: dict[str, Any],
    mission_board: dict[str, Any],
) -> dict[str, Any]:
    sources = list(queue.get("sources") or [])
    target_gaps = _extract_target_gaps(mission_board)
    ranked, recommendations = rank_sources_by_gap(sources, target_gaps)

    ranked_by_gap: list[dict[str, Any]] = []
    for gap in target_gaps:
        scores = ranked.get(gap) or []
        ranked_by_gap.append(
            {
                "gap": gap,
                "coverage_status": "candidate_sources_available" if scores else "no_queued_source",
                "top_candidates": [
                    _score_view(
                        score,
                        rank=index + 1,
                        recommendation=(
                            "ingest_next"
                            if any(item["source_id"] == score.source.get("source_id") and item["recommendation"] == "ingest_next" for item in recommendations)
                            else "ingest_after_primary"
                            if any(item["source_id"] == score.source.get("source_id") for item in recommendations)
                            else "defer"
                        ),
                    )
                    for index, score in enumerate(scores[:5])
                ],
            }
        )

    recommended_ids = [str(item["source_id"]) for item in recommendations]
    deferred = [
        {
            "source_id": source.get("source_id"),
            "title": source.get("title"),
            "source_type": source.get("source_type"),
            "reason": "not_matched_to_current_gap" if str(source.get("source_id")) not in recommended_ids else "recommended",
        }
        for source in sources
        if _is_queued(source) and str(source.get("source_id")) not in recommended_ids
    ]

    return {
        "schema_version": "p14.source_gap_fill.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "target_gaps": target_gaps,
        "summary": {
            "queued_source_count": sum(1 for source in sources if _is_queued(source)),
            "processed_source_count": sum(1 for source in sources if not _is_queued(source)),
            "gap_count": len(target_gaps),
            "recommended_next_ingest_count": len(recommendations),
            "unfilled_gap_count": sum(1 for item in ranked_by_gap if item["coverage_status"] == "no_queued_source"),
        },
        "recommended_next_ingest": recommendations,
        "ranked_by_gap": ranked_by_gap,
        "deferred_queued_sources": deferred,
        "policy_notes": [
            "source gap fill is planning substrate only",
            "do not ingest random queued sources before current target gaps are covered",
            "do not promote graph cards from these rankings",
        ],
    }


def render_pm_brief(audit: dict[str, Any]) -> str:
    recommendations = audit.get("recommended_next_ingest") or []
    primary = [item for item in recommendations if item.get("recommendation") == "ingest_next"]
    optional = [item for item in recommendations if item.get("recommendation") != "ingest_next"]
    ranked_by_gap = audit.get("ranked_by_gap") or []

    lines = [
        f"# Phase 1 Source Gap Fill: {audit['batch_id']}",
        "",
        "## 结论",
        "- 下一批先抓 3 条：翼王常用 set、沙暴/格斗对位、星陨跨源确认各一条。",
        "- 最多追加 2 条翼王补充源，用来拆物攻/魔攻/多打法，不要再随机扩源。",
        "- 这一步只决定抓取顺序，不代表任何 set 已经成立。",
        "",
        "## 下一批推荐",
    ]
    if not primary:
        lines.append("- 当前队列没有足够匹配这些 gap 的源，需要先搜索新视频。")
    for item in primary:
        lines.append(
            f"- P{item['rank']} [{item['source_id']}]({item.get('url')})：{item.get('title')}。{_brief_reason(item)}。"
        )

    lines.extend(["", "## 可选补充"])
    if optional:
        for item in optional:
            lines.append(
                f"- [{item['source_id']}]({item.get('url')})：{item.get('title')}。用途：同一 gap 的第二视角；{_brief_reason(item)}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(["", "## 不要现在做"])
    defer_lines: list[str] = []
    for item in audit.get("deferred_queued_sources") or []:
        source_type = _source_type_label(item.get("source_type"))
        if len(defer_lines) >= 5:
            break
        defer_lines.append(f"- {item.get('source_id')}：{item.get('title')}。先不抓，原因：不补当前三个 gap，类型 {source_type}。")
    lines.extend(defer_lines or ["- 无。"])

    lines.extend(["", "## Gap 覆盖检查"])
    for gap_item in ranked_by_gap:
        candidates = gap_item.get("top_candidates") or []
        if not candidates:
            lines.append(f"- {_gap_label(gap_item.get('gap'))}：没有现成 queued source，要重新搜索。")
            continue
        top = candidates[0]
        extra_count = max(len(candidates) - 1, 0)
        suffix = f"，另有 {extra_count} 个备选" if extra_count else ""
        lines.append(f"- {_gap_label(gap_item.get('gap'))}：首选 {top.get('source_id')}{suffix}。")

    lines.extend(
        [
            "",
            "## 下一步",
            "按 P1-P3 抓字幕/ASR，跑 evidence foundation，再跑 set pipeline。P4/P5 只有在翼王第一源噪声大，或者需要拆双流派时才补。",
        ]
    )
    return "\n".join(lines) + "\n"


def _apply_queue_delta(queue_path: Path, queue: dict[str, Any], audit: dict[str, Any], packet_path: Path, audit_path: Path) -> None:
    queue["latest_source_gap_fill"] = {
        "batch_id": audit["batch_id"],
        "generated_at": audit["generated_at"],
        "target_gaps": audit["target_gaps"],
        "recommended_next_source_ids": [
            item["source_id"]
            for item in audit.get("recommended_next_ingest") or []
            if item.get("recommendation") == "ingest_next"
        ],
        "optional_next_source_ids": [
            item["source_id"]
            for item in audit.get("recommended_next_ingest") or []
            if item.get("recommendation") != "ingest_next"
        ],
        "audit_path": _relpath(audit_path),
        "review_packet": _relpath(packet_path),
    }
    _write_yaml(queue_path, queue)


def run_source_gap_fill(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    mission_board: Path = DEFAULT_MISSION_BOARD,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    update_source_queue: bool = True,
) -> dict[str, Any]:
    queue = _load_yaml(source_queue)
    mission = _load_yaml(mission_board)
    audit = build_gap_fill_audit(batch_id=batch_id, queue=queue, mission_board=mission)
    audit_path = out_root / "audits" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    _write_yaml(audit_path, audit)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_pm_brief(audit), encoding="utf-8")
    if update_source_queue:
        _apply_queue_delta(source_queue, queue, audit, packet_path, audit_path)
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "audit": _relpath(audit_path),
            "pm_brief": _relpath(packet_path),
            "source_queue": _relpath(source_queue),
        },
        "summary": audit["summary"],
        "recommended_next_source_ids": [
            item["source_id"]
            for item in audit.get("recommended_next_ingest") or []
            if item.get("recommendation") == "ingest_next"
        ],
        "optional_next_source_ids": [
            item["source_id"]
            for item in audit.get("recommended_next_ingest") or []
            if item.get("recommendation") != "ingest_next"
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--mission-board", type=Path, default=DEFAULT_MISSION_BOARD)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--no-update-source-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_source_gap_fill(
        source_queue=args.source_queue,
        mission_board=args.mission_board,
        out_root=args.out_root,
        batch_id=args.batch_id,
        update_source_queue=not args.no_update_source_queue,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"source gap fill: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
