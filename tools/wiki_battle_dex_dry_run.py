#!/usr/bin/env python3
"""P1d bounded wiki crawler/cleaner dry-run.

This tool emits P1c contract artifacts and does not mutate SQLite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Iterable

import mwparserfromhell

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from roco_world_model import RocoWorldTypeChart
from tools.wiki_field_discovery_recon import (
    API_BASE_URL,
    ENTITY_CONFIGS,
    MediaWikiClient,
    PageRevision,
    clean_value,
    page_url,
    select_sample_titles,
    template_name,
)


SCHEMA_VERSION = "battle_dex_schema.v1"
FIELD_ALIGNMENT_MATRIX_VERSION = "field_alignment_matrix.v2"
PARSER_VERSION = "p1c-001"
DEFAULT_USER_AGENT = "RocoP1cCrawlerCleaner/0.1 (bounded dry-run; no database mutation)"
DEFAULT_OUTPUT_ROOT = Path("data/wiki_ingestion_runs")
DETAIL_FETCH_BATCH_SIZES = (40, 10, 1)
SCOPE_BATTLE_DEX = "battle-dex"
SCOPE_MOVE = "move"
SCOPE_SPECIES = "species"

STAT_FIELDS = ("生命", "物攻", "魔攻", "物防", "魔防", "速度")
MOVE_CATEGORY_VALUES = {"状态", "防御", "物攻", "魔攻"}
CONFIDENCE_CONFIRMED = "confirmed"
CONFIDENCE_PROVISIONAL = "provisional"

SPECIES_ALLOWED_SOURCE_FIELDS = {
    "精灵名称",
    "精灵初阶名称",
    "精灵形态",
    "地区形态名称",
    "精灵阶段",
    "主属性",
    "2属性",
    "生命",
    "物攻",
    "魔攻",
    "物防",
    "魔防",
    "速度",
    "特性",
    "特性描述",
    "技能",
    "技能解锁等级",
    "可学技能石",
    "血脉技能",
}
SPECIES_REJECTED_SOURCE_FIELDS = {
    "体型",
    "重量",
    "分布地区",
    "图鉴课题",
    "宠物立绘形态",
    "是否有异色",
    "是否有错别字",
    "更新版本",
    "精灵描述",
    "精灵类型",
    "课题技能石",
    "进化条件",
}
MOVE_ALLOWED_SOURCE_FIELDS = {"技能名称", "属性", "技能类别", "威力", "耗能", "效果", "描述", "技能版本"}
MOVE_FORBIDDEN_IMPORTED_FIELDS = {"accuracy", "Accuracy", "命中", "PP", "pp", "cooldown", "冷却"}

TYPE_ALIASES = {
    "普": "普通",
    "普通": "普通",
    "草": "草",
    "火": "火",
    "水": "水",
    "电": "电",
    "冰": "冰",
    "地": "地",
    "土": "地",
    "虫": "虫",
    "武": "武",
    "翼": "翼",
    "飞": "翼",
    "龙": "龙",
    "毒": "毒",
    "萌": "萌",
    "光": "光",
    "幽": "幽",
    "鬼": "幽",
    "恶": "恶",
    "幻": "幻",
    "械": "机械",
    "机械": "机械",
}


@dataclass(frozen=True)
class ParsedTemplate:
    template_name: str
    raw_fields: dict[str, str]
    field_order: list[str]
    templates_seen: list[str]


class ArtifactWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, filename: str, payload: Any) -> Path:
        path = self.output_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def write_jsonl(self, filename: str, rows: Iterable[dict[str, Any]]) -> Path:
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return path

    def write_text(self, filename: str, text: str) -> Path:
        path = self.output_dir / filename
        path.write_text(text, encoding="utf-8")
        return path


class DryRunBlocked(RuntimeError):
    def __init__(self, message: str, *, code: str, entity_type: str = "unknown") -> None:
        super().__init__(message)
        self.code = code
        self.entity_type = entity_type


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ_p1d_dry_run")


def manifest_scopes(scope: str) -> list[str]:
    if scope == SCOPE_MOVE:
        return ["move"]
    return ["species", "move", "ability_embedded"]


def manifest_limits(args: argparse.Namespace) -> dict[str, int]:
    if args.scope == SCOPE_MOVE:
        return {
            "species_detail_pages": 0,
            "move_detail_pages": args.move_limit,
            "ability_embedded_species_pages": 0,
        }
    if args.scope == SCOPE_SPECIES:
        return {
            "species_detail_pages": args.species_limit,
            "move_detail_pages": 0,
            "ability_embedded_species_pages": args.species_limit,
        }
    return {
        "species_detail_pages": args.species_limit,
        "move_detail_pages": args.move_limit,
        "ability_embedded_species_pages": args.species_limit,
    }


def stable_hash(value: str, length: int = 16) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def stable_id(prefix: str, *parts: Any) -> str:
    normalized = "|".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{stable_hash(normalized)}"


def empty_contract_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "source_pages": [],
        "raw_template_snapshots": [],
        "species_form_candidates": [],
        "move_candidates": [],
        "derived_ability_candidates": [],
        "species_move_pool_candidates": [],
        "validation_events": [],
        "rejected_fields": [],
    }


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def strip_markup(value: str) -> str:
    if not value:
        return ""
    try:
        stripped = mwparserfromhell.parse(value).strip_code(normalize=True, collapse=True)
    except Exception:
        stripped = value
    stripped = unicodedata.normalize("NFKC", stripped)
    return clean_value(stripped)


def normalize_type(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = strip_markup(value)
    normalized = normalized.replace("系", "").strip()
    if normalized in {"", "-", "无", "None", "null"}:
        return None
    return TYPE_ALIASES.get(normalized, normalized)


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = strip_markup(value)
    if normalized in {"", "-", "无"}:
        return []
    parts = re.split(r"[,，、]\s*", normalized)
    return [part.strip() for part in parts if part.strip()]


def canonical_move_lookup_name(move_reference: str) -> str:
    """Map source move references to canonical move names for matching only."""
    normalized = strip_markup(move_reference).replace("／", "/").strip()
    for prefix in ("技能石/", "技能石:"):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return normalized


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = strip_markup(value)
    if normalized in {"", "-", "无"}:
        return None
    match = re.search(r"-?\d+", normalized)
    if not match:
        raise ValueError(f"Cannot parse integer from {value!r}")
    return int(match.group(0))


def parse_template(content: str, target_template: str) -> ParsedTemplate | None:
    wikicode = mwparserfromhell.parse(content)
    templates_seen: list[str] = []
    for template in wikicode.filter_templates(recursive=True):
        name = template_name(template)
        templates_seen.append(name)
        if name != target_template:
            continue
        raw_fields: dict[str, str] = {}
        field_order: list[str] = []
        for param in template.params:
            if not param.showkey:
                continue
            label = clean_value(str(param.name))
            value = clean_value(str(param.value))
            raw_fields[label] = value
            field_order.append(label)
        return ParsedTemplate(
            template_name=target_template,
            raw_fields=raw_fields,
            field_order=field_order,
            templates_seen=sorted(set(templates_seen)),
        )
    return None


def source_page_record(run_id: str, entity_hint: str, page: PageRevision, parser_version: str, fetch_status: str = "ok") -> dict[str, Any]:
    return {
        "run_id": run_id,
        "source_page_id": stable_id("source", entity_hint, page.title),
        "entity_hint": entity_hint,
        "page_title": page.title,
        "page_url": page.fullurl or page_url(page.title),
        "revision_id": str(page.revid) if page.revid is not None else None,
        "revision_timestamp": page.timestamp,
        "fetched_at": utc_now(),
        "content_sha256": content_hash(page.content),
        "content_length": len(page.content),
        "parser_version": parser_version,
        "fetch_status": fetch_status,
    }


def snapshot_record(run_id: str, source_page_id: str, parsed: ParsedTemplate | None) -> dict[str, Any]:
    template = parsed.template_name if parsed else "unknown"
    return {
        "run_id": run_id,
        "snapshot_id": stable_id("snapshot", source_page_id, template),
        "source_page_id": source_page_id,
        "template_name": template,
        "raw_fields": parsed.raw_fields if parsed else {},
        "field_order": parsed.field_order if parsed else [],
        "extraction_warnings": [] if parsed else ["missing_required_template"],
    }


def validation_event(
    *,
    run_id: str,
    severity: str,
    code: str,
    entity_type: str,
    record_id: str | None,
    source_page_id: str | None,
    field_name: str | None,
    message: str,
    action_taken: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "severity": severity,
        "code": code,
        "entity_type": entity_type,
        "record_id": record_id,
        "source_page_id": source_page_id,
        "field_name": field_name,
        "message": message,
        "action_taken": action_taken,
    }


def rejected_field(
    *,
    run_id: str,
    source_page_id: str,
    entity_type: str,
    source_label: str,
    normalized_candidate: str | None,
    reason: str,
    policy_basis: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "source_page_id": source_page_id,
        "entity_type": entity_type,
        "source_label": source_label,
        "normalized_candidate": normalized_candidate,
        "reason": reason,
        "policy_basis": policy_basis,
    }


def validate_roco_type(chart: RocoWorldTypeChart, value: str | None) -> bool:
    return value is None or value in chart.type_set


def normalize_species(
    *,
    run_id: str,
    source_page_id: str,
    snapshot_id: str,
    raw_fields: dict[str, str],
    chart: RocoWorldTypeChart,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []

    for label in raw_fields:
        if label in SPECIES_REJECTED_SOURCE_FIELDS:
            rejects.append(
                rejected_field(
                    run_id=run_id,
                    source_page_id=source_page_id,
                    entity_type="species",
                    source_label=label,
                    normalized_candidate=None,
                    reason="excluded encyclopedia/cosmetic species field",
                    policy_basis="specs/field_alignment_matrix.yaml",
                )
            )
        elif label not in SPECIES_ALLOWED_SOURCE_FIELDS:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="warning",
                    code="unexpected_source_field",
                    entity_type="species",
                    record_id=None,
                    source_page_id=source_page_id,
                    field_name=label,
                    message=f"Unexpected species source field: {label}",
                    action_taken="preserved_in_raw_snapshot_only",
                )
            )

    display_name = strip_markup(raw_fields.get("精灵名称", ""))
    primary_type = normalize_type(raw_fields.get("主属性"))
    secondary_type = normalize_type(raw_fields.get("2属性"))
    record_id = stable_id(
        "species",
        display_name,
        strip_markup(raw_fields.get("精灵形态", "")),
        strip_markup(raw_fields.get("地区形态名称", "")),
    )

    required = {"精灵名称": display_name, "主属性": primary_type}
    missing = [field for field, value in required.items() if value in {None, ""}]
    if missing:
        for field in missing:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="missing_required_field",
                    entity_type="species",
                    record_id=record_id,
                    source_page_id=source_page_id,
                    field_name=field,
                    message=f"Missing required species field: {field}",
                    action_taken="candidate_not_emitted",
                )
            )
        return None, events, rejects

    for field_name, type_value in (("主属性", primary_type), ("2属性", secondary_type)):
        if not validate_roco_type(chart, type_value):
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="invalid_type",
                    entity_type="species",
                    record_id=record_id,
                    source_page_id=source_page_id,
                    field_name=field_name,
                    message=f"Invalid Roco type: {type_value}",
                    action_taken="candidate_not_emitted",
                )
            )
            return None, events, rejects

    base_stats: dict[str, int] = {}
    for stat in STAT_FIELDS:
        try:
            parsed = parse_int(raw_fields.get(stat))
        except ValueError as exc:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="invalid_numeric_value",
                    entity_type="species",
                    record_id=record_id,
                    source_page_id=source_page_id,
                    field_name=stat,
                    message=str(exc),
                    action_taken="candidate_not_emitted",
                )
            )
            return None, events, rejects
        if parsed is None:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="missing_required_field",
                    entity_type="species",
                    record_id=record_id,
                    source_page_id=source_page_id,
                    field_name=stat,
                    message=f"Missing required base stat: {stat}",
                    action_taken="candidate_not_emitted",
                )
            )
            return None, events, rejects
        base_stats[stat] = parsed

    warnings: list[str] = []
    if not strip_markup(raw_fields.get("特性", "")):
        warnings.append("missing_ability_name")
        events.append(
            validation_event(
                run_id=run_id,
                severity="warning",
                code="missing_optional_field",
                entity_type="species",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="特性",
                message="Species has no ability name.",
                action_taken="candidate_emitted_with_null",
            )
        )
    if not strip_markup(raw_fields.get("特性描述", "")):
        warnings.append("missing_ability_text")
        events.append(
            validation_event(
                run_id=run_id,
                severity="warning",
                code="missing_ability_text",
                entity_type="species",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="特性描述",
                message="Species has no ability effect text.",
                action_taken="candidate_emitted_with_null",
            )
        )

    return (
        {
            "run_id": run_id,
            "species_id": record_id,
            "display_name": display_name,
            "initial_species_name": strip_markup(raw_fields.get("精灵初阶名称", "")) or None,
            "form_name": strip_markup(raw_fields.get("精灵形态", "")) or None,
            "regional_form_name": strip_markup(raw_fields.get("地区形态名称", "")) or None,
            "evolution_stage": strip_markup(raw_fields.get("精灵阶段", "")) or None,
            "primary_type": primary_type,
            "secondary_type": secondary_type,
            "base_stats": base_stats,
            "ability_name": strip_markup(raw_fields.get("特性", "")) or None,
            "ability_effect_text": strip_markup(raw_fields.get("特性描述", "")) or None,
            "source_page_id": source_page_id,
            "raw_snapshot_id": snapshot_id,
            "confidence": CONFIDENCE_CONFIRMED,
            "normalization_warnings": warnings,
        },
        events,
        rejects,
    )


def normalize_move(
    *,
    run_id: str,
    source_page_id: str,
    snapshot_id: str,
    raw_fields: dict[str, str],
    chart: RocoWorldTypeChart,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []

    for label in raw_fields:
        if label in MOVE_FORBIDDEN_IMPORTED_FIELDS:
            rejects.append(
                rejected_field(
                    run_id=run_id,
                    source_page_id=source_page_id,
                    entity_type="move",
                    source_label=label,
                    normalized_candidate=label,
                    reason="forbidden imported move field",
                    policy_basis="specs/field_alignment_matrix.yaml",
                )
            )
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="forbidden_imported_field",
                    entity_type="move",
                    record_id=None,
                    source_page_id=source_page_id,
                    field_name=label,
                    message=f"Forbidden imported move field observed: {label}",
                    action_taken="field_rejected",
                )
            )
        elif label not in MOVE_ALLOWED_SOURCE_FIELDS:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="warning",
                    code="unexpected_source_field",
                    entity_type="move",
                    record_id=None,
                    source_page_id=source_page_id,
                    field_name=label,
                    message=f"Unexpected move source field: {label}",
                    action_taken="preserved_in_raw_snapshot_only",
                )
            )

    move_name = strip_markup(raw_fields.get("技能名称", ""))
    move_type = normalize_type(raw_fields.get("属性"))
    category_raw = strip_markup(raw_fields.get("技能类别", ""))
    record_id = stable_id("move", move_name)

    required = {"技能名称": move_name, "属性": move_type, "技能类别": category_raw, "效果": strip_markup(raw_fields.get("效果", ""))}
    missing = [field for field, value in required.items() if value in {None, ""}]
    if missing:
        for field in missing:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="missing_required_field",
                    entity_type="move",
                    record_id=record_id,
                    source_page_id=source_page_id,
                    field_name=field,
                    message=f"Missing required move field: {field}",
                    action_taken="candidate_not_emitted",
                )
            )
        return None, events, rejects

    if not validate_roco_type(chart, move_type):
        events.append(
            validation_event(
                run_id=run_id,
                severity="hard_reject",
                code="invalid_type",
                entity_type="move",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="属性",
                message=f"Invalid Roco type: {move_type}",
                action_taken="candidate_not_emitted",
            )
        )
        return None, events, rejects

    if category_raw not in MOVE_CATEGORY_VALUES:
        events.append(
            validation_event(
                run_id=run_id,
                severity="hard_reject",
                code="missing_required_field",
                entity_type="move",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="技能类别",
                message=f"Unexpected move category: {category_raw}",
                action_taken="candidate_not_emitted",
            )
        )
        return None, events, rejects

    warnings: list[str] = []
    try:
        power = parse_int(raw_fields.get("威力"))
        energy_cost = parse_int(raw_fields.get("耗能"))
    except ValueError as exc:
        events.append(
            validation_event(
                run_id=run_id,
                severity="hard_reject",
                code="invalid_numeric_value",
                entity_type="move",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="威力/耗能",
                message=str(exc),
                action_taken="candidate_not_emitted",
            )
        )
        return None, events, rejects

    description_text = strip_markup(raw_fields.get("描述", ""))
    if "描述" in raw_fields and not description_text:
        warnings.append("empty_description_text")
        events.append(
            validation_event(
                run_id=run_id,
                severity="warning",
                code="empty_description_text",
                entity_type="move",
                record_id=record_id,
                source_page_id=source_page_id,
                field_name="描述",
                message="Move description field is present but empty.",
                action_taken="candidate_emitted_with_null",
            )
        )

    return (
        {
            "run_id": run_id,
            "move_id": record_id,
            "move_name": move_name,
            "move_type": move_type,
            "category_raw": category_raw,
            "power": power,
            "energy_cost": energy_cost,
            "effect_text": strip_markup(raw_fields.get("效果", "")),
            "description_text": description_text or None,
            "source_version": strip_markup(raw_fields.get("技能版本", "")) or None,
            "source_page_id": source_page_id,
            "raw_snapshot_id": snapshot_id,
            "confidence": CONFIDENCE_CONFIRMED,
            "normalization_warnings": warnings,
        },
        events,
        rejects,
    )


def build_move_pool_rows(
    *,
    run_id: str,
    species: dict[str, Any],
    raw_fields: dict[str, str],
    source_page_id: str,
    snapshot_id: str,
    move_name_to_id: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    level_moves = split_list(raw_fields.get("技能"))
    levels = split_list(raw_fields.get("技能解锁等级"))
    species_id = species["species_id"]

    if level_moves and levels and len(level_moves) != len(levels):
        events.append(
            validation_event(
                run_id=run_id,
                severity="warning",
                code="parallel_list_length_mismatch",
                entity_type="species_move_pool",
                record_id=species_id,
                source_page_id=source_page_id,
                field_name="技能/技能解锁等级",
                message=f"Level-up moves count {len(level_moves)} does not match unlock levels count {len(levels)}.",
                action_taken="kept_unmatched_move_names",
            )
        )

    def add_row(move_name: str, channel: str, source_field: str, unlock_level: int | None = None) -> None:
        lookup_name = canonical_move_lookup_name(move_name)
        move_id = move_name_to_id.get(lookup_name)
        warnings: list[str] = []
        if lookup_name != move_name:
            warnings.append("move_reference_canonicalized_for_lookup")
        if move_id is None:
            warnings.append("move_name_unresolved")
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="warning",
                    code="move_name_unresolved",
                    entity_type="species_move_pool",
                    record_id=species_id,
                    source_page_id=source_page_id,
                    field_name=source_field,
                    message=f"Move name could not be matched to a move page: {lookup_name}",
                    action_taken="candidate_emitted_with_null_move_id",
                )
            )
        rows.append(
            {
                "run_id": run_id,
                "species_id": species_id,
                "move_name_raw": move_name,
                "move_id": move_id,
                "access_channel": channel,
                "unlock_level": unlock_level,
                "source_field": source_field,
                "source_page_id": source_page_id,
                "raw_snapshot_id": snapshot_id,
                "confidence": CONFIDENCE_CONFIRMED,
                "normalization_warnings": warnings,
            }
        )

    for index, move_name in enumerate(level_moves):
        unlock_level = None
        if index < len(levels):
            try:
                unlock_level = parse_int(levels[index])
            except ValueError:
                events.append(
                    validation_event(
                        run_id=run_id,
                        severity="warning",
                        code="invalid_numeric_value",
                        entity_type="species_move_pool",
                        record_id=species_id,
                        source_page_id=source_page_id,
                        field_name="技能解锁等级",
                        message=f"Could not parse unlock level {levels[index]!r}.",
                        action_taken="candidate_emitted_with_null_unlock_level",
                    )
                )
        add_row(move_name, "level_up", "技能", unlock_level)

    for move_name in split_list(raw_fields.get("可学技能石")):
        add_row(move_name, "skill_stone", "可学技能石")

    for move_name in split_list(raw_fields.get("血脉技能")):
        add_row(move_name, "bloodline", "血脉技能")

    return rows, events


def build_ability_candidates(
    run_id: str,
    species_candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for species in species_candidates:
        name = species.get("ability_name")
        text = species.get("ability_effect_text")
        if not name or not text:
            continue
        grouped[name][text].append(species)

    candidates: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for name, text_map in sorted(grouped.items()):
        conflict = len(text_map) > 1
        for text, sources in sorted(text_map.items(), key=lambda item: item[0]):
            source_species_ids = [source["species_id"] for source in sources]
            source_page_ids = [source["source_page_id"] for source in sources]
            ability_id = stable_id("ability", name, text if conflict else "")
            status = "conflict_review_required" if conflict else ("merged_consistent" if len(sources) > 1 else "single_source")
            candidates.append(
                {
                    "run_id": run_id,
                    "ability_id": ability_id,
                    "ability_name": name,
                    "effect_text": text,
                    "source_species_ids": source_species_ids,
                    "source_page_ids": source_page_ids,
                    "derivation_status": status,
                    "confidence": CONFIDENCE_CONFIRMED if not conflict else CONFIDENCE_PROVISIONAL,
                    "normalization_warnings": ["ability_description_conflict"] if conflict else [],
                }
            )
        if conflict:
            events.append(
                validation_event(
                    run_id=run_id,
                    severity="warning",
                    code="ability_description_conflict",
                    entity_type="derived_ability",
                    record_id=stable_id("ability", name),
                    source_page_id=None,
                    field_name="特性描述",
                    message=f"Ability name has {len(text_map)} conflicting descriptions: {name}",
                    action_taken="emitted_conflict_review_required_candidates",
                )
            )
    return candidates, events


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def clone_cached_source_pages(source_pages: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    cloned: list[dict[str, Any]] = []
    for source in source_pages:
        row = dict(source)
        row["run_id"] = run_id
        row["fetched_at"] = utc_now()
        row["parser_version"] = PARSER_VERSION
        row["fetch_status"] = "cached"
        cloned.append(row)
    return cloned


def clone_snapshots(snapshots: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    cloned: list[dict[str, Any]] = []
    for snapshot in snapshots:
        row = dict(snapshot)
        row["run_id"] = run_id
        cloned.append(row)
    return cloned


def load_cached_move_artifacts(input_dir: Path, run_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_pages_path = input_dir / "source_pages.jsonl"
    snapshots_path = input_dir / "raw_template_snapshots.jsonl"
    if not source_pages_path.exists() or not snapshots_path.exists():
        raise DryRunBlocked(
            "--cached-move-input-dir must contain source_pages.jsonl and raw_template_snapshots.jsonl.",
            code="detail_fetch_failed",
            entity_type="move",
        )

    cached_sources = [
        row for row in load_jsonl(source_pages_path) if row.get("entity_hint") == "move"
    ]
    cached_source_ids = {row["source_page_id"] for row in cached_sources}
    cached_snapshots = [
        row
        for row in load_jsonl(snapshots_path)
        if row.get("source_page_id") in cached_source_ids
        and row.get("template_name") == ENTITY_CONFIGS["move"]["detail_template"]
    ]
    if not cached_sources or not cached_snapshots:
        raise DryRunBlocked(
            "No cached move source pages with 技能信息 snapshots were found in --cached-move-input-dir.",
            code="detail_fetch_failed",
            entity_type="move",
        )
    return clone_cached_source_pages(cached_sources, run_id), clone_snapshots(cached_snapshots, run_id)


def append_pages(
    *,
    run_id: str,
    entity_hint: str,
    pages: list[PageRevision],
    template: str,
    source_pages: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> None:
    for page in pages:
        source = source_page_record(run_id, entity_hint, page, PARSER_VERSION)
        source_pages.append(source)
        parsed = parse_template(page.content, template)
        snapshots.append(snapshot_record(run_id, source["source_page_id"], parsed))


def build_candidates_from_snapshots(
    *,
    run_id: str,
    source_pages: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    chart: RocoWorldTypeChart,
) -> dict[str, Any]:
    species_candidates: list[dict[str, Any]] = []
    move_candidates: list[dict[str, Any]] = []
    species_raw_context: dict[str, tuple[dict[str, str], str, str]] = {}
    validation_events: list[dict[str, Any]] = []
    rejected_fields: list[dict[str, Any]] = []
    source_entity = {source["source_page_id"]: source.get("entity_hint", "unknown") for source in source_pages}

    for snapshot in snapshots:
        source_page_id = snapshot["source_page_id"]
        snapshot_id = snapshot["snapshot_id"]
        raw_fields = snapshot.get("raw_fields", {})
        entity_hint = source_entity.get(source_page_id, "unknown")
        template = snapshot.get("template_name")

        if template == ENTITY_CONFIGS["species"]["detail_template"]:
            candidate, events, rejects = normalize_species(
                run_id=run_id,
                source_page_id=source_page_id,
                snapshot_id=snapshot_id,
                raw_fields=raw_fields,
                chart=chart,
            )
            validation_events.extend(events)
            rejected_fields.extend(rejects)
            if candidate:
                species_candidates.append(candidate)
                species_raw_context[candidate["species_id"]] = (raw_fields, source_page_id, snapshot_id)
        elif template == ENTITY_CONFIGS["move"]["detail_template"]:
            candidate, events, rejects = normalize_move(
                run_id=run_id,
                source_page_id=source_page_id,
                snapshot_id=snapshot_id,
                raw_fields=raw_fields,
                chart=chart,
            )
            validation_events.extend(events)
            rejected_fields.extend(rejects)
            if candidate:
                move_candidates.append(candidate)
        else:
            validation_events.append(
                validation_event(
                    run_id=run_id,
                    severity="hard_reject",
                    code="missing_required_template",
                    entity_type=entity_hint,
                    record_id=None,
                    source_page_id=source_page_id,
                    field_name=None,
                    message=f"Required template not found for source page: {source_page_id}",
                    action_taken="candidate_not_emitted",
                )
            )

    move_name_to_id = {move["move_name"]: move["move_id"] for move in move_candidates}
    species_move_pool: list[dict[str, Any]] = []
    for species in species_candidates:
        raw_fields, source_page_id, snapshot_id = species_raw_context[species["species_id"]]
        rows, events = build_move_pool_rows(
            run_id=run_id,
            species=species,
            raw_fields=raw_fields,
            source_page_id=source_page_id,
            snapshot_id=snapshot_id,
            move_name_to_id=move_name_to_id,
        )
        species_move_pool.extend(rows)
        validation_events.extend(events)

    ability_candidates, ability_events = build_ability_candidates(run_id, species_candidates)
    validation_events.extend(ability_events)

    unresolved_move_names = sorted(
        {row["move_name_raw"] for row in species_move_pool if row["move_id"] is None}
    )
    ability_conflicts = sorted(
        {
            ability["ability_name"]
            for ability in ability_candidates
            if ability["derivation_status"] == "conflict_review_required"
        }
    )

    return {
        "species_candidates": species_candidates,
        "move_candidates": move_candidates,
        "ability_candidates": ability_candidates,
        "species_move_pool": species_move_pool,
        "validation_events": validation_events,
        "rejected_fields": rejected_fields,
        "unresolved_move_names": unresolved_move_names,
        "ability_conflicts": ability_conflicts,
    }


def write_completed_artifacts(
    *,
    args: argparse.Namespace,
    run_id: str,
    output_dir: Path,
    writer: ArtifactWriter,
    started_at: str,
    source_pages: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    normalized: dict[str, Any],
    fetch_strategy: str,
) -> dict[str, Path]:
    species_candidates = normalized["species_candidates"]
    move_candidates = normalized["move_candidates"]
    ability_candidates = normalized["ability_candidates"]
    species_move_pool = normalized["species_move_pool"]
    validation_events = normalized["validation_events"]
    rejected_fields = normalized["rejected_fields"]
    unresolved_move_names = normalized["unresolved_move_names"]
    ability_conflicts = normalized["ability_conflicts"]

    counts = {
        "source_pages": len(source_pages),
        "raw_template_snapshots": len(snapshots),
        "species_form_candidates": len(species_candidates),
        "move_candidates": len(move_candidates),
        "derived_ability_candidates": len(ability_candidates),
        "species_move_pool_candidates": len(species_move_pool),
        "validation_events": len(validation_events),
        "rejected_fields": len(rejected_fields),
        "unresolved_move_names": len(unresolved_move_names),
        "ability_conflicts": len(ability_conflicts),
    }
    hard_reject_count = sum(1 for event in validation_events if event["severity"] == "hard_reject")
    warning_count = sum(1 for event in validation_events if event["severity"] == "warning")
    status = "completed_with_warnings" if warning_count or hard_reject_count else "completed"

    artifact_paths: dict[str, Path] = {}
    artifact_paths["source_pages"] = writer.write_jsonl("source_pages.jsonl", source_pages)
    artifact_paths["raw_template_snapshots"] = writer.write_jsonl("raw_template_snapshots.jsonl", snapshots)
    artifact_paths["species_form_candidates"] = writer.write_jsonl("species_form_candidates.jsonl", species_candidates)
    artifact_paths["move_candidates"] = writer.write_jsonl("move_candidates.jsonl", move_candidates)
    artifact_paths["derived_ability_candidates"] = writer.write_jsonl("derived_ability_candidates.jsonl", ability_candidates)
    artifact_paths["species_move_pool_candidates"] = writer.write_jsonl("species_move_pool_candidates.jsonl", species_move_pool)
    artifact_paths["validation_events"] = writer.write_jsonl("validation_events.jsonl", validation_events)
    artifact_paths["rejected_fields"] = writer.write_jsonl("rejected_fields.jsonl", rejected_fields)

    dry_run_diff = {
        "run_id": run_id,
        "baseline_database": None,
        "added": {
            "species_form": len(species_candidates),
            "move": len(move_candidates),
            "derived_ability": len(ability_candidates),
            "species_move_pool": len(species_move_pool),
        },
        "updated": {},
        "removed": {},
        "unchanged": {},
        "conflicts": {
            "ability_conflicts": ability_conflicts,
            "unresolved_move_names": unresolved_move_names,
        },
        "requires_pm_review": bool(ability_conflicts or hard_reject_count),
    }
    artifact_paths["dry_run_diff"] = writer.write_json("dry_run_diff.json", dry_run_diff)
    artifact_paths["summary"] = writer.write_text(
        "summary.md",
        build_summary(
            run_id=run_id,
            counts=counts,
            validation_events=validation_events,
            unresolved_move_names=unresolved_move_names,
            ability_conflicts=ability_conflicts,
            output_dir=output_dir,
            status=status,
        ),
    )

    artifact_file_names = {name: path.name for name, path in artifact_paths.items()}
    artifact_file_names["run_manifest"] = "run_manifest.json"
    manifest = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "run_mode": "dry_run",
        "api_base_url": args.api_base_url,
        "parser_version": PARSER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "field_alignment_matrix_version": FIELD_ALIGNMENT_MATRIX_VERSION,
        "scopes": manifest_scopes(args.scope),
        "limits": manifest_limits(args),
        "artifact_files": artifact_file_names,
        "counts": counts,
        "validation_summary": {
            "hard_reject": hard_reject_count,
            "warning": warning_count,
            "info": sum(1 for event in validation_events if event["severity"] == "info"),
        },
        "hard_reject_count": hard_reject_count,
        "warning_count": warning_count,
        "status": status,
        "failure_reason": None,
        "fetch_strategy": fetch_strategy,
    }
    artifact_paths["run_manifest"] = writer.write_json("run_manifest.json", manifest)
    return artifact_paths


def preflight_api(client: MediaWikiClient) -> None:
    try:
        client.get({"action": "query", "meta": "siteinfo", "siprop": "general", "format": "json"})
    except RuntimeError as exc:
        raise DryRunBlocked(
            f"API preflight failed: {exc}",
            code="api_preflight_failed",
            entity_type="unknown",
        ) from exc


def fetch_pages_degraded(client: MediaWikiClient, titles: list[str], entity_type: str) -> tuple[list[PageRevision], list[dict[str, Any]]]:
    pages: list[PageRevision] = []
    events: list[dict[str, Any]] = []
    remaining = list(dict.fromkeys(titles))
    for batch_size in DETAIL_FETCH_BATCH_SIZES:
        if not remaining:
            break
        next_remaining: list[str] = []
        for start in range(0, len(remaining), batch_size):
            batch = remaining[start : start + batch_size]
            try:
                fetched = client.get_pages(batch)
                pages.extend(page for page in fetched if not page.missing)
            except RuntimeError as exc:
                if batch_size == 1:
                    title = batch[0]
                    events.append(
                        validation_event(
                            run_id="pending",
                            severity="warning",
                            code="fetch_title_skipped",
                            entity_type=entity_type,
                            record_id=None,
                            source_page_id=None,
                            field_name=None,
                            message=f"Skipped title after single-title fetch failure: {title}; {exc}",
                            action_taken="title_skipped",
                        )
                    )
                else:
                    next_remaining.extend(batch)
        remaining = next_remaining
    return pages, events


def limited_category_titles(client: MediaWikiClient, entity_type: str, limit: int) -> tuple[list[str], list[dict[str, Any]], str]:
    config = ENTITY_CONFIGS[entity_type]
    seed_titles = list(dict.fromkeys(config["preferred_titles"]))[:limit]
    try:
        members = client.get_category_members(config["category"], limit=max(limit, len(seed_titles)))
        selected_titles = select_sample_titles(
            members=members,
            preferred_titles=config["preferred_titles"],
            variation_keywords=config["variation_keywords"],
            detail_limit=limit,
        )[:limit]
        return selected_titles, [], "limited_categorymembers"
    except RuntimeError:
        # Biligame occasionally returns non-standard 5xx responses for category
        # enumeration. Seed titles are the bounded fallback.
        return seed_titles, [], "seed_titles"


def fetch_detail_pages(client: MediaWikiClient, entity_type: str, limit: int) -> tuple[list[PageRevision], list[dict[str, Any]], str]:
    selected_titles, events, strategy = limited_category_titles(client, entity_type, limit)
    pages, fetch_events = fetch_pages_degraded(client, selected_titles, entity_type)
    events.extend(fetch_events)
    if not pages:
        raise DryRunBlocked(
            f"No {entity_type} detail pages could be fetched after degraded fetch attempts.",
            code="detail_fetch_failed",
            entity_type=entity_type,
        )
    return pages[:limit], events, strategy


def build_summary(
    *,
    run_id: str,
    counts: dict[str, int],
    validation_events: list[dict[str, Any]],
    unresolved_move_names: list[str],
    ability_conflicts: list[str],
    output_dir: Path,
    status: str = "completed_with_warnings",
    failure_reason: str | None = None,
) -> str:
    by_severity = defaultdict(int)
    by_code = defaultdict(int)
    for event in validation_events:
        by_severity[event["severity"]] += 1
        by_code[event["code"]] += 1

    lines = [
        "# P1d Wiki Battle Dex Dry-Run Summary",
        "",
        f"- Run ID: `{run_id}`",
        f"- Output directory: `{output_dir}`",
        f"- Status: `{status}`",
        "- Database mutation: not performed",
        "",
        "## Artifact Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")

    lines.extend(["", "## Validation Summary", ""])
    if not validation_events:
        lines.append("- No validation events.")
    else:
        for severity in ["hard_reject", "warning", "info"]:
            lines.append(f"- `{severity}`: {by_severity.get(severity, 0)}")
        lines.append("")
        lines.append("### By Code")
        lines.append("")
        for code, count in sorted(by_code.items()):
            lines.append(f"- `{code}`: {count}")

    lines.extend(["", "## Unresolved Move Names", ""])
    if unresolved_move_names:
        for name in unresolved_move_names[:50]:
            lines.append(f"- {name}")
    else:
        lines.append("- None")

    lines.extend(["", "## Ability Conflicts", ""])
    if ability_conflicts:
        for name in ability_conflicts:
            lines.append(f"- {name}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Failure Reason",
            "",
            f"- {failure_reason or 'None'}",
            "",
            "## Recommended Next Action",
            "",
            "- Parse-validate all artifacts.",
            "- Review unresolved move names before any SQLite ingestion.",
            "- Keep this run bounded until P1d acceptance criteria are met.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_failed_artifacts(
    *,
    args: argparse.Namespace,
    run_id: str,
    output_dir: Path,
    writer: ArtifactWriter,
    started_at: str,
    failure: DryRunBlocked,
) -> dict[str, Path]:
    event = validation_event(
        run_id=run_id,
        severity="hard_reject",
        code=failure.code,
        entity_type=failure.entity_type,
        record_id=None,
        source_page_id=None,
        field_name=None,
        message=str(failure),
        action_taken="failed_manifest_emitted",
    )
    rows = empty_contract_rows()
    rows["validation_events"] = [event]
    artifact_paths: dict[str, Path] = {
        "source_pages": writer.write_jsonl("source_pages.jsonl", rows["source_pages"]),
        "raw_template_snapshots": writer.write_jsonl("raw_template_snapshots.jsonl", rows["raw_template_snapshots"]),
        "species_form_candidates": writer.write_jsonl("species_form_candidates.jsonl", rows["species_form_candidates"]),
        "move_candidates": writer.write_jsonl("move_candidates.jsonl", rows["move_candidates"]),
        "derived_ability_candidates": writer.write_jsonl("derived_ability_candidates.jsonl", rows["derived_ability_candidates"]),
        "species_move_pool_candidates": writer.write_jsonl("species_move_pool_candidates.jsonl", rows["species_move_pool_candidates"]),
        "validation_events": writer.write_jsonl("validation_events.jsonl", rows["validation_events"]),
        "rejected_fields": writer.write_jsonl("rejected_fields.jsonl", rows["rejected_fields"]),
    }
    dry_run_diff = {
        "run_id": run_id,
        "baseline_database": None,
        "added": {},
        "updated": {},
        "removed": {},
        "unchanged": {},
        "conflicts": {"failure": str(failure)},
        "requires_pm_review": True,
    }
    artifact_paths["dry_run_diff"] = writer.write_json("dry_run_diff.json", dry_run_diff)
    summary = build_summary(
        run_id=run_id,
        counts={key: len(value) for key, value in rows.items()},
        validation_events=rows["validation_events"],
        unresolved_move_names=[],
        ability_conflicts=[],
        output_dir=output_dir,
        status="failed",
        failure_reason=str(failure),
    )
    artifact_paths["summary"] = writer.write_text("summary.md", summary)
    artifact_file_names = {name: path.name for name, path in artifact_paths.items()}
    artifact_file_names["run_manifest"] = "run_manifest.json"
    manifest = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "run_mode": "dry_run",
        "api_base_url": args.api_base_url,
        "parser_version": PARSER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "field_alignment_matrix_version": FIELD_ALIGNMENT_MATRIX_VERSION,
        "scopes": manifest_scopes(args.scope),
        "limits": manifest_limits(args),
        "artifact_files": artifact_file_names,
        "counts": {key: len(value) for key, value in rows.items()},
        "validation_summary": {"hard_reject": 1, "warning": 0, "info": 0},
        "hard_reject_count": 1,
        "warning_count": 0,
        "status": "failed",
        "failure_reason": str(failure),
        "fetch_strategy": "api_preflight" if failure.code == "api_preflight_failed" else "seed_titles",
    }
    artifact_paths["run_manifest"] = writer.write_json("run_manifest.json", manifest)
    return artifact_paths


def run_dry_run(args: argparse.Namespace) -> dict[str, Path]:
    run_id = args.run_id or make_run_id()
    output_dir = (args.output_dir or (DEFAULT_OUTPUT_ROOT / run_id)).resolve()
    writer = ArtifactWriter(output_dir)
    started_at = utc_now()

    client = MediaWikiClient(
        api_base_url=args.api_base_url,
        user_agent=args.user_agent,
        sleep_seconds=args.sleep_seconds,
        timeout_seconds=args.timeout_seconds,
    )
    chart = RocoWorldTypeChart()

    source_pages: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    validation_events: list[dict[str, Any]] = []

    try:
        preflight_api(client)
        if args.scope == SCOPE_MOVE:
            species_pages = []
            species_fetch_events = []
            species_strategy = "not_requested"
            cached_move_sources = []
            cached_move_snapshots = []
            move_pages, move_fetch_events, move_strategy = fetch_detail_pages(client, "move", args.move_limit)
        elif args.scope == SCOPE_SPECIES:
            species_pages, species_fetch_events, species_strategy = fetch_detail_pages(client, "species", args.species_limit)
            cached_move_sources, cached_move_snapshots = load_cached_move_artifacts(args.cached_move_input_dir.resolve(), run_id)
            move_pages = []
            move_fetch_events = []
            move_strategy = "cached_source_pages"
        else:
            species_pages, species_fetch_events, species_strategy = fetch_detail_pages(client, "species", args.species_limit)
            cached_move_sources = []
            cached_move_snapshots = []
            move_pages, move_fetch_events, move_strategy = fetch_detail_pages(client, "move", args.move_limit)
    except DryRunBlocked as failure:
        return write_failed_artifacts(
            args=args,
            run_id=run_id,
            output_dir=output_dir,
            writer=writer,
            started_at=started_at,
            failure=failure,
        )

    if args.scope == SCOPE_MOVE:
        requested_strategies = [move_strategy]
    elif args.scope == SCOPE_SPECIES:
        requested_strategies = [species_strategy, move_strategy]
    else:
        requested_strategies = [species_strategy, move_strategy]
    fetch_strategy = ",".join(sorted(set(requested_strategies)))
    for event in (*species_fetch_events, *move_fetch_events):
        event["run_id"] = run_id
        validation_events.append(event)

    if cached_move_sources:
        source_pages.extend(cached_move_sources)
        snapshots.extend(cached_move_snapshots)
    append_pages(
        run_id=run_id,
        entity_hint="species",
        pages=species_pages,
        template=ENTITY_CONFIGS["species"]["detail_template"],
        source_pages=source_pages,
        snapshots=snapshots,
    )
    append_pages(
        run_id=run_id,
        entity_hint="move",
        pages=move_pages,
        template=ENTITY_CONFIGS["move"]["detail_template"],
        source_pages=source_pages,
        snapshots=snapshots,
    )

    normalized = build_candidates_from_snapshots(
        run_id=run_id,
        source_pages=source_pages,
        snapshots=snapshots,
        chart=chart,
    )
    normalized["validation_events"] = validation_events + normalized["validation_events"]
    return write_completed_artifacts(
        args=args,
        run_id=run_id,
        output_dir=output_dir,
        writer=writer,
        started_at=started_at,
        source_pages=source_pages,
        snapshots=snapshots,
        normalized=normalized,
        fetch_strategy=fetch_strategy,
    )


def run_clean_only(args: argparse.Namespace) -> dict[str, Path]:
    if args.clean_input_dir is None:
        raise SystemExit("--clean-input-dir is required when --execution-mode=clean-only.")

    input_dir = args.clean_input_dir.resolve()
    run_id = args.run_id or f"{make_run_id()}_clean_only"
    output_dir = (args.output_dir or (DEFAULT_OUTPUT_ROOT / run_id)).resolve()
    writer = ArtifactWriter(output_dir)
    started_at = utc_now()
    chart = RocoWorldTypeChart()

    source_pages_path = input_dir / "source_pages.jsonl"
    snapshots_path = input_dir / "raw_template_snapshots.jsonl"
    if not source_pages_path.exists() or not snapshots_path.exists():
        raise SystemExit("--clean-input-dir must contain source_pages.jsonl and raw_template_snapshots.jsonl.")

    source_pages = clone_cached_source_pages(load_jsonl(source_pages_path), run_id)
    snapshots = clone_snapshots(load_jsonl(snapshots_path), run_id)
    normalized = build_candidates_from_snapshots(
        run_id=run_id,
        source_pages=source_pages,
        snapshots=snapshots,
        chart=chart,
    )
    return write_completed_artifacts(
        args=args,
        run_id=run_id,
        output_dir=output_dir,
        writer=writer,
        started_at=started_at,
        source_pages=source_pages,
        snapshots=snapshots,
        normalized=normalized,
        fetch_strategy="cached_source_pages",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded P1d wiki battle dex dry-run without database mutation.")
    parser.add_argument("--execution-mode", choices=("fetch-clean", "clean-only"), default="fetch-clean")
    parser.add_argument("--scope", choices=(SCOPE_BATTLE_DEX, SCOPE_MOVE, SCOPE_SPECIES), default=SCOPE_BATTLE_DEX)
    parser.add_argument("--api-base-url", default=API_BASE_URL)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--clean-input-dir", type=Path, default=None)
    parser.add_argument("--cached-move-input-dir", type=Path, default=None)
    parser.add_argument("--species-limit", type=int, default=8)
    parser.add_argument("--move-limit", type=int, default=8)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.scope != SCOPE_SPECIES and args.move_limit < 1:
        raise SystemExit("--move-limit must be positive.")
    if args.scope != SCOPE_MOVE and args.species_limit < 1:
        raise SystemExit("--species-limit must be positive unless --scope move is used.")
    if args.scope == SCOPE_SPECIES and args.cached_move_input_dir is None:
        raise SystemExit("--cached-move-input-dir is required when --scope species is used.")
    if args.scope != SCOPE_SPECIES and args.cached_move_input_dir is not None:
        raise SystemExit("--cached-move-input-dir is only supported when --scope species is used.")
    if args.execution_mode == "clean-only":
        paths = run_clean_only(args)
    else:
        paths = run_dry_run(args)
    print("Wrote P1d dry-run artifacts:")
    for name, path in sorted(paths.items()):
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
