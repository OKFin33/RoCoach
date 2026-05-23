#!/usr/bin/env python3
"""Generate speed_index.yaml from species_set cards.

Scans all cards' speed_tier fields, builds ordered speed tier table
and computes pairwise speed relations.

Usage:
    .venv/bin/python tools/v2_generate_speed_index.py
"""

from __future__ import annotations

from tools.v2_meta_graph_contracts import (
    SPEED_INDEX_PATH,
    load_all_cards,
    save_yaml,
    today_str,
)


def _speed_rel_id(idx: int) -> str:
    return f"speed_rel/auto/{idx:04d}"


def build_speed_index(cards: list[dict]) -> dict:
    # Collect cards with speed_tier
    speed_entries: list[tuple[int, dict]] = []
    for card in cards:
        st = card.get("speed_tier")
        if st is None or not isinstance(st, int):
            continue
        speed_entries.append((
            st,
            {
                "species_set_id": card.get("id", "?"),
                "species_name": card.get("canonical_species_name", "?"),
                "graph_origin": card.get("graph_origin", "human"),
                "nature": card.get("nature", ""),
                "config_note": card.get("notes", ""),
            },
        ))

    # Sort descending by speed
    speed_entries.sort(key=lambda x: x[0], reverse=True)

    # Build tier map: speed value -> list of entries
    speed_tiers: dict[int, list[dict]] = {}
    for spd, entry in speed_entries:
        speed_tiers.setdefault(spd, []).append(entry)

    # Build pairwise speed relations
    speed_relations: list[dict] = []
    rel_idx = 0
    for i, (spd_a, entry_a) in enumerate(speed_entries):
        for j, (spd_b, entry_b) in enumerate(speed_entries):
            if i == j:
                continue
            if spd_a > spd_b:
                margin = spd_a - spd_b
                rel = {
                    "id": _speed_rel_id(rel_idx),
                    "faster": entry_a["species_set_id"],
                    "slower": entry_b["species_set_id"],
                    "relation": "outspeeds",
                    "margin": margin,
                    "nature_variants_known": bool(entry_a.get("nature") and entry_b.get("nature")),
                    "note": "",
                }
                speed_relations.append(rel)
                rel_idx += 1

    return {
        "generated_at": today_str(),
        "meta_snapshot": cards[0].get("meta_snapshot", "") if cards else "",
        "total_speed_entries": len(speed_entries),
        "total_speed_relations": len(speed_relations),
        "speed_tiers": speed_tiers,
        "speed_relations": speed_relations,
    }


def main():
    cards = load_all_cards()
    if not cards:
        print("No cards found — nothing to generate.")
        return

    index = build_speed_index(cards)
    save_yaml(index, SPEED_INDEX_PATH)
    print(
        f"speed_index.yaml 已生成: "
        f"{index['total_speed_entries']} 个速度条目, "
        f"{index['total_speed_relations']} 条速度关系"
    )


if __name__ == "__main__":
    main()
