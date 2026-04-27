# Policy B Resolver/Importer Change Spec

Date: 2026-04-14

Change class: Major change

## Purpose

Define how accepted data-source policy B:

- `wiki canonical + manual verified supplement`

must be implemented in the future resolver/importer layer before any SQLite write path is approved.

This change spec exists because policy B changes importer semantics, provenance handling, exclusion rules, and dry-run expectations.

## Trigger

After move-full and species-full artifact-only dry-runs, the project accepted:

- manual supplement as a formal input layer
- hidden special-form exclusion with `human-review-before-ingest`
- four manual supplement records:
  - `湿润印记`
  - `溶解液`
  - `龙之舞`
  - `溶解扩散`
- 印记 system notes into a mechanics / Agent supplement layer

These decisions are now approved strategically, but not yet encoded as a resolver/importer contract.

## Scope

In scope:

- resolver input layers
- precedence rules
- exclusion and review gates
- provenance requirements
- dry-run diff requirements
- importer stop/go conditions

Out of scope:

- actual SQLite schema implementation
- actual importer code
- Agent prompt changes
- battle report logic

## Why This Is A Major Change

This is not wording cleanup. It changes:

- what inputs are authoritative
- how conflicts are resolved
- which entities are excluded before ingest
- how raw wiki and manual supplement provenance coexist
- what an importer dry-run must show before any write is allowed

## Impacted Artifacts

Source strategy and supplement docs:

- `docs/data_source_strategy.md`
- `docs/manual_battle_data_supplement_2026-04-14.md`

New contract artifact required:

- `specs/resolver_importer_contract.md`

Potential later downstream artifacts:

- `specs/battle_dex_schema.yaml`
- `specs/p1b_minimal_battle_dex_schema.md`
- `specs/agent_tool_contracts.yaml`
- importer implementation files
- importer tests

## Required Semantics

### Input Layers

Resolver/importer must accept at least:

1. wiki canonical artifacts
2. manual verified supplement artifact
3. mechanics supplement artifact or section reference

### Precedence

Importer resolution order:

1. explicit exclusion/review gates from manual supplement
2. wiki canonical structured records
3. manual supplement for missing or conflicting battle-relevant records
4. mechanics supplement for later non-raw semantic layers

### Hidden Form Gate

The current 10 hidden special forms are excluded from current ingest target.

Future same-pattern pages must not be auto-ingested.

They must be emitted as:

- `human-review-before-ingest`

### Manual Move Supplements

The four accepted supplement records may be resolved into importer candidates even if current wiki move coverage is incomplete.

If a later wiki-canonical move page exists, importer must:

- preserve both provenance layers
- prefer wiki canonical as the default move source
- only keep supplement override behavior when explicit review says so

### Mechanics Supplement Boundary

印记 baseline rules are allowed into later mechanics / Agent inputs but must not be flattened into raw move/species schema during first importer design.

## Dry-Run Requirements

Before any SQLite write path is approved, importer dry-run must show:

- included records
- excluded records
- records requiring human review
- supplement-backed inserted candidates
- supplement-backed conflict resolutions
- unresolved records still blocked
- provenance for every resolved entity

## Stop Conditions

Do not approve SQLite writes if any of these are still undefined:

- supplement file shape and parser
- exclusion/review rule evaluation
- provenance retention model
- dry-run diff shape for resolved vs excluded vs review-needed

## Deliverable Of This Change

This change is complete only when:

1. `specs/resolver_importer_contract.md` exists
2. it clearly defines policy B precedence
3. it defines exclusion/review semantics
4. it defines dry-run output expectations
5. main-thread review can use it as the basis for importer implementation
