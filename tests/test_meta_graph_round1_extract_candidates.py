from __future__ import annotations

import unittest

from tools.meta_graph_round1_extract_candidates import (
    Paragraph,
    _level_for,
    draft_candidates,
    parse_refined_paragraphs,
)
from tools.transcript_ab_refine import TermRecord


class MetaGraphRound1ExtractCandidatesTests(unittest.TestCase):
    def test_parse_refined_paragraphs_keeps_multiline_transcript_text(self) -> None:
        text = """# demo
## Transcript

### P001

- 原文：无
- 精校：首发十菠萝
使用蓄势待发
- 自动校正：无
- A/B 命中：蓄势待发[A/move]
"""

        paragraphs = parse_refined_paragraphs(text)

        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0].span_id, "P001")
        self.assertIn("首发十菠萝", paragraphs[0].text)
        self.assertIn("蓄势待发", paragraphs[0].text)

    def test_level_for_requires_species_and_move_for_l2(self) -> None:
        self.assertEqual(
            _level_for(
                {"species": ["十菠萝"], "move": ["蓄势待发"]},
                [],
                [],
            ),
            "L2",
        )
        self.assertEqual(
            _level_for(
                {"species": ["十菠萝"], "move": []},
                [{"label": "lead", "source_phrase": "首发"}],
                [],
            ),
            "L1",
        )

    def test_draft_candidates_never_outputs_runtime_allowed(self) -> None:
        lexicon = {
            "十菠萝": TermRecord("十菠萝", "A", "species"),
            "雪影娃娃": TermRecord("雪影娃娃", "A", "species"),
            "蓄势待发": TermRecord("蓄势待发", "A", "move"),
        }
        set_payload, edge_payload, counters = draft_candidates(
            "demo",
            "demo.md",
            [Paragraph("P001", "首发十菠萝使用蓄势待发给雪影娃娃")],
            lexicon,
            {"十菠萝": "species_a", "雪影娃娃": "species_b"},
        )

        self.assertFalse(set_payload["runtime_allowed"])
        self.assertFalse(edge_payload["runtime_allowed"])
        self.assertEqual(set_payload["candidate_sets"][0]["level"], "L2")
        self.assertEqual(edge_payload["candidate_edges"][0]["level"], "L3")
        self.assertEqual(counters["L2"], 1)


if __name__ == "__main__":
    unittest.main()
