# P1d Wiki Battle Dex Dry-Run Summary

- Run ID: `2026-04-14Tfailed_preflight_validation`
- Output directory: `/Users/okfin3/project/GitHub/OKFin33/Roco/data/wiki_ingestion_runs/2026-04-14Tfailed_preflight_validation`
- Status: `failed`
- Database mutation: not performed

## Artifact Counts

- `derived_ability_candidates`: 0
- `move_candidates`: 0
- `raw_template_snapshots`: 0
- `rejected_fields`: 0
- `source_pages`: 0
- `species_form_candidates`: 0
- `species_move_pool_candidates`: 0
- `validation_events`: 1

## Validation Summary

- `hard_reject`: 1
- `warning`: 0
- `info`: 0

### By Code

- `api_preflight_failed`: 1

## Unresolved Move Names

- None

## Ability Conflicts

- None

## Failure Reason

- API preflight failed: MediaWiki API request failed after 3 attempts: HTTPConnectionPool(host='127.0.0.1', port=9): Max retries exceeded with url: /api.php?action=query&meta=siteinfo&siprop=general&format=json (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [Errno 61] Connection refused"))

## Recommended Next Action

- Parse-validate all artifacts.
- Review unresolved move names before any SQLite ingestion.
- Keep this run bounded until P1d acceptance criteria are met.
