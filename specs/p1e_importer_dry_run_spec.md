# P1e Importer Dry-Run Spec

Date: 2026-04-14

Purpose: define the first implementation target after the resolver/importer contract.

This spec covers only a dry-run importer. It does not authorize SQLite writes.

## Goal

Consume:

- one wiki canonical artifact directory
- one manual supplement layer

Then emit a reviewable importer dry-run result showing:

- what would be included
- what would be excluded
- what requires human review
- what is supplement-backed
- what remains unresolved

## Required Inputs

- wiki artifact directory from a successful or reviewable P1d run
- `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
- `specs/manual_battle_data_supplement_schema.yaml`
- `docs/data_source_strategy.md`
- `specs/resolver_importer_contract.md`

## Required Dry-Run Outputs

Minimum output files:

- `importer_run_manifest.json`
- `resolved_species_forms.jsonl`
- `resolved_moves.jsonl`
- `resolved_derived_abilities.jsonl`
- `excluded_entities.jsonl`
- `review_required_entities.jsonl`
- `supplement_backed_entities.jsonl`
- `unresolved_entities.jsonl`
- `importer_diff_summary.md`

## Resolution Status Values

Allowed statuses:

- `included`
- `excluded`
- `review_required`
- `supplement_backed`
- `unresolved`

## Minimum Record Shape

Each emitted entity row must include:

- `entity_type`
- `entity_key`
- `resolution_status`
- `canonical_source_layer`
- `wiki_source_refs`
- `supplement_refs`
- `resolution_reason`

## Required Review Questions Answered By Dry-Run

The dry-run must make it easy to answer:

- which species/forms were excluded by hidden-form policy
- which entities are blocked for human review
- which moves only exist because of manual supplement
- which wiki conflicts remain unresolved
- whether supplement changed any canonical decision

## Hard Boundaries

Do not:

- write SQLite
- mutate source artifacts
- flatten mechanics supplement into raw move/species fields
- silently drop unresolved entities
- rely on markdown-only parsing when a structured supplement export is available

## Acceptance

This dry-run spec is satisfied only when a later implementation can be reviewed without opening code first.
