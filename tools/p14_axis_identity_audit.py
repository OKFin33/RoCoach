#!/usr/bin/env python3
"""Audit P14 split blockers for A-layer identity and alter-set axis blockers.

This is control-plane substrate only. It does not update source_queue, review
ledgers, graph cards, or runtime data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.p14_set_pipeline import DEFAULT_OUT_ROOT, DEFAULT_SOURCE_QUEUE, NoAliasDumper, REPO_ROOT, _relpath
from tools.p14_recluster_split_blockers import _latest_consolidation_from_queue


DEFAULT_BATCH_ID = f"phase1_axis_identity_audit_{date.today().isoformat()}"
DEFAULT_BATTLE_DEX = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
DEFAULT_REVIEWER_LEDGER = REPO_ROOT / "data" / "knowledge_graph" / "v0" / "review_state" / "reviewer_ledger.yaml"
AXIS_DIRNAME = "axis_resolution"
MIN_AXIS_SIGNAL_VARIANTS = 3
OVERWIDE_CORE_SIZE = 6


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


def _repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _identity_policies_from_reviewer_ledger(reviewer_ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = reviewer_ledger.get("pm_decisions") or {}
    policies = decisions.get("identity_resolution") or {}
    if not isinstance(policies, dict):
        return {}
    return {
        str(species_name): dict(policy)
        for species_name, policy in policies.items()
        if isinstance(policy, dict)
    }


def _species_options_index(battle_dex: Path) -> dict[str, list[dict[str, Any]]]:
    if not battle_dex.exists():
        return {}
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(battle_dex)
        conn.row_factory = sqlite3.Row
        species_rows = conn.execute(
            """
            SELECT species_id, display_name, initial_species_name, form_name,
                   regional_form_name, evolution_stage, primary_type,
                   secondary_type, ability_name, confidence, source_page_id
            FROM species_form
            """
        ).fetchall()
        move_rows = conn.execute(
            """
            SELECT species_id, move_name
            FROM species_available_moves
            WHERE move_name IS NOT NULL AND move_name != ''
            """
        ).fetchall()
    except sqlite3.Error:
        return {}
    finally:
        if conn is not None:
            conn.close()

    moves_by_species: dict[str, set[str]] = {}
    for row in move_rows:
        moves_by_species.setdefault(str(row["species_id"]), set()).add(str(row["move_name"]))

    index: dict[str, list[dict[str, Any]]] = {}
    for row in species_rows:
        species_id = str(row["species_id"])
        display_name = str(row["display_name"])
        index.setdefault(display_name, []).append(
            {
                "species_id": species_id,
                "display_name": display_name,
                "initial_species_name": row["initial_species_name"],
                "form_name": row["form_name"],
                "regional_form_name": row["regional_form_name"],
                "evolution_stage": row["evolution_stage"],
                "primary_type": row["primary_type"],
                "secondary_type": row["secondary_type"],
                "ability_name": row["ability_name"],
                "confidence": row["confidence"],
                "source_page_id": row["source_page_id"],
                "available_moves": sorted(moves_by_species.get(species_id, set())),
            }
        )
    return index


def _observed_moves(record: dict[str, Any]) -> list[str]:
    moves: set[str] = {str(move) for move in record.get("stable_moves") or [] if move}
    for family in record.get("set_family_candidates") or []:
        moves.update(str(move) for move in family.get("core_moves") or [] if move)
        for variant in family.get("alter_variants") or []:
            moves.update(str(move) for move in variant.get("moves") or [] if move)
    return sorted(moves)


def _build_identity_report(
    *,
    record: dict[str, Any],
    species_options: list[dict[str, Any]],
    pm_identity_policy: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    species_name = str(record.get("species_name") or "")
    observed_moves = _observed_moves(record)
    if not species_name:
        return None

    if not species_options:
        report = {
            "species_name": species_name,
            "identity_status": "missing_a_layer_species",
            "candidate_species_count": 0,
            "observed_moves": observed_moves,
            "recommended_action": "repair A-layer species entry before graph review",
            "runtime_allowed": False,
        }
        if pm_identity_policy:
            report["pm_identity_policy"] = pm_identity_policy
        return report
    if len(species_options) == 1:
        return None

    observed_set = set(observed_moves)
    option_views: list[dict[str, Any]] = []
    coverage_sets: list[set[str]] = []
    for option in species_options:
        move_set = set(option.get("available_moves") or [])
        covered = sorted(observed_set & move_set)
        missing = sorted(observed_set - move_set)
        coverage_sets.append(set(covered))
        option_views.append(
            {
                "species_id": option.get("species_id"),
                "form_name": option.get("form_name"),
                "regional_form_name": option.get("regional_form_name"),
                "evolution_stage": option.get("evolution_stage"),
                "primary_type": option.get("primary_type"),
                "secondary_type": option.get("secondary_type"),
                "ability_name": option.get("ability_name"),
                "observed_move_coverage_count": len(covered),
                "missing_observed_moves": missing,
                "source_page_id": option.get("source_page_id"),
            }
        )

    max_coverage = max((item["observed_move_coverage_count"] for item in option_views), default=0)
    best = [item for item in option_views if item["observed_move_coverage_count"] == max_coverage]
    identical_coverage = all(coverage == coverage_sets[0] for coverage in coverage_sets[1:]) if coverage_sets else False

    if len(best) == 1 and max_coverage == len(observed_moves):
        status = "candidate_species_by_move_legality"
        action = "use move legality as identity evidence before PM review"
    elif identical_coverage:
        status = "blocked_same_display_name_same_move_pool"
        action = "move legality cannot resolve identity; require form/source clue or A-layer alias repair"
    else:
        status = "blocked_ambiguous_species_id"
        action = "identity remains ambiguous; inspect source/form clues before PM review"

    report = {
        "species_name": species_name,
        "identity_status": status,
        "candidate_species_count": len(species_options),
        "observed_moves": observed_moves,
        "species_options": option_views,
        "best_species_ids_by_move_coverage": [str(item["species_id"]) for item in best],
        "recommended_action": action,
        "runtime_allowed": False,
    }
    if pm_identity_policy:
        report["pm_identity_policy"] = pm_identity_policy
        policy_name = str(pm_identity_policy.get("policy") or "")
        if policy_name == "require_form_resolution_before_set_review":
            report["identity_status"] = "blocked_pm_confirmed_distinct_forms"
            report["recommended_action"] = "先从来源或形态线索解析具体形态，再进入 PM review"
            report["policy_effect"] = "upgraded_to_form_resolution_blocker"
        elif policy_name == "do_not_assume_battle_distinct_forms_without_source_evidence":
            report["policy_effect"] = "conservative_note_only"
            report["recommended_action"] = (
                "不要按形态拆分；只有来源把形态与机制、培养或 set 身份绑定时才拆"
            )
    return report


def _axis_terms(variant: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    damage_axis = str(variant.get("damage_axis") or "")
    if damage_axis and damage_axis != "status_or_unknown":
        terms.append(f"damage_axis:{damage_axis}")
    terms.extend(f"role:{role}" for role in variant.get("roles") or [] if role)
    terms.extend(f"build_axis:{axis}" for axis in variant.get("build_axes") or [] if axis)
    config = variant.get("configuration") or {}
    for field in ("nature", "individual_values", "bloodline", "ability_mentions"):
        if config.get(field):
            terms.append(f"config:{field}")
    return sorted(set(terms))


def _build_axis_report(record: dict[str, Any]) -> list[dict[str, Any]]:
    species_name = str(record.get("species_name") or "")
    reports: list[dict[str, Any]] = []
    for family in record.get("set_family_candidates") or []:
        variants = list(family.get("alter_variants") or [])
        if not variants:
            continue
        signal_variants: list[dict[str, Any]] = []
        term_counts: Counter[str] = Counter()
        damage_axis_counts: Counter[str] = Counter()
        role_counts: Counter[str] = Counter()
        build_axis_counts: Counter[str] = Counter()
        config_signal_counts: Counter[str] = Counter()
        for variant in variants:
            terms = _axis_terms(variant)
            if not terms:
                continue
            term_counts.update(terms)
            damage_axis = str(variant.get("damage_axis") or "")
            if damage_axis:
                damage_axis_counts[damage_axis] += 1
            role_counts.update(str(role) for role in variant.get("roles") or [] if role)
            build_axis_counts.update(str(axis) for axis in variant.get("build_axes") or [] if axis)
            config = variant.get("configuration") or {}
            for field in ("nature", "individual_values", "bloodline", "ability_mentions"):
                if config.get(field):
                    config_signal_counts[field] += 1
            signal_variants.append(
                {
                    "source_id": variant.get("source_id"),
                    "moves": list(variant.get("moves") or []),
                    "axis_terms": terms,
                }
            )

        if len(signal_variants) < MIN_AXIS_SIGNAL_VARIANTS:
            status = "needs_more_axis_evidence"
            action = "collect more focused set-guide sources before splitting families"
        elif len(family.get("core_moves") or []) >= OVERWIDE_CORE_SIZE:
            status = "axis_signal_present_needs_core_binding"
            action = "cluster variants by role/build/config axis before PM review"
        else:
            status = "axis_signal_present_but_family_core_still_narrow"
            action = "use axis evidence as support only; do not split unless core/build diverges"

        reports.append(
            {
                "species_name": species_name,
                "source_family_id": family.get("family_id"),
                "axis_status": status,
                "core_move_count": len(family.get("core_moves") or []),
                "primary_source_count": len(family.get("primary_source_ids") or []),
                "top_axis_terms": dict(term_counts.most_common(12)),
                "damage_axis_counts": dict(damage_axis_counts.most_common()),
                "role_counts": dict(role_counts.most_common(10)),
                "build_axis_counts": dict(build_axis_counts.most_common(10)),
                "config_signal_counts": dict(config_signal_counts.most_common()),
                "signal_variant_count": len(signal_variants),
                "signal_variants": signal_variants[:8],
                "recommended_action": action,
                "runtime_allowed": False,
            }
        )
    return reports


def build_axis_identity_audit(
    *,
    batch_id: str,
    consolidation: dict[str, Any],
    species_options_index: dict[str, list[dict[str, Any]]],
    pm_identity_policies: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    identity_reports: list[dict[str, Any]] = []
    axis_reports: list[dict[str, Any]] = []
    pm_identity_policies = pm_identity_policies or {}
    for record in consolidation.get("species_records") or []:
        if record.get("state") != "split_blocked":
            continue
        species_name = str(record.get("species_name") or "")
        identity_report = _build_identity_report(
            record=record,
            species_options=species_options_index.get(species_name) or [],
            pm_identity_policy=pm_identity_policies.get(species_name),
        )
        if identity_report and identity_report.get("identity_status") != "single_a_layer_species":
            identity_reports.append(identity_report)
        axis_reports.extend(_build_axis_report(record))

    identity_counts = Counter(str(item.get("identity_status")) for item in identity_reports)
    axis_counts = Counter(str(item.get("axis_status")) for item in axis_reports)
    blocking_identity = [
        item for item in identity_reports
        if str(item.get("identity_status", "")).startswith("blocked")
        or item.get("identity_status") == "missing_a_layer_species"
    ]
    axis_blockers = [
        item for item in axis_reports
        if item.get("axis_status") == "axis_signal_present_needs_core_binding"
    ]
    next_action = (
        "repair_a_layer_identity_before_pm_review"
        if blocking_identity
        else "cluster_axis_signals_before_pm_review"
        if axis_blockers
        else "continue_source_discovery_or_recluster_algorithm_work"
    )

    return {
        "schema_version": "p14.axis_identity_audit.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source_consolidation_batch_id": consolidation.get("batch_id"),
        "policy": {
            "promotion_forbidden": True,
            "source_queue_updates": False,
            "graph_materialization": False,
            "min_axis_signal_variants": MIN_AXIS_SIGNAL_VARIANTS,
            "overwide_core_size": OVERWIDE_CORE_SIZE,
            "pm_identity_policies_applied": bool(pm_identity_policies),
        },
        "summary": {
            "identity_report_count": len(identity_reports),
            "identity_status_counts": dict(identity_counts),
            "pm_identity_policy_count": sum(1 for item in identity_reports if item.get("pm_identity_policy")),
            "axis_report_count": len(axis_reports),
            "axis_status_counts": dict(axis_counts),
            "blocking_identity_count": len(blocking_identity),
            "axis_blocker_count": len(axis_blockers),
            "recommended_next_action": next_action,
        },
        "identity_reports": identity_reports,
        "axis_reports": axis_reports,
    }


def render_axis_identity_brief(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    identity_reports = payload.get("identity_reports") or []
    axis_reports = payload.get("axis_reports") or []
    lines = [
        f"# P14 Axis / Identity Audit: {payload['batch_id']}",
        "",
        "## 结论",
        "- 这是 split blocker 的身份/战术轴审计，不是 promotion，也不会写 graph/runtime。",
        f"- 身份问题 {summary.get('identity_report_count', 0)} 个；其中阻塞 {summary.get('blocking_identity_count', 0)} 个。",
        f"- 战术轴报告 {summary.get('axis_report_count', 0)} 个；需要先做 axis binding 的 {summary.get('axis_blocker_count', 0)} 个。",
        f"- 下一动作：`{summary.get('recommended_next_action')}`。",
        "",
        "## 身份阻塞",
    ]
    blockers = [
        item for item in identity_reports
        if str(item.get("identity_status", "")).startswith("blocked")
        or item.get("identity_status") == "missing_a_layer_species"
    ]
    if blockers:
        for item in blockers[:12]:
            form_bits = []
            for option in item.get("species_options") or []:
                form = " / ".join(
                    str(v) for v in [option.get("form_name"), option.get("regional_form_name")]
                    if v
                ) or str(option.get("species_id"))
                form_bits.append(form)
            pm_policy = item.get("pm_identity_policy") or {}
            pm_bits = ""
            if pm_policy:
                pm_bits = (
                    f"；PM身份规则={pm_policy.get('status')} / {pm_policy.get('policy')}"
                )
                consequence = pm_policy.get("product_consequence")
                if consequence:
                    pm_bits += f"；产品后果={str(consequence).rstrip('。.')}"
            lines.append(
                f"- {item['species_name']}：{item['identity_status']}；候选 {item.get('candidate_species_count')} 个；形态={'; '.join(form_bits)}；动作 {item['recommended_action']}{pm_bits}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(["", "## 战术轴阻塞"])
    axis_blockers = [
        item for item in axis_reports
        if item.get("axis_status") == "axis_signal_present_needs_core_binding"
    ]
    if axis_blockers:
        for item in axis_blockers[:12]:
            terms = ", ".join(f"{k}={v}" for k, v in (item.get("top_axis_terms") or {}).items())
            lines.append(
                f"- {item['species_name']} {item['source_family_id']}：core 宽度 {item.get('core_move_count')}，axis source {item.get('signal_variant_count')}；{terms}；动作 {item['recommended_action']}。"
            )
    else:
        lines.append("- 暂无。")

    lines.extend(
        [
            "",
            "## 边界",
            "- 身份阻塞不等于 set 不存在，只说明 A-layer 当前不能给出唯一 species/form。",
            "- 轴信号不等于可以拆 set；必须先把技能 core 与角色/培养/血脉/性格轴绑定。",
            "- 本审计只决定下一步工程动作，不会产生 PM-reviewed card。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_axis_identity_audit(
    *,
    source_queue: Path = DEFAULT_SOURCE_QUEUE,
    consolidation_path: Path | None = None,
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str = DEFAULT_BATCH_ID,
    battle_dex: Path = DEFAULT_BATTLE_DEX,
    reviewer_ledger: Path = DEFAULT_REVIEWER_LEDGER,
) -> dict[str, Any]:
    consolidation_path = consolidation_path or _latest_consolidation_from_queue(source_queue)
    consolidation = _load_yaml(consolidation_path)
    reviewer_state = _load_yaml(reviewer_ledger)
    payload = build_axis_identity_audit(
        batch_id=batch_id,
        consolidation=consolidation,
        species_options_index=_species_options_index(battle_dex),
        pm_identity_policies=_identity_policies_from_reviewer_ledger(reviewer_state),
    )
    payload["input"] = {
        "consolidation_path": _relpath(consolidation_path),
        "battle_dex": _relpath(battle_dex),
        "reviewer_ledger": _relpath(reviewer_ledger),
    }
    audit_path = out_root / AXIS_DIRNAME / f"{batch_id}.yaml"
    brief_path = out_root / "review_packets" / f"{batch_id}_axis_identity.md"
    _write_yaml(audit_path, payload)
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(render_axis_identity_brief(payload), encoding="utf-8")
    return {
        "runtime_allowed": False,
        "paths": {"audit": _relpath(audit_path), "pm_brief": _relpath(brief_path)},
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
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_axis_identity_audit(
        source_queue=args.source_queue,
        consolidation_path=args.consolidation_path,
        out_root=args.out_root,
        batch_id=args.batch_id,
        battle_dex=args.battle_dex,
        reviewer_ledger=args.reviewer_ledger,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {result['paths']['pm_brief']}")


if __name__ == "__main__":
    main()
