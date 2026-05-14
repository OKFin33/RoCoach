# P1f DB Sync Minimal Context For Crawl Thread

Date: 2026-04-14

Purpose:

- sync only the minimum database-related context back to the crawl thread
- avoid re-litigating main-thread architecture in a crawl-focused session

## What Changed

Main thread has now completed:

- structured manual supplement promotion
- P1e importer dry-run stabilization
- P1f SQLite schema + write-path validator + write smoke test

Relevant artifacts:

- `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
- `specs/manual_battle_data_supplement_schema.yaml`
- `specs/battle_dex_sqlite_schema_v1.sql`
- `specs/p1f_sqlite_write_path_spec.md`
- `tools/import_battle_dex_dry_run.py`
- `tools/validate_p1f_write_inputs.py`
- `tools/import_battle_dex_sqlite.py`

## Current Importer Dry-Run Baseline

Current approved importer dry-run directory:

- `data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`

Current counts:

- `resolved_species_forms = 566`
- `resolved_moves = 494`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 0`
- `supplement_backed_entities = 5`
- `unresolved_entities = 0`

## Current Duplicate-Page Resolution Rule

Importer still treats same-`species_id` multi-page collisions as a review gate by default, but one PM-confirmed exception now exists:

- `权杖-V / 权杖-Ⅴ`

Applied resolution:

- treat both pages as the same playable species/form
- prefer `source_bc1c2be5441bb830` as the canonical source row
- normalize final output to:
  - `display_name = 权杖-V`
  - `initial_species_name = 权杖-II`
  - `evolution_stage = 最终形态`

Why this was safe:

- the conflict was judged to be naming / maintainer-style noise rather than a real gameplay distinction
- the chosen row matches the in-game dex screenshot baseline
- provenance for both wiki pages remains preserved in importer artifacts

Implication for crawl interpretation:

- a crawler run may still be structurally valid even if the importer later downgrades some species to `review_required`
- if future crawl artifacts expose the same collapse pattern, do not auto-hotfix in crawl without main-thread schema/normalization review unless a new manual canonical override is approved
- the previous placeholder zero-stat review batch has now been manually reclassified as excluded non-live / cut content; do not treat that batch as an active importer blocker

## SQLite Write Preconditions

SQLite write path currently requires:

1. validated P1e importer dry-run
2. `unresolved_entities = 0`
3. structured supplement input (`yaml/json`)
4. excluded entities must be policy-backed
5. review-required entities must stay out of final write set

## Current SQLite Shape

Current first-pass tables:

- `import_run`
- `source_page`
- `raw_template_snapshot`
- `species_form`
- `move`
- `derived_ability`
- `species_move_pool`
- `import_entity_resolution`

Current Engine-facing views:

- `species_available_moves`
- `species_combat_profile`

## Boundary For Crawl Thread

Do not:

- mutate SQLite
- redesign canonical normalization because of importer review gates
- silently merge duplicate canonical entities in crawl output

If the crawl thread encounters more same-`species_id` multi-page collisions:

- report them as evidence
- preserve provenance
- let main thread decide whether the fix belongs in crawl, cleaner, or importer
