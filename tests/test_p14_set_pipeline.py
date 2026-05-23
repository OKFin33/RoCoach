from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_set_pipeline import run_set_pipeline


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


class P14SetPipelineTests(unittest.TestCase):
    def test_windowed_segments_create_set_and_relation_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foundation = root / "source_a" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "source_a",
                            "title": "毒队讲解",
                            "target_archetype": "毒队 / 星陨队",
                            "target_entities": ["毒队", "星陨"],
                            "ingest_artifacts": {
                                "evidence_foundation_dir": str(foundation),
                            },
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "source": {"title": "毒队讲解"},
                },
            )
            _write_yaml(
                foundation / "quality_gate.yaml",
                {"source_id": "source_a", "segment_count": 4, "claim_atom_count": 0},
            )
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "segments": [
                        {
                            "segment_id": "S0001",
                            "refined_text": "可以选择裘卡作为首发。",
                            "start_ms": 1000,
                            "end_ms": 2000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "裘卡", "kind": "species", "layer": "A"}],
                        },
                        {
                            "segment_id": "S0002",
                            "refined_text": "我们直接点毒孢子。",
                            "start_ms": 2000,
                            "end_ms": 3000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "毒孢子", "kind": "move", "layer": "A"}],
                        },
                        {
                            "segment_id": "S0003",
                            "refined_text": "然后切琉璃水母压制星兔。",
                            "start_ms": 3000,
                            "end_ms": 4000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [
                                {"term": "琉璃水母", "kind": "species", "layer": "A"},
                                {"term": "落陨星兔", "kind": "species", "layer": "A"},
                            ],
                        },
                    ],
                },
            )

            result = run_set_pipeline(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="phase1_test",
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(result["source_count"], 1)
            sets = yaml.safe_load((root / "knowledge_ops/set_candidates/source_a.candidate_sets.yaml").read_text())
            edges = yaml.safe_load((root / "knowledge_ops/relation_candidates/source_a.candidate_edges.yaml").read_text())
            by_species = {item["species_name"]: item for item in sets["candidate_sets"]}

            self.assertEqual(by_species["裘卡"]["state"], "S2_set_candidate")
            self.assertIn("毒孢子", by_species["裘卡"]["selected_moves"])
            self.assertTrue(edges["candidate_edges"])
            packet = (root / "knowledge_ops/review_packets/phase1_test_pm_delta.md").read_text()
            self.assertIn("## 结论", packet)
            self.assertIn("裘卡", packet)

    def test_source_target_species_alias_can_seed_candidate_without_exact_species_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foundation = root / "wingking" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "wingking",
                            "title": "翼王队伍实战讲解",
                            "target_archetype": "翼王队",
                            "target_entities": ["翼王"],
                            "ingest_artifacts": {
                                "evidence_foundation_dir": str(foundation),
                            },
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {"source_id": "wingking", "runtime_allowed": False, "source": {"title": "翼王队伍实战讲解"}},
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "wingking", "segment_count": 2})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "wingking",
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
                            "refined_text": "然后连续点水刃压节奏。",
                            "start_ms": 2000,
                            "end_ms": 3000,
                            "quality_gate": "claim_ready",
                            "ab_hits": [{"term": "水刃", "kind": "move", "layer": "A"}],
                        },
                    ],
                },
            )

            run_set_pipeline(source_queue=root / "source_queue.yaml", out_root=root / "knowledge_ops", batch_id="alias_test")

            sets = yaml.safe_load((root / "knowledge_ops/set_candidates/wingking.candidate_sets.yaml").read_text())
            by_species = {item["species_name"]: item for item in sets["candidate_sets"]}
            self.assertIn("圣羽翼王", by_species)
            self.assertIn("翼王", by_species["圣羽翼王"]["source_aliases_used"])
            self.assertIn("水刃", by_species["圣羽翼王"]["selected_moves"])

    def test_window_candidates_filter_illegal_nearby_moves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "battle_dex.sqlite"
            _write_test_dex(
                db_path,
                {
                    "圣羽翼王": ["水刃"],
                    "帕尔萨斯": ["极限撕裂"],
                },
            )
            foundation = root / "wingking" / "evidence_foundation"
            _write_yaml(
                root / "source_queue.yaml",
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "wingking",
                            "title": "翼王对帕尔讲解",
                            "target_archetype": "翼王队",
                            "target_entities": ["翼王"],
                            "ingest_artifacts": {
                                "evidence_foundation_dir": str(foundation),
                            },
                        }
                    ],
                },
            )
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {"source_id": "wingking", "runtime_allowed": False, "source": {"title": "翼王对帕尔讲解"}},
            )
            _write_yaml(foundation / "quality_gate.yaml", {"source_id": "wingking", "segment_count": 1})
            _write_yaml(
                foundation / "segments.yaml",
                {
                    "source_id": "wingking",
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
                                {"term": "水刃", "kind": "move", "layer": "A"},
                            ],
                        },
                    ],
                },
            )

            run_set_pipeline(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="legality_test",
                db_path=db_path,
            )

            sets = yaml.safe_load((root / "knowledge_ops/set_candidates/wingking.candidate_sets.yaml").read_text())
            by_species = {item["species_name"]: item for item in sets["candidate_sets"]}

            self.assertEqual(by_species["圣羽翼王"]["selected_moves"], ["水刃"])
            self.assertEqual(by_species["圣羽翼王"]["excluded_moves"], [{"move_name": "极限撕裂", "reason": "not_in_species_move_pool"}])
            self.assertEqual(by_species["帕尔萨斯"]["selected_moves"], ["极限撕裂"])
            self.assertEqual(by_species["帕尔萨斯"]["excluded_moves"], [{"move_name": "水刃", "reason": "not_in_species_move_pool"}])

    def test_blackwhite_descriptor_is_cosmetic_not_archetype(self) -> None:
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
                    "source": {"title": "富人区遇到逆天4黑白虫队", "source_type": "matchup_counterplay"},
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

            run_set_pipeline(
                source_queue=root / "source_queue.yaml",
                out_root=root / "knowledge_ops",
                batch_id="blackwhite_test",
                db_path=db_path,
            )

            sets = yaml.safe_load((root / "knowledge_ops/set_candidates/blackwhite.candidate_sets.yaml").read_text())
            candidate = sets["candidate_sets"][0]

            self.assertEqual(candidate["species_name"], "爬爬")
            self.assertEqual(candidate["archetype_tags"], [])
            self.assertEqual(candidate["cosmetic_descriptors"][0]["term"], "黑白")
            self.assertTrue(candidate["cosmetic_descriptors"][0]["not_an_archetype"])
            self.assertIn("cosmetic_descriptor_not_set_axis", candidate["promotion_blockers"])


if __name__ == "__main__":
    unittest.main()
