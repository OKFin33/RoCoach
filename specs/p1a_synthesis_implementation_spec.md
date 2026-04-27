# P1a Synthesis Implementation Spec

## Purpose

Define the bounded implementation plan for `P1a Reasoning / Synthesis Layer`.

This spec converts the approved post-P0 synthesis direction into a concrete
implementation target for the main development thread.

It is not a permission slip to start `P1b` presentation work, persona registry
work, or source-adapter/ingestion work.

## Authoritative Inputs

This implementation spec is controlled by:

- `specs/p1_locked_execution_plan.md`
- `specs/p1_execution_state.yaml`
- `specs/p1a_reasoning_synthesis_layer.md`
- `specs/reasoning_synthesis_contract.yaml`
- `specs/persona_doctrine_contract.yaml`
- `specs/enzo_integration_review.md`
- `specs/p1_architecture_refactor_plan.md`
- `specs/advisor_runtime_spec.md`

Existing code boundaries that must be respected:

- `advisor/runtime.py`
- `agent_core/orchestrator.py`
- `agent_core/adapters/advisor.py`
- `agent_core/contracts.py`
- `agent_core/persona.py`
- `api/services/advisor_service.py`

## Current Baseline

The current runtime shape is:

`SafetyGuard -> Advisor runtime -> AgentResponse adapter -> PersonaBoundary`

Current behavior is still the pre-P1 architecture:

- `advisor.runtime.AdvisorAgent` produces the analytical substrate directly
- `agent_core.adapters.advisor.agent_response_from_advisor(...)` maps that
  substrate into `AgentResponse`
- `agent_core.persona.PersonaBoundary` adds a thin metadata/render wrapper
- no dedicated synthesis layer exists yet
- no doctrine-aware reasoning seam exists yet

This is acceptable as the starting point, but not as the target architecture.

## P1a Implementation Goal

The implementation must introduce a real synthesis layer between:

- grounded analytical substrate (`A`)
- approved doctrine/persona reasoning subset (`B`)

and produce a typed synthesis artifact that can later feed `P1b Reply + Why`
presentation.

The implementation target is:

`SafetyGuard -> Advisor analytical substrate -> Synthesis -> AgentResponse compatibility surface -> PersonaBoundary`

## Hard Scope Boundaries

### In Scope

- add a bounded synthesis module under `agent_core`
- add typed synthesis input/output contracts in product-side code
- build an adapter from current advisor analytical output into synthesis input
- allow doctrine-aware reasoning using only the approved reasoning-facing
  persona subset
- carry synthesis output through the existing API/runtime surface without
  breaking current clients
- add tests proving doctrine affects synthesis framing but not facts,
  confidence, warnings, or refusals

### Out Of Scope

- `P1b` `Reply + Why` presentation implementation
- persona registry/runtime selection architecture
- persona source adapters
- persona artifact ingestion
- managed persona creation pipeline
- case retrieval, embeddings, web-in-loop, persistence, or new tool chains
- battle-engine, battle-dex, or crawler redesign
- replacing current CLI/API/mobile contracts wholesale

## Hard Rules

1. LLM synthesis is the reasoning unit, not the truth unit.
2. Engine / SQL / approved-doc facts remain authoritative.
3. Persona doctrine may shape judgement priority and explanation framing only.
4. Persona doctrine may not change:
   - factual meaning
   - warning visibility
   - refusal behavior
   - confidence tier semantics
5. `expression_dna`, `display_name`, and `ip_safety_profile` do not enter
   synthesis.
6. The Enzo doctrine fixture is internal-only and must remain sanitized from
   public/default runtime identity.
7. `P1a` must preserve compatibility with current API/mobile consumers while
   preparing a clean handoff to `P1b`.

## Required Module Shape

### 1. New synthesis module

Add a new module:

- `agent_core/synthesis.py`

This module should own:

- synthesis input packing
- doctrine subset extraction
- synthesis execution boundary
- synthesis output validation
- deterministic compatibility fallback behavior when synthesis is unavailable

### 2. New synthesis-side contracts

Extend product-side contracts so a typed synthesis artifact exists in code.

Preferred target:

- keep `AgentResponse` as the transport object
- add an optional synthesis payload field rather than replacing the entire
  response shape

Required new typed concepts:

- `SynthesisInput`
- `DoctrinePack`
- `SynthesisWarning`
- `SynthesisResult`

Minimum `SynthesisResult` fields must align with
`specs/reasoning_synthesis_contract.yaml`:

- `synthesis_version`
- `synthesized_judgement`
- `why_summary`
- `surfaced_warnings`
- `followup_directions`
- `grounding_refs`
- `doctrine_refs`

### 3. Orchestrator insertion point

`agent_core/orchestrator.py` must become the layer owner for synthesis.

Required flow:

1. run safety evaluation
2. obtain analytical substrate from runtime adapter
3. build doctrine pack
4. run synthesis
5. project the synthesis result onto the compatibility response surface
6. attach persona metadata/render wrapper

Hard rule:

- synthesis must happen before persona rendering
- persona rendering remains style/presentation metadata only during `P1a`

### 4. Advisor adapter split

`agent_core/adapters/advisor.py` must stop being the place where final
product-facing reasoning is decided.

It should instead become responsible for:

- converting `AdvisorResponse` into a normalized analytical substrate
- preserving tool/evidence/confidence/follow-up structure
- exposing enough grounding references for synthesis

It should not:

- contain doctrine-specific reasoning logic
- render persona style logic
- implement `Reply + Why`

## Analytical Substrate Mapping

`P1a` should treat current `AdvisorResponse` as the grounded substrate source.

Mapping rules:

