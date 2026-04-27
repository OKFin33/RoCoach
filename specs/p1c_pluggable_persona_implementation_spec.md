# P1c Pluggable Persona Implementation Spec

## Purpose

Define the bounded implementation plan for `P1c Pluggable Persona Runtime`.

This stage upgrades persona from a single hardcoded rendering wrapper into a
safe, pluggable runtime layer above presentation and below future
adapter/ingestion tracks.

It is not permission to start:

- persona source adapter work
- persona artifact ingestion
- managed persona creation flow
- Battle Wiki expansion
- retrieval or eval infrastructure expansion beyond persona-specific regression coverage

## Authoritative Inputs

This implementation spec is controlled by:

- `specs/p1_locked_execution_plan.md`
- `specs/p1c_pluggable_persona_contract.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/p1_architecture_refactor_plan.md`
- `specs/p1b_presentation_implementation_spec.md`
- `specs/presentation_response_contract.yaml`

Existing code boundaries that must be respected:

- `agent_core/persona.py`
- `agent_core/contracts.py`
- `agent_core/orchestrator.py`
- `agent_core/presentation.py`
- `api/contracts.py`
- `api/services/advisor_service.py`
- `mobile/src/api/types.ts`
- `mobile/src/components/ResponsePanel.tsx`
- `tests/test_agent_core_contracts.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_api.py`

## Current Baseline

The current post-P1b runtime already has:

`A facts + B doctrine -> synthesis -> presentation -> persona render`

But persona is still effectively:

- one hardcoded safe default persona
- one metadata envelope with `persona_id`, `display_name`, `display_style`, and
  `rendered_answer`
- one hardcoded fallback policy based on forbidden markers

Current limitations:

- there is no typed persona doctrine/runtime artifact matching the five-layer shape
- persona selection is not backed by a real built-in registry
- persona metadata is too thin to support multiple safe built-ins cleanly
- the current wrapper is closer to a safety shim than a pluggable runtime surface

This is an acceptable bridge after `P1b`, but not the `P1c` target.

## P1c Implementation Goal

The implementation must introduce a safe pluggable persona runtime above
presentation.

Target architecture:

`A facts + B doctrine -> synthesis -> presentation -> persona selection/render -> AgentResponse compatibility surface`

The runtime must support:

- at least two built-in safe personas that can render the same grounded
  `Reply + Why` differently
- typed persona doctrine / rendering inputs
- selector sanitization with safe fallback
- invariance of facts, evidence, confidence, warnings, and refusals across personas

## Hard Scope Boundaries

### In Scope

- introduce a typed built-in persona registry/runtime under `agent_core`
- add typed persona doctrine / rendering-side contracts aligned with the
  five-layer contract
- make persona selection explicit and safe in the orchestrator/runtime path
- keep `presentation` canonical while allowing persona to vary expression,
  pacing, and style
- support API selection of a bounded built-in `persona_id`
- expose enough metadata for mobile/public surfaces to distinguish effective persona
- add tests proving multiple personas can render differently without changing
  grounded truth or safety boundaries

### Out Of Scope

- user-authored persona creation
- source adapters or distillation implementations
- persona artifact ingestion or admission workflow
- registry persistence beyond bounded built-in runtime entries
- original-IP persona enablement
- freeform prompt-based persona blobs

## Hard Rules

1. Persona controls expression, not truth.
2. `presentation` remains the canonical product surface.
3. Persona may change:
   - tone
   - diction
   - pacing
   - challenge style
   - phrasing of follow-up prompts
4. Persona may not change:
   - factual meaning
   - evidence attribution
   - confidence tier
   - warning visibility
   - refusal decisions
   - backend routing
5. Unsafe or unsupported `persona_id` values must fall back safely.
6. Official-IP markers must remain blocked in shipped defaults.
7. `P1c` must keep current API/mobile compatibility while making persona truly pluggable.

## Required Module Shape

### 1. Persona registry/runtime module

