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
from knowledge.contracts import ConfidenceTier
from tools.import_battle_dex_sqlite import write_sqlite
from tools.validate_p1f_write_inputs import validate_write_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
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


def _strip_form_suffix(name: str | None) -> str:
    if not name:
        return ""
    full_width_index = name.find("（")
    half_width_index = name.find("(")
    indexes = [index for index in (full_width_index, half_width_index) if index >= 0]
    if not indexes:
        return name.strip()
    return name[: min(indexes)].strip()


def _species_search_names(hit: SpeciesSearchHit) -> tuple[str, str]:
    return hit.display_name.strip(), _strip_form_suffix(hit.initial_species_name)


def _species_search_matches(hit: SpeciesSearchHit, needle: str) -> bool:
    display_name, initial_base_name = _species_search_names(hit)
    return (
        hit.species_id == needle
        or display_name == needle
        or initial_base_name == needle
        or display_name.startswith(needle)
        or initial_base_name.startswith(needle)
        or needle in display_name
        or needle in initial_base_name
    )


def _species_search_rank(hit: SpeciesSearchHit, needle: str) -> tuple[int, int, str, str]:
    display_name, initial_base_name = _species_search_names(hit)
    if hit.species_id == needle:
        rank = 0
    elif display_name == needle:
        rank = 1
    elif initial_base_name == needle and display_name != needle:
        rank = 2
    elif display_name.startswith(needle):
        rank = 3
    elif initial_base_name.startswith(needle):
        rank = 4
    else:
        rank = 5
    return rank, len(display_name), display_name, hit.species_id


def _species_row_is_team_builder_eligible(row: sqlite3.Row) -> bool:
    return bool(row["ability_name"]) and int(row["available_move_count"] or 0) > 0


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

    def search_species(
        self,
        query: str,
        *,
        limit: int = 5,
        team_builder_eligible_only: bool = False,
    ) -> list[SpeciesSearchHit]:
        needle = query.strip()
        if not needle:
            return []

        rows = self._fetchall(
            """
            SELECT
              species_id,
              display_name,
              initial_species_name,
              form_name,
              regional_form_name,
              primary_type,
              secondary_type,
              ability_name,
              (
                SELECT COUNT(*)
                FROM species_available_moves AS sam
                WHERE sam.species_id = species_form.species_id
              ) AS available_move_count
            FROM species_form
            WHERE species_id = ?
               OR display_name = ?
               OR initial_species_name = ?
               OR display_name LIKE ?
               OR initial_species_name LIKE ?
               OR display_name LIKE ?
               OR initial_species_name LIKE ?
            ORDER BY
              CASE
                WHEN species_id = ? THEN 0
                WHEN display_name = ? THEN 1
                WHEN initial_species_name = ? AND display_name != ? THEN 2
                WHEN display_name LIKE ? THEN 3
                WHEN initial_species_name LIKE ? THEN 4
                ELSE 5
              END,
              LENGTH(display_name),
              display_name
            LIMIT ?
            """,
            (
                needle,
                needle,
                needle,
                f"{needle}%",
                f"{needle}%",
                f"%{needle}%",
                f"%{needle}%",
                needle,
                needle,
                needle,
                needle,
                f"{needle}%",
                f"{needle}%",
                max(limit * 8, 80),
            ),
        )
        hits: list[SpeciesSearchHit] = []
        for row in rows:
            if team_builder_eligible_only and not _species_row_is_team_builder_eligible(row):
                continue
            hit = SpeciesSearchHit.model_validate(dict(row))
            if _species_search_matches(hit, needle):
                hits.append(hit)
        hits.sort(key=lambda hit: _species_search_rank(hit, needle))

        # Exact-name searches must preserve form variants for disambiguation.
        if any(_species_search_rank(hit, needle)[0] <= 2 for hit in hits):
            return hits[:limit]

        # Broad searches should not let one multi-form species fill the whole list.
        unique_first: list[SpeciesSearchHit] = []
        overflow_forms: list[SpeciesSearchHit] = []
        seen_display_names: set[str] = set()
        for hit in hits:
            if hit.display_name in seen_display_names:
                overflow_forms.append(hit)
                continue
            seen_display_names.add(hit.display_name)
            unique_first.append(hit)
            if len(unique_first) >= limit:
                break

        if len(unique_first) < limit:
            unique_first.extend(overflow_forms[: limit - len(unique_first)])
        return unique_first[:limit]

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
