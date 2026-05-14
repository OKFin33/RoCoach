# P1c Crawler And Cleaner Contract

## Purpose

Define the contract between wiki crawling, data cleaning, and later ingestion.

This spec tells a crawler thread exactly what to output. It does not approve full production ingestion. It authorizes only bounded dry-run generation of candidate artifacts that can be reviewed before writing to SQLite.

## Position In The Workflow

- `P1a`: field discovery completed
- `P1b`: minimal battle dex schema drafted
- `P1c`: crawler and cleaner output contract
- `P1d`: bounded ingestion dry-run

## Non-Negotiable Constraints

The crawler/cleaner must:

- perform a lightweight API preflight before broader fetches
- use MediaWiki API revision content when possible
- parse templates rather than scraping rendered HTML as the primary source
- preserve original wiki field labels
- emit source trace for every normalized candidate
- run in bounded mode by default
- write artifacts only, not mutate SQLite
- retain unresolved names instead of dropping records
- produce a validation summary and diff-ready manifest
- emit a failed manifest and empty contract artifacts if the run fails before candidate generation
- support cleaner validation from cached source snapshots without refetching the wiki

The crawler/cleaner must not:

- create production database records directly
- infer fields from Pokemon-like schemas
- emit raw `accuracy`, `PP`, or `cooldown`
- crawl standalone ability pages unless a later discovery run proves they exist
- use community content as primary field evidence
- enumerate full categories when a bounded sample or cached seed titles are sufficient
- retry aggressively after Biligame `567` or other transient server errors

## Run Directory

Each dry-run writes to:

```text
data/wiki_ingestion_runs/{run_id}/
```

Required files:

- `run_manifest.json`
- `source_pages.jsonl`
- `raw_template_snapshots.jsonl`
- `species_form_candidates.jsonl`
- `move_candidates.jsonl`
- `derived_ability_candidates.jsonl`
- `species_move_pool_candidates.jsonl`
- `validation_events.jsonl`
- `rejected_fields.jsonl`
- `dry_run_diff.json`
- `summary.md`

Rules:

- `run_id` should be timestamp based, e.g. `2026-04-14T120000Z_p1c_dry_run`
- JSONL files must contain one JSON object per line
- all records must include `run_id`
- all normalized records must include `source_page_id`
- artifacts must be parseable without importing project code

## Input Configuration

The crawler command should accept a config equivalent to:

```yaml
run_mode: dry_run
scopes:
  - species
  - move
  - ability_embedded
limits:
  species_detail_pages: 50
  move_detail_pages: 50
  ability_embedded_species_pages: 50
source:
  api_base_url: https://wiki.biligame.com/rocom/api.php
parser:
  parser_version: p1c-001
  preferred_templates:
    species: 精灵信息
    move: 技能信息
    ability_embedded: 精灵信息
output:
  output_dir: data/wiki_ingestion_runs/{run_id}
```

Default execution must be bounded. Full crawl requires a separate explicit approval.

## Artifact Contracts

### `run_manifest.json`

Purpose:

- summarize the run and make artifacts auditable

Required fields:

- `run_id`
- `started_at`
- `finished_at`
- `run_mode`
- `api_base_url`
- `parser_version`
- `schema_version`
- `field_alignment_matrix_version`
- `scopes`
- `limits`
- `artifact_files`
- `counts`
- `validation_summary`
- `hard_reject_count`
- `warning_count`
- `status`
- `failure_reason`, nullable
- `fetch_strategy`

Allowed `status`:

- `completed`
- `completed_with_warnings`
- `failed`

If `status=failed`:

- all required artifact files must still exist
- candidate JSONL files may be empty
- `validation_events.jsonl` must include the blocking error
- `summary.md` must explain the failed stage
- `dry_run_diff.json` must set `requires_pm_review=true`

Allowed `fetch_strategy` values:

- `api_preflight`
- `seed_titles`
- `limited_categorymembers`
- `cached_source_pages`

### `source_pages.jsonl`

