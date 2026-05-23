#!/usr/bin/env python3
"""Run the Roco Bailian hotword ASR fallback pipeline for one source run."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from tools.video_evidence_foundation import build_evidence_foundation


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOCAB_ID_PATH = REPO_ROOT / "data" / "transcript_refinement" / "bailian" / "roco_asr_core_v3.vocabulary_id.txt"
DEFAULT_OUT_SUBDIR = "bailian_hotword_pipeline"


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_asr_text(asr_json_path: Path, text_path: Path) -> str:
    payload = _read_json(asr_json_path)
    text = "\n\n".join(
        transcript.get("text", "").strip()
        for transcript in payload.get("transcripts", [])
        if transcript.get("text", "").strip()
    ).strip()
    if not text:
        raise ValueError(f"No transcript text found in {asr_json_path}")
    text_path.write_text(text + "\n", encoding="utf-8")
    return text


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _known_comparison_rows(subtitle_text: str, bailian_text: str) -> list[tuple[str, str, str]]:
    probes = [
        ("team name", "去世印记队", "蓄势印记队"),
        ("lead species", "十菠萝", "嗜波螺"),
        ("species", "立灯鱼", "利灯鱼"),
        ("stat phrase", "魔攻独子值", "魔攻种族值"),
        ("move phrase", "四咬技能", "撕咬技能"),
        ("resonance magic", "月影冲击/怨力冲击", "愿力冲击"),
        ("species", "寂灭古龙", "寂灭骨龙"),
        ("user name", "北锅", "北郭"),
    ]
    rows: list[tuple[str, str, str]] = []
    for label, bad, good in probes:
        if bad in subtitle_text or good in bailian_text:
            rows.append((label, bad if bad in subtitle_text else "-", good if good in bailian_text else "-"))
    return rows


def _write_report(
    path: Path,
    *,
    source_id: str,
    audio_path: Path,
    subtitle_path: Path | None,
    asr_json_path: Path,
    asr_text_path: Path,
    refined_manifest_path: Path,
    refined_manifest: dict[str, Any],
    vocabulary_id: str,
    foundation_result: dict[str, Any] | None,
) -> None:
    subtitle_text = subtitle_path.read_text(encoding="utf-8", errors="ignore") if subtitle_path and subtitle_path.exists() else ""
    bailian_text = asr_text_path.read_text(encoding="utf-8", errors="ignore")
    rows = _known_comparison_rows(subtitle_text, bailian_text)
    quality_counts = refined_manifest.get("paragraph_quality_counts", {})
    applied = refined_manifest.get("applied_correction_counts", {})

    lines = [
        f"# Bailian Hotword ASR Pipeline - {source_id}",
        "",
        f"- audio: `{audio_path}`",
        f"- subtitle_baseline: `{subtitle_path}`" if subtitle_path else "- subtitle_baseline: none",
        f"- bailian_asr_json: `{asr_json_path}`",
        f"- bailian_asr_text: `{asr_text_path}`",
        f"- ab_refine_manifest: `{refined_manifest_path}`",
        f"- vocabulary_id: `{vocabulary_id}`",
    ]
    if foundation_result:
        foundation_paths = foundation_result.get("paths", {})
        lines.extend(
            [
                f"- source_manifest_v2: `{foundation_paths.get('source_manifest_v2')}`",
                f"- evidence_segments: `{foundation_paths.get('segments')}`",
                f"- input_quality_gate: `{foundation_paths.get('quality_gate')}`",
                f"- claim_atoms: `{foundation_paths.get('claim_atoms')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Quality",
            "",
            f"- paragraph_count: {refined_manifest.get('paragraph_count')}",
            f"- paragraph_quality_counts: `{quality_counts}`",
            f"- applied_correction_counts: `{applied}`",
        ]
    )
    if foundation_result:
        lines.append(f"- foundation_quality_summary: `{foundation_result.get('quality_summary', {})}`")
    lines.extend(["", "## Baseline Differences", ""])
    if rows:
        lines.extend(["| Span | Baseline subtitle issue | Bailian hotword ASR |", "| --- | --- | --- |"])
        lines.extend(f"| {label} | {bad} | {good} |" for label, bad, good in rows)
    else:
        lines.append("No known probe differences matched this source.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This output is transcript substrate only.",
            "- It may feed candidate extraction after PM/source review.",
            "- It is not reviewed Meta Graph data and not runtime knowledge.",
            "- Raw Bailian JSON may contain temporary uploaded file URLs; do not publish it as a public artifact without sanitizing.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--subtitle", type=Path)
    parser.add_argument("--source-id")
    parser.add_argument("--vocab-id-file", type=Path, default=DEFAULT_VOCAB_ID_PATH)
    parser.add_argument("--model", default="fun-asr")
    parser.add_argument("--out-subdir", default=DEFAULT_OUT_SUBDIR)
    parser.add_argument("--reuse-asr", action="store_true", help="Reuse existing Bailian JSON if present")
    parser.add_argument(
        "--skip-foundation",
        action="store_true",
        help="Skip source_manifest_v2 / segment evidence / quality gate / claim atom artifacts",
    )
    args = parser.parse_args()

    run_dir = args.run_dir
    source_id = args.source_id or run_dir.name
    output_dir = run_dir / args.out_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    vocabulary_id = args.vocab_id_file.read_text(encoding="utf-8").strip()
    if not vocabulary_id:
        raise SystemExit(f"Missing vocabulary id in {args.vocab_id_file}")

    asr_json_path = output_dir / f"{source_id}.bailian_hotword_asr.json"
    asr_text_path = output_dir / f"{source_id}.bailian_hotword_asr.txt"
    refined_dir = output_dir / "ab_refine"
    report_path = output_dir / f"{source_id}.pipeline_report.md"

    if not (args.reuse_asr and asr_json_path.exists()):
        _run(
            [
                "bl",
                "speech",
                "recognize",
                "--model",
                args.model,
                "--url",
                str(args.audio),
                "--language",
                "zh",
                "--vocabulary-id",
                vocabulary_id,
                "--out",
                str(asr_json_path),
                "--output",
                "json",
                "--non-interactive",
            ],
            cwd=REPO_ROOT,
        )

    _extract_asr_text(asr_json_path, asr_text_path)
    _run(
        [
            ".venv/bin/python",
            "tools/transcript_ab_refine.py",
            "--source",
            str(asr_text_path),
            "--source-id",
            f"{source_id}_bailian_hotword",
            "--out-dir",
            str(refined_dir),
            "--include-unresolved",
            "--repair-candidates",
            "--json",
        ],
        cwd=REPO_ROOT,
    )

    refined_manifest_path = refined_dir / f"{source_id}_bailian_hotword.manifest.yaml"
    refined_manifest = _load_manifest(refined_manifest_path)
    foundation_result = None
    if not args.skip_foundation:
        foundation_result = build_evidence_foundation(
            source_id=f"{source_id}_bailian_hotword",
            run_dir=run_dir,
            out_dir=output_dir / "evidence_foundation",
            source_manifest_path=run_dir / "source_manifest.yaml",
            source_type="community_video",
            transcript_method="bailian_hotword_asr_v3",
            asr_json_path=asr_json_path,
            transcript_path=asr_text_path,
            ab_refined_path=refined_dir / f"{source_id}_bailian_hotword.ab_refined.md",
            ab_manifest_path=refined_manifest_path,
        )
    _write_report(
        report_path,
        source_id=source_id,
        audio_path=args.audio,
        subtitle_path=args.subtitle,
        asr_json_path=asr_json_path,
        asr_text_path=asr_text_path,
        refined_manifest_path=refined_manifest_path,
        refined_manifest=refined_manifest,
        vocabulary_id=vocabulary_id,
        foundation_result=foundation_result,
    )
    print(
        json.dumps(
            {
                "source_id": source_id,
                "asr_json_path": str(asr_json_path),
                "asr_text_path": str(asr_text_path),
                "ab_refine_manifest": str(refined_manifest_path),
                "report_path": str(report_path),
                "evidence_foundation": foundation_result,
                "paragraph_quality_counts": refined_manifest.get("paragraph_quality_counts", {}),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
