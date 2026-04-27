from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from advisor.contracts import (
    AbilityDexRecord,
    DexBaseStats,
    MoveDexRecord,
    SpeciesDexRecord,
    SpeciesMoveRecord,
    SpeciesSearchHit,
)
from reporting.contracts import ConfidenceTier
from tools.import_battle_dex_sqlite import write_sqlite
from tools.validate_p1f_write_inputs import validate_write_inputs


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DB = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
IMPORTER_RUNS_DIR = REPO_ROOT / "data" / "importer_runs"
SCHEMA_PATH = REPO_ROOT / "specs" / "battle_dex_sqlite_schema_v1.sql"

STAT_KEY_MAP = {
    "生命": "hp",
    "物攻": "atk",
    "物防": "defense",
    "魔攻": "spa",
    "魔防": "spd",
    "速度": "spe",
}


def find_latest_importer_run(base_dir: Path = IMPORTER_RUNS_DIR) -> Path:
    candidates = sorted(path for path in base_dir.iterdir() if (path / "importer_run_manifest.json").exists())
    if not candidates:
        raise FileNotFoundError(f"No importer run manifest found under {base_dir}")

    eligible_candidates: list[Path] = []
    for candidate in candidates:
        try:
            validation = validate_write_inputs(candidate)
        except Exception:
            continue
        if validation.get("eligible_for_write"):
            eligible_candidates.append(candidate)

    if not eligible_candidates:
        raise FileNotFoundError(f"No write-eligible importer run found under {base_dir}")
    return eligible_candidates[-1]


def ensure_battle_dex_sqlite(
    db_path: Path = DEFAULT_RUNTIME_DB,
    *,
    importer_run_dir: Path | None = None,
) -> Path:
    if db_path.exists():
        return db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_importer_run = importer_run_dir or find_latest_importer_run()
    write_sqlite(
        argparse.Namespace(
            importer_run_dir=resolved_importer_run,
            db_path=db_path,
            schema_path=SCHEMA_PATH,
            write_run_id="advisor_runtime_bootstrap",
            replace_run=True,
        )
    )
    return db_path


