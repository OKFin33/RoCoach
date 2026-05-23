#!/usr/bin/env python3
"""Validate P14 Knowledge Graph control-plane gates.

This complements the older v2 Meta Graph structural validator. It checks the
P14-specific control-plane rules: graph root layout, review ledgers, mechanism
rule runtime gates, and mechanism-dependent Set Graph promotion blockers.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tools.v2_meta_graph_contracts import (
    COMPAT_META_GRAPH_DIR,
    KNOWLEDGE_GRAPH_DIR,
    MECHANISM_RULES_DIR,
    META_GRAPH_DIR,
    REVIEW_STATE_DIR,
    load_all_cards,
)


REQUIRED_REVIEW_STATE_FILES = [
    "reviewer_ledger.yaml",
    "family_review_ledger.yaml",
    "error_ledger.yaml",
    "source_reliability_ledger.yaml",
    "promotion_audit_log.yaml",
    "affected_asset_index.yaml",
]

REQUIRED_ROOT_FILES = [
    "runtime_manifest.yaml",
    "migration_log.yaml",
]

FIELD_PROVENANCE_GROUPS = [
    "species",
    "moves",
    "nature",
    "iv",
    "bloodline",
    "role",
    "teammate_relations",
    "counter_relations",
    "mechanism_dependencies",
]

REVIEW_IDENTITY_FIELDS = [
    "extractor_agent_id",
    "extractor_run_id",
    "reviewer_agent_id",
    "reviewer_run_id",
]

IDENTITY_POLICY_CUTOFF = date(2026, 5, 23)
LEGACY_IDENTITY_VALUE = "legacy_unknown"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _yaml_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.glob("*.yaml") if not p.name.startswith("_"))


def _mechanism_rules(rules_dir: Path) -> dict[str, dict[str, Any]]:
    rules: dict[str, dict[str, Any]] = {}
    for path in _yaml_files(rules_dir):
        rule = _load_yaml(path)
        rid = rule.get("id")
        if rid:
            rule["_file"] = str(path)
            rules[rid] = rule
    return rules


def _runtime_rule_ids(rules: dict[str, dict[str, Any]]) -> set[str]:
    runtime_ids: set[str] = set()
    for rid, rule in rules.items():
        review = rule.get("review", {}) or {}
        runtime = rule.get("runtime", {}) or {}
        if review.get("review_status") == "pm_reviewed" and runtime.get("runtime_allowed") is True:
            runtime_ids.add(rid)
    return runtime_ids


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _is_after_identity_cutoff(value: Any) -> bool:
    parsed = _parse_date(value)
    return bool(parsed and parsed > IDENTITY_POLICY_CUTOFF)


def _legacy_identity_fields(group: dict[str, Any], fields: list[str]) -> list[str]:
    legacy_fields = [
        field
        for field in fields
        if group.get(field) == LEGACY_IDENTITY_VALUE
    ]
    status = str(group.get("identity_status") or "")
    if status.startswith("legacy"):
        legacy_fields.append("identity_status")
    return legacy_fields


def _validate_review_state(review_state_dir: Path, *, strict: bool) -> list[str]:
    errors: list[str] = []
    if not review_state_dir.exists():
        if strict:
            errors.append(f"[review_state] missing directory: {review_state_dir}")
        return errors
    for filename in REQUIRED_REVIEW_STATE_FILES:
        path = review_state_dir / filename
        if not path.exists():
            errors.append(f"[review_state] missing required ledger: {filename}")
            continue
        data = _load_yaml(path)
        if not data.get("schema_version"):
            errors.append(f"[review_state] {filename} missing schema_version")
    errors.extend(_validate_family_review_ledger(review_state_dir))
    errors.extend(_validate_promotion_audit_log(review_state_dir))
    return errors


def _validate_root_metadata(knowledge_root: Path, *, strict: bool) -> list[str]:
    errors: list[str] = []
    if not knowledge_root.exists():
        if strict:
            errors.append(f"[root] missing knowledge graph root: {knowledge_root}")
        return errors
    for filename in REQUIRED_ROOT_FILES:
        path = knowledge_root / filename
        if not path.exists():
            errors.append(f"[root] missing required metadata file: {filename}")
            continue
        data = _load_yaml(path)
        if strict and not data.get("schema_version"):
            errors.append(f"[root] {filename} missing schema_version")
    manifest_path = knowledge_root / "runtime_manifest.yaml"
    if manifest_path.exists():
        manifest = _load_yaml(manifest_path)
        if strict and "compatibility_source" in manifest:
            errors.append(
                "[root] runtime_manifest.yaml uses deprecated compatibility_source; "
                "use schema_compatibility.migration_log_ref"
            )
        compatibility = manifest.get("schema_compatibility") or {}
        if strict and not compatibility.get("migration_log_ref"):
            errors.append("[root] runtime_manifest.yaml missing schema_compatibility.migration_log_ref")
    return errors


def _validate_family_review_ledger(review_state_dir: Path) -> list[str]:
    errors: list[str] = []
    ledger_path = review_state_dir / "family_review_ledger.yaml"
    source_path = review_state_dir / "source_reliability_ledger.yaml"
    if not ledger_path.exists():
        return errors
    ledger = _load_yaml(ledger_path)
    source_ledger_exists = source_path.exists()
    source_ledger = _load_yaml(source_path) if source_ledger_exists else {}
    known_source_ids = {
        str(item.get("source_id"))
        for item in (source_ledger.get("sources") or [])
        if item.get("source_id")
    }
    allowed_statuses = {"candidate", "review_packeted", "pm_reviewed", "deferred", "rejected", "superseded"}
    for entry in ledger.get("entries") or []:
        review_id = entry.get("review_id") or "<missing_review_id>"
        prefix = f"[family_review:{review_id}]"
        if entry.get("review_scope") != "set_family":
            errors.append(f"{prefix} review_scope must be set_family")
        review_status = ((entry.get("review") or {}).get("review_status"))
        if review_status not in allowed_statuses:
            errors.append(f"{prefix} invalid review_status: {review_status!r}")
        source_candidate = entry.get("source_candidate") or {}
        if not source_candidate.get("species_name"):
            errors.append(f"{prefix} missing source_candidate.species_name")
        if not source_candidate.get("canonical_species_id"):
            errors.append(f"{prefix} missing source_candidate.canonical_species_id")
        if not source_candidate.get("source_family_id"):
            errors.append(f"{prefix} missing source_candidate.source_family_id")
        proposed_card = entry.get("proposed_card") or {}
        if len(proposed_card.get("core_moves") or []) < 2:
            errors.append(f"{prefix} family review requires at least two core_moves")
        evidence = entry.get("evidence") or {}
        primary_source_ids = [str(sid) for sid in (evidence.get("primary_source_ids") or [])]
        if len(primary_source_ids) < 2:
            errors.append(f"{prefix} family review requires at least two primary sources")
        for sid in primary_source_ids:
            if source_ledger_exists and sid not in known_source_ids:
                errors.append(f"{prefix} primary source missing from source_reliability_ledger: {sid}")
        boundary = entry.get("species_card_boundary") or {}
        gate = entry.get("promotion_gate") or {}
        if boundary.get("species_level_card_status") == "split_blocked" and gate.get("allowed_scope") != "set_family_only":
            errors.append(f"{prefix} split-blocked species must keep allowed_scope=set_family_only")
        if gate.get("promotion_ready") is True and review_status != "pm_reviewed":
            errors.append(f"{prefix} promotion_ready=true but review_status is {review_status!r}")
        if gate.get("runtime_allowed") is True and review_status != "pm_reviewed":
            errors.append(f"{prefix} runtime_allowed=true but review_status is {review_status!r}")
        if review_status == "pm_reviewed":
            reviewer = (entry.get("review") or {}).get("reviewer")
            review_date = (entry.get("review") or {}).get("review_date")
            if not reviewer or not review_date:
                errors.append(f"{prefix} pm_reviewed entry missing reviewer or review_date")
            for field in ["extractor_agent_id", "extractor_run_id"]:
                if not source_candidate.get(field):
                    errors.append(f"{prefix} pm_reviewed entry missing source_candidate.{field}")
            review = entry.get("review") or {}
            for field in ["reviewer_agent_id", "reviewer_run_id"]:
                if not review.get(field):
                    errors.append(f"{prefix} pm_reviewed entry missing review.{field}")
            if _is_after_identity_cutoff(review_date):
                for field in _legacy_identity_fields(
                    source_candidate,
                    ["extractor_agent_id", "extractor_run_id"],
                ):
                    errors.append(
                        f"{prefix} post-2026-05-23 pm_reviewed entry uses legacy identity: "
                        f"source_candidate.{field}"
                    )
                for field in _legacy_identity_fields(
                    review,
                    ["reviewer_agent_id", "reviewer_run_id"],
                ):
                    errors.append(
                        f"{prefix} post-2026-05-23 pm_reviewed entry uses legacy identity: "
                        f"review.{field}"
                    )
    return errors


def _validate_promotion_audit_log(review_state_dir: Path) -> list[str]:
    errors: list[str] = []
    audit_path = review_state_dir / "promotion_audit_log.yaml"
    if not audit_path.exists():
        return errors
    audit = _load_yaml(audit_path)
    for entry in audit.get("promotions") or []:
        audit_id = entry.get("audit_id") or "<missing_audit_id>"
        prefix = f"[promotion_audit:{audit_id}]"
        for group_name in ["actor_identity", "reviewer_identity"]:
            group = entry.get(group_name) or {}
            for field in ["role", "agent_id", "run_or_context_id"]:
                if not group.get(field):
                    errors.append(f"{prefix} missing {group_name}.{field}")
    return errors


def _validate_mechanism_rules(rules: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for rid, rule in rules.items():
        prefix = f"[mechanism_rule:{rid}]"
        if not rule.get("normalized_rule"):
            errors.append(f"{prefix} missing normalized_rule")
        review = rule.get("review", {}) or {}
        runtime = rule.get("runtime", {}) or {}
        review_status = review.get("review_status")
        runtime_allowed = runtime.get("runtime_allowed")
        contradictions = rule.get("contradictions") or []
        unresolved = [
            c for c in contradictions
            if (c or {}).get("status") == "unresolved"
        ]
        if runtime_allowed is True and review_status != "pm_reviewed":
            errors.append(f"{prefix} runtime_allowed=true but review_status is {review_status!r}")
        if runtime_allowed is True and unresolved:
            errors.append(f"{prefix} runtime_allowed=true with unresolved contradictions")
    return errors


def _validate_mechanism_refs(
    *,
    asset_id: str,
    refs: list[str],
    all_rule_ids: set[str],
    runtime_rule_ids: set[str],
    promotion_active: bool,
) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        if ref not in all_rule_ids:
            errors.append(f"[{asset_id}] unknown mechanism_ref: {ref}")
        elif promotion_active and ref not in runtime_rule_ids:
            errors.append(f"[{asset_id}] promoted asset references non-runtime mechanism rule: {ref}")
    return errors


def _promotion_active(card: dict[str, Any]) -> bool:
    promotion = card.get("promotion", {}) or {}
    return (
        card.get("review_status") == "reviewed"
        or promotion.get("promotion_status") in {"pm_reviewed", "runtime_promoted"}
    )


def _validate_reviewed_card_overlay(card: dict[str, Any], *, active: bool) -> list[str]:
    if not active:
        return []
    errors: list[str] = []
    cid = card.get("id", card.get("_file", "?"))
    prefix = f"[{cid}]"

    if card.get("schema_version") != "p14.species_set_card.v0":
        errors.append(f"{prefix} reviewed card missing schema_version=p14.species_set_card.v0")

    projection = card.get("kg_item_projection") or {}
    if projection.get("schema_version") != "p14.kg_item.v0":
        errors.append(f"{prefix} reviewed card missing kg_item_projection.schema_version=p14.kg_item.v0")
    if not projection.get("crosswalk_ref"):
        errors.append(f"{prefix} reviewed card missing kg_item_projection.crosswalk_ref")

    provenance = card.get("field_provenance") or {}
    for group in FIELD_PROVENANCE_GROUPS:
        values = provenance.get(group)
        if not isinstance(values, list) or not values:
            errors.append(f"{prefix} reviewed card missing non-empty field_provenance.{group}")
            continue
        for idx, item in enumerate(values):
            if not isinstance(item, dict):
                errors.append(f"{prefix} field_provenance.{group}[{idx}] must be a mapping")
                continue
            support_type = item.get("support_type")
            if not support_type:
                errors.append(f"{prefix} field_provenance.{group}[{idx}] missing support_type")
            if support_type != "not_applicable":
                span_ids = item.get("source_span_ids") or []
                claim_ids = item.get("claim_atom_ids") or []
                if not span_ids and not claim_ids:
                    errors.append(
                        f"{prefix} field_provenance.{group}[{idx}] needs source_span_ids, "
                        "claim_atom_ids, or support_type=not_applicable"
                    )

    review_identity = card.get("review_identity") or {}
    for field in REVIEW_IDENTITY_FIELDS:
        if not review_identity.get(field):
            errors.append(f"{prefix} reviewed card missing review_identity.{field}")
    legacy_fields = _legacy_identity_fields(review_identity, REVIEW_IDENTITY_FIELDS)
    if legacy_fields:
        review_dates = [
            _parse_date(review_identity.get("review_date")),
            *[
                _parse_date(ref.get("review_date"))
                for ref in card.get("source_refs") or []
                if isinstance(ref, dict)
            ],
        ]
        known_dates = [item for item in review_dates if item is not None]
        if not known_dates:
            errors.append(f"{prefix} reviewed card uses legacy identity without a dated pre-policy review record")
        if any(item > IDENTITY_POLICY_CUTOFF for item in known_dates):
            for field in legacy_fields:
                errors.append(
                    f"{prefix} post-2026-05-23 reviewed card uses legacy identity: review_identity.{field}"
                )

    return errors


def _validate_set_graph_cards(
    *,
    set_graph_root: Path,
    all_rule_ids: set[str],
    runtime_rule_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    cards = load_all_cards(set_graph_root / "species_sets")
    for card in cards:
        cid = card.get("id", card.get("_file", "?"))
        active = _promotion_active(card)
        source_quality = card.get("source_quality", {}) or {}
        if active and source_quality.get("transcript_quality") == "poor":
            errors.append(f"[{cid}] promoted asset has poor transcript_quality")
        unresolved_terms = source_quality.get("asr_unresolved_terms") or []
        if active and unresolved_terms:
            errors.append(f"[{cid}] promoted asset has unresolved ASR terms: {unresolved_terms}")
        errors.extend(_validate_reviewed_card_overlay(card, active=active))
        promotion = card.get("promotion", {}) or {}
        if promotion.get("promotion_status") == "runtime_promoted" and card.get("review_status") != "reviewed":
            errors.append(f"[{cid}] runtime_promoted but review_status is not reviewed")
        errors.extend(_validate_mechanism_refs(
            asset_id=cid,
            refs=card.get("mechanism_refs") or [],
            all_rule_ids=all_rule_ids,
            runtime_rule_ids=runtime_rule_ids,
            promotion_active=active,
        ))
        for idx, rel in enumerate(card.get("related_to") or []):
            rid = f"{cid}.related_to[{idx}]"
            errors.extend(_validate_mechanism_refs(
                asset_id=rid,
                refs=rel.get("mechanism_refs") or [],
                all_rule_ids=all_rule_ids,
                runtime_rule_ids=runtime_rule_ids,
                promotion_active=active,
            ))
            if active and rel.get("claim_risk") == "high" and rel.get("reasoning_quality") == "claim_only":
                errors.append(f"[{rid}] promoted high-risk claim_only edge")
    return errors


def validate_knowledge_graph(
    *,
    knowledge_root: Path = KNOWLEDGE_GRAPH_DIR,
    set_graph_root: Path = META_GRAPH_DIR,
    mechanism_rules_dir: Path = MECHANISM_RULES_DIR,
    review_state_dir: Path = REVIEW_STATE_DIR,
    strict: bool = False,
) -> list[str]:
    errors: list[str] = []

    if strict and (COMPAT_META_GRAPH_DIR / "species_sets").exists():
        errors.append(
            "[path] historical data/meta_graph/v0 still contains active species_sets; "
            "use data/knowledge_graph/v0/set_graph as the only active runtime root"
        )

    if strict and not knowledge_root.exists():
        errors.append(f"[root] missing knowledge graph root: {knowledge_root}")
    errors.extend(_validate_root_metadata(knowledge_root, strict=strict))
    if not (set_graph_root / "species_sets").exists():
        errors.append(f"[set_graph] missing species_sets directory: {set_graph_root / 'species_sets'}")

    errors.extend(_validate_review_state(review_state_dir, strict=strict))

    rules = _mechanism_rules(mechanism_rules_dir / "rules")
    errors.extend(_validate_mechanism_rules(rules))

    errors.extend(_validate_set_graph_cards(
        set_graph_root=set_graph_root,
        all_rule_ids=set(rules),
        runtime_rule_ids=_runtime_rule_ids(rules),
    ))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate P14 Knowledge Graph gates")
    parser.add_argument("--strict", action="store_true", help="Enable strict path/layout gates")
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_GRAPH_DIR)
    parser.add_argument("--set-graph-root", type=Path, default=META_GRAPH_DIR)
    args = parser.parse_args()

    errors = validate_knowledge_graph(
        knowledge_root=args.knowledge_root,
        set_graph_root=args.set_graph_root,
        mechanism_rules_dir=args.knowledge_root / "mechanism_rules",
        review_state_dir=args.knowledge_root / "review_state",
        strict=args.strict,
    )

    if errors:
        print(f"\n❌ P14 Knowledge Graph validation failed: {len(errors)} issue(s)\n")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)

    print("✅ P14 Knowledge Graph gates passed")


if __name__ == "__main__":
    main()
