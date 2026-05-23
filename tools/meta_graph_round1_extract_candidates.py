#!/usr/bin/env python3
"""Draft first-round Meta Graph set candidates from AB-refined transcripts.

This tool deliberately stops before runtime graph promotion. It can create
L0-L3 extraction artifacts and PM review packets, but it never writes reviewed
Meta Graph cards.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from advisor.battle_dex import DEFAULT_RUNTIME_DB, ensure_battle_dex_sqlite
from tools.transcript_ab_refine import (
    TermRecord,
    exact_term_hits,
    load_a_layer_terms,
    load_b_layer_terms,
    refine_transcript,
    split_paragraphs,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = REPO_ROOT / "artifacts" / "meta_graph_round1_set_input" / "source_queue.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "meta_graph_round1_set_input"

PARAGRAPH_RE = re.compile(r"^###\s+(P\d{3,})\s*$", re.MULTILINE)
REFINED_TEXT_RE = re.compile(r"^- 精校：(.*?)(?=\n- 自动校正：|\Z)", re.MULTILINE | re.DOTALL)
ROLE_KEYWORDS = {
    "首发": "lead",
    "联防": "defensive_pivot",
    "C位": "carry",
    "主C": "carry",
    "收割": "cleaner",
    "清强化": "buff_clear",
    "强化": "setup_or_buff_control",
    "打手": "attacker",
    "猛攻手": "breaker",
    "清线手": "sweeper",
    "传递": "support_enabler",
    "印记": "mark_enabler",
    "天气": "weather_control",
    "沙暴": "sandstorm_control",
}
ARCHETYPE_KEYWORDS = {
    "光合": "photosynthesis_energy_window",
    "武队": "fighting_team",
    "毒": "poison",
    "星陨": "starfall",
    "翼王": "wingking_balance",
    "蓄势": "charge_mark",
    "圣剑": "holy_sword",
    "沙暴": "sandstorm",
    "天气": "weather",
    "电": "electric",
}
EDGE_KEYWORDS = {
    "给": "synergy",
    "传递": "synergy",
    "配合": "synergy",
    "联防": "defensive_cover",
    "防": "defensive_cover",
    "克制": "counterplay",
    "针对": "counterplay",
    "打": "threat_or_counterplay",
    "清除": "counterplay",
    "清强化": "counterplay",
    "压制": "pressure",
}


@dataclass(frozen=True)
class Paragraph:
    span_id: str
    text: str


@dataclass(frozen=True)
class LoadedSource:
    path: Path
    paragraphs: list[Paragraph]
    mode: str


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _relpath(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _resolve_repo_path(value: str | None) -> Path | None:
    if not value or value == "TBD":
        return None
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9一-鿿_-]+", "_", value).strip("_")
    return cleaned or "source"


def load_species_ids(db_path: Path = DEFAULT_RUNTIME_DB) -> dict[str, str]:
    db_path = ensure_battle_dex_sqlite(db_path)
    rows: list[tuple[str, str | None, str]] = []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT display_name, initial_species_name, species_id
            FROM species_form
            """
        ).fetchall()
    mapping: dict[str, str] = {}
    for display_name, initial_name, species_id in rows:
        mapping.setdefault(str(display_name), str(species_id))
        if initial_name:
            mapping.setdefault(str(initial_name), str(species_id))
    return mapping


def parse_refined_paragraphs(text: str) -> list[Paragraph]:
    matches = list(PARAGRAPH_RE.finditer(text))
    if not matches:
        return [Paragraph("P001", text.strip())] if text.strip() else []

    paragraphs: list[Paragraph] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        refined = REFINED_TEXT_RE.search(block)
        if not refined:
            continue
        value = refined.group(1).strip()
        if value:
            paragraphs.append(Paragraph(match.group(1), value))
    return paragraphs


def _terms_by_kind(text: str, lexicon: dict[str, TermRecord]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"species": [], "move": [], "ability": [], "mechanism": []}
    for hit in exact_term_hits(text, lexicon, max_hits=80):
        kind = hit["kind"]
        term = hit["term"]
        if kind in {"species", "species_initial"}:
            buckets["species"].append(term)
        elif kind == "move":
            buckets["move"].append(term)
        elif kind == "ability":
            buckets["ability"].append(term)
        else:
            buckets["mechanism"].append(term)
    return {key: sorted(set(values), key=lambda item: (-len(item), item)) for key, values in buckets.items()}