class BattleDexRepository:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    def close(self) -> None:
        return None

    def __enter__(self) -> "BattleDexRepository":
        self._ensure_db_exists()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def search_species(self, query: str, *, limit: int = 5) -> list[SpeciesSearchHit]:
        needle = query.strip()
        if not needle:
            return []

        rows = self._fetchall(
            """
            SELECT species_id, display_name, initial_species_name, primary_type, secondary_type
            FROM species_form
            WHERE species_id = ?
               OR display_name = ?
               OR initial_species_name = ?
               OR display_name LIKE ?
               OR initial_species_name LIKE ?
            ORDER BY
              CASE
                WHEN species_id = ? THEN 0
                WHEN display_name = ? THEN 1
                WHEN initial_species_name = ? AND display_name != ? THEN 2
                ELSE 3
              END,
              LENGTH(display_name),
              display_name
            LIMIT ?
            """,
            (
                needle,
                needle,
                needle,
                f"%{needle}%",
                f"%{needle}%",
                needle,
                needle,
                needle,
                needle,
                limit,
            ),
        )
        return [SpeciesSearchHit.model_validate(dict(row)) for row in rows]

    def get_species_profile(self, query: str) -> SpeciesDexRecord | None:
        row = self._fetchone(
            """
            SELECT
              species_id,
              display_name,
              initial_species_name,
              form_name,
              regional_form_name,
              evolution_stage,
              primary_type,
              secondary_type,
              base_stats_json,
              ability_name,
              ability_effect_text,
              confidence,
              canonical_source_layer,
              source_page_id,
              import_run_id
            FROM species_form
            WHERE species_id = ?
               OR display_name = ?
               OR initial_species_name = ?
            ORDER BY
              CASE
                WHEN species_id = ? THEN 0
                WHEN display_name = ? THEN 1
                WHEN initial_species_name = ? AND display_name != ? THEN 2
                ELSE 3
              END,
              LENGTH(display_name),
              display_name
            LIMIT 1
            """,
            (query, query, query, query, query, query, query),
        )
        if row is None:
            hits = self.search_species(query, limit=1)
            if not hits:
                return None
            row = self._fetchone(
                """
                SELECT
                  species_id,
                  display_name,
                  initial_species_name,
                  form_name,
                  regional_form_name,
                  evolution_stage,
                  primary_type,
                  secondary_type,
                  base_stats_json,
                  ability_name,
                  ability_effect_text,
                  confidence,
                  canonical_source_layer,
                  source_page_id,
                  import_run_id
                FROM species_form
                WHERE species_id = ?
                LIMIT 1
                """,
                (hits[0].species_id,),
            )
        if row is None:
            return None

        payload = dict(row)
        payload["base_stats"] = self._parse_base_stats(payload.pop("base_stats_json"))
        payload["confidence"] = ConfidenceTier(payload["confidence"])
        return SpeciesDexRecord.model_validate(payload)

    def get_species_available_moves(self, query: str, *, limit: int | None = None) -> list[SpeciesMoveRecord]:
        species = self.get_species_profile(query)
        if species is None:
            return []

        sql = """
            SELECT
              smp.species_id,
              smp.move_id,
              COALESCE(m.move_name, smp.move_name_raw) AS move_name,
              m.move_type,
              m.category_raw,
              smp.access_channel,
              smp.unlock_level,
              m.power,
              m.effect_text
            FROM species_move_pool AS smp
            LEFT JOIN move AS m ON m.move_id = smp.move_id
            WHERE smp.species_id = ?
            ORDER BY
              CASE smp.access_channel
                WHEN 'level_up' THEN 0
                WHEN 'skill_stone' THEN 1
                WHEN 'bloodline' THEN 2
                ELSE 3
              END,
              COALESCE(smp.unlock_level, 999),
              move_name
        """
        params: list[object] = [species.species_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self._fetchall(sql, tuple(params))
        return [SpeciesMoveRecord.model_validate(dict(row)) for row in rows]

    def get_move_detail(self, query: str) -> MoveDexRecord | None:
        row = self._fetchone(
            """
            SELECT
              move_id,
              move_name,
              move_type,
              category_raw,
              power,
              energy_cost,
              effect_text,
              description_text,
              confidence,
              canonical_source_layer
            FROM move
            WHERE move_id = ?
               OR move_name = ?
            ORDER BY LENGTH(move_name), move_name
            LIMIT 1
            """,
            (query, query),
        )
        if row is None:
            row = self._fetchone(
                """
                SELECT
                  move_id,
                  move_name,
                  move_type,
                  category_raw,
                  power,
                  energy_cost,
                  effect_text,
                  description_text,
                  confidence,
                  canonical_source_layer
                FROM move
                WHERE move_name LIKE ?
                ORDER BY LENGTH(move_name), move_name
                LIMIT 1
                """,
                (f"%{query}%",),
            )
        if row is None:
            return None
        payload = dict(row)
        payload["confidence"] = ConfidenceTier(payload["confidence"])
        return MoveDexRecord.model_validate(payload)

    def get_ability_detail(self, query: str) -> AbilityDexRecord | None:
        row = self._fetchone(
            """
            SELECT
              ability_id,
              ability_name,
              effect_text,
              confidence,
              canonical_source_layer,
              derivation_status
            FROM derived_ability
            WHERE ability_id = ?
               OR ability_name = ?
            ORDER BY LENGTH(ability_name), ability_name
            LIMIT 1
            """,
            (query, query),
        )
        if row is not None:
            payload = dict(row)
            payload["confidence"] = ConfidenceTier(payload["confidence"])
            return AbilityDexRecord.model_validate(payload)

        fallback_row = self._fetchone(
            """
            SELECT
              species_id AS ability_id,
              ability_name,
              ability_effect_text AS effect_text,
              confidence,
              canonical_source_layer
            FROM species_form
            WHERE ability_name = ?
            ORDER BY LENGTH(display_name), display_name
            LIMIT 1
            """,
            (query,),
        )
        if fallback_row is None:
            return None
        payload = dict(fallback_row)
        payload["confidence"] = ConfidenceTier(payload["confidence"])
        payload["derivation_status"] = None
        return AbilityDexRecord.model_validate(payload)

    def iter_species_names(self) -> Iterable[str]:
        rows = self._fetchall(
            "SELECT display_name FROM species_form ORDER BY LENGTH(display_name) DESC, display_name"
        )
        for row in rows:
            yield row[0]

    def _ensure_db_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Battle dex SQLite not found: {self.db_path}")

    def _fetchone(self, sql: str, params: tuple[object, ...]) -> sqlite3.Row | None:
        self._ensure_db_exists()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchone()

    def _fetchall(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        self._ensure_db_exists()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchall()

    def _parse_base_stats(self, raw_json: str) -> DexBaseStats:
        raw = json.loads(raw_json)
        payload = {target: int(raw[source]) for source, target in STAT_KEY_MAP.items()}
        return DexBaseStats.model_validate(payload)
