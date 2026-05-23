from __future__ import annotations

import unittest

from tools.transcript_quality import transcript_quality_flags, transcript_quality_label


class TranscriptQualityTests(unittest.TestCase):
    def test_unresolved_asr_requires_repair(self) -> None:
        flags = transcript_quality_flags("邓回哥带来的压力很大，一个不慎牵野手死了。")

        self.assertIn("unresolved_asr:邓回哥", flags)
        self.assertEqual(transcript_quality_label(flags), "needs_repair")

    def test_multiple_suspect_markers_require_repair(self) -> None:
        flags = transcript_quality_flags("无际斩杀线，你也手打，仿前玩家。")

        self.assertEqual(transcript_quality_label(flags), "needs_repair")

    def test_single_suspect_marker_is_caution(self) -> None:
        flags = transcript_quality_flags("这里出现了韩一球。")

        self.assertEqual(transcript_quality_label(flags), "usable_with_caution")


if __name__ == "__main__":
    unittest.main()
