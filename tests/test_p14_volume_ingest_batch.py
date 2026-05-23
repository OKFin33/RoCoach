import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.p14_volume_ingest_batch import (
    MAX_SUBTITLE_PARTS,
    _existing_ingest_result,
    _selected_source_ids,
    _subtitle_ingest_block,
)


class P14VolumeIngestBatchTest(unittest.TestCase):
    def test_implicit_limit_skips_selected_sources_that_are_already_processed(self) -> None:
        queue = {
            "latest_volume_batch_plan": {
                "selected_source_ids": ["already_done", "next_a", "next_b"],
            },
            "sources": [
                {"source_id": "already_done", "ingest_status": "set_pipeline_processed"},
                {"source_id": "next_a", "ingest_status": "queued"},
                {"source_id": "next_b", "ingest_status": "queued"},
            ],
        }

        self.assertEqual(
            _selected_source_ids(queue, limit=1, explicit_source_ids=[]),
            ["next_a"],
        )

    def test_explicit_source_ids_are_not_filtered_by_status(self) -> None:
        queue = {
            "latest_volume_batch_plan": {
                "selected_source_ids": ["already_done", "next_a"],
            },
            "sources": [
                {"source_id": "already_done", "ingest_status": "set_pipeline_processed"},
                {"source_id": "next_a", "ingest_status": "queued"},
            ],
        }

        self.assertEqual(
            _selected_source_ids(queue, limit=1, explicit_source_ids=["already_done"]),
            ["already_done"],
        )

    def test_subtitle_ingest_blocks_playlist_like_part_count(self) -> None:
        with TemporaryDirectory() as tmpdir:
            files: list[Path] = []
            for index in range(MAX_SUBTITLE_PARTS + 1):
                path = Path(tmpdir) / f"part_{index}.srt"
                path.write_text("字幕\n", encoding="utf-8")
                files.append(path)

            block = _subtitle_ingest_block(files)

        self.assertIsNotNone(block)
        assert block is not None
        self.assertEqual(block["reason"], "multi_part_subtitle_over_limit")
        self.assertEqual(block["subtitle_part_count"], MAX_SUBTITLE_PARTS + 1)

    def test_subtitle_ingest_allows_small_multi_track_subtitles(self) -> None:
        with TemporaryDirectory() as tmpdir:
            files = []
            for index in range(2):
                path = Path(tmpdir) / f"track_{index}.srt"
                path.write_text("字幕\n", encoding="utf-8")
                files.append(path)

            self.assertIsNone(_subtitle_ingest_block(files))

    def test_existing_ingest_result_preserves_artifact_paths_for_repair_reruns(self) -> None:
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "source_a"
            foundation_dir = run_dir / "evidence_foundation"
            foundation_dir.mkdir(parents=True)
            (foundation_dir / "segments.yaml").write_text("segments: []\n", encoding="utf-8")
            (foundation_dir / "quality_gate.yaml").write_text(
                "segment_count: 3\nclaim_atom_count: 1\nrepair_required_segments: []\n",
                encoding="utf-8",
            )
            (run_dir / "source_a.ab_refined.md").write_text("clean\n", encoding="utf-8")
            (run_dir / "source_a.manifest.yaml").write_text("paragraph_quality_counts:\n  good: 1\n", encoding="utf-8")
            (run_dir / "source_a.review_questions.yaml").write_text("[]\n", encoding="utf-8")
            (run_dir / "source_manifest.yaml").write_text("source_id: source_a\n", encoding="utf-8")
            (run_dir / "BVtest.ai-zh.srt").write_text("字幕\n", encoding="utf-8")

            result = _existing_ingest_result({"source_id": "source_a"}, run_dir)

        self.assertEqual(result["status"], "already_ingested")
        self.assertEqual(result["transcript_method"], "subtitle_ai_zh")
        self.assertTrue(result["evidence_foundation_dir"].endswith("evidence_foundation"))
        self.assertTrue(result["ab_refined_path"].endswith("source_a.ab_refined.md"))
        self.assertEqual(result["foundation_quality"]["segment_count"], 3)


if __name__ == "__main__":
    unittest.main()
