#!/usr/bin/env python3
"""Validate Meta Graph species_set cards and index files.

Usage:
    .venv/bin/python tools/v2_validate_graph.py
    .venv/bin/python tools/v2_validate_graph.py --strict
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

from tools.v2_meta_graph_contracts import (
    EDGE_INDEX_PATH,
    META_GRAPH_DIR,
    REGISTRY_PATH,
    SPECIES_SETS_DIR,
    SPEED_INDEX_PATH,
    Confidence,
    EdgeType,
    GraphOrigin,
    ReasoningQuality,
    ReviewStatus,
    RoleLabel,
    SourceType,
    list_card_files,
    load_all_cards,
    load_card,
    load_registry,
)

REQUIRED_FIELDS = [
    "id", "canonical_species_id", "canonical_species_name",
    "moves", "ability", "meta_snapshot",
    "graph_origin", "source_refs",
    "confidence", "review_status",
]

RELATED_TO_REQUIRED = [
    "target_species_set_id", "edge_type", "description",
    "reasoning_quality", "confidence", "evidence_refs",
]

EVIDENCE_REF_REQUIRED = [
    "source_type", "source_ref", "claim",
    "reasoning_available", "date",
]


def validate_card(card: dict, path: Path, strict: bool) -> list[str]:
    errors: list[str] = []
    cid = card.get("id", path.name)

    # ── Required fields ──
    for field in REQUIRED_FIELDS:
        if not card.get(field):
            errors.append(f"[{cid}] 缺少必填字段: {field}")

    # ── moves must be a non-empty list ──
    moves = card.get("moves")
    if not isinstance(moves, list) or len(moves) == 0:
        errors.append(f"[{cid}] moves 必须是非空列表")

    # ── source_refs must be a non-empty list ──
    refs = card.get("source_refs")
    if not isinstance(refs, list) or len(refs) == 0:
        errors.append(f"[{cid}] source_refs 必须是非空列表")

    # ── Enum validations ──
    if card.get("graph_origin") and card["graph_origin"] not in GraphOrigin._value2member_map_:
        errors.append(f"[{cid}] 无效 graph_origin: {card['graph_origin']}")
    if card.get("confidence") and card["confidence"] not in Confidence._value2member_map_:
        errors.append(f"[{cid}] 无效 confidence: {card['confidence']}")
    if card.get("review_status") and card["review_status"] not in ReviewStatus._value2member_map_:
        errors.append(f"[{cid}] 无效 review_status: {card['review_status']}")

    # ── role_labels enum ──
    for rl in card.get("role_labels") or []:
        if rl not in RoleLabel._value2member_map_:
            errors.append(f"[{cid}] 无效 role_label: {rl}")

    # ── source_refs entries ──
    for i, sr in enumerate(refs):
        st = sr.get("source_type", "")
        if st not in SourceType._value2member_map_:
            errors.append(f"[{cid}] source_refs[{i}] 无效 source_type: {st}")

    # ── speed_tier should be int if present ──
    st = card.get("speed_tier")
    if st is not None and not isinstance(st, int):
        errors.append(f"[{cid}] speed_tier 必须是整数，当前: {type(st).__name__}")

    # ── stat_profile.speed should be int if present ──
    sp = card.get("stat_profile", {}) or {}
    if sp.get("speed") is not None and not isinstance(sp["speed"], int):
        errors.append(f"[{cid}] stat_profile.speed 必须是整数")

    # ── Validate related_to entries ──
    for j, rel in enumerate(card.get("related_to") or []):
        prefix = f"[{cid}] related_to[{j}]"

        for field in RELATED_TO_REQUIRED:
            if not rel.get(field):
                errors.append(f"{prefix} 缺少必填字段: {field}")

        et = rel.get("edge_type", "")
        if et and et not in EdgeType._value2member_map_:
            errors.append(f"{prefix} 无效 edge_type: {et}")

        rq = rel.get("reasoning_quality", "")
        if rq and rq not in ReasoningQuality._value2member_map_:
            errors.append(f"{prefix} 无效 reasoning_quality: {rq}")

        rc = rel.get("confidence", "")
        if rc and rc not in Confidence._value2member_map_:
            errors.append(f"{prefix} 无效 confidence: {rc}")

        if rel.get("target_species_set_id") == cid:
            errors.append(f"{prefix} related_to 不能指向自己")

        # confidence downgrade rule: claim_only + observed -> warn
        if rq == "claim_only" and rc == "observed" and strict:
            errors.append(
                f"{prefix} reasoning_quality=claim_only，"
                f"confidence 应降级为 inferred"
            )

        # Validate evidence_refs in relation
        for k, er in enumerate(rel.get("evidence_refs") or []):
            for erf in EVIDENCE_REF_REQUIRED:
                if erf not in er:
                    errors.append(f"{prefix} evidence_refs[{k}] 缺少: {erf}")
            if er.get("source_type") and er["source_type"] not in SourceType._value2member_map_:
                errors.append(f"{prefix} evidence_refs[{k}] 无效 source_type: {er['source_type']}")
            if not isinstance(er.get("reasoning_available"), bool):
                errors.append(f"{prefix} evidence_refs[{k}] reasoning_available 必须是 bool")
            if er.get("reasoning_available") and not er.get("reasoning_summary"):
                errors.append(f"{prefix} evidence_refs[{k}] reasoning_available=true 但缺少 reasoning_summary")

    return errors


def validate_cross_card(
    cards: list[dict],
    all_ids: set[str],
    strict: bool,
) -> list[str]:
    errors: list[str] = []

    # ── Duplicate IDs ──
    id_counts = Counter(c["id"] for c in cards if c.get("id"))
    for cid, count in id_counts.items():
        if count > 1:
            errors.append(f"[跨卡] 重复 ID ({count}次): {cid}")

    # ── Orphan related_to references ──
    for card in cards:
        cid = card.get("id", "?")
        for j, rel in enumerate(card.get("related_to") or []):
            target = rel.get("target_species_set_id", "")
            if target and target not in all_ids:
                errors.append(
                    f"[{cid}] related_to[{j}] 引用不存在的 target: {target}"
                )

    # ── Registry vs actual cards ──
    registry = load_registry()
    registered_ids = {e["id"] for e in registry.get("species_sets", [])}
    card_ids = {c["id"] for c in cards if c.get("id")}
    unregistered = card_ids - registered_ids
    missing_from_disk = registered_ids - card_ids

    if unregistered:
        errors.append(f"[注册表] 以下卡未在 graph_registry.yaml 注册: {unregistered}")
    if missing_from_disk:
        errors.append(f"[注册表] 以下卡在注册表中但文件缺失: {missing_from_disk}")

    return errors


def validate_edge_index(card_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not EDGE_INDEX_PATH.exists():
        return errors  # index hasn't been generated yet
    with open(EDGE_INDEX_PATH, encoding="utf-8") as fh:
        index = yaml.safe_load(fh) or {}
    for i, edge in enumerate(index.get("edges", [])):
        src = edge.get("source_species_set_id", "")
        tgt = edge.get("target_species_set_id", "")
        if src and src not in card_ids:
            errors.append(f"[edge_index] edge[{i}] source 不存在: {src}")
        if tgt and tgt not in card_ids:
            errors.append(f"[edge_index] edge[{i}] target 不存在: {tgt}")
    return errors


def validate_speed_index(card_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not SPEED_INDEX_PATH.exists():
        return errors
    with open(SPEED_INDEX_PATH, encoding="utf-8") as fh:
        index = yaml.safe_load(fh) or {}
    for tier_val, entries in (index.get("speed_tiers") or {}).items():
        for entry in entries:
            sid = entry.get("species_set_id", "")
            if sid and sid not in card_ids:
                errors.append(f"[speed_index] tier {tier_val} 引用不存在的卡: {sid}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Meta Graph")
    parser.add_argument("--strict", action="store_true", help="Enable stricter checks")
    args = parser.parse_args()

    all_errors: list[str] = []

    # ── Ensure directories exist ──
    if not SPECIES_SETS_DIR.exists():
        print("⚠ species_sets/ 目录不存在，跳过验证")
        return

    # ── Per-card validation ──
    card_files = list_card_files()
    if not card_files:
        print("⚠ 没有卡片文件，跳过验证")
        return

    print(f"验证 {len(card_files)} 张卡...")
    cards = []
    for path in card_files:
        try:
            card = load_card(path)
        except Exception as exc:
            all_errors.append(f"[{path.name}] YAML 解析失败: {exc}")
            continue
        cards.append(card)
        errs = validate_card(card, path, strict=args.strict)
        all_errors.extend(errs)

    all_ids = {c["id"] for c in cards if c.get("id")}

    # ── Cross-card validation ──
    all_errors.extend(validate_cross_card(cards, all_ids, strict=args.strict))

    # ── Index validation ──
    all_errors.extend(validate_edge_index(all_ids))
    all_errors.extend(validate_speed_index(all_ids))

    # ── Report ──
    if all_errors:
        print(f"\n❌ {len(all_errors)} 个问题:\n")
        for e in all_errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print(f"\n✅ {len(card_files)} 张卡验证通过")
        print(f"   已注册物种 ID: {len(all_ids)}")


if __name__ == "__main__":
    main()
