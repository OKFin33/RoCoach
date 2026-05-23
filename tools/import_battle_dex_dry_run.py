#!/usr/bin/env python3
"""P1e battle dex importer dry-run.

Consumes wiki artifact files and a manual supplement layer, then emits a
reviewable importer decision set without mutating SQLite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


DEFAULT_OUTPUT_ROOT = Path("data/importer_runs")
DEFAULT_SUPPLEMENT_PATH = Path("data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml")


@dataclass(frozen=True)
class ManualMoveSupplement:
    move_name: str
    move_type: str | None
    category_raw: str | None
    energy_cost: int | None
    power: int | None
    effect_text: str | None
    section_ref: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManualSpeciesCanonicalOverride:
    species_id: str
    canonical_display_name: str
    preferred_source_page_id: str
    normalized_initial_species_name: str | None
    normalized_evolution_stage: str | None
    override_ability_name: str | None
    override_ability_effect_text: str | None
    section_ref: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManualSupplement:
    excluded_forms: list[str]
    species_canonical_overrides: dict[str, ManualSpeciesCanonicalOverride]
    manual_moves: dict[str, ManualMoveSupplement]
    move_aliases: dict[str, str]
    ability_text_overrides: dict[str, str]
    source_ref: str


class ArtifactWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, filename: str, payload: Any) -> Path:
        path = self.output_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def write_jsonl(self, filename: str, rows: list[dict[str, Any]]) -> Path:
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return path

    def write_text(self, filename: str, text: str) -> Path:
        path = self.output_dir / filename
        path.write_text(text, encoding="utf-8")
        return path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ_p1e_importer_dry_run")


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized in {"", "null", "None"}:
        return None
    return int(normalized)


def normalize_effect_text_for_grouping(text: str) -> str:
    return (
        text.strip()
        .replace("，", ",")
        .replace("：", ":")
        .replace("；", ";")
        .replace("（", "(")
        .replace("）", ")")
    )


def parse_manual_supplement_markdown(path: Path) -> ManualSupplement:
    text = path.read_text(encoding="utf-8")
    excluded_forms_match = re.search(
        r"Current excluded forms:\n\n(?P<body>(?:- .+\n)+)",
        text,
        re.MULTILINE,
    )
    excluded_forms: list[str] = []
    if excluded_forms_match:
        excluded_forms = [
            line[2:].strip()
            for line in excluded_forms_match.group("body").strip().splitlines()
            if line.startswith("- ")
        ]

    species_canonical_overrides: dict[str, ManualSpeciesCanonicalOverride] = {}
    override_section_match = re.search(
        r"## Manual Species Canonical Overrides\n(?P<body>.*?)(?:\n## |\Z)",
        text,
        re.DOTALL,
    )
    if override_section_match:
        body = override_section_match.group("body")
        for match in re.finditer(r"### (?P<name>.+?)\n(?P<section>.*?)(?=\n### |\Z)", body, re.DOTALL):
            name = match.group("name").strip()
            section = match.group("section")
            fields: dict[str, str] = {}
            note_lines: list[str] = []
            collecting_notes = False
            for raw_line in section.splitlines():
                line = raw_line.strip()
                if line.startswith("- notes:"):
                    collecting_notes = True
                    continue
                if collecting_notes and line.startswith("- "):
                    note_lines.append(line[2:].strip())
                    continue
                collecting_notes = False
                if line.startswith("- ") and ": " in line:
                    key, value = line[2:].split(": ", 1)
                    fields[key.strip()] = value.strip().strip("`")
            species_id = fields.get("species_id")
            preferred_source_page_id = fields.get("preferred_source_page_id")
            canonical_display_name = fields.get("canonical_display_name") or name
            if species_id and preferred_source_page_id:
                species_canonical_overrides[species_id] = ManualSpeciesCanonicalOverride(
                    species_id=species_id,
                    canonical_display_name=canonical_display_name,
                    preferred_source_page_id=preferred_source_page_id,
                    normalized_initial_species_name=fields.get("normalized_initial_species_name"),
                    normalized_evolution_stage=fields.get("normalized_evolution_stage"),
                    override_ability_name=fields.get("override_ability_name"),
                    override_ability_effect_text=fields.get("override_ability_effect_text"),
                    section_ref=f"{path.name}::{name}",
                    notes=tuple(note_lines),
                )

    manual_moves: dict[str, ManualMoveSupplement] = {}
    move_section_match = re.search(
        r"## Manual Move Supplements\n(?P<body>.*?)(?:\n## |\Z)",
        text,
        re.DOTALL,
    )
    if move_section_match:
        body = move_section_match.group("body")
        for match in re.finditer(r"### (?P<name>.+?)\n(?P<section>.*?)(?=\n### |\Z)", body, re.DOTALL):
            name = match.group("name").strip()
            section = match.group("section")
            fields: dict[str, str] = {}
            for raw_line in section.splitlines():
                line = raw_line.strip()
                if line.startswith("- ") and ": " in line:
                    key, value = line[2:].split(": ", 1)
                    fields[key.strip()] = value.strip()
            if "move_name" in fields:
                manual_moves[fields["move_name"]] = ManualMoveSupplement(
                    move_name=fields["move_name"],
                    move_type=fields.get("move_type"),
                    category_raw=fields.get("category_raw"),
                    energy_cost=parse_int(fields.get("energy_cost")),
                    power=parse_int(fields.get("power")),
                    effect_text=fields.get("effect_text"),
                    section_ref=f"{path.name}::{name}",
                    notes=(),
                )

    move_aliases: dict[str, str] = {}
    alias_section_match = re.search(
        r"## Manual Move Alias Rules\n(?P<body>.*?)(?:\n## |\Z)",
        text,
        re.DOTALL,
    )
    if alias_section_match:
        body = alias_section_match.group("body")
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line.startswith("- alias: "):
                continue
            payload = line[len("- alias: "):]
            if " -> " not in payload:
                continue
            source_name, target_name = payload.split(" -> ", 1)
            if source_name.strip() and target_name.strip():
                move_aliases[source_name.strip()] = target_name.strip()

    ability_text_overrides: dict[str, str] = {}
    pending_match = re.search(
        r"## Pending Human Clarification\n(?P<body>.*?)(?:\n## |\Z)",
        text,
        re.DOTALL,
    )
    if pending_match:
        body = pending_match.group("body")
        for match in re.finditer(r"### (?P<name>.+?)\n(?P<section>.*?)(?=\n### |\Z)", body, re.DOTALL):
            name = match.group("name").strip()
            section = match.group("section")
            confirmed_match = re.search(
                r"Human-confirmed current text:\n\n- (?P<text>.+)",
                section,
                re.MULTILINE,
            )
            if confirmed_match:
                ability_text_overrides[name] = confirmed_match.group("text").strip()

    return ManualSupplement(
        excluded_forms=excluded_forms,
        species_canonical_overrides=species_canonical_overrides,
        manual_moves=manual_moves,
        move_aliases=move_aliases,
        ability_text_overrides=ability_text_overrides,
        source_ref=str(path),
    )


def parse_manual_supplement_structured(path: Path) -> ManualSupplement:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Structured supplement must be a mapping: {path}")

    exclusions = payload.get("exclusions", {})
    species_forms = exclusions.get("species_forms", []) if isinstance(exclusions, dict) else []
    excluded_forms = [row["display_name"] for row in species_forms if isinstance(row, dict) and row.get("display_name")]

    species_canonical_overrides: dict[str, ManualSpeciesCanonicalOverride] = {}
    for row in payload.get("species_canonical_overrides", []):
        if not isinstance(row, dict):
            continue
        species_id = row.get("species_id")
        preferred_source_page_id = row.get("preferred_source_page_id")
        canonical_display_name = row.get("canonical_display_name")
        if species_id and preferred_source_page_id and canonical_display_name:
            species_canonical_overrides[species_id] = ManualSpeciesCanonicalOverride(
                species_id=species_id,
                canonical_display_name=canonical_display_name,
                preferred_source_page_id=preferred_source_page_id,
                normalized_initial_species_name=row.get("normalized_initial_species_name"),
                normalized_evolution_stage=row.get("normalized_evolution_stage"),
                override_ability_name=row.get("override_ability_name"),
                override_ability_effect_text=row.get("override_ability_effect_text"),
                section_ref=f"{path.name}::{canonical_display_name}",
                notes=tuple(row.get("notes", []) or ()),
            )

    manual_moves: dict[str, ManualMoveSupplement] = {}
    for row in payload.get("manual_moves", []):
        if not isinstance(row, dict) or not row.get("move_name"):
            continue
        move_name = row["move_name"]
        manual_moves[move_name] = ManualMoveSupplement(
            move_name=move_name,
            move_type=row.get("move_type"),
            category_raw=row.get("category_raw"),
            energy_cost=row.get("energy_cost"),
            power=row.get("power"),
            effect_text=row.get("effect_text"),
            section_ref=f"{path.name}::{move_name}",
            notes=tuple(row.get("notes", []) or ()),
        )

    move_aliases: dict[str, str] = {}
    for row in payload.get("move_aliases", []):
        if not isinstance(row, dict):
            continue
        source_name = row.get("source_move_name")
        target_name = row.get("target_move_name")
        if source_name and target_name:
            move_aliases[source_name] = target_name

    ability_text_overrides: dict[str, str] = {}
    for row in payload.get("ability_text_overrides", []):
        if not isinstance(row, dict):
            continue
        ability_name = row.get("ability_name")
        override_text = row.get("override_text")
        if ability_name and override_text:
            ability_text_overrides[ability_name] = override_text

    return ManualSupplement(
        excluded_forms=excluded_forms,
        species_canonical_overrides=species_canonical_overrides,
        manual_moves=manual_moves,
        move_aliases=move_aliases,
        ability_text_overrides=ability_text_overrides,
        source_ref=str(path),
    )


def parse_manual_supplement(path: Path) -> ManualSupplement:
    if path.suffix.lower() in {".yaml", ".yml", ".json"}:
        return parse_manual_supplement_structured(path)
    return parse_manual_supplement_markdown(path)


def record_base(
    *,
    entity_type: str,
    entity_key: str,
    resolution_status: str,
    canonical_source_layer: str,
    wiki_source_refs: list[str],
    supplement_refs: list[str],
    resolution_reason: str,
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "entity_key": entity_key,
        "resolution_status": resolution_status,
        "canonical_source_layer": canonical_source_layer,
        "wiki_source_refs": wiki_source_refs,
        "supplement_refs": supplement_refs,
        "resolution_reason": resolution_reason,
    }


def build_summary(
    *,
    run_id: str,
    canonical_artifact_dir: Path,
    output_dir: Path,
    counts: dict[str, int],
    unresolved_move_names: list[str],
    review_required_titles: list[str],
    excluded_titles: list[str],
) -> str:
    lines = [
        "# P1e Importer Dry-Run Summary",
        "",
        f"- Run ID: `{run_id}`",
        f"- Canonical artifact dir: `{canonical_artifact_dir}`",
        f"- Output directory: `{output_dir}`",
        "- SQLite mutation: not performed",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")

    lines.extend(["", "## Excluded Entities", ""])
    if excluded_titles:
        for title in excluded_titles:
            lines.append(f"- {title}")
    else:
        lines.append("- None")

    lines.extend(["", "## Review Required", ""])
    if review_required_titles:
        for title in review_required_titles:
            lines.append(f"- {title}")
    else:
        lines.append("- None")

    lines.extend(["", "## Remaining Unresolved Move Names", ""])
    if unresolved_move_names:
        for name in unresolved_move_names:
            lines.append(f"- {name}")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def group_rows_by_key(rows: list[dict[str, Any]], key_field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key_field]].append(row)
    return grouped


def apply_species_canonical_override(
    species_row: dict[str, Any],
    canonical_override: ManualSpeciesCanonicalOverride | None,
) -> tuple[dict[str, Any], bool]:
    row = dict(species_row)
    if canonical_override is None:
        return row, False

    changed = False

    if row.get("display_name") != canonical_override.canonical_display_name:
        row["display_name"] = canonical_override.canonical_display_name
        changed = True
    if (
        canonical_override.normalized_initial_species_name
        and row.get("initial_species_name") != canonical_override.normalized_initial_species_name
    ):
        row["initial_species_name"] = canonical_override.normalized_initial_species_name
        changed = True
    if canonical_override.normalized_evolution_stage and row.get("evolution_stage") != canonical_override.normalized_evolution_stage:
        row["evolution_stage"] = canonical_override.normalized_evolution_stage
        changed = True
    if canonical_override.override_ability_name and row.get("ability_name") != canonical_override.override_ability_name:
        row["ability_name"] = canonical_override.override_ability_name
        changed = True
    if (
        canonical_override.override_ability_effect_text
        and row.get("ability_effect_text") != canonical_override.override_ability_effect_text
    ):
        row["ability_effect_text"] = canonical_override.override_ability_effect_text
        changed = True

    if changed:
        row["normalization_warnings"] = sorted(
            {
                *(row.get("normalization_warnings") or []),
                "manual_species_canonical_override",
            }
        )

    return row, changed


def build_ability_candidates_from_resolved_species(
    run_id: str,
    resolved_species_forms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for species in resolved_species_forms:
        ability_name = species.get("ability_name")
        effect_text = species.get("ability_effect_text")
        if not ability_name or not effect_text:
            continue
        grouped[ability_name][normalize_effect_text_for_grouping(effect_text)].append(species)

    candidates: list[dict[str, Any]] = []
    for ability_name, text_map in sorted(grouped.items()):
        conflict = len(text_map) > 1
        for _, sources in sorted(text_map.items(), key=lambda item: item[0]):
            preferred_source = next(
                (source for source in sources if source.get("canonical_source_layer") == "manual_supplement"),
                sources[0],
            )
            effect_text = preferred_source["ability_effect_text"]
            source_species_ids = sorted({source["species_id"] for source in sources})
            source_page_ids = sorted({source["source_page_id"] for source in sources})
            supplement_refs = sorted({ref for source in sources for ref in source.get("supplement_refs", [])})
            source_layers = sorted({source.get("canonical_source_layer", "wiki") for source in sources})
            candidates.append(
                {
                    "run_id": run_id,
                    "ability_id": stable_id("ability", ability_name, effect_text if conflict else ""),
                    "ability_name": ability_name,
                    "effect_text": effect_text,
                    "source_species_ids": source_species_ids,
                    "source_page_ids": source_page_ids,
                    "supplement_refs": supplement_refs,
                    "source_layers": source_layers,
                    "derivation_status": (
                        "conflict_review_required"
                        if conflict
                        else ("merged_consistent" if len(sources) > 1 else "single_source")
                    ),
                    "confidence": "provisional" if conflict else "confirmed",
                    "normalization_warnings": ["ability_description_conflict"] if conflict else [],
                }
            )
    return candidates


def run_importer_dry_run(args: argparse.Namespace) -> dict[str, Path]:
    run_id = args.run_id or make_run_id()
    canonical_dir = args.canonical_artifact_dir.resolve()
    output_dir = (args.output_dir or (DEFAULT_OUTPUT_ROOT / run_id)).resolve()
    writer = ArtifactWriter(output_dir)
    started_at = utc_now()
    supplement = parse_manual_supplement(args.supplement_path)

    manifest = load_json(canonical_dir / "run_manifest.json")
    source_pages = load_jsonl(canonical_dir / "source_pages.jsonl")
    species_candidates = load_jsonl(canonical_dir / "species_form_candidates.jsonl")
    move_candidates = load_jsonl(canonical_dir / "move_candidates.jsonl")
    raw_ability_candidates = load_jsonl(canonical_dir / "derived_ability_candidates.jsonl")
    move_pool_candidates = load_jsonl(canonical_dir / "species_move_pool_candidates.jsonl")
    validation_events = load_jsonl(canonical_dir / "validation_events.jsonl")

    source_page_title_by_id = {row["source_page_id"]: row["page_title"] for row in source_pages}
    move_id_by_name = {row["move_name"]: row["move_id"] for row in move_candidates}
    move_name_aliases = dict(supplement.move_aliases)

    resolved_species_forms: list[dict[str, Any]] = []
    resolved_moves: list[dict[str, Any]] = []
    resolved_abilities: list[dict[str, Any]] = []
    excluded_entities: list[dict[str, Any]] = []
    review_required_entities: list[dict[str, Any]] = []
    supplement_backed_entities: list[dict[str, Any]] = []
    unresolved_entities: list[dict[str, Any]] = []

    excluded_title_set = set(supplement.excluded_forms)
    excluded_source_page_ids = {
        source_page_id
        for source_page_id, title in source_page_title_by_id.items()
        if title in excluded_title_set
    }

    seen_excluded_titles: set[str] = set()
    for title in supplement.excluded_forms:
        if title in seen_excluded_titles:
            continue
        seen_excluded_titles.add(title)
        source_ids = [
            source_page_id
            for source_page_id, page_title in source_page_title_by_id.items()
            if page_title == title
        ]
        excluded_entities.append(
            {
                **record_base(
                    entity_type="species_form",
                    entity_key=stable_id("excluded_species", title),
                    resolution_status="excluded",
                    canonical_source_layer="manual_supplement",
                    wiki_source_refs=source_ids,
                    supplement_refs=[supplement.source_ref],
                    resolution_reason="hidden plot-only / non-human-facing form excluded by policy B",
                ),
                "display_name": title,
            }
        )

    review_source_page_ids = set()
    hard_reject_species = [
        event
        for event in validation_events
        if event["entity_type"] == "species" and event["severity"] == "hard_reject"
    ]
    for event in hard_reject_species:
        source_page_id = event["source_page_id"]
        if source_page_id in excluded_source_page_ids:
            continue
        review_source_page_ids.add(source_page_id)

    grouped_species = group_rows_by_key(species_candidates, "species_id")
    for species_id, species_rows in sorted(grouped_species.items()):
        source_page_ids = sorted({row["source_page_id"] for row in species_rows})
        page_title = source_page_title_by_id.get(source_page_ids[0], source_page_ids[0])
        canonical_override = supplement.species_canonical_overrides.get(species_id)

        if any(source_page_id in excluded_source_page_ids for source_page_id in source_page_ids):
            continue

        if len(species_rows) > 1:
            if canonical_override:
                preferred_rows = [
                    row for row in species_rows if row["source_page_id"] == canonical_override.preferred_source_page_id
                ]
                if len(preferred_rows) == 1:
                    species = preferred_rows[0]
                    row, _ = apply_species_canonical_override(species, canonical_override)
                    row.update(
                        record_base(
                            entity_type="species_form",
                            entity_key=species["species_id"],
                            resolution_status="supplement_backed",
                            canonical_source_layer="manual_supplement",
                            wiki_source_refs=source_page_ids,
                            supplement_refs=[canonical_override.section_ref],
                            resolution_reason=(
                                "manual supplement selected canonical wiki source for duplicate playable species pages"
                            ),
                        )
                    )
                    resolved_species_forms.append(row)
                    supplement_backed_entities.append(dict(row))
                    continue
            review_required_entities.append(
                {
                    **record_base(
                        entity_type="species_form",
                        entity_key=species_id,
                        resolution_status="review_required",
                        canonical_source_layer="wiki",
                        wiki_source_refs=source_page_ids,
                        supplement_refs=[],
                        resolution_reason="multiple wiki pages collapsed to the same species_id; human review required before ingest",
                    ),
                    "display_name": page_title,
                }
            )
            review_source_page_ids.update(source_page_ids)
            continue

        species = species_rows[0]
        source_page_id = species["source_page_id"]
        base_stats = species.get("base_stats", {})
        all_zero_stats = bool(base_stats) and all((value or 0) == 0 for value in base_stats.values())

        if all_zero_stats:
            review_source_page_ids.add(source_page_id)

        if source_page_id in review_source_page_ids:
            review_required_entities.append(
                {
                    **record_base(
                        entity_type="species_form",
                        entity_key=species["species_id"],
                        resolution_status="review_required",
                        canonical_source_layer="wiki",
                        wiki_source_refs=[source_page_id],
                        supplement_refs=[],
                        resolution_reason=(
                            "species page uses placeholder / zero base stats and needs human review"
                            if all_zero_stats
                            else "species page failed canonical normalization and is not covered by explicit exclusion policy"
                        ),
                    ),
                    "display_name": page_title,
                }
            )
            continue

        row, has_manual_override = apply_species_canonical_override(species, canonical_override)
        if has_manual_override:
            row.update(
                record_base(
                    entity_type="species_form",
                    entity_key=species["species_id"],
                    resolution_status="supplement_backed",
                    canonical_source_layer="manual_supplement",
                    wiki_source_refs=[source_page_id],
                    supplement_refs=[canonical_override.section_ref],
                    resolution_reason="manual supplement corrected a species-level canonical field while preserving wiki provenance",
                )
            )
            supplement_backed_entities.append(dict(row))
        else:
            row.update(
                record_base(
                    entity_type="species_form",
                    entity_key=species["species_id"],
                    resolution_status="included",
                    canonical_source_layer="wiki",
                    wiki_source_refs=[source_page_id],
                    supplement_refs=[],
                    resolution_reason="eligible wiki canonical species/form candidate",
                )
            )
        resolved_species_forms.append(row)

    reviewed_species_source_ids = {row["wiki_source_refs"][0] for row in review_required_entities if row["wiki_source_refs"]}
    for source_page_id in sorted(review_source_page_ids.difference(reviewed_species_source_ids)):
        title = source_page_title_by_id.get(source_page_id, source_page_id)
        review_required_entities.append(
            {
                **record_base(
                    entity_type="species_form",
                    entity_key=stable_id("review_species", title),
                    resolution_status="review_required",
                    canonical_source_layer="wiki",
                    wiki_source_refs=[source_page_id],
                    supplement_refs=[],
                    resolution_reason="species page failed canonical normalization and is not covered by explicit exclusion policy",
                ),
                "display_name": title,
            }
        )

    for move in move_candidates:
        row = dict(move)
        row.update(
            record_base(
                entity_type="move",
                entity_key=move["move_id"],
                resolution_status="included",
                canonical_source_layer="wiki",
                wiki_source_refs=[move["source_page_id"]],
                supplement_refs=[],
                resolution_reason="wiki canonical move candidate from 技能信息",
            )
        )
        resolved_moves.append(row)

    for move_name, supplement_move in sorted(supplement.manual_moves.items()):
        if move_name in move_id_by_name:
            continue
        move_id = stable_id("supplement_move", move_name)
        payload = {
            "run_id": run_id,
            "move_id": move_id,
            "move_name": supplement_move.move_name,
            "move_type": supplement_move.move_type,
            "category_raw": supplement_move.category_raw,
            "power": supplement_move.power,
            "energy_cost": supplement_move.energy_cost,
            "effect_text": supplement_move.effect_text,
            "description_text": None,
            "source_version": None,
            "source_page_id": None,
            "raw_snapshot_id": None,
            "confidence": "provisional",
            "normalization_warnings": ["manual_supplement_record"],
            **record_base(
                entity_type="move",
                entity_key=move_id,
                resolution_status="supplement_backed",
                canonical_source_layer="manual_supplement",
                wiki_source_refs=[],
                supplement_refs=[supplement_move.section_ref],
                resolution_reason="manual supplement fills missing wiki canonical move coverage",
            ),
        }
        resolved_moves.append(payload)
        supplement_backed_entities.append(payload)
        move_id_by_name[move_name] = move_id

    ability_candidates = build_ability_candidates_from_resolved_species(run_id, resolved_species_forms)
    rebuilt_ability_names = {row["ability_name"] for row in ability_candidates}
    for row in raw_ability_candidates:
        if row.get("ability_name") in rebuilt_ability_names:
            continue
        fallback_row = dict(row)
        fallback_row.setdefault("supplement_refs", [])
        fallback_row.setdefault("source_layers", ["wiki"])
        ability_candidates.append(fallback_row)

    conflict_names = {
        row["ability_name"]
        for row in ability_candidates
        if row["derivation_status"] == "conflict_review_required"
    }
    grouped_ability_rows: dict[str, list[dict[str, Any]]] = {}
    for row in ability_candidates:
        grouped_ability_rows.setdefault(row["ability_name"], []).append(row)

    for ability_name, rows in sorted(grouped_ability_rows.items()):
        if ability_name in supplement.ability_text_overrides:
            source_species_ids = sorted({sid for row in rows for sid in row["source_species_ids"]})
            source_page_ids = sorted({sid for row in rows for sid in row["source_page_ids"]})
            supplement_refs = sorted(
                {
                    ref
                    for row in rows
                    for ref in row.get("supplement_refs", [])
                }
            )
            resolved = {
                "run_id": run_id,
                "ability_id": stable_id("resolved_ability", ability_name),
                "ability_name": ability_name,
                "effect_text": supplement.ability_text_overrides[ability_name],
                "source_species_ids": source_species_ids,
                "source_page_ids": source_page_ids,
                "derivation_status": "supplement_backed",
                "confidence": "provisional",
                "normalization_warnings": ["wiki_conflict_preserved_in_provenance"],
                **record_base(
                    entity_type="derived_ability",
                    entity_key=stable_id("resolved_ability", ability_name),
                    resolution_status="supplement_backed",
                    canonical_source_layer="manual_supplement",
                    wiki_source_refs=source_page_ids,
                    supplement_refs=[*supplement_refs, f"{supplement.source_ref}::{ability_name}"],
                    resolution_reason="manual supplement selected current accepted ability text over conflicting wiki-derived variants",
                ),
            }
            resolved_abilities.append(resolved)
            supplement_backed_entities.append(resolved)
            continue

        if ability_name in conflict_names:
            unresolved_entities.append(
                {
                    **record_base(
                        entity_type="derived_ability",
                        entity_key=stable_id("unresolved_ability", ability_name),
                        resolution_status="unresolved",
                        canonical_source_layer="wiki",
                        wiki_source_refs=sorted({sid for row in rows for sid in row["source_page_ids"]}),
                        supplement_refs=[],
                        resolution_reason="conflicting wiki-derived ability texts without accepted supplement resolution",
                    ),
                    "ability_name": ability_name,
                }
            )
            continue

        row = dict(rows[0])
        uses_supplement = bool(row.get("supplement_refs")) or "manual_supplement" in row.get("source_layers", [])
        row.update(
            record_base(
                entity_type="derived_ability",
                entity_key=row["ability_id"],
                resolution_status="supplement_backed" if uses_supplement else "included",
                canonical_source_layer="manual_supplement" if uses_supplement else "wiki",
                wiki_source_refs=row["source_page_ids"],
                supplement_refs=row.get("supplement_refs", []) if uses_supplement else [],
                resolution_reason=(
                    "derived ability rebuilt from resolved species forms including species-level supplement corrections"
                    if uses_supplement
                    else "wiki-derived ability candidate rebuilt from resolved species forms without unresolved conflict"
                ),
            )
        )
        resolved_abilities.append(row)
        if uses_supplement:
            supplement_backed_entities.append(dict(row))

    unresolved_move_names = sorted(
        {
            row["move_name_raw"]
            for row in move_pool_candidates
            if row["move_id"] is None
            and move_name_aliases.get(row["move_name_raw"], row["move_name_raw"]) not in move_id_by_name
        }
    )
    for row in move_pool_candidates:
        if row["move_id"] is not None:
            continue
        effective_move_name = move_name_aliases.get(row["move_name_raw"], row["move_name_raw"])
        if effective_move_name in move_id_by_name:
            continue
        unresolved_entities.append(
            {
                **record_base(
                    entity_type="species_move_reference",
                    entity_key=stable_id("unresolved_move_ref", row["species_id"], row["move_name_raw"], row["access_channel"]),
                    resolution_status="unresolved",
                    canonical_source_layer="wiki",
                    wiki_source_refs=[row["source_page_id"]],
                    supplement_refs=[],
                    resolution_reason="species move reference still has no canonical or supplement-backed move record",
                ),
                "species_id": row["species_id"],
                "move_name_raw": row["move_name_raw"],
                "access_channel": row["access_channel"],
            }
        )

    counts = {
        "resolved_species_forms": len(resolved_species_forms),
        "resolved_moves": len(resolved_moves),
        "resolved_derived_abilities": len(resolved_abilities),
        "excluded_entities": len(excluded_entities),
        "review_required_entities": len(review_required_entities),
        "supplement_backed_entities": len(supplement_backed_entities),
        "unresolved_entities": len(unresolved_entities),
    }

    artifact_paths: dict[str, Path] = {}
    artifact_paths["resolved_species_forms"] = writer.write_jsonl("resolved_species_forms.jsonl", resolved_species_forms)
    artifact_paths["resolved_moves"] = writer.write_jsonl("resolved_moves.jsonl", resolved_moves)
    artifact_paths["resolved_derived_abilities"] = writer.write_jsonl("resolved_derived_abilities.jsonl", resolved_abilities)
    artifact_paths["excluded_entities"] = writer.write_jsonl("excluded_entities.jsonl", excluded_entities)
    artifact_paths["review_required_entities"] = writer.write_jsonl("review_required_entities.jsonl", review_required_entities)
    artifact_paths["supplement_backed_entities"] = writer.write_jsonl("supplement_backed_entities.jsonl", supplement_backed_entities)
    artifact_paths["unresolved_entities"] = writer.write_jsonl("unresolved_entities.jsonl", unresolved_entities)
    artifact_paths["importer_diff_summary"] = writer.write_text(
        "importer_diff_summary.md",
        build_summary(
            run_id=run_id,
            canonical_artifact_dir=canonical_dir,
            output_dir=output_dir,
            counts=counts,
            unresolved_move_names=unresolved_move_names,
            review_required_titles=[row["display_name"] for row in review_required_entities],
            excluded_titles=[row["display_name"] for row in excluded_entities],
        ),
    )

    output_files = {name: path.name for name, path in artifact_paths.items()}
    output_files["importer_run_manifest"] = "importer_run_manifest.json"
    importer_manifest = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "run_mode": "dry_run",
        "canonical_artifact_dir": str(canonical_dir),
        "canonical_run_id": manifest["run_id"],
        "supplement_path": str(args.supplement_path.resolve()),
        "supplement_format": args.supplement_path.suffix.lower().lstrip(".") or "unknown",
        "policy_mode": "policy_b",
        "output_files": output_files,
        "counts": counts,
        "resolution_statuses": ["included", "excluded", "review_required", "supplement_backed", "unresolved"],
        "sqlite_mutation": False,
    }
    artifact_paths["importer_run_manifest"] = writer.write_json("importer_run_manifest.json", importer_manifest)
    return artifact_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run battle dex importer dry-run from wiki artifacts and manual supplement.")
    parser.add_argument("--canonical-artifact-dir", type=Path, required=True)
    parser.add_argument("--supplement-path", type=Path, default=DEFAULT_SUPPLEMENT_PATH)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    paths = run_importer_dry_run(args)
    print("Wrote importer dry-run artifacts:")
    for name, path in sorted(paths.items()):
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
