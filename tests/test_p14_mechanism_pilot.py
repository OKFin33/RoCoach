from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_mechanism_pilot import build_mechanism_pilot


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class P14MechanismPilotTests(unittest.TestCase):
    def test_builds_review_packet_without_runtime_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foundation = root / "source_a" / "evidence_foundation"
            _write_yaml(
                foundation / "source_manifest_v2.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "source": {"title": "星陨机制测试", "url": "https://example.invalid/BV"},
                },
            )
            _write_yaml(
                foundation / "quality_gate.yaml",
                {
                    "source_id": "source_a",
                    "segment_count": 3,
                    "claim_atom_count": 4,
                    "quality_gate_counts": {"claim_ready": 3},
                    "repair_required_segments": [],
                    "runtime_allowed": False,
                },
            )
            _write_yaml(
                foundation / "claim_atoms.yaml",
                {
                    "source_id": "source_a",
                    "runtime_allowed": False,
                    "claim_atoms": [
                        {
                            "claim_id": "claim/source_a/S0001/01",
                            "source_id": "source_a",
                            "segment_id": "S0001",
                            "atom_type": "mechanism_claim",
                            "subject": "星陨印记",
                            "subject_resolution_status": "mechanism_subject_fallback",
                            "predicate": "uses_mechanism",
                            "object": "mark",
                            "mentioned_species": [],
                            "mentioned_moves": ["水刃"],
                            "mentioned_mechanisms": ["星陨印记"],
                            "quality_gate": "claim_ready",
                            "evidence": {"start_ms": 1000, "end_ms": 3000, "quote": "水刃引爆星陨印记"},
                        },
                        {
                            "claim_id": "claim/source_a/S0002/01",
                            "source_id": "source_a",
                            "segment_id": "S0002",
                            "atom_type": "mechanism_claim",
                            "subject": "星陨印记",
                            "subject_resolution_status": "mechanism_subject_fallback",
                            "predicate": "uses_mechanism",
                            "object": "mark",
                            "mentioned_species": [],
                            "mentioned_moves": [],
                            "mentioned_mechanisms": ["星陨印记"],
                            "quality_gate": "claim_ready",
                            "evidence": {"start_ms": 4000, "end_ms": 6000, "quote": "叠加星陨印记"},
                        },
                        {
                            "claim_id": "claim/source_a/S0003/01",
                            "source_id": "source_a",
                            "segment_id": "S0003",
                            "atom_type": "resource_claim",
                            "subject": "裘卡",
                            "subject_resolution_status": "exact_single_species",
                            "predicate": "supports",
                            "object": "energy_window",
                            "mentioned_species": ["裘卡"],
                            "mentioned_moves": [],
                            "mentioned_mechanisms": [],
                            "quality_gate": "claim_ready",
                            "evidence": {"start_ms": 7000, "end_ms": 9000, "quote": "裘卡没能量了"},
                        },
                        {
                            "claim_id": "claim/source_a/S0004/01",
                            "source_id": "source_a",
                            "segment_id": "S0004",
                            "atom_type": "species_role",
                            "subject": "裘卡",
                            "subject_resolution_status": "exact_single_species",
                            "predicate": "has_role",
                            "object": "lead",
                            "mentioned_species": ["裘卡"],
                            "mentioned_moves": [],
                            "mentioned_mechanisms": [],
                            "quality_gate": "claim_ready",
                            "evidence": {"start_ms": 10000, "end_ms": 12000, "quote": "裘卡首发"},
                        },
                        {
                            "claim_id": "claim/source_a/S0005/01",
                            "source_id": "source_a",
                            "segment_id": "S0005",
                            "atom_type": "species_role",
                            "subject": "应对",
                            "subject_resolution_status": "mechanism_subject_fallback",
                            "predicate": "has_role",
                            "object": "lead",
                            "mentioned_species": [],
                            "mentioned_moves": [],
                            "mentioned_mechanisms": ["应对"],
                            "quality_gate": "claim_ready",
                            "evidence": {"start_ms": 13000, "end_ms": 14000, "quote": "首发应对教程"},
                        },
                    ],
                },
            )

            result = build_mechanism_pilot(
                foundation_dirs=[foundation],
                out_root=root / "knowledge_ops",
                batch_id="phase1_test",
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(result["summary"]["mechanism_relevant_claim_count"], 3)
            clusters = yaml.safe_load((root / "knowledge_ops/mechanism_rules/candidate_clusters/phase1_test.yaml").read_text())
            by_topic = {cluster["topic"]: cluster for cluster in clusters["clusters"]}
            self.assertEqual(by_topic["星陨印记"]["review_recommendation"], "decision_needed")
            self.assertEqual(by_topic["裘卡"]["review_recommendation"], "auto_defer")
            self.assertFalse(by_topic["星陨印记"]["runtime_allowed"])
            packet = (root / "knowledge_ops/review_packets/phase1_test_review.md").read_text()
            self.assertIn("## 你只要判断这一句", packet)
            self.assertIn("## 这次输入质量", packet)


if __name__ == "__main__":
    unittest.main()
