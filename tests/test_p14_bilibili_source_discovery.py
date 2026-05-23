import subprocess
import unittest
from unittest.mock import patch

from tools.p14_bilibili_source_discovery import (
    SearchHit,
    build_candidate,
    hard_reject_hit,
    has_roco_or_entity_signal,
    infer_entities,
    infer_source_type,
    parse_search_line,
    run_bilisearch,
    score_hit,
    select_diverse_candidates,
)


class P14BilibiliSourceDiscoveryTest(unittest.TestCase):
    def test_parse_search_line(self) -> None:
        line = 'BV123\t洛克王国世界PVP阵容讲解\t作者\t1778510821\t10000\t20\t120\t["pvp", "洛克王国"]'
        hit = parse_search_line(line, "洛克王国世界 PVP 阵容")

        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.bvid, "BV123")
        self.assertEqual(hit.tags, ["pvp", "洛克王国"])
        self.assertEqual(hit.view_count, 10000)

    def test_parse_search_line_canonicalizes_multi_part_bvid(self) -> None:
        line = 'BV1ABC_p5\t洛克王国世界PVP阵容讲解 p05\t作者\t1778510821\t10000\t20\t120\t["pvp"]'
        hit = parse_search_line(line, "洛克王国世界 PVP 阵容")

        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.bvid, "BV1ABC")
        self.assertEqual(hit.page_index, 5)

    def test_infer_source_type_prefers_mechanism(self) -> None:
        self.assertEqual(infer_source_type("洛克王国世界PVP速度线机制必修课"), "mechanism_tutorial")
        self.assertEqual(infer_source_type("洛神杯冠军都在学的洛克王国联攻理论基础"), "mechanism_tutorial")
        self.assertEqual(infer_source_type("洛克王国世界PVP周报热门阵容一览"), "tier_overview")
        self.assertEqual(infer_source_type("洛克王国世界S2平衡性调整精灵强度排行"), "tier_overview")
        self.assertEqual(infer_source_type("水刃翼王对线毒队翻盘思路"), "matchup_counterplay")
        self.assertEqual(infer_source_type("音速犬配招配置教学"), "team_explainer")

    def test_infer_entities_uses_aliases_and_species_names(self) -> None:
        entities = infer_entities("火狗和水刃翼王对线奇丽花", ["音速犬", "圣羽翼王", "奇丽花"])

        self.assertEqual(entities, ["圣羽翼王", "音速犬", "奇丽花"])

    def test_build_candidate_is_queue_substrate(self) -> None:
        hit = SearchHit(
            bvid="BV1ABC",
            title="洛克王国世界PVP音速犬高端局配招教学",
            uploader="作者",
            timestamp=1778510821,
            view_count=20000,
            like_count=100,
            duration=180.0,
            tags=["洛克王国", "pvp"],
            query="洛克王国世界 PVP 音速犬",
        )

        candidate = build_candidate(hit, ["音速犬"])
        score, reasons = score_hit(hit, ["音速犬"])

        self.assertGreaterEqual(score, 10)
        self.assertIn("battle_related", reasons)
        self.assertEqual(candidate["source_id"], "kgsrc_bili_bv1abc")
        self.assertEqual(candidate["url"], "https://www.bilibili.com/video/BV1ABC/")
        self.assertEqual(candidate["source_type"], "team_explainer")
        self.assertFalse(candidate.get("runtime_allowed", False))
        self.assertIn("音速犬", candidate["target_entities"])

    def test_build_candidate_preserves_anthology_page_identity(self) -> None:
        hit = SearchHit(
            bvid="BV1ABC",
            title="洛克王国世界PVP阵容讲解 p05 对战音速犬",
            uploader="作者",
            timestamp=1778510821,
            view_count=20000,
            like_count=100,
            duration=180.0,
            tags=["洛克王国", "pvp"],
            query="洛克王国世界 PVP 阵容",
            page_index=5,
        )

        candidate = build_candidate(hit, ["音速犬"])

        self.assertEqual(candidate["source_id"], "kgsrc_bili_bv1abc_p05")
        self.assertEqual(candidate["url"], "https://www.bilibili.com/video/BV1ABC/?p=5")
        self.assertEqual(candidate["anthology_page_index"], 5)

    def test_score_does_not_use_query_as_roco_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1OTHER",
            title="赛尔号pvp阵容组建教程",
            uploader="作者",
            timestamp=None,
            view_count=20000,
            like_count=100,
            duration=180.0,
            tags=["pvp"],
            query="洛克王国世界 PVP 队伍推荐",
        )

        score, reasons = score_hit(hit, [])
        candidate = build_candidate(hit, ["圣羽翼王"])

        self.assertNotIn("roco_related", reasons)
        self.assertGreaterEqual(score, 6)
        self.assertFalse(has_roco_or_entity_signal(hit, candidate))

    def test_entity_signal_can_keep_title_without_roco_word(self) -> None:
        hit = SearchHit(
            bvid="BV1WING",
            title="水刃翼王对线毒队翻盘思路",
            uploader="作者",
            timestamp=None,
            view_count=20000,
            like_count=100,
            duration=180.0,
            tags=["pvp"],
            query="洛克王国世界 PVP 队伍推荐",
        )
        candidate = build_candidate(hit, ["圣羽翼王"])

        self.assertTrue(has_roco_or_entity_signal(hit, candidate))
        self.assertIn("圣羽翼王", candidate["target_entities"])

    def test_move_signal_can_keep_title_without_roco_word(self) -> None:
        hit = SearchHit(
            bvid="BV1MOVE",
            title="哪个神人教的一次打两发折射？？",
            uploader="作者",
            timestamp=None,
            view_count=20000,
            like_count=100,
            duration=180.0,
            tags=["pvp"],
            query="洛克王国世界 PVP 折射",
        )
        candidate = build_candidate(hit, [], ["折射"])

        self.assertTrue(has_roco_or_entity_signal(hit, candidate))
        self.assertIn("折射", candidate["target_moves"])
        self.assertIn("a_layer_move_mentioned", candidate["source_quality_prior"]["promotion_bias"])

    def test_tournament_source_is_roco_battle_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1CUP",
            title="《洛克王国 世界》b站洛神杯决赛 收官日比赛解说",
            uploader="作者",
            timestamp=None,
            view_count=20000,
            like_count=100,
            duration=600.0,
            tags=[],
            query="洛克王国世界 洛神杯 PVP",
        )

        score, reasons = score_hit(hit, [])

        self.assertIsNone(hard_reject_hit(hit))
        self.assertGreaterEqual(score, 7)
        self.assertIn("roco_related", reasons)
        self.assertIn("battle_related", reasons)

    def test_hard_reject_non_pvp_clearance_guide(self) -> None:
        hit = SearchHit(
            bvid="BV1PVE",
            title="圣羽翼王无脑通关命定花种攻略【洛克王国】",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国"],
            query="洛克王国世界 PVP 圣羽翼王",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_dex_capture_without_battle_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1DEX",
            title="洛克王国世界精灵图鉴全收集：海豹船长，素材获取方式捕捉地点，及性格选择。",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国"],
            query="洛克王国世界 PVP 海豹船长",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_dex_or_capture_title")

    def test_hard_reject_breeding_log_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1EGG",
            title="孵蛋日志：两只恶魔狼喜欢打架的问题已初步确定",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 PVP 恶魔狼",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_breeding_or_resource_title")

    def test_hard_reject_perfect_egg_even_with_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1PVPegg",
            title="洛克王国S2利用回溯机制节省大量资源获得pvp精灵完美蛋",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 PVP 队伍推荐",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_breeding_or_resource_title")

    def test_hard_reject_magic_egg_guide_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1EGGGUIDE",
            title="【洛克王国：世界】神奇的蛋全攻略教程",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 PVP 队伍推荐",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_breeding_or_resource_title")

    def test_hard_reject_solo_clear_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1SOLO",
            title="单通翼王！对萌新最友好！",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 翼王 pvp",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_boss_title_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1BOSS",
            title="[雪影平衡] 实战思路解说 打boss合集",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 翼王 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_fast_clear_title_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1FAST",
            title="23秒过帕尔，1愿力秒翼王，确定不练一个？",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 翼王 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_fast_farm_title_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1FARM",
            title="一发愿力秒杀翼王！炽心勇狮三回合速刷两大传说精灵【洛克王国世界】",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 翼王 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_controller_setup_title_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1PAD",
            title="首发最强公测手柄完美爽玩保姆级攻略（附独家配置包）【洛克王国世界】",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 PVP 化蝶 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_non_battle_event_title")

    def test_hard_reject_pvp_badge_achievement_title(self) -> None:
        hit = SearchHit(
            bvid="BV1BADGE",
            title="一个视频教会你如何拿到PVP最难获得的奖牌，摧枯拉朽（完整版）",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 化蝶 阵容 PVP",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_non_battle_event_title")

    def test_hard_reject_event_news_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1NEWS",
            title="龙息帕尔副本周五开启，赛季奇遇精灵果实上线，刷异色难度降低",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 PVP 帕尔",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_main_quest_without_pvp_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1QUEST",
            title="【洛克王国世界】主线任务：闪闪翎羽 完成攻略",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 翼王 pvp",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_mingding_clearance_even_when_tags_have_pvp(self) -> None:
        hit = SearchHit(
            bvid="BV1MINGDING",
            title="第三期命定花种 嘟嘟锅 琉璃水母 九幽菇打法攻略合集 50级零练度简单好抄",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 PVP 奇丽花",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_pve_or_non_pvp_title")

    def test_hard_reject_capture_walkthrough_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1CAPTURE",
            title="限定幻系精灵 暮星辰 技能搭配 捕捉攻略 实战打法",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界"],
            query="洛克王国世界 PVP 寂灭骨龙",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_dex_or_capture_title")

    def test_hard_reject_material_route_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1MATERIAL",
            title="恶魔狼泛滥！全矿石、材料点位位置",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "pvp"],
            query="洛克王国世界 PVP 恶魔狼",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_dex_or_capture_title")

    def test_hard_reject_gathering_route_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1ROUTE",
            title="【洛克王国世界】奇丽花90分钟5000花+4000矿教学，18条线路任你选",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 星陨 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_resource_route_title")

    def test_hard_reject_acquisition_clickbait_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1GET",
            title="【洛克王国世界】全网最强陨星虫获取攻略，点击就送",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 星陨队 PVP",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_dex_or_capture_title")

    def test_hard_reject_capture_grab_word_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1GRAB",
            title="【洛克王国世界】新手必看的抓骨龙焚决，还有机会抓到被污染的骨龙",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 PVP 寂灭骨龙",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_dex_or_capture_title")

    def test_hard_reject_action_unlock_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1ACTION",
            title="紧急提醒！S1 限定动作，赛季结束马上绝版？全动作解锁攻略【洛克王国世界】",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 PVP 海豹船长",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_non_battle_event_title")

    def test_hard_reject_cosmetic_reward_without_pvp_title_signal(self) -> None:
        hit = SearchHit(
            bvid="BV1REWARD",
            title="【洛克王国世界】提醒：想白嫖 炫彩圣羽翼王 传说印记记得用！",
            uploader="作者",
            timestamp=None,
            view_count=1000,
            like_count=10,
            duration=100.0,
            tags=["洛克王国世界", "PVP"],
            query="洛克王国世界 翼王 阵容",
        )

        self.assertEqual(hard_reject_hit(hit), "off_boundary_non_battle_event_title")

    def test_select_diverse_candidates_caps_same_bvid_and_uploader(self) -> None:
        scored: list[tuple[int, dict[str, object]]] = []
        for index in range(1, 6):
            hit = SearchHit(
                bvid="BV1SAME",
                title=f"洛克王国世界PVP阵容讲解 p{index:02d}",
                uploader="作者A",
                timestamp=None,
                view_count=20000,
                like_count=100,
                duration=180.0,
                tags=["洛克王国", "PVP"],
                query="洛克王国世界 PVP 阵容",
                page_index=index + 1,
            )
            scored.append((12, build_candidate(hit, [])))
        for index in range(1, 5):
            hit = SearchHit(
                bvid=f"BV1OTHER{index}",
                title=f"洛克王国世界PVP队伍推荐 {index}",
                uploader="作者A",
                timestamp=None,
                view_count=20000,
                like_count=100,
                duration=180.0,
                tags=["洛克王国", "PVP"],
                query="洛克王国世界 PVP 队伍推荐",
            )
            scored.append((11, build_candidate(hit, [])))

        selected, skipped, summary = select_diverse_candidates(
            scored,
            max_candidates=10,
            max_per_bvid=3,
            max_per_uploader=5,
        )

        same_bvid_selected = [item for item in selected if item["source_id"].startswith("kgsrc_bili_bv1same")]
        self.assertEqual(len(same_bvid_selected), 3)
        self.assertLessEqual(len([item for item in selected if item.get("uploader") == "作者A"]), 5)
        skip_reasons = {item["reason"] for item in skipped}
        self.assertIn("diversity_bvid_cap", skip_reasons)
        self.assertIn("diversity_uploader_cap", skip_reasons)
        self.assertGreaterEqual(summary["selected_unique_bvid_count"], 3)

    def test_run_bilisearch_timeout_returns_diagnostics_instead_of_crashing(self) -> None:
        with patch(
            "tools.p14_bilibili_source_discovery.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["yt-dlp"], timeout=7),
        ):
            hits, diagnostics = run_bilisearch("洛克王国世界 PVP 阵容", per_query=3, timeout=7)

        self.assertEqual(hits, [])
        self.assertIn("yt-dlp_timeout_after=7s", diagnostics)


if __name__ == "__main__":
    unittest.main()
