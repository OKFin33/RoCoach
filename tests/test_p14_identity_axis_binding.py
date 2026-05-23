from __future__ import annotations

import unittest

from tools.p14_identity_axis_binding import build_identity_axis_binding, render_identity_axis_brief


def _option(species_id: str, moves: list[str], *, regional: str) -> dict[str, object]:
    return {
        "species_id": species_id,
        "form_name": "地区形态",
        "regional_form_name": regional,
        "available_moves": moves,
    }


def _variant(source_id: str, moves: list[str], **kwargs: object) -> dict[str, object]:
    return {
        "source_id": source_id,
        "moves": moves,
        "roles": kwargs.get("roles", []),
        "damage_axis": kwargs.get("damage_axis", "physical"),
        "build_axes": kwargs.get("build_axes", []),
        "configuration": kwargs.get("configuration", {}),
    }


def _record(species_name: str, variants: list[dict[str, object]]) -> dict[str, object]:
    return {
        "species_name": species_name,
        "state": "split_blocked",
        "set_family_candidates": [
            {
                "family_id": "family_01",
                "core_moves": ["偷袭", "先发制人", "吓退", "电弧"],
                "primary_source_count": len(variants),
                "alter_variants": variants,
            }
        ],
    }


class P14IdentityAxisBindingTests(unittest.TestCase):
    def test_distinct_form_policy_binds_unique_move_legal_form(self) -> None:
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={
                "batch_id": "c1",
                "source_quality": {"s1": {"title": "雪山卡瓦重配置"}},
                "species_records": [_record("卡瓦重", [_variant("s1", ["冰雹", "速冻"])])],
            },
            species_options_index={
                "卡瓦重": [
                    _option("grass", ["晒太阳"], regional="草地附近的样子"),
                    _option("snow", ["冰雹", "速冻"], regional="雪山附近的样子"),
                ]
            },
            pm_identity_policies={
                "卡瓦重": {"policy": "require_form_resolution_before_set_review"}
            },
            target_species=["卡瓦重"],
        )

        report = payload["form_reports"][0]
        self.assertEqual(report["concrete_form_bound_source_count"], 1)
        self.assertEqual(report["source_bindings"][0]["form_binding_status"], "form_bound_by_title_and_move_legality")
        self.assertEqual(report["concrete_form_counts"], {"雪山附近的样子": 1})

    def test_multiple_legal_forms_count_as_unresolved_for_distinct_forms(self) -> None:
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={
                "batch_id": "c1",
                "source_quality": {},
                "species_records": [_record("卡瓦重", [_variant("s1", ["防御"])])],
            },
            species_options_index={
                "卡瓦重": [
                    _option("grass", ["防御"], regional="草地附近的样子"),
                    _option("snow", ["防御"], regional="雪山附近的样子"),
                ]
            },
            pm_identity_policies={
                "卡瓦重": {"policy": "require_form_resolution_before_set_review"}
            },
            target_species=["卡瓦重"],
        )

        report = payload["form_reports"][0]
        self.assertEqual(report["source_bindings"][0]["form_binding_status"], "form_ambiguous_multiple_legal_forms")
        self.assertEqual(report["unresolved_form_source_count"], 1)
        self.assertEqual(payload["summary"]["distinct_form_unresolved_source_count"], 1)

    def test_cosmetic_form_policy_does_not_split_by_form(self) -> None:
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={
                "batch_id": "c1",
                "source_quality": {},
                "species_records": [_record("化蝶", [_variant("s1", ["晒太阳"])])],
            },
            species_options_index={"化蝶": [_option("a", ["晒太阳"], regional="平常的样子"), _option("b", ["晒太阳"], regional="奇丽花的样子")]},
            pm_identity_policies={
                "化蝶": {"policy": "do_not_assume_battle_distinct_forms_without_source_evidence"}
            },
            target_species=["化蝶"],
        )

        report = payload["form_reports"][0]
        self.assertEqual(report["report_status"], "form_split_not_assumed")
        self.assertEqual(
            report["source_bindings"][0]["form_binding_status"],
            "form_not_split_without_source_backed_battle_difference",
        )

    def test_shared_core_with_divergent_flex_axes_is_axis_candidate(self) -> None:
        variants = [
            _variant("a", ["偷袭", "先发制人", "吓退"], roles=["defensive_pivot"], build_axes=["speed"]),
            _variant("b", ["偷袭", "先发制人", "吓退"], roles=["defensive_pivot"], build_axes=["speed"]),
            _variant("c", ["偷袭", "先发制人", "电弧"], roles=["lead"], build_axes=["physical"]),
            _variant("d", ["偷袭", "先发制人", "电弧"], roles=["lead"], build_axes=["physical"]),
        ]
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={"batch_id": "c1", "source_quality": {}, "species_records": [_record("寂灭骨龙", variants)]},
            species_options_index={},
            pm_identity_policies={},
            target_species=["寂灭骨龙"],
        )

        self.assertEqual(payload["summary"]["axis_candidate_count"], 1)
        pivot = payload["axis_reports"][0]["family_reports"][0]["pair_pivots"][0]
        self.assertEqual(pivot["shared_core_moves"], ["偷袭", "先发制人"])
        self.assertEqual(pivot["pivot_status"], "shared_core_axis_candidate")
        self.assertIn("shared_core=偷袭 / 先发制人", render_identity_axis_brief(payload))

    def test_bonedragon_build_specific_axis_branch_gate(self) -> None:
        variants = [
            _variant(
                "bulk_a",
                ["吓退", "报复", "先发制人"],
                roles=["defensive_pivot"],
                configuration={
                    "nature": [
                        {
                            "source_phrase": "性格",
                            "evidence": {"quote": "分为联防生命寂灭骨龙 生命物防魔防依靠坦度硬防致命伤害"},
                        }
                    ]
                },
            ),
            _variant(
                "bulk_b",
                ["吓退", "报复", "先发制人"],
                roles=["defensive_pivot"],
                configuration={
                    "nature": [
                        {
                            "source_phrase": "性格",
                            "evidence": {"quote": "平和加生命走坦度流 以消耗对方能量为目的"},
                        }
                    ]
                },
            ),
            _variant(
                "pressure_a",
                ["偷袭", "电弧", "先发制人"],
                roles=["pressure"],
                build_axes=["physical"],
                configuration={
                    "nature": [
                        {
                            "source_phrase": "性格",
                            "evidence": {"quote": "压制输出寂灭骨龙 固执性格走物攻流"},
                        }
                    ]
                },
            ),
            _variant(
                "pressure_b",
                ["偷袭", "电弧", "先发制人"],
                roles=["lead"],
                build_axes=["physical"],
                configuration={
                    "nature": [
                        {
                            "source_phrase": "性格",
                            "evidence": {"quote": "高物攻的寂灭骨龙带电弧偷袭 弥补输出"},
                        }
                    ]
                },
            ),
        ]
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={"batch_id": "c1", "source_quality": {}, "species_records": [_record("寂灭骨龙", variants)]},
            species_options_index={},
            pm_identity_policies={},
            target_species=["寂灭骨龙"],
        )

        self.assertEqual(payload["summary"]["axis_branch_candidate_count"], 1)
        self.assertEqual(payload["summary"]["recommended_next_action"], "build_pm_axis_branch_review_packet")
        candidate = payload["axis_reports"][0]["axis_branch_candidates"][0]
        self.assertEqual(candidate["status"], "candidate_for_pm_axis_branch_review")
        self.assertIn("axis_branch=bulk_defensive_vs_physical_pressure", render_identity_axis_brief(payload))

    def test_explicit_target_species_does_not_pull_policy_species(self) -> None:
        payload = build_identity_axis_binding(
            batch_id="test",
            consolidation={
                "batch_id": "c1",
                "source_quality": {},
                "species_records": [
                    _record("卡瓦重", [_variant("k1", ["防御"])]),
                    _record("寂灭骨龙", [_variant("b1", ["偷袭", "电弧", "先发制人"], build_axes=["physical"])]),
                ],
            },
            species_options_index={
                "卡瓦重": [
                    _option("grass", ["防御"], regional="草地附近的样子"),
                    _option("snow", ["防御"], regional="雪山附近的样子"),
                ]
            },
            pm_identity_policies={
                "卡瓦重": {"policy": "require_form_resolution_before_set_review"}
            },
            target_species=["寂灭骨龙"],
        )

        self.assertEqual(payload["summary"]["distinct_form_unresolved_source_count"], 0)
        self.assertEqual(payload["policy"]["target_species"], ["寂灭骨龙"])


if __name__ == "__main__":
    unittest.main()
