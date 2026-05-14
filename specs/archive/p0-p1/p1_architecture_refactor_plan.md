# P1 Architecture Refactor Plan

## Purpose

Define the bounded post-P0 refactor that lets persona integrate more deeply
into the system without turning the codebase into spaghetti.

This is a layer refactor, not a full rewrite.

## Refactor Goal

Move the product from:

`analytical payload -> direct answer formatting -> thin persona wrapper`

to:

`grounded facts (A) + doctrine/persona inputs (B) -> synthesis -> Reply/Why presentation -> persona render`

## What Gets Rebuilt

### Rebuild / introduce

- reasoning / synthesis contract
- persona doctrine contract
- persona source adapter contract
- persona artifact ingestion contract
- managed persona creation pipeline
- conversational presentation contract
- persona registry architecture
- adapters between analytical layer and synthesis layer

### Keep

- deterministic battle engine
- type model
- SQLite battle-dex
- API boundary
- mobile scaffold
- refusal and confidence discipline

### Do not rewrite

- crawler/importer pipeline
- battle-dex storage model
- public-release hardening work
- existing API/mobile infrastructure foundations

## Layer Model

### Layer 1. Grounded Facts

Owned by:

- Engine
- SQL / battle-dex
- approved bounded retrieval facts

### Layer 2. Doctrine Pack

Owned by:

- approved mechanics/methodology docs
- taxonomy docs
- persona doctrine contract

### Layer 3. Reasoning / Synthesis

Owned by:

- LLM synthesis over `A + B`

### Layer 4. Presentation

Owned by:

- `Reply + Why`
- visible warnings
- detail drawer policy

### Layer 5. Persona Render

Owned by:

- expression DNA
- display identity
- tone and pacing only

## Migration Strategy

### Phase 1

- finalize SSD for:
  - `persona_doctrine_contract.yaml`
  - `persona_source_adapter_contract.yaml`
  - `persona_artifact_ingestion_contract.yaml`
  - `managed_persona_creation_pipeline_spec.md`
  - `reasoning_synthesis_contract.yaml`
  - `presentation_response_contract.yaml`
- keep current runtime behavior unchanged

### Phase 2

- implement synthesis layer behind compatibility adapters
- keep current analytical contracts as substrate
- avoid breaking CLI/API/mobile response compatibility until presentation is
  ready

### Phase 3

- implement `Reply + Why` presentation
- keep evidence/confidence/tool traces inspectable

### Phase 4

- upgrade persona from thin metadata envelope to doctrine + rendering system

### Phase 5

- support managed persona creation through source adapters plus ingestion
- keep Nuwa as the first distillation adapter, not as the entire persona system
- later allow original persona design through a separate adapter path

## Acceptance Criteria

The refactor is successful when:

- LLM is the core analysis unit but not the truth unit
- persona doctrine can shape reasoning without mutating facts
- users see a coach-like `Reply + Why` instead of raw analytical payloads
- existing Engine / SQL substrate remains intact
- API/mobile do not need infrastructural rewrites to consume the new output
- persona creation remains pipeline-based rather than prompt-blob based
