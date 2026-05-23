from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_source_gap_fill import run_source_gap_fill


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class P14SourceGapFillTests(unittest.TestCase):
    def test_ranks_next_sources_by_mission_gaps_and_skips_processed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            mission_board = root / "mission_board.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "processed_starfall",
                            "title": "星陨机制讲解",
                            "source_type": "mechanism_tutorial",
                            "target_archetype": "星陨帕尔体系",
                            "target_entities": ["星陨", "帕尔"],
                            "priority": "high",
                            "expected_value": "high",
                            "ingest_status": "set_pipeline_processed",
                        },
                        {
                            "source_id": "wingking_best",
                            "url": "https://example.com/wing",
                            "title": "翼王队伍一图流与实战",
                            "source_type": "team_explainer",
                            "target_archetype": "翼王队",
                            "target_entities": ["翼王"],
                            "priority": "high",
                            "expected_value": "high",
                            "ingest_status": "queued",
                        },
                        {
                            "source_id": "sandstorm_fighting",
                            "url": "https://example.com/sand",
                            "title": "面对沙暴格斗的思路",
                            "source_type": "matchup_counterplay",
                            "target_archetype": "沙暴格斗",
                            "target_entities": ["沙暴", "格斗"],
                            "priority": "high",
                            "expected_value": "high",
                            "ingest_status": "queued",
                        },
                        {
                            "source_id": "starfall_intro",
                            "url": "https://example.com/star",
                            "title": "简单聊一下星陨队的思路",
                            "source_type": "gameplay_replay",
                            "target_archetype": "星陨队",
                            "target_entities": ["星陨"],
                            "priority": "medium",
                            "expected_value": "medium",
                            "ingest_status": "queued",
                            "source_quality_prior": {
                                "likely_noise": "high",
                                "promotion_bias": ["self_declared_newbie"],
                            },
                        },
                        {
                            "source_id": "generic_speed",
                            "url": "https://example.com/speed",
                            "title": "速度线与词条解释",
                            "source_type": "mechanism_tutorial",
                            "target_archetype": "通用PVP机制",
                            "target_entities": ["速度线"],
                            "priority": "high",
                            "expected_value": "high",
                            "ingest_status": "queued",
                        },
                    ],
                },
            )
            _write_yaml(
                mission_board,
                {
                    "schema_version": "p14.mission_board.v0",
                    "phase1_experiments": [
                        {
                            "experiment_id": "p14_e2_source_discovery_gap_fill",
                            "target_gaps": [
                                "翼王 common sets",
                                "沙暴/格斗 matchup",
                                "星陨 cross-source confirmation",
                            ],
                        }
                    ],
                },
            )

            result = run_source_gap_fill(
                source_queue=source_queue,
                mission_board=mission_board,
                out_root=out_root,
                batch_id="phase1_gap_test",
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(
                result["recommended_next_source_ids"],
                ["wingking_best", "sandstorm_fighting", "starfall_intro"],
            )
            audit = yaml.safe_load((out_root / "audits/phase1_gap_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(audit["summary"]["queued_source_count"], 4)
            self.assertEqual(audit["summary"]["processed_source_count"], 1)
            self.assertIn("adds_cross_source_confirmation", audit["ranked_by_gap"][2]["top_candidates"][0]["reasons"])
            packet = (out_root / "review_packets/phase1_gap_test_pm_brief.md").read_text(encoding="utf-8")
            self.assertIn("下一批推荐", packet)
            self.assertIn("wingking_best", packet)
            self.assertIn("generic_speed", packet)
            updated_queue = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(
                updated_queue["latest_source_gap_fill"]["recommended_next_source_ids"],
                ["wingking_best", "sandstorm_fighting", "starfall_intro"],
            )


if __name__ == "__main__":
    unittest.main()