Add a bounded module under `agent_core`, for example:

- `agent_core/persona_registry.py`

This module should own:

- built-in persona registration
- safe selector lookup
- public-safe fallback resolution
- typed runtime persona loading

### 2. Typed persona-side contracts

Extend product/runtime contracts so persona is more than a thin envelope.

Required new typed concepts should cover:

- `ExpressionDNA`
- `PersonaMentalModel`
- `PersonaDecisionHeuristic`
- `PersonaHonestyBoundary`
- `PersonaProfile` or equivalent built-in runtime persona shape
- `PersonaRenderInput`

The five-layer doctrine shape from `specs/persona_doctrine_contract.yaml` must
be represented in bounded runtime form, but this stage may keep it as built-in
Python data rather than ingestion artifacts.

### 3. Orchestrator insertion point

`agent_core/orchestrator.py` must treat persona as a selected runtime layer,
not just an attached optional envelope.

Required flow:

1. run safety
2. obtain analytical substrate
3. run synthesis
4. run presentation
5. resolve effective persona from selector + built-in registry
6. render persona output from the presented answer
7. attach effective persona metadata to `AgentResponse`

Hard rule:

- persona remains downstream of presentation
- `AgentResponse.answer` and `response.presentation.reply` must remain the canonical non-persona answer

### 4. Persona boundary behavior

`agent_core/persona.py` should evolve from a hardcoded wrapper into a bounded
persona render boundary driven by selected built-in persona data.

It should become responsible for:

- rendering a selected safe persona over the canonical presented answer
- preserving fact lock invariants
- sanitizing unsafe selectors to a safe built-in default
- exposing the effective persona identity rather than the raw request

It should not:

- invent new facts
- rewrite visible warnings out of the answer
- alter `presentation.reply` or upstream synthesis meaning

## Built-In Persona Policy

`P1c` should support a bounded built-in set only.

Minimum target:

- one safe default persona continuing the current public-safe role
- one alternate safe persona with a meaningfully different expression profile

Both personas must:

- share the same fact lock policy
- preserve the same grounded `presentation.reply`
- preserve the same warnings and refusals
- differ only in allowed expression-layer outputs

## Compatibility Surface Rules

`P1c` must preserve current consumers while improving persona structure.

Compatibility policy:

- `AgentResponse.answer`
  - remains the canonical non-persona answer from presentation
- `AgentResponse.presentation`
  - remains canonical and inspectable
- `AgentResponse.persona.rendered_answer`
  - becomes the persona-rendered variant of the already-presented answer
- `AgentResponse.persona.persona_id`
  - must reflect the effective sanitized persona, not an unsafe raw request
- existing API/mobile consumers
  - may continue using `answer`, while richer surfaces can inspect persona metadata and rendered output

## Required Tests

The implementation must add focused tests proving:

- two safe built-in personas render the same grounded answer differently
- `answer`, `presentation.reply`, evidence, confidence, warnings, and refusals
  remain invariant across persona choices
- unsafe persona selectors fall back to the safe default
- effective persona metadata matches the sanitized persona, not the raw unsafe request
- API persona selection remains bounded and serializes correctly
- mobile/public consumers can distinguish canonical answer vs persona-rendered answer without ambiguity

## Explicit Non-Goals For This Stage

`P1c` does not include:

- source adapter execution
- ingestion validation/admission states
- managed persona creation product flow
- long-term persona storage or sync
- generalized marketplace / plugin persona ecosystem

## Implementation Readiness Check

`P1c implementation spec` is complete only when:

- it defines a bounded built-in persona runtime target
- it keeps persona strictly downstream of presentation
- it preserves canonical `answer` / `presentation` ownership
- it prevents selector drift and unsafe-IP drift
- it names the tests needed to prove persona pluggability without fact drift

## Next Unlocked Action

If accepted, the next legal stage is:

- `P1c implementation`

And the implementation packet must remain bounded to built-in runtime persona
pluggability only.