One record per fetched page.

Required fields:

- `run_id`
- `source_page_id`
- `entity_hint`
- `page_title`
- `page_url`
- `revision_id`
- `revision_timestamp`
- `fetched_at`
- `content_sha256`
- `content_length`
- `parser_version`
- `fetch_status`

Allowed `entity_hint`:

- `species`
- `move`
- `ability_embedded`
- `unknown`

Allowed `fetch_status`:

- `ok`
- `missing`
- `error`

### `raw_template_snapshots.jsonl`

One record per parsed structured template.

Required fields:

- `run_id`
- `snapshot_id`
- `source_page_id`
- `template_name`
- `raw_fields`
- `field_order`
- `extraction_warnings`

Allowed `template_name`:

- `精灵信息`
- `技能信息`
- `unknown`

Rules:

- `raw_fields` must preserve original labels and unnormalized source values
- empty source fields should be preserved if their label is relevant to schema review
- unexpected labels must be preserved and also emitted to `validation_events.jsonl`

### `species_form_candidates.jsonl`

One record per normalized species/form candidate.

Required fields:

- `run_id`
- `species_id`
- `display_name`
- `initial_species_name`
- `form_name`
- `regional_form_name`
- `evolution_stage`
- `primary_type`
- `secondary_type`
- `base_stats`
- `ability_name`
- `ability_effect_text`
- `source_page_id`
- `raw_snapshot_id`
- `confidence`
- `normalization_warnings`

Rules:

- `base_stats` must use game-native keys: `生命`, `物攻`, `魔攻`, `物防`, `魔防`, `速度`
- `species_id` must be deterministic from source identity and form identity
- missing optional fields should be `null`, not omitted
- invalid type names are hard rejects

### `move_candidates.jsonl`

One record per normalized move candidate.

Required fields:

- `run_id`
- `move_id`
- `move_name`
- `move_type`
- `category_raw`
- `power`
- `energy_cost`
- `effect_text`
- `description_text`
- `source_version`
- `source_page_id`
- `raw_snapshot_id`
- `confidence`
- `normalization_warnings`

Rules:

- `category_raw` must remain one of the observed game-native values
- `power` may be `0`
- `power`, `energy_cost`, and numeric fields must be parsed from source strings with warnings on coercion
- do not emit `accuracy`
- do not emit `PP`
- do not emit raw `cooldown`

### `derived_ability_candidates.jsonl`

One record per locally derived ability candidate.

Required fields:

- `run_id`
- `ability_id`
- `ability_name`
- `effect_text`
- `source_species_ids`
- `source_page_ids`
- `derivation_status`
- `confidence`
- `normalization_warnings`

Allowed `derivation_status`:

- `single_source`
- `merged_consistent`
- `conflict_review_required`

Rules:

- derive only from species `特性` and `特性描述`
- identical name plus identical text may merge
- identical name plus conflicting text must emit `conflict_review_required`
- do not invent structured numeric modifier fields from text

### `species_move_pool_candidates.jsonl`

One record per species-to-move access candidate.

Required fields:

- `run_id`
- `species_id`
- `move_name_raw`
- `move_id`
- `access_channel`
- `unlock_level`
- `source_field`
- `source_page_id`
- `raw_snapshot_id`
- `confidence`
- `normalization_warnings`

Allowed `access_channel`:

- `level_up`
- `skill_stone`
- `bloodline`
- `unknown`

Rules:

- `技能` maps to `level_up`
- `可学技能石` maps to `skill_stone`
- `血脉技能` maps to `bloodline`
- `技能解锁等级` must be used only as unlock metadata for `level_up`
- a source reference such as `技能石/光刃` must be treated as acquisition evidence for canonical move `光刃`, not as a separate `move` candidate
- canonical move battle semantics must come from `{{技能信息}}` when a move detail page exists
- if `技能` and `技能解锁等级` lengths differ, emit a warning and keep unmatched move names
- `move_id` may be `null` when name matching fails
- Engine-facing views will union `level_up`, `skill_stone`, and `bloodline` by default
- bloodline mutual-exclusion and acquisition legality are deferred to a later legality layer

