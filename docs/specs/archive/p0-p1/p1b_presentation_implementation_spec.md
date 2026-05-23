# P1b Presentation Implementation Spec

Supersession note, 2026-04-27:

The old mobile `ResponsePanel` scaffold has been removed during RN UI V1
merge closeout. Current mobile presentation rendering lives in
`mobile/src/roco/rocoPresentation.ts`, `mobile/src/components/roco/AnalysisCard.tsx`,
and `mobile/src/screens/ChatScreen.tsx`.

## Purpose

Define the bounded implementation plan for `P1b Conversational Presentation
Layer`.

This spec converts the already-approved presentation direction into a concrete
implementation target for the next development stage.

It is not permission to start:

- persona registry/runtime selection work
- persona source adapter work
- persona artifact ingestion
- managed persona creation flow
- case retrieval or broader doctrine-eval infrastructure
- mobile redesign beyond what is required for presentation compatibility

## Authoritative Inputs

This implementation spec is controlled by:

- `specs/p1_locked_execution_plan.md`
- `specs/p1b_conversational_presentation_layer.md`
- `specs/presentation_response_contract.yaml`
- `specs/reasoning_synthesis_contract.yaml`
- `specs/p1_architecture_refactor_plan.md`
- `specs/p1c_pluggable_persona_contract.md`

Existing code boundaries that must be respected:

- `agent_core/orchestrator.py`
- `agent_core/contracts.py`
- `agent_core/persona.py`
- `api/services/advisor_service.py`
- `api/contracts.py`
- `mobile/src/api/types.ts`
- `mobile/src/roco/rocoPresentation.ts`
- `mobile/src/components/roco/AnalysisCard.tsx`
- `mobile/src/screens/ChatScreen.tsx`
- `tests/test_agent_core_contracts.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_api.py`

## Current Baseline

The current post-P1a flow is:

`SafetyGuard -> Advisor analytical substrate -> Synthesis -> AgentResponse.answer -> PersonaBoundary`

Current behavior:

- synthesis is already the reasoning owner
- `AgentResponse.answer` carries synthesized judgement
- persona attaches metadata and a rendered wrapper, but not a real front-stage
  conversational presentation object
- there is no typed `Reply + Why` presentation payload yet
- the default surface still behaves like a synthesis-led technical answer rather
  than a true product presentation layer

This is acceptable as the starting point, but not as the P1b target.

## P1b Implementation Goal

The implementation must introduce a real presentation layer above synthesis and
below persona rendering.

Target architecture:

`SafetyGuard -> Advisor analytical substrate -> Synthesis -> Presentation -> AgentResponse compatibility surface -> PersonaBoundary`

The presentation layer must turn synthesis output into the default
coach-oriented front-stage surface:

- `Reply`
- `Why`

while keeping evidence, confidence, warnings, and tool traces inspectable.

## Hard Scope Boundaries

### In Scope

- add a bounded presentation module under `agent_core`
- add typed presentation input/output contracts in product-side code
- map synthesis output into a presentation payload aligned with
  `specs/presentation_response_contract.yaml`
- keep material warnings visible in the presentation payload
- preserve inspectable detail sections for:
  - evidence
  - confidence
  - tool trace
  - analytical base
  - follow-up
- keep API/mobile compatibility while making `Reply + Why` the product-facing
  default
- add tests proving presentation changes phrasing/surface only, not facts,
  confidence, warnings, or refusal boundaries

### Out Of Scope

- deeper B-layer doctrine work
- A-layer mechanism schema work
- evaluator plumbing beyond presentation-specific regression checks
- persona registry/runtime selection
- persona source adapter or ingestion implementation
- new retrieval systems
- web/live integrations
- mobile visual redesign beyond contract-compatible presentation rendering

## Hard Rules

1. Presentation is the surface unit, not the truth unit.
2. Synthesis remains upstream and authoritative for judgement meaning.
3. Presentation may compress, reorder, or foreground content, but may not:
   - change factual meaning
   - upgrade or downgrade confidence
   - hide material warnings
   - erase refusal boundaries
4. `Reply` must preserve the meaning of `synthesized_judgement`.
5. `Why` must remain aligned with the upstream reasoning path.
6. Persona may style the already-presented answer, but may not define the
   default non-persona presentation contract.
7. `P1b` must preserve API/mobile compatibility for existing consumers that
   still read `answer`.

## Required Module Shape

### 1. New presentation module

Add a new module:

- `agent_core/presentation.py`

This module should own:

