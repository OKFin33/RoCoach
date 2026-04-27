# Analytical Response Layer Specification

## Purpose

Define the internal analytical layer that combines deterministic structure
analysis, bounded retrieval, and constrained semantic judgement.

Historical note:

- this file used to frame the product as a "report layer"
- that is no longer the default product surface
- the analytical layer now feeds a separate reasoning/synthesis layer, which
  then feeds conversational presentation

## Scope

This document covers:

- analytical-layer inputs
- analytical-layer components
- PydanticAI usage boundaries
- retrieval boundaries
- analytical output responsibilities
- boundaries between analytical output and user-facing presentation

It does **not** define the final default user-facing reply style, and it does
not treat raw analytical payloads as the product's core analysis experience.

## Core Principle

The analytical layer does **not** decide battle truth for deterministic
subproblems, and it does **not** define the final conversational UX.

It must follow this hierarchy:

1. `Engine / SQL / approved docs` determine factual substrate
2. `retrieval` provides bounded domain context
3. `battle doctrine pack` provides methodology, taxonomy, and taste constraints
4. `LLM synthesis` performs grounded advisory reasoning
5. `presentation` decides how that synthesized material is shown to the user
6. `persona` decides style only

## Surface Split

The product now has three distinct surfaces:

### A. Analytical Contract Surface

Used by:

- runtime internals
- API payloads
- validation
- debug/inspection UI

Contains:

- answer summary
- evidence
- confidence
- tool traces
- follow-up options

### B. Reasoning / Synthesis Surface

Used by:

- post-P0 advisor reasoning
- grounded LLM explanation
- reply/why generation

Contains:

- synthesized judgement
- key reasons
- surfaced warnings
- recommended follow-up direction

### C. Default User-Facing Surface

Used by:

- mobile default reply view
- future product chat surfaces

Contains:

- coach-style primary message
- compact `Reply`
- compact `Why`
- conversational tone
- folded evidence/confidence/tool detail

Hard rule:

- the default user-facing surface may change wording and ordering
- it may not change underlying facts, confidence tier, evidence attribution, or
  refusal decisions

## Current Runtime Choice

The analytical layer may use `PydanticAI` where semantic/tool-orchestrated work
is needed.

Reasons:

- typed Python integration
- clean fit with FastAPI and Pydantic contracts
- strong structured output support
- native tool usage pattern
- sufficient support for lightweight multi-turn advisory interaction

## Layer Inputs

The analytical layer may consume:

- `TeamStructureReport` from the deterministic Engine
- structured battle-dex records
- a curated set of retrieved knowledge snippets
- a battle doctrine pack built from approved mechanics/methodology/taxonomy
  materials
- explicit user constraints and goals
- optional selected persona identifier as metadata only

The analytical layer must not infer hidden game facts that are unavailable in:

- Engine output
- approved domain documents
- explicit user input

## Approved Knowledge Sources

High-priority sources:

- `docs/domain_primer.md`
- `specs/scoring_system.md`
- `specs/role_taxonomy.md`
- `specs/archetype_taxonomy.md`

Lower-priority contextual sources:

- `docs/research/luoke_world_pvp_domain_primer_v2.md`

Deferred and not yet approved as default retrieval material:

- community meta signal collections
- speculative environment notes
- unconstrained external web content

## Analytical Layer Components

### 1. KnowledgeRetriever

Responsibilities:

- fetch only relevant approved snippets
- label retrieved snippets by source and confidence tier
- avoid broad document dumping

### 2. ContextBuilder

Responsibilities:

- combine Engine output with retrieved snippets
- combine structured records with mechanics notes when a semantic pass needs
  them
- include only material relevant to the current analysis task
- preserve source labels for downstream validation and presentation

### 3. BattleDoctrinePackBuilder

Responsibilities:

- assemble the non-factual but approved advisory context (`B`)
- include only approved:
  - mechanics notes
  - methodology guidance
  - role/archetype taxonomy
  - accepted taste / interpretation constraints
- avoid broad document dumping or speculative meta filler

### 4. ReasoningSynthesizer

Implementation note:

- may be implemented with `PydanticAI`

Responsibilities:

- take `A` analytical facts and `B` doctrine context as input
- perform the product's core advisory reasoning
- judge role / tactical / mechanics implications that are not yet covered by
  deterministic tools
- produce a concrete conclusion plus a compact explanation path
- surface explicit uncertainty when evidence is partial
- never restate synthesized guesses as deterministic facts

### 5. AnalyticalResponseAssembler

Responsibilities:

- generate the structured analytical payload
- combine Engine findings and semantic findings using project-approved
  vocabulary
- avoid unsupported meta or role claims

### 6. ReportValidator

Responsibilities:

- validate analytical structure
- validate that high-confidence structural claims are grounded in Engine
  evidence
- validate that semantic claims cite approved retrieval or structured dex
  evidence
- reject outputs that exceed the allowed confidence policy

### 7. PresentationRenderer

Responsibilities:

- consume synthesis output and produce the default coach-style `Reply` and
  `Why`
- keep warnings visible when they materially affect user interpretation
- fold evidence/confidence/tool traces into inspectable secondary UI

### 8. PersonaRenderer

Responsibilities:

- apply tone/style after the analytical structure is fixed
- preserve factual payload
- never alter evidence, confidence, or refusal

## Multi-Turn Boundary

The analytical layer may support lightweight multi-turn interaction.

Allowed:

- follow-up clarification
- re-explaining the same conclusion
- comparing a small number of patch directions
- carrying the current team and user constraints within a session

Not allowed yet:

- autonomous planning
- autonomous background tasks
- long-term memory across many sessions
- self-directed tool expansion
- autonomous species-level replacement advice without stronger evidence

## Tool Boundary

The analytical layer may call approved tools only.

Current approved tools:

- `analyze_team_structure`
- `get_species_profile`
- `get_species_available_moves`
- `retrieve_doc_context`
- `analyze_species_semantics`

Deferred tools remain separate and do not automatically become part of the
default presentation layer.

## Retrieval Boundary

Retrieval should remain curated RAG, not open-ended search.

Rules:

- retrieve from approved project documents first
- prefer shorter snippets over whole-document injection
- separate factual mechanism context from low-confidence strategic commentary
- never allow low-confidence snippets to override Engine evidence

## Analytical Output Responsibilities

The analytical layer must output enough material for:

- one concise grounded answer summary
- evidence summary
- confidence notes
- tool traces
- follow-up options

Exact field structure belongs to the analytical/runtime contracts, not to the
default user-facing presentation.

The post-P0 reasoning/synthesis layer should then transform this material into:

- one grounded judgement
- one compact explanation path
- one warning surface decision
- one follow-up direction set

## Default Presentation Responsibilities

The default product surface must:

- show a coach-style primary `Reply`
- show a compact `Why`
- avoid dumping raw protocol fields first
- keep evidence/confidence/detail accessible on demand
- preserve the ability to audit or debug the answer

## Non-Goals

This layer does not yet provide:

- full species recommendation
- current-meta authoritative judgement
- battle simulation
- autonomous team building
- environment-aware counter-teaming

## Upgrade Path

This analytical layer should evolve alongside:

- a reasoning / synthesis layer
- a conversational presentation layer
- a pluggable persona contract
- deterministic role scoring
- optional persistence and casebank support later
