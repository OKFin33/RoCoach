# P1d Move-Full Bounded Dry-Run Request

Date: 2026-04-14

Purpose: ask the crawl-focused thread to build a complete move dictionary artifact before expanding species crawl scope.

This is an approved bounded dry-run request. It does not approve SQLite mutation or full production ingestion.

## Rationale

Current `species_move_pool` unresolved names are dominated by insufficient move detail coverage.

Expanding species first would mostly increase unresolved noise. Building fuller move coverage first makes later species move-pool matching meaningful.

## Required Context

Read these files before executing:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/爬session.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1d_fetch_resilience_change_context.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1c_crawler_cleaner_contract.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_crawler_cleaner_contract.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1b_minimal_battle_dex_schema.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/combat_ontology.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Do not rely on chat memory alone.

## Approved Scope

Allowed:

- scope limited to `分类:技能`
- parse only pages containing `{{技能信息}}`
- emit P1c artifact files
- generate a move dictionary artifact through the existing dry-run artifact contract
- run validator and tests
- report API stability

Forbidden:

- no SQLite mutation
- no standalone ability pages
- no species expansion for this task
- no full production crawl
- no community/meta data
- no imported fields such as `accuracy`, `PP`, or raw `cooldown`
- no silent schema expansion
- no aggressive retry pressure after Biligame `567`

## Current Tooling Constraint

Current tool:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/tools/wiki_battle_dex_dry_run.py`

Known issue:

- the current `fetch-clean` path historically fetched both species and moves
- this request needs move-only execution

Allowed implementation change:

- add a minimal move-only scope if needed, for example `--scope move` or equivalent
- move-only mode must still emit all required P1c artifacts
- species-related artifact files may be empty, but must exist
- manifest must report scope and counts clearly

Do not use this as permission to redesign the crawler broadly.

## Execution Plan

1. Validate existing baseline artifacts:

```bash
python3 tools/validate_p1c_artifacts.py \
  data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run
```

2. Run tests before online execution:

```bash
.venv/bin/python -m unittest discover -s tests
```

3. If move-only support is missing, implement the smallest necessary tool change and rerun tests.

4. Run move-full bounded dry-run.

Preferred command shape if move-only scope exists:

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --execution-mode fetch-clean \
  --scope move \
  --move-limit 10000 \
  --sleep-seconds 1.0 \
  --run-id 2026-04-14Tmove_full_bounded_p1d
```

If the actual number of move pages is known from bounded category enumeration, the tool may cap naturally at the category size.

5. If the API returns `567` or unstable server errors, stop after the existing bounded degradation path. Do not increase retry pressure.

6. Validate generated artifacts:

```bash
python3 tools/validate_p1c_artifacts.py \
  data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d
```

7. Run tests again:

```bash
.venv/bin/python -m unittest discover -s tests
```

Optional:

```bash
python3 -m unittest discover -s tests
```

System Python may skip wiki helper tests if `mwparserfromhell` is unavailable.

## Required Report Back

Return:

- exact command executed
- run directory
- manifest `status`
- `failure_reason`
- `fetch_strategy`
- total move candidate count
- hard reject count
- warning count
- move category distribution by `category_raw`
- count of empty `description_text`
- count and examples of invalid numeric fields, if any
- top validation event codes
- API stability notes
- confirmation that SQLite was not mutated
- confirmation that no standalone ability pages were crawled
- whether a move-only tool patch was needed

## Acceptance Criteria

Accept if:

- all P1c artifacts exist
- artifact validator passes
- `.venv` tests pass
- no SQLite mutation occurred
- no standalone ability pages were crawled
- move candidate count is reported
- category distribution is reported
- hard rejects are zero, or every hard reject is explicitly listed with source page and reason

If `hard_reject_count > 0`, stop and request main-thread review before any importer work.

## Suggested Opening Prompt

Use this in the crawl-focused thread:

```text
Read /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1d_move_full_bounded_dry_run_request.md and all required context files listed inside it. Execute the approved move-full bounded P1d dry-run under the existing artifact-only constraints. Scope is limited to 分类:技能 / {{技能信息}}. Do not mutate SQLite, do not crawl standalone ability pages, and do not expand species crawl. If current tooling lacks move-only scope, make only the minimal scope patch needed, run tests, then execute. Validate artifacts and report move count, hard rejects, category distribution, empty descriptions, invalid numeric fields, and API stability.
```
