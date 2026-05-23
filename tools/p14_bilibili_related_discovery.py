#!/usr/bin/env python3
"""Discover P14 Bilibili source candidates from related-video recommendations.

This fallback lane starts from already useful seed videos, asks Bilibili's
related-video endpoint for adjacent BVs, fetches metadata with yt-dlp, and emits
the same source-candidate YAML consumed by ``p14_source_queue_expand.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

try:
    from tools.p14_bilibili_creator_discovery import fetch_video_hit
    from tools.p14_bilibili_source_discovery import (
        DEFAULT_BATTLE_DEX,
        DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
        DEFAULT_OUT_DIR,
        DEFAULT_SOURCE_QUEUE,
        _existing_source_keys,
        _extract_bvid,
        _load_move_names,
        _load_species_names,
        _load_yaml,
        _write_yaml,
        build_candidate,
        hard_reject_hit,
        has_roco_or_entity_signal,
        select_diverse_candidates,
    )
except ModuleNotFoundError:  # pragma: no cover - script-path execution
    from p14_bilibili_creator_discovery import fetch_video_hit
    from p14_bilibili_source_discovery import (
        DEFAULT_BATTLE_DEX,
        DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
        DEFAULT_OUT_DIR,
        DEFAULT_SOURCE_QUEUE,
        _existing_source_keys,
        _extract_bvid,
        _load_move_names,
        _load_species_names,
        _load_yaml,
        _write_yaml,
        build_candidate,
        hard_reject_hit,
        has_roco_or_entity_signal,
        select_diverse_candidates,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_ID = f"p14_bili_related_discovery_{date.today().isoformat()}"
RELATED_ENDPOINT = "https://api.bilibili.com/x/web-interface/archive/related"
SCORE_RE = re.compile(r"score=(\d+)")


@dataclass(frozen=True)
class RelatedSeed:
    bvid: str
    seed_source_id: str = ""
    title: str = ""


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _source_by_id(source_queue_path: Path, source_id: str) -> dict[str, Any] | None:
    queue = _load_yaml(source_queue_path)
    for source in queue.get("sources") or []:
        if str(source.get("source_id") or "") == source_id:
            return dict(source)
    return None


def related_seeds_from_args(*, source_queue_path: Path, bvids: list[str], seed_source_ids: list[str]) -> list[RelatedSeed]:
    seeds: list[RelatedSeed] = []
    seen: set[str] = set()
    for raw_bvid in bvids:
        bvid = _extract_bvid(raw_bvid) or raw_bvid.strip()
        if bvid and bvid not in seen:
            seeds.append(RelatedSeed(bvid=bvid))
            seen.add(bvid)
    for source_id in seed_source_ids:
        source = _source_by_id(source_queue_path, source_id)
        if not source:
            continue
        bvid = _extract_bvid(str(source.get("url") or ""))
        if not bvid or bvid in seen:
            continue
        seeds.append(RelatedSeed(bvid=bvid, seed_source_id=source_id, title=str(source.get("title") or "")))
        seen.add(bvid)
    return seeds


def parse_related_bvids(response_text: str) -> list[str]:
    payload = json.loads(response_text)
    if int(payload.get("code") or 0) != 0:
        return []
    bvids: list[str] = []
    for item in payload.get("data") or []:
        bvid = str(item.get("bvid") or "").strip()
        if bvid and bvid not in bvids:
            bvids.append(bvid)
    return bvids


def fetch_related_bvids(seed: RelatedSeed, *, max_related: int, timeout: int) -> tuple[list[str], str]:
    query = urllib.parse.urlencode({"bvid": seed.bvid})
    request = urllib.request.Request(
        f"{RELATED_ENDPOINT}?{query}",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://www.bilibili.com/video/{seed.bvid}/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        return [], f"related_api_error={exc}"
    try:
        bvids = parse_related_bvids(text)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return [], f"related_api_parse_error={exc}"
    return bvids[:max_related], ""


def discover_related_candidates(
    *,
    seeds: list[RelatedSeed],
    max_related_per_seed: int,
    max_candidates: int,
    min_score: int,
    source_queue_path: Path,
    battle_dex_path: Path,
    timeout: int,
    use_chrome_cookies: bool = False,
    max_per_uploader: int = DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing = _existing_source_keys(source_queue_path)
    species_names = _load_species_names(battle_dex_path)
    move_names = _load_move_names(battle_dex_path)
    candidates_with_score: list[tuple[int, dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []
    seed_reports: list[dict[str, Any]] = []
    seen: set[str] = set()

    for seed in seeds:
        related_bvids, diagnostics = fetch_related_bvids(seed, max_related=max_related_per_seed, timeout=timeout)
        fetched = 0
        for bvid in related_bvids:
            if bvid == seed.bvid:
                skipped.append({"bvid": bvid, "reason": "same_as_seed", "seed_bvid": seed.bvid})
                continue
            if bvid in seen:
                skipped.append({"bvid": bvid, "reason": "duplicate_in_related_results", "seed_bvid": seed.bvid})
                continue
            seen.add(bvid)
            if (bvid, None) in existing:
                skipped.append({"bvid": bvid, "reason": "duplicate_existing_queue", "seed_bvid": seed.bvid})
                continue
            query_label = f"related_video:{seed.seed_source_id or seed.bvid}"
            hit, metadata_diagnostics = fetch_video_hit(
                bvid,
                query_label=query_label,
                timeout=timeout,
                use_chrome_cookies=use_chrome_cookies,
            )
            fetched += 1
            if not hit:
                skipped.append({"bvid": bvid, "reason": "metadata_fetch_failed", "seed_bvid": seed.bvid, "diagnostics": metadata_diagnostics[:200]})
                continue
            hard_reject_reason = hard_reject_hit(hit)
            if hard_reject_reason:
                skipped.append({"bvid": bvid, "title": hit.title, "reason": hard_reject_reason, "seed_bvid": seed.bvid})
                continue
            candidate = build_candidate(hit, species_names, move_names)
            candidate["discovered_by"] = "agent_related_video_api"
            candidate["discovery_reason"] = (
                f"Agent discovered 洛克王国世界PVP Bilibili source from related-video recommendations; "
                f"seed_source={seed.seed_source_id or seed.bvid}."
            )
            candidate["notes"] = f"{candidate.get('notes')}; related_seed_bvid={seed.bvid}; seed_source={seed.seed_source_id or 'direct'}"
            if not has_roco_or_entity_signal(hit, candidate):
                skipped.append({"bvid": bvid, "title": hit.title, "reason": "not_roco_or_a_layer_entity", "seed_bvid": seed.bvid})
                continue
            match = SCORE_RE.search(str(candidate.get("notes") or ""))
            score = int(match.group(1)) if match else 0
            if score < min_score:
                skipped.append({"bvid": bvid, "title": hit.title, "reason": f"score_below_{min_score}", "score": score, "seed_bvid": seed.bvid})
                continue
            candidates_with_score.append((score, candidate))

        seed_reports.append(
            {
                "seed_bvid": seed.bvid,
                "seed_source_id": seed.seed_source_id,
                "seed_title": seed.title,
                "related_bvid_count": len(related_bvids),
                "metadata_fetch_count": fetched,
                "diagnostics": diagnostics,
            }
        )

    candidates_with_score.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(str(item[1].get("priority")), 3),
            -item[0],
            str(item[1].get("published_at") or ""),
            str(item[1].get("title") or ""),
        )
    )
    selected, diversity_skipped, diversity_summary = select_diverse_candidates(
        candidates_with_score,
        max_candidates=max_candidates,
        max_per_bvid=1,
        max_per_uploader=max_per_uploader,
    )
    report = {
        "seed_count": len(seeds),
        "candidate_count_before_cap": len(candidates_with_score),
        "candidate_count_after_cap": len(selected),
        "skipped_count": len(skipped),
        "diversity_skipped_count": len(diversity_skipped),
        "diversity": {
            **diversity_summary,
            "max_candidates_per_bvid": 1,
            "max_candidates_per_uploader": max_per_uploader,
        },
        "seeds": seed_reports,
        "skipped": [*skipped[:160], *diversity_skipped[:50]],
    }
    return selected, report


def render_related_discovery_report(payload: dict[str, Any]) -> str:
    report = payload.get("discovery_report") or {}
    skipped = report.get("skipped") or []
    skip_reasons = Counter(str(item.get("reason") or "unknown") for item in skipped)
    lines = [
        f"# Related Video Discovery Yield: {payload['batch_id']}",
        "",
        "## 结论",
        f"- Seed {report.get('seed_count', 0)} 个；候选 {report.get('candidate_count_after_cap', 0)} 条；跳过 {report.get('skipped_count', 0)} 条。",
        f"- Diversity：unique BV {((report.get('diversity') or {}).get('selected_unique_bvid_count', 0))}；unique uploader {((report.get('diversity') or {}).get('selected_unique_uploader_count', 0))}；diversity skipped {report.get('diversity_skipped_count', 0)}。",
        "- 这些只是 source queue 候选，不是证据；进入队列后仍要过字幕/ASR、AB 精校、evidence foundation、Set Inventory。",
        "",
        "## Related Funnel",
    ]
    for item in report.get("seeds") or []:
        diag = str(item.get("diagnostics") or "").splitlines()[0] if item.get("diagnostics") else ""
        suffix = f"；diag={diag[:80]}" if diag else ""
        label = item.get("seed_source_id") or item.get("seed_bvid")
        lines.append(
            f"- `{label}`：related={item.get('related_bvid_count', 0)}；metadata_fetch={item.get('metadata_fetch_count', 0)}{suffix}"
        )

    lines.extend(["", "## Skip Reasons"])
    if not skip_reasons:
        lines.append("- 无。")
    for reason, count in skip_reasons.most_common(12):
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Candidate Preview"])
    candidates = payload.get("candidates") or []
    if not candidates:
        lines.append("- 无。")
    for candidate in candidates[:24]:
        lines.append(f"- [{candidate.get('source_id')}]({candidate.get('url')}): {candidate.get('title')}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--bvid", action="append", default=[])
    parser.add_argument("--seed-source-id", action="append", default=[])
    parser.add_argument("--max-related-per-seed", type=int, default=20)
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--min-score", type=int, default=7)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--battle-dex", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--use-chrome-cookies", action="store_true")
    parser.add_argument("--max-candidates-per-uploader", type=int, default=DEFAULT_MAX_CANDIDATES_PER_UPLOADER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    seeds = related_seeds_from_args(source_queue_path=args.source_queue, bvids=args.bvid, seed_source_ids=args.seed_source_id)
    candidates, report = discover_related_candidates(
        seeds=seeds,
        max_related_per_seed=args.max_related_per_seed,
        max_candidates=args.max_candidates,
        min_score=args.min_score,
        source_queue_path=args.source_queue,
        battle_dex_path=args.battle_dex,
        timeout=args.timeout,
        use_chrome_cookies=args.use_chrome_cookies,
        max_per_uploader=args.max_candidates_per_uploader,
    )
    payload = {
        "schema_version": "p14.source_candidates.v0",
        "batch_id": args.batch_id,
        "created_at": date.today().isoformat(),
        "runtime_allowed": False,
        "discovery_method": "bilibili_related_video_api",
        "discovery_notes": [
            "Discovery output is queue substrate only.",
            "Run p14_source_queue_expand.py before ingest; do not treat this file as evidence.",
            "Related-video mining is a fallback for search-page instability and must still pass PvP boundary gates.",
        ],
        "related_seeds": [seed.__dict__ for seed in seeds],
        "max_related_per_seed": args.max_related_per_seed,
        "discovery_report": report,
        "candidates": candidates,
    }
    out_path = args.out_dir / f"{args.batch_id}_candidates.yaml"
    _write_yaml(out_path, payload)
    packet_path = args.out_dir.parent / "review_packets" / f"{args.batch_id}_related_discovery_yield.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_related_discovery_report(payload), encoding="utf-8")

    summary = {
        "batch_id": args.batch_id,
        "runtime_allowed": False,
        "candidate_file": _relpath(out_path),
        "pm_brief": _relpath(packet_path),
        "seed_count": len(seeds),
        "candidate_count": len(candidates),
        "skipped_count": report["skipped_count"],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(summary)


if __name__ == "__main__":
    main()
