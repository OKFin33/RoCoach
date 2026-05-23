# P1d Bounded Dry-Run Request For Session 019d8685-2728-7c50-b102-59a5ee5f43ef

## Purpose

This request is for continuing the Roco project in session:

- `019d8685-2728-7c50-b102-59a5ee5f43ef`

The target session should execute a broader but still bounded `P1d` wiki battle dex dry-run.

It must preserve SSD discipline and must not mutate SQLite.

## Required Context To Read First

Read these files before executing:

- `specs/爬session.md`
- `specs/总session.md`
- `log/project_log.md`
- `specs/p1c_crawler_cleaner_contract.md`
- `specs/wiki_crawler_cleaner_contract.yaml`
- `specs/p1b_minimal_battle_dex_schema.md`
- `specs/battle_dex_schema.yaml`
- `specs/field_alignment_matrix.yaml`
- `docs/wiki_field_discovery_review_2026-04-13.md`

Do not rely on chat memory alone.

## Current State

Completed:

- `P1a` field discovery
- `P1b` minimal battle dex schema
- `P1c` crawler/cleaner contract
- initial `P1d` dry-run tool and validator

Existing tools:

- `tools/wiki_battle_dex_dry_run.py`
- `tools/validate_p1c_artifacts.py`

Existing dry-run:

- `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run/`

Existing dry-run result:

- `source_pages`: 10
- `species_form_candidates`: 5
- `move_candidates`: 5
- `derived_ability_candidates`: 5
- `species_move_pool_candidates`: 226
- `hard_reject`: 0
- `warning`: 229
- `unresolved_move_names`: 154
- `ability_conflicts`: 0

Interpretation:

- the artifact pipeline works
- unresolved move names are high because the initial run only crawled 5 move detail pages
- this is not permission for full crawl

## Task

Run a broader bounded dry-run to improve move coverage and validate cleaner stability.

Recommended first attempt:

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --species-limit 50 \
  --move-limit 200 \
  --sleep-seconds 0.5 \
  --run-id 2026-04-14Tbounded_p1d_s50_m200
```

If the wiki API returns `567` or other transient server errors, do not hammer the site.

Fallback strategy:

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --species-limit 30 \
  --move-limit 50 \
  --sleep-seconds 1.0 \
  --run-id 2026-04-14Tbounded_p1d_s30_m50
```

If that still fails, stop and report the API instability. Do not implement aggressive retry loops.

## Mandatory Validation

After a successful run, validate artifacts:

```bash
python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/<run_id>
```

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

Optional system Python check:

```bash
python3 -m unittest discover -s tests
```

System Python may skip wiki helper tests if `mwparserfromhell` is not installed. That is acceptable if `.venv` tests pass.

## Required Report Back

Return:

- run directory
- exact command executed
- artifact validation result
- test result
- counts from `run_manifest.json`
- hard reject count
- warning count
- unresolved move name count
- ability conflict count
- top validation event codes
- whether unresolved move names decreased compared with `154`
- any API instability observed

## Acceptance Criteria

Accept the run if:

- all P1c artifacts exist
- JSON/JSONL validation passes
- `.venv` tests pass
- `hard_reject_count == 0`
- `ability_conflicts == 0`, or conflicts are explicitly listed
- unresolved move names are listed in `summary.md`
- no SQLite mutation occurred

If `hard_reject_count > 0`, stop and report.

## Forbidden Actions

Do not:

- perform full production crawl
- write to SQLite
- crawl standalone ability pages
- import `accuracy`, `PP`, or raw `cooldown`
- normalize move categories into Pokemon-like labels
- drop unresolved move names
- use community/meta data
- add uncontrolled schema fields
- increase retry pressure aggressively after Biligame `567`

## SSD Discipline

If the run reveals schema drift:

1. record the observed source field
2. map it back to `specs/field_alignment_matrix.yaml`
3. classify it as `confirmed`, `provisional`, or `forbidden_by_default`
4. update specs before changing implementation
5. log the decision in `log/project_log.md`

Do not patch the crawler to silently accept new fields.

## Suggested Opening Prompt

Use this prompt in session `019d8685-2728-7c50-b102-59a5ee5f43ef`:

```text
Read /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1d_bounded_dry_run_request_019d8685.md and the required context files listed inside it. Then execute the bounded P1d wiki battle dex dry-run exactly under that SSD contract. Do not mutate SQLite. Prefer the species=50, move=200 run; if Biligame API returns 567 or unstable server errors, fall back to species=30, move=50 with longer sleep. Validate artifacts and tests, then report counts, unresolved move names, hard rejects, ability conflicts, and API stability.
```
