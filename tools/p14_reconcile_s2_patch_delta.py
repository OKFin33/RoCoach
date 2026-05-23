from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import hashlib
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATCH = REPO_ROOT / "data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_patch_delta_pack_v0.yaml"
DEFAULT_DB = REPO_ROOT / "data/runtime/battle_dex.sqlite"
DEFAULT_OUTPUT = REPO_ROOT / "data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_a_layer_reconciliation_v0.yaml"

STAT_KEYS = {
    "hp": "生命",
    "physical_attack": "物攻",
    "magical_attack": "魔攻",
    "physical_defense": "物防",
    "magical_defense": "魔防",
    "speed": "速度",
}

SPECIES_ALIASES = {
    "古卷甲魔像": ("古卷匣魔像", "visual_or_ocr_alias"),
    "塞音蛇": ("寒音蛇", "visual_or_ocr_alias"),
    "花鱼": ("龙鱼", "visual_or_ocr_alias_high_impact"),
    "风滚蓟虫": ("风滚暮虫", "visual_or_ocr_alias"),
    "雅丹鬓": ("雅丹鬃", "visual_or_ocr_alias"),
    "混乱触彩": ("混乱鱿彩", "visual_or_ocr_alias"),
    "高脚鹤": ("高脚鹬", "visual_or_ocr_alias"),
}

FORM_ALIASES = {
    "翠绿纱布": ("翠绿纶布", "visual_or_ocr_alias"),
    "储水时的样子": ("储水期的样子", "wording_alias"),
}

MOVE_ALIASES = {
    "聚盅": ("聚盐", "visual_or_ocr_alias_by_effect_text"),
}

ABILITY_ALIASES = {
    "回游": ("洄游", "canonical_ability_name"),
}

WORDING_ENTITY_OVERRIDES = {
    "化茧": "ability",
    "小偷小摸": "ability",
    "双向光速": "ability",
    "复方汤剂": "ability",
    "先手": "concept",
}

USER_ACCEPTED_STAT_OLD_VALUE_CONFLICTS = {
    ("爵士鹿", None): "PM accepted: freeze S1 Dex as historical baseline, but use S2 patch new stat value for candidate overlay because 爵士鹿/波普鹿 S1 physical attack may be uncertain.",
}

USER_ACCEPTED_ABILITY_TEXT_DIFFS = {
    ("祭礼巨像", "坠星"): "PM accepted as wording-only old-text difference.",
    ("波普鹿", "超级电池"): "PM accepted as wording-only old-text difference.",
}

USER_ACCEPTED_WORDING_TEXT_DIFFS = {
    "双向光速": "PM accepted as wording-only old-text difference.",
}

MECHANISM_CONCEPT_ROUTES = {
    "先手": "Route to B-layer mechanism/concept clarification: 先手度 is priority +x-like action priority, not speed; S2 screenshot explicitly states priority values can stack. Treat as explicit documentation/clarification unless later evidence proves this was a mechanical change.",
}

