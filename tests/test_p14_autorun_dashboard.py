from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from tools import p14_autorun_dashboard as dashboard_module
from tools.p14_autorun_dashboard import run_autorun_dashboard


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _source(source_id: str, *, status: str = "set_pipeline_processed") -> dict[str, object]:
    return {
        "source_id": source_id,
        "title": source_id,
        "url": f"https://example.com/{source_id}",
        "source_type": "team_explainer",
        "priority": "high",
        "expected_value": "high",
        "ingest_status": status,
        "subtitle_status": {
            "checked_with_chrome_cookies": True,
            "chinese_subtitle_track": "ai-zh",
            "transcript_method": "subtitle_ai_zh",
            "asr_fallback_needed": False,
        },
        "source_quality_prior": {
            "latest_evidence_foundation": {
                "segment_count": 10,
                "claim_atom_count": 2,
                "repair_required_segments": 0,
            }
        },
    }


def _inventory(source_id: str) -> dict[str, object]:
    return {
        "schema_version": "p14.set_inventory.v0",
        "source_id": source_id,
        "runtime_allowed": False,
        "source": {"title": source_id},
        "coverage_records": [],
        "set_dossiers": [],
        "summary": {},
    }


def _write_species_db(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE species_form (species_id TEXT PRIMARY KEY, display_name TEXT)")
        conn.executemany("INSERT INTO species_form (species_id, display_name) VALUES (?, ?)", rows)
        conn.commit()
    finally:
        conn.close()


def _write_species_form_db(path: Path, rows: list[tuple[str, str, str, str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE species_form (
                species_id TEXT PRIMARY KEY,
                display_name TEXT,
                initial_species_name TEXT,
                evolution_stage TEXT,
                ability_name TEXT,
                ability_effect_text TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO species_form (
                species_id,
                display_name,
                initial_species_name,
                evolution_stage,
                ability_name,
                ability_effect_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


class P14AutorunDashboardTests(unittest.TestCase):
    def test_dashboard_queue_write_preserves_newer_volume_plan_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "latest_volume_batch_plan": {"batch_id": "new_plan"},
                },
            )
            stale_queue_snapshot = {
                "schema_version": "p14.source_queue.v0",
                "latest_volume_batch_plan": {"batch_id": "old_plan"},
            }
            payload = {
                "batch_id": "autorun_test",
                "generated_at": "2026-05-21",
                "source_health": {"active_source_count": 1, "queued_source_count": 2},
                "control_gate_lane": {"pm_attention_required_count": 0},
                "promotion_lane": {"pm_attention_required_count": 0},
                "autorun_decision": {"next_action": {"action": "continue_volume_lane_and_queue_split_blockers"}},
            }

            dashboard_module._apply_queue_delta(
                source_queue,
                stale_queue_snapshot,
                payload,
                root / "autorun/autorun_test.yaml",
                root / "review_packets/autorun_test.md",
            )

            updated = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(updated["latest_volume_batch_plan"]["batch_id"], "new_plan")
            self.assertEqual(updated["latest_autorun_dashboard"]["batch_id"], "autorun_test")

    def test_dashboard_uses_active_sources_and_ignores_stale_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"

            _write_yaml(inventory_dir / "source_a.source_inventory.yaml", _inventory("source_a"))
            _write_yaml(inventory_dir / "source_b.source_inventory.yaml", _inventory("source_b"))
            _write_yaml(inventory_dir / "stale_old.source_inventory.yaml", _inventory("stale_old"))
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        _source("source_a"),
                        _source("source_b"),
                        _source("queued_next", status="queued"),
                    ],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "schema_version": "p14.set_inventory_consolidation.v0",
                    "batch_id": "consolidation",
                    "runtime_allowed": False,
                    "summary": {
                        "species_count": 1,
                        "split_blocked_count": 1,
                        "review_candidate_count": 0,
                        "family_review_candidate_count": 1,
                    },
                    "species_records": [
                        {
                            "species_name": "圣羽翼王",
                            "state": "split_blocked",
                            "source_count": 2,
                            "primary_source_count": 2,
                            "split_hypotheses": [{"hypothesis_id": "split_01_02"}],
                            "family_review_candidates": [
                                {
                                    "family_id": "family_02",
                                    "core_moves": ["水刃", "闪击", "力量增效"],
                                    "flex_moves": ["光之矛"],
                                    "primary_source_count": 2,
                                    "primary_source_ids": ["source_a", "source_b"],
                                    "runtime_allowed": False,
                                }
                            ],
                            "suggested_next_action": "build_family_level_reviewer_packet_keep_species_split_blocked",
                            "runtime_allowed": False,
                        }
                    ],
                },
            )
            _write_yaml(
                family_ledger,
                {
                    "schema_version": "p14.family_review_ledger.v0",
                    "entries": [
                        {
                            "review_id": "family_review/wingking/waterblade",
                            "proposed_card": {
                                "canonical_species_name": "圣羽翼王",
                                "core_moves": ["水刃", "闪击", "力量增效"],
                            },
                            "review": {"review_status": "pm_reviewed"},
                        }
                    ],
                },
            )

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            self.assertEqual(result["summary"]["next_action"], "expand_source_discovery_before_volume_autorun")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["active_source_ids"], ["source_a", "source_b"])
            self.assertEqual(dashboard["source_health"]["ignored_stale_inventory_count"], 1)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["already_reviewed_candidates"], 1)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_family_review_candidates"], 0)
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("没有新的 PM 必审项", packet)
            self.assertIn("忽略 stale inventory artifacts：1", packet)
            updated_queue = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(updated_queue["latest_autorun_dashboard"]["next_action"], "expand_source_discovery_before_volume_autorun")

    def test_new_family_candidate_requires_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b"), _source("source_c", status="queued")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                    "latest_volume_batch_plan": {
                        "batch_id": "volume_plan",
                        "selected_source_count": 3,
                        "selected_source_ids": ["source_a", "source_b", "source_c"],
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "恶魔狼",
                            "state": "review_candidate",
                            "stable_moves": ["技能A", "技能B", "技能C"],
                            "primary_source_count": 2,
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["技能A", "技能B", "技能C"],
                                    "primary_source_count": 2,
                                    "primary_source_ids": ["source_a", "source_b"],
                                    "core_cooccurrence_primary_source_count": 3,
                                    "alter_variants": [
                                        {"source_id": "source_a", "moves": ["技能A", "技能B", "技能C"]},
                                        {"source_id": "source_b", "moves": ["技能A", "技能B", "技能C"]},
                                    ],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 1)
            self.assertEqual(result["summary"]["next_action"], "build_pm_review_packet_for_new_promotion_candidates")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_family_review_candidates"], 1)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_species_review_candidates"], 0)
            self.assertEqual(dashboard["volume_batch_plan"]["remaining_selected_source_ids"], ["source_c"])
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("先停在 review gate，不继续自动跑", packet)
            self.assertIn("先生成聚焦 PM review packet", packet)
            self.assertNotIn("继续当前 volume batch plan 的剩余源", packet)

    def test_three_core_family_without_full_core_source_is_deferred_not_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b", "source_c", "source_d"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b"), _source("source_c"), _source("source_d")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b", "source_c", "source_d"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "琉璃水母",
                            "state": "review_candidate",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["泡沫幻影", "甩水", "洗礼"],
                                    "primary_source_count": 4,
                                    "primary_source_ids": ["source_a", "source_b", "source_c", "source_d"],
                                    "core_cooccurrence_primary_source_count": 4,
                                    "alter_variants": [
                                        {"source_id": "source_a", "moves": ["泡沫幻影", "甩水"]},
                                        {"source_id": "source_b", "moves": ["泡沫幻影", "甩水"]},
                                        {"source_id": "source_c", "moves": ["泡沫幻影", "甩水"]},
                                        {"source_id": "source_d", "moves": ["泡沫幻影", "洗礼"]},
                                    ],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            deferred = dashboard["promotion_lane"]["deferred_family_candidates"][0]
            self.assertEqual(deferred["defer_reason"], "no_full_core_source_for_three_plus_core_family")
            self.assertEqual(deferred["full_core_primary_source_count"], 0)

    def test_reviewed_flex_move_does_not_reopen_pm_attention_as_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "圣羽翼王",
                            "state": "split_blocked",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_02",
                                    "core_moves": ["水刃", "闪击", "力量增效", "光之矛"],
                                    "primary_source_count": 4,
                                    "primary_source_ids": ["source_a", "source_b"],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(
                family_ledger,
                {
                    "entries": [
                        {
                            "review_id": "family_review/wingking/waterblade",
                            "proposed_card": {
                                "canonical_species_name": "圣羽翼王",
                                "core_moves": ["水刃", "闪击", "力量增效"],
                                "flex_moves": ["光之矛"],
                            },
                            "review": {"review_status": "pm_reviewed"},
                        }
                    ]
                },
            )

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            reviewed = dashboard["promotion_lane"]["already_reviewed_candidates"][0]
            self.assertEqual(reviewed["ledger_match_kind"], "reviewed_core_with_flex_promoted_by_extraction")
            self.assertEqual(reviewed["recommended_action"], "ledger_update_only_reviewed_flex_not_auto_core")

    def test_reviewed_core_with_unreviewed_extra_core_is_deferred_not_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "海豹船长",
                            "state": "split_blocked",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["水刃", "听桥", "斩断", "防御"],
                                    "primary_source_count": 9,
                                    "primary_source_ids": ["source_a", "source_b"],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(
                family_ledger,
                {
                    "entries": [
                        {
                            "review_id": "family_review/seal_captain/waterblade_listenbridge",
                            "proposed_card": {
                                "canonical_species_name": "海豹船长",
                                "core_moves": ["水刃", "听桥"],
                                "flex_moves": ["斩断"],
                            },
                            "review": {"review_status": "pm_reviewed"},
                        }
                    ]
                },
            )

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            deferred = dashboard["promotion_lane"]["deferred_family_candidates"][0]
            self.assertEqual(deferred["defer_reason"], "reviewed_core_with_unreviewed_core_expansion")
            self.assertEqual(deferred["unreviewed_core_moves"], ["防御"])
            self.assertEqual(deferred["recommended_action"], "keep_as_candidate_evidence_do_not_reopen_pm_or_promote_core")

    def test_two_core_family_candidate_is_deferred_not_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "音速犬",
                            "state": "review_candidate",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["当头棒喝", "焚烧烙印"],
                                    "primary_source_count": 4,
                                    "primary_source_ids": ["source_a", "source_b"],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_family_review_candidates"], 0)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["deferred_family_candidates"], 1)
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("自动暂缓 family 候选：音速犬 family_01", packet)

    def test_low_cooccurrence_new_family_candidate_is_deferred_not_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b", "source_c", "source_d"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b"), _source("source_c"), _source("source_d")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b", "source_c", "source_d"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "龙鱼",
                            "state": "review_candidate",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["龙吟", "水刃", "龙之利爪"],
                                    "primary_source_count": 4,
                                    "primary_source_ids": ["source_a", "source_b", "source_c", "source_d"],
                                    "core_cooccurrence_primary_source_count": 2,
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            deferred = dashboard["promotion_lane"]["deferred_family_candidates"][0]
            self.assertEqual(deferred["defer_reason"], "core_cooccurrence_below_new_family_review_threshold")

    def test_low_cooccurrence_family_candidate_stays_deferred_even_with_many_primary_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            for sid in ["source_a", "source_b", "source_c", "source_d", "source_e"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source(f"source_{suffix}") for suffix in ["a", "b", "c", "d", "e"]],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b", "source_c", "source_d", "source_e"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "雪影娃娃",
                            "state": "split_blocked",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["冰墙", "暴风雪", "冰点", "碎冰冰"],
                                    "primary_source_count": 5,
                                    "primary_source_ids": ["source_a", "source_b", "source_c", "source_d", "source_e"],
                                    "core_cooccurrence_primary_source_count": 2,
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_family_review_candidates"], 0)
            deferred = dashboard["promotion_lane"]["deferred_family_candidates"][0]
            self.assertEqual(deferred["defer_reason"], "core_cooccurrence_below_new_family_review_threshold")

    def test_dashboard_continues_remaining_volume_plan_before_queue_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"

            _write_yaml(inventory_dir / "source_a.source_inventory.yaml", _inventory("source_a"))
            _write_yaml(inventory_dir / "source_b.source_inventory.yaml", _inventory("source_b"))
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        _source("source_a"),
                        _source("source_b"),
                        *[_source(f"done_{index}") for index in range(17)],
                        _source("source_c", status="queued"),
                    ],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                    "latest_volume_batch_plan": {
                        "batch_id": "volume_plan",
                        "selected_source_count": 20,
                        "selected_source_ids": ["source_a", "source_b", *[f"done_{index}" for index in range(17)], "source_c"],
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "split_blocked_count": 1},
                    "species_records": [
                        {
                            "species_name": "海豹船长",
                            "state": "split_blocked",
                            "primary_source_count": 2,
                            "split_hypotheses": [{"hypothesis_id": "split_01_02"}],
                            "suggested_next_action": "build_family_level_reviewer_packet_keep_species_split_blocked",
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["queued_source_count"], 1)
            self.assertEqual(result["summary"]["next_action"], "continue_volume_lane_and_queue_split_blockers")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertFalse(dashboard["autorun_decision"]["queue_capacity_ready"])
            self.assertTrue(dashboard["autorun_decision"]["volume_plan_has_remaining"])
            self.assertEqual(dashboard["volume_batch_plan"]["remaining_selected_source_ids"], ["source_c"])
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("当前 volume batch plan 还没跑完", packet)
            self.assertNotIn("下一步应先自动扩源", packet)

    def test_dashboard_refuses_under_target_volume_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"

            _write_yaml(inventory_dir / "source_a.source_inventory.yaml", _inventory("source_a"))
            _write_yaml(
                source_queue,
                {
                    "sources": [
                        _source("source_a"),
                        *[_source(f"queued_{index}", status="queued") for index in range(15)],
                    ],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a"],
                        "consolidation_path": str(consolidation_path),
                    },
                    "latest_volume_batch_plan": {
                        "batch_id": "under_target_plan",
                        "selected_source_count": 15,
                        "selected_source_ids": [f"queued_{index}" for index in range(15)],
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "split_blocked_count": 1},
                    "species_records": [
                        {
                            "species_name": "化蝶",
                            "state": "split_blocked",
                            "primary_source_count": 2,
                            "split_hypotheses": [{"hypothesis_id": "split_01_02"}],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["next_action"], "expand_source_discovery_before_volume_autorun")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(dashboard["autorun_decision"]["volume_plan_below_target"])
            self.assertFalse(dashboard["autorun_decision"]["volume_lane_ready_to_continue"])
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("下一步应先自动扩源", packet)

    def test_two_move_species_candidate_is_deferred_not_pm_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"

            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "小皮球",
                            "state": "review_candidate",
                            "stable_moves": ["防御", "心灵洞悉"],
                            "primary_source_count": 5,
                            "family_review_candidates": [],
                            "suggested_next_action": "build_reviewer_packet_before_any_promotion",
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_species_review_candidates"], 0)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["deferred_species_candidates"], 1)
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("自动暂缓 species-level 候选：小皮球", packet)

    def test_non_final_form_with_menghua_context_is_deferred_as_stateful_form_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            battle_dex = root / "battle_dex.sqlite"

            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "爬爬",
                            "state": "review_candidate",
                            "stable_moves": ["破罐破摔", "引燃", "摇篮曲", "晒太阳"],
                            "primary_source_count": 10,
                            "family_review_candidates": [],
                            "dossier_variants": [
                                {
                                    "source_id": "source_a",
                                    "moves": ["引燃"],
                                    "configuration": {"mechanism_mentions": ["萌化"]},
                                },
                                {
                                    "source_id": "source_b",
                                    "moves": ["摇篮曲"],
                                    "configuration": {"mechanism_mentions": []},
                                },
                            ],
                            "suggested_next_action": "build_reviewer_packet_before_any_promotion",
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})
            _write_species_form_db(
                battle_dex,
                [
                    ("species_momo", "毛毛", "毛毛", "I阶", "化茧", "受到致命伤害时,获得1层萌化,并免疫此次伤害。"),
                    ("species_papa", "爬爬", "毛毛", "II阶", "化茧", "受到致命伤害时,获得1层萌化,并免疫此次伤害。"),
                    ("species_huadie", "化蝶", "毛毛", "最终形态", "化茧", "受到致命伤害时,获得1层萌化,并免疫此次伤害。"),
                ],
            )

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                battle_dex=battle_dex,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_species_review_candidates"], 0)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["deferred_species_candidates"], 1)
            deferred = dashboard["promotion_lane"]["deferred_species_candidates"][0]
            self.assertEqual(deferred["defer_reason"], "possible_stateful_form_evidence_from_menghua")
            self.assertEqual(deferred["recommended_action"], "reclassify_as_stateful_form_evidence_candidate")
            self.assertEqual(deferred["observed_battle_form"], "爬爬")
            self.assertEqual(deferred["roster_species_candidates"], ["化蝶"])
            self.assertEqual(deferred["form_derivation_mechanism_terms"], ["萌化"])
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("自动暂缓 species-level 候选：爬爬", packet)
            self.assertIn("possible_stateful_form_evidence_from_menghua", packet)

    def test_ambiguous_a_layer_species_id_defers_family_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            battle_dex = root / "battle_dex.sqlite"

            for sid in ["source_a", "source_b"]:
                _write_yaml(inventory_dir / f"{sid}.source_inventory.yaml", _inventory(sid))
            _write_species_db(battle_dex, [("species_a", "化蝶"), ("species_b", "化蝶")])
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a"), _source("source_b")],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a", "source_b"],
                        "consolidation_path": str(consolidation_path),
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "family_review_candidate_count": 1},
                    "species_records": [
                        {
                            "species_name": "化蝶",
                            "state": "split_blocked",
                            "family_review_candidates": [
                                {
                                    "family_id": "family_01",
                                    "core_moves": ["退化", "晒太阳"],
                                    "primary_source_count": 2,
                                    "primary_source_ids": ["source_a", "source_b"],
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                battle_dex=battle_dex,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["new_family_review_candidates"], 0)
            self.assertEqual(dashboard["promotion_lane"]["candidate_counts"]["deferred_family_candidates"], 1)
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("自动暂缓 family 候选：化蝶 family_01", packet)

    def test_axis_branch_control_gate_blocks_autorun_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            identity_axis_dir = out_root / "identity_axis_binding"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"

            _write_yaml(inventory_dir / "source_a.source_inventory.yaml", _inventory("source_a"))
            _write_yaml(
                source_queue,
                {
                    "sources": [
                        _source("source_a"),
                        *[_source(f"done_{index}") for index in range(18)],
                        _source("source_b", status="queued"),
                    ],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a"],
                        "consolidation_path": str(consolidation_path),
                    },
                    "latest_volume_batch_plan": {
                        "batch_id": "volume_plan",
                        "selected_source_count": 20,
                        "selected_source_ids": ["source_a", *[f"done_{index}" for index in range(18)], "source_b"],
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "split_blocked_count": 1},
                    "species_records": [
                        {"species_name": "寂灭骨龙", "state": "split_blocked", "primary_source_count": 4}
                    ],
                },
            )
            _write_yaml(
                identity_axis_dir / "axis_gate.yaml",
                {
                    "batch_id": "axis_gate",
                    "runtime_allowed": False,
                    "axis_reports": [
                        {
                            "species_name": "寂灭骨龙",
                            "axis_branch_candidates": [
                                {
                                    "axis_id": "bulk_defensive_vs_physical_pressure",
                                    "axis_label": "联防生命/坦度流 vs 压制输出/物攻流",
                                    "status": "candidate_for_pm_axis_branch_review",
                                    "supported_branch_count": 2,
                                    "required_branch_count": 2,
                                    "recommended_action": "ask PM to accept axis boundary",
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                identity_axis_dir=identity_axis_dir,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 1)
            self.assertEqual(result["summary"]["control_gate_pm_attention_required_count"], 1)
            self.assertEqual(result["summary"]["next_action"], "build_pm_axis_branch_review_packet")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(dashboard["autorun_decision"]["control_gate_lane_has_new_pm_work"])
            self.assertEqual(dashboard["control_gate_lane"]["axis_branch_gates"][0]["species_name"], "寂灭骨龙")
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("控制面 PM gate", packet)
            self.assertIn("bulk_defensive_vs_physical_pressure", packet)
            self.assertIn("先停在 review gate", packet)

    def test_pm_accepted_axis_branch_gate_does_not_block_autorun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            identity_axis_dir = out_root / "identity_axis_binding"
            consolidation_path = out_root / "set_inventory_consolidation/consolidation.yaml"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            reviewer_ledger = root / "reviewer_ledger.yaml"

            _write_yaml(inventory_dir / "source_a.source_inventory.yaml", _inventory("source_a"))
            _write_yaml(
                source_queue,
                {
                    "sources": [
                        _source("source_a"),
                        *[_source(f"done_{index}") for index in range(18)],
                        _source("source_b", status="queued"),
                    ],
                    "latest_set_inventory_consolidation": {
                        "source_ids": ["source_a"],
                        "consolidation_path": str(consolidation_path),
                    },
                    "latest_volume_batch_plan": {
                        "batch_id": "volume_plan",
                        "selected_source_count": 20,
                        "selected_source_ids": ["source_a", *[f"done_{index}" for index in range(18)], "source_b"],
                    },
                },
            )
            _write_yaml(
                consolidation_path,
                {
                    "summary": {"species_count": 1, "split_blocked_count": 1},
                    "species_records": [
                        {"species_name": "寂灭骨龙", "state": "split_blocked", "primary_source_count": 4}
                    ],
                },
            )
            _write_yaml(
                identity_axis_dir / "axis_gate.yaml",
                {
                    "batch_id": "axis_gate",
                    "runtime_allowed": False,
                    "axis_reports": [
                        {
                            "species_name": "寂灭骨龙",
                            "axis_branch_candidates": [
                                {
                                    "axis_id": "bulk_defensive_vs_physical_pressure",
                                    "axis_label": "联防生命/坦度流 vs 压制输出/物攻流",
                                    "status": "candidate_for_pm_axis_branch_review",
                                    "supported_branch_count": 2,
                                    "required_branch_count": 2,
                                }
                            ],
                        }
                    ],
                },
            )
            _write_yaml(
                reviewer_ledger,
                {
                    "pm_decisions": {
                        "axis_branch_resolution": {
                            "寂灭骨龙": {
                                "axis_id": "bulk_defensive_vs_physical_pressure",
                                "status": "pm_accepted_control_plane_boundary",
                                "accepted_at": "2026-05-20",
                            }
                        }
                    }
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                reviewer_ledger=reviewer_ledger,
                identity_axis_dir=identity_axis_dir,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["pm_attention_required_count"], 0)
            self.assertEqual(result["summary"]["control_gate_pm_attention_required_count"], 0)
            self.assertEqual(result["summary"]["next_action"], "continue_volume_lane_and_queue_split_blockers")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertFalse(dashboard["autorun_decision"]["control_gate_lane_has_new_pm_work"])
            self.assertEqual(dashboard["control_gate_lane"]["accepted_axis_branch_gates"][0]["species_name"], "寂灭骨龙")
            packet = (out_root / "review_packets/autorun_test_autorun_dashboard.md").read_text(encoding="utf-8")
            self.assertIn("已接受 axis_branch", packet)

    def test_missing_active_inventory_blocks_autorun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_root = root / "knowledge_ops"
            inventory_dir = out_root / "set_inventory"
            source_queue = root / "source_queue.yaml"
            family_ledger = root / "family_review_ledger.yaml"
            _write_yaml(
                source_queue,
                {
                    "sources": [_source("source_a")],
                    "latest_set_inventory_consolidation": {"source_ids": ["source_a"]},
                },
            )
            _write_yaml(family_ledger, {"entries": []})

            result = run_autorun_dashboard(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="autorun_test",
                inventory_dir=inventory_dir,
                family_review_ledger=family_ledger,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["next_action"], "repair_batch_artifacts_before_autorun")
            dashboard = yaml.safe_load((out_root / "autorun/autorun_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(dashboard["blocker_lane"]["missing_active_artifacts"]["missing_inventory_paths"])


if __name__ == "__main__":
    unittest.main()
