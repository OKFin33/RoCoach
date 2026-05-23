#!/usr/bin/env python3
"""Build human-readable PM review sheets for Round 1 Meta Graph candidates."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.transcript_quality import transcript_quality_flags, transcript_quality_label


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUND_ROOT = REPO_ROOT / "artifacts" / "meta_graph_round1_set_input"
DEFAULT_QUEUE = DEFAULT_ROUND_ROOT / "source_queue.yaml"
DEFAULT_REVIEW_ROOT = DEFAULT_ROUND_ROOT / "pm_review"

PRIORITY_SCORE = {"p0": 30, "p1": 20, "p2": 10}
STATUS_SCORE = {
    "ab_refined_exists": 30,
    "corrected_transcript_exists": 25,
    "needs_ab_refine_refresh": 15,
    "needs_ab_refine": 10,
}


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    review_type: str
    score: int
    candidate_id: str
    source_id: str
    priority: str
    target_archetype: str
    source_ref: str
    span: str
    level: str
    species: str
    moves: str
    roles: str
    archetypes: str
    blockers: str
    quality_flags: str
    excerpt: str


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _compact_text(value: str, *, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _join(values: list[Any]) -> str:
    return " / ".join(str(value) for value in values if str(value).strip())


def _role_text(item: dict[str, Any]) -> str:
    rendered: list[str] = []
    for role in item.get("inferred_roles", []):
        labels = role.get("role_labels", [])
        phrase = role.get("source_phrase", "")
        if labels:
            rendered.append(f"{_join(labels)} ({phrase})" if phrase else _join(labels))
    return " / ".join(rendered)


def _score_candidate(candidate: dict[str, Any], source: dict[str, Any]) -> int:
    score = 0
    score += PRIORITY_SCORE.get(str(source.get("priority", "")), 0)
    score += STATUS_SCORE.get(str(source.get("ingest_status", "")), 0)
    if candidate.get("level") == "L2":
        score += 100
    if candidate.get("promotion_blockers") == ["pm_review_required"]:
        score += 25
    if candidate.get("source_names", {}).get("species"):
        score += 10
    if candidate.get("source_names", {}).get("moves"):
        score += 10
    if source.get("source_id") == "tier_rating_0412":
        score -= 20
    flags = _quality_flags(candidate)
    label = transcript_quality_label(flags)
    if label == "needs_repair":
        score -= 80
    if label == "usable_with_caution":
        score -= 20
    return score


def _quality_flags(candidate: dict[str, Any]) -> list[str]:
    return transcript_quality_flags(str(candidate.get("source_excerpt", "")))


def collect_review_items(
    round_root: Path,
    queue_path: Path,
    *,
    top_n: int,
    max_per_source: int,
    repair_n: int,
) -> list[ReviewItem]:
    queue = _read_yaml(queue_path)
    source_by_id = {str(source["source_id"]): source for source in queue.get("sources", [])}
    candidates: list[tuple[int, str, dict[str, Any], dict[str, Any], dict[str, Any]]] = []

    for path in sorted((round_root / "extracted").glob("*.candidate_sets.yaml")):
        payload = _read_yaml(path)
        source_id = str(payload.get("source_id", ""))
        if source_id not in source_by_id:
            continue
        source = source_by_id.get(source_id, {"source_id": source_id})
        for candidate in payload.get("candidate_sets", []):
            if candidate.get("level") != "L2":
                continue
            score = _score_candidate(candidate, source)
            candidates.append((score, source_id, source, payload, candidate))

    candidates.sort(key=lambda row: (-row[0], row[1], row[4].get("candidate_id", "")))

    selected: list[tuple[int, str, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    per_source: dict[str, int] = {}
    for row in candidates:
        if _review_type(row[4]) == "needs_transcript_repair":
            continue
        source_id = row[1]
        if per_source.get(source_id, 0) >= max_per_source:
            continue
        selected.append(row)
        per_source[source_id] = per_source.get(source_id, 0) + 1
        if len(selected) >= top_n:
            break

    selected_ids = {row[4].get("candidate_id", "") for row in selected}
    repair_rows = [
        row
        for row in candidates
        if _review_type(row[4]) == "needs_transcript_repair"
        and row[4].get("candidate_id", "") not in selected_ids
    ][:repair_n]
    selected.extend(repair_rows)

    review_items: list[ReviewItem] = []
    selected.sort(
        key=lambda row: (
            _review_type(row[4]) != "card_candidate",
            -row[0],
            row[1],
            row[4].get("candidate_id", ""),
        )
    )
    for index, (score, source_id, source, payload, candidate) in enumerate(selected, start=1):
        names = candidate.get("source_names", {})
        review_items.append(
            ReviewItem(
                review_id=f"R1-{index:03d}",
                review_type=_review_type(candidate),
                score=score,
                candidate_id=str(candidate.get("candidate_id", "")),
                source_id=source_id,
                priority=str(source.get("priority", "")),
                target_archetype=str(source.get("target_archetype", "")),
                source_ref=str(payload.get("source_ref", "")),
                span=_join(candidate.get("source_span_ids", [])),
                level=str(candidate.get("level", "")),
                species=_join(names.get("species", [])),
                moves=_join(names.get("moves", [])),
                roles=_role_text(candidate),
                archetypes=_join(candidate.get("archetype_tags", [])),
                blockers=_join(candidate.get("promotion_blockers", [])),
                quality_flags=_join(_quality_flags(candidate)),
                excerpt=_compact_text(str(candidate.get("source_excerpt", ""))),
            )
        )
    return review_items


def write_csv(path: Path, items: list[ReviewItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "review_id",
        "review_type",
        "decision",
        "correction_note",
        "species_should_be",
        "moves_should_be",
        "review_question",
        "priority",
        "source_id",
        "target_archetype",
        "span",
        "species",
        "moves",
        "roles",
        "archetypes",
        "blockers",
        "quality_flags",
        "excerpt",
        "candidate_id",
        "source_ref",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "review_id": item.review_id,
                    "review_type": item.review_type,
                    "decision": "",
                    "correction_note": "",
                    "species_should_be": "",
                    "moves_should_be": "",
                    "review_question": "这个片段能不能作为一个图谱配置候选？",
                    "priority": item.priority,
                    "source_id": item.source_id,
                    "target_archetype": item.target_archetype,
                    "span": item.span,
                    "species": item.species,
                    "moves": item.moves,
                    "roles": item.roles,
                    "archetypes": item.archetypes,
                    "blockers": item.blockers,
                    "quality_flags": item.quality_flags,
                    "excerpt": item.excerpt,
                    "candidate_id": item.candidate_id,
                    "source_ref": item.source_ref,
                }
            )


def write_dashboard(path: Path, items: list[ReviewItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Round 1 PM Review Dashboard",
        "",
        "这个文件是给 PM 看的，不需要读代码，也不需要读 YAML。",
        "",
        "## How To Review",
        "",
        "先看 `Card Candidates`。这些是短片段，适合转成图谱配置卡。",
        "",
        "字段意思：",
        "",
        "- `片段里出现的精灵`: 机器从原文里认出的精灵名。它们可能是我方、对方、队友、克制对象，不一定都是同一个 set 成员。",
        "- `片段里出现的技能`: 机器从原文里认出的技能名。它们只是证据线索，不等于最终配招。",
        "- `可能的定位线索`: 从 `首发`、`联防`、`C位`、`清强化` 这类词猜出来的角色线索，只是提示你快速判断。",
        "",
        "你真正要判断的是：这段话能不能整理成一个有用的图谱卡/关系/案例，不是检查机器字段格式。",
        "",
        "- `accept`: 这个片段可以进入 graph card 草稿。",
        "- `edge_only`: 不够做单卡，但可以保留为关系/克制/配合线索。",
        "- `fix`: 大方向对，但名字、技能、角色需要改。",
        "- `reject`: 片段不可靠或信息不够。",
        "",
        "你可以直接回：`R1-003 accept；R1-006 fix：物种应为 X；R1-009 reject`。",
        "",
        "## Card Candidates",
        "",
    ]

    for item in [item for item in items if item.review_type == "card_candidate"]:
        lines.extend(
            [
                f"### {item.review_id}: {item.species or '未解析物种'}",
                "",
                f"- 建议优先级: `{item.priority}`",
                f"- 来源: `{item.source_id}` / `{item.span}`",
                f"- 目标桶: {item.target_archetype}",
                f"- 片段里出现的精灵: {item.species or '无'}",
                f"- 片段里出现的技能: {item.moves or '无'}",
                f"- 可能的定位线索: {item.roles or item.archetypes or '无'}",
                f"- 文本质量标记: {item.quality_flags or '无'}",
                f"- 阻塞项: {item.blockers or '无'}",
                f"- 原片段: {item.excerpt}",
                "- 你要判: 这段能否整理成“某个精灵/队伍结构在什么情况下有用”的图谱信息？",
                "",
                "你的判断：",
                "",
                "- [ ] accept",
                "- [ ] edge_only",
                "- [ ] fix:",
                "- [ ] reject",
                "",
            ]
        )
    lines.extend(
        [
            "## Battle Moment Candidates",
            "",
            "这些不建议直接做配置卡，主要判断是否值得保留为 D-layer 例子或 relation edge。",
            "",
        ]
    )
    for item in [item for item in items if item.review_type == "battle_moment_candidate"]:
        lines.extend(
            [
                f"### {item.review_id}: {item.target_archetype}",
                "",
                f"- 建议优先级: `{item.priority}`",
                f"- 来源: `{item.source_id}` / `{item.span}`",
                f"- 涉及精灵: {item.species or '无'}",
                f"- 涉及技能: {item.moves or '无'}",
                f"- 可能价值: {item.roles or item.archetypes or '关系/博弈片段'}",
                f"- 文本质量标记: {item.quality_flags or '无'}",
                f"- 原片段: {item.excerpt}",
                "",
                "你的判断：",
                "",
                "- [ ] keep_as_d_layer",
                "- [ ] keep_as_relation",
                "- [ ] fix:",
                "- [ ] reject",
                "",
            ]
        )
    repair_items = [item for item in items if item.review_type == "needs_transcript_repair"]
    if repair_items:
        lines.extend(
            [
                "## Needs Transcript Repair",
                "",
                "这些片段先不要做机制判断。只需要补错词，或者直接 reject。",
                "",
            ]
        )
        for item in repair_items:
            lines.extend(
                [
                    f"### {item.review_id}: {item.source_id} / {item.span}",
                    "",
                    f"- 文本质量标记: {item.quality_flags}",
                    f"- 片段里出现的精灵: {item.species or '无'}",
                    f"- 片段里出现的技能: {item.moves or '无'}",
                    f"- 原片段: {item.excerpt}",
                    "",
                    "你的判断：",
                    "",
                    "- [ ] repair:",
                    "- [ ] reject",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def _lazy_decision(item: ReviewItem) -> tuple[str, str, bool]:
    if item.review_type == "needs_transcript_repair":
        return (
            "defer_repair",
            "ASR 仍有未解词；先不让它阻塞图谱，后面只做 transcript repair。",
            False,
        )
    if item.source_id == "tier_rating_0412" or item.priority == "p2":
        return (
            "defer_coverage_only",
            "评级/概览源适合做覆盖信号，不适合第一轮直接出 reviewed card。",
            False,
        )
    if item.review_type == "battle_moment_candidate":
        if item.priority == "p0":
            return (
                "keep_as_d_layer_candidate",
                "这是博弈/应对片段，先沉到 D-layer 候选，不要求你现在逐字审。",
                False,
            )
        return (
            "keep_as_relation_candidate",
            "片段信息密度高但不是单卡，先保留为关系/克制候选。",
            False,
        )
    if item.source_id == "light_fighting_team_0414" and "光合" in item.target_archetype:
        return (
            "auto_draft_with_known_guardrail",
            "可自动做未审草稿，但套用已知 PM 约束：光合印记由光合作用产生，食尘短绒只按偷/保印记处理。",
            False,
        )
    if item.source_id == "niche_electric_ball_sheep_0415":
        return (
            "defer_until_cleaner_source",
            "这个源口语噪声太大，先不消耗你的 review 注意力。",
            False,
        )
    if item.quality_flags:
        return (
            "defer_quality_risk",
            "文本质量标记不干净，先不进入第一批草稿。",
            False,
        )
    return (
        "auto_draft_unreviewed",
        "字段够且文本干净，可先做 unreviewed 草稿；不进入 runtime。",
        False,
    )


def write_lazy_review(path: Path, items: list[ReviewItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decisions = [(item, *_lazy_decision(item)) for item in items]
    buckets: dict[str, list[tuple[ReviewItem, str, bool]]] = {}
    for item, decision, reason, needs_pm in decisions:
        buckets.setdefault(decision, []).append((item, reason, needs_pm))

    auto_draft = buckets.get("auto_draft_unreviewed", []) + buckets.get("auto_draft_with_known_guardrail", [])
    keep_later = (
        buckets.get("keep_as_d_layer_candidate", [])
        + buckets.get("keep_as_relation_candidate", [])
        + buckets.get("defer_coverage_only", [])
        + buckets.get("defer_until_cleaner_source", [])
        + buckets.get("defer_quality_risk", [])
        + buckets.get("defer_repair", [])
    )

    lines = [
        "# Round 1 Lazy Review",
        "",
        "这个文件是给不想读 review 的 PM 看的。",
        "",
        "原则：我先给默认动作；默认动作只会进入 `unreviewed` 草稿、relation candidate、D-layer candidate 或 backlog，不会进入 runtime reviewed graph。",
        "",
        "你只需要看 `Need Your Attention`。如果你懒得看，可以直接回：`按 lazy review 默认执行`。",
        "",
        "## Summary",
        "",
        f"- total_review_items: {len(items)}",
        f"- auto_draft_unreviewed: {len(auto_draft)}",
        f"- keep_or_defer_without_pm: {len(keep_later)}",
        "- runtime_promotion: 0",
        "",
        "## Need Your Attention",
        "",
    ]

    attention_items = [
        row
        for row in auto_draft
        if row[0].source_id == "light_fighting_team_0414"
        or row[0].source_id == "pvp_daily_001_hotword_asr_v3"
    ][:8]
    if not attention_items:
        lines.append("无。")
    for item, reason, _needs_pm in attention_items:
        lines.extend(
            [
                f"### {item.review_id}: {item.species or item.target_archetype}",
                "",
                f"- default_action: `{_lazy_decision(item)[0]}`",
                f"- why: {reason}",
                f"- source: `{item.source_id}` / `{item.span}`",
                f"- species: {item.species or '无'}",
                f"- moves: {item.moves or '无'}",
                f"- only_check: 这条是否明显方向错了；不是让你逐字审。",
                f"- excerpt: {item.excerpt}",
                "",
            ]
        )

    lines.extend(
        [
            "## Default Actions",
            "",
            "| default_action | count | ids |",
            "|---|---:|---|",
        ]
    )
    for decision in sorted(buckets):
        ids = ", ".join(item.review_id for item, _reason, _needs_pm in buckets[decision])
        lines.append(f"| `{decision}` | {len(buckets[decision])} | {ids} |")

    lines.extend(
        [
            "",
            "## Execution Contract",
            "",
            "- `auto_draft_unreviewed`: 生成 card draft，但保持 `review_status: unreviewed`。",
            "- `auto_draft_with_known_guardrail`: 生成 card draft，并套用 PM 已确认机制边界，不额外问你。",
            "- `keep_as_d_layer_candidate`: 生成 D-layer 候选案例，不做图谱卡。",
            "- `keep_as_relation_candidate`: 生成 relation/edge 候选，不做图谱卡。",
            "- `defer_*`: 本轮不处理，不再占用 PM review。",
            "",
            "## Full Detail",
            "",
        ]
    )
    for item, decision, reason, _needs_pm in decisions:
        lines.extend(
            [
                f"### {item.review_id}: {decision}",
                "",
                f"- reason: {reason}",
                f"- type: `{item.review_type}`",
                f"- source: `{item.source_id}` / `{item.span}`",
                f"- species: {item.species or '无'}",
                f"- moves: {item.moves or '无'}",
                f"- value: {item.roles or item.archetypes or item.target_archetype}",
                f"- excerpt: {item.excerpt}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_lazy_decisions(path: Path, items: list[ReviewItem]) -> None:
    payload = {
        "runtime_promotion": False,
        "review_mode": "lazy_default",
        "operator_instruction": "PM may reply `按 lazy review 默认执行`; defaults only create unreviewed drafts/candidates/backlog.",
        "decisions": [
            {
                "review_id": item.review_id,
                "candidate_id": item.candidate_id,
                "source_id": item.source_id,
                "span": item.span,
                "review_type": item.review_type,
                "default_action": decision,
                "reason": reason,
                "species": item.species,
                "moves": item.moves,
                "target_archetype": item.target_archetype,
                "runtime_allowed": False,
            }
            for item, decision, reason, _needs_pm in [(item, *_lazy_decision(item)) for item in items]
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _review_type(candidate: dict[str, Any]) -> str:
    flags = _quality_flags(candidate)
    if transcript_quality_label(flags) == "needs_repair":
        return "needs_transcript_repair"
    names = candidate.get("source_names", {})
    species_count = len(names.get("species", []))
    move_count = len(names.get("moves", []))
    if 1 <= species_count <= 2 and 1 <= move_count <= 4:
        return "card_candidate"
    return "battle_moment_candidate"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--round-root", type=Path, default=DEFAULT_ROUND_ROOT)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--review-root", type=Path, default=DEFAULT_REVIEW_ROOT)
    parser.add_argument("--top-n", type=int, default=30)
    parser.add_argument("--max-per-source", type=int, default=4)
    parser.add_argument("--repair-n", type=int, default=8)
    args = parser.parse_args()

    items = collect_review_items(
        args.round_root,
        args.queue,
        top_n=args.top_n,
        max_per_source=args.max_per_source,
        repair_n=args.repair_n,
    )
    write_dashboard(args.review_root / "ROUND1_REVIEW_DASHBOARD.md", items)
    write_lazy_review(args.review_root / "ROUND1_LAZY_REVIEW.md", items)
    write_lazy_decisions(args.review_root / "round1_lazy_decisions.yaml", items)
    write_csv(args.review_root / "round1_review_sheet.csv", items)
    print(f"review_items: {len(items)}")
    print(f"dashboard: {args.review_root / 'ROUND1_REVIEW_DASHBOARD.md'}")
    print(f"lazy_review: {args.review_root / 'ROUND1_LAZY_REVIEW.md'}")
    print(f"lazy_decisions: {args.review_root / 'round1_lazy_decisions.yaml'}")
    print(f"csv: {args.review_root / 'round1_review_sheet.csv'}")


if __name__ == "__main__":
    main()
