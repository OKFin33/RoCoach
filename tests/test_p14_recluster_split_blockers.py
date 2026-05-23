from __future__ import annotations

import unittest

from tools.p14_recluster_split_blockers import build_recluster_audit


def _family(family_id: str, variants: list[tuple[str, list[str]]]) -> dict[str, object]:
    return {
        "family_id": family_id,
        "primary_source_ids": [source_id for source_id, _ in variants],
        "alter_variants": [
            {"source_id": source_id, "moves": moves}
            for source_id, moves in variants
        ],
    }


def _consolidation(*families: dict[str, object], species_name: str = "寂灭骨龙") -> dict[str, object]:
    source_ids = [
        source_id
        for family in families
        for variant in family.get("alter_variants", [])
        for source_id in [variant.get("source_id")]
        if source_id
    ]
    return {
        "batch_id": "test_consolidation",
        "source_quality": {
            source_id: {"title": f"{species_name} focused source {source_id}"}
            for source_id in source_ids
        },
        "species_records": [
            {
                "species_name": species_name,
                "state": "split_blocked",
                "primary_source_count": 4,
                "stable_moves": ["偷袭", "先发制人", "吓退", "防御", "电弧"],
                "set_family_summary": {"overwide_move_pool_blocked": True},
                "set_family_candidates": list(families),
                "split_hypotheses": [{"hypothesis_id": "split_01_02"}],
                "family_review_candidates": [],
            }
        ],
    }