def _labels_from_keywords(text: str, mapping: dict[str, str]) -> list[dict[str, str]]:
    labels: list[dict[str, str]] = []
    seen: set[str] = set()
    for keyword, label in mapping.items():
        if keyword not in text or label in seen:
            continue
        labels.append({"label": label, "source_phrase": keyword})
        seen.add(label)
    return labels


def _level_for(terms: dict[str, list[str]], role_labels: list[dict[str, str]], archetype_tags: list[str]) -> str:
    if terms["species"] and terms["move"]:
        return "L2"
    if terms["species"] and (role_labels or archetype_tags):
        return "L1"
    if terms["species"] or archetype_tags:
        return "L0"
    return "discard"


def draft_candidates(
    source_id: str,
    source_ref: str,
    paragraphs: list[Paragraph],
    lexicon: dict[str, TermRecord],
    species_ids: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    candidate_sets: list[dict[str, Any]] = []
    candidate_edges: list[dict[str, Any]] = []
    counters = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "discard": 0}

    set_index = 1
    edge_index = 1
    for paragraph in paragraphs:
        terms = _terms_by_kind(paragraph.text, lexicon)
        role_hits = _labels_from_keywords(paragraph.text, ROLE_KEYWORDS)
        archetype_hits = _labels_from_keywords(paragraph.text, ARCHETYPE_KEYWORDS)
        archetype_tags = [hit["label"] for hit in archetype_hits]
        level = _level_for(terms, role_hits, archetype_tags)
        counters[level] += 1
        if level != "discard":
            species = [
                {
                    "raw": name,
                    "canonical_species_name": name,
                    "canonical_species_id": species_ids.get(name, ""),
                    "resolution_status": "exact" if species_ids.get(name) else "review_required",
                }
                for name in terms["species"]
            ]
            moves = [
                {
                    "raw": name,
                    "canonical_move_name": name,
                    "resolution_status": "exact",
                }
                for name in terms["move"]
            ]
            candidate_sets.append(
                {
                    "candidate_id": f"cand/{source_id}/set/{set_index:03d}",
                    "level": level,
                    "source_span_ids": [paragraph.span_id],
                    "archetype_tags": archetype_tags,
                    "source_names": {
                        "species": terms["species"],
                        "moves": terms["move"],
                        "abilities": terms["ability"],
                        "mechanisms": terms["mechanism"],
                    },
                    "resolved": {"species": species, "moves": moves},
                    "inferred_roles": [
                        {
                            "species_name": terms["species"][0] if terms["species"] else "",
                            "role_labels": [hit["label"] for hit in role_hits],
                            "source_phrase": ", ".join(hit["source_phrase"] for hit in role_hits),
                        }
                    ] if role_hits else [],
                    "selected_moves": [
                        {
                            "species_name": terms["species"][0] if terms["species"] else "",
                            "moves": terms["move"],
                            "completeness": "partial" if terms["move"] else "unknown",
                        }
                    ],
                    "source_excerpt": paragraph.text[:240],
                    "unresolved_terms": [],
                    "promotion_blockers": _promotion_blockers(level, species, terms),
                }
            )
            set_index += 1

        edge_hits = _labels_from_keywords(paragraph.text, EDGE_KEYWORDS)
        if len(terms["species"]) >= 2 and edge_hits:
            counters["L3"] += 1
            candidate_edges.append(
                {
                    "candidate_id": f"cand/{source_id}/edge/{edge_index:03d}",
                    "level": "L3",
                    "source_span_ids": [paragraph.span_id],
                    "source_species_or_sets": terms["species"][:1],
                    "target_species_or_sets": terms["species"][1:],
                    "edge_type": edge_hits[0]["label"],
                    "source_claim": paragraph.text[:240],
                    "reasoning_quality": "source_phrase_only",
                    "unresolved_terms": [],
                }
            )
            edge_index += 1

    set_payload = {
        "source_id": source_id,
        "source_ref": source_ref,
        "runtime_allowed": False,
        "candidate_sets": candidate_sets,
    }
    edge_payload = {
        "source_id": source_id,
        "source_ref": source_ref,
        "runtime_allowed": False,
        "candidate_edges": candidate_edges,
    }
    return set_payload, edge_payload, counters


def _promotion_blockers(level: str, species: list[dict[str, str]], terms: dict[str, list[str]]) -> list[str]:
    blockers: list[str] = ["pm_review_required"]
    if level != "L2":
        blockers.append("not_enough_fields_for_card_candidate")
    if any(not item["canonical_species_id"] for item in species):
        blockers.append("species_name_review_required")
    if not terms["move"]:
        blockers.append("selected_moves_missing")
    return blockers


