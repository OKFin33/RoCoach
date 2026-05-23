#!/usr/bin/env python3
"""Export manual supplement markdown into structured YAML/JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from tools.import_battle_dex_dry_run import parse_manual_supplement_markdown


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_payload(markdown_path: Path) -> dict[str, Any]:
    supplement = parse_manual_supplement_markdown(markdown_path)
    species_forms: list[dict[str, Any]] = []
    for display_name in supplement.excluded_forms:
        reason_code = "unreleased_form" if "火山附近的样子" in display_name else "hidden_special_form"
        entry: dict[str, Any] = {
            "display_name": display_name,
            "reason_code": reason_code,
            "resolution_status": "excluded",
        }
        if reason_code == "unreleased_form":
            entry["notes"] = "当前游戏版本未上线，排除出 battle dex ingest target"
        species_forms.append(entry)

    species_canonical_overrides = []
    for species_id in sorted(supplement.species_canonical_overrides):
        row = supplement.species_canonical_overrides[species_id]
        species_canonical_overrides.append(
            {
                "species_id": row.species_id,
                "canonical_display_name": row.canonical_display_name,
                "preferred_source_page_id": row.preferred_source_page_id,
                "source_status": "manual_verified_by_pm",
                "normalized_initial_species_name": row.normalized_initial_species_name,
                "normalized_evolution_stage": row.normalized_evolution_stage,
                "override_ability_name": row.override_ability_name,
                "override_ability_effect_text": row.override_ability_effect_text,
                "notes": list(row.notes),
            }
        )

    manual_moves = []
    for move_name in sorted(supplement.manual_moves):
        row = supplement.manual_moves[move_name]
        manual_moves.append(
            {
                "move_name": row.move_name,
                "source_status": "manual_verified_by_pm",
                "wiki_status": "unresolved_move_name",
                "move_type": row.move_type,
                "category_raw": row.category_raw,
                "energy_cost": row.energy_cost,
                "power": row.power,
                "effect_text": row.effect_text,
                "notes": list(row.notes),
            }
        )

    move_aliases = []
    for source_move_name in sorted(supplement.move_aliases):
        move_aliases.append(
            {
                "source_move_name": source_move_name,
                "target_move_name": supplement.move_aliases[source_move_name],
                "source_status": "manual_verified_by_pm",
                "notes": [
                    "treat source move name as a learnset/source alias of the canonical target move",
                    "preserve raw wiki provenance; do not mutate crawl artifacts",
                ],
            }
        )

    ability_text_overrides = []
    for ability_name in sorted(supplement.ability_text_overrides):
        ability_text_overrides.append(
            {
                "ability_name": ability_name,
                "source_status": "manual_verified_by_pm",
                "override_text": supplement.ability_text_overrides[ability_name],
                "notes": [
                    "current manual-verified baseline resolves conflicting wiki-derived effect texts",
                    "conflicting wiki evidence must remain visible in provenance",
                ],
            }
        )

    return {
        "version": 1,
        "source_policy": "policy_b",
        "source_markdown": str(markdown_path.resolve()),
        "generated_at": utc_now(),
        "exclusions": {"species_forms": species_forms},
        "species_canonical_overrides": species_canonical_overrides,
        "review_rules": [
            {
                "rule_id": "review_hidden_or_non_human_facing_form",
                "entity_type": "species_form",
                "trigger": "form is not visible in the human-facing dex path and looks plot-only / non-player-usable",
                "importer_status": "human-review-before-ingest",
            },
            {
                "rule_id": "review_missing_battle_stats_special_form",
                "entity_type": "species_form",
                "trigger": "form page lacks required battle stats and appears to be a special form",
                "importer_status": "human-review-before-ingest",
            },
            {
                "rule_id": "review_not_yet_live_form",
                "entity_type": "species_form",
                "trigger": "wiki page exists but PM manually confirms the form is not yet live",
                "importer_status": "human-review-before-ingest",
            },
        ],
        "manual_moves": manual_moves,
        "move_aliases": move_aliases,
        "ability_text_overrides": ability_text_overrides,
        "mechanics_notes": [
            {
                "mechanic_name": "印记系统基础规则",
                "source_status": "manual_verified_by_pm",
                "notes": [
                    "湿润印记效果为能耗 -1",
                    "印记不会因轮换而消失",
                    "单位最多同时拥有 1 个正面印记和 1 个负面印记",
                    "特殊技能可清除印记，例如：倾泻、食腐、焚烧烙印",
                ],
                "modeling_guidance": [
                    "do not flatten these notes into raw move/species fields during first-pass importer design",
                    "expose them later through mechanics supplement inputs for Engine or Agent reasoning",
                ],
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export manual supplement markdown into structured files.")
    parser.add_argument("--markdown-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()

    payload = build_payload(args.markdown_path)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        args.output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        args.output_path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
