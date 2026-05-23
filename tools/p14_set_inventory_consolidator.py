#!/usr/bin/env python3
"""Consolidate P14 source-level Set Inventory into cross-source signals.

This is an emergence observer, not a promotion tool. It groups L1a/L1b source
inventory records by species, counts repeated legal move evidence across
sources, and emits a PM-readable brief. It never writes runtime graph data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import DEFAULT_BATTLE_DEX, DEFAULT_OUT_ROOT, NoAliasDumper, _relpath


DEFAULT_BATCH_ID = f"phase1_set_inventory_consolidation_{date.today().isoformat()}"
DEFAULT_INVENTORY_DIR = DEFAULT_OUT_ROOT / "set_inventory"
CONSOLIDATION_DIRNAME = "set_inventory_consolidation"

DAMAGE_AXIS_BY_CATEGORY = {
    "物攻": "physical",
    "物理": "physical",
    "魔攻": "magical",
    "魔法": "magical",
    "状态": "status",
    "变化": "status",
}

BUILD_AXIS_KEYWORDS = {
    "物攻": "physical",
    "攻击": "physical",
    "魔攻": "magical",
    "魔法": "magical",
    "双刀": "mixed",
    "速度": "speed",
    "极速": "speed",
    "肉": "bulk",
    "耐久": "bulk",
    "防御": "bulk",
    "血量": "bulk",
}

ROLE_GROUPS = {
    "cleaner": "offense",
    "pressure": "offense",
    "setup": "offense",
    "lead": "lead",
    "pivot_in": "pivot",
    "defensive_pivot": "defense",
    "support_transfer": "support",
    "preserve_resource": "support",
}

HARD_CONFLICT_AXIS_GROUPS = [
    {"physical", "magical"},
    {"speed", "bulk"},
]
MAX_STANDARD_SET_MOVES = 4


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def load_move_metadata(db_path: Path = DEFAULT_BATTLE_DEX) -> dict[str, dict[str, Any]]:
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "select move_name, move_type, category_raw, power, energy_cost from move"
        ).fetchall()
    finally:
        conn.close()
    return {
        str(move_name): {
            "move_type": move_type,
            "category_raw": category_raw,
            "power": power,
            "energy_cost": energy_cost,
        }
        for move_name, move_type, category_raw, power, energy_cost in rows
    }


def load_inventories(
    inventory_dir: Path = DEFAULT_INVENTORY_DIR,
    *,
    source_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    inventories: list[dict[str, Any]] = []
    for path in sorted(inventory_dir.glob("*.source_inventory.yaml")):
        payload = _load_yaml(path)
        source_id = str(payload.get("source_id") or path.name.split(".")[0])
        if source_ids and source_id not in source_ids:
            continue
        payload["_inventory_path"] = str(path)
        inventories.append(payload)
    return inventories


def _source_id(inventory: dict[str, Any]) -> str:
    return str(inventory.get("source_id") or "")


def _source_type(inventory: dict[str, Any]) -> str:
    return str((inventory.get("source") or {}).get("source_type") or "")


def _low_confidence_use(inventory: dict[str, Any]) -> str:
    return str((inventory.get("source") or {}).get("low_confidence_use") or "")


def _is_primary_source(inventory: dict[str, Any]) -> bool:
    return not _low_confidence_use(inventory)


def _axis_from_category(category: Any) -> str | None:
    value = str(category or "")
    for raw, axis in DAMAGE_AXIS_BY_CATEGORY.items():
        if raw in value:
            return axis
    return None


def _damage_axis(moves: list[str], move_metadata: dict[str, dict[str, Any]]) -> str:
    axes = {
        axis
        for move in moves
        if (axis := _axis_from_category((move_metadata.get(move) or {}).get("category_raw"))) and axis != "status"
    }
    if axes == {"physical"}:
        return "physical"
    if axes == {"magical"}:
        return "magical"
    if "physical" in axes and "magical" in axes:
        return "mixed"
    if not axes and moves:
        return "status_or_unknown"
    return "unknown"


def _collect_build_axes(configuration: dict[str, Any]) -> list[str]:
    axes: set[str] = set()
    haystack: list[str] = []
    for key in ("nature", "individual_values", "bloodline", "ability_mentions", "mechanism_mentions"):
        values = configuration.get(key) or []
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    haystack.extend(str(value) for value in item.values())
                else:
                    haystack.append(str(item))
        elif values:
            haystack.append(str(values))
    joined = " ".join(haystack)
    for phrase, axis in BUILD_AXIS_KEYWORDS.items():
        if phrase in joined:
            axes.add(axis)
    return sorted(axes)


def _role_groups(roles: list[str]) -> list[str]:
    return sorted({ROLE_GROUPS.get(role, role) for role in roles})


def _has_hard_axis_conflict(axes_a: set[str], axes_b: set[str]) -> bool:
    for group in HARD_CONFLICT_AXIS_GROUPS:
        if axes_a & group and axes_b & group and not (axes_a & axes_b & group):
            return True
    return False


def _variant_split_reason(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    moves_a = set(a.get("moves") or [])
    moves_b = set(b.get("moves") or [])
    overlap = moves_a & moves_b
    min_size = max(1, min(len(moves_a), len(moves_b)))
    min_overlap_ratio = len(overlap) / min_size
    reasons: list[str] = []
    if len(overlap) == 0 and min_size >= 3:
        reasons.append("no_move_overlap")
    elif min_overlap_ratio < 0.5 and min_size >= 3:
        reasons.append("low_move_overlap")

    damage_axes = {a.get("damage_axis"), b.get("damage_axis")}
    if "physical" in damage_axes and "magical" in damage_axes and (len(overlap) == 0 or min_overlap_ratio < 0.5):
        reasons.append("damage_axis_divergence")

    if _has_hard_axis_conflict(set(a.get("build_axes") or []), set(b.get("build_axes") or [])):
        reasons.append("configuration_axis_divergence")

    role_groups_a = set(a.get("role_groups") or [])
    role_groups_b = set(b.get("role_groups") or [])
    if role_groups_a and role_groups_b and not role_groups_a & role_groups_b:
        if {"offense", "defense"} <= (role_groups_a | role_groups_b) or {"offense", "support"} <= (role_groups_a | role_groups_b):
            reasons.append("role_axis_divergence")

    return reasons


def _same_set_family(a: dict[str, Any], b: dict[str, Any]) -> bool:
    moves_a = set(a.get("moves") or [])
    moves_b = set(b.get("moves") or [])
    overlap = moves_a & moves_b
    min_size = max(1, min(len(moves_a), len(moves_b)))
    min_overlap_ratio = len(overlap) / min_size
    split_reasons = set(_variant_split_reason(a, b))
    strong_conflict = {"configuration_axis_divergence", "role_axis_divergence"} & split_reasons

    if len(overlap) >= 2 and not {"configuration_axis_divergence", "role_axis_divergence"} & split_reasons:
        return True
    if min_overlap_ratio >= 0.67 and not strong_conflict:
        return True
    if len(overlap) >= 1 and min(len(moves_a), len(moves_b)) <= 2 and not strong_conflict:
        return True
    return False


def _variant_sort_key(variant: dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(variant.get("low_confidence_use")),
        -len(variant.get("moves") or []),
        variant.get("source_id", ""),
    )


def _family_core_moves(variants: list[dict[str, Any]]) -> list[str]:
    counts = Counter(move for variant in variants for move in (variant.get("moves") or []))
    if len(variants) <= 1:
        return []
    return [move for move, count in counts.most_common() if count >= 2]


def _core_cooccurrence_primary_source_count(members: list[dict[str, Any]], core_moves: list[str]) -> int:
    core = set(core_moves)
    if not core:
        return 0
    return sum(
        1
        for member in members
        if not member.get("low_confidence_use") and len(core & set(member.get("moves") or [])) >= 2
    )


def _build_set_families(variants: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sorted_variants = sorted(variants, key=_variant_sort_key)
    families: list[dict[str, Any]] = []
    split_hypotheses: list[dict[str, Any]] = []

    for variant in sorted_variants:
        assigned = False
        for family in families:
            if any(_same_set_family(variant, member) for member in family["variants"]):
                family["variants"].append(variant)
                assigned = True
                break
        if not assigned:
            families.append({"variants": [variant]})

    rendered_families: list[dict[str, Any]] = []
    for index, family in enumerate(families, start=1):
        members = sorted(family["variants"], key=_variant_sort_key)
        move_counts = Counter(move for variant in members for move in (variant.get("moves") or []))
        core_moves = _family_core_moves(members)
        core_cooccurrence_count = _core_cooccurrence_primary_source_count(members, core_moves)
        flex_moves = [move for move, _ in move_counts.most_common() if move not in core_moves]
        primary_sources = sorted({variant["source_id"] for variant in members if not variant.get("low_confidence_use")})
        supporting_sources = sorted({variant["source_id"] for variant in members if variant.get("low_confidence_use")})
        damage_axes = sorted({axis for variant in members if (axis := variant.get("damage_axis")) and axis != "unknown"})
        role_groups = sorted({role for variant in members for role in (variant.get("role_groups") or [])})
        build_axes = sorted({axis for variant in members for axis in (variant.get("build_axes") or [])})
        rendered_families.append(
            {
                "family_id": f"family_{index:02d}",
                "family_state": "candidate_set_family" if len(members) > 1 else "single_source_or_sparse_family",
                "variant_count": len(members),
                "primary_source_count": len(primary_sources),
                "primary_source_ids": primary_sources,
                "supporting_source_count": len(supporting_sources),
                "supporting_source_ids": supporting_sources,
                "core_moves": core_moves,
                "flex_moves": flex_moves,
                "core_cooccurrence_primary_source_count": core_cooccurrence_count,
                "representative_moves": [move for move, _ in move_counts.most_common(6)],
                "damage_axes": damage_axes,
                "role_groups": role_groups,
                "build_axes": build_axes,
                "alter_variants": [
                    {
                        "source_id": variant["source_id"],
                        "variant_type": "alter_variant" if len(members) > 1 else "source_variant",
                        "moves": variant.get("moves") or [],
                        "roles": variant.get("roles") or [],
                        "damage_axis": variant.get("damage_axis"),
                        "build_axes": variant.get("build_axes") or [],
                        "configuration": variant.get("configuration") or {},
                        "low_confidence_use": variant.get("low_confidence_use"),
                    }
                    for variant in members
                ],
                "runtime_allowed": False,
            }
        )

    if len(rendered_families) > 1:
        for left_index, left in enumerate(families):
            for right_index, right in enumerate(families[left_index + 1 :], start=left_index + 1):
                reason_counts = Counter(
                    reason
                    for left_variant in left["variants"]
                    for right_variant in right["variants"]
                    for reason in _variant_split_reason(left_variant, right_variant)
                )
                if reason_counts:
                    split_hypotheses.append(
                        {
                            "hypothesis_id": f"split_{left_index + 1:02d}_{right_index + 1:02d}",
                            "family_ids": [f"family_{left_index + 1:02d}", f"family_{right_index + 1:02d}"],
                            "reason_codes": [reason for reason, _ in reason_counts.most_common()],
                            "status": "candidate_only_needs_more_flow_specific_evidence",
                            "runtime_allowed": False,
                        }
                    )

    return rendered_families, split_hypotheses


def _family_review_candidates(species_name: str, families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for family in families:
        core_moves = list(family.get("core_moves") or [])
        primary_source_count = int(family.get("primary_source_count") or 0)
        core_cooccurrence_count = int(family.get("core_cooccurrence_primary_source_count") or 0)
        if primary_source_count < 2 or len(core_moves) < 2:
            continue
        if len(core_moves) > MAX_STANDARD_SET_MOVES:
            continue
        if core_cooccurrence_count < 2:
            continue
        candidates.append(
            {
                "review_scope": "set_family",
                "species_name": species_name,
                "family_id": family["family_id"],
                "family_state": family.get("family_state"),
                "core_moves": core_moves,
                "flex_moves": list(family.get("flex_moves") or []),
                "representative_moves": list(family.get("representative_moves") or []),
                "primary_source_count": primary_source_count,
                "primary_source_ids": list(family.get("primary_source_ids") or []),
                "core_cooccurrence_primary_source_count": core_cooccurrence_count,
                "supporting_source_count": int(family.get("supporting_source_count") or 0),
                "supporting_source_ids": list(family.get("supporting_source_ids") or []),
                "damage_axes": list(family.get("damage_axes") or []),
                "role_groups": list(family.get("role_groups") or []),
                "build_axes": list(family.get("build_axes") or []),
                "promotion_boundary": "family_only_species_level_card_remains_blocked_if_split_hypotheses_exist",
                "suggested_next_action": "build_family_level_reviewer_packet_before_any_promotion",
                "runtime_allowed": False,
            }
        )
    return candidates


def _move_records(move_sources: dict[str, dict[str, set[str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for move_name, buckets in move_sources.items():
        primary_sources = sorted(buckets["primary"])
        supporting_sources = sorted(buckets["supporting"])
        sources = sorted(set(primary_sources) | set(supporting_sources))
        rows.append(
            {
                "move_name": move_name,
                "source_count": len(sources),
                "primary_source_count": len(primary_sources),
                "supporting_source_count": len(supporting_sources),
                "sources": sources,
            }
        )
    return sorted(rows, key=lambda item: (-item["primary_source_count"], -item["source_count"], item["move_name"]))


def _state_for_record(
    *,
    primary_source_count: int,
    supporting_source_count: int,
    stable_moves: list[str],
    observed_moves: list[dict[str, Any]],
    dossier_variants: list[dict[str, Any]],
    split_hypotheses: list[dict[str, Any]] | None = None,
) -> str:
    if split_hypotheses:
        return "split_blocked"
    if len(stable_moves) > MAX_STANDARD_SET_MOVES:
        return "split_blocked"
    primary_move_count = sum(1 for item in observed_moves if item["primary_source_count"] > 0)
    if primary_source_count >= 2 and len(stable_moves) >= 2:
        return "review_candidate"
    if primary_source_count >= 2 or (primary_source_count >= 1 and supporting_source_count >= 1):
        return "emerging"
    if primary_move_count > 0:
        return "needs_more_source"
    return "coverage_only"


def _next_action(
    *,
    state: str,
    stable_moves: list[str],
    primary_source_count: int,
    supporting_source_count: int,
    split_hypotheses: list[dict[str, Any]] | None = None,
    family_review_candidates: list[dict[str, Any]] | None = None,
) -> str:
    if len(stable_moves) > MAX_STANDARD_SET_MOVES:
        return "recluster_overwide_move_pool_before_reviewer_packet"
    if split_hypotheses and family_review_candidates:
        return "build_family_level_reviewer_packet_keep_species_split_blocked"
    if split_hypotheses:
        return "resolve_same_species_set_family_split_before_reviewer_packet"
    if state == "review_candidate":
        return "build_reviewer_packet_before_any_promotion"
    if state == "emerging" and len(stable_moves) < 2:
        return "add_targeted_sources_until_repeated_move_skeleton_emerges"
    if primary_source_count == 0 and supporting_source_count > 0:
        return "find_primary_source_because_current_signal_is_support_only"
    if state == "needs_more_source":
        return "collect_more_sources_before_review"
    return "keep_as_coverage_until_move_evidence_appears"


def _promotion_blockers(
    state: str,
    stable_moves: list[str],
    primary_source_count: int,
    split_hypotheses: list[dict[str, Any]] | None = None,
) -> list[str]:
    blockers = ["runtime_promotion_forbidden", "pm_or_reviewer_review_required"]
    if split_hypotheses:
        blockers.append("same_species_set_family_split_unresolved")
    if len(stable_moves) > MAX_STANDARD_SET_MOVES:
        blockers.append("overwide_move_pool_needs_reclustering")
    if primary_source_count < 2:
        blockers.append("insufficient_primary_source_repetition")
    if len(stable_moves) < 2:
        blockers.append("insufficient_repeated_move_skeleton")
    if state != "review_candidate":
        blockers.append("not_review_candidate")
    return blockers


def build_consolidation(
    batch_id: str,
    inventories: list[dict[str, Any]],
    *,
    move_metadata: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    species: dict[str, dict[str, Any]] = {}
    source_lookup = {_source_id(inventory): inventory for inventory in inventories}
    move_metadata = move_metadata or {}

    for inventory in inventories:
        sid = _source_id(inventory)
        is_primary = _is_primary_source(inventory)
        for coverage in inventory.get("coverage_records") or []:
            name = str(coverage.get("species_name") or "")
            if not name:
                continue
            record = species.setdefault(
                name,
                {
                    "coverage_sources": set(),
                    "dossier_sources": set(),
                    "primary_sources": set(),
                    "supporting_sources": set(),
                    "move_sources": defaultdict(lambda: {"primary": set(), "supporting": set()}),
                    "role_counter": Counter(),
                    "dossier_variants": [],
                    "excluded_move_counter": Counter(),
                },
            )
            record["coverage_sources"].add(sid)

        for dossier in inventory.get("set_dossiers") or []:
            name = str(dossier.get("species_name") or "")
            if not name:
                continue
            record = species.setdefault(
                name,
                {
                    "coverage_sources": set(),
                    "dossier_sources": set(),
                    "primary_sources": set(),
                    "supporting_sources": set(),
                    "move_sources": defaultdict(lambda: {"primary": set(), "supporting": set()}),
                    "role_counter": Counter(),
                    "dossier_variants": [],
                    "excluded_move_counter": Counter(),
                },
            )
            record["dossier_sources"].add(sid)
            source_bucket = "primary_sources" if is_primary else "supporting_sources"
            record[source_bucket].add(sid)
            moves = list((dossier.get("move_slots") or {}).get("known_moves") or [])
            configuration = dossier.get("configuration") or {}
            roles = (dossier.get("tactical_context") or {}).get("roles") or []
            for move_name in moves:
                bucket = "primary" if is_primary else "supporting"
                record["move_sources"][move_name][bucket].add(sid)
            record["role_counter"].update(roles)
            record["excluded_move_counter"].update((dossier.get("legality_filter") or {}).get("excluded_move_counts") or {})
            record["dossier_variants"].append(
                {
                    "source_id": sid,
                    "source_type": _source_type(inventory),
                    "low_confidence_use": _low_confidence_use(inventory),
                    "moves": moves,
                    "completeness": (dossier.get("move_slots") or {}).get("completeness"),
                    "roles": roles,
                    "role_groups": _role_groups(roles),
                    "damage_axis": _damage_axis(moves, move_metadata),
                    "build_axes": _collect_build_axes(configuration),
                    "configuration": configuration,
                    "mention_count": dossier.get("mention_count", 0),
                }
            )

    species_records: list[dict[str, Any]] = []
    for name, record in species.items():
        observed_moves = _move_records(record["move_sources"])
        stable_moves = [
            item["move_name"]
            for item in observed_moves
            if item["primary_source_count"] >= 2 or (item["primary_source_count"] >= 1 and item["supporting_source_count"] >= 1)
        ]
        primary_source_count = len(record["primary_sources"])
        supporting_source_count = len(record["supporting_sources"])
        set_families, split_hypotheses = _build_set_families(record["dossier_variants"])
        family_review_candidates = _family_review_candidates(name, set_families)
        state = _state_for_record(
            primary_source_count=primary_source_count,
            supporting_source_count=supporting_source_count,
            stable_moves=stable_moves,
            observed_moves=observed_moves,
            dossier_variants=record["dossier_variants"],
            split_hypotheses=split_hypotheses,
        )
        source_ids = sorted(record["coverage_sources"] | record["dossier_sources"])
        species_records.append(
            {
                "species_name": name,
                "state": state,
                "source_count": len(source_ids),
                "source_ids": source_ids,
                "primary_source_count": primary_source_count,
                "primary_source_ids": sorted(record["primary_sources"]),
                "supporting_source_count": supporting_source_count,
                "supporting_source_ids": sorted(record["supporting_sources"]),
                "coverage_source_count": len(record["coverage_sources"]),
                "coverage_source_ids": sorted(record["coverage_sources"]),
                "stable_moves": stable_moves,
                "observed_moves": observed_moves,
                "top_roles": [item for item, _ in record["role_counter"].most_common(6)],
                "dossier_variants": sorted(
                    record["dossier_variants"],
                    key=_variant_sort_key,
                ),
                "set_family_summary": {
                    "family_count": len(set_families),
                    "split_hypothesis_count": len(split_hypotheses),
                    "decision": "split_hypothesis" if split_hypotheses else "same_family_or_insufficient_split_evidence",
                    "default_policy": "keep_skill_differences_as_alter_variants_until_role_or_build_axis_split_is_supported",
                    "overwide_move_pool_blocked": len(stable_moves) > MAX_STANDARD_SET_MOVES,
                },
                "set_family_candidates": set_families,
                "split_hypotheses": split_hypotheses,
                "top_excluded_move_counts": dict(record["excluded_move_counter"].most_common(8)),
                "suggested_next_action": _next_action(
                    state=state,
                    stable_moves=stable_moves,
                    primary_source_count=primary_source_count,
                    supporting_source_count=supporting_source_count,
                    split_hypotheses=split_hypotheses,
                    family_review_candidates=family_review_candidates,
                ),
                "promotion_blockers": _promotion_blockers(state, stable_moves, primary_source_count, split_hypotheses),
                "family_review_candidates": family_review_candidates,
                "runtime_allowed": False,
            }
        )

    state_rank = {"split_blocked": 0, "review_candidate": 1, "emerging": 2, "needs_more_source": 3, "coverage_only": 4}
    species_records = sorted(
        species_records,
        key=lambda item: (
            state_rank.get(item["state"], 9),
            -len(item.get("stable_moves") or []),
            -item.get("primary_source_count", 0),
            item["species_name"],
        ),
    )
    state_counts = Counter(item["state"] for item in species_records)
    return {
        "schema_version": "p14.set_inventory_consolidation.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "input_inventory_paths": [_relpath(Path(item.get("_inventory_path", ""))) for item in inventories],
        "summary": {
            "inventory_source_count": len(inventories),
            "species_count": len(species_records),
            "split_blocked_count": state_counts.get("split_blocked", 0),
            "review_candidate_count": state_counts.get("review_candidate", 0),
            "emerging_count": state_counts.get("emerging", 0),
            "needs_more_source_count": state_counts.get("needs_more_source", 0),
            "coverage_only_count": state_counts.get("coverage_only", 0),
            "split_hypothesis_count": sum(
                len(item.get("split_hypotheses") or []) for item in species_records
            ),
            "set_family_candidate_count": sum(
                len(item.get("set_family_candidates") or []) for item in species_records
            ),
            "family_review_candidate_count": sum(
                len(item.get("family_review_candidates") or []) for item in species_records
            ),
            "primary_source_count": sum(1 for inventory in inventories if _is_primary_source(inventory)),
            "supporting_source_count": sum(1 for inventory in inventories if not _is_primary_source(inventory)),
        },
        "source_quality": {
            sid: {
                "title": (inventory.get("source") or {}).get("title"),
                "url": (inventory.get("source") or {}).get("url"),
                "source_type": _source_type(inventory),
                "low_confidence_use": _low_confidence_use(inventory),
                "primary_for_consolidation": _is_primary_source(inventory),
            }
            for sid, inventory in sorted(source_lookup.items())
        },
        "species_records": species_records,
    }


def render_pm_brief(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    records = payload.get("species_records") or []
    split_blocked = [item for item in records if item["state"] == "split_blocked"]
    review_candidates = [item for item in records if item["state"] == "review_candidate"]
    emerging = [item for item in records if item["state"] == "emerging"]
    needs_more = [item for item in records if item["state"] == "needs_more_source"]
    family_review_candidates = [
        (item, family)
        for item in records
        for family in (item.get("family_review_candidates") or [])
    ]

    lines = [
        f"# Phase 1 Set Inventory Consolidation: {payload['batch_id']}",
        "",
        "## 结论",
        "- 这一步只观察跨源重复，不做 promotion。",
        f"- 输入 {summary['inventory_source_count']} 个 inventory 源；源越多，重复技能骨架会自然往上浮。",
        f"- 当前没有可直接进 runtime 的 set；split_blocked {summary.get('split_blocked_count', 0)} 个，review_candidate {summary['review_candidate_count']} 个，emerging {summary['emerging_count']} 个，needs_more_source {summary['needs_more_source_count']} 个。",
        f"- set_family candidates {summary.get('set_family_candidate_count', 0)} 个；family_review_candidate {summary.get('family_review_candidate_count', 0)} 个；split_hypothesis {summary.get('split_hypothesis_count', 0)} 个。",
        "",
        "## 已经浮出来的信号",
    ]
    candidates_to_show = [*split_blocked, *review_candidates, *emerging][:8]
    if candidates_to_show:
        for item in candidates_to_show:
            stable = " / ".join(item.get("stable_moves") or []) or "暂无重复技能"
            variants = []
            for variant in (item.get("dossier_variants") or [])[:3]:
                moves = " / ".join(variant.get("moves") or []) or "无技能"
                suffix = "；低置信补证" if variant.get("low_confidence_use") else ""
                variants.append(f"{variant['source_id']}={moves}{suffix}")
            family_summary = item.get("set_family_summary") or {}
            family_note = ""
            if family_summary.get("split_hypothesis_count"):
                family_note = f"；疑似流派分叉 {family_summary['split_hypothesis_count']} 个"
            lines.append(
                f"- {item['species_name']}：{item['state']}；稳定技能 {stable}；主证 {item['primary_source_count']} 条，补证 {item['supporting_source_count']} 条{family_note}；{'; '.join(variants)}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(["", "## 可先做 family-level review 的 set"])
    if family_review_candidates:
        for species_record, family in family_review_candidates[:8]:
            core = " / ".join(family.get("core_moves") or []) or "核心未重复"
            flex = " / ".join(family.get("flex_moves") or []) or "无"
            axes = "/".join(family.get("damage_axes") or family.get("build_axes") or []) or "轴未知"
            source_ids = ", ".join(family.get("primary_source_ids") or [])
            cooccurrence_count = family.get("core_cooccurrence_primary_source_count", 0)
            species_note = "；物种级仍 split_blocked" if species_record.get("split_hypotheses") else ""
            lines.append(
                f"- {species_record['species_name']} {family['family_id']}：core={core}；flex={flex}；axis={axes}；主证 {family['primary_source_count']} 条，核心共现源 {cooccurrence_count} 条（{source_ids}）{species_note}。"
            )
    else:
        lines.append("- 暂无。")

    split_records = [item for item in records if item.get("split_hypotheses")]
    lines.extend(["", "## 同物种 set family / alter 判断"])
    if split_records:
        for item in split_records[:5]:
            family_bits = []
            for family in (item.get("set_family_candidates") or [])[:4]:
                core = " / ".join(family.get("core_moves") or []) or "核心未重复"
                flex = " / ".join(family.get("flex_moves") or []) or "无"
                axes = "/".join(family.get("damage_axes") or family.get("build_axes") or []) or "轴未知"
                family_bits.append(f"{family['family_id']} core={core}, flex={flex}, axis={axes}")
            reasons = sorted({reason for split in item.get("split_hypotheses") or [] for reason in split.get("reason_codes") or []})
            lines.append(
                f"- {item['species_name']}：先按 split_hypothesis 处理，不拆正式卡；原因 {', '.join(reasons)}；{'; '.join(family_bits)}。"
            )
    else:
        lines.append("- 当前没有足够证据证明同物种需要拆成独立 set；技能差异先保留为 alter variants。")

    lines.extend(["", "## 还缺什么"])
    if needs_more:
        for item in needs_more[:6]:
            moves = []
            for move in item.get("observed_moves") or []:
                moves.append(f"{move['move_name']}({move['source_count']})")
            lines.append(
                f"- {item['species_name']}：{', '.join(moves) or '无技能'}；动作：{item['suggested_next_action']}。"
            )
    else:
        lines.append("- 暂无单源弱信号。")

    wingking = next((item for item in records if item.get("species_name") == "圣羽翼王"), None)
    next_lines = [
        "",
        "## 对下一步的影响",
        "- 如果某个物种主证 >=3 但 stable_moves <2，说明同物种多流派或字幕粒度已经分叉，继续补源时要按流派分簇，不要合成一张卡。",
    ]
    if wingking and wingking.get("primary_source_count", 0) >= 3:
        next_lines.append("- 当前 `圣羽翼王` 已经证明会分叉：水刃线和魔攻/回旋风暴线不能直接合并。")
    next_lines.extend(
        [
            "- 下一批要么补同流派证据，例如水刃翼王或魔攻翼王；要么扩大到水毒、星陨帕尔、沙暴/格斗主证源。",
            "- reviewer packet 可以按 set family 生成；物种级卡必须等 split_hypothesis 解决后再做。",
        ]
    )
    lines.extend(next_lines)
    return "\n".join(lines) + "\n"


def render_family_review_packet(payload: dict[str, Any]) -> str:
    source_quality = payload.get("source_quality") or {}
    records = payload.get("species_records") or []
    candidates = [
        (record, family)
        for record in records
        for family in (record.get("family_review_candidates") or [])
    ]

    lines = [
        f"# Family-Level Set Review Packet: {payload['batch_id']}",
        "",
        "## 你需要看的结论",
        "- 这不是 runtime promotion，也不是物种级总卡。",
        "- 只审已经形成重复技能骨架的 set family；同物种其它流派继续锁住。",
    ]
    if not candidates:
        lines.append("- 当前没有 family-level review candidate。")
        return "\n".join(lines) + "\n"

    lines.append(f"- 当前可审 family：{len(candidates)} 个。")
    for index, (record, family) in enumerate(candidates, start=1):
        core = " / ".join(family.get("core_moves") or []) or "核心未重复"
        flex = " / ".join(family.get("flex_moves") or []) or "无"
        axes = "/".join(family.get("damage_axes") or family.get("build_axes") or []) or "轴未知"
        proposed_name = _family_review_proposed_name(family)
        source_lines = []
        for sid in family.get("primary_source_ids") or []:
            meta = source_quality.get(sid) or {}
            title = meta.get("title") or sid
            url = meta.get("url")
            source_lines.append(f"- {title} ({sid})" + (f": {url}" if url else ""))

        unresolved_families = [
            item
            for item in (record.get("set_family_candidates") or [])
            if item.get("family_id") != family.get("family_id")
        ]
        unresolved_bits = []
        for other in unresolved_families:
            other_moves = " / ".join(other.get("representative_moves") or other.get("flex_moves") or []) or "无技能"
            other_axes = "/".join(other.get("damage_axes") or other.get("build_axes") or []) or "轴未知"
            unresolved_bits.append(f"{other['family_id']}={other_moves} ({other_axes})")

        lines.extend(
            [
                "",
                f"## Candidate {index}: {record['species_name']} {family['family_id']}",
                f"- 建议审查范围：`{record['species_name']} - set family {family['family_id']}`，不是 `{record['species_name']}` 总卡。",
                f"- 核心技能：{core}",
                f"- 可选/旁证技能：{flex}",
                f"- 轴：{axes}",
                f"- 主证数量：{family.get('primary_source_count', 0)}",
                f"- 核心共现源：{family.get('core_cooccurrence_primary_source_count', 0)}",
                "- 主证来源：",
                *source_lines,
                "- 暂不合并的同物种其它线：" + ("；".join(unresolved_bits) if unresolved_bits else "无"),
                "",
                "### 建议给 PM 的判断题",
                f"- 是否允许这条 family 进入 reviewer ledger，名称暂定为{proposed_name}？",
                f"- 可选/旁证技能是否只作为 flex 保留，不进入核心技能：{flex}？",
                "- 暂不合并的同物种其它线是否继续保留为 blocker / 补源目标，而不是合并进这条 family？",
            ]
        )

    return "\n".join(lines) + "\n"


def _family_review_proposed_name(family: dict[str, Any]) -> str:
    core_moves = [str(item) for item in family.get("core_moves") or [] if item]
    damage_axes = set(str(item) for item in family.get("damage_axes") or [])
    if "水刃" in core_moves and "physical" in damage_axes:
        return "水刃物攻线"
    if core_moves:
        return f"{core_moves[0]}线"
    return str(family.get("family_id") or "未命名 family")


def run_set_inventory_consolidator(
    *,
    inventory_dir: Path = DEFAULT_INVENTORY_DIR,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    source_ids: set[str] | None = None,
    db_path: Path = DEFAULT_BATTLE_DEX,
) -> dict[str, Any]:
    inventories = load_inventories(inventory_dir, source_ids=source_ids)
    payload = build_consolidation(batch_id, inventories, move_metadata=load_move_metadata(db_path))
    consolidation_path = out_root / CONSOLIDATION_DIRNAME / f"{batch_id}.yaml"
    brief_path = out_root / "review_packets" / f"{batch_id}_pm_brief.md"
    family_review_path = out_root / "review_packets" / f"{batch_id}_family_review.md"
    _write_yaml(consolidation_path, payload)
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(render_pm_brief(payload), encoding="utf-8")
    family_review_path.write_text(render_family_review_packet(payload), encoding="utf-8")
    return {
        "batch_id": batch_id,
        "runtime_allowed": False,
        "source_count": len(inventories),
        "paths": {
            "consolidation": _relpath(consolidation_path),
            "pm_brief": _relpath(brief_path),
            "family_review": _relpath(family_review_path),
        },
        "summary": payload["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_set_inventory_consolidator(
        inventory_dir=args.inventory_dir,
        out_root=args.out_root,
        batch_id=args.batch_id,
        source_ids=set(args.source_id) if args.source_id else None,
        db_path=args.db_path,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"set inventory consolidation: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
