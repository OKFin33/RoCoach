# Nuwa Persona Distillation Request: Enzo Internal Draft

## Purpose

Run a separate bounded research/distillation thread to produce an internal
`Enzo` persona draft using the Nuwa-style five-layer distillation approach.

This is **not** a runtime implementation request.
This is **not** a public-release approval.
This is a persona-source generation task whose output will later be mapped into
the project's persona doctrine contract.

## Current Main-Thread Architecture

The project has already locked the following post-P0 direction:

- `A` = grounded facts
  - deterministic Engine output
  - SQL / battle-dex facts
  - bounded approved retrieval facts
- `B` = doctrine pack
  - approved mechanics and methodology
  - taxonomy/taste constraints
  - persona doctrine inputs
- `LLM synthesis` = core analysis unit
- `presentation` = `Reply + Why`
- `persona render` = expression layer only
- source-of-truth remains:
  - Engine
  - SQL / battle-dex
  - approved docs

The relevant SSD has already been written. This thread must treat the following
as binding:

- `specs/p1_architecture_refactor_plan.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/p1a_reasoning_synthesis_layer.md`
- `specs/p1b_conversational_presentation_layer.md`
- `specs/p1c_pluggable_persona_contract.md`
- `specs/reasoning_synthesis_contract.yaml`

## Task Goal

Produce one bounded internal persona doctrine draft for `Enzo`, using the
Nuwa-style five-layer framing:

1. expression DNA
2. mental models
3. decision heuristics
4. anti-patterns / bottom lines
5. honesty boundaries

The result must be usable as a future input to:

- synthesis-facing persona doctrine
- rendering-facing persona style

## Output Requirements

The thread should produce all of the following artifacts:

### 1. Distillation memo

Suggested path:

- `docs/personas/enzo_internal_distillation_memo.md`

Required contents:

- sources used
- confidence / reliability notes
- what appears stable vs speculative
- Nuwa five-layer distillation summary
- what is missing or ambiguous

### 2. Persona doctrine draft

Suggested path:

- `docs/personas/enzo_internal_persona_doctrine.yaml`

This draft must map to:

- `specs/persona_doctrine_contract.yaml`

It should include:

- `persona_id`
- `display_name`
- `expression_dna`
- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`
- `fact_policy`
- `ip_safety_profile`

### 3. Mapping note

Suggested path:

- `docs/personas/enzo_internal_mapping_note.md`

Required contents:

- which doctrine fields should enter synthesis
- which fields should enter rendering
- which fields should stay metadata-only
- what would need sanitization if later adapted for public-safe release

## Scope Rules

Allowed:

- use Nuwa-style methodology
- use public information
- distill one internal persona draft
- note contradictions or low-confidence areas
- produce a doctrine artifact aligned with project contracts

Not allowed:

- modify runtime code
- modify API/mobile behavior
- rewrite current persona implementation
- treat the draft as public-safe by default
- treat the draft as final product copy
- silently invent missing character traits without labeling uncertainty

## Quality Bar

The persona draft should be:

- specific enough to change reasoning style
- specific enough to change rendering style
- honest about what is inferred vs directly supported
- not just a list of vibes or adjectives

Avoid low-value output such as:

- generic "cold / smart / mysterious"
- quote imitation without cognitive structure
- style without heuristics
- heuristics without stated limits

## Suggested Execution Method

If the thread can actually use Nuwa or reproduce its workflow, do so.

If not, emulate the same structure manually:

- collect sources
- extract candidate models/heuristics
- remove unstable fluff
- produce a contract-shaped doctrine draft

## Final Return Format

Return:

1. files created
2. concise source summary
3. top 5 mental models
4. top 5 decision heuristics
5. key anti-patterns / honesty boundaries
6. confidence assessment of the overall draft
7. whether the doctrine draft is ready for integration review

## Copy-Paste Prompt For New Thread

```text
Read these files first:

- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_architecture_refactor_plan.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_doctrine_contract.yaml
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1a_reasoning_synthesis_layer.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1b_conversational_presentation_layer.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1c_pluggable_persona_contract.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/reasoning_synthesis_contract.yaml
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/nuwa_persona_distillation_enzo_request.md

You are a bounded persona-distillation thread.

Goal:
Produce one internal `Enzo` persona draft using the Nuwa-style five-layer approach:
- expression DNA
- mental models
- decision heuristics
- anti-patterns
- honesty boundaries

This is not a runtime implementation task. Do not modify product code. Do not change API/mobile/runtime behavior. Do not declare the result public-safe. Your job is to create doctrine artifacts that can later be reviewed and mapped into the project's persona system.

Deliverables:
- docs/personas/enzo_internal_distillation_memo.md
- docs/personas/enzo_internal_persona_doctrine.yaml
- docs/personas/enzo_internal_mapping_note.md

The doctrine draft must map cleanly to `specs/persona_doctrine_contract.yaml`.

Be explicit about uncertainty. Do not just imitate dialogue style. Extract cognitive structure.

Return:
1. files created
2. source summary
3. top mental models
4. top decision heuristics
5. anti-patterns / honesty boundaries
6. confidence assessment
7. whether it is ready for integration review
```
