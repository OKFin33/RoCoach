#!/usr/bin/env python3
"""Build segment-preserving source evidence for Roco video ingestion.

This tool sits before Meta Graph and D-layer extraction. It preserves source
segments, applies the same conservative A/B transcript repair pass, gates input
quality per segment, and emits unreviewed claim atoms. It never writes reviewed
graph cards or runtime knowledge.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from advisor.battle_dex import DEFAULT_RUNTIME_DB
from tools.transcript_ab_refine import (
    DEFAULT_CORRECTIONS_PATH,
    CorrectionRule,
    TermRecord,
    apply_corrections,
    apply_guided_repairs,
    apply_source_profile_repairs,
    build_source_profile,
    exact_term_hits,
    fuzzy_review_candidates,
    guided_repair_candidates,
    load_a_layer_terms,
    load_b_layer_terms,
    load_corrections,
    split_paragraphs,
    unresolved_domain_phrases,
)
from tools.transcript_quality import transcript_quality_flags, transcript_quality_label


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_SUBDIR = "evidence_foundation"

SRT_TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)

CLAIM_PATTERNS: tuple[dict[str, Any], ...] = (
    {"predicate": "has_role", "object": "lead", "phrases": ("首发",), "atom_type": "species_role"},
    {"predicate": "has_role", "object": "defensive_pivot", "phrases": ("联防",), "atom_type": "species_role"},
    {"predicate": "has_role", "object": "carry", "phrases": ("C位", "主C"), "atom_type": "species_role"},
    {"predicate": "has_role", "object": "cleaner", "phrases": ("收割", "清线手"), "atom_type": "species_role"},
    {"predicate": "has_role", "object": "buff_clear", "phrases": ("清强化", "清除对面"), "atom_type": "species_role"},
    {"predicate": "supports", "object": "energy_window", "phrases": ("能耗", "回合结束", "能量"), "atom_type": "resource_claim"},
    {
        "predicate": "uses_mechanism",
        "object": "mark",
        "phrases": ("印记", "引爆", "触发", "挂上", "叠层", "层", "星陨伤害", "爆炸伤害"),
        "atom_type": "mechanism_claim",
    },
    {"predicate": "uses_mechanism", "object": "weather", "phrases": ("天气", "沙暴", "沙涌"), "atom_type": "mechanism_claim"},
    {"predicate": "has_counterplay", "object": "counterplay", "phrases": ("克制", "针对", "防对面", "有奇效"), "atom_type": "relation_claim"},
    {"predicate": "has_synergy", "object": "synergy", "phrases": ("配合", "传递", "给"), "atom_type": "relation_claim"},
)

IMPLICIT_MECHANISM_TRIGGERS: tuple[dict[str, Any], ...] = (
    {
        "mechanism": "星陨印记",
        "requires_any": ("星陨", "星云印记", "星云帕尔"),
        "context_any": ("印记", "层", "引爆", "触发", "挂上", "偷", "覆盖", "星陨伤害", "爆炸伤害"),
    },
    {
        "mechanism": "灼烧",
        "requires_any": ("灼烧", "烧伤"),
        "context_any": ("挂", "层", "状态"),
    },
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _relpath(path: Path | None) -> str | None:
    if not path:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_yaml(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _parse_ms(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_srt_timestamp(value: str) -> int:
    hours, minutes, rest = value.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    return (
        int(hours) * 60 * 60 * 1000
        + int(minutes) * 60 * 1000
        + int(seconds) * 1000
        + int(millis)
    )


def segments_from_bailian_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract sentence-level segments from Bailian JSON without copying URLs."""
    segments: list[dict[str, Any]] = []
    index = 1
    for transcript in payload.get("transcripts", []) or []:
        channel_id = transcript.get("channel_id")
        sentences = transcript.get("sentences") or []
        for sentence in sentences:
            text = _compact_text(str(sentence.get("text", "")))
            if not text:
                continue
            segments.append(
                {
                    "segment_id": f"S{index:04d}",
                    "source_segment_id": str(sentence.get("sentence_id") or f"S{index:04d}"),
                    "source_kind": "bailian_asr_sentence",
                    "channel_id": channel_id,
                    "start_ms": _parse_ms(sentence.get("begin_time")),
                    "end_ms": _parse_ms(sentence.get("end_time")),
                    "raw_text": text,
                }
            )
            index += 1
    if segments:
        return segments

    # Some providers only return transcript-level text. Keep the fallback
    # explicit so downstream can see timing is unavailable.
    for transcript in payload.get("transcripts", []) or []:
        text = _compact_text(str(transcript.get("text", "")))
        if not text:
            continue
        for paragraph in split_paragraphs(text):
            segments.append(
                {
                    "segment_id": f"S{len(segments) + 1:04d}",
                    "source_segment_id": f"P{len(segments) + 1:03d}",
                    "source_kind": "bailian_asr_text_fallback",
                    "channel_id": transcript.get("channel_id"),
                    "start_ms": None,
                    "end_ms": None,
                    "raw_text": _compact_text(paragraph),
                }
            )
    return segments