- `AdvisorResponse.answer_summary`
  - becomes analytical summary input only
  - it is no longer the authoritative final product judgement once synthesis is
    enabled
- `tool_results`
  - remain the source for backend/tool state
- `evidence_summary`
  - remain the source for factual grounding refs
- `confidence_notes`
  - remain the source for confidence boundary text
- `followup_options`
  - remain the source for default follow-up affordances

No deterministic field should be discarded during `P1a`.

## Doctrine Pack Rules

Doctrine packing must use only the synthesis-approved subset from
`specs/persona_doctrine_contract.yaml`:

- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`

The following are forbidden in the `P1a` synthesis input:

- `display_name`
- `expression_dna`
- franchise/IP markers
- rendering/taboo phrase data
- unsanitized lore anchors

The first doctrine fixture may be sourced from the reviewed internal Enzo
sample, but only through a sanitized internal fixture path.

Required doctrine references for the first implementation:

- generic doctrine identifiers derived from the Enzo review, such as:
  - `high_pressure_consequence_frame`
  - `compressed_verdict_style`
  - `anti_comfort_theater_heuristic`
  - `disputed_evidence_honesty_rule`
  - `method_over_moral_packaging_check`

## Compatibility Surface Rules

`P1a` must not force API/mobile clients to understand `P1b` before `P1b`
exists.

Therefore the implementation should use this temporary compatibility policy:

- `AgentResponse.answer`
  - should carry `synthesized_judgement` once synthesis succeeds
- `AgentResponse.persona.rendered_answer`
  - may continue to wrap the compatibility answer during `P1a`
- `AgentResponse.tool_results`
  - unchanged
- `AgentResponse.evidence`
  - unchanged
- `AgentResponse.confidence_notes`
  - unchanged
- `AgentResponse.followup_options`
  - preserved from synthesis output when explicitly returned, otherwise sourced
    from existing runtime follow-up options
- new optional `synthesis` field
  - carries the full `SynthesisResult` for future `P1b`

This preserves compatibility while making synthesis the real reasoning source.

## Warning And Refusal Rules

The implementation must preserve current safety behavior and warning visibility.

Required rule set:

- if the runtime returns a refusal or unsupported result, synthesis may
  compress/explain it but may not convert it into a normal recommendation
- if a current warning condition exists, the same warning must remain visible
  in `SynthesisResult.surfaced_warnings`
- if synthesis cannot safely produce a stronger judgement, it must stay
  provisional
- if synthesis execution fails, the system must return a bounded degraded
  response instead of silently inventing a judgement

Required surfaced warning coverage:

- partial team
- provisional only
- deterministic fallback
- unsupported scope
- refused missing context
- refused missing species

## Initial Synthesis Behavior

`P1a` should support the currently grounded product tasks only:

- team structure analysis
- species role analysis
- patch-direction recommendation synthesis
- low-evidence / disputed-context handling

Expected behavior improvements over the current baseline:

- move from analytical summary restatement to one grounded judgement
- make the causal priority clearer
- narrow fake-optionality when evidence supports a main direction
- retain uncertainty explicitly when evidence is partial or disputed

The implementation must not:

- invent new product tasks
- become a planner/agent loop
- claim live-meta or future-balance knowledge

## Implementation Shape By File

The expected implementation should mainly touch:

- `agent_core/contracts.py`
  - add typed synthesis models and optional response field
- `agent_core/synthesis.py`
  - new synthesis boundary
- `agent_core/orchestrator.py`
  - insert synthesis between runtime adapter and persona boundary
- `agent_core/adapters/advisor.py`
  - expose analytical substrate cleanly for synthesis input building
- `agent_core/persona.py`
  - only minimal compatibility adjustments if required by the new answer source
- `api/contracts.py`
  - only if optional schema exposure is required for the new response field
- tests under `tests/`
  - new synthesis coverage
  - updated orchestrator/API compatibility assertions

Avoid touching unrelated files unless a narrow compatibility fix is required.

## Validation Requirements

Implementation for this spec must include tests covering:

1. synthesis runs after safety and before persona rendering
2. doctrine changes judgement framing without changing grounded evidence refs
3. doctrine cannot mutate refusal outcomes
4. doctrine cannot remove or downgrade required warnings
5. fallback/degraded behavior is explicit when synthesis execution fails
6. current API/mobile-visible fields remain present and typed
7. `AgentResponse.answer` is synthesis-led after `P1a`
8. `AgentResponse.synthesis.why_summary` remains available for future `P1b`

At least these command classes must pass during implementation:

- targeted unit tests for `agent_core`
- API contract tests that serialize the updated response shape
- full project test suite

## Acceptance Criteria For This Spec

`P1a implementation` should be considered complete only if it satisfies all of
the following:

- a dedicated synthesis module exists
- synthesis consumes analytical substrate plus doctrine subset
- synthesis result is typed and attached to the product response
- synthesis becomes the source of `AgentResponse.answer`
- tool/evidence/confidence/refusal boundaries remain grounded and unchanged
- internal doctrine fixture can influence reasoning without introducing IP
  leakage or public-runtime identity coupling
- existing API/mobile compatibility is preserved

## Explicit Non-Goals For The Development Thread

When implementing this spec, do not:

- build `Reply + Why` UI or presentation logic beyond carrying `why_summary`
- redesign session state
- add multi-agent flows
- add persona registry CRUD or persona upload flows
- add web search/live patch prediction
- reopen P0 work unless a regression blocks `P1a`

## Next Step After This Spec

If this spec is accepted by the main thread, the next unlocked action is:

- `P1a implementation`

Until that acceptance happens, code implementation remains blocked by Gate 2.
