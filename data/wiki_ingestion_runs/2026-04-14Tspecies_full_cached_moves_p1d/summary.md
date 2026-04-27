# P1d Wiki Battle Dex Dry-Run Summary

- Run ID: `2026-04-14Tspecies_full_cached_moves_p1d`
- Output directory: `/Users/okfin3/project/GitHub/OKFin33/Roco/data/wiki_ingestion_runs/2026-04-14Tspecies_full_cached_moves_p1d`
- Status: `completed_with_warnings`
- Database mutation: not performed

## Artifact Counts

- `ability_conflicts`: 1
- `derived_ability_candidates`: 181
- `move_candidates`: 491
- `raw_template_snapshots`: 1081
- `rejected_fields`: 6378
- `source_pages`: 1081
- `species_form_candidates`: 580
- `species_move_pool_candidates`: 22071
- `unresolved_move_names`: 3
- `validation_events`: 741

## Validation Summary

- `hard_reject`: 10
- `warning`: 731
- `info`: 0

### By Code

- `ability_description_conflict`: 1
- `empty_description_text`: 489
- `invalid_numeric_value`: 2
- `missing_ability_text`: 104
- `missing_optional_field`: 104
- `missing_required_field`: 10
- `move_name_unresolved`: 4
- `unexpected_source_field`: 27

## Unresolved Move Names

- 湿润印记
- 溶解液
- 龙之舞

## Ability Conflicts

- 溶解扩散

## Failure Reason

- None

## Recommended Next Action

- Parse-validate all artifacts.
- Review unresolved move names before any SQLite ingestion.
- Keep this run bounded until P1d acceptance criteria are met.
