# P1d Wiki Battle Dex Dry-Run Summary

- Run ID: `2026-04-14Tspecies_cached_moves_s50`
- Output directory: `/Users/okfin3/project/GitHub/OKFin33/Roco/data/wiki_ingestion_runs/2026-04-14Tspecies_cached_moves_s50`
- Status: `completed_with_warnings`
- Database mutation: not performed

## Artifact Counts

- `ability_conflicts`: 0
- `derived_ability_candidates`: 24
- `move_candidates`: 491
- `raw_template_snapshots`: 541
- `rejected_fields`: 542
- `source_pages`: 541
- `species_form_candidates`: 50
- `species_move_pool_candidates`: 2059
- `unresolved_move_names`: 1
- `validation_events`: 505

## Validation Summary

- `hard_reject`: 0
- `warning`: 505
- `info`: 0

### By Code

- `empty_description_text`: 489
- `missing_ability_text`: 7
- `missing_optional_field`: 7
- `move_name_unresolved`: 1
- `unexpected_source_field`: 1

## Unresolved Move Names

- 龙之舞

## Ability Conflicts

- None

## Failure Reason

- None

## Recommended Next Action

- Parse-validate all artifacts.
- Review unresolved move names before any SQLite ingestion.
- Keep this run bounded until P1d acceptance criteria are met.
