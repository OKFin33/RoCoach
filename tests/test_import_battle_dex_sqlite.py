from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from argparse import Namespace
from contextlib import closing
from pathlib import Path

from tools.import_battle_dex_sqlite import write_sqlite
from tools.validate_p1f_write_inputs import validate_write_inputs


class ImportBattleDexSqliteTests(unittest.TestCase):
    def test_validate_write_inputs_accepts_current_policy_b_run(self) -> None:
        result = validate_write_inputs(
            Path("/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run")
        )
        self.assertTrue(result["eligible_for_write"])
        self.assertEqual(result["supplement_format"], "yaml")

    def test_write_sqlite_persists_expected_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "battle_dex.sqlite"
            importer_run_dir = Path("/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run")
            result = write_sqlite(
                Namespace(
                    importer_run_dir=importer_run_dir,
                    db_path=db_path,
                    schema_path=Path("/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_sqlite_schema_v1.sql"),
                    write_run_id="test_policy_b_write",
                    replace_run=False,
                )
            )
            self.assertEqual(result["import_run_id"], "test_policy_b_write")
            self.assertGreater(result["species_form_count"], 0)
            self.assertGreater(result["species_move_pool_count"], 0)

            with closing(sqlite3.connect(db_path)) as conn:
                species_count = conn.execute("SELECT COUNT(*) FROM species_form").fetchone()[0]
                move_count = conn.execute("SELECT COUNT(*) FROM move").fetchone()[0]
                excluded_count = conn.execute(
                    "SELECT COUNT(*) FROM import_entity_resolution WHERE resolution_status = 'excluded'"
                ).fetchone()[0]
                fire_form_rows = conn.execute(
                    "SELECT COUNT(*) FROM species_form WHERE display_name = '卡瓦重' AND regional_form_name = '火山附近的样子'"
                ).fetchone()[0]
                supplement_move = conn.execute(
                    "SELECT move_name, canonical_source_layer FROM move WHERE move_name = '湿润印记'"
                ).fetchone()
                available_move_row = conn.execute(
                    "SELECT COUNT(*) FROM species_available_moves"
                ).fetchone()[0]

            manifest = json.loads((importer_run_dir / "importer_run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(species_count, manifest["counts"]["resolved_species_forms"])
            self.assertEqual(move_count, manifest["counts"]["resolved_moves"])
            self.assertEqual(excluded_count, manifest["counts"]["excluded_entities"])
            self.assertEqual(fire_form_rows, 0)
            self.assertEqual(supplement_move, ("湿润印记", "manual_supplement"))
            self.assertGreater(available_move_row, 0)

    def test_same_import_run_requires_replace_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "battle_dex.sqlite"
            args = Namespace(
                importer_run_dir=Path("/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run"),
                db_path=db_path,
                schema_path=Path("/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_sqlite_schema_v1.sql"),
                write_run_id="duplicate_run",
                replace_run=False,
            )
            write_sqlite(args)
            with self.assertRaisesRegex(ValueError, "import_run_id already exists"):
                write_sqlite(args)


if __name__ == "__main__":
    unittest.main()
