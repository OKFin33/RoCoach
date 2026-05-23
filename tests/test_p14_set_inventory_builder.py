from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_set_inventory_builder import run_set_inventory_builder


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_test_dex(path: Path, pools: dict[str, list[str]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE species_form (species_id TEXT PRIMARY KEY, display_name TEXT NOT NULL)")
        conn.execute("CREATE TABLE move (move_id TEXT PRIMARY KEY, move_name TEXT NOT NULL)")
        conn.execute("CREATE TABLE species_move_pool (species_id TEXT, move_name_raw TEXT, move_id TEXT)")
        move_ids: dict[str, str] = {}
        for index, move_name in enumerate(sorted({move for moves in pools.values() for move in moves}), start=1):
            move_id = f"move_{index}"
            move_ids[move_name] = move_id
            conn.execute("INSERT INTO move VALUES (?, ?)", (move_id, move_name))
        for index, (species_name, moves) in enumerate(pools.items(), start=1):
            species_id = f"species_{index}"
            conn.execute("INSERT INTO species_form VALUES (?, ?)", (species_id, species_name))
            for move_name in moves:
                conn.execute(
                    "INSERT INTO species_move_pool VALUES (?, ?, ?)",
                    (species_id, move_name, move_ids[move_name]),
                )
        conn.commit()
    finally:
        conn.close()


class P14SetInventoryBuilderTests(unittest.TestCase):
    def test_builds_coverage_records_and_set_dossiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "battle_dex.sqlite"
            _write_test_dex(db_path, {"圣羽翼王": ["水刃", "闪击"], "裘卡": []})
            foundation = root / "source_a" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "source_a",
                            "title": "翼王队伍实战讲解",
                            "target_archetype": "翼王队",
                            "target_entities": ["翼王"],
                            "ingest_artifacts": {"evidence_foundation_dir": str(foundation)},
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "source": {
                        "title": "翼王队伍实战讲解",
                        "url": "https://example.com",
                        "source_type": "team_explainer",
                    },
                },
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "source_a", "segment_count": 4})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "segments": [
                        {
                            "segment_id": "S0001",
                            "refined_text": "这里翼王可以迅捷上场。",
                            "start_ms": 1000,
                            "end_ms": 2000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "迅捷", "kind": "mechanism", "layer": "B"}],
                        },
                        {
                            "segment_id": "S0002",
                            "refined_text": "然后点水刃压节奏。",
                            "start_ms": 2000,
                            "end_ms": 3000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "水刃", "kind": "move", "layer": "A"}],
                        },
                        {
                            "segment_id": "S0003",
                            "refined_text": "这局还带闪击。",
                            "start_ms": 3000,
                            "end_ms": 4000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "闪击", "kind": "move", "layer": "A"}],
                        },
                        {
                            "segment_id": "S0004",
                            "refined_text": "队里也出现裘卡。",
                            "start_ms": 4000,
                            "end_ms": 5000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "裘卡", "kind": "species", "layer": "A"}],
                        },
                    ],
                },
            )

            result = run_set_inventory_builder(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="inventory_test",
                db_path=db_path,
            )

            self.assertFalse(result["runtime_allowed"])
            inventory = yaml.safe_load((root / "knowledge_ops/set_inventory/source_a.source_inventory.yaml").read_text())
            dossiers = {item["species_name"]: item for item in inventory["set_dossiers"]}
            coverage = {item["species_name"]: item for item in inventory["coverage_records"]}

            self.assertIn("圣羽翼王", dossiers)
            self.assertEqual(dossiers["圣羽翼王"]["move_slots"]["completeness"], "partial_2_3_moves")
            self.assertEqual(dossiers["圣羽翼王"]["move_slots"]["known_moves"], ["水刃", "闪击"])
            self.assertIn("翼王", dossiers["圣羽翼王"]["source_aliases_used"])
            self.assertIn("裘卡", coverage)
            packet = (root / "knowledge_ops/review_packets/inventory_test_pm_brief.md").read_text()
            self.assertIn("Set Inventory", packet)
            self.assertIn("圣羽翼王", packet)

    def test_filters_illegal_moves_and_nested_short_move_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "battle_dex.sqlite"
            _write_test_dex(
                db_path,
                {
                    "圣羽翼王": ["水刃", "闪击"],
                    "帕尔萨斯": ["极限撕裂", "撕裂"],
                },
            )
            foundation = root / "source_b" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "source_b",
                            "title": "翼王对帕尔讲解",
                            "target_archetype": "翼王队",
                            "target_entities": ["翼王"],
                            "ingest_artifacts": {"evidence_foundation_dir": str(foundation)},
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "source_b",
                    "runtime_allowed": False,
                    "source": {
                        "title": "翼王对帕尔讲解",
                        "url": "https://example.com",
                        "source_type": "team_explainer",
                    },
                },
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "source_b", "segment_count": 1})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "source_b",
                    "runtime_allowed": False,
                    "segments": [
                        {
                            "segment_id": "S0001",
                            "refined_text": "翼王面对帕尔萨斯的极限撕裂，可以点水刃。",
                            "start_ms": 1000,
                            "end_ms": 2000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [
                                {"term": "帕尔萨斯", "kind": "species", "layer": "A"},
                                {"term": "极限撕裂", "kind": "move", "layer": "A"},
                                {"term": "撕裂", "kind": "move", "layer": "A"},
                                {"term": "水刃", "kind": "move", "layer": "A"},
                            ],
                        }
                    ],
                },
            )

            run_set_inventory_builder(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="inventory_test",
                db_path=db_path,
            )

            inventory = yaml.safe_load((root / "knowledge_ops/set_inventory/source_b.source_inventory.yaml").read_text())
            dossiers = {item["species_name"]: item for item in inventory["set_dossiers"]}

            wingking = dossiers["圣羽翼王"]
            self.assertEqual(wingking["move_slots"]["known_moves"], ["水刃"])
            self.assertEqual(
                wingking["legality_filter"]["excluded_move_counts"],
                {"极限撕裂": 1, "撕裂": 1},
            )
            self.assertEqual(
                {item["move_name"]: item["reason"] for item in wingking["legality_filter"]["excluded_move_mentions"]},
                {
                    "极限撕裂": "not_in_species_move_pool",
                    "撕裂": "overlap_inside_longer_move",
                },
            )

            parr = dossiers["帕尔萨斯"]
            self.assertEqual(parr["move_slots"]["known_moves"], ["极限撕裂"])
            self.assertEqual(parr["legality_filter"]["excluded_move_counts"], {"撕裂": 1, "水刃": 1})

    def test_acquisition_or_unlock_context_does_not_create_set_moves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "battle_dex.sqlite"
            _write_test_dex(db_path, {"龙鱼": ["水刃", "龙吟"], "圣羽翼王": ["水刃", "扇风"]})
            foundation = root / "source_c" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "source_c",
                            "title": "水刃流翼王技能石获取",
                            "target_archetype": "水刃翼王",
                            "target_entities": ["翼王", "龙鱼"],
                            "ingest_artifacts": {"evidence_foundation_dir": str(foundation)},
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "source_c",
                    "runtime_allowed": False,
                    "source": {
                        "title": "水刃流翼王技能石获取",
                        "url": "https://example.com",
                        "source_type": "team_explainer",
                    },
                },
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "source_c", "segment_count": 2})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "source_c",
                    "runtime_allowed": False,
                    "segments": [
                        {
                            "segment_id": "S0001",
                            "refined_text": "这套翼王带水刃和扇风。",
                            "start_ms": 1000,
                            "end_ms": 2000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [
                                {"term": "翼王", "kind": "species", "layer": "A", "canonical": "圣羽翼王"},
                                {"term": "水刃", "kind": "move", "layer": "A"},
                                {"term": "扇风", "kind": "move", "layer": "A"},
                            ],
                        },
                        {
                            "segment_id": "S0002",
                            "refined_text": "然后来到右边水域抓取龙鱼，并且让龙鱼在战斗中使用两次水刃就能解锁图鉴获得技能石。",
                            "start_ms": 2000,
                            "end_ms": 3000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [
                                {"term": "龙鱼", "kind": "species", "layer": "A"},
                                {"term": "水刃", "kind": "move", "layer": "A"},
                            ],
                        },
                    ],
                },
            )

            run_set_inventory_builder(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="inventory_test",
                db_path=db_path,
            )

            inventory = yaml.safe_load((root / "knowledge_ops/set_inventory/source_c.source_inventory.yaml").read_text())
            dossiers = {item["species_name"]: item for item in inventory["set_dossiers"]}
            coverage = {item["species_name"]: item for item in inventory["coverage_records"]}

            self.assertEqual(dossiers["圣羽翼王"]["move_slots"]["known_moves"], ["水刃", "扇风"])
            self.assertNotIn("龙鱼", dossiers)
            self.assertIn("龙鱼", coverage)
            self.assertEqual(coverage["龙鱼"]["legality_filter"]["acquisition_context_ref_count"], 1)

    def test_blackwhite_source_title_is_cosmetic_descriptor_not_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "battle_dex.sqlite"
            _write_test_dex(db_path, {"爬爬": ["引燃"]})
            foundation = root / "blackwhite" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "blackwhite",
                            "title": "富人区遇到逆天4黑白虫队",
                            "target_archetype": "富人区遇到逆天4黑白虫队",
                            "target_entities": [],
                            "ingest_artifacts": {"evidence_foundation_dir": str(foundation)},
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "blackwhite",
                    "runtime_allowed": False,
                    "source": {
                        "title": "富人区遇到逆天4黑白虫队",
                        "url": "https://example.com",
                        "source_type": "matchup_counterplay",
                    },
                },
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "blackwhite", "segment_count": 1})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "blackwhite",
                    "runtime_allowed": False,
                    "segments": [
                        {
                            "segment_id": "S0001",
                            "refined_text": "黑白爬爬引燃的呃。",
                            "start_ms": 1000,
                            "end_ms": 2000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [
                                {"term": "爬爬", "kind": "species", "layer": "A"},
                                {"term": "引燃", "kind": "move", "layer": "A"},
                            ],
                        }
                    ],
                },
            )

            run_set_inventory_builder(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="inventory_blackwhite",
                db_path=db_path,
            )

            inventory = yaml.safe_load((root / "knowledge_ops/set_inventory/blackwhite.source_inventory.yaml").read_text())
            source = inventory["source"]
            dossier = inventory["set_dossiers"][0]

            self.assertEqual(source["source_descriptors"][0]["term"], "黑白")
            self.assertFalse(source["target_archetype_normalization"]["usable_as_archetype"])
            self.assertEqual(dossier["cosmetic_descriptors"][0]["term"], "黑白")
            self.assertEqual(dossier["archetype_tags"], [])
            self.assertIn("cosmetic_descriptor_not_set_axis", dossier["promotion_blockers"])


if __name__ == "__main__":
    unittest.main()
