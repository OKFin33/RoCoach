from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_set_inventory_consolidator import run_set_inventory_consolidator


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _inventory(
    *,
    source_id: str,
    source_type: str = "team_explainer",
    low_confidence_use: str = "",
    dossiers: list[dict[str, object]] | None = None,
    coverage: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "p14.set_inventory.v0",
        "source_id": source_id,
        "generated_at": "2026-05-18",
        "runtime_allowed": False,
        "source": {
            "title": source_id,
            "source_type": source_type,
            "low_confidence_use": low_confidence_use,
        },
        "coverage_records": [
            {
                "species_name": species_name,
                "runtime_allowed": False,
                "status": "coverage_only",
                "evidence_refs": [],
            }
            for species_name in (coverage or [])
        ],
        "set_dossiers": dossiers or [],
        "summary": {},
    }


def _config_signal(phrase: str) -> dict[str, object]:
    return {"source_phrase": phrase, "evidence": {}}


def _dossier(
    species_name: str,
    moves: list[str],
    *,
    roles: list[str] | None = None,
    configuration: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "species_name": species_name,
        "runtime_allowed": False,
        "move_slots": {
            "known_moves": moves,
            "known_move_count": len(moves),
            "completeness": "partial_2_3_moves" if len(moves) >= 2 else "single_move_signal",
        },
        "configuration": configuration or {},
        "tactical_context": {"roles": roles or []},
        "legality_filter": {"excluded_move_counts": {}},
        "mention_count": 3,
    }


