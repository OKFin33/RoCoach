#!/usr/bin/env python3
"""Select the next P14 volume-lane source batch from queued sources."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_BATCH_ID = f"phase1_volume_batch_plan_{date.today().isoformat()}"
DEFAULT_TARGET_SIZE = 20
MIN_TARGET_SIZE = 20
MAX_TARGET_SIZE = 30
ANTHOLOGY_PAGE_BVID_CAP = 3
BV_RE = re.compile(r"(BV[0-9A-Za-z]+)")
PAGE_RE = re.compile(r"(?:[?&]p=|_p)(\d+)")

PRIORITY_SCORE = {"high": 300, "medium": 180, "low": 60}
EXPECTED_VALUE_SCORE = {"high": 250, "medium": 140, "low": 30}
SOURCE_TYPE_SCORE = {
    "team_explainer": 140,
    "matchup_counterplay": 140,
    "mechanism_tutorial": 80,
    "gameplay_replay": 70,
    "tier_overview": 25,
}
QUALITY_PENALTIES = {
    "older_meta_snapshot": -90,
    "tier_overview_is_coverage_only": -45,
    "broad_pve_pvp_mixed_source": -30,
    "short_video_may_lack_reasoning": -25,
    "version_answer_framing": -20,
    "title_under_specified": -35,
    "title_needs_content_verification": -25,
}
STRONG_PVP_TITLE_TERMS = ("pvp", "PVP", "天梯", "竞技场", "对战", "对局", "阵容", "配队", "队伍", "上分", "大师", "登顶")
OFF_BOUNDARY_PVE_TITLE_TERMS = ("通关", "单通", "单刷", "必过", "秒过", "速刷", "boss", "Boss", "BOSS", "命定", "低练度", "大世界", "待机", "剧情", "主线任务", "主线", "完成攻略", "孵蛋", "神奇的蛋", "蛋全攻略", "副本", "异色", "奇遇")
OFF_BOUNDARY_DEX_TITLE_TERMS = ("图鉴", "捕捉地点", "捕捉", "抓", "抓到", "抓宠", "抓精灵", "获取方式", "获取攻略", "全收集", "点击就送", "素材", "矿石", "矿", "矿教学", "材料", "点位", "线路")
OFF_BOUNDARY_RESOURCE_ROUTE_TITLE_TERMS = ("采集", "跑图", "路线", "资源路线", "资源点", "全图", "全地图", "地图探索", "宝箱", "收集路线", "开图")
OFF_BOUNDARY_ALWAYS_TITLE_TERMS = ("手柄", "摇杆", "配置包", "大合照", "奖牌")
OFF_BOUNDARY_EVENT_TITLE_TERMS = ("限定动作", "动作解锁", "解锁攻略", "绝版", "白嫖", "炫彩", "奖励", "手柄", "摇杆", "配置包", "大合照", "奖牌")


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


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


def _is_queued(source: dict[str, Any]) -> bool:
    return str(source.get("ingest_status") or "queued") == "queued"


def _risk_flags(source: dict[str, Any]) -> list[str]:
    prior = source.get("source_quality_prior") or {}
    flags: list[str] = []
    if prior.get("likely_noise") == "high":
        flags.append("likely_noise=high")
    for item in prior.get("promotion_bias") or []:
        flags.append(str(item))
    return flags


def _extract_bvid(source: dict[str, Any]) -> str | None:
    match = BV_RE.search(str(source.get("url") or ""))
    return match.group(1) if match else None


def _has_anthology_page(source: dict[str, Any]) -> bool:
    if source.get("anthology_page_index"):
        return True
    match = PAGE_RE.search(str(source.get("url") or ""))
    if not match:
        return False
    try:
        return int(match.group(1)) > 1
    except ValueError:
        return False


def _score_source(
    source: dict[str, Any],
    *,
    recommended_ids: set[str],
    optional_ids: set[str],
) -> tuple[int, list[str], list[str]]:
    source_id = str(source.get("source_id") or "")
    reasons: list[str] = []
    flags = _risk_flags(source)
    score = 0
    if source_id in recommended_ids:
        score += 1000
        reasons.append("latest_source_gap_fill_recommended")
    elif source_id in optional_ids:
        score += 760
        reasons.append("latest_source_gap_fill_optional")
    priority = str(source.get("priority") or "low")
    expected_value = str(source.get("expected_value") or "low")
    source_type = str(source.get("source_type") or "")
    score += PRIORITY_SCORE.get(priority, 0)
    score += EXPECTED_VALUE_SCORE.get(expected_value, 0)
    score += SOURCE_TYPE_SCORE.get(source_type, 0)
    reasons.append(f"priority={priority}")
    reasons.append(f"expected_value={expected_value}")
    reasons.append(f"source_type={source_type}")
    for flag in flags:
        if flag in QUALITY_PENALTIES:
            score += QUALITY_PENALTIES[flag]
            reasons.append(f"penalty={flag}")
    return score, reasons, flags


def _off_boundary_defer_reason(source: dict[str, Any]) -> str | None:
    title = str(source.get("title") or "")
    if any(term in title for term in OFF_BOUNDARY_ALWAYS_TITLE_TERMS):
        return "outside_pvp_boundary_title"
    if any(term in title for term in OFF_BOUNDARY_RESOURCE_ROUTE_TITLE_TERMS):
        return "outside_pvp_boundary_title"
    title_has_strong_pvp = any(term in title for term in STRONG_PVP_TITLE_TERMS)
    if any(term in title for term in OFF_BOUNDARY_PVE_TITLE_TERMS) and not title_has_strong_pvp:
        return "outside_pvp_boundary_title"
    if any(term in title for term in OFF_BOUNDARY_DEX_TITLE_TERMS) and not title_has_strong_pvp:
        return "outside_pvp_boundary_title"
    if any(term in title for term in OFF_BOUNDARY_EVENT_TITLE_TERMS) and not title_has_strong_pvp:
        return "outside_pvp_boundary_title"
    if any(term in title for term in ("PVE", "pve")) and "PVP" not in title and "pvp" not in title:
        return "outside_pvp_boundary_title"
    return None


def _quota_defer_reason(
    source: dict[str, Any],
    selected: list[dict[str, Any]],
    target_size: int,
    *,
    protected: bool,
) -> str | None:
    if protected:
        return None
    source_type = str(source.get("source_type") or "")
    flags = _risk_flags(source)
    selected_type_counts = Counter(str(item.get("source_type") or "") for item in selected)
    selected_low_count = sum(1 for item in selected if str(item.get("priority") or "") == "low")
    selected_old_count = sum(1 for item in selected if "older_meta_snapshot" in _risk_flags(item))
    bvid = _extract_bvid(source)
    selected_same_bvid_count = sum(1 for item in selected if bvid and _extract_bvid(item) == bvid)

    tier_cap = max(3, target_size // 5)
    low_cap = max(4, target_size // 4)
    older_cap = max(3, target_size // 5)
    if _has_anthology_page(source) and bvid and selected_same_bvid_count >= ANTHOLOGY_PAGE_BVID_CAP:
        return "anthology_bvid_page_quota_reached"
    if source_type == "tier_overview" and selected_type_counts["tier_overview"] >= tier_cap:
        return "tier_overview_quota_reached"
    if str(source.get("priority") or "") == "low" and selected_low_count >= low_cap:
        return "low_priority_quota_reached"
    if "older_meta_snapshot" in flags and selected_old_count >= older_cap:
        return "older_snapshot_quota_reached"
    return None


def build_volume_batch_plan(
    *,
    batch_id: str,
    queue: dict[str, Any],
    target_size: int = DEFAULT_TARGET_SIZE,
) -> dict[str, Any]:
    target_size = max(MIN_TARGET_SIZE, min(MAX_TARGET_SIZE, target_size))
    queued = [source for source in queue.get("sources") or [] if _is_queued(source)]
    latest_gap = queue.get("latest_source_gap_fill") or {}
    recommended_ids = {str(item) for item in latest_gap.get("recommended_next_source_ids") or []}
    optional_ids = {str(item) for item in latest_gap.get("optional_next_source_ids") or []}

    scored: list[dict[str, Any]] = []
    for source in queued:
        off_boundary_reason = _off_boundary_defer_reason(source)
        score, reasons, flags = _score_source(source, recommended_ids=recommended_ids, optional_ids=optional_ids)
        scored.append(
            {
                "source": source,
                "score": score,
                "reasons": reasons,
                "risk_flags": flags,
                "off_boundary_reason": off_boundary_reason,
            }
        )
    scored.sort(key=lambda item: (-int(item["score"]), str(item["source"].get("source_id") or "")))

    selected_sources: list[dict[str, Any]] = []
    deferred_sources: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for item in scored:
        source = item["source"]
        source_id = str(source.get("source_id") or "")
        off_boundary_reason = item.get("off_boundary_reason")
        if off_boundary_reason:
            deferred_sources.append(_deferred_view(source, str(off_boundary_reason)))
            continue
        if len(selected_sources) >= target_size:
            deferred_sources.append(_deferred_view(source, "outside_target_batch_size"))
            continue
        protected = source_id in recommended_ids or source_id in optional_ids
        reason = _quota_defer_reason(source, selected_sources, target_size, protected=protected)
        if reason:
            deferred_sources.append(_deferred_view(source, reason))
            continue
        selected_sources.append(source)
        selected_ids.add(source_id)

    selected_views = [
        _selected_view(source, rank=index + 1, score=scored_item["score"], reasons=scored_item["reasons"], flags=scored_item["risk_flags"])
        for index, source in enumerate(selected_sources)
        for scored_item in scored
        if scored_item["source"] is source
    ]
    for item in scored:
        source = item["source"]
        source_id = str(source.get("source_id") or "")
        if source_id in selected_ids:
            continue
        if any(deferred.get("source_id") == source_id for deferred in deferred_sources):
            continue
        deferred_sources.append(_deferred_view(source, "not_selected"))

    source_type_mix = Counter(str(source.get("source_type") or "") for source in selected_sources)
    risk_mix = Counter(flag for source in selected_sources for flag in _risk_flags(source))
    plan = {
        "schema_version": "p14.volume_batch_plan.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "selection_policy": {
            "target_size": target_size,
            "target_batch_range": {"min": MIN_TARGET_SIZE, "max": MAX_TARGET_SIZE},
            "latest_source_gap_fill_batch": latest_gap.get("batch_id"),
            "recommended_sources_are_protected": True,
            "discovered_metadata_is_not_evidence": True,
        },
        "summary": {
            "queued_source_count": len(queued),
            "selected_source_count": len(selected_sources),
            "deferred_source_count": len(deferred_sources),
            "recommended_included_count": sum(1 for source in selected_sources if source.get("source_id") in recommended_ids),
            "optional_included_count": sum(1 for source in selected_sources if source.get("source_id") in optional_ids),
            "source_type_mix": dict(sorted(source_type_mix.items())),
            "risk_flag_mix": dict(sorted(risk_mix.items())),
        },
        "selected_sources": selected_views,
        "deferred_sources": deferred_sources,
        "selected_source_ids": [source["source_id"] for source in selected_views],
        "policy_notes": [
            "volume batch plan selects ingest order only",
            "subtitle/ASR and evidence foundation must still pass per source",
            "promotion lane remains closed unless consolidation/dashboard opens a PM review item",
        ],
    }
    return plan


def _selected_view(source: dict[str, Any], *, rank: int, score: int, reasons: list[str], flags: list[str]) -> dict[str, Any]:
    return {
        "rank": rank,
        "source_id": source.get("source_id"),
        "title": source.get("title"),
        "url": source.get("url"),
        "source_type": source.get("source_type"),
        "target_archetype": source.get("target_archetype"),
        "priority": source.get("priority"),
        "expected_value": source.get("expected_value"),
        "score": score,
        "selection_reasons": reasons,
        "risk_flags": flags,
    }


def _deferred_view(source: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "title": source.get("title"),
        "url": source.get("url"),
        "source_type": source.get("source_type"),
        "priority": source.get("priority"),
        "reason": reason,
    }


def render_pm_brief(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    lines = [
        f"# Volume Batch Plan: {plan['batch_id']}",
        "",
        "## 结论",
        f"- 下一批选 {summary['selected_source_count']} 条 queued source 进入字幕/ASR 和 Set Inventory。",
        f"- gap fill 推荐源纳入 {summary['recommended_included_count']} 条；可选补充纳入 {summary['optional_included_count']} 条。",
        "- 这个清单只决定抓取顺序，不代表来源内容可信，也不代表 set 已成立。",
        "",
        "## Source Mix",
    ]
    for key, value in summary.get("source_type_mix", {}).items():
        lines.append(f"- {key}: {value}")
    if summary.get("risk_flag_mix"):
        lines.extend(["", "## 风险标签"])
        for key, value in summary["risk_flag_mix"].items():
            lines.append(f"- {key}: {value}")

    lines.extend(["", "## 批跑清单"])
    for item in plan.get("selected_sources") or []:
        flags = ", ".join(item.get("risk_flags") or [])
        suffix = f"；风险 {flags}" if flags else ""
        lines.append(
            f"- P{item['rank']} [{item['source_id']}]({item.get('url')})：{item.get('title')}；{item.get('source_type')}；{item.get('target_archetype')}{suffix}。"
        )

    lines.extend(["", "## 暂缓"])
    for item in (plan.get("deferred_sources") or [])[:10]:
        lines.append(f"- {item.get('source_id')}：{item.get('title')}；原因 {item.get('reason')}。")
    if not plan.get("deferred_sources"):
        lines.append("- 无。")

    lines.extend(
        [
            "",
            "## 下一步",
            "按这个 source_id 清单跑字幕/ASR、AB 精校、evidence foundation、Set Inventory、consolidation，再生成 autorun dashboard。PM 只看 dashboard 的异常和新晋升候选。",
        ]
    )
    return "\n".join(lines) + "\n"


def _apply_queue_delta(queue_path: Path, queue: dict[str, Any], plan: dict[str, Any], plan_path: Path, packet_path: Path) -> None:
    queue["latest_volume_batch_plan"] = {
        "batch_id": plan["batch_id"],
        "generated_at": plan["generated_at"],
        "selected_source_ids": plan["selected_source_ids"],
        "selected_source_count": plan["summary"]["selected_source_count"],
        "queued_source_count": plan["summary"]["queued_source_count"],
        "plan_path": _relpath(plan_path),
        "review_packet": _relpath(packet_path),
        "runtime_allowed": False,
    }
    _write_yaml(queue_path, queue)


def run_volume_batch_plan(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    target_size: int = DEFAULT_TARGET_SIZE,
    update_source_queue: bool = True,
) -> dict[str, Any]:
    queue = _load_yaml(source_queue)
    plan = build_volume_batch_plan(batch_id=batch_id, queue=queue, target_size=target_size)
    plan_path = out_root / "volume_batches" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    _write_yaml(plan_path, plan)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_pm_brief(plan), encoding="utf-8")
    if update_source_queue:
        _apply_queue_delta(source_queue, queue, plan, plan_path, packet_path)
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "plan": _relpath(plan_path),
            "pm_brief": _relpath(packet_path),
            "source_queue": _relpath(source_queue),
        },
        "summary": plan["summary"],
        "selected_source_ids": plan["selected_source_ids"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument("--no-update-source-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_volume_batch_plan(
        source_queue=args.source_queue,
        out_root=args.out_root,
        batch_id=args.batch_id,
        target_size=args.target_size,
        update_source_queue=not args.no_update_source_queue,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"volume batch plan: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