- presentation input packing
- presentation rendering boundary
- warning visibility enforcement
- inspectable detail-section assembly
- compatibility fallback behavior when presentation is unavailable

### 2. New presentation-side contracts

Extend product-side contracts so a typed presentation artifact exists in code.

Preferred target:

- keep `AgentResponse` as the transport object
- add an optional `presentation` payload field rather than replacing the
  existing response model wholesale

Required new typed concepts:

- `PresentationInput`
- `VisibleWarning`
- `DetailSection`
- `PresentationResult`

Minimum `PresentationResult` fields must align with
`specs/presentation_response_contract.yaml`:

- `presentation_version`
- `reply`
- `why`
- `visible_warnings`
- `detail_sections`
- `followup_prompts`
- `presentation_metadata`

### 3. Orchestrator insertion point

`agent_core/orchestrator.py` must become the layer owner for presentation.

Required flow:

1. run safety evaluation
2. obtain analytical substrate from runtime adapter
3. build doctrine pack
4. run synthesis
5. run presentation over synthesis output
6. project the presentation result onto the compatibility response surface
7. attach persona metadata/render wrapper

Hard rule:

- presentation must happen after synthesis
- persona rendering remains downstream of presentation

### 4. Persona boundary interaction

`agent_core/persona.py` must stop acting like the only user-facing rendering
layer.

It should become responsible for:

- optional persona metadata
- optional persona-flavored wrapping of already-presented content
- fact lock enforcement

It should not:

- invent the base `Reply + Why`
- replace the presentation contract with persona-only rendering

## Presentation Mapping Rules

`P1b` should treat current synthesis output as the presentation source.

Mapping rules:

- `synthesized_judgement`
  - becomes the semantic source for `reply`
- `why_summary`
  - becomes the primary source for `why`
- `surfaced_warnings`
  - become `visible_warnings`
- `followup_directions`
  - become `followup_prompts`
- evidence/confidence/tool traces
  - move into `detail_sections`

No grounded field from the analytical/synthesis path should be discarded.

## Compatibility Surface Rules

`P1b` must not force current API/mobile consumers to immediately migrate to a
new front-stage object.

Temporary compatibility policy:

- `AgentResponse.answer`
  - should carry `presentation.reply` once presentation succeeds
- `AgentResponse.synthesis`
  - remains unchanged and inspectable
- new optional `presentation` field
  - carries the full `PresentationResult`
- `AgentResponse.persona.rendered_answer`
  - may wrap the presentation-layer default answer, not the raw synthesis-only
    answer
- existing evidence/tool/confidence/follow-up fields
  - remain present for compatibility and inspection

## Warning Visibility Rules

The following warning cases must remain visible in `reply` or `why`, and must
also appear in `presentation.visible_warnings`:

- partial-team analysis
- provisional-only interpretation
- deterministic fallback
- unsupported scope
- refused_missing_context
- refused_missing_species

If presentation compresses the answer so aggressively that a material warning
disappears, that is a P1b failure.

## Detail Section Rules

The first implementation should support a bounded inspectable-detail model with
stable sections:

- `evidence`
- `confidence`
- `tool_trace`
- `analytical_base`
- `followup`

Default policy:

- front stage remains compact
- detail sections default to collapsed unless there is a strong reason to
  expand by default

## Mobile/API Boundary

`P1b` should preserve the current API contract shape while adding typed
presentation support.

Expected first-pass behavior:

- API responses continue to serialize a valid `AgentResponse`
- existing consumers reading `answer` still work
- newer consumers may read `presentation.reply` / `presentation.why`
- mobile presentation mapping may be updated only as needed to render
  `Reply + Why` and visible warnings without forcing a larger UI rewrite

## Test Requirements

Implementation is complete only if tests prove:

1. presentation changes the default user-facing answer shape
2. facts/evidence/confidence are unchanged underneath presentation
3. refusal outputs remain refusals
4. visible warnings remain visible after presentation
5. API serialization preserves compatibility
6. persona wrapping happens after presentation rather than replacing it

Minimum test targets:

- `tests/test_agent_core_contracts.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_api.py`

## Exit Criteria

`P1b implementation spec` is complete only when:

- it defines the bounded module and contract changes
- it preserves P1a factual/confidence/refusal boundaries
- it defines compatibility policy for `AgentResponse.answer`
- it defines how `Reply + Why` becomes the default front-stage surface
- it stays out of later persona-registry / creation-pipeline work

## Next Unlocked Action

If this spec is accepted by the main thread, the next unlocked action is:

- `P1b implementation`

Nothing later is unlocked by this spec alone.
