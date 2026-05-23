# P1d Species-Only With Cached Move Dictionary Bounded Dry-Run Request

Date: 2026-04-14

Purpose: ask the crawl-focused thread to validate species learnset matching against the already-crawled full move dictionary without re-fetching move detail pages online.

This is an approved bounded dry-run request. It does not approve SQLite mutation or full production ingestion.

## Rationale

The move dictionary dry-run already produced `491` move candidates from `分类:技能`.

The next useful bounded check is not another repeated move crawl. It is a species-focused run that reuses the cached move source snapshots so `species_move_pool` matching can be measured cleanly.

## Required Context

Read these files before executing:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/爬session.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1d_fetch_resilience_change_context.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1c_crawler_cleaner_contract.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_crawler_cleaner_contract.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1b_minimal_battle_dex_schema.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

## Approved Scope

Allowed:

- online scope limited to species detail pages from `分类:精灵`
- move dictionary must be loaded from cached artifacts under:
  - `data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d`
- parse only structured templates:
  - species: `{{精灵信息}}`
  - move: cached `{{技能信息}}`
- emit normal P1c artifact files
- run validator and tests

Forbidden:

- no SQLite mutation
- no standalone ability pages
- no online move-page re-fetch for this task
- no full production crawl
- no silent schema expansion

## Tooling Requirement

The crawler may add the smallest necessary implementation to support:

- `--scope species`
- `--cached-move-input-dir`

Species scope should:

- fetch species detail pages online
- load cached move `source_pages.jsonl` and `raw_template_snapshots.jsonl`
- rebuild move candidates inside the new run
- match `species_move_pool` against the cached move dictionary

## Preferred Command Shape

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --execution-mode fetch-clean \
  --scope species \
  --cached-move-input-dir data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d \
  --species-limit 50 \
  --sleep-seconds 1.0 \
  --run-id 2026-04-14Tspecies_cached_moves_s50
```

If Biligame returns `567` or unstable server errors, reduce species limit and keep or increase sleep. Do not add retry pressure.

## Required Report Back

Return:

- exact command executed
- run directory
- manifest `status`
- `failure_reason`
- `fetch_strategy`
- species count
- move count reused from cache
- species move-pool count
- unresolved move-name count
- top unresolved examples
- hard rejects
- ability conflicts
- API stability notes
- confirmation that SQLite was not mutated

## Acceptance Criteria

Accept if:

- all P1c artifacts exist
- artifact validator passes
- `.venv` tests pass
- no SQLite mutation occurred
- no online move-page fetch was required
- unresolved move-name count is reported
- hard rejects are zero, or every hard reject is explicitly listed with source page and reason
