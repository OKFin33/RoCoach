from __future__ import annotations

import unittest

from tools.p14_axis_identity_audit import build_axis_identity_audit, render_axis_identity_brief


def _record(
    *,
    species_name: str = "化蝶",
    stable_moves: list[str] | None = None,
    families: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "species_name": species_name,
        "state": "split_blocked",
        "primary_source_count": 10,
        "stable_moves": stable_moves or ["晒太阳", "毒孢子"],
        "set_family_candidates": families or [],
    }


def _option(species_id: str, moves: list[str], *, form: str = "地区形态") -> dict[str, object]:
    return {
        "species_id": species_id,
        "form_name": form,
        "regional_form_name": species_id,
        "evolution_stage": "最终形态",
        "primary_type": "虫",
        "secondary_type": "萌",
        "ability_name": "化茧",
        "available_moves": moves,
    }


class P14AxisIdentityAuditTests(unittest.TestCase):
    def test_same_display_name_same_move_pool_blocks_identity_resolution(self) -> None:
        payload = build_axis_identity_audit(
            batch_id="test",
            consolidation={"batch_id": "c1", "species_records": [_record()]},
            species_options_index={
                "化蝶": [
                    _option("species_a", ["晒太阳", "毒孢子", "闪击"]),
                    _option("species_b", ["晒太阳", "毒孢子", "闪击"]),
                ]
            },
        )

        report = payload["identity_reports"][0]
        self.assertEqual(report["identity_status"], "blocked_same_display_name_same_move_pool")
        self.assertEqual(report["best_species_ids_by_move_coverage"], ["species_a", "species_b"])
        self.assertEqual(payload["summary"]["blocking_identity_count"], 1)

    def test_move_legality_can_select_single_species_candidate(self) -> None:
        payload = build_axis_identity_audit(
            batch_id="test",
            consolidation={"batch_id": "c1", "species_records": [_record(stable_moves=["晒太阳", "超维投射"])]},
            species_options_index={
                "化蝶": [
                    _option("species_a", ["晒太阳", "毒孢子"]),
                    _option("species_b", ["晒太阳", "超维投射"]),
                ]
            },
        )

        report = payload["identity_reports"][0]
        self.assertEqual(report["identity_status"], "candidate_species_by_move_legality")
        self.assertEqual(report["best_species_ids_by_move_coverage"], ["species_b"])
        self.assertEqual(payload["summary"]["blocking_identity_count"], 0)

    def test_pm_confirmed_distinct_forms_upgrade_identity_blocker(self) -> None:
        payload = build_axis_identity_audit(
            batch_id="test",
            consolidation={"batch_id": "c1", "species_records": [_record(species_name="卡瓦重")]},
            species_options_index={
                "卡瓦重": [
                    _option("grass_form", ["晒太阳", "毒孢子"], form="原始形态"),
                    _option("snow_form", ["晒太阳", "毒孢子"], form="地区形态"),
                    _option("sand_form", ["晒太阳"], form="地区形态"),
                ]
            },
            pm_identity_policies={
                "卡瓦重": {
                    "status": "distinct_forms_confirmed_by_pm",
                    "policy": "require_form_resolution_before_set_review",
                    "product_consequence": "Set evidence must bind to a concrete form.",
                }
            },
        )

        report = payload["identity_reports"][0]
        self.assertEqual(report["identity_status"], "blocked_pm_confirmed_distinct_forms")
        self.assertEqual(report["policy_effect"], "upgraded_to_form_resolution_blocker")
        self.assertEqual(payload["summary"]["blocking_identity_count"], 1)
        self.assertIn("PM身份规则=distinct_forms_confirmed_by_pm", render_axis_identity_brief(payload))

    def test_overwide_family_with_axis_signals_requires_core_binding(self) -> None:
        family = {
            "family_id": "family_01",
            "core_moves": ["水刃", "闪击", "疾风连袭", "热身运动", "三连破", "防御"],
            "primary_source_ids": ["s1", "s2", "s3"],
            "alter_variants": [
                {
                    "source_id": "s1",
                    "moves": ["水刃", "闪击", "力量增效"],
                    "roles": ["cleaner"],
                    "damage_axis": "physical",
                    "build_axes": ["speed"],
                    "configuration": {"nature": [{"source_phrase": "开朗"}]},
                },
                {
                    "source_id": "s2",
                    "moves": ["水花四溅", "魔法增效", "防御"],
                    "roles": ["pressure"],
                    "damage_axis": "magical",
                    "build_axes": ["magical"],
                    "configuration": {"nature": [{"source_phrase": "加魔攻"}]},
                },
                {
                    "source_id": "s3",
                    "moves": ["三连破", "热身运动", "乘胜追击"],
                    "roles": ["cleaner"],
                    "damage_axis": "physical",
                    "build_axes": ["physical"],
                    "configuration": {"bloodline": [{"source_phrase": "血脉"}]},
                },
            ],
        }
        payload = build_axis_identity_audit(
            batch_id="test",
            consolidation={"batch_id": "c1", "species_records": [_record(species_name="圣羽翼王", families=[family])]},
            species_options_index={"圣羽翼王": [_option("wingking", ["水刃", "闪击"], form="最终形态")]},
        )

        report = payload["axis_reports"][0]
        self.assertEqual(report["axis_status"], "axis_signal_present_needs_core_binding")
        self.assertEqual(payload["summary"]["axis_blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