def segments_from_srt_text(text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for block in re.split(r"\n\s*\n", text.replace("\ufeff", "").strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_index = next((idx for idx, line in enumerate(lines) if SRT_TIME_RE.search(line)), None)
        if time_index is None:
            continue
        match = SRT_TIME_RE.search(lines[time_index])
        if not match:
            continue
        body = " ".join(re.sub(r"<[^>]+>", "", line).strip() for line in lines[time_index + 1 :])
        body = _compact_text(body)
        if not body:
            continue
        segments.append(
            {
                "segment_id": f"S{len(segments) + 1:04d}",
                "source_segment_id": lines[0] if time_index > 0 and lines[0].isdigit() else f"S{len(segments) + 1:04d}",
                "source_kind": "subtitle_srt_cue",
                "channel_id": None,
                "start_ms": _parse_srt_timestamp(match.group("start")),
                "end_ms": _parse_srt_timestamp(match.group("end")),
                "raw_text": body,
            }
        )
    return segments


def segments_from_plain_text(text: str, *, source_kind: str = "plain_transcript_paragraph") -> list[dict[str, Any]]:
    return [
        {
            "segment_id": f"S{index:04d}",
            "source_segment_id": f"P{index:03d}",
            "source_kind": source_kind,
            "channel_id": None,
            "start_ms": None,
            "end_ms": None,
            "raw_text": _compact_text(paragraph),
        }
        for index, paragraph in enumerate(split_paragraphs(text), start=1)
        if _compact_text(paragraph)
    ]


def load_source_segments(
    *,
    asr_json_path: Path | None = None,
    transcript_path: Path | None = None,
    ab_refined_path: Path | None = None,
) -> tuple[list[dict[str, Any]], str]:
    if asr_json_path and asr_json_path.exists():
        payload = json.loads(asr_json_path.read_text(encoding="utf-8"))
        return segments_from_bailian_payload(payload), "bailian_asr_json_sentences"

    if transcript_path and transcript_path.exists():
        text = transcript_path.read_text(encoding="utf-8", errors="ignore")
        suffix = transcript_path.suffix.lower()
        if suffix in {".srt", ".vtt"}:
            return segments_from_srt_text(text), "subtitle_segments"
        return segments_from_plain_text(text), "plain_transcript_paragraphs"

    if ab_refined_path and ab_refined_path.exists():
        text = ab_refined_path.read_text(encoding="utf-8", errors="ignore")
        refined_lines = re.findall(r"^- 精校：(.*?)(?=\n- 自动校正：|\Z)", text, flags=re.MULTILINE | re.DOTALL)
        segments = [
            {
                "segment_id": f"S{index:04d}",
                "source_segment_id": f"P{index:03d}",
                "source_kind": "ab_refined_paragraph_fallback",
                "channel_id": None,
                "start_ms": None,
                "end_ms": None,
                "raw_text": _compact_text(value),
            }
            for index, value in enumerate(refined_lines, start=1)
            if _compact_text(value)
        ]
        return segments, "ab_refined_fallback"

    return [], "missing_source_segments"


def load_ab_lexicon(db_path: Path = DEFAULT_RUNTIME_DB) -> tuple[dict[str, TermRecord], dict[str, int]]:
    a_terms = load_a_layer_terms(db_path)
    b_terms = load_b_layer_terms()
    return {**b_terms, **a_terms}, {"a_layer_terms": len(a_terms), "b_layer_terms": len(b_terms)}


def _segment_gate(
    *,
    corrected_text: str,
    hits: list[dict[str, str]],
    quality_label: str,
    quality_flags: list[str],
    fuzzy: list[dict[str, Any]],
    unresolved: list[str],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if quality_label == "needs_repair":
        reasons.append("quality_label_needs_repair")
        return "repair_required", reasons
    if not hits:
        reasons.append("no_ab_exact_hit")
        return "coverage_only", reasons

    if quality_label != "good":
        reasons.append(f"quality_label_{quality_label}")
    if len(fuzzy) >= 4:
        reasons.append("many_fuzzy_candidates")
    if len(unresolved) >= 8:
        reasons.append("many_unresolved_domain_phrases")
    if len(corrected_text) >= 260:
        reasons.append("long_segment")

    if reasons:
        return "claim_ready_caution", reasons
    return "claim_ready", ["clean_ab_supported_segment"]


def refine_evidence_segments(
    segments: list[dict[str, Any]],
    lexicon: dict[str, TermRecord],
    correction_rules: list[CorrectionRule],
    *,
    repair_candidates: bool = True,
    auto_repair_threshold: float = 0.95,
) -> list[dict[str, Any]]:
    raw_corpus = "\n".join(str(segment.get("raw_text", "")) for segment in segments)
    source_profile = build_source_profile(raw_corpus, lexicon) if repair_candidates else {}
    refined_segments: list[dict[str, Any]] = []

    for segment in segments:
        raw_text = _compact_text(str(segment.get("raw_text", "")))
        corrected, applied, blocked = apply_corrections(raw_text, correction_rules, lexicon)
        profile_applied: list[dict[str, Any]] = []
        if repair_candidates and source_profile:
            corrected, profile_applied = apply_source_profile_repairs(corrected, lexicon, source_profile)

        guided: list[dict[str, Any]] = []
        guided_applied: list[dict[str, Any]] = []
        preliminary_label = transcript_quality_label(transcript_quality_flags(corrected))
        if repair_candidates and preliminary_label == "needs_repair":
            guided = guided_repair_candidates(
                corrected,
                lexicon,
                auto_threshold=auto_repair_threshold,
                max_items=12,
            )
            corrected, guided_applied = apply_guided_repairs(corrected, guided)

        hits = exact_term_hits(corrected, lexicon, max_hits=30)
        fuzzy = fuzzy_review_candidates(corrected, lexicon, max_items=8)
        unresolved = unresolved_domain_phrases(corrected, lexicon)[:12]
        quality_flags = transcript_quality_flags(corrected)
        quality_label = transcript_quality_label(quality_flags)
        gate, gate_reasons = _segment_gate(
            corrected_text=corrected,
            hits=hits,
            quality_label=quality_label,
            quality_flags=quality_flags,
            fuzzy=fuzzy,
            unresolved=unresolved,
        )

        refined = dict(segment)
        refined.update(
            {
                "refined_text": corrected,
                "applied_repairs": [*applied, *profile_applied, *guided_applied],
                "blocked_corrections": blocked,
                "ab_hits": hits,
                "fuzzy_candidates": fuzzy,
                "guided_repair_candidates": guided,
                "unresolved_terms": unresolved,
                "quality_flags": quality_flags,
                "quality_label": quality_label,
                "quality_gate": gate,
                "quality_gate_reasons": gate_reasons,
                "claim_extraction_allowed": gate in {"claim_ready", "claim_ready_caution"},
                "runtime_allowed": False,
            }
        )
        refined_segments.append(refined)

    return refined_segments


def _hit_terms(segment: dict[str, Any], kinds: set[str]) -> list[str]:
    values = [
        str(hit.get("term", ""))
        for hit in segment.get("ab_hits", [])
        if str(hit.get("kind", "")) in kinds and hit.get("term")
    ]
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _implicit_mechanisms(text: str) -> list[str]:
    result: list[str] = []
    for rule in IMPLICIT_MECHANISM_TRIGGERS:
        if not any(token in text for token in rule["requires_any"]):
            continue
        if not any(token in text for token in rule["context_any"]):
            continue
        mechanism = str(rule["mechanism"])
        if mechanism not in result:
            result.append(mechanism)
    return result


def _first_index(text: str, values: list[str]) -> int | None:
    positions = [text.find(value) for value in values if value and text.find(value) >= 0]
    return min(positions) if positions else None


def _term_positions(text: str, terms: list[str]) -> list[tuple[str, int]]:
    positions: list[tuple[str, int]] = []
    for term in terms:
        idx = text.find(term)
        if idx >= 0:
            positions.append((term, idx))
    return sorted(positions, key=lambda item: item[1])


def _resolve_subject(
    text: str,
    species: list[str],
    mechanisms: list[str],
    matched_phrases: list[str],
) -> tuple[str, str, list[str]]:
    if len(species) == 1:
        return species[0], "exact_single_species", species
    if not species:
        if mechanisms:
            return mechanisms[0], "mechanism_subject_fallback", mechanisms
        return "", "missing_subject", []

    phrase_idx = _first_index(text, matched_phrases)
    positions = _term_positions(text, species)
    if phrase_idx is None or not positions:
        return "", "ambiguous_multi_species", species

    nearest = min(positions, key=lambda item: abs(item[1] - phrase_idx))
    return nearest[0], "heuristic_nearest_species", species


def _resolve_synergy_object(text: str, species: list[str], matched_phrases: list[str]) -> tuple[str, Any, str]:
    phrase_idx = _first_index(text, matched_phrases)
    positions = _term_positions(text, species)
    if phrase_idx is None or len(positions) < 2:
        return "", {"relation": "synergy", "targets": species}, "ambiguous_multi_species"

    before = [term for term, idx in positions if idx < phrase_idx]
    after = [term for term, idx in positions if idx > phrase_idx]
    if before and after:
        return before[-1], {"relation": "synergy", "targets": after}, "heuristic_before_phrase_to_after_phrase"
    return "", {"relation": "synergy", "targets": species}, "ambiguous_multi_species"


def build_claim_atoms(source_id: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    for segment in segments:
        text = str(segment.get("refined_text") or segment.get("raw_text") or "")
        implicit_mechanisms = _implicit_mechanisms(text)
        if not segment.get("claim_extraction_allowed") and not implicit_mechanisms:
            continue
        species = _hit_terms(segment, {"species", "species_initial"})
        moves = _hit_terms(segment, {"move"})
        abilities = _hit_terms(segment, {"ability"})
        mechanisms = _hit_terms(segment, {"mechanism", "mechanism_heading"})
        for mechanism in implicit_mechanisms:
            if mechanism not in mechanisms:
                mechanisms.append(mechanism)
        if not (species or mechanisms):
            continue

        local_index = 1
        for pattern in CLAIM_PATTERNS:
            matched = [phrase for phrase in pattern["phrases"] if phrase in text]
            if pattern["object"] == "mark" and not mechanisms:
                # Generic "层" appears in many non-mark contexts. Without an
                # explicit or implicit mechanism anchor, only literal "印记"
                # is safe enough for a raw claim atom.
                matched = [phrase for phrase in matched if phrase == "印记"]
            if (
                pattern["object"] == "mark"
                and mechanisms
                and not any("印记" in mechanism for mechanism in mechanisms)
                and not any(token in text for token in ("印记", "星陨", "星云"))
            ):
                matched = []
            if not matched:
                continue
            subject, subject_status, subject_candidates = _resolve_subject(text, species, mechanisms, matched)
            object_value: Any = pattern["object"]
            if pattern["predicate"] == "has_synergy" and len(species) > 1:
                subject, object_value, subject_status = _resolve_synergy_object(text, species, matched)
                subject_candidates = species
            elif pattern["atom_type"] == "relation_claim" and len(species) > 1:
                subject = ""
                subject_status = "ambiguous_multi_species_relation"
                subject_candidates = species
            atoms.append(
                {
                    "claim_id": f"claim/{source_id}/{segment['segment_id']}/{local_index:02d}",
                    "source_id": source_id,
                    "segment_id": segment["segment_id"],
                    "atom_type": pattern["atom_type"],
                    "subject": subject,
                    "subject_resolution_status": subject_status,
                    "subject_candidates": subject_candidates,
                    "predicate": pattern["predicate"],
                    "object": object_value,
                    "source_phrases": matched,
                    "mentioned_species": species,
                    "mentioned_moves": moves,
                    "mentioned_abilities": abilities,
                    "mentioned_mechanisms": mechanisms,
                    "evidence": {
                        "start_ms": segment.get("start_ms"),
                        "end_ms": segment.get("end_ms"),
                        "quote": text[:220],
                    },
                    "quality_gate": segment.get("quality_gate"),
                    "review_status": "unreviewed",
                    "runtime_allowed": False,
                }
            )
            local_index += 1

        if species and moves:
            subject = species[0] if len(species) == 1 else ""
            subject_status = "exact_single_species" if len(species) == 1 else "ambiguous_multi_species"
            atoms.append(
                {
                    "claim_id": f"claim/{source_id}/{segment['segment_id']}/{local_index:02d}",
                    "source_id": source_id,
                    "segment_id": segment["segment_id"],
                    "atom_type": "species_move_mention",
                    "subject": subject,
                    "subject_resolution_status": subject_status,
                    "subject_candidates": species,
                    "predicate": "source_mentions_move" if subject else "segment_mentions_move",
                    "object": moves[:4],
                    "source_phrases": [],
                    "mentioned_species": species,
                    "mentioned_moves": moves,
                    "mentioned_abilities": abilities,
                    "mentioned_mechanisms": mechanisms,
                    "evidence": {
                        "start_ms": segment.get("start_ms"),
                        "end_ms": segment.get("end_ms"),
                        "quote": text[:220],
                    },
                    "quality_gate": segment.get("quality_gate"),
                    "review_status": "unreviewed",
                    "runtime_allowed": False,
                }
            )

    return atoms


def build_quality_summary(segments: list[dict[str, Any]], atoms: list[dict[str, Any]]) -> dict[str, Any]:
    gate_counts = Counter(str(segment.get("quality_gate", "unknown")) for segment in segments)
    quality_counts = Counter(str(segment.get("quality_label", "unknown")) for segment in segments)
    repair_segments = [
        segment["segment_id"]
        for segment in segments
        if segment.get("quality_gate") == "repair_required"
    ]
    return {
        "segment_count": len(segments),
        "claim_atom_count": len(atoms),
        "quality_label_counts": dict(sorted(quality_counts.items())),
        "quality_gate_counts": dict(sorted(gate_counts.items())),
        "repair_required_segments": repair_segments,
        "claim_extraction_segments": [
            segment["segment_id"]
            for segment in segments
            if segment.get("claim_extraction_allowed")
        ],
        "runtime_allowed": False,
    }


def build_source_manifest_v2(
    *,
    source_id: str,
    source_type: str,
    transcript_method: str,
    segment_source: str,
    source_manifest_v1: dict[str, Any],
    source_manifest_path: Path | None,
    run_dir: Path,
    out_dir: Path,
    asr_json_path: Path | None,
    transcript_path: Path | None,
    ab_refined_path: Path | None,
    ab_manifest_path: Path | None,
    title: str | None,
    source_url: str | None,
    lexicon_counts: dict[str, int],
    quality_summary: dict[str, Any],
) -> dict[str, Any]:
    url = source_url or source_manifest_v1.get("url") or source_manifest_v1.get("source_url")
    resolved_title = title or source_manifest_v1.get("title")
    return {
        "schema_version": "roco.video_source_manifest.v2",
        "source_id": source_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source": {
            "source_type": source_type,
            "url": url,
            "title": resolved_title,
            "origin_manifest_path": _relpath(source_manifest_path),
        },
        "ingest": {
            "transcript_method": transcript_method,
            "segment_source": segment_source,
            "run_dir": _relpath(run_dir),
            "out_dir": _relpath(out_dir),
            "artifacts": {
                "asr_json_path": _relpath(asr_json_path),
                "transcript_path": _relpath(transcript_path),
                "ab_refined_path": _relpath(ab_refined_path),
                "ab_manifest_path": _relpath(ab_manifest_path),
            },
            "lexicon_counts": lexicon_counts,
        },
        "quality": quality_summary,
        "promotion_boundary": {
            "claim_atoms_are": "unreviewed_source_substrate",
            "meta_graph_promotion_requires": "PM/source review plus existing L4 gate",
            "d_layer_promotion_requires": "PM-reviewed expert demonstration extraction",
            "raw_asr_json_publication": "sanitize before publishing; provider URLs are not copied here",
        },
    }


def write_bundle(out_dir: Path, payloads: dict[str, Any]) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "source_manifest_v2": out_dir / "source_manifest_v2.yaml",
        "segments": out_dir / "segments.yaml",
        "quality_gate": out_dir / "quality_gate.yaml",
        "claim_atoms": out_dir / "claim_atoms.yaml",
    }
    paths["source_manifest_v2"].write_text(
        yaml.dump(payloads["source_manifest_v2"], allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )
    paths["segments"].write_text(
        yaml.dump(payloads["segments"], allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )
    paths["quality_gate"].write_text(
        yaml.dump(payloads["quality_gate"], allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )
    paths["claim_atoms"].write_text(
        yaml.dump(payloads["claim_atoms"], allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )
    return {key: str(path) for key, path in paths.items()}


def build_evidence_foundation(
    *,
    source_id: str,
    run_dir: Path,
    out_dir: Path | None = None,
    source_manifest_path: Path | None = None,
    source_type: str = "community_video",
    transcript_method: str = "auto",
    asr_json_path: Path | None = None,
    transcript_path: Path | None = None,
    ab_refined_path: Path | None = None,
    ab_manifest_path: Path | None = None,
    source_url: str | None = None,
    title: str | None = None,
    db_path: Path = DEFAULT_RUNTIME_DB,
    corrections_path: Path | None = DEFAULT_CORRECTIONS_PATH,
    repair_candidates: bool = True,
) -> dict[str, Any]:
    out = out_dir or (run_dir / DEFAULT_OUT_SUBDIR)
    source_manifest_path = source_manifest_path or (run_dir / "source_manifest.yaml")
    source_manifest_v1 = _read_yaml(source_manifest_path)

    raw_segments, segment_source = load_source_segments(
        asr_json_path=asr_json_path,
        transcript_path=transcript_path,
        ab_refined_path=ab_refined_path,
    )
    if not raw_segments:
        raise ValueError("No source segments found. Provide --asr-json, --transcript, or --ab-refined.")

    lexicon, lexicon_counts = load_ab_lexicon(db_path)
    rules = load_corrections(corrections_path)
    refined_segments = refine_evidence_segments(
        raw_segments,
        lexicon,
        rules,
        repair_candidates=repair_candidates,
    )
    claim_atoms = build_claim_atoms(source_id, refined_segments)
    quality_summary = build_quality_summary(refined_segments, claim_atoms)

    resolved_method = transcript_method
    if resolved_method == "auto":
        if asr_json_path:
            resolved_method = "bailian_hotword_asr_or_provider_json"
        elif transcript_path and transcript_path.suffix.lower() in {".srt", ".vtt"}:
            resolved_method = "subtitle"
        elif transcript_path:
            resolved_method = "plain_transcript"
        else:
            resolved_method = "ab_refined_fallback"

    manifest_v2 = build_source_manifest_v2(
        source_id=source_id,
        source_type=source_type,
        transcript_method=resolved_method,
        segment_source=segment_source,
        source_manifest_v1=source_manifest_v1,
        source_manifest_path=source_manifest_path if source_manifest_path.exists() else None,
        run_dir=run_dir,
        out_dir=out,
        asr_json_path=asr_json_path,
        transcript_path=transcript_path,
        ab_refined_path=ab_refined_path,
        ab_manifest_path=ab_manifest_path,
        title=title,
        source_url=source_url,
        lexicon_counts=lexicon_counts,
        quality_summary=quality_summary,
    )

    payloads = {
        "source_manifest_v2": manifest_v2,
        "segments": {
            "schema_version": "roco.evidence_segments.v1",
            "source_id": source_id,
            "runtime_allowed": False,
            "segments": refined_segments,
        },
        "quality_gate": {
            "schema_version": "roco.input_quality_gate.v1",
            "source_id": source_id,
            **quality_summary,
        },
        "claim_atoms": {
            "schema_version": "roco.raw_claim_atoms.v1",
            "source_id": source_id,
            "runtime_allowed": False,
            "review_status": "unreviewed",
            "claim_atoms": claim_atoms,
        },
    }
    paths = write_bundle(out, payloads)
    return {
        "source_id": source_id,
        "out_dir": str(out),
        "paths": paths,
        "quality_summary": quality_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--source-type", default="community_video")
    parser.add_argument("--transcript-method", default="auto")
    parser.add_argument("--asr-json", type=Path)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--ab-refined", type=Path)
    parser.add_argument("--ab-manifest", type=Path)
    parser.add_argument("--source-url")
    parser.add_argument("--title")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_RUNTIME_DB)
    parser.add_argument("--corrections", type=Path, default=DEFAULT_CORRECTIONS_PATH)
    parser.add_argument("--no-repair-candidates", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = build_evidence_foundation(
        source_id=args.source_id,
        run_dir=args.run_dir,
        out_dir=args.out_dir,
        source_manifest_path=args.source_manifest,
        source_type=args.source_type,
        transcript_method=args.transcript_method,
        asr_json_path=args.asr_json,
        transcript_path=args.transcript,
        ab_refined_path=args.ab_refined,
        ab_manifest_path=args.ab_manifest,
        source_url=args.source_url,
        title=args.title,
        db_path=args.db_path,
        corrections_path=args.corrections,
        repair_candidates=not args.no_repair_candidates,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"foundation: {result['out_dir']}")
        print(f"quality: {json.dumps(result['quality_summary'], ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
