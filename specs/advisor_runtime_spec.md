# Advisor Runtime Spec

## Purpose

Define the near-term runtime contract for the `Roco` conversational advisor.

This spec exists to constrain implementation so the project ships a usable
`conversational Agent CLI` instead of drifting into either:

- a thin prompt wrapper with weak evidence discipline
- an overbuilt autonomous runtime with infrastructure tax

Boundary note:

- the runtime produces an analytical contract
- the analytical contract is not identical to the final default user-facing surface
- post-P0 product direction adds:
  - a reasoning / synthesis layer above analytical facts
  - a conversational presentation layer above synthesis
- public/mobile default UX should not be raw runtime payload formatting

## Runtime Target

The approved runtime target is:

- `PydanticAI` native orchestration target
- local tool calls
- short multi-turn session state
- hybrid local RAG
- evidence-graded outputs

Migration note:

- a temporary dual-track period is allowed while the advisor migrates from a
  deterministic router path to `pydantic_ai_native`
- this does not change the runtime direction
- `PydanticAI` is no longer treated as an indefinitely optional hook for the
  conversational advisor

Runtime configuration note:

- native advisor execution may read model configuration from a local env file
  outside the repo
- approved near-term fields are:
  - `ROCO_ADVISOR_MODEL`
  - `ROCO_OPENAI_BASE_URL`
  - `ROCO_OPENAI_API_KEY`
- project files must not store live API keys
- CLI default backend policy may be `auto`:
  - valid native model config selects `pydantic_ai_native`
  - missing native model config falls back to `deterministic`
  - native runtime/provider failure or timeout under `auto` falls back to
    `deterministic` for supported flows
  - after a native failure under `auto`, the current CLI process may mark native
    unhealthy and skip repeated native timeout windows for later supported
    messages
  - explicit backend overrides remain authoritative

The runtime is not:

- a long-horizon autonomous agent
- a background planner
- a multi-agent workflow engine
- an open-ended web reasoner

## Core Responsibilities

The advisor runtime must:

1. parse the user request into an analysis task
2. decide which tools to call
3. retrieve only bounded approved context
4. assemble evidence into a typed response
5. preserve confidence and refusal policy
6. maintain a small session state for follow-up questions
7. remain compatible with a future synthesis-first product surface

The advisor runtime does **not** own the final coach-style wording shown by
default in product surfaces. In the approved post-P0 direction, the final
product answer should come from downstream reasoning/synthesis plus
presentation/persona layers.

## Core Components

### 1. AdvisorAgent

Responsibilities:

- receive user message
- choose tool sequence
- request retrieval context
- produce final response object

Hard rule:

- the agent may not bypass deterministic tools for structural facts

### 2. ToolRouter

Responsibilities:

- map intent to approved tool calls
- reject unsupported tool chains
- keep tool fan-out small

Initial approved tools:

- `analyze_team_structure`
- `get_species_profile`
- `get_species_available_moves`
- `retrieve_doc_context`
- `analyze_species_semantics`

Deferred, not MVP-required:

- `retrieve_case_context`
- `analyze_team_semantics`

### 3. ContextBuilder

Responsibilities:

- merge deterministic outputs with retrieval evidence
- separate `facts`, `mechanics`, and `cases`
- deduplicate redundant snippets
- label every context item with source and confidence tier

### 3.5 DoctrinePackBuilder

Responsibilities:

- build the approved non-factual advisory context (`B`)
- include mechanics, methodology, taxonomy, and taste constraints only from
  approved sources
- keep doctrine separate from deterministic facts

### 4. SessionStateStore

Responsibilities:

- keep current team state
- keep user goal/preferences
- keep last report/result summary
- allow incremental refinement in the same session

Scope boundary:

- session-local only
- no long-term memory in v1

### 5. TraceRecorder

Responsibilities:

- capture tool call order
- capture retrieval selections
- capture final confidence notes

The first implementation may write structured local traces only.

## Session State Contract

The runtime should maintain:

- `current_team`
- `current_species_context`
- `user_constraints`
- `last_analysis_type`
- `last_result_ref`
- `pending_followup_targets`

The runtime should not maintain:

- open-ended memory across threads
- implicit user profile beyond the active session
- hidden planning state unrelated to the current conversation
- formal runtime-level `message_history` as an approved session-state field in
  MVP

## Execution Loop

For each user message:

1. parse intent
2. inspect session state
3. choose tools
4. retrieve bounded context if needed
5. run analysis tools
6. build evidence package
7. generate typed answer
8. validate confidence and evidence rules
9. update session state

## Confidence And Refusal Rules

The runtime must:

- mark structural claims as `confirmed` only when backed by Engine or SQL facts
- mark semantic role claims as `provisional` unless a deterministic scorer later exists
- refuse unsupported species recommendation requests when required evidence is missing
- explicitly say when a claim depends on team context or assumed set context

## Failure And Fallback

If retrieval fails:

- continue with deterministic tools when possible
- reduce semantic ambition
- surface a lower-confidence answer

If semantic tools fail:

- return structure-only analysis
- note that semantic interpretation is unavailable

If native runtime execution fails or exceeds the configured timeout:

- under `auto`, return deterministic fallback where the requested flow supports it
- under `auto`, subsequent supported messages in the same CLI process may use
  deterministic fallback directly while native remains marked unhealthy
- under explicit `pydantic_ai_native`, return a bounded failure response
- do not silently fall back when the user explicitly requested native runtime

If team input is partial:

- analysis may continue on the supplied slots
- output must include a partial-team caveat
- follow-up options should ask for missing slots

If the request exceeds current product scope:

- refuse cleanly
- suggest the closest supported analysis
- for future/live-meta or official balance prediction requests, explicitly say
  the MVP has no web/live official-balance feed and cannot predict future
  buffs/nerfs or live meta changes

## Output Shape

Every final advisor response should contain:

- `answer_summary`
- `tool_results`
- `evidence_summary`
- `confidence_notes`
- `followup_options`

The CLI renderer may format this into prose, but the runtime contract should
stay typed.

Important:

- this typed response is the analytical substrate
- it may be surfaced directly in CLI/debug contexts
- it should not be treated as the final default mobile/product reply surface
- presentation/persona layers may reorder and summarize disclosure, but may not
  mutate facts, evidence, confidence, or refusal decisions

## Non-Goals

The first runtime does not provide:

- autonomous team building
- background ingestion refresh
- long-running planning
- persistent memory
- environment-aware live meta judgement

## Milestones

### M1

- single-session conversational CLI
- structure analysis + doc retrieval
- `PydanticAI` native runtime path established as the migration target
- local native-model env configuration path established outside the repo
- CLI `auto` backend policy established without expanding MVP scope
- native failure / timeout fallback semantics established for `auto`
- partial-team caveat requirement established

### M2

- battle-dex SQL retrieval
- species semantic analysis

### M3

- tactical case retrieval
- team semantic analysis

## Post-P0 Direction

The next approved product-direction change is:

- LLM should become the core analysis/synthesis unit for product-facing
  advisory judgement
- deterministic Engine / SQL / approved docs remain the source-of-truth unit
- default UX should feel like talking to a tactical coach
- structured fields remain the internal protocol and inspectable detail layer

Therefore, post-P0 work should add:

- `P1a Reasoning / Synthesis Layer`
- `P1b Conversational Presentation Layer`
- `P1c Pluggable Persona Contract`

before treating raw analytical runtime payloads as the main product experience.