def load_source_paragraphs(
    source: dict[str, Any],
    out_root: Path,
    *,
    refine_missing: bool = False,
) -> LoadedSource | None:
    refined = _resolve_repo_path(source.get("refined_artifact"))
    if refined and refined.exists():
        return LoadedSource(
            path=refined,
            paragraphs=parse_refined_paragraphs(refined.read_text(encoding="utf-8", errors="ignore")),
            mode="ab_refined",
        )

    generated_refined = out_root / "source_runs" / _slug(str(source.get("source_id", ""))) / f"{_slug(str(source.get('source_id', '')))}.ab_refined.md"
    if generated_refined.exists() and not refine_missing:
        return LoadedSource(
            path=generated_refined,
            paragraphs=parse_refined_paragraphs(generated_refined.read_text(encoding="utf-8", errors="ignore")),
            mode="ab_refined_generated",
        )

    raw = _resolve_repo_path(source.get("url_or_path"))
    if not raw or not raw.exists() or source.get("source_type") == "bilibili_url_tbd":
        return None

    if not refine_missing:
        paragraphs = [
            Paragraph(f"P{index:03d}", text)
            for index, text in enumerate(split_paragraphs(raw.read_text(encoding="utf-8", errors="ignore")), start=1)
        ]
        return LoadedSource(path=raw, paragraphs=paragraphs, mode="raw_exact_only")

    out_dir = out_root / "source_runs" / _slug(str(source["source_id"]))
    manifest = refine_transcript(
        raw,
        out_dir=out_dir,
        source_id=str(source["source_id"]),
        include_unresolved=True,
    )
    cleaned = _resolve_repo_path(manifest["cleaned_path"])
    if not cleaned or not cleaned.exists():
        return None
    return LoadedSource(
        path=cleaned,
        paragraphs=parse_refined_paragraphs(cleaned.read_text(encoding="utf-8", errors="ignore")),
        mode="ab_refined_generated",
    )


