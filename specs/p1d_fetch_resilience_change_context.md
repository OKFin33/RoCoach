# P1d Fetch Resilience Lightweight Context

Date: 2026-04-14

This note only records the crawler-related changes made in the main thread after the blocked P1d dry-run.

## Why This Was Changed

The crawl thread reported that P1d failed on Biligame API `567`.

The important finding was not just "API unstable"; the crawler design was too brittle:

- fallback still used the same failing batch request shape
- category enumeration was broader than a bounded dry-run should require
- fetch failures did not emit contract-valid failed artifacts
- cleaner/parser validation required hitting the live wiki again

## What Changed

Updated:

- `tools/wiki_battle_dex_dry_run.py`
- `tools/validate_p1c_artifacts.py`
- `tests/test_wiki_battle_dex_dry_run.py`
- `specs/p1c_crawler_cleaner_contract.md`
- `specs/wiki_crawler_cleaner_contract.yaml`
- `log/project_log.md`

Main behavior changes:

- Added API preflight before broader fetches.
- Limited category enumeration to bounded sample needs.
- Added detail fetch degradation: `40` batch -> `10` batch -> single title.
- Failed fetch/preflight now emits full artifacts with `run_manifest.status=failed`.
- Added `--execution-mode clean-only` to regenerate cleaned artifacts from cached snapshots without touching the wiki.
- Validator now requires `failure_reason` and `fetch_strategy` in `run_manifest.json`.

## How To Use

Validate existing baseline:

```bash
python3 tools/validate_p1c_artifacts.py \
  data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run
```

Run cleaner offline from cached baseline:

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --execution-mode clean-only \
  --clean-input-dir data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run \
  --run-id 2026-04-14Tclean_only_validation \
  --output-dir data/wiki_ingestion_runs/2026-04-14Tclean_only_validation
```

Validate offline cleaner output:

```bash
python3 tools/validate_p1c_artifacts.py \
  data/wiki_ingestion_runs/2026-04-14Tclean_only_validation
```

If API is stable, next crawl-thread retry should start small:

```bash
.venv/bin/python tools/wiki_battle_dex_dry_run.py \
  --execution-mode fetch-clean \
  --species-limit 30 \
  --move-limit 50 \
  --sleep-seconds 1.0 \
  --run-id 2026-04-14Tbounded_p1d_s30_m50_retry
```

## Validation Done

Passed:

```bash
python3 -m py_compile tools/wiki_battle_dex_dry_run.py tools/validate_p1c_artifacts.py
.venv/bin/python -m unittest discover -s tests
python3 -m unittest discover -s tests
python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run
python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14Tclean_only_validation
python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14Tfailed_preflight_validation
```

## Boundary

Main thread owns SSD, contract, schema, and acceptance criteria.

Crawl thread should own bounded online dry-runs, API stability handling, and crawl artifacts.

Do not:

- mutate SQLite
- full crawl
- crawl standalone ability pages
- increase retry pressure
- silently expand schema
