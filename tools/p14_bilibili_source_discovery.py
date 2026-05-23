#!/usr/bin/env python3
"""Discover Bilibili source candidates for the P14 volume lane.

This tool is discovery substrate only. It searches Bilibili through yt-dlp's
`bilisearchN:` extractor, emits source candidate YAML, and lets
`p14_source_queue_expand.py` apply the queue/import validation gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_candidates"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
DEFAULT_BATCH_ID = f"p14_bili_discovery_{date.today().isoformat()}"
DEFAULT_MAX_CANDIDATES_PER_BVID = 3
DEFAULT_MAX_CANDIDATES_PER_UPLOADER = 8
BV_RE = re.compile(r"(BV[0-9A-Za-z]+)")

DEFAULT_QUERIES = [
    "洛克王国世界 PVP 小皮球",
    "洛克王国世界 PVP 寂灭骨龙",
    "洛克王国世界 PVP 音速犬",
    "洛克王国世界 PVP 翠顶夫人",
    "洛克王国世界 PVP 化蝶",
    "洛克王国世界 PVP 海豹船长",
    "洛克王国世界 PVP 圣羽翼王 魔攻",
    "洛克王国世界 PVP 奇丽花 队伍",
    "洛克王国世界 PVP 阵容 讲解",
    "洛克王国世界 PVP 周报 日报",
]

SOURCE_TYPE_RULES = [
    ("mechanism_tutorial", ("机制", "速度线", "规则", "必修课", "理论", "基础概念", "联攻", "小技巧")),
    ("tier_overview", ("周报", "日报", "排行", "排名", "T0", "t0", "版本答案", "热门", "阵容一览", "环境", "平衡性", "调整", "强度")),
    ("matchup_counterplay", ("克制", "反制", "对线", "内战", "对局", "打不过", "打", "VS", "vs", "翻盘")),
    ("team_explainer", ("攻略", "教学", "讲解", "配招", "配置", "养成", "阵容", "队伍", "配队", "推荐", "打法", "思路", "上分")),
    ("gameplay_replay", ("实战", "记录", "直播切片", "天梯", "洛神杯", "闪耀杯", "比赛", "决赛", "赛事", "解说")),
]

BATTLE_TERMS = (
    "pvp",
    "PVP",
    "天梯",
    "竞技场",
    "对战",
    "对局",
    "实战",
    "阵容",
    "配队",
    "队伍",
    "打法",
    "思路",
    "机制",
    "攻略",
    "教学",
    "上分",
    "大师",
    "登顶",
    "T0",
    "t0",
    "洛神杯",
    "闪耀杯",
    "排位",
    "比赛",
    "决赛",
    "赛事",
    "冠军",
    "联攻",
    "平衡性",
    "强度",
    "调整",
)
EXPLICIT_PVP_TERMS = (
    "pvp",
    "PVP",
    "天梯",
    "竞技场",
    "对战",
    "对局",
    "实战",
    "阵容",
    "配队",
    "队伍",
    "打法",
    "上分",
    "大师",
    "登顶",
    "洛神杯",
    "闪耀杯",
    "排位",
    "比赛",
    "赛事",
    "联攻",
)
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
ROCO_TERMS = ("洛克王国世界", "洛克王国", "洛手", "洛克", "洛神杯", "闪耀杯")
META_BATTLE_TERMS = ("联攻", "平衡性", "强度排行", "调整", "小技巧", "机制", "理论", "基础概念")
NEGATIVE_TERMS = (
    "待机",
    "大世界探索",
    "大世界",
    "剧情",
    "主线任务",
    "主线",
    "日常",
    "开箱",
    "抽卡",
    "音乐",
    "壁纸",
    "手柄",
    "摇杆",
    "配置包",
    "大合照",
    "奖牌",
    "通关",
    "单通",
    "单刷",
    "必过",
    "秒过",
    "速刷",
    "boss",
    "Boss",
    "BOSS",
    "命定",
    "低练度",
    "图鉴",
    "捕捉地点",
    "抓",
    "抓到",
    "抓宠",
    "抓精灵",
    "获取攻略",
    "点击就送",
    "全收集",
    "素材",
    "矿石",
    "矿",
    "矿教学",
    "材料",
    "点位",
    "线路",
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
    "限定动作",
    "动作解锁",
    "解锁攻略",
    "绝版",
    "白嫖",
    "炫彩",
    "奖励",
    "完成攻略",
    "孵蛋",
    "神奇的蛋",
    "蛋全攻略",
    "副本",
    "异色",
    "奇遇",
)
ALIAS_TO_ENTITY = {
    "翼王": "圣羽翼王",
    "水刃翼王": "圣羽翼王",
    "火狗": "音速犬",
    "骨龙": "寂灭骨龙",
    "翠顶": "翠顶夫人",
}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


@dataclass(frozen=True)
class SearchHit:
    bvid: str
    title: str
    uploader: str
    timestamp: int | None
    view_count: int | None
    like_count: int | None
    duration: float | None
    tags: list[str]
    query: str
    page_index: int | None = None


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


def _extract_bvid(value: str) -> str | None:
    match = BV_RE.search(value or "")
    return match.group(1) if match else None


def _extract_page_index(value: str) -> int | None:
    match = re.search(r"(?:_p|[?&]p=)(\d+)", value or "")
    if not match:
        return None
    try:
        page_index = int(match.group(1))
    except ValueError:
        return None
    return page_index if page_index > 0 else None


def _source_key(bvid: str, page_index: int | None) -> tuple[str, int | None]:
    return (bvid, page_index if page_index and page_index > 1 else None)


def _existing_source_keys(source_queue_path: Path) -> set[tuple[str, int | None]]:
    queue = _load_yaml(source_queue_path)
    keys: set[tuple[str, int | None]] = set()
    for source in queue.get("sources") or []:
        url = str(source.get("url") or "")
        bvid = _extract_bvid(url)
        if bvid:
            page_index = source.get("anthology_page_index") or _extract_page_index(url)
            keys.add(_source_key(bvid, int(page_index) if page_index else None))
    return keys


def _load_species_names(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT display_name
            FROM species_form
            WHERE display_name IS NOT NULL AND LENGTH(display_name) >= 2
            ORDER BY LENGTH(display_name) DESC, display_name
            """
        ).fetchall()
    return [str(row[0]) for row in rows if row[0]]


