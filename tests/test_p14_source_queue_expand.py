from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_source_queue_expand import run_source_queue_expand


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class P14SourceQueueExpandTests(unittest.TestCase):
    def test_appends_valid_bilibili_sources_and_updates_queue_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "existing_processed",
                            "url": "https://www.bilibili.com/video/BV1111111111/",
                            "title": "洛克王国世界 PVP 已处理",
                            "source_type": "team_explainer",
                            "ingest_status": "set_pipeline_processed",
                        }
                    ],
                },
            )
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": [
                        {
                            "source_id": "new_roco_pvp",
                            "url": "https://www.bilibili.com/video/BV2222222222/?spm_id_from=x",
                            "title": "洛克王国世界 PVP 阵容讲解",
                            "source_type": "team_explainer",
                            "target_archetype": "测试队",
                            "target_entities": ["测试精灵"],
                            "priority": "high",
                            "expected_value": "high",
                        }
                    ],
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertFalse(result["runtime_allowed"])
            self.assertEqual(result["added_source_ids"], ["new_roco_pvp"])
            updated = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(updated["sources"][-1]["url"], "https://www.bilibili.com/video/BV2222222222/")
            self.assertEqual(updated["sources"][-1]["ingest_status"], "queued")
            self.assertEqual(updated["latest_source_queue_expansion"]["added_count"], 1)
            packet = (out_root / "review_packets/expand_test_pm_brief.md").read_text(encoding="utf-8")
            self.assertIn("新增 1 条待抓源", packet)

    def test_skips_duplicate_and_out_of_boundary_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "existing",
                            "url": "https://www.bilibili.com/video/BV3333333333/",
                            "title": "洛克王国世界 PVP 已存在",
                            "source_type": "team_explainer",
                            "ingest_status": "queued",
                        }
                    ],
                },
            )
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": [
                        {
                            "source_id": "duplicate_bvid",
                            "url": "https://www.bilibili.com/video/BV3333333333/",
                            "title": "洛克王国世界 PVP 重复视频",
                            "source_type": "team_explainer",
                        },
                        {
                            "source_id": "bad_boundary",
                            "url": "https://www.bilibili.com/video/BV4444444444/",
                            "title": "洛克王国世界 家园种田小技巧",
                            "source_type": "team_explainer",
                        },
                        {
                            "source_id": "bad_grab",
                            "url": "https://www.bilibili.com/video/BV6666666666/",
                            "title": "【洛克王国世界】新手必看的抓骨龙焚决，还有机会抓到被污染的骨龙",
                            "source_type": "gameplay_replay",
                            "target_archetype": "洛克王国世界PVP候选源：寂灭骨龙",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 PVP 寂灭骨龙 配招`.",
                        },
                        {
                            "source_id": "bad_action",
                            "url": "https://www.bilibili.com/video/BV7777777777/",
                            "title": "紧急提醒！S1 限定动作，赛季结束马上绝版？全动作解锁攻略【洛克王国世界】",
                            "source_type": "team_explainer",
                            "target_archetype": "洛克王国世界PVP候选源：海豹船长",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 PVP 海豹船长 配招`.",
                        },
                        {
                            "source_id": "bad_boss",
                            "url": "https://www.bilibili.com/video/BV8888888888/",
                            "title": "[雪影平衡] 实战思路解说 打boss合集",
                            "source_type": "gameplay_replay",
                            "target_archetype": "洛克王国世界PVP候选源：雪影娃娃",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 雪影娃娃 PVP`.",
                        },
                        {
                            "source_id": "bad_magic_egg",
                            "url": "https://www.bilibili.com/video/BV1414141414/",
                            "title": "【洛克王国：世界】神奇的蛋全攻略教程",
                            "source_type": "team_explainer",
                            "target_archetype": "洛克王国世界PVP候选源：化蝶",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 PVP 化蝶`.",
                        },
                        {
                            "source_id": "bad_perfect_egg_with_pvp",
                            "url": "https://www.bilibili.com/video/BV1515151515/",
                            "title": "洛克王国S2利用回溯机制节省资源获得pvp精灵完美蛋",
                            "source_type": "mechanism_tutorial",
                            "target_archetype": "洛克王国世界PVP候选源：化蝶",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 PVP 化蝶`.",
                        },
                        {
                            "source_id": "bad_controller",
                            "url": "https://www.bilibili.com/video/BV9999999999/",
                            "title": "首发最强公测手柄完美爽玩保姆级攻略（附独家配置包）【洛克王国世界】",
                            "source_type": "team_explainer",
                            "target_archetype": "洛克王国世界PVP候选源：化蝶",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 化蝶 阵容 PVP`.",
                        },
                        {
                            "source_id": "bad_badge",
                            "url": "https://www.bilibili.com/video/BV1010101010/",
                            "title": "一个视频教会你如何拿到PVP最难获得的奖牌，摧枯拉朽（完整版）",
                            "source_type": "gameplay_replay",
                            "target_archetype": "洛克王国世界PVP候选源：化蝶",
                            "discovery_reason": "Agent discovered via query `洛克王国世界 化蝶 阵容 PVP`.",
                        },
                        {
                            "source_id": "bad_query_injected",
                            "url": "https://www.bilibili.com/video/BV1212121212/",
                            "title": "花衣蝶闪击了翼王？！世界观重塑中",
                            "source_type": "gameplay_replay",
                            "target_archetype": "洛克王国世界PVP候选源：圣羽翼王",
                            "target_entities": ["圣羽翼王"],
                            "discovery_reason": "Agent discovered via query `洛克王国世界 翼王 PVP 阵容`.",
                        },
                        {
                            "source_id": "good_matchup",
                            "url": "https://www.bilibili.com/video/BV5555555555/",
                            "title": "洛克王国世界 PVP 沙暴格斗对位实战",
                            "source_type": "matchup_counterplay",
                        },
                        {
                            "source_id": "good_focused_set_guide",
                            "url": "https://www.bilibili.com/video/BV1313131313/",
                            "title": "圣羽翼王无限连击保姆级攻略",
                            "source_type": "team_explainer",
                            "target_entities": ["圣羽翼王"],
                        },
                    ],
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertEqual(result["added_source_ids"], ["good_matchup", "good_focused_set_guide"])
            self.assertEqual(result["skipped_count"], 10)
            audit = yaml.safe_load((out_root / "audits/expand_test.yaml").read_text(encoding="utf-8"))
            skipped_reasons = [item["reasons"][0] for item in audit["skipped_candidates"]]
            self.assertIn("duplicate_bvid_page", skipped_reasons)
            self.assertIn("outside_pvp_battle_boundary", skipped_reasons)

    def test_allows_tournament_theory_and_move_signal_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(source_queue, {"schema_version": "p14.source_queue.v0", "sources": []})
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": [
                        {
                            "source_id": "good_luoshencup",
                            "url": "https://www.bilibili.com/video/BV1111111111/",
                            "title": "《洛克王国 世界》b站洛神杯决赛 收官日比赛解说",
                            "source_type": "gameplay_replay",
                        },
                        {
                            "source_id": "good_union_theory",
                            "url": "https://www.bilibili.com/video/BV2222222222/",
                            "title": "【洛神杯冠军都在学】洛克王国联攻理论基础 p01 基础概念",
                            "source_type": "mechanism_tutorial",
                        },
                        {
                            "source_id": "good_move_signal",
                            "url": "https://www.bilibili.com/video/BV3333333333/",
                            "title": "哪个神人教的一次打两发折射？？",
                            "source_type": "gameplay_replay",
                            "target_moves": ["折射"],
                        },
                    ],
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertEqual(
                result["added_source_ids"],
                ["good_luoshencup", "good_union_theory", "good_move_signal"],
            )
            updated = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            self.assertEqual(updated["sources"][-1]["target_moves"], ["折射"])

    def test_allows_anthology_page_candidate_when_whole_bv_is_already_known(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(
                source_queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "existing_whole",
                            "url": "https://www.bilibili.com/video/BV3333333333/",
                            "title": "洛克王国世界 PVP 合集 p01",
                            "source_type": "team_explainer",
                            "ingest_status": "transcript_unavailable_no_text",
                        }
                    ],
                },
            )
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": [
                        {
                            "source_id": "kgsrc_bili_bv3333333333_p05",
                            "url": "https://www.bilibili.com/video/BV3333333333/?p=5",
                            "anthology_page_index": 5,
                            "title": "洛克王国世界PVP阵容讲解 p05 对战音速犬",
                            "source_type": "team_explainer",
                            "target_entities": ["音速犬"],
                        }
                    ],
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertEqual(result["added_source_ids"], ["kgsrc_bili_bv3333333333_p05"])
            updated = yaml.safe_load(source_queue.read_text(encoding="utf-8"))
            added = updated["sources"][-1]
            self.assertEqual(added["url"], "https://www.bilibili.com/video/BV3333333333/?p=5")
            self.assertEqual(added["anthology_page_index"], 5)
            self.assertIn("anthology_page_source", added["source_quality_prior"]["promotion_bias"])

    def test_skips_resource_route_candidate_even_with_pvp_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(source_queue, {"schema_version": "p14.source_queue.v0", "sources": []})
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": [
                        {
                            "source_id": "bad_resource_route",
                            "url": "https://www.bilibili.com/video/BV1414141414/",
                            "title": "洛克王国世界 PVP 全图采集跑图路线 4800球攻略说明",
                            "source_type": "team_explainer",
                            "target_entities": ["圣羽翼王"],
                        },
                        {
                            "source_id": "good_pvp_guide",
                            "url": "https://www.bilibili.com/video/BV1515151515/",
                            "title": "洛克王国世界 PVP 圣羽翼王队伍讲解",
                            "source_type": "team_explainer",
                            "target_entities": ["圣羽翼王"],
                        },
                    ],
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertEqual(result["added_source_ids"], ["good_pvp_guide"])
            self.assertEqual(result["skipped_count"], 1)
            audit = yaml.safe_load((out_root / "audits/expand_test.yaml").read_text(encoding="utf-8"))
            self.assertEqual(audit["skipped_candidates"][0]["source_id"], "bad_resource_route")
            self.assertIn("outside_pvp_battle_boundary", audit["skipped_candidates"][0]["reasons"])

    def test_caps_new_sources_from_same_bvid_per_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_queue = root / "source_queue.yaml"
            candidate_file = root / "candidates.yaml"
            out_root = root / "knowledge_ops"
            _write_yaml(source_queue, {"schema_version": "p14.source_queue.v0", "sources": []})
            candidates = []
            for page in range(2, 7):
                candidates.append(
                    {
                        "source_id": f"kgsrc_bili_bv1616161616_p{page:02d}",
                        "url": f"https://www.bilibili.com/video/BV1616161616/?p={page}",
                        "anthology_page_index": page,
                        "title": f"洛克王国世界 PVP 阵容讲解 p{page:02d}",
                        "source_type": "team_explainer",
                        "target_entities": ["圣羽翼王"],
                    }
                )
            _write_yaml(
                candidate_file,
                {
                    "schema_version": "p14.source_queue_candidates.v0",
                    "batch_id": "candidate_test",
                    "candidates": candidates,
                },
            )

            result = run_source_queue_expand(
                candidate_file=candidate_file,
                source_queue=source_queue,
                out_root=out_root,
                batch_id="expand_test",
            )

            self.assertEqual(len(result["added_source_ids"]), 3)
            audit = yaml.safe_load((out_root / "audits/expand_test.yaml").read_text(encoding="utf-8"))
            skipped_reasons = [item["reasons"][0] for item in audit["skipped_candidates"]]
            self.assertEqual(skipped_reasons.count("diversity_bvid_cap"), 2)
            self.assertEqual(audit["summary"]["unique_bvid_added_count"], 1)


if __name__ == "__main__":
    unittest.main()
