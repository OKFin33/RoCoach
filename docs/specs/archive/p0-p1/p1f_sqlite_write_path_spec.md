# P1f SQLite Write-Path Spec

Date: 2026-04-14

Purpose: define the first approved path from importer dry-run artifacts to a SQLite battle dex.

This spec does not itself authorize production writes. It defines the contract a
later implementation must satisfy before write approval.

## Scope

This phase covers:

- SQLite table DDL for first-pass battle dex storage
- importer write-path behavior
- migration and idempotency expectations

This phase does not cover:

- legality filtering
- Agent orchestration
- live wiki crawling
- automatic conflict adjudication

## Write Preconditions

The write-path may run only when all of the following are true:

1. input is a validated P1e importer dry-run directory
2. `unresolved_entities.jsonl` count is `0`
3. every excluded entity is policy-backed, not parser-failed noise
4. review-required entities are explicitly kept out of the write set
5. the supplement input is a structured YAML/JSON artifact, not markdown-only parsing

## Input Contract

Required dry-run files:

- `importer_run_manifest.json`
- `resolved_species_forms.jsonl`
- `resolved_moves.jsonl`
- `resolved_derived_abilities.jsonl`
- `excluded_entities.jsonl`
- `review_required_entities.jsonl`
- `supplement_backed_entities.jsonl`
- `unresolved_entities.jsonl`

Required metadata:

- `policy_mode = policy_b`
- `sqlite_mutation = false` on the upstream dry-run
- canonical artifact run id
- supplement artifact path

## Write Strategy

### Phase 1: Staging Load

Load dry-run rows into staging tables keyed by `import_run_id`.

Rules:

- do not write directly from JSONL into final tables
- reject the write if staging counts differ from manifest counts
- keep one staging snapshot per import run for auditability

### Phase 2: Validation Gate

Before merge into final tables:

- ensure primary keys are unique inside staging
- ensure every foreign key target exists in staging or already in final canonical tables
- ensure excluded and review-required entities are absent from staging write sets
- ensure supplement-backed rows preserve `canonical_source_layer` and provenance refs

If any of these fail:

- abort transaction
- emit a write-failure report
- do not partially merge

### Phase 3: Transactional Merge

Merge inside a single SQLite transaction.

Rules:

- use deterministic upsert on canonical ids
- update final rows only from `included` or `supplement_backed` dry-run rows
- preserve previous rows when the new run does not mention them
- record `import_run_id` and `last_resolved_at` on touched rows

### Phase 4: Post-Write Views

Refresh or recreate Engine-facing views:

- `species_available_moves`
- `species_combat_profile`

These views remain derived products, not primary source tables.

## Idempotency

Re-running the same dry-run input must be safe.

Required behavior:

- same `import_run_id` cannot be applied twice unless `--replace-run` is explicitly requested
- same canonical row content should not create duplicates
- repeated writes from the same artifact should converge to the same final table contents

## Provenance Requirements

Final tables must preserve:

- `canonical_source_layer`
- `wiki_source_refs`
- `supplement_refs`
- `resolution_reason`
- `import_run_id`
- `last_resolved_at`

## First SQLite Approval Boundary

The first approved write implementation may write only:

- `source_page`
- `raw_template_snapshot`
- `species_form`
- `move`
- `derived_ability`
- `species_move_pool`
- `import_run`
- `import_entity_resolution`

Do not write:

- mechanics notes
- legality-layer tables
- inferred role labels
- meta snapshot tables

## Required Deliverables Before Write Approval

- SQLite DDL file
- importer write-path tool spec
- dry-run-to-write validator
- one local smoke test against a disposable SQLite file
- rollback behavior description
