from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.transcript_ab_refine import (
    CorrectionRule,
    TermRecord,
    apply_corrections,
    apply_guided_repairs,
    apply_source_profile_repairs,
    build_source_profile,
    exact_term_hits,
    guided_repair_candidates,
    split_paragraphs,
    strip_subtitle_markup,
)


class TranscriptABRefineTests(unittest.TestCase):
    def test_applies_pm_confirmed_correction_when_target_in_lexicon(self) -> None:
        lexicon = {
            "沙涌": TermRecord("沙涌", "A", "move"),
        }
        corrected, applied, blocked = apply_corrections(
            "这里沙咏开沙暴。",
            [CorrectionRule(raw="沙咏", canonical="沙涌", status="pm_confirmed")],
            lexicon,
        )

        self.assertEqual(corrected, "这里沙涌开沙暴。")
        self.assertEqual(applied[0]["raw"], "沙咏")
        self.assertEqual(blocked, [])

    def test_blocks_unreviewed_or_unknown_correction(self) -> None:
        corrected, applied, blocked = apply_corrections(
            "这里某某开局。",
            [CorrectionRule(raw="某某", canonical="不存在术语", status="unreviewed")],
            {},
        )

        self.assertEqual(corrected, "这里某某开局。")
        self.assertEqual(applied, [])
        self.assertEqual(blocked[0]["reason"], "target_not_in_ab_lexicon_or_not_pm_confirmed")

    def test_split_long_single_line_transcript(self) -> None:
        text = "第一句。第二句。第三句。第四句。"
        paragraphs = split_paragraphs(text)
        self.assertGreaterEqual(len(paragraphs), 1)
        self.assertIn("第一句", paragraphs[0])

    def test_split_newline_asr_transcript(self) -> None:
        text = "\n".join(f"第{i}行" for i in range(1, 18))
        paragraphs = split_paragraphs(text)
        self.assertGreaterEqual(len(paragraphs), 3)
        self.assertIn("第1行", paragraphs[0])
        self.assertIn("第9行", paragraphs[1])

    def test_strip_srt_markup(self) -> None:
        text = "1\n00:00:00,120 --> 00:00:02,260\n第一句\n\n2\n00:00:02,260 --> 00:00:03,380\n第二句\n"
        stripped = strip_subtitle_markup(text)
        self.assertEqual(stripped, "第一句\n第二句")

    def test_exact_term_hits_use_longest_non_overlapping_match(self) -> None:
        lexicon = {
            "极限撕裂": TermRecord("极限撕裂", "A", "move"),
            "撕裂": TermRecord("撕裂", "A", "move"),
        }

        hits = exact_term_hits("帕尔萨斯使用极限撕裂。", lexicon)

        self.assertEqual([hit["term"] for hit in hits], ["极限撕裂"])

    def test_exact_term_hits_keep_standalone_short_term(self) -> None:
        lexicon = {
            "极限撕裂": TermRecord("极限撕裂", "A", "move"),
            "撕裂": TermRecord("撕裂", "A", "move"),
        }

        hits = exact_term_hits("先用极限撕裂，再补一发撕裂。", lexicon)

        self.assertEqual([hit["term"] for hit in hits], ["极限撕裂", "撕裂"])

    def test_guided_repair_suggests_a_layer_species_candidate(self) -> None:
        lexicon = {
            "贝古斯": TermRecord("贝古斯", "A", "species"),
        }

        candidates = guided_repair_candidates("这里古斯会上场。", lexicon)

        self.assertTrue(any(item["span"] == "古斯" for item in candidates))
        best = next(item for item in candidates if item["span"] == "古斯")["candidates"][0]
        self.assertEqual(best["term"], "贝古斯")
        self.assertEqual(best["action"], "suggest")

    def test_guided_repair_can_auto_apply_only_at_high_confidence(self) -> None:
        repaired, applied = apply_guided_repairs(
            "这里贝古斯上场。",
            [
                {
                    "span": "贝古斯",
                    "candidates": [
                        {
                            "term": "贝古斯",
                            "score": 1.0,
                            "layer": "A",
                            "kind": "species",
                            "evidence": "char_similarity",
                            "action": "suggest",
                        }
                    ],
                },
                {
                    "span": "冰钻布鲁",
                    "candidates": [
                        {
                            "term": "冰钻布鲁斯",
                            "score": 0.97,
                            "layer": "A",
                            "kind": "species",
                            "evidence": "char_similarity",
                            "action": "auto_replace",
                        }
                    ],
                },
            ],
        )

        self.assertEqual(repaired, "这里贝古斯上场。")
        self.assertEqual(applied, [])

    def test_guided_repair_applies_auto_replace_candidate(self) -> None:
        repaired, applied = apply_guided_repairs(
            "这里冰钻布鲁上场。",
            [
                {
                    "span": "冰钻布鲁",
                    "candidates": [
                        {
                            "term": "冰钻布鲁斯",
                            "score": 0.97,
                            "layer": "A",
                            "kind": "species",
                            "evidence": "char_similarity",
                            "action": "auto_replace",
                        }
                    ],
                }
            ],
        )

        self.assertEqual(repaired, "这里冰钻布鲁斯上场。")
        self.assertEqual(applied[0]["canonical"], "冰钻布鲁斯")

    def test_source_profile_repairs_known_asr_phrase_cluster(self) -> None:
        lexicon = {
            "寒音蛇": TermRecord("寒音蛇", "A", "species"),
        }
        profile = build_source_profile("对面还没开韩英雄的示弱，最后拿下韩一球。", lexicon)

        repaired, applied = apply_source_profile_repairs(
            "对面还没开韩英雄的示弱，最后拿下韩一球。",
            lexicon,
            profile,
        )

        self.assertEqual(repaired, "对面还没开寒音蛇的示弱，最后拿下寒音蛇。")
        self.assertEqual([event["canonical"] for event in applied], ["寒音蛇", "寒音蛇"])

    def test_source_profile_repairs_wingking_composite_phrase(self) -> None:
        lexicon = {
            "圣羽翼王": TermRecord("圣羽翼王", "A", "species"),
            "水刃": TermRecord("水刃", "A", "move"),
        }
        profile = build_source_profile("后排有水人一王，还可以接电愿力。", lexicon)

        repaired, applied = apply_source_profile_repairs(
            "后排有水人一王，一个不慎就没法玩。",
            lexicon,
            profile,
        )

        self.assertEqual(repaired, "后排有水刃翼王，一个不慎就没法玩。")
        self.assertEqual(applied[0]["status"], "source_profile_auto")

    def test_source_profile_repairs_poison_team_short_aliases(self) -> None:
        lexicon = {
            "琉璃水母": TermRecord("琉璃水母", "A", "species"),
            "厉毒修萝": TermRecord("厉毒修萝", "A", "species"),
            "寂灭骨龙": TermRecord("寂灭骨龙", "A", "species"),
        }
        profile = build_source_profile("毒队里水母、古龙和修罗都能轮转。", lexicon)

        repaired, applied = apply_source_profile_repairs(
            "毒队里水母、古龙和修罗都能轮转。",
            lexicon,
            profile,
        )

        self.assertEqual(repaired, "毒队里琉璃水母、寂灭骨龙和厉毒修萝都能轮转。")
        self.assertEqual({event["canonical"] for event in applied}, {"琉璃水母", "寂灭骨龙", "厉毒修萝"})

    def test_source_profile_does_not_double_replace_existing_canonical(self) -> None:
        lexicon = {
            "琉璃水母": TermRecord("琉璃水母", "A", "species"),
        }
        profile = build_source_profile("毒队里琉璃水母继续叠毒。", lexicon)

        repaired, applied = apply_source_profile_repairs("琉璃水母继续叠毒。", lexicon, profile)

        self.assertEqual(repaired, "琉璃水母继续叠毒。")
        self.assertEqual(applied, [])

    def test_source_profile_repairs_same_source_species_asr_cluster(self) -> None:
        lexicon = {
            "贝古斯": TermRecord("贝古斯", "A", "species"),
        }
        profile = build_source_profile("贝古斯对位很好，贝伍斯上场后，被古斯一般会防御。", lexicon)

        repaired, applied = apply_source_profile_repairs(
            "贝伍斯上场后，被古斯一般会防御。",
            lexicon,
            profile,
        )

        self.assertEqual(repaired, "贝古斯上场后，贝古斯一般会防御。")
        self.assertEqual([event["canonical"] for event in applied], ["贝古斯", "贝古斯"])


if __name__ == "__main__":
    unittest.main()
