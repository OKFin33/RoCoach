from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.contracts import TeamSlot
from engine.contracts import to_payload
from engine.team_structure import TeamStructureAnalyzer


def parse_slot(raw: str, slot_index: int) -> TeamSlot:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError(
            "Each --slot must use 'name,primary_type' or 'name,primary_type,secondary_type'"
        )

    nickname = parts[0] or None
    primary_type = parts[1]
    secondary_type = parts[2] if len(parts) == 3 and parts[2] else None
    return TeamSlot(
        slot_index=slot_index,
        species_key=None,
        nickname=nickname,
        primary_type=primary_type,
        secondary_type=secondary_type,
    )


def parse_slot_payload(payload: dict, slot_index: int) -> TeamSlot:
    primary_type = payload.get("primary_type")
    if not primary_type:
        raise ValueError("Each slot payload must include primary_type")

    return TeamSlot(
        slot_index=slot_index,
        species_key=payload.get("species_key"),
        nickname=payload.get("name") or payload.get("nickname"),
        primary_type=primary_type,
        secondary_type=payload.get("secondary_type"),
        selected_ability=payload.get("selected_ability"),
        selected_moves=tuple(payload.get("selected_moves", ())),
        item=payload.get("item"),
    )


def load_slots_from_file(input_file: str) -> tuple[TeamSlot, ...]:
    path = Path(input_file)
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_slots = payload.get("slots")
    if not isinstance(raw_slots, list) or not raw_slots:
        raise ValueError("Input file must contain a non-empty 'slots' list")

    return tuple(parse_slot_payload(slot_payload, index) for index, slot_payload in enumerate(raw_slots, start=1))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 team structure analyzer")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--slot",
        action="append",
        help="Team slot in the form 'name,primary_type' or 'name,primary_type,secondary_type'",
    )
    source_group.add_argument(
        "--input-file",
        help="JSON file containing a 'slots' list with primary_type and optional secondary_type",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser


def format_report(report) -> str:
    lines = []
    lines.append("== Team Structure Report ==")
    lines.append(f"structural_score: {report.structural_score:.3f}")
    lines.append(f"repeated_weaknesses: {', '.join(report.repeated_weaknesses) or 'none'}")
    lines.append(f"missing_resistances: {', '.join(report.missing_resistances) or 'none'}")
    lines.append(f"primary_patch_types: {', '.join(report.primary_patch_types) or 'none'}")
    lines.append(
        "conditional_dual_patch_types: "
        f"{', '.join(report.conditional_dual_patch_types) or 'none'}"
    )
    lines.append("")
    lines.append("== Defensive Coverage ==")
    for entry in report.defensive_coverage:
        lines.append(
            f"{entry.defending_type}: weak={entry.weak_slots} resist={entry.resist_slots} neutral={entry.neutral_slots}"
        )
    lines.append("")
    lines.append("== Offensive Coverage (STAB-only) ==")
    for entry in report.offensive_coverage:
        lines.append(
            f"{entry.attacker_type}: strong=[{', '.join(entry.super_effective_targets)}] "
            f"resisted=[{', '.join(entry.resisted_targets)}]"
        )
    if report.overlap_notes:
        lines.append("")
        lines.append("== Notes ==")
        lines.extend(report.overlap_notes)
    lines.append("")
    lines.append("== Evidence ==")
    lines.extend(report.evidence)
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.input_file:
        slots = load_slots_from_file(args.input_file)
    else:
        if len(args.slot) > 6:
            raise SystemExit("A team may include at most 6 slots")
        slots = tuple(parse_slot(raw, index) for index, raw in enumerate(args.slot, start=1))

    if len(slots) > 6:
        raise SystemExit("A team may include at most 6 slots")

    analyzer = TeamStructureAnalyzer()
    report = analyzer.analyze(slots)
    if args.format == "json":
        print(json.dumps(to_payload(report), ensure_ascii=False, indent=2))
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()
