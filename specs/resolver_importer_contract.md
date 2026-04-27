# Resolver / Importer Contract

Date: 2026-04-14

Status: draft_for_implementation

## Purpose

Define the first formal contract for resolving battle-dex records from:

- wiki canonical crawl artifacts
- manual verified supplement
- later mechanics supplement

This contract is the gate between artifact generation and any future SQLite importer implementation.

It does not approve direct database writes by itself.

## Position In Workflow

Current sequence:

- `P1a`: field discovery
- `P1b`: minimal battle schema
- `P1c`: crawler/cleaner artifact contract
- `P1d`: bounded dry-runs
- `P1e`: resolver/importer contract
- later: importer dry-run
- only after that: SQLite write approval

## Inputs

Required inputs:

1. wiki canonical artifact directory
2. manual supplement document or normalized supplement export

Optional later input:

3. mechanics supplement document or normalized mechanics export

Current canonical sources:

- wiki canonical artifacts:
  - `source_pages.jsonl`
  - `raw_template_snapshots.jsonl`
  - `species_form_candidates.jsonl`
  - `move_candidates.jsonl`
  - `derived_ability_candidates.jsonl`
  - `species_move_pool_candidates.jsonl`
  - `validation_events.jsonl`
  - `rejected_fields.jsonl`
- manual supplement:
  - `docs/manual_battle_data_supplement_2026-04-14.md`
  - `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
  - `specs/manual_battle_data_supplement_schema.yaml`

## Resolution Goals

The resolver/importer must produce a battle-dex candidate set that:

- preserves wiki provenance
- applies accepted manual supplement rules without erasing raw wiki evidence
- excludes out-of-scope hidden special forms
- keeps unresolved ambiguity visible
- can be reviewed in dry-run mode before any SQLite write is considered

## Resolution Layers

### Layer A: Exclusion / Review Gate

Runs first.

Purpose:

- stop obviously out-of-scope records before canonical merge

Current required rule:

- the current 10 hidden special forms are excluded from current ingest target
- future same-pattern forms are marked `human-review-before-ingest`

Resolver output states at this layer:

- `excluded`
- `review_required`
- `eligible`

### Layer B: Wiki Canonical Resolution

Runs second for `eligible` entities.

Purpose:

- use structured wiki artifacts as the default canonical source

Rules:

- wiki canonical records are the default source for species, move, and derived ability candidates
- raw source provenance must be preserved
- hard-reject artifact records must not be silently imported

### Layer C: Manual Supplement Resolution

Runs third.

Purpose:

- fill known wiki omissions
- provide reviewed tie-breakers for accepted battle-relevant conflicts

Current accepted supplement candidates:

- `湿润印记`
- `溶解液`
- `龙之舞`
- `溶解扩散`

Rules:

- supplement may add candidate records when current wiki canonical coverage is missing
- supplement may resolve a conflict only when the supplement decision is explicit and reviewable
- supplement must never delete raw wiki evidence
- if a later wiki-canonical `{{技能信息}}` page appears, default canonical preference returns to the wiki record unless review policy says otherwise

### Layer D: Mechanics Supplement

Runs outside first-pass raw importer normalization.

Purpose:

- provide higher-order mechanics context for later Engine / Agent use

Current accepted boundary:

- 印记 baseline rules belong here
- they do not become raw move/species fields in first importer design

## Entity-Specific Rules

### Species / Form

Importer must:

- preserve form distinction
- reject auto-ingest of hidden special plot forms already excluded by supplement
- mark future same-pattern forms as `human-review-before-ingest`
- preserve source page and raw snapshot lineage

### Move

Importer must:

- prefer wiki `{{技能信息}}` moves as canonical move records
- allow manual supplement move records when wiki coverage is missing
- keep supplement provenance attached to such moves
- not treat skill-stone acquisition pages as separate move entities

### Derived Ability

Importer must:

- preserve wiki-derived ability conflicts
- not silently collapse conflicting `effect_text`
- allow later manual review to resolve which text is currently accepted

Current accepted manual conflict resolution:

- `溶解扩散` current manual-verified baseline text is accepted as supplement guidance
- conflicting wiki evidence must remain visible in provenance and review output

### Species Move Pool

Importer must:

- preserve `access_channel`
- preserve unresolved names when they still cannot be matched
- allow move matching against supplement-backed move records

Engine-facing note:

- `species_available_moves` still unions `level_up`, `skill_stone`, and `bloodline`
- legality filtering remains a later layer

## Provenance Requirements

Every resolved entity must retain:

- canonical source layer: `wiki` or `manual_supplement`
- raw source references when available
- resolution note when supplement altered the importer decision
- exclusion/review reason when not imported

Minimum provenance fields for dry-run output:

- `entity_type`
- `entity_key`
- `resolution_status`
- `canonical_source_layer`
- `wiki_source_refs`
- `supplement_refs`
- `resolution_reason`

## Dry-Run Output Contract

Before SQLite write approval, importer dry-run must emit a reviewable report with at least:

### Included

- entities that would be inserted
- canonical source layer for each entity

### Excluded

- entities blocked by explicit exclusion rules
- exclusion reason

### Review Required

- entities marked `human-review-before-ingest`
- why they need review

### Supplement-Backed

- entities inserted or resolved using manual supplement
- exact supplement reference

### Conflicts

- wiki/manual disagreements still visible after resolution
- unresolved conflicts still blocking import

### Summary Counts

- total included species/forms
- total included moves
- total included derived abilities
- total excluded records
- total review-required records
- total supplement-backed records

## Non-Goals

This contract does not yet define:

- final SQLite table DDL
- migration scripts
- write transaction behavior
- legality-layer enforcement
- Agent prompt structure

## Stop Conditions

Implementation must stop and return to spec review if:

- a new supplement class is needed beyond current policy B
- a hidden-form pattern cannot be classified confidently
- supplement needs to overwrite a wiki canonical field without explicit review basis
- mechanics notes are about to be flattened into raw schema fields

## First Implementation Target

The first resolver/importer implementation should be:

- dry-run only
- artifact-driven
- no SQLite mutation
- able to show `included | excluded | review_required | supplement_backed | unresolved`
- prefer structured supplement input; markdown parsing remains compatibility-only

Only after that dry-run is reviewed should the project decide the next SQLite step.
