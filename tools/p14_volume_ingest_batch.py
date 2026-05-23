#!/usr/bin/env python3
"""Run a small P14 volume-lane ingest batch from queued Bilibili sources.

This tool is source substrate only. It downloads subtitles or ASR transcripts,
runs AB refinement and evidence foundation, then refreshes Set Pipeline,
Set Inventory, consolidation, and autorun dashboard. It never promotes runtime
graph data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_autorun_dashboard import run_autorun_dashboard
from tools.p14_set_inventory_builder import run_set_inventory_builder
from tools.p14_set_inventory_consolidator import run_set_inventory_consolidator
from tools.p14_set_pipeline import run_set_pipeline
from tools.transcript_ab_refine import refine_transcript
from tools.video_evidence_foundation import build_evidence_foundation


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_QUEUE = REPO_ROOT / "artifacts" / "knowledge_ops" / "source_queue.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
DEFAULT_SOURCE_PROBE_DIR = DEFAULT_OUT_ROOT / "source_probe"
DEFAULT_VOCAB_ID_PATH = REPO_ROOT / "data" / "transcript_refinement" / "bailian" / "roco_asr_core_v3.vocabulary_id.txt"
DEFAULT_BATCH_ID = f"phase1_volume_ingest_{date.today().isoformat()}"
MAX_SUBTITLE_PARTS = 8
MAX_COMBINED_SUBTITLE_BYTES = 300_000


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


def _relpath(path: Path | str | None) -> str:
    if not path:
        return ""
    path = Path(path)
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _tail(text: str, lines: int = 10) -> list[str]:
    return [line for line in text.splitlines()[-lines:] if line.strip()]


def _subtitle_ingest_block(subtitle_files: list[Path]) -> dict[str, Any] | None:
    total_bytes = sum(path.stat().st_size for path in subtitle_files if path.exists())
    if len(subtitle_files) > MAX_SUBTITLE_PARTS:
        return {
            "reason": "multi_part_subtitle_over_limit",
            "subtitle_part_count": len(subtitle_files),
            "subtitle_bytes": total_bytes,
            "max_subtitle_parts": MAX_SUBTITLE_PARTS,
            "max_combined_subtitle_bytes": MAX_COMBINED_SUBTITLE_BYTES,
        }
    if len(subtitle_files) > 1 and total_bytes > MAX_COMBINED_SUBTITLE_BYTES:
        return {
            "reason": "combined_subtitle_bytes_over_limit",
            "subtitle_part_count": len(subtitle_files),
            "subtitle_bytes": total_bytes,
            "max_subtitle_parts": MAX_SUBTITLE_PARTS,
            "max_combined_subtitle_bytes": MAX_COMBINED_SUBTITLE_BYTES,
        }
    return None


def _source_by_id(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(source.get("source_id")): source for source in queue.get("sources") or [] if source.get("source_id")}


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _existing_ingest_result(source: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    source_id = str(source.get("source_id"))
    foundation_dir = run_dir / "evidence_foundation"
    subtitle_path = _first_existing(
        [
            run_dir / f"{source_id}.combined.srt",
            *sorted(path for path in run_dir.glob("*.combined.srt")),
            *sorted(path for path in run_dir.glob("*.srt") if "combined" not in path.name),
            *sorted(path for path in run_dir.glob("*.vtt") if "combined" not in path.name),
        ]
    )
    prior_method = str((source.get("subtitle_status") or {}).get("transcript_method") or "")
    transcript_method = prior_method if prior_method and prior_method != "existing" else ("subtitle_ai_zh" if subtitle_path else "existing")
    ab_manifest_path = run_dir / f"{source_id}.manifest.yaml"
    ab_manifest = _load_yaml(ab_manifest_path)
    return {
        "source_id": source_id,
        "status": "already_ingested",
        "run_dir": _relpath(run_dir),
        "transcript_method": transcript_method,
        "subtitle_path": _relpath(subtitle_path),
        "subtitle_track": _track_label(subtitle_path),
        "asr_fallback_needed": False,
        "asr_json_path": "",
        "ab_refined_path": _relpath(_first_existing([run_dir / f"{source_id}.ab_refined.md"])),
        "review_questions_path": _relpath(_first_existing([run_dir / f"{source_id}.review_questions.yaml"])),
        "manifest_path": _relpath(_first_existing([ab_manifest_path])),
        "source_manifest_path": _relpath(_first_existing([run_dir / "source_manifest.yaml"])),
        "evidence_foundation_dir": _relpath(foundation_dir),
        "foundation_quality": _load_yaml(foundation_dir / "quality_gate.yaml"),
        "paragraph_quality_counts": ab_manifest.get("paragraph_quality_counts") or {},
    }


def _selected_source_ids(queue: dict[str, Any], *, limit: int | None, explicit_source_ids: list[str]) -> list[str]:
    if explicit_source_ids:
        return list(dict.fromkeys(explicit_source_ids))
    plan = queue.get("latest_volume_batch_plan") or {}
    source_map = _source_by_id(queue)
    ids = [str(item) for item in plan.get("selected_source_ids") or [] if item]
    ids = [
        source_id
        for source_id in ids
        if str((source_map.get(source_id) or {}).get("ingest_status") or "queued") == "queued"
    ]
    if limit:
        return ids[:limit]
    return ids


def _write_source_manifest(run_dir: Path, source: dict[str, Any]) -> Path:
    manifest_path = run_dir / "source_manifest.yaml"
    manifest = {
        "schema_version": "p14.raw_source_manifest.v0",
        "source_id": source.get("source_id"),
        "created_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source": {
            "platform": source.get("platform"),
            "url": source.get("url"),
            "title": source.get("title"),
            "uploader": source.get("uploader"),
            "published_at": source.get("published_at"),
            "source_type": source.get("source_type"),
            "target_archetype": source.get("target_archetype"),
            "target_entities": source.get("target_entities") or [],
        },
        "ingest_policy": {
            "subtitle_first": True,
            "asr_fallback_only_if_no_usable_subtitle": True,
            "runtime_allowed": False,
        },
    }
    _write_yaml(manifest_path, manifest)
    return manifest_path


def _download_subtitles(source: dict[str, Any], run_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    source_id = str(source.get("source_id"))
    command = [
        "yt-dlp",
        "--cookies-from-browser",
        "chrome",
        "--no-playlist",
        "--write-subs",
        "--sub-langs",
        "ai-zh,zh.*,zh-Hans,zh-CN",
        "--sub-format",
        "srt",
        "--skip-download",
        "-o",
        str(run_dir / "%(id)s.%(ext)s"),
        str(source.get("url")),
    ]
    result = _run(command)
    subtitle_files = sorted(
        path for path in [*run_dir.glob("*.srt"), *run_dir.glob("*.vtt")]
        if "combined" not in path.name
    )
    if not subtitle_files:
        return None, {
            "step": "subtitle_download",
            "exit_code": result.returncode,
            "method": "yt-dlp_chrome_cookies",
            "output_tail": _tail(result.stdout),
        }
    blocked = _subtitle_ingest_block(subtitle_files)
    if blocked:
        return None, {
            "step": "subtitle_download",
            "exit_code": result.returncode,
            "method": "yt-dlp_chrome_cookies",
            "blocked_reason": blocked["reason"],
            "subtitle_part_count": blocked["subtitle_part_count"],
            "subtitle_bytes": blocked["subtitle_bytes"],
            "max_subtitle_parts": blocked["max_subtitle_parts"],
            "max_combined_subtitle_bytes": blocked["max_combined_subtitle_bytes"],
            "subtitle_parts": [_relpath(path) for path in subtitle_files[:MAX_SUBTITLE_PARTS]],
            "output_tail": _tail(result.stdout),
        }
    if len(subtitle_files) == 1:
        return subtitle_files[0], {
            "step": "subtitle_download",
            "exit_code": result.returncode,
            "method": "yt-dlp_chrome_cookies",
            "subtitle_path": _relpath(subtitle_files[0]),
            "output_tail": _tail(result.stdout),
        }
    combined = run_dir / f"{source_id}.combined.srt"
    combined.write_text(
        "\n\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in subtitle_files),
        encoding="utf-8",
    )
    return combined, {
        "step": "subtitle_download",
        "exit_code": result.returncode,
        "method": "yt-dlp_chrome_cookies",
        "subtitle_path": _relpath(combined),
        "subtitle_parts": [_relpath(path) for path in subtitle_files],
        "output_tail": _tail(result.stdout),
    }


def _download_audio(source: dict[str, Any], run_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    command = [
        "yt-dlp",
        "--cookies-from-browser",
        "chrome",
        "--no-playlist",
        "-f",
        "ba/bestaudio/worstaudio/worst",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "7",
        "-o",
        str(run_dir / "%(id)s.%(ext)s"),
        str(source.get("url")),
    ]
    result = _run(command)
    audio_files = sorted(run_dir.glob("*.mp3"))
    return (audio_files[0] if audio_files else None), {
        "step": "audio_download",
        "exit_code": result.returncode,
        "method": "yt-dlp_chrome_cookies",
        "audio_path": _relpath(audio_files[0]) if audio_files else "",
        "output_tail": _tail(result.stdout),
    }


def _extract_bailian_text(asr_json_path: Path, text_path: Path) -> str:
    payload = json.loads(asr_json_path.read_text(encoding="utf-8"))
    text = "\n\n".join(
        transcript.get("text", "").strip()
        for transcript in payload.get("transcripts", [])
        if transcript.get("text", "").strip()
    ).strip()
    if not text:
        raise ValueError("ASR response produced no transcript words")
    text_path.write_text(text + "\n", encoding="utf-8")
    return text


def _run_bailian_asr(source_id: str, audio_path: Path, run_dir: Path, vocab_id_path: Path) -> tuple[Path | None, Path | None, dict[str, Any]]:
    if not vocab_id_path.exists():
        return None, None, {
            "step": "bailian_asr",
            "exit_code": None,
            "method": "bailian_fun_asr_hotword",
            "error": f"missing_vocab_id_file:{_relpath(vocab_id_path)}",
        }
    vocabulary_id = vocab_id_path.read_text(encoding="utf-8").strip()
    if not vocabulary_id:
        return None, None, {
            "step": "bailian_asr",
            "exit_code": None,
            "method": "bailian_fun_asr_hotword",
            "error": "empty_vocab_id",
        }
    asr_json_path = run_dir / f"{source_id}.bailian_hotword_asr.json"
    asr_text_path = run_dir / f"{source_id}.bailian_hotword_asr.txt"
    command = [
        "bl",
        "speech",
        "recognize",
        "--model",
        "fun-asr",
        "--url",
        str(audio_path),
        "--language",
        "zh",
        "--vocabulary-id",
        vocabulary_id,
        "--out",
        str(asr_json_path),
        "--output",
        "json",
        "--non-interactive",
    ]
    result = _run(command)
    record = {
        "step": "bailian_asr",
        "exit_code": result.returncode,
        "method": "bailian_fun_asr_hotword",
        "asr_json_path": _relpath(asr_json_path) if asr_json_path.exists() else "",
        "asr_text_path": _relpath(asr_text_path),
        "output_tail": _tail(result.stdout),
    }
    if result.returncode != 0 or not asr_json_path.exists():
        return None, None, record
    try:
        _extract_bailian_text(asr_json_path, asr_text_path)
    except ValueError as exc:
        record["error"] = str(exc)
        return asr_json_path, None, record
    return asr_json_path, asr_text_path, record


def _track_label(path: Path | None) -> str:
    if not path:
        return ""
    name = path.name
    if ".ai-zh." in name:
        return "ai-zh"
    if ".zh-Hans." in name:
        return "zh-Hans"
    if ".zh-CN." in name:
        return "zh-CN"
    if name.endswith(".combined.srt"):
        return "combined_chinese_subtitle"
    return path.suffix.lstrip(".")


def _ingest_one(
    *,
    source: dict[str, Any],
    run_dir: Path,
    vocab_id_path: Path,
    enable_asr_fallback: bool,
    force: bool,
) -> dict[str, Any]:
    source_id = str(source.get("source_id"))
    if not force and (run_dir / "evidence_foundation" / "segments.yaml").exists():
        return _existing_ingest_result(source, run_dir)

    run_dir.mkdir(parents=True, exist_ok=True)
    source_manifest_path = _write_source_manifest(run_dir, source)
    steps: list[dict[str, Any]] = []
    subtitle_path, subtitle_step = _download_subtitles(source, run_dir)
    steps.append(subtitle_step)
    if subtitle_step.get("blocked_reason"):
        return {
            "source_id": source_id,
            "status": "transcript_blocked",
            "run_dir": _relpath(run_dir),
            "reason": subtitle_step.get("blocked_reason"),
            "transcript_method": "subtitle_blocked_before_refinement",
            "subtitle_part_count": subtitle_step.get("subtitle_part_count"),
            "subtitle_bytes": subtitle_step.get("subtitle_bytes"),
            "asr_fallback_needed": False,
            "steps": steps,
        }

    transcript_path = subtitle_path
    asr_json_path: Path | None = None
    transcript_method = "subtitle_ai_zh" if subtitle_path else ""
    asr_fallback_needed = subtitle_path is None
    if not transcript_path and enable_asr_fallback:
        audio_path, audio_step = _download_audio(source, run_dir)
        steps.append(audio_step)
        if audio_path:
            asr_json_path, asr_text_path, asr_step = _run_bailian_asr(source_id, audio_path, run_dir, vocab_id_path)
            steps.append(asr_step)
            transcript_path = asr_text_path
            transcript_method = "bailian_hotword_asr_v3" if asr_text_path else ""

    if not transcript_path:
        return {
            "source_id": source_id,
            "status": "transcript_blocked",
            "run_dir": _relpath(run_dir),
            "reason": "no_usable_chinese_subtitle_or_asr_text",
            "steps": steps,
        }

    manifest = refine_transcript(
        transcript_path,
        out_dir=run_dir,
        source_id=source_id,
        include_unresolved=True,
        repair_candidates=True,
    )
    ab_refined_path = Path(manifest["cleaned_path"])
    ab_manifest_path = run_dir / f"{source_id}.manifest.yaml"
    foundation = build_evidence_foundation(
        source_id=source_id,
        run_dir=run_dir,
        out_dir=run_dir / "evidence_foundation",
        source_manifest_path=source_manifest_path,
        source_type=str(source.get("source_type") or "community_video"),
        transcript_method=transcript_method,
        asr_json_path=asr_json_path,
        transcript_path=transcript_path,
        ab_refined_path=ab_refined_path,
        ab_manifest_path=ab_manifest_path,
        source_url=str(source.get("url") or ""),
        title=str(source.get("title") or ""),
    )
    return {
        "source_id": source_id,
        "status": "evidence_foundation_ready",
        "run_dir": _relpath(run_dir),
        "transcript_method": transcript_method,
        "subtitle_path": _relpath(subtitle_path),
        "subtitle_track": _track_label(subtitle_path),
        "asr_fallback_needed": asr_fallback_needed,
        "asr_json_path": _relpath(asr_json_path),
        "ab_refined_path": _relpath(ab_refined_path),
        "review_questions_path": _relpath(run_dir / f"{source_id}.review_questions.yaml"),
        "manifest_path": _relpath(ab_manifest_path),
        "source_manifest_path": _relpath(source_manifest_path),
        "evidence_foundation_dir": _relpath(run_dir / "evidence_foundation"),
        "foundation_quality": foundation.get("quality_summary") or {},
        "paragraph_quality_counts": manifest.get("paragraph_quality_counts") or {},
        "steps": steps,
    }


def _update_source_after_ingest(source: dict[str, Any], result: dict[str, Any]) -> None:
    if result["status"] in {"evidence_foundation_ready", "already_ingested"}:
        source["ingest_status"] = "evidence_foundation_ready"
        source["subtitle_status"] = {
            "checked_with_chrome_cookies": True,
            "chinese_subtitle_track": result.get("subtitle_track") or "",
            "transcript_method": result.get("transcript_method"),
            "asr_fallback_needed": bool(result.get("asr_fallback_needed")),
        }
        artifacts = dict(source.get("ingest_artifacts") or {})
        for key in [
            "subtitle_path",
            "ab_refined_path",
            "review_questions_path",
            "manifest_path",
            "source_manifest_path",
            "evidence_foundation_dir",
        ]:
            if result.get(key):
                artifacts[key] = result[key]
        source["ingest_artifacts"] = artifacts
        prior = dict(source.get("source_quality_prior") or {})
        quality = result.get("foundation_quality") or {}
        prior["latest_evidence_foundation"] = {
            "segment_count": quality.get("segment_count", 0),
            "claim_atom_count": quality.get("claim_atom_count", 0),
            "repair_required_segments": len(quality.get("repair_required_segments") or []),
        }
        source["source_quality_prior"] = prior
    elif result["status"] == "transcript_blocked":
        source["ingest_status"] = "transcript_unavailable_no_text"
        source["subtitle_status"] = {
            "checked_with_chrome_cookies": True,
            "chinese_subtitle_track": "",
            "transcript_method": result.get("transcript_method") or "",
            "asr_fallback_needed": bool(result.get("asr_fallback_needed", True)),
            "blocked_reason": result.get("reason"),
        }
        artifacts = dict(source.get("ingest_artifacts") or {})
        if result.get("subtitle_part_count") is not None:
            artifacts["blocked_subtitle_part_count"] = result.get("subtitle_part_count")
        if result.get("subtitle_bytes") is not None:
            artifacts["blocked_subtitle_bytes"] = result.get("subtitle_bytes")
        if artifacts:
            source["ingest_artifacts"] = artifacts


def _mark_processed_outputs(
    queue: dict[str, Any],
    *,
    source_ids: list[str],
    set_pipeline_result: dict[str, Any],
    inventory_result: dict[str, Any],
) -> None:
    source_map = _source_by_id(queue)
    for source_id in source_ids:
        source = source_map[source_id]
        if source.get("ingest_status") != "evidence_foundation_ready":
            continue
        artifacts = dict(source.get("ingest_artifacts") or {})
        artifacts.update(
            {
                "set_candidates_path": f"artifacts/knowledge_ops/set_candidates/{source_id}.candidate_sets.yaml",
                "relation_candidates_path": f"artifacts/knowledge_ops/relation_candidates/{source_id}.candidate_edges.yaml",
                "set_delta_batch": set_pipeline_result["batch_id"],
                "set_delta_packet": set_pipeline_result["paths"]["pm_delta_packet"],
                "set_delta_audit": set_pipeline_result["paths"]["audit"],
                "set_inventory_path": f"artifacts/knowledge_ops/set_inventory/{source_id}.source_inventory.yaml",
                "set_inventory_batch": inventory_result["batch_id"],
            }
        )
        source["ingest_artifacts"] = artifacts
        source["ingest_status"] = "set_pipeline_processed"


def _render_pm_brief(batch: dict[str, Any]) -> str:
    lines = [
        f"# Volume Ingest Batch: {batch['batch_id']}",
        "",
        "## 结论",
        f"- 请求处理 {batch['summary']['requested_source_count']} 条；成功进入 Set Inventory {batch['summary']['processed_source_count']} 条；blocked {batch['summary']['blocked_source_count']} 条。",
        "- 这些输出仍然是候选素材，不是 runtime graph，也不是 PM-reviewed set。",
        "",
        "## Source Results",
    ]
    for item in batch.get("source_results") or []:
        if item.get("status") == "set_pipeline_processed":
            quality = item.get("foundation_quality") or {}
            lines.append(
                f"- {item['source_id']}：ok；method={item.get('transcript_method')}；segments={quality.get('segment_count', 0)}；claims={quality.get('claim_atom_count', 0)}；repair_required={len(quality.get('repair_required_segments') or [])}。"
            )
        else:
            lines.append(f"- {item['source_id']}：{item.get('status')}；reason={item.get('reason', '')}。")
    lines.extend(
        [
            "",
            "## Batch Outputs",
            f"- set pipeline: `{batch.get('set_pipeline', {}).get('paths', {}).get('pm_delta_packet', '')}`",
            f"- set inventory: `{batch.get('set_inventory', {}).get('paths', {}).get('pm_brief', '')}`",
            f"- consolidation: `{batch.get('consolidation', {}).get('paths', {}).get('pm_brief', '')}`",
            f"- autorun dashboard: `{batch.get('autorun_dashboard', {}).get('paths', {}).get('pm_dashboard', '')}`",
            "",
            "## 下一步",
            "看 autorun dashboard。只有新晋升候选、schema 分叉、高影响机制冲突需要 PM；普通 blocked source 继续留在 blocker queue。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_volume_ingest_batch(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    out_root: Path = DEFAULT_OUT_ROOT,
    source_probe_dir: Path = DEFAULT_SOURCE_PROBE_DIR,
    batch_id: str = DEFAULT_BATCH_ID,
    limit: int | None = None,
    source_ids: list[str] | None = None,
    enable_asr_fallback: bool = False,
    vocab_id_path: Path = DEFAULT_VOCAB_ID_PATH,
    force: bool = False,
    update_source_queue: bool = True,
) -> dict[str, Any]:
    queue = _load_yaml(source_queue)
    source_map = _source_by_id(queue)
    requested_source_ids = _selected_source_ids(queue, limit=limit, explicit_source_ids=source_ids or [])
    missing = [source_id for source_id in requested_source_ids if source_id not in source_map]
    if missing:
        raise ValueError(f"source ids not found in queue: {', '.join(missing)}")

    source_results: list[dict[str, Any]] = []
    for source_id in requested_source_ids:
        source = source_map[source_id]
        result = _ingest_one(
            source=source,
            run_dir=source_probe_dir / source_id,
            vocab_id_path=vocab_id_path,
            enable_asr_fallback=enable_asr_fallback,
            force=force,
        )
        _update_source_after_ingest(source, result)
        source_results.append(result)

    processed_ids = [item["source_id"] for item in source_results if item["status"] in {"evidence_foundation_ready", "already_ingested"}]
    blocked_ids = [item["source_id"] for item in source_results if item["status"] == "transcript_blocked"]

    set_pipeline_result: dict[str, Any] = {}
    inventory_result: dict[str, Any] = {}
    consolidation_result: dict[str, Any] = {}
    dashboard_result: dict[str, Any] = {}
    if processed_ids:
        if update_source_queue:
            _write_yaml(source_queue, queue)
        set_pipeline_result = run_set_pipeline(
            source_queue=source_queue,
            out_root=out_root,
            batch_id=f"{batch_id}_set_pipeline",
            source_ids=set(processed_ids),
        )
        inventory_result = run_set_inventory_builder(
            source_queue=source_queue,
            out_root=out_root,
            batch_id=f"{batch_id}_set_inventory",
            source_ids=set(processed_ids),
        )
        _mark_processed_outputs(
            queue,
            source_ids=processed_ids,
            set_pipeline_result=set_pipeline_result,
            inventory_result=inventory_result,
        )

        previous = queue.get("latest_set_inventory_consolidation") or {}
        active_source_ids = list(dict.fromkeys([*(previous.get("source_ids") or []), *processed_ids]))
        consolidation_result = run_set_inventory_consolidator(
            out_root=out_root,
            batch_id=f"{batch_id}_consolidation",
            source_ids=set(active_source_ids),
        )
        queue["latest_set_inventory_consolidation"] = {
            "batch_id": consolidation_result["batch_id"],
            "source_ids": active_source_ids,
            "consolidation_path": consolidation_result["paths"]["consolidation"],
            "review_packet": consolidation_result["paths"]["pm_brief"],
            "family_review_packet": consolidation_result["paths"]["family_review"],
            "family_review_ledger": "data/knowledge_graph/v0/review_state/family_review_ledger.yaml",
            "summary": consolidation_result["summary"],
            "runtime_allowed": False,
        }

    for item in source_results:
        if item["source_id"] in processed_ids:
            item["status"] = "set_pipeline_processed"

    batch = {
        "schema_version": "p14.volume_ingest_batch.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "requested_source_ids": requested_source_ids,
        "processed_source_ids": processed_ids,
        "blocked_source_ids": blocked_ids,
        "summary": {
            "requested_source_count": len(requested_source_ids),
            "processed_source_count": len(processed_ids),
            "blocked_source_count": len(blocked_ids),
            "asr_fallback_enabled": enable_asr_fallback,
        },
        "source_results": source_results,
        "set_pipeline": set_pipeline_result,
        "set_inventory": inventory_result,
        "consolidation": consolidation_result,
    }

    audit_path = out_root / "audits" / f"{batch_id}.yaml"
    packet_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    _write_yaml(audit_path, batch)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(_render_pm_brief(batch), encoding="utf-8")

    queue["latest_volume_ingest"] = {
        "batch_id": batch_id,
        "generated_at": batch["generated_at"],
        "requested_source_ids": requested_source_ids,
        "processed_source_ids": processed_ids,
        "blocked_source_ids": blocked_ids,
        "audit_path": _relpath(audit_path),
        "review_packet": _relpath(packet_path),
        "runtime_allowed": False,
    }
    if update_source_queue:
        _write_yaml(source_queue, queue)
        if processed_ids:
            dashboard_result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id=f"{batch_id}_autorun_dashboard",
            )
            # Refresh queue handle after dashboard updated it.
            queue = _load_yaml(source_queue)

    batch["autorun_dashboard"] = dashboard_result
    if dashboard_result:
        _write_yaml(audit_path, batch)
        packet_path.write_text(_render_pm_brief(batch), encoding="utf-8")
        queue["latest_volume_ingest"]["autorun_dashboard"] = dashboard_result["paths"].get("pm_dashboard")
        if update_source_queue:
            _write_yaml(source_queue, queue)

    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "paths": {
            "audit": _relpath(audit_path),
            "pm_brief": _relpath(packet_path),
            "source_queue": _relpath(source_queue),
        },
        "summary": batch["summary"],
        "processed_source_ids": processed_ids,
        "blocked_source_ids": blocked_ids,
        "autorun_dashboard": dashboard_result.get("paths", {}).get("pm_dashboard") if dashboard_result else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--source-probe-dir", type=Path, default=DEFAULT_SOURCE_PROBE_DIR)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--enable-asr-fallback", action="store_true")
    parser.add_argument("--vocab-id-path", type=Path, default=DEFAULT_VOCAB_ID_PATH)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-update-source-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_volume_ingest_batch(
        source_queue=args.source_queue,
        out_root=args.out_root,
        source_probe_dir=args.source_probe_dir,
        batch_id=args.batch_id,
        limit=args.limit,
        source_ids=args.source_id,
        enable_asr_fallback=args.enable_asr_fallback,
        vocab_id_path=args.vocab_id_path,
        force=args.force,
        update_source_queue=not args.no_update_source_queue,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"volume ingest batch: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
