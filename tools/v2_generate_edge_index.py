#!/usr/bin/env python3
"""Generate edge_index.yaml from species_set cards.

Scans all cards' related_to fields, aggregates into a bidirectional edge index.

Usage:
    .venv/bin/python tools/v2_generate_edge_index.py
"""

from __future__ import annotations

import sys

import yaml

from tools.v2_meta_graph_contracts import (
    EDGE_INDEX_PATH,
    load_all_cards,
    save_yaml,
    today_str,
)


def _edge_id(idx: int) -> str:
    return f"edge/auto/{idx:04d}"


def build_edge_index(cards: list[dict]) -> dict:
    # Build a lookup: which cards mention which targets
    target_to_sources: dict[str, list[str]] = {}
    edges: list[dict] = []

    for card in cards:
        src_id = card.get("id", "?")
        for rel in card.get("related_to") or []:
            tgt_id = rel.get("target_species_set_id", "")
            if not tgt_id:
                continue

            edge = {
                "id": None,  # assigned below
                "source_species_set_id": src_id,
                "target_species_set_id": tgt_id,
                "edge_type": rel.get("edge_type", ""),
                "description": rel.get("description", ""),
                "reasoning_quality": rel.get("reasoning_quality", ""),
                "conditions": rel.get("conditions", []),
                "confidence": rel.get("confidence", ""),
                "evidence_refs": rel.get("evidence_refs", []),
                "tags": rel.get("tags", []),
                "mechanism_refs": rel.get("mechanism_refs", []),
                "evidence_bundle_id": rel.get("evidence_bundle_id", ""),
                "claim_risk": rel.get("claim_risk", ""),
                "review_status": card.get("review_status", "unreviewed"),
                "meta_snapshot": card.get("meta_snapshot", ""),
                "graph_origin": card.get("graph_origin", "human"),
                "claimed_by_source_only": None,  # filled after first pass
                "has_counter_claim": False,
                "counter_claim_id": None,
            }
            edges.append(edge)
            target_to_sources.setdefault(tgt_id, []).append(src_id)

    # Assign IDs
    for i, edge in enumerate(edges):
        edge["id"] = _edge_id(i)

    # Compute claimed_by_source_only and counter_claims
    for edge in edges:
        src = edge["source_species_set_id"]
        tgt = edge["target_species_set_id"]
        edge["claimed_by_source_only"] = tgt not in target_to_sources

    # Detect counter-claims: edges in opposite direction with conflicting type
    edge_map: dict[tuple[str, str], list[int]] = {}
    for i, edge in enumerate(edges):
        pair = (edge["source_species_set_id"], edge["target_species_set_id"])
        edge_map.setdefault(pair, []).append(i)

    for (src, tgt), indices in edge_map.items():
        reverse = (tgt, src)
        if reverse in edge_map:
            for idx in indices:
                edges[idx]["has_counter_claim"] = True
                # Point to the first reverse edge
                reverse_idx = edge_map[reverse][0]
                edges[idx]["counter_claim_id"] = _edge_id(reverse_idx)

    return {
        "generated_at": today_str(),
        "meta_snapshot": cards[0].get("meta_snapshot", "") if cards else "",
        "total_edges": len(edges),
        "edges": edges,
    }


def main():
    cards = load_all_cards()
    if not cards:
        print("No cards found — nothing to generate.")
        return

    index = build_edge_index(cards)
    save_yaml(index, EDGE_INDEX_PATH)
    print(f"edge_index.yaml 已生成: {index['total_edges']} 条边")


if __name__ == "__main__":
    main()
