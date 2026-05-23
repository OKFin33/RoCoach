from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_promotion_review_packet import build_species_review_packet


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _source(source_id: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "title": f"title {source_id}",
        "url": f"https://example.com/{source_id}",
        "source_type": "team_explainer",
        "ingest_status": "set_pipeline_processed",
        "subtitle_status": {"transcript_method": "subtitle_ai_zh"},
        "source_quality_prior": {
            "latest_evidence_foundation": {
                "segment_count": 10,
                "claim_atom_count": 2,
            }
        },
    }


class P14PromotionReviewPacketTests(unittest.TestCase):
    def test_species_packet_defers_cross_source_single_move_cluster(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            consolidation = root / "consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(source_queue, {"sources": [_source("s1"), _source("s2"), _source("s3")]})
            _write_yaml(
                consolidation,
                {
                    "species_records": [
                        {
                            "species_name": "爬爬",
                            "state": "review_candidate",
                            "stable_moves": ["破罐破摔", "引燃", "摇篮曲", "晒太阳"],
                            "primary_source_count": 3,
                            "source_count": 3,
                            "top_roles": ["pivot_in"],
                            "promotion_blockers": ["runtime_promotion_forbidden"],
                            "observed_moves": [
                                {"move_name": "破罐破摔", "primary_source_count": 1, "source_count": 1, "sources": ["s1"]},
                                {"move_name": "引燃", "primary_source_count": 1, "source_count": 1, "sources": ["s2"]},
                                {"move_name": "摇篮曲", "primary_source_count": 1, "source_count": 1, "sources": ["s3"]},
                                {"move_name": "晒太阳", "primary_source_count": 1, "source_count": 1, "sources": ["s1"]},
                            ],
                            "dossier_variants": [
                                {"source_id": "s1", "moves": ["破罐破摔", "晒太阳"], "mention_count": 3},
                                {"source_id": "s2", "moves": ["引燃"], "mention_count": 2},
                                {"source_id": "s3", "moves": ["摇篮曲"], "mention_count": 2},
                            ],
                            "split_hypotheses": [],
                            "set_family_summary": {},
                            "set_family_candidates": [],
                            "suggested_next_action": "build_reviewer_packet_before_any_promotion",
                        }
                    ]
                },
            )

            result = build_species_review_packet(
                consolidation_path=consolidation,
                species_name="爬爬",
                source_queue_path=source_queue,
                batch_id="packet_test",
                out_root=out_root,
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(result["summary"]["recommended_decision"], "defer_until_more_same-core_evidence")
            self.assertEqual(result["summary"]["max_core_moves_in_one_source"], 2)
            packet = (out_root / "review_packets/packet_test_promotion_review.md").read_text(encoding="utf-8")
            self.assertIn("我的建议：`defer_until_more_same-core_evidence`", packet)
            self.assertIn("同一来源最多同时支持 2 个稳定技能", packet)

    def test_species_packet_accepts_repeated_full_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            consolidation = root / "consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(source_queue, {"sources": [_source("s1"), _source("s2")]})
            _write_yaml(
                consolidation,
                {
                    "species_records": [
                        {
                            "species_name": "恶魔狼",
                            "state": "review_candidate",
                            "stable_moves": ["技能A", "技能B", "技能C", "技能D"],
                            "primary_source_count": 2,
                            "source_count": 2,
                            "observed_moves": [],
                            "dossier_variants": [
                                {"source_id": "s1", "moves": ["技能A", "技能B", "技能C", "技能D"], "mention_count": 3},
                                {"source_id": "s2", "moves": ["技能A", "技能B", "技能C", "技能D"], "mention_count": 2},
                            ],
                            "split_hypotheses": [],
                            "set_family_summary": {},
                            "set_family_candidates": [],
                            "promotion_blockers": [],
                        }
                    ]
                },
            )

            result = build_species_review_packet(
                consolidation_path=consolidation,
                species_name="恶魔狼",
                source_queue_path=source_queue,
                batch_id="packet_test_accept",
                out_root=out_root,
            )

            self.assertEqual(result["summary"]["recommended_decision"], "accept_as_species_set_candidate")
            self.assertEqual(result["summary"]["source_count_with_full_core"], 2)


if __name__ == "__main__":
    unittest.main()
