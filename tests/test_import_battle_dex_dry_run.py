from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.export_manual_battle_data_supplement import build_payload
from tools.import_battle_dex_dry_run import ArtifactWriter, parse_manual_supplement, parse_manual_supplement_markdown, run_importer_dry_run
from tools.validate_p1e_importer_artifacts import validate_artifacts


class ImportBattleDexDryRunTests(unittest.TestCase):
    def test_parse_manual_supplement_extracts_expected_records_from_markdown(self) -> None:
        supplement = parse_manual_supplement(
            Path("/Users/okfin3/project/GitHub/OKFin33/Roco/docs/research/manual_battle_data_supplement_2026-04-14.md")
        )
        self.assertIn("炽心勇狮（悲鸣的样子）", supplement.excluded_forms)
        self.assertIn("species_3d2f11185009b67c", supplement.species_canonical_overrides)
        self.assertEqual(
            supplement.species_canonical_overrides["species_ec83c314cf3ed3eb"].override_ability_effect_text,
            "队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+15%。",
        )
        self.assertEqual(
            supplement.species_canonical_overrides["species_ec83c314cf3ed3eb"].override_ability_name,
            "虫群突袭",
        )
        self.assertEqual(
            supplement.species_canonical_overrides["species_62289c78a3b186dc"].override_ability_name,
            "虫群鼓舞",
        )
        self.assertNotIn("湿润印记", supplement.manual_moves)
        self.assertEqual(supplement.manual_moves["溶解液"].move_type, "毒")
        self.assertEqual(
            supplement.ability_text_overrides["溶解扩散"],
            "每携带1个毒系技能，水系技能使敌方中毒+1层。",
        )
        self.assertEqual(supplement.move_aliases["湿润印记"], "打湿")

    def test_parse_manual_supplement_extracts_expected_records_from_structured_yaml(self) -> None:
        supplement = parse_manual_supplement(
            Path("/Users/okfin3/project/GitHub/OKFin33/Roco/data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml")
        )
        self.assertIn("卡瓦重（火山附近的样子）", supplement.excluded_forms)
        self.assertEqual(
            supplement.species_canonical_overrides["species_3d2f11185009b67c"].preferred_source_page_id,
            "source_bc1c2be5441bb830",
        )
        self.assertEqual(
            supplement.species_canonical_overrides["species_62289c78a3b186dc"].override_ability_name,
            "虫群鼓舞",
        )
        self.assertNotIn("湿润印记", supplement.manual_moves)
        self.assertEqual(supplement.move_aliases["湿润印记"], "打湿")
        self.assertIn("current manual-verified baseline resolves conflicting wiki-derived effect texts", build_payload(
            Path("/Users/okfin3/project/GitHub/OKFin33/Roco/docs/research/manual_battle_data_supplement_2026-04-14.md")
        )["ability_text_overrides"][0]["notes"])

    def test_export_payload_stays_aligned_with_markdown_parser(self) -> None:
        markdown_path = Path("/Users/okfin3/project/GitHub/OKFin33/Roco/docs/research/manual_battle_data_supplement_2026-04-14.md")
        parsed = parse_manual_supplement_markdown(markdown_path)
        payload = build_payload(markdown_path)
        self.assertEqual(sorted(parsed.excluded_forms), sorted(row["display_name"] for row in payload["exclusions"]["species_forms"]))
        self.assertEqual(
            parsed.species_canonical_overrides["species_3d2f11185009b67c"].preferred_source_page_id,
            payload["species_canonical_overrides"][0]["preferred_source_page_id"],
        )
        self.assertEqual(sorted(parsed.manual_moves), sorted(row["move_name"] for row in payload["manual_moves"]))
        self.assertEqual(
            parsed.move_aliases["湿润印记"],
            next(row["target_move_name"] for row in payload["move_aliases"] if row["source_move_name"] == "湿润印记"),
        )
        self.assertEqual(
            parsed.ability_text_overrides["溶解扩散"],
            next(row["override_text"] for row in payload["ability_text_overrides"] if row["ability_name"] == "溶解扩散"),
        )

    def test_run_importer_dry_run_emits_contract_valid_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical_dir = root / "canonical"
            writer = ArtifactWriter(canonical_dir)
            writer.write_json(
                "run_manifest.json",
                {
                    "run_id": "canonical_test",
                    "status": "completed_with_warnings",
                },
            )
            writer.write_jsonl(
                "source_pages.jsonl",
                [
                    {
                        "source_page_id": "source_hidden",
                        "page_title": "炽心勇狮（悲鸣的样子）",
                        "page_url": "https://example.test/hidden",
                    },
                    {
                        "source_page_id": "source_species",
                        "page_title": "普通精灵",
                        "page_url": "https://example.test/species",
                    },
                    {
                        "source_page_id": "source_review",
                        "page_title": "待审精灵",
                        "page_url": "https://example.test/review",
                    },
                    {
                        "source_page_id": "source_dup_old",
                        "page_title": "权杖-V",
                        "page_url": "https://example.test/staff-old",
                    },
                    {
                        "source_page_id": "source_bc1c2be5441bb830",
                        "page_title": "权杖-Ⅴ",
                        "page_url": "https://example.test/staff-new",
                    },
                    {
                        "source_page_id": "source_qb",
                        "page_title": "女王蜂",
                        "page_url": "https://example.test/queen-bee",
                    },
                    {
                        "source_page_id": "source_hkfh",
                        "page_title": "花魁蜂后",
                        "page_url": "https://example.test/flower-queen",
                    },
                ],
            )
            writer.write_jsonl(
                "species_form_candidates.jsonl",
                [
                    {
                        "species_id": "species_ok",
                        "source_page_id": "source_species",
                        "display_name": "普通精灵",
                        "ability_name": None,
                        "ability_effect_text": None,
                        "base_stats": {"生命": 1, "物攻": 1, "魔攻": 1, "物防": 1, "魔防": 1, "速度": 1},
                    },
                    {
                        "species_id": "species_3d2f11185009b67c",
                        "source_page_id": "source_dup_old",
                        "display_name": "权杖-V",
                        "evolution_stage": "II阶",
                        "initial_species_name": "权杖-II",
                        "ability_name": "机械变式",
                        "ability_effect_text": "自己携带的技能每回合位置变化时,该技能能耗-1。",
                        "base_stats": {"生命": 103, "物攻": 105, "魔攻": 97, "物防": 136, "魔防": 136, "速度": 75},
                        "normalization_warnings": [],
                    },
                    {
                        "species_id": "species_3d2f11185009b67c",
                        "source_page_id": "source_bc1c2be5441bb830",
                        "display_name": "权杖-V",
                        "evolution_stage": "最终形态",
                        "initial_species_name": "权杖-II",
                        "ability_name": "机械变式",
                        "ability_effect_text": "自己携带的技能每回合位置变化时,该技能能耗-1。",
                        "base_stats": {"生命": 103, "物攻": 105, "魔攻": 97, "物防": 136, "魔防": 136, "速度": 75},
                        "normalization_warnings": [],
                    },
                    {
                        "species_id": "species_ec83c314cf3ed3eb",
                        "source_page_id": "source_qb",
                        "display_name": "女王蜂",
                        "evolution_stage": "最终形态",
                        "initial_species_name": "一窝蜂",
                        "ability_name": "虫群鼓舞",
                        "ability_effect_text": "队伍中每有1只其他的虫系精灵,自己入场时获得攻防速+10%。",
                        "base_stats": {"生命": 145, "物攻": 50, "魔攻": 45, "物防": 42, "魔防": 42, "速度": 40},
                        "normalization_warnings": [],
                    },
                    {
                        "species_id": "species_62289c78a3b186dc",
                        "source_page_id": "source_hkfh",
                        "display_name": "花魁蜂后",
                        "evolution_stage": "最终形态",
                        "initial_species_name": "一窝蜂",
                        "ability_name": "虫群突袭",
                        "ability_effect_text": "队伍中每有1只其他的虫系精灵,自己入场时获得攻防速+15%。",
                        "base_stats": {"生命": 145, "物攻": 54, "魔攻": 49, "物防": 45, "魔防": 45, "速度": 44},
                        "normalization_warnings": [],
                    },
                ],
            )
            writer.write_jsonl(
                "move_candidates.jsonl",
                [
                    {
                        "move_id": "move_existing",
                        "move_name": "已有技能",
                        "source_page_id": "source_move",
                    },
                    {
                        "move_id": "move_dashi",
                        "move_name": "打湿",
                        "source_page_id": "source_move_dashi",
                    },
                ],
            )
            writer.write_jsonl(
                "derived_ability_candidates.jsonl",
                [
                    {
                        "ability_id": "ability_conflict_a",
                        "ability_name": "溶解扩散",
                        "effect_text": "冲突A",
                        "source_page_ids": ["source_species"],
                        "source_species_ids": ["species_ok"],
                        "derivation_status": "conflict_review_required",
                    },
                    {
                        "ability_id": "ability_conflict_b",
                        "ability_name": "溶解扩散",
                        "effect_text": "冲突B",
                        "source_page_ids": ["source_species"],
                        "source_species_ids": ["species_ok"],
                        "derivation_status": "conflict_review_required",
                    },
                ],
            )
            writer.write_jsonl(
                "species_move_pool_candidates.jsonl",
                [
                    {
                        "species_id": "species_ok",
                        "move_name_raw": "龙之舞",
                        "move_id": None,
                        "access_channel": "level_up",
                        "source_page_id": "source_species",
                    },
                    {
                        "species_id": "species_ok",
                        "move_name_raw": "湿润印记",
                        "move_id": None,
                        "access_channel": "level_up",
                        "source_page_id": "source_species",
                    }
                ],
            )
            writer.write_jsonl(
                "validation_events.jsonl",
                [
                    {
                        "severity": "hard_reject",
                        "entity_type": "species",
                        "source_page_id": "source_hidden",
                    },
                    {
                        "severity": "hard_reject",
                        "entity_type": "species",
                        "source_page_id": "source_review",
                    },
                ],
            )

            class Args:
                canonical_artifact_dir = canonical_dir
                supplement_path = Path("/Users/okfin3/project/GitHub/OKFin33/Roco/data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml")
                output_dir = root / "output"
                run_id = "importer_test"

            run_importer_dry_run(Args())
            result = validate_artifacts(Args.output_dir)
            self.assertEqual(result["policy_mode"], "policy_b")

            resolved_moves = [
                json.loads(line)
                for line in (Args.output_dir / "resolved_moves.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(row["move_name"] == "龙之舞" and row["resolution_status"] == "supplement_backed" for row in resolved_moves))

            excluded = [
                json.loads(line)
                for line in (Args.output_dir / "excluded_entities.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(row["display_name"] == "炽心勇狮（悲鸣的样子）" for row in excluded))

            resolved_species = [
                json.loads(line)
                for line in (Args.output_dir / "resolved_species_forms.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertFalse(any(row["display_name"] == "炽心勇狮（悲鸣的样子）" for row in resolved_species))
            self.assertTrue(
                any(
                    row["display_name"] == "权杖-V"
                    and row["resolution_status"] == "supplement_backed"
                    and row["evolution_stage"] == "最终形态"
                    for row in resolved_species
                )
            )
            self.assertTrue(
                any(
                    row["display_name"] == "女王蜂"
                    and row["resolution_status"] == "supplement_backed"
                    and row["ability_name"] == "虫群突袭"
                    and row["ability_effect_text"] == "队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+15%。"
                    for row in resolved_species
                )
            )
            self.assertTrue(
                any(
                    row["display_name"] == "花魁蜂后"
                    and row["resolution_status"] == "supplement_backed"
                    and row["ability_name"] == "虫群鼓舞"
                    and row["ability_effect_text"] == "队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+10%。"
                    for row in resolved_species
                )
            )

            review_required = [
                json.loads(line)
                for line in (Args.output_dir / "review_required_entities.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(row["display_name"] == "待审精灵" for row in review_required))
            self.assertFalse(any(row["entity_key"] == "species_3d2f11185009b67c" for row in review_required))

            abilities = [
                json.loads(line)
                for line in (Args.output_dir / "resolved_derived_abilities.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(row["ability_name"] == "溶解扩散" and row["resolution_status"] == "supplement_backed" for row in abilities))
            unresolved = [
                json.loads(line)
                for line in (Args.output_dir / "unresolved_entities.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertFalse(any(row.get("move_name_raw") == "湿润印记" for row in unresolved))
            self.assertTrue(
                any(
                    row["ability_name"] == "虫群鼓舞"
                    and row["effect_text"] == "队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+10%。"
                    and row["resolution_status"] == "supplement_backed"
                    for row in abilities
                )
            )
            self.assertTrue(
                any(
                    row["ability_name"] == "虫群突袭"
                    and row["effect_text"] == "队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+15%。"
                    and row["resolution_status"] == "supplement_backed"
                    for row in abilities
                )
            )


if __name__ == "__main__":
    unittest.main()
