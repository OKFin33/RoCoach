#!/usr/bin/env python3
"""Bind P14 form identity and overwide alter-set axes before PM review.

This is control-plane substrate only. It reads Set Inventory consolidation,
A-layer Battle Dex form/move data, and reviewer identity policies. It does not
update source_queue, A-layer SQLite, graph cards, review ledgers, or runtime data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_axis_identity_audit import (
    DEFAULT_BATTLE_DEX,
    DEFAULT_REVIEWER_LEDGER,
    _identity_policies_from_reviewer_ledger,
    _species_options_index,
)
from tools.p14_recluster_split_blockers import _latest_consolidation_from_queue
from tools.p14_set_pipeline import DEFAULT_OUT_ROOT, DEFAULT_SOURCE_QUEUE, NoAliasDumper, REPO_ROOT, _relpath


DEFAULT_BATCH_ID = f"phase1_identity_axis_binding_{date.today().isoformat()}"
IDENTITY_AXIS_DIRNAME = "identity_axis_binding"
DEFAULT_TARGET_SPECIES = ["卡瓦重", "化蝶", "寂灭骨龙"]
MIN_PAIR_SOURCE_COUNT = 3
MIN_BRANCH_SOURCE_COUNT = 2
MIN_AXIS_BRANCH_SOURCE_COUNT = 2
MAX_PIVOTS_PER_FAMILY = 6

AXIS_BRANCH_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "寂灭骨龙": [
        {
            "axis_id": "bulk_defensive_vs_physical_pressure",
            "axis_label": "联防生命/坦度流 vs 压制输出/物攻流",
            "branch_count_required": 2,
            "branches": [
                {
                    "branch_id": "bulk_defensive",
                    "label": "联防生命/坦度流",
                    "match_terms": ["联防", "生命", "坦度", "平和", "消耗", "满生命", "双生命"],
                    "build_axes": ["bulk"],
                    "roles": ["defensive_pivot"],
                    "candidate_moves": ["吓退", "报复", "先发制人"],
                },
                {
                    "branch_id": "physical_pressure",
                    "label": "压制输出/物攻流",
                    "match_terms": ["压制输出", "物攻", "高物攻", "固执", "满攻击", "输出"],
                    "build_axes": ["physical"],
                    "roles": ["pressure", "lead"],
                    "candidate_moves": ["偷袭", "电弧", "先发制人"],
                },
            ],
        }
    ]
}


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _variant_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in record.get("set_family_candidates") or []:
        for variant in family.get("alter_variants") or []:
            rows.append({**variant, "family_id": family.get("family_id")})
    return rows


def _form_terms(option: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for raw in (option.get("regional_form_name"), option.get("form_name")):
        value = str(raw or "").strip()
        if not value:
            continue
        terms.add(value)
        cleaned = (
            value.replace("附近的样子", "")
            .replace("的样子", "")
            .replace("形态", "")
            .replace("地区", "")
            .replace("原始", "")
            .strip()
        )
        if len(cleaned) >= 2:
            terms.add(cleaned)
    return {term for term in terms if term}


def _title_form_matches(title: str, species_options: list[dict[str, Any]]) -> list[str]:
    matches: list[str] = []
    for option in species_options:
        if any(term and term in title for term in _form_terms(option)):
            matches.append(str(option.get("species_id")))
    return sorted(set(matches))


def _best_coverage(
    moves: set[str],
    species_options: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for option in species_options:
        available = set(option.get("available_moves") or [])
        covered = sorted(moves & available)
        missing = sorted(moves - available)
        rows.append(
            {
                "species_id": option.get("species_id"),
                "form_name": option.get("form_name"),
                "regional_form_name": option.get("regional_form_name"),
                "covered_move_count": len(covered),
                "missing_move_count": len(missing),
                "missing_moves": missing,
            }
        )
    full_legal = sorted(str(row["species_id"]) for row in rows if row["missing_move_count"] == 0)
    if not rows:
        return full_legal, rows
    best_score = max((row["covered_move_count"], -row["missing_move_count"]) for row in rows)
    best_rows = [
        row
        for row in rows
        if (row["covered_move_count"], -row["missing_move_count"]) == best_score
    ]
    return full_legal, best_rows


def _form_status(
    *,
    policy_name: str,
    full_legal_species_ids: list[str],
    title_form_matches: list[str],
    best_coverage_options: list[dict[str, Any]],
) -> str:
    if policy_name == "do_not_assume_battle_distinct_forms_without_source_evidence":
        return "form_not_split_without_source_backed_battle_difference"
    if len(full_legal_species_ids) == 1:
        if title_form_matches == full_legal_species_ids:
            return "form_bound_by_title_and_move_legality"
        return "form_bound_by_move_legality"
    if len(full_legal_species_ids) > 1:
        return "form_ambiguous_multiple_legal_forms"
    if len(title_form_matches) == 1:
        return "title_clue_with_move_legality_gap"
    if len(best_coverage_options) == 1:
        return "partial_form_hint_needs_a_layer_move_check"
    return "unresolved_form_binding"


def _build_form_report(
    *,
    record: dict[str, Any],
    species_options: list[dict[str, Any]],
    pm_identity_policy: dict[str, Any] | None,
    source_quality: dict[str, Any],
) -> dict[str, Any] | None:
    policy = pm_identity_policy or {}
    policy_name = str(policy.get("policy") or "")
    if not policy_name and len(species_options) <= 1:
        return None

    species_name = str(record.get("species_name") or "")
    rows: list[dict[str, Any]] = []
    for variant in _variant_rows(record):
        moves = {str(move) for move in variant.get("moves") or [] if move}
        if not moves:
            continue
        source_id = str(variant.get("source_id") or "")
        title = str((source_quality.get(source_id) or {}).get("title") or "")
        full_legal, best_options = _best_coverage(moves, species_options)
        title_matches = _title_form_matches(title, species_options)
        status = _form_status(
            policy_name=policy_name,
            full_legal_species_ids=full_legal,
            title_form_matches=title_matches,
            best_coverage_options=best_options,
        )
        rows.append(
            {
                "source_id": source_id,
                "family_id": variant.get("family_id"),
                "title": title,
                "moves": sorted(moves),
                "form_binding_status": status,
                "full_legal_species_ids": full_legal,
                "title_form_match_species_ids": title_matches,
                "best_coverage_options": best_options,
            }
        )

    status_counts = Counter(str(row.get("form_binding_status")) for row in rows)
    concrete_bound_rows = [
        row
        for row in rows
        if row.get("form_binding_status") in {"form_bound_by_move_legality", "form_bound_by_title_and_move_legality"}
    ]
    unresolved_rows = [
        row
        for row in rows
        if row.get("form_binding_status") in {
            "unresolved_form_binding",
            "form_ambiguous_multiple_legal_forms",
            "partial_form_hint_needs_a_layer_move_check",
            "title_clue_with_move_legality_gap",
        }
    ]
    form_counts: Counter[str] = Counter()
    option_by_id = {str(option.get("species_id")): option for option in species_options}
    for row in concrete_bound_rows:
        for species_id in row.get("full_legal_species_ids") or []:
            option = option_by_id.get(str(species_id)) or {}
            form_counts.update([str(option.get("regional_form_name") or species_id)])

    if policy_name == "require_form_resolution_before_set_review":
        next_action = "resolve_unbound_sources_or_keep_them_out_of_pm_review"
        report_status = "distinct_form_binding_required"
    elif policy_name == "do_not_assume_battle_distinct_forms_without_source_evidence":
        next_action = "cluster_by_build_mechanism_or_role_not_by_form"
        report_status = "form_split_not_assumed"
    else:
        next_action = "use_as_identity_context_only"
        report_status = "identity_context"

    return {
        "species_name": species_name,
        "report_status": report_status,
        "pm_identity_policy": policy,
        "candidate_form_count": len(species_options),
        "source_variant_count": len(rows),
        "form_binding_status_counts": dict(status_counts),
        "concrete_form_bound_source_count": len(concrete_bound_rows),
        "unresolved_form_source_count": len(unresolved_rows),
        "concrete_form_counts": dict(form_counts),
        "source_bindings": rows,
        "recommended_action": next_action,
        "runtime_allowed": False,
    }


def _axis_terms(variant: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    damage_axis = str(variant.get("damage_axis") or "")
    if damage_axis and damage_axis not in {"unknown", "status_or_unknown"}:
        terms.append(f"damage:{damage_axis}")
    terms.extend(f"build:{axis}" for axis in variant.get("build_axes") or [] if axis)
    terms.extend(f"role:{role}" for role in variant.get("roles") or [] if role)
    config = variant.get("configuration") or {}
    for field in ("nature", "individual_values", "bloodline", "ability_mentions", "mechanism_mentions"):
        if config.get(field):
            terms.append(f"config:{field}")
    return sorted(set(terms))


def _variant_text(variant: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(str(move) for move in variant.get("moves") or [] if move)
    parts.extend(str(axis) for axis in variant.get("build_axes") or [] if axis)
    parts.extend(str(role) for role in variant.get("roles") or [] if role)
    config = variant.get("configuration") or {}
    for value in config.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    evidence = item.get("evidence") or {}
                    parts.append(str(item.get("source_phrase") or ""))
                    parts.append(str(evidence.get("quote") or ""))
                else:
                    parts.append(str(item or ""))
        elif value:
            parts.append(str(value))
    return " ".join(part for part in parts if part)


def _variant_quotes(variant: dict[str, Any], terms: list[str], *, limit: int = 2) -> list[str]:
    quotes: list[str] = []
    config = variant.get("configuration") or {}
    for value in config.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            quote = str((item.get("evidence") or {}).get("quote") or "").strip()
            if not quote:
                continue
            if terms and not any(term in quote for term in terms):
                continue
            if quote not in quotes:
                quotes.append(quote)
            if len(quotes) >= limit:
                return quotes
    return quotes


def _branch_assignment(variant: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any] | None:
    moves = {str(move) for move in variant.get("moves") or [] if move}
    candidate_moves = {str(move) for move in branch.get("candidate_moves") or [] if move}
    move_overlap = sorted(moves & candidate_moves)
    if not move_overlap:
        return None

    text = _variant_text(variant)
    matched_terms = [str(term) for term in branch.get("match_terms") or [] if str(term) in text]
    matched_build_axes = sorted(
        set(str(axis) for axis in variant.get("build_axes") or [])
        & set(str(axis) for axis in branch.get("build_axes") or [])
    )
    matched_roles = sorted(
        set(str(role) for role in variant.get("roles") or [])
        & set(str(role) for role in branch.get("roles") or [])
    )
    if not (matched_terms or matched_build_axes):
        return None

    source_id = str(variant.get("source_id") or "")
    return {
        "source_id": source_id,
        "family_id": variant.get("family_id"),
        "moves": sorted(moves),
        "move_overlap": move_overlap,
        "matched_terms": matched_terms,
        "matched_build_axes": matched_build_axes,
        "matched_roles": matched_roles,
        "confidence": "strong_quote_signal" if matched_terms else "medium_structured_axis_signal",
        "evidence_quotes": _variant_quotes(variant, matched_terms),
    }


def _branch_signal_terms(counter: Counter[str]) -> set[str]:
    return {
        term
        for term, count in counter.items()
        if count >= MIN_BRANCH_SOURCE_COUNT and not term.startswith("damage:")
    }


def _pair_pivots(family: dict[str, Any]) -> list[dict[str, Any]]:
    pair_sources: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for variant in family.get("alter_variants") or []:
        if variant.get("low_confidence_use"):
            continue
        moves = sorted({str(move) for move in variant.get("moves") or [] if move})
        for left_index, left in enumerate(moves):
            for right in moves[left_index + 1 :]:
                pair_sources[(left, right)].append(variant)

    pivots: list[dict[str, Any]] = []
    for pair, variants in pair_sources.items():
        source_ids = sorted({str(variant.get("source_id")) for variant in variants if variant.get("source_id")})
        if len(source_ids) < MIN_PAIR_SOURCE_COUNT:
            continue
        flex_counts: Counter[str] = Counter()
        axis_counts: Counter[str] = Counter()
        branch_axis_counts: dict[str, Counter[str]] = defaultdict(Counter)
        branch_source_ids: dict[str, set[str]] = defaultdict(set)
        for variant in variants:
            terms = _axis_terms(variant)
            axis_counts.update(terms)
            source_id = str(variant.get("source_id") or "")
            for move in variant.get("moves") or []:
                move = str(move)
                if move in pair:
                    continue
                flex_counts[move] += 1
                branch_axis_counts[move].update(terms)
                if source_id:
                    branch_source_ids[move].add(source_id)

        branches = [
            {
                "flex_move": move,
                "source_count": len(branch_source_ids.get(move) or set()),
                "axis_terms": dict(branch_axis_counts[move].most_common(10)),
            }
            for move, count in flex_counts.most_common(6)
            if count >= MIN_BRANCH_SOURCE_COUNT
        ]
        meaningful_branch_terms = [_branch_signal_terms(Counter(branch.get("axis_terms") or {})) for branch in branches]
        divergent = False
        if len(meaningful_branch_terms) >= 2:
            nonempty = [terms for terms in meaningful_branch_terms if terms]
            divergent = bool(nonempty) and any(terms != nonempty[0] for terms in nonempty[1:])

        if len(branches) >= 2 and divergent:
            status = "shared_core_axis_candidate"
            action = "bind shared core flex branches to role/build/config axis before PM review"
        elif len(branches) >= 2:
            status = "shared_core_likely_flex_variants"
            action = "treat as alter-variant flex unless source spans name distinct roles"
        else:
            status = "common_pair_needs_more_branch_evidence"
            action = "collect or inspect focused sources before splitting"

        pivots.append(
            {
                "shared_core_moves": list(pair),
                "source_count": len(source_ids),
                "source_ids": source_ids,
                "flex_move_counts": dict(flex_counts.most_common(8)),
                "axis_terms": dict(axis_counts.most_common(12)),
                "branches": branches,
                "pivot_status": status,
                "recommended_action": action,
            }
        )

    return sorted(
        pivots,
        key=lambda item: (
            item["pivot_status"] != "shared_core_axis_candidate",
            -item["source_count"],
            item["shared_core_moves"],
        ),
    )[:MAX_PIVOTS_PER_FAMILY]


def _compact_family_candidates(family: dict[str, Any]) -> list[dict[str, Any]]:
    core_moves = list(family.get("core_moves") or [])
    if not (2 <= len(core_moves) <= 4):
        return []
    if int(family.get("primary_source_count") or 0) < MIN_PAIR_SOURCE_COUNT:
        return []
    return [
        {
            "family_id": family.get("family_id"),
            "core_moves": core_moves,
            "flex_moves": list(family.get("flex_moves") or [])[:6],
            "primary_source_count": family.get("primary_source_count"),
            "damage_axes": list(family.get("damage_axes") or []),
            "build_axes": list(family.get("build_axes") or []),
            "status": "compact_family_candidate_needs_identity_or_span_check",
        }
    ]


def _axis_branch_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    species_name = str(record.get("species_name") or "")
    patterns = AXIS_BRANCH_PATTERNS.get(species_name) or []
    if not patterns:
        return []

    variants = _variant_rows(record)
    candidates: list[dict[str, Any]] = []
    for pattern in patterns:
        branch_reports: list[dict[str, Any]] = []
        for branch in pattern.get("branches") or []:
            assignments = [
                assignment
                for variant in variants
                if (assignment := _branch_assignment(variant, branch))
            ]
            source_ids = sorted(
                {str(assignment.get("source_id")) for assignment in assignments if assignment.get("source_id")}
            )
            strong_source_ids = sorted(
                {
                    str(assignment.get("source_id"))
                    for assignment in assignments
                    if assignment.get("source_id")
                    and assignment.get("confidence") == "strong_quote_signal"
                }
            )
            status = (
                "branch_supported"
                if len(source_ids) >= MIN_AXIS_BRANCH_SOURCE_COUNT
                and len(strong_source_ids) >= MIN_AXIS_BRANCH_SOURCE_COUNT
                else "branch_needs_more_source_support"
            )
            assignments = sorted(
                assignments,
                key=lambda item: (
                    item.get("confidence") != "strong_quote_signal",
                    str(item.get("source_id") or ""),
                ),
            )
            branch_reports.append(
                {
                    "branch_id": branch.get("branch_id"),
                    "label": branch.get("label"),
                    "source_count": len(source_ids),
                    "source_ids": source_ids,
                    "strong_source_count": len(strong_source_ids),
                    "strong_source_ids": strong_source_ids,
                    "candidate_moves": list(branch.get("candidate_moves") or []),
                    "matched_assignments": assignments[:8],
                    "status": status,
                }
            )

        supported_branches = [
            branch for branch in branch_reports if branch.get("status") == "branch_supported"
        ]
        required = int(pattern.get("branch_count_required") or 2)
        if len(supported_branches) >= required:
            status = "candidate_for_pm_axis_branch_review"
            action = "ask PM to accept axis boundary before any family card promotion"
        else:
            status = "axis_branch_needs_more_source_span_support"
            action = "collect focused sources or improve branch assignment before PM review"

        candidates.append(
            {
                "axis_id": pattern.get("axis_id"),
                "axis_label": pattern.get("axis_label"),
                "status": status,
                "supported_branch_count": len(supported_branches),
                "required_branch_count": required,
                "branches": branch_reports,
                "recommended_action": action,
            }
        )

    return candidates


def _build_axis_report(record: dict[str, Any]) -> dict[str, Any] | None:
    family_reports: list[dict[str, Any]] = []
    for family in record.get("set_family_candidates") or []:
        pivots = _pair_pivots(family)
        compact = _compact_family_candidates(family)
        if not pivots and not compact:
            continue
        family_reports.append(
            {
                "family_id": family.get("family_id"),
                "core_move_count": len(family.get("core_moves") or []),
                "primary_source_count": family.get("primary_source_count"),
                "pair_pivots": pivots,
                "compact_family_candidates": compact,
            }
        )
    branch_candidates = _axis_branch_candidates(record)
    if not family_reports and not branch_candidates:
        return None
    axis_candidate_count = sum(
        1
        for family in family_reports
        for pivot in family.get("pair_pivots") or []
        if pivot.get("pivot_status") == "shared_core_axis_candidate"
    )
    axis_branch_candidate_count = sum(
        1
        for candidate in branch_candidates
        if candidate.get("status") == "candidate_for_pm_axis_branch_review"
    )
    return {
        "species_name": record.get("species_name"),
        "axis_report_status": (
            "axis_branch_pm_review_gate"
            if axis_branch_candidate_count
            else "axis_binding_candidates_present"
            if axis_candidate_count
            else "axis_context_only"
        ),
        "family_reports": family_reports,
        "axis_branch_candidates": branch_candidates,
        "axis_candidate_count": axis_candidate_count,
        "axis_branch_candidate_count": axis_branch_candidate_count,
        "recommended_action": (
            "build PM axis-branch review packet before any set-card promotion"
            if axis_branch_candidate_count
            else
            "bind shared-core branches before PM review"
            if axis_candidate_count
            else "keep as context until more axis evidence appears"
        ),
        "runtime_allowed": False,
    }


def build_identity_axis_binding(
    *,
    batch_id: str,
    consolidation: dict[str, Any],
    species_options_index: dict[str, list[dict[str, Any]]],
    pm_identity_policies: dict[str, dict[str, Any]],
    target_species: list[str] | None = None,
) -> dict[str, Any]:
    source_quality = consolidation.get("source_quality") or {}
    target_set = set(target_species or DEFAULT_TARGET_SPECIES)
    if target_species is None:
        target_set.update(pm_identity_policies.keys())

    form_reports: list[dict[str, Any]] = []
    axis_reports: list[dict[str, Any]] = []
    for record in consolidation.get("species_records") or []:
        species_name = str(record.get("species_name") or "")
        if target_set and species_name not in target_set:
            continue
        form_report = _build_form_report(
            record=record,
            species_options=species_options_index.get(species_name) or [],
            pm_identity_policy=pm_identity_policies.get(species_name),
            source_quality=source_quality,
        )
        if form_report:
            form_reports.append(form_report)
        axis_report = _build_axis_report(record)
        if axis_report:
            axis_reports.append(axis_report)

    distinct_form_unresolved = sum(
        int(report.get("unresolved_form_source_count") or 0)
        for report in form_reports
        if (report.get("pm_identity_policy") or {}).get("policy") == "require_form_resolution_before_set_review"
    )
    axis_candidate_count = sum(int(report.get("axis_candidate_count") or 0) for report in axis_reports)
    axis_branch_candidate_count = sum(
        int(report.get("axis_branch_candidate_count") or 0) for report in axis_reports
    )
    if distinct_form_unresolved:
        next_action = "resolve_form_binding_before_pm_review"
    elif axis_branch_candidate_count:
        next_action = "build_pm_axis_branch_review_packet"
    elif axis_candidate_count:
        next_action = "bind_shared_core_flex_axes_before_pm_review"
    else:
        next_action = "continue_targeted_source_or_span_inspection"

    return {
        "schema_version": "p14.identity_axis_binding.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source_consolidation_batch_id": consolidation.get("batch_id"),
        "policy": {
            "promotion_forbidden": True,
            "source_queue_updates": False,
            "a_layer_mutation": False,
            "graph_materialization": False,
            "target_species": sorted(target_set),
            "min_pair_source_count": MIN_PAIR_SOURCE_COUNT,
            "min_branch_source_count": MIN_BRANCH_SOURCE_COUNT,
            "min_axis_branch_source_count": MIN_AXIS_BRANCH_SOURCE_COUNT,
        },
        "summary": {
            "form_report_count": len(form_reports),
            "distinct_form_unresolved_source_count": distinct_form_unresolved,
            "axis_report_count": len(axis_reports),
            "axis_candidate_count": axis_candidate_count,
            "axis_branch_candidate_count": axis_branch_candidate_count,
            "recommended_next_action": next_action,
        },
        "form_reports": form_reports,
        "axis_reports": axis_reports,
    }


def render_identity_axis_brief(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        f"# P14 Identity / Axis Binding: {payload['batch_id']}",
        "",
        "## 结论",
        "- 这是身份/形态绑定与 alter-set 轴绑定审计，不是 promotion，也不会写 graph/runtime。",
        f"- 形态/身份报告 {summary.get('form_report_count', 0)} 个；确认 distinct-form 但仍未绑定的 source variant {summary.get('distinct_form_unresolved_source_count', 0)} 个。",
        f"- 战术轴报告 {summary.get('axis_report_count', 0)} 个；shared-core 轴候选 {summary.get('axis_candidate_count', 0)} 个；axis_branch PM gate {summary.get('axis_branch_candidate_count', 0)} 个。",
        f"- 下一动作：`{summary.get('recommended_next_action')}`。",
        "",
        "## 形态绑定",
    ]
    form_reports = payload.get("form_reports") or []
    if not form_reports:
        lines.append("- 暂无。")
    for report in form_reports:
        policy = report.get("pm_identity_policy") or {}
        counts = ", ".join(f"{k}={v}" for k, v in (report.get("form_binding_status_counts") or {}).items())
        form_counts = ", ".join(f"{k}={v}" for k, v in (report.get("concrete_form_counts") or {}).items()) or "暂无"
        lines.append(
            f"- {report['species_name']}：{report['report_status']}；PM规则={policy.get('policy') or '无'}；状态计数 {counts or '暂无'}；已绑定形态 {form_counts}；动作 {report['recommended_action']}。"
        )
        shown = 0
        for row in report.get("source_bindings") or []:
            if row.get("form_binding_status") in {
                "unresolved_form_binding",
                "form_ambiguous_multiple_legal_forms",
                "partial_form_hint_needs_a_layer_move_check",
                "title_clue_with_move_legality_gap",
            } or shown < 3:
                best = [
                    str(option.get("regional_form_name") or option.get("species_id"))
                    for option in row.get("best_coverage_options") or []
                ]
                lines.append(
                    f"  - {row['source_id']}：{row['form_binding_status']}；moves={' / '.join(row.get('moves') or [])}；best={', '.join(best) or '无'}。"
                )
                shown += 1
            if shown >= 6:
                break

    lines.extend(["", "## 轴绑定"])
    axis_reports = payload.get("axis_reports") or []
    if not axis_reports:
        lines.append("- 暂无。")
    for report in axis_reports:
        lines.append(
            f"- {report['species_name']}：{report['axis_report_status']}；动作 {report['recommended_action']}。"
        )
        for candidate in report.get("axis_branch_candidates") or []:
            lines.append(
                f"  - axis_branch={candidate.get('axis_id')}；{candidate.get('axis_label')}；状态 {candidate.get('status')}；支持分支 {candidate.get('supported_branch_count')}/{candidate.get('required_branch_count')}。"
            )
            for branch in candidate.get("branches") or []:
                preferred_sources = branch.get("strong_source_ids") or branch.get("source_ids") or []
                source_ids = ", ".join(preferred_sources[:6]) or "无"
                if len(preferred_sources) > 6:
                    source_ids += f", ...(+{len(preferred_sources) - 6})"
                moves = " / ".join(branch.get("candidate_moves") or [])
                lines.append(
                    f"    - {branch.get('branch_id')}：sources={branch.get('source_count')}；strong={branch.get('strong_source_count')}；moves={moves}；状态 {branch.get('status')}；strong_source_ids={source_ids}。"
                )
                sample = (branch.get("matched_assignments") or [{}])[0]
                quotes = sample.get("evidence_quotes") or []
                if quotes:
                    lines.append(f"      - 例证：{quotes[0]}")
        shown = 0
        for family in report.get("family_reports") or []:
            for pivot in family.get("pair_pivots") or []:
                if pivot.get("pivot_status") != "shared_core_axis_candidate" and shown >= 2:
                    continue
                flex = ", ".join(f"{k}={v}" for k, v in (pivot.get("flex_move_counts") or {}).items())
                lines.append(
                    f"  - {family['family_id']} shared_core={' / '.join(pivot.get('shared_core_moves') or [])}；sources={pivot.get('source_count')}；flex={flex}；状态 {pivot['pivot_status']}。"
                )
                shown += 1
            for compact in family.get("compact_family_candidates") or []:
                if shown >= 4:
                    continue
                lines.append(
                    f"  - {family['family_id']} compact_core={' / '.join(compact.get('core_moves') or [])}；sources={compact.get('primary_source_count')}；状态 {compact['status']}。"
                )
                shown += 1
            if shown >= 4:
                break

    lines.extend(
        [
            "",
            "## 边界",
            "- 卡瓦重这类 PM-confirmed distinct forms 不能把未绑定来源混进 set review。",
            "- 化蝶这类 form 差异不确定的 species 不按形态硬拆；先看技能、血脉、性格、机制和角色轴。",
            "- shared-core + flex 分支只是轴候选，不等于独立 set；必须补 source span 或角色/培养差异。",
            "- axis_branch 只是“同一 family 的构筑分支”候选；PM 接受轴边界以后，仍不能直接 runtime promotion。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_identity_axis_binding(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    consolidation_path: Path | None = None,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    battle_dex: Path = DEFAULT_BATTLE_DEX,
    reviewer_ledger: Path = DEFAULT_REVIEWER_LEDGER,
    target_species: list[str] | None = None,
) -> dict[str, Any]:
    consolidation_path = consolidation_path or _latest_consolidation_from_queue(source_queue)
    consolidation = _load_yaml(consolidation_path)
    reviewer_state = _load_yaml(reviewer_ledger)
    payload = build_identity_axis_binding(
        batch_id=batch_id,
        consolidation=consolidation,
        species_options_index=_species_options_index(battle_dex),
        pm_identity_policies=_identity_policies_from_reviewer_ledger(reviewer_state),
        target_species=target_species,
    )
    payload["input"] = {
        "consolidation_path": _relpath(consolidation_path),
        "battle_dex": _relpath(battle_dex),
        "reviewer_ledger": _relpath(reviewer_ledger),
    }
    out_path = out_root / IDENTITY_AXIS_DIRNAME / f"{batch_id}.yaml"
    brief_path = out_root / "review_packets" / f"{batch_id}_identity_axis_binding.md"
    _write_yaml(out_path, payload)
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(render_identity_axis_brief(payload), encoding="utf-8")
    return {
        "runtime_allowed": False,
        "paths": {"audit": _relpath(out_path), "pm_brief": _relpath(brief_path)},
        "summary": payload["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-queue", type=Path, default=DEFAULT_SOURCE_QUEUE)
    parser.add_argument("--consolidation-path", type=Path)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--battle-dex", type=Path, default=DEFAULT_BATTLE_DEX)
    parser.add_argument("--reviewer-ledger", type=Path, default=DEFAULT_REVIEWER_LEDGER)
    parser.add_argument("--species", action="append", dest="target_species")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_identity_axis_binding(
        source_queue=args.source_queue,
        consolidation_path=args.consolidation_path,
        out_root=args.out_root,
        batch_id=args.batch_id,
        battle_dex=args.battle_dex,
        reviewer_ledger=args.reviewer_ledger,
        target_species=args.target_species,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {result['paths']['pm_brief']}")


if __name__ == "__main__":
    main()
