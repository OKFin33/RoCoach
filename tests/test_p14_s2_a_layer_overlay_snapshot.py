import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_build_s2_a_layer_overlay_snapshot import (
    build_overlay_payload,
    semantic_move_effect_changes,
    write_s1_snapshot,
)


class P14S2ALayerOverlaySnapshotTests(unittest.TestCase):
    def test_s1_snapshot_hash_is_reproducible_and_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_db = root / "data" / "runtime" / "battle_dex.sqlite"
            runtime_db.parent.mkdir(parents=True)
            runtime_db.write_bytes(b"stable battle dex bytes")

            manifest = write_s1_snapshot(
                runtime_db=runtime_db,
                snapshot_dir=root / "data" / "runtime" / "snapshots" / "s1_2026-05-20",
                created_at="2026-05-23T00:00:00+08:00",
                repo_root=root,
            )

            self.assertFalse(manifest["runtime_allowed"])
            self.assertTrue(manifest["byte_identical_to_source"])
            self.assertEqual(manifest["source"]["sha256"], manifest["snapshot"]["sha256"])
            self.assertEqual((root / manifest["snapshot"]["path"]).read_bytes(), runtime_db.read_bytes())

    def test_overlay_manifest_required_boundary_fields(self) -> None:
        overlay = build_overlay_payload(
            reconciliation={
                "summary": {"unresolved_or_non_dex_items": 0},
                "stat_overlays": [],
                "ability_overlays": [],
                "move_pool_additions": [],
                "move_effect_overlays": [
                    {
                        "source_image_id": "s2_patch_img_006",
                        "status": "ready_candidate_overlay",
                        "move_resolution": {
                            "status": "resolved_exact",
                            "move": {
                                "move_id": "move_waterblade",
                                "move_name": "水刃",
                                "energy_cost": 4,
                            },
                        },
                        "patch_old_text": "造成物伤，应对状态：本技能能耗永久-4。",
                        "patch_new_text": "造成物伤，应对状态：本技能能耗永久-3。",
                    }
                ],
                "wording_updates": [],
                "unresolved_or_non_dex_items": [],
            },
            base_snapshot_ref="data/runtime/snapshots/s1_2026-05-20/manifest.yaml",
            patch_delta_ref="data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_patch_delta_pack_v0.yaml",
            reconciliation_ref="data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_a_layer_reconciliation_v0.yaml",
            official_source_ref="data/knowledge_graph/v0/patch_deltas/s2_2026-05-20_official_balance_sources/s2_2026-05-20_official_balance_manifest.yaml",
            created_at="2026-05-23T00:00:00+08:00",
        )

        self.assertEqual(overlay["schema_version"], "p14.a_layer_overlay.v0")
        self.assertEqual(overlay["game_epoch"], "s2_2026-05-21_candidate")
        self.assertFalse(overlay["runtime_allowed"])
        self.assertFalse(overlay["may_write_runtime_db"])
        self.assertEqual(overlay["promotion_status"], "candidate_only")
        self.assertTrue(overlay["requires_pm_review_before_runtime"])

    def test_runtime_allowed_false_enforced_on_overlay_entries(self) -> None:
        overlay = build_overlay_payload(
            reconciliation={
                "summary": {"unresolved_or_non_dex_items": 0},
                "stat_overlays": [
                    {
                        "source_image_id": "img",
                        "status": "ready_candidate_overlay",
                        "resolution": {
                            "status": "resolved_exact",
                            "species": {"species_id": "species_a", "display_name": "测试精灵"},
                        },
                        "changes": [{"stat": "生命", "patch_new": 100}],
                    }
                ],
                "ability_overlays": [],
                "move_pool_additions": [],
                "move_effect_overlays": [],
                "wording_updates": [],
                "unresolved_or_non_dex_items": [],
            },
            base_snapshot_ref="base",
            patch_delta_ref="patch",
            reconciliation_ref="recon",
            official_source_ref="official",
            created_at="2026-05-23T00:00:00+08:00",
        )

        for group in overlay["entries"].values():
            for entry in group:
                self.assertFalse(entry["runtime_allowed"])

    def test_waterblade_response_state_energy_reduction_not_base_energy_cost(self) -> None:
        changes = semantic_move_effect_changes(
            {
                "patch_old_text": "造成物伤，应对状态：本技能能耗永久-4。",
                "patch_new_text": "造成物伤，应对状态：本技能能耗永久-3。",
                "field_checks": [],
            }
        )

        self.assertEqual(
            changes,
            [
                {
                    "field": "response_state_attached_effect_energy_reduction",
                    "old": -4,
                    "new": -3,
                    "base_energy_cost_change": False,
                    "interpretation": "Attached effect under 应对状态; do not write this as move.energy_cost.",
                }
            ],
        )

    def test_written_manifest_yaml_has_no_runtime_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "overlay.yaml"
            payload = build_overlay_payload(
                reconciliation={
                    "summary": {"unresolved_or_non_dex_items": 0},
                    "stat_overlays": [],
                    "ability_overlays": [],
                    "move_pool_additions": [],
                    "move_effect_overlays": [],
                    "wording_updates": [],
                    "unresolved_or_non_dex_items": [],
                },
                base_snapshot_ref="base",
                patch_delta_ref="patch",
                reconciliation_ref="recon",
                official_source_ref="official",
                created_at="2026-05-23T00:00:00+08:00",
            )
            path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            loaded = yaml.safe_load(path.read_text())

        self.assertFalse(loaded["runtime_allowed"])
        self.assertEqual(loaded["promotion_status"], "candidate_only")
        self.assertIn("pm_review_required_before_runtime_or_a_layer_write", loaded["remaining_blockers"])


if __name__ == "__main__":
    unittest.main()