### `validation_events.jsonl`

One record per warning or hard reject.

Required fields:

- `run_id`
- `severity`
- `code`
- `entity_type`
- `record_id`
- `source_page_id`
- `field_name`
- `message`
- `action_taken`

Allowed `severity`:

- `info`
- `warning`
- `hard_reject`

Common warning codes:

- `unexpected_source_field`
- `missing_optional_field`
- `missing_ability_text`
- `move_name_unresolved`
- `parallel_list_length_mismatch`
- `ability_description_conflict`
- `empty_description_text`

Common hard reject codes:

- `invalid_type`
- `missing_source_trace`
- `missing_required_template`
- `missing_required_field`
- `invalid_numeric_value`
- `forbidden_imported_field`

### `rejected_fields.jsonl`

One record per rejected source or normalized field.

Required fields:

- `run_id`
- `source_page_id`
- `entity_type`
- `source_label`
- `normalized_candidate`
- `reason`
- `policy_basis`

Required rejects:

- `accuracy`
- `PP`
- raw `cooldown`
- Pokemon-style category names
- encyclopedia/cosmetic species fields excluded by the alignment matrix

### `dry_run_diff.json`

Purpose:

- compare candidate artifacts against an existing database snapshot when one exists

Required fields:

- `run_id`
- `baseline_database`
- `added`
- `updated`
- `removed`
- `unchanged`
- `conflicts`
- `requires_pm_review`

If no baseline database exists:

- set `baseline_database` to `null`
- count all accepted candidates as `added`

### `summary.md`

Required sections:

- run scope
- artifact counts
- warning summary
- hard reject summary
- unresolved names
- ability merge conflicts
- schema drift observations
- recommended next action

## Name Normalization Contract

Minimum rules:

- trim whitespace
- normalize full-width and half-width delimiters only where safe
- preserve raw source text in all candidate records
- deterministic IDs must be stable across repeated runs

Do not:

- fuzzy-match by default
- merge visually similar names without exact evidence
- drop unmatched move names
- translate game-native labels into foreign-game terms

## Fetch Resilience Contract

The fetch stage must be bounded and polite.

Required behavior:

- run a preflight request before broader detail fetches
- prefer seed title fetches for bounded dry-runs when known seeds are enough
- if category enumeration is used, request no more than the current limit plus a small buffer
- fetch detail pages by bounded batches
- on batch failure, degrade to smaller batches
- on smaller batch failure, degrade to single-title fetch
- if single-title fetch fails for a seed required to start the run, emit failed artifacts and stop
- do not increase retry count beyond the existing bounded internal retry policy

Recommended degradation:

```text
batch size 40 -> batch size 10 -> batch size 1 -> failed manifest
```

The implementation may skip failed non-critical titles only when enough other pages remain to satisfy the requested bounded sample. It must record skipped titles in validation events.

## Fetch/Clean Separation

The tool should support two modes:

- `fetch-clean`: fetch source pages and immediately clean them into candidate artifacts
- `clean-only`: read cached `source_pages.jsonl` and raw page content/snapshots from a prior run, then regenerate normalized artifacts

`clean-only` exists so parser and schema changes can be validated without hitting the wiki again.

## P1d Entry Criteria

P1d may begin only when:

- all required P1c artifacts are generated for a bounded sample
- JSON and JSONL artifacts parse successfully
- no `hard_reject` exists for accepted records
- unresolved move names are listed and reviewed
- ability conflicts are listed and reviewed
- dry-run diff is generated

## Full Crawl Gate

A full crawl is allowed only after:

- P1d bounded ingestion dry-run succeeds
- schema migration path is clear
- hard reject rate is acceptable
- PM approves the crawl scope

Default full-crawl scope should still exclude:

- standalone ability pages
- cosmetic species metadata
- community/meta data
