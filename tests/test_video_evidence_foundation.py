from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.transcript_ab_refine import CorrectionRule, TermRecord
from tools.video_evidence_foundation import (
    build_claim_atoms,
    build_quality_summary,
    build_source_manifest_v2,
    refine_evidence_segments,
    segments_from_bailian_payload,
    segments_from_srt_text,
)


class VideoEvidenceFoundationTests(unittest.TestCase):
    def test_bailian_segments_preserve_sentence_timing_without_provider_url(self) -> None:
        payload = {
            "file_url": "https://temporary.example.invalid/audio.mp3",
            "transcripts": [
                {
                    "channel_id": 0,
                    "text": "ignored full text",
                    "sentences": [
                        {
                            "sentence_id": 7,
                            "begin_time": 1200,
                            "end_time": 3400,
                            "text": "针叶巡林使用沙涌。",
                            "words": [],
                        }
                    ],
                }
            ],
        }

        segments = segments_from_bailian_payload(payload)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["source_kind"], "bailian_asr_sentence")
        self.assertEqual(segments[0]["start_ms"], 1200)
        self.assertEqual(segments[0]["end_ms"], 3400)
        self.assertNotIn("file_url", segments[0])

    def test_srt_segments_preserve_cue_timing(self) -> None:
        text = "1\n00:00:01,200 --> 00:00:03,400\n针叶巡林使用沙涌。\n"

        segments = segments_from_srt_text(text)

        self.assertEqual(segments[0]["source_kind"], "subtitle_srt_cue")
        self.assertEqual(segments[0]["start_ms"], 1200)
        self.assertEqual(segments[0]["end_ms"], 3400)

    def test_refined_segment_quality_gate_and_claim_atom(self) -> None:
        lexicon = {
            "针叶巡林": TermRecord("针叶巡林", "A", "species"),
            "沙涌": TermRecord("沙涌", "A", "move"),
        }
        rules = [CorrectionRule(raw="沙咏", canonical="沙涌", status="pm_confirmed")]
        segments = [
            {
                "segment_id": "S0001",
                "source_segment_id": "1",
                "source_kind": "subtitle_srt_cue",
                "channel_id": None,
                "start_ms": 1200,
                "end_ms": 3400,
                "raw_text": "针叶巡林首发使用沙咏开沙暴。",
            }
        ]

        refined = refine_evidence_segments(segments, lexicon, rules)
        atoms = build_claim_atoms("demo_source", refined)
        summary = build_quality_summary(refined, atoms)

        self.assertEqual(refined[0]["refined_text"], "针叶巡林首发使用沙涌开沙暴。")
        self.assertEqual(refined[0]["quality_gate"], "claim_ready")
        self.assertTrue(refined[0]["claim_extraction_allowed"])
        self.assertTrue(any(atom["predicate"] == "has_role" for atom in atoms))
        self.assertTrue(any(atom["predicate"] == "source_mentions_move" for atom in atoms))
        self.assertEqual(summary["quality_gate_counts"]["claim_ready"], 1)
        self.assertFalse(any(atom["runtime_allowed"] for atom in atoms))

    def test_multi_species_move_atom_is_marked_ambiguous(self) -> None:
        segment = {
            "segment_id": "S0001",
            "raw_text": "雪影娃娃使用赤子之心，然后把效果给寂灭骨龙或者音速犬。",
            "refined_text": "雪影娃娃使用赤子之心，然后把效果给寂灭骨龙或者音速犬。",
            "ab_hits": [
                {"term": "雪影娃娃", "layer": "A", "kind": "species"},
                {"term": "寂灭骨龙", "layer": "A", "kind": "species"},
                {"term": "音速犬", "layer": "A", "kind": "species"},
                {"term": "赤子之心", "layer": "A", "kind": "move"},
            ],
            "quality_gate": "claim_ready",
            "claim_extraction_allowed": True,
            "start_ms": 1000,
            "end_ms": 3000,
        }

        atoms = build_claim_atoms("demo_source", [segment])
        move_atom = next(atom for atom in atoms if atom["atom_type"] == "species_move_mention")
        synergy_atom = next(atom for atom in atoms if atom["predicate"] == "has_synergy")

        self.assertEqual(move_atom["predicate"], "segment_mentions_move")
        self.assertEqual(move_atom["subject"], "")
        self.assertEqual(move_atom["subject_resolution_status"], "ambiguous_multi_species")
        self.assertEqual(synergy_atom["subject"], "雪影娃娃")
        self.assertEqual(synergy_atom["object"]["targets"], ["寂灭骨龙", "音速犬"])

    def test_implicit_starfall_layer_phrase_creates_mechanism_atom(self) -> None:
        segment = {
            "segment_id": "S0001",
            "raw_text": "七层星陨。",
            "refined_text": "七层星陨。",
            "ab_hits": [],
            "quality_gate": "coverage_only",
            "claim_extraction_allowed": False,
            "start_ms": 1000,
            "end_ms": 3000,
        }

        atoms = build_claim_atoms("demo_source", [segment])

        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0]["atom_type"], "mechanism_claim")
        self.assertEqual(atoms[0]["subject"], "星陨印记")
        self.assertIn("星陨印记", atoms[0]["mentioned_mechanisms"])
        self.assertEqual(atoms[0]["quality_gate"], "coverage_only")

    def test_layer_phrase_without_mechanism_anchor_does_not_create_mark_claim(self) -> None:
        segment = {
            "segment_id": "S0001",
            "raw_text": "20层帕尔萨斯的极限撕裂。",
            "refined_text": "20层帕尔萨斯的极限撕裂。",
            "ab_hits": [
                {"term": "帕尔萨斯", "layer": "A", "kind": "species"},
                {"term": "极限撕裂", "layer": "A", "kind": "move"},
            ],
            "quality_gate": "claim_ready",
            "claim_extraction_allowed": True,
            "start_ms": 1000,
            "end_ms": 3000,
        }

        atoms = build_claim_atoms("demo_source", [segment])

        self.assertFalse(any(atom["atom_type"] == "mechanism_claim" for atom in atoms))

    def test_source_manifest_v2_does_not_copy_provider_file_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_source_manifest_v2(
                source_id="demo",
                source_type="community_video",
                transcript_method="bailian_hotword_asr_v3",
                segment_source="bailian_asr_json_sentences",
                source_manifest_v1={"url": "https://www.bilibili.com/video/BVxxxx", "title": "demo"},
                source_manifest_path=None,
                run_dir=root,
                out_dir=root / "foundation",
                asr_json_path=root / "asr.json",
                transcript_path=None,
                ab_refined_path=None,
                ab_manifest_path=None,
                title=None,
                source_url=None,
                lexicon_counts={"a_layer_terms": 1, "b_layer_terms": 1},
                quality_summary={"segment_count": 1, "runtime_allowed": False},
            )

        rendered = str(manifest)
        self.assertIn("BVxxxx", rendered)
        self.assertNotIn("file_url", rendered)
        self.assertFalse(manifest["runtime_allowed"])


if __name__ == "__main__":
    unittest.main()
