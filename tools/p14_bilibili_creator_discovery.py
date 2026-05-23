#!/usr/bin/env python3
"""Discover P14 Bilibili source candidates from trusted creator spaces.

This is a fallback lane for when Bilibili search is low-yield or unstable.
It mines upload lists from creators already seen in the source queue, fetches
per-video metadata, and emits the same source-candidate YAML consumed by
``p14_source_queue_expand.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

try:
    from tools.p14_bilibili_source_discovery import (
        DEFAULT_BATTLE_DEX,
        DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
        DEFAULT_OUT_DIR,
        DEFAULT_SOURCE_QUEUE,
        SearchHit,
        _existing_source_keys,
        _extract_bvid,
        _load_move_names,
        _load_species_names,
        _load_yaml,
        _write_yaml,
        build_candidate,
        hard_reject_hit,
        has_roco_or_entity_signal,
        parse_search_line,
        select_diverse_candidates,
    )
except ModuleNotFoundError:  # pragma: no cover - script-path execution
    from p14_bilibili_source_discovery import (
        DEFAULT_BATTLE_DEX,
        DEFAULT_MAX_CANDIDATES_PER_UPLOADER,
        DEFAULT_OUT_DIR,
        DEFAULT_SOURCE_QUEUE,
        SearchHit,
        _existing_source_keys,
        _extract_bvid,
        _load_move_names,
        _load_species_names,
        _load_yaml,
        _write_yaml,
        build_candidate,
        hard_reject_hit,
        has_roco_or_entity_signal,
        parse_search_line,
        select_diverse_candidates,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_ID = f"p14_bili_creator_discovery_{date.today().isoformat()}"
BV_RE = re.compile(r"(BV[0-9A-Za-z]+)")
PRINT_TEMPLATE = "%(id)s\t%(title)s\t%(uploader)s\t%(timestamp)s\t%(view_count)s\t%(like_count)s\t%(duration)s\t%(tags)j"


@dataclass(frozen=True)
class CreatorSeed:
    uploader_id: str
    uploader: str = ""
    seed_source_id: str = ""


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _run_yt_dlp(command: list[str], *, timeout: int) -> tuple[str, str, int]:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return "", f"yt-dlp_timeout_after={timeout}s", 124
    return result.stdout, result.stderr.strip(), result.returncode


def _source_by_id(source_queue_path: Path, source_id: str) -> dict[str, Any] | None:
    queue = _load_yaml(source_queue_path)
    for source in queue.get("sources") or []:
        if str(source.get("source_id") or "") == source_id:
            return dict(source)
    return None


def resolve_creator_from_video_url(url: str, *, timeout: int, use_chrome_cookies: bool = False) -> CreatorSeed | None:
    command = [
        "yt-dlp",
        "--skip-download",
        "--no-warnings",
        "--print",
        "%(uploader_id)s\t%(uploader)s",
    ]
    if use_chrome_cookies:
        command.extend(["--cookies-from-browser", "chrome"])
    command.append(url)
    stdout, _stderr, returncode = _run_yt_dlp(command, timeout=timeout)
    if returncode != 0:
        return None
    first = next((line for line in stdout.splitlines() if line.strip()), "")
    parts = first.split("\t")
    if not parts or not parts[0] or parts[0] == "NA":
        return None
    return CreatorSeed(uploader_id=parts[0], uploader=parts[1] if len(parts) > 1 and parts[1] != "NA" else "")


def creator_seeds_from_args(
    *,
    source_queue_path: Path,
    uploader_ids: list[str],
    seed_source_ids: list[str],
    timeout: int,
    use_chrome_cookies: bool = False,
) -> list[CreatorSeed]:
    seeds: list[CreatorSeed] = []
    seen: set[str] = set()
    for uploader_id in uploader_ids:
        uploader_id = uploader_id.strip()
        if uploader_id and uploader_id not in seen:
            seeds.append(CreatorSeed(uploader_id=uploader_id))
            seen.add(uploader_id)

    for source_id in seed_source_ids:
        source = _source_by_id(source_queue_path, source_id)
        if not source:
            continue
        seed = resolve_creator_from_video_url(str(source.get("url") or ""), timeout=timeout, use_chrome_cookies=use_chrome_cookies)
        if not seed or seed.uploader_id in seen:
            continue
        seeds.append(CreatorSeed(uploader_id=seed.uploader_id, uploader=seed.uploader, seed_source_id=source_id))
        seen.add(seed.uploader_id)
    return seeds


def run_creator_space(
    seed: CreatorSeed,
    *,
    max_videos: int,
    timeout: int,
    use_chrome_cookies: bool = False,
) -> tuple[list[str], str]:
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end",
        str(max_videos),
        "--no-warnings",
        "--print",
        "%(id)s",
    ]
    if use_chrome_cookies:
        command.extend(["--cookies-from-browser", "chrome"])
    command.append(f"https://space.bilibili.com/{seed.uploader_id}/video")
    stdout, stderr, returncode = _run_yt_dlp(command, timeout=timeout)
    diagnostics = stderr
    if returncode != 0:
        diagnostics = "\n".join(part for part in [diagnostics, f"yt-dlp_exit={returncode}"] if part)
    bvids: list[str] = []
    for line in stdout.splitlines():
        bvid = _extract_bvid(line.strip())
        if bvid and bvid not in bvids:
            bvids.append(bvid)
    return bvids, diagnostics


def fetch_video_hit(
    bvid: str,
    *,
    query_label: str,
    timeout: int,
    use_chrome_cookies: bool = False,
) -> tuple[SearchHit | None, str]:
    command = [
        "yt-dlp",
        "--skip-download",
        "--no-warnings",
        "--print",
        PRINT_TEMPLATE,
    ]
    if use_chrome_cookies:
        command.extend(["--cookies-from-browser", "chrome"])
    command.append(f"https://www.bilibili.com/video/{bvid}/")
    stdout, stderr, returncode = _run_yt_dlp(command, timeout=timeout)
    diagnostics = stderr
    if returncode != 0:
        diagnostics = "\n".join(part for part in [diagnostics, f"yt-dlp_exit={returncode}"] if part)
    for line in stdout.splitlines():
        hit = parse_search_line(line, query_label)
        if hit:
            return hit, diagnostics
    return None, diagnostics or "metadata_parse_empty"


def discover_creator_candidates(
    *,
    seeds: list[CreatorSeed],
    max_videos_per_creator: int,
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
    creator_reports: list[dict[str, Any]] = []
    seen: set[str] = set()

    for seed in seeds:
        bvids, diagnostics = run_creator_space(
            seed,
            max_videos=max_videos_per_creator,
            timeout=timeout,
            use_chrome_cookies=use_chrome_cookies,
        )
        fetched = 0
        for bvid in bvids:
            if bvid in seen:
                skipped.append({"bvid": bvid, "reason": "duplicate_in_creator_results", "uploader_id": seed.uploader_id})
                continue
            seen.add(bvid)
            if (bvid, None) in existing:
                skipped.append({"bvid": bvid, "reason": "duplicate_existing_queue", "uploader_id": seed.uploader_id})
                continue
            query_label = f"creator_space:{seed.uploader or seed.uploader_id}"
            hit, metadata_diagnostics = fetch_video_hit(
                bvid,
                query_label=query_label,
                timeout=timeout,
                use_chrome_cookies=use_chrome_cookies,
            )
            fetched += 1
            if not hit:
                skipped.append({"bvid": bvid, "reason": "metadata_fetch_failed", "uploader_id": seed.uploader_id, "diagnostics": metadata_diagnostics[:200]})
                continue
            hard_reject_reason = hard_reject_hit(hit)
            if hard_reject_reason:
                skipped.append({"bvid": bvid, "title": hit.title, "reason": hard_reject_reason, "uploader_id": seed.uploader_id})
                continue
            candidate = build_candidate(hit, species_names, move_names)
            candidate["discovered_by"] = "agent_creator_space_yt_dlp"
            candidate["discovery_reason"] = (
                f"Agent discovered 洛克王国世界PVP Bilibili source from creator space `{seed.uploader or seed.uploader_id}`; "
                f"seed_source={seed.seed_source_id or 'direct'}."
            )
            candidate["notes"] = f"{candidate.get('notes')}; creator_id={seed.uploader_id}; seed_source={seed.seed_source_id or 'direct'}"
            if not has_roco_or_entity_signal(hit, candidate):
                skipped.append({"bvid": bvid, "title": hit.title, "reason": "not_roco_or_a_layer_entity", "uploader_id": seed.uploader_id})
                continue
            score_match = re.search(r"score=(\d+)", str(candidate.get("notes") or ""))
            score = int(score_match.group(1)) if score_match else 0
            if score < min_score:
                skipped.append({"bvid": bvid, "title": hit.title, "reason": f"score_below_{min_score}", "score": score, "uploader_id": seed.uploader_id})
                continue
            candidates_with_score.append((score, candidate))

        creator_reports.append(
            {
                "uploader_id": seed.uploader_id,
                "uploader": seed.uploader,
                "seed_source_id": seed.seed_source_id,
                "listed_bvid_count": len(bvids),
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
        "creator_count": len(seeds),
        "candidate_count_before_cap": len(candidates_with_score),
        "candidate_count_after_cap": len(selected),
        "skipped_count": len(skipped),
        "diversity_skipped_count": len(diversity_skipped),
        "diversity": {
            **diversity_summary,
            "max_candidates_per_bvid": 1,
            "max_candidates_per_uploader": max_per_uploader,
        },
        "creators": creator_reports,
        "skipped": [*skipped[:120], *diversity_skipped[:50]],
    }
    return selected, report


def render_creator_discovery_report(payload: dict[str, Any]) -> str:
    report = payload.get("discovery_report") or {}
    skipped = report.get("skipped") or []
    skip_reasons = Counter(str(item.get("reason") or "unknown") for item in skipped)
    lines = [
        f"# Creator Space Discovery Yield: {payload['batch_id']}",
        "",
        "## 结论",
        f"- Creator {report.get('creator_count', 0)} 个；候选 {report.get('candidate_count_after_cap', 0)} 条；跳过 {report.get('skipped_count', 0)} 条。",
        f"- Diversity：unique BV {((report.get('diversity') or {}).get('selected_unique_bvid_count', 0))}；unique uploader {((report.get('diversity') or {}).get('selected_unique_uploader_count', 0))}；diversity skipped {report.get('diversity_skipped_count', 0)}。",
        "- 这些只是 source queue 候选，不是证据；进入队列后仍要过字幕/ASR、AB 精校、evidence foundation、Set Inventory。",
        "",
        "## Creator Funnel",
    ]
    for item in report.get("creators") or []:
        diag = str(item.get("diagnostics") or "").splitlines()[0] if item.get("diagnostics") else ""
        suffix = f"；diag={diag[:80]}" if diag else ""
        label = item.get("uploader") or item.get("uploader_id")
        lines.append(
            f"- `{label}`：listed={item.get('listed_bvid_count', 0)}；metadata_fetch={item.get('metadata_fetch_count', 0)}{suffix}"
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
    parser.add_argument("--uploader-id", action="append", default=[])
    parser.add_argument("--seed-source-id", action="append", default=[])
    parser.add_argument("--max-videos-per-creator", type=int, default=20)
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

    seeds = creator_seeds_from_args(
        source_queue_path=args.source_queue,
        uploader_ids=args.uploader_id,
        seed_source_ids=args.seed_source_id,
        timeout=args.timeout,
        use_chrome_cookies=args.use_chrome_cookies,
    )
    candidates, report = discover_creator_candidates(
        seeds=seeds,
        max_videos_per_creator=args.max_videos_per_creator,
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
        "discovery_method": "yt_dlp_bilibili_creator_space",
        "discovery_notes": [
            "Discovery output is queue substrate only.",
            "Run p14_source_queue_expand.py before ingest; do not treat this file as evidence.",
            "Creator-space mining is a fallback for search-page instability and must still pass PvP boundary gates.",
        ],
        "creator_seeds": [seed.__dict__ for seed in seeds],
        "max_videos_per_creator": args.max_videos_per_creator,
        "discovery_report": report,
        "candidates": candidates,
    }
    out_path = args.out_dir / f"{args.batch_id}_candidates.yaml"
    _write_yaml(out_path, payload)
    packet_path = args.out_dir.parent / "review_packets" / f"{args.batch_id}_creator_discovery_yield.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(render_creator_discovery_report(payload), encoding="utf-8")

    summary = {
        "batch_id": args.batch_id,
        "runtime_allowed": False,
        "candidate_file": _relpath(out_path),
        "pm_brief": _relpath(packet_path),
        "creator_count": len(seeds),
        "candidate_count": len(candidates),
        "skipped_count": report["skipped_count"],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(summary)


if __name__ == "__main__":
    main()
