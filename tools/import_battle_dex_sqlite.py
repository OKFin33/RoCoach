#!/usr/bin/env python3
"""Write validated P1e importer dry-run artifacts into SQLite."""

from __future__ import annotations

import argparse
from contextlib import closing
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validate_p1e_importer_artifacts import iter_jsonl, load_json
from tools.validate_p1f_write_inputs import validate_write_inputs


DEFAULT_SCHEMA_PATH = Path("specs/battle_dex_sqlite_schema_v1.sql")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return iter_jsonl(path)


def create_staging_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TEMP TABLE staging_source_page (
          source_page_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL
        );
        CREATE TEMP TABLE staging_raw_template_snapshot (
          snapshot_id TEXT PRIMARY KEY,
          source_page_id TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );
        CREATE TEMP TABLE staging_species_form (
          species_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL
        );
        CREATE TEMP TABLE staging_move (
          move_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL
        );
        CREATE TEMP TABLE staging_derived_ability (
          ability_id TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL
        );
        CREATE TEMP TABLE staging_species_move_pool (
          species_id TEXT NOT NULL,
          move_name_raw TEXT NOT NULL,
          access_channel TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (species_id, move_name_raw, access_channel)
        );
        CREATE TEMP TABLE staging_import_entity_resolution (
          entity_type TEXT NOT NULL,
          entity_key TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (entity_type, entity_key)
        );
        """
    )


def load_staging(
    conn: sqlite3.Connection,
    *,
    source_pages: list[dict[str, Any]],
    raw_template_snapshots: list[dict[str, Any]],
    resolved_species_forms: list[dict[str, Any]],
    resolved_moves: list[dict[str, Any]],
    resolved_derived_abilities: list[dict[str, Any]],
    species_move_pool_rows: list[dict[str, Any]],
    import_entity_resolutions: list[dict[str, Any]],
) -> None:
    conn.executemany(
        "INSERT INTO staging_source_page (source_page_id, payload_json) VALUES (?, ?)",
        [(row["source_page_id"], json_text(row)) for row in source_pages],
    )
    conn.executemany(
        "INSERT INTO staging_raw_template_snapshot (snapshot_id, source_page_id, payload_json) VALUES (?, ?, ?)",
        [(row["snapshot_id"], row["source_page_id"], json_text(row)) for row in raw_template_snapshots],
    )
    conn.executemany(
        "INSERT INTO staging_species_form (species_id, payload_json) VALUES (?, ?)",
        [(row["species_id"], json_text(row)) for row in resolved_species_forms],
    )
    conn.executemany(
        "INSERT INTO staging_move (move_id, payload_json) VALUES (?, ?)",
        [(row["move_id"], json_text(row)) for row in resolved_moves],
    )
    conn.executemany(
        "INSERT INTO staging_derived_ability (ability_id, payload_json) VALUES (?, ?)",
        [(row["ability_id"], json_text(row)) for row in resolved_derived_abilities],
    )
    conn.executemany(
        "INSERT INTO staging_species_move_pool (species_id, move_name_raw, access_channel, payload_json) VALUES (?, ?, ?, ?)",
        [(row["species_id"], row["move_name_raw"], row["access_channel"], json_text(row)) for row in species_move_pool_rows],
    )
    conn.executemany(
        "INSERT INTO staging_import_entity_resolution (entity_type, entity_key, payload_json) VALUES (?, ?, ?)",
        [(row["entity_type"], row["entity_key"], json_text(row)) for row in import_entity_resolutions],
    )


def assert_staging_counts(conn: sqlite3.Connection, expected: dict[str, int]) -> None:
    checks = {
        "source_pages": ("staging_source_page", expected["source_pages"]),
        "raw_template_snapshots": ("staging_raw_template_snapshot", expected["raw_template_snapshots"]),
        "resolved_species_forms": ("staging_species_form", expected["resolved_species_forms"]),
        "resolved_moves": ("staging_move", expected["resolved_moves"]),
        "resolved_derived_abilities": ("staging_derived_ability", expected["resolved_derived_abilities"]),
        "species_move_pool": ("staging_species_move_pool", expected["species_move_pool"]),
        "import_entity_resolutions": ("staging_import_entity_resolution", expected["import_entity_resolutions"]),
    }
    for label, (table_name, expected_count) in checks.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        if actual != expected_count:
            raise ValueError(f"Staging count mismatch for {label}: expected {expected_count}, got {actual}")


def _existing_ids(conn: sqlite3.Connection, table: str, column: str) -> set[str]:
    rows = conn.execute(f"SELECT {column} FROM {table}").fetchall()
    return {row[0] for row in rows}


def validate_staging_gate(
    conn: sqlite3.Connection,
    *,
    resolved_species_forms: list[dict[str, Any]],
    resolved_moves: list[dict[str, Any]],
    species_move_pool_rows: list[dict[str, Any]],
) -> None:
    existing_species_ids = _existing_ids(conn, "species_form", "species_id")
    existing_move_ids = _existing_ids(conn, "move", "move_id")
    existing_source_page_ids = _existing_ids(conn, "source_page", "source_page_id")

    staging_species_ids = {row["species_id"] for row in resolved_species_forms}
    staging_move_ids = {row["move_id"] for row in resolved_moves}
    staging_source_page_ids = {
        row[0] for row in conn.execute("SELECT source_page_id FROM staging_source_page").fetchall()
    }

    for row in resolved_species_forms:
        if row["resolution_status"] not in {"included", "supplement_backed"}:
            raise ValueError(f"Species row leaked non-writable status: {row['species_id']}")
        source_page_id = row.get("source_page_id")
        if source_page_id and source_page_id not in staging_source_page_ids and source_page_id not in existing_source_page_ids:
            raise ValueError(f"Species row references missing source_page_id: {source_page_id}")

    for row in resolved_moves:
        if row["resolution_status"] not in {"included", "supplement_backed"}:
            raise ValueError(f"Move row leaked non-writable status: {row['move_id']}")
        source_page_id = row.get("source_page_id")
        if source_page_id and source_page_id not in staging_source_page_ids and source_page_id not in existing_source_page_ids:
            raise ValueError(f"Move row references missing source_page_id: {source_page_id}")

    valid_species_ids = staging_species_ids | existing_species_ids
    valid_move_ids = staging_move_ids | existing_move_ids
    valid_source_page_ids = staging_source_page_ids | existing_source_page_ids
    for row in species_move_pool_rows:
        if row["species_id"] not in valid_species_ids:
            raise ValueError(f"species_move_pool references missing species_id: {row['species_id']}")
        move_id = row.get("move_id")
        if move_id and move_id not in valid_move_ids:
            raise ValueError(f"species_move_pool references missing move_id: {move_id}")
        if row["source_page_id"] not in valid_source_page_ids:
            raise ValueError(f"species_move_pool references missing source_page_id: {row['source_page_id']}")


def delete_existing_run(conn: sqlite3.Connection, import_run_id: str) -> None:
    for table in (
        "species_move_pool",
        "derived_ability",
        "move",
        "species_form",
        "import_entity_resolution",
    ):
        conn.execute(f"DELETE FROM {table} WHERE import_run_id = ?", (import_run_id,))
    conn.execute("DELETE FROM import_run WHERE import_run_id = ?", (import_run_id,))


def upsert_source_pages(conn: sqlite3.Connection, source_pages: list[dict[str, Any]]) -> None:
    conn.executemany(
        """
        INSERT INTO source_page (
          source_page_id, entity_hint, page_title, page_url, revision_id, fetched_at, content_sha256, parser_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_page_id) DO UPDATE SET
          entity_hint=excluded.entity_hint,
          page_title=excluded.page_title,
          page_url=excluded.page_url,
          revision_id=excluded.revision_id,
          fetched_at=excluded.fetched_at,
          content_sha256=excluded.content_sha256,
          parser_version=excluded.parser_version
        """,
        [
            (
                row["source_page_id"],
                row["entity_hint"],
                row["page_title"],
                row["page_url"],
                row.get("revision_id"),
                row["fetched_at"],
                row["content_sha256"],
                row["parser_version"],
            )
            for row in source_pages
        ],
    )


def upsert_raw_template_snapshots(conn: sqlite3.Connection, snapshots: list[dict[str, Any]]) -> None:
    conn.executemany(
        """
        INSERT INTO raw_template_snapshot (
          snapshot_id, source_page_id, template_name, raw_fields_json, extraction_warnings_json
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(snapshot_id) DO UPDATE SET
          source_page_id=excluded.source_page_id,
          template_name=excluded.template_name,
          raw_fields_json=excluded.raw_fields_json,
          extraction_warnings_json=excluded.extraction_warnings_json
        """,
        [
            (
                row["snapshot_id"],
                row["source_page_id"],
                row["template_name"],
                json_text(row.get("raw_fields", {})),
                json_text(row.get("extraction_warnings", [])),
            )
            for row in snapshots
        ],
    )


def upsert_species_forms(conn: sqlite3.Connection, rows: list[dict[str, Any]], import_run_id: str, timestamp: str) -> None:
    conn.executemany(
        """
        INSERT INTO species_form (
          species_id, display_name, initial_species_name, form_name, regional_form_name, evolution_stage,
          primary_type, secondary_type, base_stats_json, ability_name, ability_effect_text, source_page_id,
          raw_snapshot_id, confidence, canonical_source_layer, wiki_source_refs_json, supplement_refs_json,
          resolution_reason, import_run_id, last_resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(species_id) DO UPDATE SET
          display_name=excluded.display_name,
          initial_species_name=excluded.initial_species_name,
          form_name=excluded.form_name,
          regional_form_name=excluded.regional_form_name,
          evolution_stage=excluded.evolution_stage,
          primary_type=excluded.primary_type,
          secondary_type=excluded.secondary_type,
          base_stats_json=excluded.base_stats_json,
          ability_name=excluded.ability_name,
          ability_effect_text=excluded.ability_effect_text,
          source_page_id=excluded.source_page_id,
          raw_snapshot_id=excluded.raw_snapshot_id,
          confidence=excluded.confidence,
          canonical_source_layer=excluded.canonical_source_layer,
          wiki_source_refs_json=excluded.wiki_source_refs_json,
          supplement_refs_json=excluded.supplement_refs_json,
          resolution_reason=excluded.resolution_reason,
          import_run_id=excluded.import_run_id,
          last_resolved_at=excluded.last_resolved_at
        """,
        [
            (
                row["species_id"],
                row["display_name"],
                row.get("initial_species_name"),
                row.get("form_name"),
                row.get("regional_form_name"),
                row.get("evolution_stage"),
                row["primary_type"],
                row.get("secondary_type"),
                json_text(row.get("base_stats", {})),
                row.get("ability_name"),
                row.get("ability_effect_text"),
                row["source_page_id"],
                row.get("raw_snapshot_id"),
                row["confidence"],
                row["canonical_source_layer"],
                json_text(row["wiki_source_refs"]),
                json_text(row["supplement_refs"]),
                row["resolution_reason"],
                import_run_id,
                timestamp,
            )
            for row in rows
        ],
    )


def upsert_moves(conn: sqlite3.Connection, rows: list[dict[str, Any]], import_run_id: str, timestamp: str) -> None:
    conn.executemany(
        """
        INSERT INTO move (
          move_id, move_name, move_type, category_raw, power, energy_cost, effect_text, description_text,
          source_version, source_page_id, raw_snapshot_id, confidence, canonical_source_layer, wiki_source_refs_json,
          supplement_refs_json, resolution_reason, import_run_id, last_resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(move_id) DO UPDATE SET
          move_name=excluded.move_name,
          move_type=excluded.move_type,
          category_raw=excluded.category_raw,
          power=excluded.power,
          energy_cost=excluded.energy_cost,
          effect_text=excluded.effect_text,
          description_text=excluded.description_text,
          source_version=excluded.source_version,
          source_page_id=excluded.source_page_id,
          raw_snapshot_id=excluded.raw_snapshot_id,
          confidence=excluded.confidence,
          canonical_source_layer=excluded.canonical_source_layer,
          wiki_source_refs_json=excluded.wiki_source_refs_json,
          supplement_refs_json=excluded.supplement_refs_json,
          resolution_reason=excluded.resolution_reason,
          import_run_id=excluded.import_run_id,
          last_resolved_at=excluded.last_resolved_at
        """,
        [
            (
                row["move_id"],
                row["move_name"],
                row.get("move_type"),
                row.get("category_raw"),
                row.get("power"),
                row.get("energy_cost"),
                row.get("effect_text"),
                row.get("description_text"),
                row.get("source_version"),
                row.get("source_page_id"),
                row.get("raw_snapshot_id"),
                row["confidence"],
                row["canonical_source_layer"],
                json_text(row["wiki_source_refs"]),
                json_text(row["supplement_refs"]),
                row["resolution_reason"],
                import_run_id,
                timestamp,
            )
            for row in rows
        ],
    )


def upsert_derived_abilities(conn: sqlite3.Connection, rows: list[dict[str, Any]], import_run_id: str, timestamp: str) -> None:
    conn.executemany(
        """
        INSERT INTO derived_ability (
          ability_id, ability_name, effect_text, source_species_ids_json, source_page_ids_json, derivation_status,
          confidence, canonical_source_layer, wiki_source_refs_json, supplement_refs_json, resolution_reason,
          import_run_id, last_resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ability_id) DO UPDATE SET
          ability_name=excluded.ability_name,
          effect_text=excluded.effect_text,
          source_species_ids_json=excluded.source_species_ids_json,
          source_page_ids_json=excluded.source_page_ids_json,
          derivation_status=excluded.derivation_status,
          confidence=excluded.confidence,
          canonical_source_layer=excluded.canonical_source_layer,
          wiki_source_refs_json=excluded.wiki_source_refs_json,
          supplement_refs_json=excluded.supplement_refs_json,
          resolution_reason=excluded.resolution_reason,
          import_run_id=excluded.import_run_id,
          last_resolved_at=excluded.last_resolved_at
        """,
        [
            (
                row["ability_id"],
                row["ability_name"],
                row["effect_text"],
                json_text(row["source_species_ids"]),
                json_text(row["source_page_ids"]),
                row["derivation_status"],
                row["confidence"],
                row["canonical_source_layer"],
                json_text(row["wiki_source_refs"]),
                json_text(row["supplement_refs"]),
                row["resolution_reason"],
                import_run_id,
                timestamp,
            )
            for row in rows
        ],
    )


def replace_species_move_pool(conn: sqlite3.Connection, rows: list[dict[str, Any]], import_run_id: str, timestamp: str) -> None:
    touched_species_ids = sorted({row["species_id"] for row in rows})
    if touched_species_ids:
        conn.executemany(
            "DELETE FROM species_move_pool WHERE species_id = ?",
            [(species_id,) for species_id in touched_species_ids],
        )
    conn.executemany(
        """
        INSERT INTO species_move_pool (
          species_id, move_name_raw, move_id, access_channel, unlock_level, source_field, confidence,
          source_page_id, import_run_id, last_resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["species_id"],
                row["move_name_raw"],
                row.get("move_id"),
                row["access_channel"],
                row.get("unlock_level"),
                row["source_field"],
                row["confidence"],
                row["source_page_id"],
                import_run_id,
                timestamp,
            )
            for row in rows
        ],
    )


def insert_import_entity_resolutions(conn: sqlite3.Connection, rows: list[dict[str, Any]], import_run_id: str, timestamp: str) -> None:
    conn.executemany(
        """
        INSERT INTO import_entity_resolution (
          entity_type, entity_key, resolution_status, canonical_source_layer, wiki_source_refs_json,
          supplement_refs_json, resolution_reason, import_run_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_type, entity_key, import_run_id) DO UPDATE SET
          resolution_status=excluded.resolution_status,
          canonical_source_layer=excluded.canonical_source_layer,
          wiki_source_refs_json=excluded.wiki_source_refs_json,
          supplement_refs_json=excluded.supplement_refs_json,
          resolution_reason=excluded.resolution_reason,
          created_at=excluded.created_at
        """,
        [
            (
                row["entity_type"],
                row["entity_key"],
                row["resolution_status"],
                row["canonical_source_layer"],
                json_text(row["wiki_source_refs"]),
                json_text(row["supplement_refs"]),
                row["resolution_reason"],
                import_run_id,
                timestamp,
            )
            for row in rows
        ],
    )


def insert_import_run(conn: sqlite3.Connection, *, import_run_id: str, manifest: dict[str, Any], timestamp: str) -> None:
    conn.execute(
        """
        INSERT INTO import_run (
          import_run_id, upstream_importer_run_id, policy_mode, canonical_artifact_dir, canonical_run_id,
          supplement_artifact_path, started_at, finished_at, write_mode, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            import_run_id,
            manifest["run_id"],
            manifest["policy_mode"],
            manifest["canonical_artifact_dir"],
            manifest["canonical_run_id"],
            manifest["supplement_path"],
            manifest["started_at"],
            manifest["finished_at"],
            "write",
            timestamp,
        ),
    )


def build_species_move_pool_rows(
    *,
    canonical_dir: Path,
    resolved_species_forms: list[dict[str, Any]],
    resolved_moves: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    move_pool_candidates = read_jsonl(canonical_dir / "species_move_pool_candidates.jsonl")
    included_species_ids = {row["species_id"] for row in resolved_species_forms}
    move_id_by_name = {row["move_name"]: row["move_id"] for row in resolved_moves}
    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row in move_pool_candidates:
        if row["species_id"] not in included_species_ids:
            continue
        resolved_move_id = row.get("move_id") or move_id_by_name.get(row["move_name_raw"])
        if not resolved_move_id:
            continue
        key = (row["species_id"], row["move_name_raw"], row["access_channel"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        rows.append({**row, "move_id": resolved_move_id})
    return rows


def collect_import_entity_resolutions(importer_run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for filename in (
        "resolved_species_forms.jsonl",
        "resolved_moves.jsonl",
        "resolved_derived_abilities.jsonl",
        "excluded_entities.jsonl",
        "review_required_entities.jsonl",
        "supplement_backed_entities.jsonl",
        "unresolved_entities.jsonl",
    ):
        rows.extend(read_jsonl(importer_run_dir / filename))
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        deduped[(row["entity_type"], row["entity_key"])] = row
    return list(deduped.values())


def write_sqlite(args: argparse.Namespace) -> dict[str, Any]:
    eligibility = validate_write_inputs(args.importer_run_dir)
    importer_manifest = load_json(args.importer_run_dir / "importer_run_manifest.json")
    canonical_dir = Path(importer_manifest["canonical_artifact_dir"])
    source_pages = read_jsonl(canonical_dir / "source_pages.jsonl")
    raw_template_snapshots = read_jsonl(canonical_dir / "raw_template_snapshots.jsonl")
    resolved_species_forms = read_jsonl(args.importer_run_dir / "resolved_species_forms.jsonl")
    resolved_moves = read_jsonl(args.importer_run_dir / "resolved_moves.jsonl")
    resolved_derived_abilities = read_jsonl(args.importer_run_dir / "resolved_derived_abilities.jsonl")
    species_move_pool_rows = build_species_move_pool_rows(
        canonical_dir=canonical_dir,
        resolved_species_forms=resolved_species_forms,
        resolved_moves=resolved_moves,
    )
    import_entity_resolutions = collect_import_entity_resolutions(args.importer_run_dir)

    import_run_id = args.write_run_id or f"{importer_manifest['run_id']}__write"
    timestamp = utc_now()
    schema_sql = args.schema_path.read_text(encoding="utf-8")
    args.db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(args.db_path, check_same_thread=False)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)

        existing = conn.execute("SELECT 1 FROM import_run WHERE import_run_id = ?", (import_run_id,)).fetchone()
        if existing:
            if not args.replace_run:
                raise ValueError(f"import_run_id already exists: {import_run_id}")
            delete_existing_run(conn, import_run_id)

        conn.execute("BEGIN")
        try:
            create_staging_tables(conn)
            load_staging(
                conn,
                source_pages=source_pages,
                raw_template_snapshots=raw_template_snapshots,
                resolved_species_forms=resolved_species_forms,
                resolved_moves=resolved_moves,
                resolved_derived_abilities=resolved_derived_abilities,
                species_move_pool_rows=species_move_pool_rows,
                import_entity_resolutions=import_entity_resolutions,
            )
            assert_staging_counts(
                conn,
                expected={
                    "source_pages": len(source_pages),
                    "raw_template_snapshots": len(raw_template_snapshots),
                    "resolved_species_forms": len(resolved_species_forms),
                    "resolved_moves": len(resolved_moves),
                    "resolved_derived_abilities": len(resolved_derived_abilities),
                    "species_move_pool": len(species_move_pool_rows),
                    "import_entity_resolutions": len(import_entity_resolutions),
                },
            )
            validate_staging_gate(
                conn,
                resolved_species_forms=resolved_species_forms,
                resolved_moves=resolved_moves,
                species_move_pool_rows=species_move_pool_rows,
            )
            insert_import_run(conn, import_run_id=import_run_id, manifest=importer_manifest, timestamp=timestamp)
            upsert_source_pages(conn, source_pages)
            upsert_raw_template_snapshots(conn, raw_template_snapshots)
            upsert_species_forms(conn, resolved_species_forms, import_run_id, timestamp)
            upsert_moves(conn, resolved_moves, import_run_id, timestamp)
            upsert_derived_abilities(conn, resolved_derived_abilities, import_run_id, timestamp)
            replace_species_move_pool(conn, species_move_pool_rows, import_run_id, timestamp)
            insert_import_entity_resolutions(conn, import_entity_resolutions, import_run_id, timestamp)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {
        "db_path": str(args.db_path),
        "import_run_id": import_run_id,
        "source_page_count": len(source_pages),
        "raw_template_snapshot_count": len(raw_template_snapshots),
        "species_form_count": len(resolved_species_forms),
        "move_count": len(resolved_moves),
        "derived_ability_count": len(resolved_derived_abilities),
        "species_move_pool_count": len(species_move_pool_rows),
        "import_entity_resolution_count": len(import_entity_resolutions),
        "eligibility": eligibility,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write validated P1e importer dry-run artifacts into SQLite.")
    parser.add_argument("--importer-run-dir", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--schema-path", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--write-run-id", default=None)
    parser.add_argument("--replace-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = write_sqlite(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
