import unittest
from pathlib import Path

import yaml

from tools.p14_versioned_a_layer_resolver import resolve_entities


PHASE50_DIR = Path(
    "artifacts/knowledge_ops/dataset_pipeline_runs/"
    "phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23"
)
OLD_S2_BLOCKER = "s2_a_layer_reconciliation_required_before_runtime_or_gold"
NEW_S2_GATE = "s2_a_layer_overlay_referenced_pm_review_gold_gate_required"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


class P14Phase50S2OverlayReblockTests(unittest.TestCase):
    def test_versioned_resolver_is_candidate_only_and_resolves_overlay_entities(self) -> None:
        payload = resolve_entities(["落雷", "龙鱼"])

        self.assertFalse(payload["runtime_allowed"])
        self.assertFalse(payload["may_write_runtime_db"])
        self.assertGreater(payload["coverage_counts"]["overlay_species_count"], 0)
        self.assertGreater(payload["coverage_counts"]["overlay_move_count"], 0)
        by_entity = {item["entity"]: item for item in payload["resolved_entities"]}
        self.assertEqual(by_entity["落雷"]["overlay_resolution"], "s2_overlay_target")
        self.assertEqual(by_entity["龙鱼"]["overlay_resolution"], "s2_overlay_target")

    def test_phase50_outputs_keep_reblocked_candidates_candidate_only(self) -> None:
        candidates = _load_yaml(PHASE50_DIR / "candidate_kg_items.yaml")
        blocker_report = _load_yaml(PHASE50_DIR / "blocker_migration_report.yaml")
        clustering_report = _load_yaml(PHASE50_DIR / "clustering_report.yaml")
        dashboard = _load_yaml(PHASE50_DIR / "dashboard.yaml")

        items = candidates.get("candidate_items") or []
        self.assertTrue(items)
        self.assertFalse(candidates["runtime_allowed"])
        self.assertTrue(all(item.get("runtime_allowed") is False for item in items))
        self.assertFalse(any(OLD_S2_BLOCKER in (item.get("blocked_by") or []) for item in items))
        self.assertEqual(blocker_report["phase49"]["old_s2_reference_surface_blocker_count"], 5)
        self.assertEqual(blocker_report["phase49"]["new_s2_overlay_referenced_gate_count"], 5)
        self.assertFalse(clustering_report["runtime_allowed"])
        self.assertEqual(clustering_report["decision_counts"]["separate_set"], 0)
        self.assertGreaterEqual(clustering_report["decision_counts"]["split_blocked"], 1)
        self.assertEqual(dashboard["review_candidate_count"], 0)
        self.assertTrue(dashboard["clustering_summary"]["explicit_clustering_report"].endswith("clustering_report.yaml"))
        self.assertGreaterEqual(dashboard["blocker_counts"].get(NEW_S2_GATE, 0), 5)


if __name__ == "__main__":
    unittest.main()