def _load_move_names(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT move_name
            FROM move
            WHERE move_name IS NOT NULL AND LENGTH(move_name) >= 2
            ORDER BY LENGTH(move_name) DESC, move_name
            """
        ).fetchall()
    return [str(row[0]) for row in rows if row[0]]


def _creator_seed_queries(source_queue_path: Path, *, limit: int) -> list[str]:
    if limit <= 0:
        return []
    queue = _load_yaml(source_queue_path)
    scores: Counter[str] = Counter()
    for source in queue.get("sources") or []:
        uploader = str(source.get("uploader") or "").strip()
        if not uploader:
            continue
        status = str(source.get("ingest_status") or "")
        if status not in {"set_pipeline_processed", "evidence_foundation_ready"}:
            continue
        quality = (source.get("source_quality_prior") or {}).get("latest_evidence_foundation") or {}
        claim_count = int(quality.get("claim_atom_count") or 0)
        segment_count = int(quality.get("segment_count") or 0)
        scores[uploader] += max(1, claim_count * 4 + min(segment_count // 100, 8))
    queries: list[str] = []
    for uploader, _ in scores.most_common(limit):
        queries.append(f"{uploader} 洛克王国世界 PVP 阵容")
    return queries


def infer_source_type(title: str) -> str:
    for source_type, needles in SOURCE_TYPE_RULES:
        if any(needle in title for needle in needles):
            return source_type
    return "gameplay_replay"


def infer_entities(text: str, species_names: list[str]) -> list[str]:
    entities: list[str] = []
    for alias, entity in ALIAS_TO_ENTITY.items():
        if alias in text and entity not in entities:
            entities.append(entity)
    for name in species_names:
        if name in text and name not in entities:
            entities.append(name)
    return entities[:6]


def infer_terms(text: str, names: list[str], *, limit: int = 8) -> list[str]:
    terms: list[str] = []
    for name in names:
        if name in text and name not in terms:
            terms.append(name)
        if len(terms) >= limit:
            break
    return terms


def score_hit(hit: SearchHit, entities: list[str]) -> tuple[int, list[str]]:
    source_text = " ".join([hit.title, *hit.tags])
    score = 0
    reasons: list[str] = []
    if any(term in source_text for term in ROCO_TERMS):
        score += 3
        reasons.append("roco_related")
    if any(term in source_text for term in BATTLE_TERMS):
        score += 4
        reasons.append("battle_related")
    if entities:
        score += min(4, len(entities) * 2)
        reasons.append("a_layer_entity_mentioned")
    if any(term in source_text for term in META_BATTLE_TERMS):
        score += 2
        reasons.append("meta_battle_signal")
    if any(term in hit.title for term in ("攻略", "教学", "讲解", "配置", "配招", "阵容", "队伍", "周报", "日报")):
        score += 2
        reasons.append("likely_explainer")
    if hit.view_count and hit.view_count >= 10000:
        score += 1
        reasons.append("nontrivial_view_count")
    if any(term in hit.title for term in NEGATIVE_TERMS):
        score -= 5
        reasons.append("off_boundary_title_risk")
    if any(term in hit.title for term in ("PVE", "pve")) and "PVP" not in hit.title and "pvp" not in hit.title:
        score -= 3
        reasons.append("pve_without_pvp_title_risk")
    return score, reasons


def has_roco_or_entity_signal(hit: SearchHit, candidate: dict[str, Any]) -> bool:
    source_text = " ".join([hit.title, *hit.tags])
    return (
        any(term in source_text for term in ROCO_TERMS)
        or bool(candidate.get("target_entities"))
        or bool(candidate.get("target_moves"))
    )


def hard_reject_hit(hit: SearchHit) -> str | None:
    source_text = " ".join([hit.title, *hit.tags])
    has_explicit_pvp = any(term in source_text for term in EXPLICIT_PVP_TERMS)
    title_has_strong_pvp = any(term in hit.title for term in STRONG_PVP_TITLE_TERMS)
    if any(term in hit.title for term in ("孵蛋", "神奇的蛋", "完美蛋", "蛋全攻略")):
        return "off_boundary_breeding_or_resource_title"
    if any(term in hit.title for term in ("手柄", "摇杆", "配置包", "大合照", "奖牌")):
        return "off_boundary_non_battle_event_title"
    if any(term in hit.title for term in ("通关", "单通", "单刷", "必过", "秒过", "速刷", "boss", "Boss", "BOSS", "命定", "低练度", "大世界", "待机", "剧情", "主线任务", "主线", "完成攻略", "孵蛋", "神奇的蛋", "蛋全攻略", "副本", "异色", "奇遇")) and not title_has_strong_pvp:
        return "off_boundary_pve_or_non_pvp_title"
    if any(term in hit.title for term in ("采集", "跑图", "路线", "线路", "资源路线", "资源点", "全图", "全地图", "地图探索", "宝箱", "收集路线", "开图")):
        return "off_boundary_resource_route_title"
    if any(term in hit.title for term in ("图鉴", "捕捉地点", "捕捉", "抓", "抓到", "抓宠", "抓精灵", "获取方式", "获取攻略", "全收集", "点击就送", "素材", "矿石", "矿", "矿教学", "材料", "点位", "线路")) and not title_has_strong_pvp:
        return "off_boundary_dex_or_capture_title"
    if any(term in hit.title for term in ("限定动作", "动作解锁", "解锁攻略", "绝版", "白嫖", "炫彩", "奖励", "手柄", "摇杆", "配置包")) and not title_has_strong_pvp:
        return "off_boundary_non_battle_event_title"
    if any(term in hit.title for term in ("PVE", "pve")) and "PVP" not in hit.title and "pvp" not in hit.title:
        return "pve_without_pvp_title"
    return None


def likely_noise(score: int, hit: SearchHit) -> str:
    if score >= 10 and hit.duration and hit.duration >= 90:
        return "low"
    if score >= 7:
        return "medium"
    return "high"


def priority_for(score: int, source_type: str) -> str:
    if score >= 11 and source_type in {"team_explainer", "matchup_counterplay", "mechanism_tutorial", "tier_overview"}:
        return "high"
    if score >= 7:
        return "medium"
    return "low"


def _published_at(timestamp: int | None) -> str | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()


def source_id_for(bvid: str, page_index: int | None = None) -> str:
    canonical = _extract_bvid(bvid) or bvid
    suffix = f"_p{page_index:02d}" if page_index and page_index > 1 else ""
    return f"kgsrc_bili_{canonical.lower()}{suffix}"


def source_url_for(bvid: str, page_index: int | None = None) -> str:
    canonical = _extract_bvid(bvid) or bvid
    if page_index and page_index > 1:
        return f"https://www.bilibili.com/video/{canonical}/?p={page_index}"
    return f"https://www.bilibili.com/video/{canonical}/"


def build_candidate(hit: SearchHit, species_names: list[str], move_names: list[str] | None = None) -> dict[str, Any]:
    entity_text = " ".join([hit.title, *hit.tags])
    entities = infer_entities(entity_text, species_names)
    move_terms = infer_terms(entity_text, move_names or [])
    score, reasons = score_hit(hit, entities)
    if move_terms:
        score += min(3, len(move_terms))
        reasons.append("a_layer_move_mentioned")
    source_type = infer_source_type(hit.title)
    priority = priority_for(score, source_type)
    candidate: dict[str, Any] = {
        "source_id": source_id_for(hit.bvid, hit.page_index),
        "url": source_url_for(hit.bvid, hit.page_index),
        "platform": "bilibili",
        "title": hit.title,
        "source_type": source_type,
        "target_archetype": f"洛克王国世界PVP候选源：{hit.title}",
        "target_entities": entities,
        "priority": priority,
        "expected_value": "high" if priority == "high" else "medium" if priority == "medium" else "low",
        "discovered_by": "agent_bilisearch_yt_dlp",
        "discovered_at": date.today().isoformat(),
        "source_quality_prior": {
            "likely_subtitle_available": "unknown",
            "likely_noise": likely_noise(score, hit),
            "promotion_bias": reasons,
        },
        "discovery_reason": f"Agent discovered 洛克王国世界PVP Bilibili source via query `{hit.query}`; discovery score {score}.",
    }
    if hit.uploader and hit.uploader != "NA":
        candidate["uploader"] = hit.uploader
    if move_terms:
        candidate["target_moves"] = move_terms
    published_at = _published_at(hit.timestamp)
    if published_at:
        candidate["published_at"] = published_at
    if hit.page_index and hit.page_index > 1:
        candidate["anthology_page_index"] = hit.page_index
    candidate["notes"] = f"query={hit.query}; score={score}; views={hit.view_count or 'unknown'}; duration={hit.duration or 'unknown'}"
    return candidate


def _parse_optional_int(value: str) -> int | None:
    if not value or value == "NA":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_optional_float(value: str) -> float | None:
    if not value or value == "NA":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_search_line(line: str, query: str) -> SearchHit | None:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 8:
        return None
    bvid, title, uploader, timestamp, view_count, like_count, duration, tags_raw = parts
    canonical_bvid = _extract_bvid(bvid)
    if not canonical_bvid:
        return None
    page_index = _extract_page_index(bvid)
    try:
        tags = json.loads(tags_raw) if tags_raw and tags_raw != "NA" else []
    except json.JSONDecodeError:
        tags = []
    return SearchHit(
        bvid=canonical_bvid,
        page_index=page_index,
        title=title,
        uploader=uploader,
        timestamp=_parse_optional_int(timestamp),
        view_count=_parse_optional_int(view_count),
        like_count=_parse_optional_int(like_count),
        duration=_parse_optional_float(duration),
        tags=[str(item) for item in tags if item],
        query=query,
    )


def _candidate_bvid(candidate: dict[str, Any]) -> str:
    return _extract_bvid(str(candidate.get("url") or "")) or str(candidate.get("source_id") or "")


def _candidate_uploader(candidate: dict[str, Any]) -> str:
    uploader = str(candidate.get("uploader") or "").strip()
    return uploader if uploader and uploader != "NA" else ""


def select_diverse_candidates(
    candidates_with_score: list[tuple[int, dict[str, Any]]],
    *,
    max_candidates: int,
    max_per_bvid: int = DEFAULT_MAX_CANDIDATES_PER_BVID,
    max_per_uploader: int = DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    bvid_counts: Counter[str] = Counter()
    uploader_counts: Counter[str] = Counter()

    for score, candidate in candidates_with_score:
        if len(selected) >= max_candidates:
            break
        bvid = _candidate_bvid(candidate)
        uploader = _candidate_uploader(candidate)
        if max_per_bvid > 0 and bvid and bvid_counts[bvid] >= max_per_bvid:
            skipped.append(
                {
                    "bvid": bvid,
                    "source_id": candidate.get("source_id"),
                    "title": candidate.get("title"),
                    "reason": "diversity_bvid_cap",
                    "score": score,
                }
            )
            continue
        if max_per_uploader > 0 and uploader and uploader_counts[uploader] >= max_per_uploader:
            skipped.append(
                {
                    "bvid": bvid,
                    "uploader": uploader,
                    "source_id": candidate.get("source_id"),
                    "title": candidate.get("title"),
                    "reason": "diversity_uploader_cap",
                    "score": score,
                }
            )
            continue
        selected.append(candidate)
        if bvid:
            bvid_counts[bvid] += 1
        if uploader:
            uploader_counts[uploader] += 1

    return selected, skipped, {
        "selected_unique_bvid_count": len(bvid_counts),
        "selected_unique_uploader_count": len(uploader_counts),
    }


def run_bilisearch(
    query: str,
    *,
    per_query: int,
    timeout: int,
    use_chrome_cookies: bool = False,
    playlist_start: int = 1,
) -> tuple[list[SearchHit], str]:
    print_template = "%(id)s\t%(title)s\t%(uploader)s\t%(timestamp)s\t%(view_count)s\t%(like_count)s\t%(duration)s\t%(tags)j"
    playlist_end = playlist_start + per_query - 1
    extractor_count = max(per_query, playlist_end)
    command = [
        "yt-dlp",
        "--skip-download",
        "--playlist-start",
        str(playlist_start),
        "--playlist-end",
        str(playlist_end),
        "--no-warnings",
        "--print",
        print_template,
    ]
    if use_chrome_cookies:
        command.extend(["--cookies-from-browser", "chrome"])
    command.append(f"bilisearch{extractor_count}:{query}")
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return [], f"yt-dlp_timeout_after={timeout}s"
    hits = [hit for line in result.stdout.splitlines() for hit in [parse_search_line(line, query)] if hit]
    diagnostics = result.stderr.strip()
    if result.returncode != 0:
        diagnostics = "\n".join(part for part in [diagnostics, f"yt-dlp_exit={result.returncode}"] if part)
    return hits, diagnostics


def discover_candidates(
    *,
    queries: list[str],
    per_query: int,
    max_candidates: int,
    min_score: int,
    source_queue_path: Path,
    battle_dex_path: Path,
    timeout: int,
    use_chrome_cookies: bool = False,
    search_window_count: int = 1,
    auto_cookie_retry: bool = False,
    max_per_bvid: int = DEFAULT_MAX_CANDIDATES_PER_BVID,
    max_per_uploader: int = DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing = _existing_source_keys(source_queue_path)
    species_names = _load_species_names(battle_dex_path)
    move_names = _load_move_names(battle_dex_path)
    seen: set[tuple[str, int | None]] = set()
    candidates_with_score: list[tuple[int, dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []
    query_reports: list[dict[str, Any]] = []

    for query in queries:
        for window_index in range(max(1, search_window_count)):
            playlist_start = window_index * per_query + 1
            hits, diagnostics = run_bilisearch(
                query,
                per_query=per_query,
                timeout=timeout,
                use_chrome_cookies=use_chrome_cookies,
                playlist_start=playlist_start,
            )
            retried_with_cookies = False
            if auto_cookie_retry and not use_chrome_cookies and not hits and "412" in diagnostics:
                retried_with_cookies = True
                hits, retry_diagnostics = run_bilisearch(
                    query,
                    per_query=per_query,
                    timeout=timeout,
                    use_chrome_cookies=True,
                    playlist_start=playlist_start,
                )
                diagnostics = "\n".join(
                    part
                    for part in [
                        diagnostics,
                        "auto_cookie_retry=true",
                        retry_diagnostics,
                    ]
                    if part
                )
            query_reports.append(
                {
                    "query": query,
                    "window_index": window_index + 1,
                    "playlist_start": playlist_start,
                    "playlist_end": playlist_start + per_query - 1,
                    "hit_count": len(hits),
                    "used_chrome_cookies": bool(use_chrome_cookies or retried_with_cookies),
                    "diagnostics": diagnostics,
                }
            )
            for hit in hits:
                hit_key = _source_key(hit.bvid, hit.page_index)
                base_key = _source_key(hit.bvid, None)
                existing_duplicate = hit_key in existing or (hit.page_index in (None, 1) and base_key in existing)
                if existing_duplicate:
                    skipped.append(
                        {
                            "bvid": hit.bvid,
                            "page_index": hit.page_index,
                            "title": hit.title,
                            "reason": "duplicate_existing_queue",
                            "query": query,
                        }
                    )
                    continue
                if hit_key in seen:
                    skipped.append(
                        {
                            "bvid": hit.bvid,
                            "page_index": hit.page_index,
                            "title": hit.title,
                            "reason": "duplicate_in_search_results",
                            "query": query,
                        }
                    )
                    continue
                hard_reject_reason = hard_reject_hit(hit)
                if hard_reject_reason:
                    skipped.append({"bvid": hit.bvid, "page_index": hit.page_index, "title": hit.title, "reason": hard_reject_reason, "query": query})
                    seen.add(hit_key)
                    continue
                candidate = build_candidate(hit, species_names, move_names)
                if not has_roco_or_entity_signal(hit, candidate):
                    skipped.append({"bvid": hit.bvid, "page_index": hit.page_index, "title": hit.title, "reason": "not_roco_or_a_layer_entity", "query": query})
                    seen.add(hit_key)
                    continue
                score_match = re.search(r"score=(\d+)", str(candidate.get("notes") or ""))
                score = int(score_match.group(1)) if score_match else 0
                if score < min_score:
                    skipped.append({"bvid": hit.bvid, "page_index": hit.page_index, "title": hit.title, "reason": f"score_below_{min_score}", "score": score, "query": query})
                    seen.add(hit_key)
                    continue
                seen.add(hit_key)
                candidates_with_score.append((score, candidate))

    candidates_with_score.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(str(item[1].get("priority")), 3),
            -item[0],
            str(item[1].get("title")),
        )
    )
    selected, diversity_skipped, diversity_summary = select_diverse_candidates(
        candidates_with_score,
        max_candidates=max_candidates,
        max_per_bvid=max_per_bvid,
        max_per_uploader=max_per_uploader,
    )
    report = {
        "query_count": len(queries),
        "candidate_count_before_cap": len(candidates_with_score),
        "candidate_count_after_cap": len(selected),
        "skipped_count": len(skipped),
        "diversity_skipped_count": len(diversity_skipped),
        "diversity": {
            **diversity_summary,
            "max_candidates_per_bvid": max_per_bvid,
            "max_candidates_per_uploader": max_per_uploader,
        },
        "queries": query_reports,
        "skipped": [*skipped[:100], *diversity_skipped[:50]],
    }
    return selected, report


def _queries_from_args(args: argparse.Namespace) -> list[str]:
    queries = list(args.query or [])
    if args.query_file:
        payload = _load_yaml(Path(args.query_file))
        queries.extend(str(item) for item in payload.get("queries") or [] if item)
    if args.creator_seed_limit:
        queries.extend(_creator_seed_queries(args.source_queue, limit=args.creator_seed_limit))
    if not queries:
        queries = list(DEFAULT_QUERIES)
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))


def render_discovery_yield_report(payload: dict[str, Any]) -> str:
    report = payload.get("discovery_report") or {}
    skipped = report.get("skipped") or []
    skip_reasons = Counter(str(item.get("reason") or "unknown") for item in skipped)
    query_rows = report.get("queries") or []
    lines = [
        f"# Source Discovery Yield: {payload['batch_id']}",
        "",
        "## 结论",
        f"- Query {report.get('query_count', 0)} 个；search windows {len(query_rows)} 个；候选 {report.get('candidate_count_after_cap', 0)} 条；跳过 {report.get('skipped_count', 0)} 条。",
        f"- Diversity：unique BV {((report.get('diversity') or {}).get('selected_unique_bvid_count', 0))}；unique uploader {((report.get('diversity') or {}).get('selected_unique_uploader_count', 0))}；diversity skipped {report.get('diversity_skipped_count', 0)}。",
        "- 这些只是 source queue 候选，不是证据；进入队列后仍要过字幕/ASR、AB 精校、evidence foundation、Set Inventory。",
        "",
        "## Funnel",
    ]
    for item in query_rows[:24]:
        diag = str(item.get("diagnostics") or "").splitlines()[0] if item.get("diagnostics") else ""
        cookie = "cookies" if item.get("used_chrome_cookies") else "no-cookies"
        window = f"{item.get('playlist_start')}-{item.get('playlist_end')}"
        suffix = f"；diag={diag[:80]}" if diag else ""
        lines.append(f"- `{item.get('query')}` window {window}：hits={item.get('hit_count', 0)}；{cookie}{suffix}")
    if len(query_rows) > 24:
        lines.append(f"- ... 另有 {len(query_rows) - 24} 个窗口见 YAML audit。")

    lines.extend(["", "## Skip Reasons"])
    if not skip_reasons:
        lines.append("- 无。")
    for reason, count in skip_reasons.most_common(12):
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Candidate Preview"])
    candidates = payload.get("candidates") or []
    if not candidates:
        lines.append("- 无。")
    for candidate in candidates[:20]:
        page = f" p{candidate.get('anthology_page_index')}" if candidate.get("anthology_page_index") else ""
        lines.append(f"- [{candidate.get('source_id')}]({candidate.get('url')}){page}: {candidate.get('title')}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--query-file")
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--min-score", type=int, default=7)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--battle-dex", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--use-chrome-cookies", action="store_true")
    parser.add_argument("--auto-cookie-retry", action="store_true")
    parser.add_argument("--search-window-count", type=int, default=1)
    parser.add_argument("--creator-seed-limit", type=int, default=0)
    parser.add_argument("--max-candidates-per-bvid", type=int, default=DEFAULT_MAX_CANDIDATES_PER_BVID)
    parser.add_argument("--max-candidates-per-uploader", type=int, default=DEFAULT_MAX_CANDIDATES_PER_UPLOADER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    queries = _queries_from_args(args)
    candidates, report = discover_candidates(
        queries=queries,
        per_query=args.per_query,
        max_candidates=args.max_candidates,
        min_score=args.min_score,
        source_queue_path=args.source_queue,
        battle_dex_path=args.battle_dex,
        timeout=args.timeout,
        use_chrome_cookies=args.use_chrome_cookies,
        search_window_count=args.search_window_count,
        auto_cookie_retry=args.auto_cookie_retry,
        max_per_bvid=args.max_candidates_per_bvid,
        max_per_uploader=args.max_candidates_per_uploader,
    )
    payload = {
        "schema_version": "p14.source_candidates.v0",
        "batch_id": args.batch_id,
        "created_at": date.today().isoformat(),
        "runtime_allowed": False,
        "discovery_method": "yt_dlp_bilisearch_windowed",
        "discovery_notes": [
            "Discovery output is queue substrate only.",
            "Run p14_source_queue_expand.py before ingest; do not treat this file as evidence.",
        ],
        "queries": queries,
        "search_window_count": max(1, args.search_window_count),
        "creator_seed_limit": args.creator_seed_limit,
        "discovery_report": report,
        "candidates": candidates,
    }
    out_path = args.out_dir / f"{args.batch_id}_candidates.yaml"
    _write_yaml(out_path, payload)
    packet_path = args.out_dir.parent / "review_packets" / f"{args.batch_id}_discovery_yield.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_discovery_yield_report(payload), encoding="utf-8")

    summary = {
        "batch_id": args.batch_id,
        "runtime_allowed": False,
        "candidate_file": str(out_path.relative_to(REPO_ROOT)),
        "pm_brief": str(packet_path.relative_to(REPO_ROOT)),
        "query_count": len(queries),
        "candidate_count": len(candidates),
        "skipped_count": report["skipped_count"],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(summary)


if __name__ == "__main__":
    main()