class P14SetInventoryConsolidatorTests(unittest.TestCase):
    def test_consolidates_repeated_moves_across_primary_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(source_id="source_a", dossiers=[_dossier("圣羽翼王", ["水刃", "闪击"])]),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(source_id="source_b", dossiers=[_dossier("圣羽翼王", ["水刃", "光之矛"])]),
            )

            result = run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            self.assertFalse(result["runtime_allowed"])
            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["species_name"], "圣羽翼王")
            self.assertEqual(record["state"], "emerging")
            self.assertEqual(record["stable_moves"], ["水刃"])
            self.assertEqual(record["primary_source_count"], 2)
            self.assertEqual(record["suggested_next_action"], "add_targeted_sources_until_repeated_move_skeleton_emerges")
            self.assertEqual(record["set_family_summary"]["family_count"], 1)
            self.assertEqual(record["set_family_candidates"][0]["core_moves"], ["水刃"])
            self.assertEqual(set(record["set_family_candidates"][0]["flex_moves"]), {"闪击", "光之矛"})
            brief = (root / "knowledge_ops/review_packets/consolidation_test_pm_brief.md").read_text()
            self.assertIn("源越多", brief)
            self.assertIn("圣羽翼王", brief)

    def test_low_confidence_source_is_supporting_not_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(source_id="source_a", dossiers=[_dossier("帕尔萨斯", ["极限撕裂", "防御"])]),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(
                    source_id="source_b",
                    low_confidence_use="cross_source_confirmation_only_not_primary_promotion_evidence",
                    dossiers=[_dossier("帕尔萨斯", ["防御", "先发制人"])],
                ),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["primary_source_count"], 1)
            self.assertEqual(record["supporting_source_count"], 1)
            self.assertEqual(record["stable_moves"], ["防御"])
            self.assertIn("insufficient_primary_source_repetition", record["promotion_blockers"])

    def test_skill_substitution_stays_inside_one_set_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(source_id="source_a", dossiers=[_dossier("恶魔狼", ["核心A", "核心B", "可选C", "可选D"])]),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(source_id="source_b", dossiers=[_dossier("恶魔狼", ["核心A", "核心B", "可选E", "可选F"])]),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["set_family_summary"]["decision"], "same_family_or_insufficient_split_evidence")
            self.assertEqual(record["set_family_summary"]["family_count"], 1)
            self.assertEqual(record["set_family_candidates"][0]["core_moves"], ["核心A", "核心B"])
            self.assertEqual(record["split_hypotheses"], [])

    def test_overwide_repeated_move_pool_blocks_family_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(source_id="source_a", dossiers=[_dossier("海豹船长", ["水刃", "防御", "一拳"])]),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(source_id="source_b", dossiers=[_dossier("海豹船长", ["水刃", "防御", "听桥"])]),
            )
            _write_yaml(
                inventory_dir / "source_c.source_inventory.yaml",
                _inventory(source_id="source_c", dossiers=[_dossier("海豹船长", ["水刃", "一拳", "斩断"])]),
            )
            _write_yaml(
                inventory_dir / "source_d.source_inventory.yaml",
                _inventory(source_id="source_d", dossiers=[_dossier("海豹船长", ["水刃", "听桥", "斩断", "泡沫幻影"])]),
            )
            _write_yaml(
                inventory_dir / "source_e.source_inventory.yaml",
                _inventory(source_id="source_e", dossiers=[_dossier("海豹船长", ["水刃", "防御", "泡沫幻影"])]),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["species_name"], "海豹船长")
            self.assertEqual(record["state"], "split_blocked")
            self.assertGreater(len(record["stable_moves"]), 4)
            self.assertTrue(record["set_family_summary"]["overwide_move_pool_blocked"])
            self.assertEqual(record["family_review_candidates"], [])
            self.assertIn("overwide_move_pool_needs_reclustering", record["promotion_blockers"])
            self.assertEqual(record["suggested_next_action"], "recluster_overwide_move_pool_before_reviewer_packet")

    def test_single_full_source_plus_single_move_echoes_does_not_create_family_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(source_id="source_a", dossiers=[_dossier("音速犬", ["防御", "力量增效", "闪光冲击"])]),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(source_id="source_b", dossiers=[_dossier("音速犬", ["防御"])]),
            )
            _write_yaml(
                inventory_dir / "source_c.source_inventory.yaml",
                _inventory(source_id="source_c", dossiers=[_dossier("音速犬", ["力量增效"])]),
            )
            _write_yaml(
                inventory_dir / "source_d.source_inventory.yaml",
                _inventory(source_id="source_d", dossiers=[_dossier("音速犬", ["闪光冲击"])]),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            family = record["set_family_candidates"][0]
            self.assertEqual(family["core_moves"], ["防御", "力量增效", "闪光冲击"])
            self.assertEqual(family["core_cooccurrence_primary_source_count"], 1)
            self.assertEqual(record["family_review_candidates"], [])

    def test_build_axis_conflict_creates_split_hypothesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(
                    source_id="source_a",
                    dossiers=[
                        _dossier(
                            "圣羽翼王",
                            ["水刃", "闪击", "力量增效"],
                            configuration={"nature": [_config_signal("物攻性格")]},
                        )
                    ],
                ),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(
                    source_id="source_b",
                    dossiers=[
                        _dossier(
                            "圣羽翼王",
                            ["魔法增效", "回旋风暴", "三连破"],
                            configuration={"nature": [_config_signal("魔攻性格")]},
                        )
                    ],
                ),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["state"], "split_blocked")
            self.assertEqual(record["set_family_summary"]["decision"], "split_hypothesis")
            self.assertEqual(record["set_family_summary"]["family_count"], 2)
            self.assertEqual(record["family_review_candidates"], [])
            self.assertIn("same_species_set_family_split_unresolved", record["promotion_blockers"])
            self.assertIn("not_review_candidate", record["promotion_blockers"])
            self.assertIn("configuration_axis_divergence", record["split_hypotheses"][0]["reason_codes"])
            self.assertEqual(record["suggested_next_action"], "resolve_same_species_set_family_split_before_reviewer_packet")

    def test_split_hypothesis_blocks_review_candidate_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_dir = root / "set_inventory"
            _write_yaml(
                inventory_dir / "source_a.source_inventory.yaml",
                _inventory(
                    source_id="source_a",
                    dossiers=[_dossier("圣羽翼王", ["水刃", "闪击", "力量增效"])],
                ),
            )
            _write_yaml(
                inventory_dir / "source_b.source_inventory.yaml",
                _inventory(
                    source_id="source_b",
                    dossiers=[_dossier("圣羽翼王", ["水刃", "闪击", "力量增效"])],
                ),
            )
            _write_yaml(
                inventory_dir / "source_c.source_inventory.yaml",
                _inventory(
                    source_id="source_c",
                    dossiers=[
                        _dossier(
                            "圣羽翼王",
                            ["魔法增效", "回旋风暴", "三连破"],
                            configuration={"nature": [_config_signal("魔攻性格")]},
                        )
                    ],
                ),
            )

            run_set_inventory_consolidator(
                inventory_dir=inventory_dir,
                out_root=root / "knowledge_ops",
                batch_id="consolidation_test",
            )

            payload = yaml.safe_load((root / "knowledge_ops/set_inventory_consolidation/consolidation_test.yaml").read_text())
            record = payload["species_records"][0]
            self.assertEqual(record["state"], "split_blocked")
            self.assertEqual(payload["summary"]["review_candidate_count"], 0)
            self.assertEqual(payload["summary"]["split_blocked_count"], 1)
            self.assertEqual(payload["summary"]["family_review_candidate_count"], 1)
            self.assertEqual(set(record["stable_moves"]), {"水刃", "闪击", "力量增效"})
            self.assertEqual(record["suggested_next_action"], "build_family_level_reviewer_packet_keep_species_split_blocked")
            self.assertEqual(len(record["family_review_candidates"]), 1)
            family_candidate = record["family_review_candidates"][0]
            self.assertEqual(family_candidate["review_scope"], "set_family")
            self.assertEqual(family_candidate["species_name"], "圣羽翼王")
            self.assertEqual(set(family_candidate["core_moves"]), {"水刃", "闪击", "力量增效"})
            self.assertEqual(family_candidate["primary_source_count"], 2)
            self.assertEqual(
                family_candidate["promotion_boundary"],
                "family_only_species_level_card_remains_blocked_if_split_hypotheses_exist",
            )
            brief = (root / "knowledge_ops/review_packets/consolidation_test_pm_brief.md").read_text()
            self.assertIn("可先做 family-level review", brief)
            self.assertIn("物种级仍 split_blocked", brief)
            family_packet = (root / "knowledge_ops/review_packets/consolidation_test_family_review.md").read_text()
            self.assertIn("这不是 runtime promotion", family_packet)
            self.assertIn("水刃 / 闪击 / 力量增效", family_packet)
            self.assertIn("不是 `圣羽翼王` 总卡", family_packet)
            self.assertNotIn("魔攻线是否继续补源", family_packet)
            self.assertNotIn("`光之矛` 是否只作为 flex", family_packet)


if __name__ == "__main__":
    unittest.main()
