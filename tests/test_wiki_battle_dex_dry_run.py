from __future__ import annotations

import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path

from tools.validate_p1c_artifacts import validate_artifacts


if find_spec("mwparserfromhell"):
    from tools.wiki_battle_dex_dry_run import (
        ArtifactWriter,
        DryRunBlocked,
        SCOPE_MOVE,
        SCOPE_SPECIES,
        canonical_move_lookup_name,
        load_cached_move_artifacts,
        manifest_limits,
        manifest_scopes,
        normalize_type,
        parse_int,
        split_list,
        stable_id,
        write_failed_artifacts,
    )


@unittest.skipUnless(find_spec("mwparserfromhell"), "mwparserfromhell is required for wiki dry-run helpers")
class WikiBattleDexDryRunHelperTests(unittest.TestCase):
    def test_normalize_type_maps_wiki_aliases(self) -> None:
        self.assertEqual(normalize_type("普"), "普通")
        self.assertEqual(normalize_type("械"), "机械")
        self.assertEqual(normalize_type("机械系"), "机械")
        self.assertIsNone(normalize_type(""))

    def test_split_list_preserves_move_names(self) -> None:
        self.assertEqual(split_list("防御,鬼火,勾魂"), ["防御", "鬼火", "勾魂"])
        self.assertEqual(split_list("防御、鬼火，勾魂"), ["防御", "鬼火", "勾魂"])

    def test_canonical_move_lookup_name_treats_skill_stone_page_as_move_reference(self) -> None:
        self.assertEqual(canonical_move_lookup_name("技能石/光刃"), "光刃")
        self.assertEqual(canonical_move_lookup_name("技能石／光刃"), "光刃")
        self.assertEqual(canonical_move_lookup_name("光刃"), "光刃")

    def test_parse_int_accepts_source_strings(self) -> None:
        self.assertEqual(parse_int("70"), 70)
        self.assertEqual(parse_int("威力 160"), 160)
        self.assertIsNone(parse_int(""))

    def test_stable_id_is_deterministic(self) -> None:
        self.assertEqual(stable_id("move", "防御"), stable_id("move", "防御"))
        self.assertNotEqual(stable_id("move", "防御"), stable_id("move", "鬼火"))

    def test_move_only_manifest_scope_does_not_request_species(self) -> None:
        class Args:
            scope = SCOPE_MOVE
            species_limit = 50
            move_limit = 10000

        self.assertEqual(manifest_scopes(Args.scope), ["move"])
        self.assertEqual(
            manifest_limits(Args()),
            {
                "species_detail_pages": 0,
                "move_detail_pages": 10000,
                "ability_embedded_species_pages": 0,
            },
        )

    def test_species_scope_uses_cached_moves_without_online_move_limit(self) -> None:
        class Args:
            scope = SCOPE_SPECIES
            species_limit = 50
            move_limit = 10000

        self.assertEqual(manifest_scopes(Args.scope), ["species", "move", "ability_embedded"])
        self.assertEqual(
            manifest_limits(Args()),
            {
                "species_detail_pages": 50,
                "move_detail_pages": 0,
                "ability_embedded_species_pages": 50,
            },
        )

    def test_load_cached_move_artifacts_filters_move_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp)
            writer = ArtifactWriter(input_dir)
            writer.write_jsonl(
                "source_pages.jsonl",
                [
                    {
                        "run_id": "old",
                        "source_page_id": "move_source",
                        "entity_hint": "move",
                        "page_title": "暴风眼",
                        "page_url": "https://example.test/move",
                        "revision_id": "1",
                        "revision_timestamp": "2026-04-14T00:00:00Z",
                        "fetched_at": "2026-04-14T00:00:00+00:00",
                        "content_sha256": "abc",
                        "content_length": 10,
                        "parser_version": "p1c-001",
                        "fetch_status": "ok",
                    },
                    {
                        "run_id": "old",
                        "source_page_id": "species_source",
                        "entity_hint": "species",
                        "page_title": "阿布",
                        "page_url": "https://example.test/species",
                        "revision_id": "2",
                        "revision_timestamp": "2026-04-14T00:00:00Z",
                        "fetched_at": "2026-04-14T00:00:00+00:00",
                        "content_sha256": "def",
                        "content_length": 10,
                        "parser_version": "p1c-001",
                        "fetch_status": "ok",
                    },
                ],
            )
            writer.write_jsonl(
                "raw_template_snapshots.jsonl",
                [
                    {
                        "run_id": "old",
                        "snapshot_id": "move_snapshot",
                        "source_page_id": "move_source",
                        "template_name": "技能信息",
                        "raw_fields": {"技能名称": "暴风眼"},
                        "field_order": ["技能名称"],
                        "extraction_warnings": [],
                    },
                    {
                        "run_id": "old",
                        "snapshot_id": "species_snapshot",
                        "source_page_id": "species_source",
                        "template_name": "精灵信息",
                        "raw_fields": {"精灵名称": "阿布"},
                        "field_order": ["精灵名称"],
                        "extraction_warnings": [],
                    },
                ],
            )

            sources, snapshots = load_cached_move_artifacts(input_dir, "new_run")
            self.assertEqual(len(sources), 1)
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(sources[0]["entity_hint"], "move")
            self.assertEqual(sources[0]["run_id"], "new_run")
            self.assertEqual(sources[0]["fetch_status"], "cached")
            self.assertEqual(snapshots[0]["template_name"], "技能信息")
            self.assertEqual(snapshots[0]["run_id"], "new_run")

    def test_validate_artifacts_accepts_empty_jsonl_files_with_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            writer = ArtifactWriter(output_dir)
            writer.write_json(
                "run_manifest.json",
                {
                    "run_id": "test",
                    "started_at": "2026-04-14T00:00:00+00:00",
                    "finished_at": "2026-04-14T00:00:01+00:00",
                    "run_mode": "dry_run",
                    "api_base_url": "https://example.test/api.php",
                    "parser_version": "p1c-001",
                    "schema_version": "battle_dex_schema.v1",
                    "field_alignment_matrix_version": "field_alignment_matrix.v2",
                    "scopes": ["species"],
                    "limits": {},
                    "artifact_files": {},
                    "counts": {},
                    "validation_summary": {},
                    "hard_reject_count": 0,
                    "warning_count": 0,
                    "status": "completed",
                    "failure_reason": None,
                    "fetch_strategy": "seed_titles",
                },
            )
            writer.write_json("dry_run_diff.json", {"run_id": "test"})
            writer.write_text("summary.md", "# Summary\n")
            for filename in (
                "source_pages.jsonl",
                "raw_template_snapshots.jsonl",
                "species_form_candidates.jsonl",
                "move_candidates.jsonl",
                "derived_ability_candidates.jsonl",
                "species_move_pool_candidates.jsonl",
                "validation_events.jsonl",
                "rejected_fields.jsonl",
            ):
                writer.write_jsonl(filename, [])

            result = validate_artifacts(output_dir)
            self.assertEqual(result["manifest_status"], "completed")

    def test_failed_artifacts_are_contract_valid(self) -> None:
        class Args:
            api_base_url = "https://example.test/api.php"
            scope = SCOPE_MOVE
            species_limit = 1
            move_limit = 1

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            writer = ArtifactWriter(output_dir)
            write_failed_artifacts(
                args=Args(),
                run_id="failed_test",
                output_dir=output_dir,
                writer=writer,
                started_at="2026-04-14T00:00:00+00:00",
                failure=DryRunBlocked("preflight failed", code="api_preflight_failed"),
            )
            result = validate_artifacts(output_dir)
            self.assertEqual(result["manifest_status"], "failed")


if __name__ == "__main__":
    unittest.main()
