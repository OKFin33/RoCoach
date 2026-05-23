#!/usr/bin/env python3
"""Append discovered P14 Bilibili sources to the source queue.

Discovery rows are planning substrate only. They decide what the agent may
ingest next, but they never become evidence or reviewed graph data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_BATCH_ID = f"phase1_source_queue_expansion_{date.today().isoformat()}"
DEFAULT_MAX_NEW_SOURCES_PER_BVID = 3

ALLOWED_SOURCE_TYPES = {
    "team_explainer",
    "matchup_counterplay",
    "mechanism_tutorial",
    "gameplay_replay",
    "tier_overview",
}
BOUNDARY_TERMS = (
    "pvp",
    "PVP",
    "天梯",
    "竞技场",
    "对战",
    "实战",
    "阵容",
    "配队",
    "队伍",
    "打法",
    "思路",
    "机制",
    "速度线",
    "配招",
    "配置",
    "技能搭配",
    "用法",
    "玩法",
    "攻略",
    "教学",
    "讲解",
    "养成",
    "推荐",
    "精灵学",
    "精灵详解",
    "上大师",
    "登顶",
    "洛神杯",
    "闪耀杯",
    "排位",
    "比赛",
    "决赛",
    "赛事",
    "冠军",
    "联攻",
    "平衡性",
    "强度排行",
    "调整",
)
ROCO_TERMS = ("洛克王国世界", "洛克王国", "洛手", "洛克", "洛神杯", "闪耀杯")
STRONG_PVP_TITLE_TERMS = (
    "pvp",
    "PVP",
    "天梯",
    "竞技场",
    "对战",
    "对局",
    "阵容",
    "配队",
    "队伍",
    "上分",
    "大师",
    "登顶",
    "洛神杯",
    "闪耀杯",
    "排位",
    "联攻",
    "比赛解说",
    "决赛",
)
OFF_BOUNDARY_PVE_TITLE_TERMS = ("通关", "单通", "单刷", "必过", "秒过", "速刷", "boss", "Boss", "BOSS", "命定", "低练度", "大世界", "待机", "剧情", "主线任务", "主线", "完成攻略", "孵蛋", "神奇的蛋", "蛋全攻略", "副本", "异色", "奇遇")
OFF_BOUNDARY_DEX_TITLE_TERMS = (
    "图鉴",
    "捕捉地点",
    "捕捉",
    "抓",
    "抓到",
    "抓宠",
    "抓精灵",
    "获取方式",
    "获取攻略",
    "全收集",
    "点击就送",
    "素材",
    "矿石",
    "矿",
    "矿教学",
    "材料",
    "点位",
    "线路",
)
OFF_BOUNDARY_RESOURCE_ROUTE_TITLE_TERMS = (
    "采集",
    "跑图",
    "路线",
    "资源路线",
    "资源点",
    "全图",
    "全地图",
    "地图探索",
    "宝箱",
    "收集路线",
    "开图",
)
OFF_BOUNDARY_ALWAYS_TITLE_TERMS = ("手柄", "摇杆", "配置包", "大合照", "奖牌", "孵蛋", "神奇的蛋", "完美蛋", "蛋全攻略")
OFF_BOUNDARY_EVENT_TITLE_TERMS = ("限定动作", "动作解锁", "解锁攻略", "绝版", "白嫖", "炫彩", "奖励", "手柄", "摇杆", "配置包", "大合照", "奖牌")
BV_RE = re.compile(r"(BV[0-9A-Za-z]+)")


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


def _extract_bvid(url: str) -> str | None:
    match = BV_RE.search(url or "")
    if not match:
        return None
    return match.group(1)


def _extract_page_index(url: str, candidate: dict[str, Any] | None = None) -> int | None:
    if candidate and candidate.get("anthology_page_index"):
        try:
            value = int(candidate["anthology_page_index"])
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None
    parsed = urlsplit(url or "")
    page_value = (parse_qs(parsed.query).get("p") or [None])[0]
    if not page_value:
        match = re.search(r"_p(\d+)", url or "")
        page_value = match.group(1) if match else None
    if not page_value:
        return None
    try:
        value = int(page_value)
    except ValueError:
        return None
    return value if value > 0 else None


def _source_key(url: str, candidate: dict[str, Any] | None = None) -> tuple[str, int | None] | None:
    bvid = _extract_bvid(url)
    if not bvid:
        return None
    page_index = _extract_page_index(url, candidate)
    return (bvid, page_index if page_index and page_index > 1 else None)


def _canonical_bilibili_url(url: str) -> str:
    bvid = _extract_bvid(url)
    if bvid:
        page_index = _extract_page_index(url)
        query = f"?{urlencode({'p': page_index})}" if page_index and page_index > 1 else ""
        return f"https://www.bilibili.com/video/{bvid}/{query}"
    return url


def _source_text(source: dict[str, Any]) -> str:
    fields = [
        source.get("source_id"),
        source.get("title"),
        source.get("source_type"),
    ]
    fields.extend(source.get("target_entities") or [])
    fields.extend(source.get("target_moves") or [])
    return " ".join(str(item) for item in fields if item)


def _looks_roco_pvp(source: dict[str, Any]) -> bool:
    # Do not trust generated fields such as target_archetype/discovery_reason for
    # boundary checks. They often contain the search query and can inject "PVP"
    # into an otherwise off-boundary result.
    title = str(source.get("title") or "")
    title_lower = title.lower()
    entities = _normalize_list(source.get("target_entities"))
    moves = _normalize_list(source.get("target_moves"))
    has_roco = any(term in title for term in ROCO_TERMS) or bool(entities) or bool(moves)
    battle_title_terms = (
        *BOUNDARY_TERMS,
        "对线",
        "翻盘",
        "胜率",
        "连胜",
        "高分",
        "排位",
        "周报",
        "日报",
        "环境",
        "版本答案",
        "热门",
        "科研",
        "斩杀线",
        "平衡队",
        "毒队",
        "火队",
        "地刺队",
        "沙暴队",
        "格斗队",
        "武队",
        "洛神杯",
        "闪耀杯",
        "排位",
        "比赛",
        "决赛",
        "赛事",
        "冠军",
        "联攻",
        "平衡性",
        "强度排行",
        "调整",
    )
    has_battle = bool(moves) or any(term in title or term.lower() in title_lower for term in battle_title_terms)
    return has_roco and has_battle


def _has_off_boundary_title(source: dict[str, Any]) -> bool:
    title = str(source.get("title") or "")
    if any(term in title for term in OFF_BOUNDARY_ALWAYS_TITLE_TERMS):
        return True
    if any(term in title for term in OFF_BOUNDARY_RESOURCE_ROUTE_TITLE_TERMS):
        return True
    title_has_strong_pvp = any(term in title for term in STRONG_PVP_TITLE_TERMS)
    if title_has_strong_pvp:
        return False
    if any(term in title for term in OFF_BOUNDARY_PVE_TITLE_TERMS):
        return True
    if any(term in title for term in OFF_BOUNDARY_DEX_TITLE_TERMS):
        return True
    if any(term in title for term in OFF_BOUNDARY_EVENT_TITLE_TERMS):
        return True
    if any(term in title for term in ("PVE", "pve")) and "PVP" not in title and "pvp" not in title:
        return True
    return False


def _validate_candidate(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for field in ("source_id", "url", "title", "source_type"):
        if not candidate.get(field):
            errors.append(f"missing_{field}")
    platform = str(candidate.get("platform") or "bilibili")
    if platform != "bilibili":
        errors.append("platform_not_bilibili")
    parsed = urlsplit(str(candidate.get("url") or ""))
    if parsed.netloc and "bilibili.com" not in parsed.netloc:
        errors.append("url_not_bilibili")
    if not _extract_bvid(str(candidate.get("url") or "")):
        errors.append("missing_bvid")
    if str(candidate.get("source_type") or "") not in ALLOWED_SOURCE_TYPES:
        errors.append("invalid_source_type")
    if _has_off_boundary_title(candidate):
        errors.append("outside_pvp_battle_boundary")
    if not _looks_roco_pvp(candidate):
        errors.append("outside_pvp_battle_boundary")
    return not errors, errors


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)]


def _normalize_source(candidate: dict[str, Any]) -> dict[str, Any]:
    prior = dict(candidate.get("source_quality_prior") or {})
    prior.setdefault("likely_subtitle_available", "unknown")
    prior.setdefault("likely_noise", "medium")
    prior["promotion_bias"] = _normalize_list(prior.get("promotion_bias"))

    source: dict[str, Any] = {
        "source_id": str(candidate["source_id"]),
        "url": _canonical_bilibili_url(str(candidate["url"])),
        "platform": "bilibili",
        "title": str(candidate["title"]),
    }
    for field in ("uploader", "published_at"):
        if candidate.get(field):
            source[field] = str(candidate[field])
    source.update(
        {
            "source_type": str(candidate["source_type"]),
            "target_archetype": str(candidate.get("target_archetype") or candidate["title"]),
            "target_entities": _normalize_list(candidate.get("target_entities")),
            "discovery_reason": str(candidate.get("discovery_reason") or "Agent discovered PvP/battle-related Bilibili source for volume-lane ingest."),
            "expected_value": str(candidate.get("expected_value") or "medium"),
            "priority": str(candidate.get("priority") or "medium"),
            "ingest_status": "queued",
            "source_quality_prior": prior,
            "discovery_meta": {
                "discovered_by": str(candidate.get("discovered_by") or "agent_web_search"),
                "discovered_at": str(candidate.get("discovered_at") or date.today().isoformat()),
            },
        }
    )
    target_moves = _normalize_list(candidate.get("target_moves"))
    if target_moves:
        source["target_moves"] = target_moves
    if candidate.get("notes"):
        source["notes"] = str(candidate["notes"])
    page_index = _extract_page_index(source["url"], candidate)
    if page_index and page_index > 1:
        source["anthology_page_index"] = page_index
        source["source_quality_prior"]["promotion_bias"].append("anthology_page_source")
    return source


def _existing_indexes(sources: list[dict[str, Any]]) -> tuple[set[str], set[tuple[str, int | None]], set[str]]:
    source_ids = {str(source.get("source_id")) for source in sources if source.get("source_id")}
    keys: set[tuple[str, int | None]] = set()
    whole_bvids: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "")
        key = _source_key(url, source)
        if not key:
            continue
        keys.add(key)
        if key[1] is None:
            whole_bvids.add(key[0])
    return source_ids, keys, whole_bvids


def build_expansion_audit(
    *,
    batch_id: str,
    queue: dict[str, Any],
    candidate_payload: dict[str, Any],
    max_new_sources_per_bvid: int = DEFAULT_MAX_NEW_SOURCES_PER_BVID,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    existing_sources = list(queue.get("sources") or [])
    existing_ids, existing_keys, existing_whole_bvids = _existing_indexes(existing_sources)
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, int | None]] = set()
    added_bvid_counts: Counter[str] = Counter()
    added_sources: list[dict[str, Any]] = []
    added_views: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidate_payload.get("candidates") or [], start=1):
        candidate = dict(candidate or {})
        source_id = str(candidate.get("source_id") or "")
        url = str(candidate.get("url") or "")
        bvid = _extract_bvid(url)
        key = _source_key(url, candidate)
        ok, errors = _validate_candidate(candidate)
        if not ok:
            skipped.append({"index": index, "source_id": source_id or None, "url": candidate.get("url"), "reasons": errors})
            continue
        if source_id in existing_ids:
            skipped.append({"index": index, "source_id": source_id, "url": candidate.get("url"), "reasons": ["duplicate_source_id"]})
            continue
        if key and (key in existing_keys or (key[1] is None and key[0] in existing_whole_bvids)):
            skipped.append({"index": index, "source_id": source_id, "url": candidate.get("url"), "bvid": bvid, "page_index": key[1], "reasons": ["duplicate_bvid_page"]})
            continue
        if source_id in seen_ids or (key and key in seen_keys):
            skipped.append({"index": index, "source_id": source_id, "url": candidate.get("url"), "bvid": bvid, "page_index": key[1] if key else None, "reasons": ["duplicate_in_batch"]})
            continue
        if max_new_sources_per_bvid > 0 and bvid and added_bvid_counts[bvid] >= max_new_sources_per_bvid:
            skipped.append({"index": index, "source_id": source_id, "url": candidate.get("url"), "bvid": bvid, "page_index": key[1] if key else None, "reasons": ["diversity_bvid_cap"]})
            continue

        source = _normalize_source(candidate)
        added_sources.append(source)
        added_views.append(
            {
                "source_id": source["source_id"],
                "title": source["title"],
                "url": source["url"],
                "source_type": source["source_type"],
                "target_archetype": source["target_archetype"],
                "priority": source["priority"],
                "expected_value": source["expected_value"],
            }
        )
        seen_ids.add(source_id)
        if key:
            seen_keys.add(key)
        if bvid:
            added_bvid_counts[bvid] += 1

    type_mix = Counter(str(item["source_type"]) for item in added_sources)
    queue_after = len(existing_sources) + len(added_sources)
    queued_after = sum(
        1
        for source in [*existing_sources, *added_sources]
        if str(source.get("ingest_status") or "queued") == "queued"
    )
    audit = {
        "schema_version": "p14.source_queue_expansion.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "candidate_batch_id": candidate_payload.get("batch_id"),
        "summary": {
            "candidate_count": len(candidate_payload.get("candidates") or []),
            "added_count": len(added_sources),
            "skipped_count": len(skipped),
            "source_count_before": len(existing_sources),
            "source_count_after": queue_after,
            "queued_source_count_after": queued_after,
            "source_type_mix_added": dict(sorted(type_mix.items())),
            "unique_bvid_added_count": len(added_bvid_counts),
            "max_new_sources_per_bvid": max_new_sources_per_bvid,
        },
        "added_sources": added_views,
        "skipped_candidates": skipped,
        "policy_notes": [
            "source queue expansion is discovery substrate only",
            "new rows remain ingest_status=queued until subtitle/ASR ingest succeeds",
            "do not treat discovered metadata as strategic evidence",
        ],
    }
    return audit, added_sources


def render_pm_brief(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        f"# Source Queue Expansion: {audit['batch_id']}",
        "",
        "## 结论",
        f"- 新增 {summary['added_count']} 条待抓源；当前 queued source 共 {summary['queued_source_count_after']} 条。",
        "- 这些只是抓取队列，不是证据；后续必须经过字幕/ASR、AB 精校、evidence foundation、Set Inventory。",
        "- 重复视频、非 B 站源、非 PVP/对战边界内容已在队列层跳过。",
        "",
        "## 新增来源",
    ]
    if not audit.get("added_sources"):
        lines.append("- 无。")
    for item in audit.get("added_sources") or []:
        lines.append(
            f"- [{item['source_id']}]({item['url']})：{item['title']}；类型 {item['source_type']}；目标 {item['target_archetype']}。"
        )

    lines.extend(["", "## 跳过"])
    if not audit.get("skipped_candidates"):
        lines.append("- 无。")
    for item in audit.get("skipped_candidates") or []:
        reasons = "、".join(item.get("reasons") or [])
        label = item.get("source_id") or item.get("url") or f"candidate#{item.get('index')}"
        lines.append(f"- {label}：{reasons}")

    lines.extend(
        [
            "",
            "## 下一步",
            "先跑 gap fill，让工具从 queued 池里挑 20-30 批次的优先级；然后才进入字幕/ASR 和 Set Inventory。PM 不需要看这些代码，只需要看后续 dashboard 的异常和新 promotion 候选。",
        ]
    )
    return "\n".join(lines) + "\n"


def _apply_queue_delta(
    queue_path: Path,
    queue: dict[str, Any],
    audit: dict[str, Any],
    added_sources: list[dict[str, Any]],
    audit_path: Path,
    packet_path: Path,
) -> None:
    queue.setdefault("sources", [])
    queue["sources"].extend(added_sources)
    queue["latest_source_queue_expansion"] = {
        "batch_id": audit["batch_id"],
        "generated_at": audit["generated_at"],
        "added_source_ids": [source["source_id"] for source in added_sources],
        "added_count": audit["summary"]["added_count"],
        "skipped_count": audit["summary"]["skipped_count"],
        "queued_source_count_after": audit["summary"]["queued_source_count_after"],
        "audit_path": _relpath(audit_path),
        "review_packet": _relpath(packet_path),
        "runtime_allowed": False,
    }
    _write_yaml(queue_path, queue)


def run_source_queue_expand(
    *,
    candidate_file: Path,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    update_source_queue: bool = True,
    max_new_sources_per_bvid: int = DEFAULT_MAX_NEW_SOURCES_PER_BVID,
) -> dict[str, Any]:
    queue = _load_yaml(source_queue)
    candidate_payload = _load_yaml(candidate_file)
    audit, added_sources = build_expansion_audit(
        batch_id=batch_id,
        queue=queue,
        candidate_payload=candidate_payload,
        max_new_sources_per_bvid=max_new_sources_per_bvid,
    )
    audit_path = out_root / "audits" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    _write_yaml(audit_path, audit)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_pm_brief(audit), encoding="utf-8")
    if update_source_queue:
        _apply_queue_delta(source_queue, queue, audit, added_sources, audit_path, packet_path)
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "audit": _relpath(audit_path),
            "pm_brief": _relpath(packet_path),
            "source_queue": _relpath(source_queue),
        },
        "summary": audit["summary"],
        "added_source_ids": [source["source_id"] for source in added_sources],
        "skipped_count": audit["summary"]["skipped_count"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-file", type=Path, required=True)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--max-new-sources-per-bvid", type=int, default=DEFAULT_MAX_NEW_SOURCES_PER_BVID)
    parser.add_argument("--no-update-source-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_source_queue_expand(
        candidate_file=args.candidate_file,
        source_queue=args.source_queue,
        out_root=args.out_root,
        batch_id=args.batch_id,
        update_source_queue=not args.no_update_source_queue,
        max_new_sources_per_bvid=args.max_new_sources_per_bvid,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"source queue expansion: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
