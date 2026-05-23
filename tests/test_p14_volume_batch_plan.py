from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_volume_batch_plan import run_volume_batch_plan


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _source(
    source_id: str,
    *,
    title: str | None = None,
    source_type: str = "team_explainer",
    priority: str = "medium",
    expected_value: str = "medium",
    risks: list[str] | None = None,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "title": title or f"洛克王国世界 PVP {source_id}",
        "url": f"https://www.bilibili.com/video/BV{source_id.upper()}",
        "source_type": source_type,
        "target_archetype": source_id,
        "priority": priority,
        "expected_value": expected_value,
        "ingest_status": "queued",
        "source_quality_prior": {
            "likely_subtitle_available": "unknown",
            "likely_noise": "medium",
            "promotion_bias": risks or [],
        },
    }


class P14VolumeBatchPlanTests(unittest.TestCase):
    def test_selects_recommended_sources_first_and_updates_queue_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source("rec_a", priority="medium"),
                _source("rec_b", source_type="matchup_counterplay", priority="medium"),
                _source("optional_a", priority="low", risks=["older_meta_snapshot"]),
            ]
            sources.extend(_source(f"high_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": sources,
                    "latest_source_gap_fill": {
                        "batch_id": "gap_test",
                        "recommended_next_source_ids": ["rec_a", "rec_b"],
                        "optional_next_source_ids": ["optional_a"],
                    },
                },
            )

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertEqual(result["selected_source_ids"][:3], ["rec_a", "rec_b", "optional_a"])
            self.assertEqual(result["summary"]["recommended_included_count"], 2)
            updated = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(updated["latest_volume_batch_plan"]["selected_source_count"], 20)
            packet = (out_root / "review_packets/volume_test_pm_brief.md").read_text(encoding="utf-8")
            self.assertIn("下一批选 20 条", packet)

    def test_caps_low_signal_tier_overviews_when_enough_sources_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = []
            sources.extend(
                _source(f"tier_{index}", source_type="tier_overview", priority="high", expected_value="high", risks=["tier_overview_is_coverage_only"])
                for index in range(12)
            )
            sources.extend(_source(f"team_{index}", priority="medium", expected_value="medium") for index in range(18))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertLessEqual(result["summary"]["source_type_mix"].get("tier_overview", 0), 4)
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(any(item["reason"] == "tier_overview_quota_reached" for item in plan["deferred_sources"]))

    def test_caps_same_bv_anthology_pages_in_one_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = []
            for index in range(1, 10):
                source = _source(f"anthology_{index}", priority="high", expected_value="high")
                source["url"] = f"https://www.bilibili.com/video/BVANTHOLOGY/?p={index + 1}"
                source["anthology_page_index"] = index + 1
                sources.append(source)
            sources.extend(_source(f"team_{index}", priority="medium", expected_value="medium") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            selected_anthology = [source_id for source_id in result["selected_source_ids"] if source_id.startswith("anthology_")]
            self.assertLessEqual(len(selected_anthology), 3)
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(any(item["reason"] == "anthology_bvid_page_quota_reached" for item in plan["deferred_sources"]))

    def test_keeps_anthology_cap_when_quota_breach_starts_at_fill_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = []
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(12))
            for index in range(1, 11):
                source = _source(f"anthology_{index}", priority="medium", expected_value="high")
                source["url"] = f"https://www.bilibili.com/video/BVBOUNDARY/?p={index + 1}"
                source["anthology_page_index"] = index + 1
                sources.append(source)
            sources.extend(_source(f"tail_{index}", priority="medium", expected_value="medium") for index in range(13))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            selected_anthology = [source_id for source_id in result["selected_source_ids"] if source_id.startswith("anthology_")]
            self.assertLessEqual(len(selected_anthology), 3)
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(any(item["reason"] == "anthology_bvid_page_quota_reached" for item in plan["deferred_sources"]))

    def test_caps_anthology_pages_from_url_when_page_index_field_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = []
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(12))
            for index in range(1, 11):
                source = _source(f"legacy_page_{index}", priority="medium", expected_value="high")
                source["url"] = f"https://www.bilibili.com/video/BVLEGACY/?p={index + 1}"
                sources.append(source)
            sources.extend(_source(f"tail_{index}", priority="medium", expected_value="medium") for index in range(13))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            selected_pages = [source_id for source_id in result["selected_source_ids"] if source_id.startswith("legacy_page_")]
            self.assertLessEqual(len(selected_pages), 3)
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            self.assertTrue(any(item["reason"] == "anthology_bvid_page_quota_reached" for item in plan["deferred_sources"]))

    def test_defers_off_boundary_playthrough_titles_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "full_flow",
                    title="洛克王国世界手游全流程实况视频，大世界探索",
                    source_type="gameplay_replay",
                    priority="high",
                    expected_value="high",
                    risks=["older_meta_snapshot", "long_playthrough", "low_precision"],
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("full_flow", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["full_flow"], "outside_pvp_boundary_title")

    def test_defers_boss_titles_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "boss_mix",
                    title="[雪影平衡] 实战思路解说 打boss合集",
                    source_type="gameplay_replay",
                    priority="high",
                    expected_value="high",
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("boss_mix", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["boss_mix"], "outside_pvp_boundary_title")

    def test_defers_magic_egg_guides_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "magic_egg",
                    title="【洛克王国：世界】神奇的蛋全攻略教程",
                    source_type="team_explainer",
                    priority="high",
                    expected_value="high",
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("magic_egg", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["magic_egg"], "outside_pvp_boundary_title")

    def test_defers_controller_setup_titles_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "controller_setup",
                    title="首发最强公测手柄完美爽玩保姆级攻略（附独家配置包）【洛克王国世界】",
                    source_type="team_explainer",
                    priority="high",
                    expected_value="high",
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("controller_setup", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["controller_setup"], "outside_pvp_boundary_title")

    def test_defers_pvp_badge_titles_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "badge_achievement",
                    title="一个视频教会你如何拿到PVP最难获得的奖牌，摧枯拉朽（完整版）",
                    source_type="gameplay_replay",
                    priority="high",
                    expected_value="high",
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("badge_achievement", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["badge_achievement"], "outside_pvp_boundary_title")

    def test_defers_resource_route_titles_even_with_pvp_before_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            out_root = root / "knowledge_ops"
            sources = [
                _source(
                    "resource_route",
                    title="洛克王国世界 PVP 全图采集跑图路线 4800球攻略说明",
                    source_type="team_explainer",
                    priority="high",
                    expected_value="high",
                )
            ]
            sources.extend(_source(f"team_{index}", priority="high", expected_value="high") for index in range(25))
            _write_yaml(source_queue, {"sources": sources})

            result = run_volume_batch_plan(
                source_queue=source_queue,
                out_root=out_root,
                batch_id="volume_test",
                target_size=20,
                update_source_queue=False,
            )

            self.assertEqual(result["summary"]["selected_source_count"], 20)
            self.assertNotIn("resource_route", result["selected_source_ids"])
            plan = yaml.safe_load((out_root / "volume_batches/volume_test.yaml").read_text(encoding="utf-8"))
            deferred = {item["source_id"]: item["reason"] for item in plan["deferred_sources"]}
            self.assertEqual(deferred["resource_route"], "outside_pvp_boundary_title")


if __name__ == "__main__":
    unittest.main()