READY_STAT_STATUSES = {"ready_candidate_overlay", "ready_candidate_overlay_pm_accepted_old_value_conflict"}
READY_ABILITY_STATUSES = {"ready_candidate_overlay", "ready_candidate_overlay_pm_accepted_text_diff"}
READY_MOVE_POOL_STATUSES = {"ready_candidate_addition", "already_present_in_current_a_layer"}
READY_MOVE_EFFECT_STATUSES = {"ready_candidate_overlay", "ready_candidate_overlay_pm_accepted_old_value_conflict"}
READY_WORDING_STATUSES = {
    "ready_candidate_wording_update",
    "ready_candidate_wording_update_pm_accepted_text_diff",
    "routed_to_mechanism_concept_candidate",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[\s,，。:：；;（）()「」\"'、]", "", value)


def _split_species_form(label: str) -> tuple[str, str | None]:
    match = re.match(r"^(?P<name>[^（(]+)[（(](?P<form>.+?)[）)]$", label)
    if not match:
        return label, None
    form = match.group("form").strip()
    form = form.removesuffix("的样子").strip()
    return match.group("name").strip(), form


def _canonical_species_query(entity: str, form: str | None) -> tuple[str, str | None, list[dict[str, str]]]:
    notes: list[dict[str, str]] = []
    name = entity
    if name in SPECIES_ALIASES:
        canonical, reason = SPECIES_ALIASES[name]
        notes.append({"raw": name, "canonical": canonical, "reason": reason})
        name = canonical
    canonical_form = form
    if canonical_form and "首领化" in canonical_form:
        notes.append({"raw_form": canonical_form, "canonical_form": "首领形态", "reason": "boss_form_wording_alias"})
        canonical_form = "首领形态"
    if canonical_form in FORM_ALIASES:
        alias, reason = FORM_ALIASES[canonical_form]
        notes.append({"raw_form": canonical_form, "canonical_form": alias, "reason": reason})
        canonical_form = alias
    return name, canonical_form, notes


def _canonical_move_query(move: str) -> tuple[str, list[dict[str, str]]]:
    if move in MOVE_ALIASES:
        canonical, reason = MOVE_ALIASES[move]
        return canonical, [{"raw": move, "canonical": canonical, "reason": reason}]
    return move, []


def _canonical_ability_query(ability: str) -> tuple[str, list[dict[str, str]]]:
    if ability in ABILITY_ALIASES:
        canonical, reason = ABILITY_ALIASES[ability]
        return canonical, [{"raw": ability, "canonical": canonical, "reason": reason}]
    return ability, []


def _resolve_species(conn: sqlite3.Connection, entity: str, form: str | None = None) -> dict[str, Any]:
    name, canonical_form, notes = _canonical_species_query(entity, form)
    rows = conn.execute(
        """
        SELECT species_id, display_name, initial_species_name, form_name,
               regional_form_name, base_stats_json, ability_name, ability_effect_text
        FROM species_form
        WHERE display_name = ? OR initial_species_name = ?
        ORDER BY display_name, species_id
        """,
        (name, name),
    ).fetchall()
    if canonical_form:
        form_needles = {canonical_form, f"{canonical_form}的样子"}
        rows = [
            row
            for row in rows
            if row["regional_form_name"] in form_needles
            or row["form_name"] in form_needles
            or row["regional_form_name"] == canonical_form
            or row["form_name"] == canonical_form
        ]
    if len(rows) == 1:
        row = dict(rows[0])
        row.pop("base_stats_json", None)
        return {
            "status": "resolved_alias" if notes else "resolved_exact",
            "query": {"entity": entity, "form": form},
            "canonical_query": {"entity": name, "form": canonical_form},
            "species": row,
            "alias_notes": notes,
        }
    if not canonical_form and len(rows) > 1:
        original_rows = [
            row
            for row in rows
            if row["form_name"] == "原始形态" and row["regional_form_name"] is None
        ]
        if len(original_rows) == 1:
            row = dict(original_rows[0])
            row.pop("base_stats_json", None)
            return {
                "status": "resolved_alias" if notes else "resolved_exact",
                "query": {"entity": entity, "form": form},
                "canonical_query": {"entity": name, "form": canonical_form},
                "species": row,
                "alias_notes": notes
                + [{"reason": "duplicate_display_prefer_original_form_without_regional_suffix"}],
            }
    if not rows:
        return {
            "status": "unresolved",
            "query": {"entity": entity, "form": form},
            "canonical_query": {"entity": name, "form": canonical_form},
            "alias_notes": notes,
        }
    return {
        "status": "ambiguous",
        "query": {"entity": entity, "form": form},
        "canonical_query": {"entity": name, "form": canonical_form},
        "candidates": [dict(row) | {"base_stats_json": None} for row in rows],
        "alias_notes": notes,
    }


def _resolve_move(conn: sqlite3.Connection, move: str) -> dict[str, Any]:
    name, notes = _canonical_move_query(move)
    rows = conn.execute(
        """
        SELECT move_id, move_name, move_type, category_raw, power, energy_cost, effect_text, description_text
        FROM move
        WHERE move_name = ?
        ORDER BY move_id
        """,
        (name,),
    ).fetchall()
    if len(rows) == 1:
        return {
            "status": "resolved_alias" if notes else "resolved_exact",
            "query": move,
            "canonical_query": name,
            "move": dict(rows[0]),
            "alias_notes": notes,
        }
    if not rows:
        return {"status": "unresolved", "query": move, "canonical_query": name, "alias_notes": notes}
    return {
        "status": "ambiguous",
        "query": move,
        "canonical_query": name,
        "candidates": [dict(row) for row in rows],
        "alias_notes": notes,
    }


def _resolve_ability(conn: sqlite3.Connection, ability: str) -> dict[str, Any]:
    name, notes = _canonical_ability_query(ability)
    rows = conn.execute(
        """
        SELECT ability_id, ability_name, effect_text, source_species_ids_json
        FROM derived_ability
        WHERE ability_name = ?
        ORDER BY ability_id
        """,
        (name,),
    ).fetchall()
    if len(rows) == 1:
        return {
            "status": "resolved_alias" if notes else "resolved_exact",
            "query": ability,
            "canonical_query": name,
            "ability": dict(rows[0]),
            "alias_notes": notes,
        }
    if not rows:
        return {"status": "unresolved", "query": ability, "canonical_query": name, "alias_notes": notes}
    return {
        "status": "ambiguous",
        "query": ability,
        "canonical_query": name,
        "candidates": [dict(row) for row in rows],
        "alias_notes": notes,
    }


def _stat_current(conn: sqlite3.Connection, species_id: str) -> dict[str, int]:
    raw = conn.execute("SELECT base_stats_json FROM species_form WHERE species_id = ?", (species_id,)).fetchone()
    return json.loads(raw["base_stats_json"]) if raw else {}


def _extract_int_after(label: str, text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(rf"{re.escape(label)}\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _same_old_effect(current: str | None, old_effect: str | None) -> bool:
    current_norm = _normalize_text(current)
    old_norm = _normalize_text(old_effect)
    return bool(current_norm and old_norm and (current_norm == old_norm or old_norm in current_norm or current_norm in old_norm))


def reconcile(patch_path: Path, db_path: Path, *, created_at: str) -> dict[str, Any]:
    patch = yaml.safe_load(patch_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    stat_overlays: list[dict[str, Any]] = []
    ability_overlays: list[dict[str, Any]] = []
    move_pool_additions: list[dict[str, Any]] = []
    move_effect_overlays: list[dict[str, Any]] = []
    wording_updates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for item in patch.get("stat_deltas", []):
        species = _resolve_species(conn, item["entity"], item.get("form"))
        record = {"source_image_id": item["source_image_id"], "resolution": species}
        if species["status"].startswith("resolved"):
            current_stats = _stat_current(conn, species["species"]["species_id"])
            changes = []
            all_old_match = True
            for key, values in item.get("stats", {}).items():
                stat_name = STAT_KEYS[key]
                current = current_stats.get(stat_name)
                old_match = current == values.get("old")
                all_old_match = all_old_match and old_match
                changes.append(
                    {
                        "stat": stat_name,
                        "current_a_layer": current,
                        "patch_old": values.get("old"),
                        "patch_new": values.get("new"),
                        "old_matches_current_a_layer": old_match,
                    }
                )
            record["changes"] = changes
            record["status"] = "ready_candidate_overlay" if all_old_match else "old_value_conflict"
            override_key = (item["entity"], item.get("form"))
            if record["status"] == "old_value_conflict" and override_key in USER_ACCEPTED_STAT_OLD_VALUE_CONFLICTS:
                record["status"] = "ready_candidate_overlay_pm_accepted_old_value_conflict"
                record["pm_review_note"] = USER_ACCEPTED_STAT_OLD_VALUE_CONFLICTS[override_key]
        else:
            record["status"] = species["status"]
            unresolved.append({"kind": "stat_delta", "entity": item["entity"], "form": item.get("form"), "resolution": species})
        stat_overlays.append(record)

    for item in patch.get("ability_deltas", []):
        species = _resolve_species(conn, item["entity"], item.get("form"))
        ability = _resolve_ability(conn, item["ability"])
        status = "ready_candidate_overlay"
        if not species["status"].startswith("resolved") or not ability["status"].startswith("resolved"):
            status = "unresolved"
            unresolved.append(
                {
                    "kind": "ability_delta",
                    "entity": item["entity"],
                    "ability": item["ability"],
                    "species_resolution": species,
                    "ability_resolution": ability,
                }
            )
        else:
            if species["species"]["ability_name"] != ability["ability"]["ability_name"]:
                status = "species_ability_mismatch"
            elif not _same_old_effect(ability["ability"]["effect_text"], item.get("old_effect")):
                status = "old_effect_text_differs"
                override_key = (item["entity"], item["ability"])
                if override_key in USER_ACCEPTED_ABILITY_TEXT_DIFFS:
                    status = "ready_candidate_overlay_pm_accepted_text_diff"
        record = {
            "source_image_id": item["source_image_id"],
            "status": status,
            "species_resolution": species,
            "ability_resolution": ability,
            "patch_old_effect": item.get("old_effect"),
            "patch_new_effect": item.get("new_effect"),
        }
        override_key = (item["entity"], item["ability"])
        if status == "ready_candidate_overlay_pm_accepted_text_diff" and override_key in USER_ACCEPTED_ABILITY_TEXT_DIFFS:
            record["pm_review_note"] = USER_ACCEPTED_ABILITY_TEXT_DIFFS[override_key]
        ability_overlays.append(record)

    for group in patch.get("move_pool_additions", []):
        move = _resolve_move(conn, group["move"])
        for raw_form in group.get("added_learning_forms", []):
            entity, form = _split_species_form(raw_form)
            species = _resolve_species(conn, entity, form)
            status = "ready_candidate_addition"
            existing = None
            if not species["status"].startswith("resolved") or not move["status"].startswith("resolved"):
                status = "unresolved"
                unresolved.append(
                    {
                        "kind": "move_pool_addition",
                        "species_label": raw_form,
                        "move": group["move"],
                        "species_resolution": species,
                        "move_resolution": move,
                    }
                )
            else:
                existing = conn.execute(
                    """
                    SELECT access_channel, source_field, confidence
                    FROM species_move_pool
                    WHERE species_id = ? AND move_id = ?
                    ORDER BY access_channel
                    """,
                    (species["species"]["species_id"], move["move"]["move_id"]),
                ).fetchall()
                if existing:
                    status = "already_present_in_current_a_layer"
            move_pool_additions.append(
                {
                    "source_image_id": group["source_image_id"],
                    "status": status,
                    "species_label": raw_form,
                    "species_resolution": species,
                    "move_resolution": move,
                    "current_a_layer_entries": [dict(row) for row in existing] if existing else [],
                }
            )

    for item in patch.get("wording_only_skill_description_deltas", []):
        entity_type = WORDING_ENTITY_OVERRIDES.get(item["move"], "move")
        if entity_type == "ability":
            resolution = _resolve_ability(conn, item["move"])
            current_text = resolution.get("ability", {}).get("effect_text")
        elif entity_type == "concept":
            resolution = {"status": "mechanism_concept", "query": item["move"], "canonical_query": item["move"]}
            current_text = None
        else:
            resolution = _resolve_move(conn, item["move"])
            current_text = resolution.get("move", {}).get("effect_text")
        if entity_type == "concept" and item["move"] in MECHANISM_CONCEPT_ROUTES:
            status = "routed_to_mechanism_concept_candidate"
        else:
            status = "ready_candidate_wording_update" if resolution["status"].startswith("resolved") else resolution["status"]
        if resolution["status"].startswith("resolved") and not _same_old_effect(current_text, item.get("old_text")):
            status = "old_text_differs"
            if item["move"] in USER_ACCEPTED_WORDING_TEXT_DIFFS:
                status = "ready_candidate_wording_update_pm_accepted_text_diff"
        if not resolution["status"].startswith("resolved") and status != "routed_to_mechanism_concept_candidate":
            unresolved.append({"kind": "wording_update", "entity": item["move"], "entity_type": entity_type, "resolution": resolution})
        record = {
            "source_image_id": item["source_image_id"],
            "entity_type": entity_type,
            "status": status,
            "resolution": resolution,
            "current_a_layer_text": current_text,
            "patch_old_text": item.get("old_text"),
            "patch_new_text": item.get("new_text"),
        }
        if status == "routed_to_mechanism_concept_candidate":
            record["mechanism_route_note"] = MECHANISM_CONCEPT_ROUTES[item["move"]]
        elif status == "ready_candidate_wording_update_pm_accepted_text_diff":
            record["pm_review_note"] = USER_ACCEPTED_WORDING_TEXT_DIFFS[item["move"]]
        wording_updates.append(record)

    for item in patch.get("move_effect_deltas", []):
        move = _resolve_move(conn, item["move"])
        status = "ready_candidate_overlay" if move["status"].startswith("resolved") else move["status"]
        checks: list[dict[str, Any]] = []
        old_text = item.get("old_text")
        new_text = item.get("new_text")
        if move["status"].startswith("resolved"):
            old_power = _extract_int_after("威力", old_text)
            new_power = _extract_int_after("威力", new_text)
            old_energy = _extract_int_after("技能能耗", old_text)
            new_energy = _extract_int_after("技能能耗", new_text)
            if old_power is not None:
                checks.append(
                    {
                        "field": "power",
                        "current_a_layer": move["move"]["power"],
                        "patch_old": old_power,
                        "patch_new": new_power,
                        "old_matches_current_a_layer": move["move"]["power"] == old_power,
                    }
                )
            if old_energy is not None:
                checks.append(
                    {
                        "field": "energy_cost",
                        "current_a_layer": move["move"]["energy_cost"],
                        "patch_old": old_energy,
                        "patch_new": new_energy,
                        "old_matches_current_a_layer": move["move"]["energy_cost"] == old_energy,
                    }
                )
            if any(check.get("old_matches_current_a_layer") is False for check in checks):
                status = "old_value_conflict"
        else:
            unresolved.append({"kind": "move_effect_delta", "move": item["move"], "resolution": move})
        move_effect_overlays.append(
            {
                "source_image_id": item["source_image_id"],
                "status": status,
                "move_resolution": move,
                "field_checks": checks,
                "patch_old_text": old_text,
                "patch_new_text": new_text,
                "structured_changes": item.get("changes", []),
            }
        )

    counts = {
        "stat_overlay_entries": len(stat_overlays),
        "stat_ready": sum(1 for item in stat_overlays if item["status"] in READY_STAT_STATUSES),
        "ability_overlay_entries": len(ability_overlays),
        "ability_ready": sum(1 for item in ability_overlays if item["status"] in READY_ABILITY_STATUSES),
        "move_pool_addition_entries": len(move_pool_additions),
        "move_pool_ready": sum(1 for item in move_pool_additions if item["status"] in READY_MOVE_POOL_STATUSES),
        "move_effect_entries": len(move_effect_overlays),
        "move_effect_ready": sum(1 for item in move_effect_overlays if item["status"] in READY_MOVE_EFFECT_STATUSES),
        "wording_update_entries": len(wording_updates),
        "wording_ready": sum(1 for item in wording_updates if item["status"] in READY_WORDING_STATUSES),
        "mechanism_concept_routed": sum(
            1 for item in wording_updates if item["status"] == "routed_to_mechanism_concept_candidate"
        ),
        "unresolved_or_non_dex_items": len(unresolved),
    }

    official_source = (patch.get("source_policy") or {}).get("official_source") or {}

    return {
        "schema_version": "p14.s2_a_layer_reconciliation.v0",
        "id": "s2_2026-05-21_a_layer_reconciliation_v0",
        "created_at": created_at,
        "runtime_allowed": False,
        "promotion_status": "candidate_only",
        "patch_delta_ref": str(patch_path.relative_to(REPO_ROOT)),
        "patch_delta_sha256": _sha256(patch_path),
        "a_layer_db_ref": str(db_path.relative_to(REPO_ROOT)),
        "a_layer_db_sha256": _sha256(db_path),
        "source_policy": {
            "may_write_runtime_db": False,
            "may_generate_candidate_overlay": True,
            "official_patch_note_ref": official_source.get("source_manifest_ref", ""),
            "requires_pm_review_before_a_layer_write": True,
            "requires_runtime_db_snapshot_before_runtime_promotion": True,
        },
        "pm_review_decisions": {
            "爵士鹿_stat_old_value_conflict": USER_ACCEPTED_STAT_OLD_VALUE_CONFLICTS[("爵士鹿", None)],
            "祭礼巨像_坠星_old_text_diff": USER_ACCEPTED_ABILITY_TEXT_DIFFS[("祭礼巨像", "坠星")],
            "波普鹿_超级电池_old_text_diff": USER_ACCEPTED_ABILITY_TEXT_DIFFS[("波普鹿", "超级电池")],
            "双向光速_old_text_diff": USER_ACCEPTED_WORDING_TEXT_DIFFS["双向光速"],
            "先手_route": MECHANISM_CONCEPT_ROUTES["先手"],
        },
        "summary": counts,
        "stat_overlays": stat_overlays,
        "ability_overlays": ability_overlays,
        "move_pool_additions": move_pool_additions,
        "wording_updates": wording_updates,
        "move_effect_overlays": move_effect_overlays,
        "unresolved_or_non_dex_items": unresolved,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-at", default="2026-05-23T00:00:00+08:00")
    args = parser.parse_args()

    result = reconcile(args.patch, args.db, created_at=args.created_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"wrote {args.output}")
    print(yaml.safe_dump({"summary": result["summary"]}, allow_unicode=True, sort_keys=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