def write_review_packet(
    path: Path,
    source: dict[str, Any],
    set_payload: dict[str, Any],
    edge_payload: dict[str, Any],
    counters: dict[str, int],
) -> None:
    lines = [
        f"# PM Review Packet: {source['source_id']}",
        "",
        f"- source: `{source.get('url_or_path', '')}`",
        f"- target_archetype: {source.get('target_archetype', '')}",
        f"- runtime_allowed: false",
        f"- counters: {json.dumps(counters, ensure_ascii=False, sort_keys=True)}",
        "",
        "## Promotion Rule",
        "",
        "Only manually reviewed L2 candidates can become graph cards. L0/L1 are coverage signals. L3 edges require source-fidelity review.",
        "",
        "## Strongest Set Candidates",
        "",
    ]
    candidates = sorted(
        set_payload["candidate_sets"],
        key=lambda item: (item["level"] != "L2", item["level"], item["candidate_id"]),
    )
    for item in candidates[:12]:
        species = ", ".join(item["source_names"]["species"]) or "none"
        moves = ", ".join(item["source_names"]["moves"]) or "none"
        blockers = ", ".join(item["promotion_blockers"]) or "none"
        lines.extend(
            [
                f"### {item['candidate_id']} [{item['level']}]",
                "",
                f"- span: {', '.join(item['source_span_ids'])}",
                f"- species: {species}",
                f"- moves: {moves}",
                f"- blockers: {blockers}",
                f"- excerpt: {item['source_excerpt']}",
                "",
            ]
        )
    lines.extend(["## Relation Candidates", ""])
    for item in edge_payload["candidate_edges"][:12]:
        lines.extend(
            [
                f"### {item['candidate_id']} [{item['edge_type']}]",
                "",
                f"- span: {', '.join(item['source_span_ids'])}",
                f"- source: {', '.join(item['source_species_or_sets'])}",
                f"- target: {', '.join(item['target_species_or_sets'])}",
                f"- claim: {item['source_claim']}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_coverage_markdown(path: Path, report: dict[str, Any]) -> None:
    extracted = [item for item in report["summaries"] if item["status"] == "extracted"]
    skipped = [item for item in report["summaries"] if item["status"] != "extracted"]
    total_sets = sum(int(item.get("candidate_set_count", 0)) for item in extracted)
    total_edges = sum(int(item.get("candidate_edge_count", 0)) for item in extracted)
    total_l2 = sum(int(item.get("level_counts", {}).get("L2", 0)) for item in extracted)
    lines = [
        "# Meta Graph Round 1 Coverage Report",
        "",
        f"- runtime_allowed: `{str(report.get('runtime_allowed', False)).lower()}`",
        f"- processed_sources: `{len(extracted)}`",
        f"- skipped_sources: `{len(skipped)}`",
        f"- candidate_sets: `{total_sets}`",
        f"- l2_card_candidates: `{total_l2}`",
        f"- candidate_edges: `{total_edges}`",
        "",
        "## Source Summary",
        "",
        "| source_id | mode | sets | L2 | edges | status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in report["summaries"]:
        counts = item.get("level_counts", {})
        lines.append(
            "| {source_id} | {mode} | {sets} | {l2} | {edges} | {status} |".format(
                source_id=item["source_id"],
                mode=item.get("source_mode", ""),
                sets=item.get("candidate_set_count", 0),
                l2=counts.get("L2", 0),
                edges=item.get("candidate_edge_count", 0),
                status=item["status"] if item["status"] == "extracted" else item.get("reason", item["status"]),
            )
        )
    lines.extend(
        [
            "",
            "## Reading Rules",
            "",
            "- L2 means mechanically extractable card candidate, not a reviewed Meta Graph card.",
            "- raw_exact_only sources need AB-refine before promotion.",
            "- Large overview sources are coverage sources first; promote only source-span-specific claims.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    queue_path: Path,
    out_root: Path,
    source_ids: set[str] | None = None,
    limit: int | None = None,
    *,
    refine_missing: bool = False,
) -> dict[str, Any]:
    queue = _read_yaml(queue_path)
    out_root.mkdir(parents=True, exist_ok=True)
    lexicon = {**load_b_layer_terms(), **load_a_layer_terms(DEFAULT_RUNTIME_DB)}
    species_ids = load_species_ids(DEFAULT_RUNTIME_DB)
    summaries: list[dict[str, Any]] = []

    sources = queue.get("sources", [])
    if source_ids:
        sources = [source for source in sources if str(source.get("source_id")) in source_ids]
    if limit:
        sources = sources[:limit]

    for source in sources:
        source_id = str(source.get("source_id", "")).strip()
        if not source_id:
            continue
        loaded = load_source_paragraphs(source, out_root, refine_missing=refine_missing)
        if not loaded:
            summaries.append({"source_id": source_id, "status": "skipped", "reason": "missing_or_blocked_source"})
            continue

        set_payload, edge_payload, counters = draft_candidates(
            source_id,
            _relpath(loaded.path),
            loaded.paragraphs,
            lexicon,
            species_ids,
        )
        _write_yaml(out_root / "extracted" / f"{source_id}.candidate_sets.yaml", set_payload)
        _write_yaml(out_root / "extracted" / f"{source_id}.candidate_edges.yaml", edge_payload)
        write_review_packet(
            out_root / "review_packets" / f"{source_id}.pm_review.md",
            source,
            set_payload,
            edge_payload,
            counters,
        )
        summaries.append(
            {
                "source_id": source_id,
                "status": "extracted",
                "source_ref": _relpath(loaded.path),
                "source_mode": loaded.mode,
                "paragraph_count": len(loaded.paragraphs),
                "candidate_set_count": len(set_payload["candidate_sets"]),
                "candidate_edge_count": len(edge_payload["candidate_edges"]),
                "level_counts": counters,
            }
        )

    report = {
        "round_id": queue.get("round_id", "meta_graph_round1_set_input"),
        "runtime_allowed": False,
        "source_count": len(summaries),
        "summaries": summaries,
    }
    _write_yaml(out_root / "round1_coverage_report.yaml", report)
    write_coverage_markdown(out_root / "round1_coverage_report.md", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--source-id", action="append", help="Limit extraction to one source id; can be repeated")
    parser.add_argument("--limit", type=int, help="Limit processed sources after source-id filtering")
    parser.add_argument(
        "--refine-missing",
        action="store_true",
        help="Run full AB refinement for sources without refined_artifact. Default uses exact-only raw/corrected text for speed.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(
        args.queue,
        args.out_root,
        source_ids=set(args.source_id) if args.source_id else None,
        limit=args.limit,
        refine_missing=args.refine_missing,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"sources: {report['source_count']}")
        for item in report["summaries"]:
            print(
                f"{item['source_id']}: {item['status']}"
                + (f" sets={item.get('candidate_set_count', 0)} edges={item.get('candidate_edge_count', 0)}" if item["status"] == "extracted" else f" reason={item.get('reason', '')}")
            )


if __name__ == "__main__":
    main()
