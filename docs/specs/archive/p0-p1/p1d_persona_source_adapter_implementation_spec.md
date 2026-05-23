# P1d Persona Source Adapter Implementation Spec

## Purpose

Define the bounded implementation plan for `P1d Persona Source Adapter`.

This stage introduces the first upstream adapter that can produce a reviewable
persona artifact bundle before ingestion. It is the bridge between one-off
persona distillation work and the later managed persona pipeline.

This spec is not permission to start:

- persona artifact ingestion implementation
- registry admission or runtime activation
- managed persona creation UX
- crawler / Battle Wiki / SQLite expansion
- the unrelated crawler-side `P1d` dry-run track

## Naming Guard

This repo already contains a different `P1d` label for crawler-side dry-run
work.

For LaunchPad execution, this stage always means:

- `P1d Persona Source Adapter`

It never means:

- `P1d` crawler dry-run
- Battle Wiki fetch / clean / import work

Any packet or implementation request for this slice must use the full stage
name above to avoid cross-track contamination.

## Authoritative Inputs

This implementation spec is controlled by:

- `specs/p1_locked_execution_plan.md`
- `specs/p1_architecture_refactor_plan.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/persona_source_adapter_contract.yaml`
- `specs/persona_artifact_ingestion_contract.yaml`
- `specs/managed_persona_creation_pipeline_spec.md`
- `specs/nuwa_persona_distillation_enzo_request.md`
- `specs/enzo_integration_review.md`
- `specs/p1c_pluggable_persona_implementation_spec.md`

Existing project artifacts that must be treated as baseline inputs only:

- `docs/personas/enzo_internal_distillation_memo.md`
- `docs/personas/enzo_internal_persona_doctrine.yaml`
- `docs/personas/enzo_internal_mapping_note.md`

Existing code boundaries that must be respected:

- `agent_core/contracts.py`
- `agent_core/persona.py`
- `agent_core/persona_registry.py`
- `agent_core/orchestrator.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_agent_core_contracts.py`

## Current Baseline

The repo now has:

- a bounded synthesis layer (`P1a`)
- a bounded presentation layer (`P1b`)
- a bounded built-in persona runtime (`P1c`)
- one reviewed internal persona sample derived from Nuwa-style distillation

What is still missing:

- a typed adapter boundary that produces source artifacts before ingestion
- a standard provenance payload for upstream persona creation
- a reusable internal path for "adapter output bundle" generation
- a project-owned implementation of the approved first adapter:
  `nuwa_distillation_adapter`

Right now the Enzo doctrine artifacts exist as reviewed documents, but not as
the output of a project-owned source adapter interface. That gap blocks `P1e`
ingestion from having a clean upstream contract in code.

## P1d Implementation Goal

The implementation must introduce one bounded, internal-only persona source
adapter path that can emit a reviewable artifact bundle.

Target architecture:

`bounded source input -> source adapter -> artifact bundle -> later P1e ingestion`

Minimum supported adapter in this stage:

- `nuwa_distillation_adapter`

Required adapter outputs:

- `distillation_or_design_memo`
- `normalized_persona_doctrine_draft`
- `mapping_or_usage_note`
- provenance metadata with adapter identity and source summary

The generated bundle must be suitable for later ingestion, but `P1d` itself
must stop before any ingestion or registry admission occurs.

## Hard Scope Boundaries

### In Scope

- define typed source-adapter-side contracts in code
- implement one internal-only adapter for the approved Nuwa distillation path
- normalize adapter output into the bundle shape required by
  `specs/persona_source_adapter_contract.yaml`
- persist or emit reviewable artifacts rather than ephemeral strings only
- support a bounded local input path using checked-in project materials
- add focused tests proving bundle shape, provenance completeness, and
  non-runtime behavior

### Out Of Scope

- ingestion status assignment
- registry writes
- runtime persona selection changes
- public-safe approval
- original-persona design adapter implementation
- live web retrieval
- Battle Wiki crawler / import / SQLite work
- mobile / API surface expansion beyond regression preservation

## Implementation Shape

`P1d` should stay minimal and deterministic.

Preferred shape:

- add source-adapter models and helpers under `agent_core`
- keep adapter execution separate from runtime persona rendering
- use existing checked-in Enzo artifacts as bounded fixture-grade input for the
  first adapter path
- allow artifact output to a reviewable directory instead of silently mutating
  runtime structures

Acceptable module layout:

- `agent_core/persona_source_adapter.py`
- `agent_core/contracts.py` for typed bundle / provenance models
- optional small helper under `tools/` only if needed to exercise the adapter

It should not require:

- live Nuwa repo execution
- external API calls
- implicit writes into `agent_core/persona_registry.py`

## Bundle Rules

The adapter output must explicitly carry:

- `adapter_id`
- `adapter_kind`
- `run_mode`
- `source_summary`
- references or paths for:
  - memo
  - doctrine draft
  - mapping note

For this first stage:

- `adapter_id` should resolve to `nuwa_distillation_adapter`
- `adapter_kind` should be `distill_from_existing_subject`
- `run_mode` should default to `internal_only`

The implementation must reject or fail clearly when any required artifact or
provenance field is missing.

## Runtime Boundary Rules

`P1d` must preserve the current `P1c` runtime boundary.

Specifically, this stage must not:

- add the adapter output directly into builtin runtime persona selection
- bypass `P1e` ingestion to create a registry entry
- treat a generated doctrine draft as public-safe by default
- wire adapter output into API or mobile persona selectors

`P1c` remains the active runtime path until later stages explicitly replace it.

## Required Tests

The implementation must add focused tests proving:

- the adapter emits a complete artifact bundle matching the contract shape
- provenance metadata includes adapter id, adapter kind, run mode, and a
  non-empty source summary
- the doctrine artifact still targets
  `specs/persona_doctrine_contract.yaml`
- the output remains internal-only by default
- missing required artifacts fail fast with an explicit error
- no runtime registry activation occurs as a side effect
- the persona-side `P1d` path cannot be confused with crawler-side `P1d`
  terminology in the adapter-facing entry points

## Explicit Non-Goals For This Stage

`P1d` does not include:

- `P1e` ingestion validation or admission status logic
- `P1f` managed persona creation workflow
- `nexus_original_design_adapter`
- default shipping of any generated persona
- broader persona sample generation
- LaunchPad packet dispatch for implementation in this step

## Implementation Readiness Check

`P1d persona source adapter implementation spec` is complete only when:

- it defines one bounded upstream adapter target
- it enforces artifact-bundle output instead of prompt-only output
- it keeps source adapter output strictly upstream of ingestion and runtime
- it names the minimal files and test surfaces needed to implement safely
- it explicitly guards against the crawler-side `P1d` naming collision

## Next Unlocked Action

If accepted, the next legal stage is:

- `P1d persona source adapter implementation`

And the implementation packet must remain bounded to:

- one internal-only `nuwa_distillation_adapter`
- artifact-bundle generation only
- no ingestion, no registry admission, no runtime activation