class P14ReclusterSplitBlockersTests(unittest.TestCase):
    def test_finds_full_core_recluster_candidate(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["偷袭", "先发制人", "吓退", "防御"]),
                        ("source_b", ["偷袭", "先发制人", "吓退"]),
                        ("source_c", ["偷袭", "先发制人", "吓退", "电弧"]),
                    ],
                )
            ),
            family_ledger={"entries": []},
            species_index={},
        )

        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 1)
        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(proposal["gate_status"], "candidate_for_pm_recluster_packet")
        self.assertEqual(proposal["proposed_core_moves"], ["偷袭", "先发制人", "吓退"])
        self.assertEqual(proposal["full_core_primary_source_count"], 3)
        self.assertEqual(proposal["flex_moves_from_full_core_sources"], ["防御", "电弧"])

    def test_exact_reviewed_core_is_not_reopened(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["水刃", "闪击", "力量增效"]),
                        ("source_b", ["水刃", "闪击", "力量增效"]),
                        ("source_c", ["水刃", "闪击", "力量增效"]),
                    ],
                ),
                species_name="圣羽翼王",
            ),
            family_ledger={
                "entries": [
                    {
                        "review_id": "family_review/wingking/waterblade",
                        "review": {"review_status": "pm_reviewed"},
                        "proposed_card": {
                            "canonical_species_name": "圣羽翼王",
                            "proposed_family_name": "水刃物攻线",
                            "core_moves": ["水刃", "闪击", "力量增效"],
                        },
                    }
                ]
            },
            species_index={},
        )

        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        self.assertEqual(proposal["gate_status"], "already_reviewed_core")

    def test_reviewed_core_overlap_is_boundary_evidence_only(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["水刃", "闪击", "防御"]),
                        ("source_b", ["水刃", "闪击", "防御"]),
                        ("source_c", ["水刃", "闪击", "防御"]),
                    ],
                ),
                species_name="圣羽翼王",
            ),
            family_ledger={
                "entries": [
                    {
                        "review_id": "family_review/wingking/waterblade",
                        "review": {"review_status": "pm_reviewed"},
                        "proposed_card": {
                            "canonical_species_name": "圣羽翼王",
                            "proposed_family_name": "水刃物攻线",
                            "core_moves": ["水刃", "闪击", "力量增效"],
                        },
                    }
                ]
            },
            species_index={},
        )

        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        self.assertEqual(proposal["gate_status"], "blocked_by_reviewed_core_overlap")
        self.assertEqual(proposal["overlap_reviewed_entries"][0]["overlap_moves"], ["水刃", "闪击"])

    def test_previously_deferred_exact_core_is_not_counted_as_reviewed(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["热身运动", "三连破", "乘胜追击"]),
                        ("source_b", ["热身运动", "三连破", "乘胜追击"]),
                        ("source_c", ["热身运动", "三连破", "乘胜追击"]),
                    ],
                ),
                species_name="圣羽翼王",
            ),
            family_ledger={
                "entries": [
                    {
                        "review_id": "family_review/wingking/warmup",
                        "review": {"review_status": "deferred"},
                        "proposed_card": {
                            "canonical_species_name": "圣羽翼王",
                            "proposed_family_name": "热身三连破线",
                            "core_moves": ["热身运动", "三连破", "乘胜追击"],
                        },
                    }
                ]
            },
            species_index={},
        )

        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        self.assertEqual(proposal["gate_status"], "previously_deferred_core")

    def test_ambiguous_species_identity_blocks_pm_candidate(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["晒太阳", "毒孢子", "破罐破摔"]),
                        ("source_b", ["晒太阳", "毒孢子", "破罐破摔"]),
                        ("source_c", ["晒太阳", "毒孢子", "破罐破摔"]),
                    ],
                ),
                species_name="化蝶",
            ),
            family_ledger={"entries": []},
            species_index={"化蝶": ["species_a", "species_b"]},
        )

        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        self.assertEqual(proposal["gate_status"], "blocked_by_ambiguous_species_id")

    def test_requires_at_least_two_focused_sources(self) -> None:
        consolidation = _consolidation(
            _family(
                "family_01",
                [
                    ("source_a", ["偷袭", "先发制人", "吓退"]),
                    ("source_b", ["偷袭", "先发制人", "吓退"]),
                    ("source_c", ["偷袭", "先发制人", "吓退"]),
                ],
            )
        )
        consolidation["source_quality"] = {
            "source_a": {"title": "寂灭骨龙 高端局教学"},
            "source_b": {"title": "平衡队版本答案"},
            "source_c": {"title": "大师局PVP解说"},
        }
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=consolidation,
            family_ledger={"entries": []},
            species_index={},
        )

        proposal = payload["species_reports"][0]["candidate_proposals"][0]
        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        self.assertEqual(proposal["gate_status"], "needs_more_focused_full_core_sources")
        self.assertEqual(proposal["focused_full_core_primary_source_count"], 1)

    def test_overlapping_ready_cores_need_axis_resolution_before_pm(self) -> None:
        payload = build_recluster_audit(
            batch_id="test",
            consolidation=_consolidation(
                _family(
                    "family_01",
                    [
                        ("source_a", ["偷袭", "先发制人", "吓退"]),
                        ("source_b", ["偷袭", "先发制人", "吓退"]),
                        ("source_c", ["偷袭", "先发制人", "吓退"]),
                        ("source_d", ["偷袭", "先发制人", "电弧"]),
                        ("source_e", ["偷袭", "先发制人", "电弧"]),
                        ("source_f", ["偷袭", "先发制人", "电弧"]),
                    ],
                )
            ),
            family_ledger={"entries": []},
            species_index={},
        )

        self.assertEqual(payload["summary"]["pm_recluster_candidate_count"], 0)
        statuses = {
            tuple(proposal["proposed_core_moves"]): proposal["gate_status"]
            for proposal in payload["species_reports"][0]["candidate_proposals"]
        }
        self.assertEqual(
            statuses[("偷袭", "先发制人", "吓退")],
            "candidate_cluster_needs_axis_resolution",
        )
        self.assertEqual(
            statuses[("偷袭", "先发制人", "电弧")],
            "candidate_cluster_needs_axis_resolution",
        )


if __name__ == "__main__":
    unittest.main()
