from __future__ import annotations

import argparse
import json

from engine.phase1_cli import load_slots_from_file, parse_slot
from knowledge.service import Phase15ReportService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1.5 report and advisor harness")
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
        "--backend",
        choices=("deterministic", "pydantic_ai"),
        default="deterministic",
        help="Narrative generation backend",
    )
    parser.add_argument(
        "--model",
        help="Model name for the PydanticAI backend, e.g. 'openai:gpt-5.2-mini'",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser


def format_report(payload: dict) -> str:
    report = payload["narrative_report"]
    structure_report = payload["structure_report"]

    lines = []
    lines.append("== Phase 1.5 Team Report ==")
    lines.append(f"backend: {payload['backend']}")
    lines.append(f"structural_score: {structure_report['structural_score']:.3f}")
    lines.append("")
    lines.append("== Summary ==")
    lines.append(report["summary"])
    lines.append("")
    lines.append("== Major Risks ==")
    for item in report["major_risks"]:
        lines.append(f"- [{item['severity']}] {item['title']}: {item['explanation']}")
    lines.append("")
    lines.append("== Defensive Takeaways ==")
    for item in report["defensive_takeaways"]:
        lines.append(f"- {item['theme']}: {item['explanation']}")
    lines.append("")
    lines.append("== Offensive Takeaways ==")
    for item in report["offensive_takeaways"]:
        lines.append(f"- {item['theme']}: {item['explanation']}")
    lines.append("")
    lines.append("== Patch Guidance ==")
    patch = report["patch_guidance"]
    lines.append(f"primary_patch_types: {', '.join(patch['primary_patch_types']) or 'none'}")
    lines.append(
        "conditional_dual_patch_types: "
        f"{', '.join(patch['conditional_dual_patch_types']) or 'none'}"
    )
    lines.append(patch["explanation"])
    lines.append("")
    lines.append("== Confidence Notes ==")
    for item in report["confidence_notes"]:
        lines.append(f"- [{item['confidence']}] {item['claim_scope']}: {item['note']}")
    lines.append("")
    lines.append("== Evidence Summary ==")
    lines.extend(f"- {line}" for line in report["evidence_summary"])
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

    service = Phase15ReportService()
    result = service.analyze(slots, backend=args.backend, model_name=args.model)
    payload = result.model_dump(mode="json")

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report(payload))


if __name__ == "__main__":
    main()
