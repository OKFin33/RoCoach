# Product Architecture Roadmap

## Purpose

This document defines the product and architecture roadmap after the completed
Advisor CLI MVP.

It covers:

- macro architecture
- short-term execution plan
- long-term product plan
- repo-to-architecture mapping
- public-release gaps
- IP and persona boundaries

This is a main-thread planning document. It is not an implementation request by
itself.

## Current Baseline

As of `2026-04-19`, the repo state is:

- Advisor CLI MVP is complete.
- Deterministic battle/type engine is available.
- SQLite battle-dex repository is available.
- Curated bounded doc retrieval is available.
- `deterministic`, `pydantic_ai_native`, and `auto` advisor backends exist.
- `auto` is native-first with deterministic fallback for supported flows.
- `agent_core` now defines the pure app/API-facing response contract and thin
  orchestrator boundary.
- FastAPI local product backend exists and passed P0c API audit.
- API session continuity is in-memory per-process through optional
  `session_id`.
- API default backend is deterministic; request models do not accept provider
  API keys.
- Tool status contract now uses only:
  - `ok`
  - `degraded`
  - `refused`
  - `failed`
- Full test suite reports:
  - `.venv/bin/python -m unittest discover -s tests`
  - `Ran 89 tests`
  - `OK`

Current runtime is no longer CLI-only. It has a local FastAPI product boundary,
but it is not yet a mobile product release.

P0 status:

- P0 scope is complete.
- The repo is ready for post-P0 planning.

Presentation status:

- the system already has a stable analytical contract
- the next product gap is not factual substrate, but grounded reasoning /
  synthesis plus default conversational presentation
- structured evidence/confidence/tool traces should be treated as internal
  protocol plus inspectable detail, not as the default user-facing surface

## Product Target

First public release target:

- mobile app
- user-supplied model/API-key configuration
- conversational battle advisor
- character-presented Agent
- LLM-synthesized coach-style default conversational answers
- inspectable evidence/confidence/detail drawer
- team structure analysis
- species lookup and follow-up questions
- deterministic fallback when native/LLM path fails

The first public character should be an original persona, not an official Enzo
implementation.

Approved public positioning:

- unofficial Roco battle analysis tool
- character-like tactical coach
- user-configurable persona framework
- default original dark-alchemist / tactical-officer persona

Disallowed for public release:

- official Enzo name as product character
- official Enzo artwork
- official screenshots / portraits / logo reuse
- official dialogue imitation
- wording that implies Tencent, Roco Kingdom, or official authorization

## Macro Architecture

Target architecture:

```text
Mobile App
  -> Product API
    -> Agent Orchestrator
      -> Safety / IP Guard
      -> Tool Router
      -> Deterministic Engine
      -> Battle-Dex Repository
      -> Retrieval Layer
      -> Battle Doctrine Pack
      -> Persona Doctrine Pack
      -> LLM Reasoning / Synthesis Layer
    -> Analytical Response Contract
    -> Synthesis Contract
  -> Presentation Layer
    -> Persona Layer
    -> Evidence / Confidence / Tool Detail UI
```

Trust hierarchy:

```text
Engine / SQLite facts
  > approved doctrine / methodology docs
  > curated cases, once added
  > LLM synthesis
  > persona style
```

Hard rule:

- reasoning/synthesis may combine and explain grounded inputs only
- presentation and persona may change wording, ordering, and default disclosure
  only.
- reasoning/presentation/persona may not change facts, confidence tier,
  evidence references, or refusal decisions.

## Core Design Principles

### 1. Fact Ownership

Confirmed facts must come from:

- `battle_engine`
- `roco_world_model`
- `BattleDexRepository`
- approved static docs

LLM output must not create confirmed facts.

### 2. Product Boundary Before Mobile

The mobile app must call a stable API contract.

The mobile app must not:

- shell out to CLI
- read SQLite directly
- call LLM providers directly for core advisor behavior
- duplicate battle logic

### 3. Persona Isolation

Persona is a presentation layer.

Persona can control:

- tone
- phrasing
- pacing
- challenge style
- short flavor lines

Persona cannot control:

- tool selection rules
- factual claims
- evidence contents
- confidence notes
- refusal policy
- IP-sensitive names or official assets

### 3.5. Default User-Facing Surface

The default user-facing output should feel like talking to a tactical coach.

Therefore:

- the primary visible message should be conversational
- the visible answer should come from a synthesis step, not from raw
  deterministic payload formatting
- raw structured fields should not be the default first screen
- evidence/confidence/tool traces remain mandatory but should live in an
  inspectable secondary layer
- the user should be able to understand the main conclusion without reading raw
  protocol fields first

### 4. Graceful Degradation

The product must still produce useful deterministic output when:

- native provider is missing
- user API key is invalid
- provider times out
- retrieval returns no useful snippets
- species is not found

### 5. Evidence Visibility

Every answer that uses analytical tools should expose:

- a coach-style primary message
- inspectable evidence items
- inspectable confidence notes
- inspectable unsupported/provisional boundary
- inspectable tool traces at detail/debug level

Mobile UI should hide analytical complexity by default but keep evidence
inspectable.

### 6. API-Key Handling Boundary

Public release must choose and document one provider-key mode before mobile
integration:

- local-user-key mode:
  - mobile stores the user key in platform secure storage.
  - API receives provider config only for the current request/session.
  - logs and errors must redact provider config.
- backend-managed-key mode:
  - backend owns provider configuration.
  - mobile never sees provider secrets.
  - hosted deployment needs stricter abuse controls and rate limits.

Do not mix the two modes implicitly.

Until this is decided, API and mobile work must keep provider configuration
behind explicit interfaces and tests.

### 7. Session Continuity Before Mobile

The completed CLI MVP is session-local.

Before mobile release, the API contract must define how follow-up context is
carried:

- client-managed session state
- or API-managed lightweight session state

Full persistent history is not required for P0, but mobile cannot rely on a
hidden CLI process state.

## Proposed Repo Layout

Target layout:

```text
Roco/
  battle_engine/
    # deterministic team/type analysis

  roco_world_model.py
    # type chart and type mechanics

  advisor/
    # current CLI runtime; gradually becomes compatibility layer

  agent_core/
    contracts.py
    orchestrator.py
    synthesis.py
    presentation.py
    persona.py
    persona_registry.py
    persona_doctrine.py
    safety.py
    tools.py
    memory.py
    response.py

  api/
    main.py
    contracts.py
    routes/
    services/
    dependencies.py

  mobile/
    package.json
    app.json
    src/
      screens/
      components/
      api/
      state/
      theme/

  reporting/
    # report generation and validation

  tools/
    # crawler/importer/admin tools

  data/
    # runtime SQLite and generated artifacts

  infra/
    Dockerfile
    docker-compose.yml
```

Migration rule:

- Do not move battle engine or battle-dex code until API and agent boundaries
  are stable.
- Extract `agent_core` by copying small contracts/adapters first, not by a large
  rewrite.
- Keep `advisor.conversation_cli` working as a regression harness.

## Current Repo Mapping

Implemented:

| Capability | Current location | Status |
| --- | --- | --- |
| Type mechanics | `roco_world_model.py` | implemented |
| Team structure analysis | `battle_engine/team_structure.py` | implemented |
| CLI team analysis | `battle_engine/phase1_cli.py` | implemented |
| Report generation | `reporting/` | implemented |
| Battle-dex SQLite access | `advisor/battle_dex.py` | implemented |
| CLI advisor runtime | `advisor/runtime.py` | implemented |
| CLI entrypoint | `advisor/conversation_cli.py` | implemented |
| Curated doc retrieval | `advisor/retrieval.py` | implemented |
| Runtime response contracts | `advisor/contracts.py` | partially product-ready |
| App-facing response schema | `agent_core/contracts.py` | implemented |
| Agent orchestrator module | `agent_core/orchestrator.py` | implemented |
| Persona V1 boundary | `agent_core/persona.py` | implemented and audited |
| Safety boundary | `agent_core/safety.py` | minimal allow/refuse implemented |
| Product API | `api/` | implemented and P0c-audited |
| Import pipeline | `tools/` and `data/importer_runs/` | implemented |

Missing:

| Capability | Target location | Status |
| --- | --- | --- |
| Reasoning / synthesis layer | `agent_core/synthesis.py` | missing |
| Conversational presentation layer | `agent_core/presentation.py` | missing |
| Pluggable persona contract/registry | `agent_core/persona_registry.py` | missing |
| Persona doctrine layer | `agent_core/persona_doctrine.py` | missing |
| Persona source-adapter layer | `agent_core/persona_sources.py` | missing |
| Persona ingestion/review layer | `agent_core/persona_ingestion.py` | missing |
| Persistent app sessions | `agent_core/memory.py` or `api/services/session.py` | P1; not required for P0 |
| Mobile app | `mobile/` | implemented and audited |
| Deployment config | `infra/` | missing |
| Production rate limiting | `api/` | placeholder only |
| Public data/version endpoint | `api/` | missing |

## Known Contract Gap

Resolved for app/API-facing output:

- `agent_core/contracts.py` defines `AgentResponse`.
- `AgentToolResult.evidence_refs` is required.
- `ConfidenceNote` is structured.
- Adapter logic is isolated in `agent_core/adapters/advisor.py`.
- `advisor/runtime.py` remains CLI/runtime compatibility code.

Remaining caution:

- `advisor/contracts.py` is still CLI/runtime-facing.
- Mobile and API should use `agent_core.contracts.AgentResponse`, not
  `advisor.contracts.AdvisorResponse`.
- `AgentResponse` is the analytical/app contract, not the final default
  presentation surface.

## Short-Term Plan

P0 work is ordered. Do not parallelize later P0 tracks until their dependencies
exist.

### P0a. App-Facing Contract Normalization

Goal:

- define one stable response shape for API and mobile.

Work:

- create `agent_core/contracts.py`
- define:
  - `AgentResponse`
  - `AgentToolResult`
  - `EvidenceItem`
  - `ConfidenceNote`
  - `FollowupOption`
  - `PersonaEnvelope`
- decide whether `evidence_refs` are required.
- add schema tests that validate all required fields, not just status enum.
- provide adapter from current `AdvisorResponse` to `AgentResponse`.

Acceptance:

- CLI still passes existing tests.
- new contract tests fail on missing required fields.
- serialized API payload is stable for mobile.

Non-goals:

- no API.
- no mobile.
- no persona rendering.
- no case retrieval.
- no embeddings.
- no web-in-loop.
- no runtime policy change.

### P0b. Minimal Agent Core Extraction

Goal:

- stop treating `advisor/runtime.py` as the permanent product runtime.

Work:

- create `agent_core/`.
- move or wrap only product boundaries:
  - response assembly
  - persona selection
  - safety checks
  - tool adapter interfaces
- do not rewrite the deterministic analyzer.
- do not break `advisor.conversation_cli`.

Acceptance:

- current CLI can use the new adapter or remain backed by compatibility code.
- no battle facts move into persona code.
- safety checks can run without a live model.

Dependency:

- P0a app-facing contract normalization.

Status:

- implementation completed.
- persona/IP guard audit returned `PASS`.
- mobile readiness returned `ready_for_P0e_mobile_scaffold`.
- full suite reported after implementation: `Ran 93 tests`, `OK`.
- P0e Mobile MVP Scaffold is ready for scheduling.

### P0c. FastAPI Backend

Goal:

- expose the advisor as a product service.

Required endpoints:

```text
GET  /health
GET  /metadata
POST /chat
POST /team/analyze
GET  /species/search
GET  /species/{species_id}
```

Work:

- add `fastapi` and `uvicorn` dependencies.
- create `api/main.py`.
- add request/response models based on `AgentResponse`.
- add DB dependency wrapper.
- add bounded timeout behavior.
- add CORS config.
- add basic rate-limit hook or placeholder interface.
- add session-continuity contract for follow-up questions.
- add provider config interfaces without logging API keys.
- ensure API keys are never logged.

Acceptance:

- API tests cover all endpoints.
- `/chat` can execute deterministic flow without live model key.
- `/metadata` exposes battle-dex version/import run.
- app does not need to know SQLite paths.
- app does not need to know CLI internals.
- provider/API-key errors are bounded and redacted.

Dependencies:

- P0a app-facing contract normalization.
- preferably P0b minimal agent core extraction.

Status:

- completed.
- API architecture audit returned `PASS`.
- P0d/mobile readiness returned `ready_for_next_P0_track`.

### P0d. Persona V1 + IP Guard

Update, 2026-04-27:

- current V1 runtime id: `you_know_who`
- current public label: `You know who`
- source boundary: Enzo-derived distilled persona layer after abstraction and
  IP sanitization
- legacy alias only: `obsidian_tactical_coach` / `黑曜战术官`
- public UI must not expose Enzo/恩佐 or official-character positioning

Goal:

- provide an original default character posture for public release.

Default persona:

- working name: `Obsidian Tactical Coach`
- Chinese display candidate: `黑曜战术官`
- style: cold, precise, high-pressure, tactical
- no official Enzo name, art, dialogue, or story references

Work:

- define persona contract.
- define public-safe default persona.
- add IP guardrails.
- add tests:
  - persona cannot mark provisional claims as confirmed
  - persona cannot remove evidence notes
  - persona cannot inject official IP names into public default output

Acceptance:

- same factual input produces same evidence/confidence after persona rendering.
- public default persona contains no official character names.
- persona rendering cannot alter factual evidence, confidence tier, or refusal
  decision.

Dependency:

- P0a app-facing contract normalization.

Status:

- completed.
- persona/IP guard audit returned `PASS`.
- mobile readiness returned `ready_for_P0e_mobile_scaffold`.

### P0e. Mobile MVP Scaffold

Goal:

- create the first mobile shell after API contract is stable.

Recommended stack:

- React Native
- Expo
- TypeScript

Initial screens:

- chat screen
- team editor
- species search
- evidence drawer
- settings/local API base URL screen

Acceptance:

- app can connect to local API.
- user can ask a team analysis question.
- user can inspect evidence.
- local API connection failure is visible and recoverable.
- mobile does not read SQLite, shell out to CLI, or duplicate battle logic.

Dependencies:

- P0a app-facing contract normalization.
- P0c FastAPI backend.
- P0d Persona V1 + IP Guard.

Status:

- completed.
- mobile scaffold audit returned `PASS`.
- P0f readiness returned `ready_for_P0f_hardening`.

### P0f. Public-Release Hardening

Goal:

- make the first public release operable and safe.

Work:

- Docker or equivalent local run path.
- `.env.example` without live secrets.
- healthcheck.
- structured logs.
- log redaction.
- version endpoint.
- basic rate limiting.
- provider config validation.
- bounded timeout tests.
- public disclaimer / unofficial positioning copy.

Acceptance:

- local run path works from a clean checkout.
- API keys are never committed, logged, or bundled.
- provider failure is visible and recoverable.
- public default persona/assets contain no official IP names or assets.

Dependencies:

- P0c FastAPI backend.
- P0d Persona V1 + IP Guard.
- P0e Mobile MVP Scaffold.

Status:

- completed.
- hardening audit returned `PASS`.
- post-P0 readiness returned `ready_for_post_P0_planning`.

### P0g. Native Provider Reliability

Goal:

- turn the accepted MVP P3 finding into a product reliability check.

Work:

- validate provider config before expensive calls where feasible.
- keep timeout behavior bounded.
- keep `auto` fallback behavior.
- redact provider config in logs/errors.
- add tests for local/unreachable/missing provider states.

Acceptance:

- valid provider path can be verified in a controlled environment.
- unreachable provider does not stall repeated requests.
- explicit native failure remains bounded and does not silently fall back.

Dependency:

- P0c FastAPI backend if tested through API, otherwise can be done earlier as a
  runtime reliability pass.

## Medium-Term Plan

Sequence note:

- because the product target is coach-style conversation by default, post-P0
  work should prioritize reasoning/synthesis, then presentation, then persona
  contract upgrades before persistence and deeper advisory-intelligence tracks

### P1a. Reasoning / Synthesis Layer

Goal:

- make LLM the core analysis unit for product-facing advisory judgement without
  making it the source-of-truth unit

Work:

- define a synthesis-layer contract that consumes:
  - analytical facts (`A`)
  - battle doctrine / methodology context (`B`)
- allow the reasoning-facing subset of persona doctrine to enter `B`
- make synthesis responsible for:
  - concrete advisory judgement
  - reasoning summary
  - reply/why intent
  - mandatory warning surfacing
- keep deterministic engine / SQL / approved docs as fact owners
- keep synthesis output grounded, inspectable, and validator-friendly

Non-goal:

- no fact ownership transfer into the LLM
- no freeform open-ended reasoning without tool/retrieval boundaries

### P1b. Conversational Presentation Layer

Goal:

- turn synthesized advisory output into the default coach-style user-facing
  reply surface

Work:

- define a presentation-layer contract that consumes synthesis output
- default front-stage surface should be:
  - `Reply`
  - `Why`
- fold evidence/confidence/tool traces into secondary inspectable UI
- define when warnings must remain visible in `Reply` or `Why`
- keep CLI free to remain a more explicit/debug-oriented inspection surface

Non-goal:

- no change to fact ownership, tool evidence, or confidence policy

### P1c. Pluggable Persona Contract

Goal:

- make persona a first-class rendering strategy above synthesis/presentation,
  rather than a single attached metadata field

Work:

- define persona rendering contract
- adopt the five-layer doctrine shape:
  - expression DNA
  - mental models
  - decision heuristics
  - anti-patterns
  - honesty boundaries
- define safe built-in persona schema
- define what persona may and may not control
- keep official third-party IP personas out of shipped defaults
- support future local user-defined personas only behind explicit safety rules

Non-goal:

- no arbitrary prompt-driven persona override in the core product path
- no persona ability to alter facts, evidence, confidence, or refusals

### P1d. Persona Source Adapter Contract

Goal:

- support multiple upstream persona-creation methods without coupling runtime
  to a single tool such as Nuwa

Work:

- define `distill_from_existing_subject` adapters
- define `design_from_zero` adapters
- keep all source adapters artifact-producing only

### P1e. Persona Artifact Ingestion

Goal:

- normalize, validate, review, and admit persona artifacts before runtime use

Work:

- define registry admission states
- define provenance checks
- define schema/safety/review gates
- keep public-safe approval separate from raw creation success

### P1f. Managed Persona Creation Pipeline

Goal:

- expose one unified product path for persona creation while keeping the
  internal system pipeline-based

Work:

- source adapter selection
- artifact generation
- ingestion and review
- registry admission
- runtime availability after approval

### P1. Session Persistence

Goal:

- support mobile sessions beyond a single CLI process.

Work:

- session table or lightweight file/SQLite store.
- store current team, current species context, constraints, and last result ref.
- avoid storing raw provider API keys.

Non-goal:

- no long-term personality memory in first public release.

P0 boundary:

- API/mobile must define session-continuity mechanics before release.
- durable persistence, saved teams, and cross-device history can stay P1.

### P1. Better Species UX

Work:

- autocomplete species search.
- display types, BST, ability, available moves.
- show confidence and source layer.
- show "not enough evidence" states clearly.

### P1. Deterministic Role Scoring

Goal:

- reduce overreliance on LLM semantic phrasing.

Work:

- add deterministic role feature extraction from stats, move categories, and
  utility tags.
- keep role labels provisional until casebank exists.

### P1. Casebank Phase A

Goal:

- support team-conditional role judgement with curated examples.

Work:

- define casebank schema.
- add curated cases manually.
- retrieve by metadata first.
- do not add embeddings until metadata retrieval proves insufficient.

### P1. Deployment Readiness

Work:

- production deployment profiles beyond the P0 local run path.
- hosted environment configuration.
- observability beyond basic structured logs.
- abuse controls beyond basic rate limiting.
- backup/restore process for user data if persistence is enabled.

## Long-Term Plan

### Phase 2. Productized Agent Platform

Capabilities:

- multiple original personas
- user-created local personas
- persona marketplace only if IP guardrails are enforceable
- richer battle explanations
- saved teams
- shareable analysis reports

Constraint:

- official third-party IP personas must not be shipped by default.

### Phase 3. Hybrid Retrieval Upgrade

Capabilities:

- structured SQL retrieval
- curated doc retrieval
- case retrieval
- optional embeddings for docs/cases
- lightweight reranking

Rule:

- factual battle-dex fields stay SQL-first.
- embeddings must never override exact facts.

### Phase 4. Meta Snapshot System

Capabilities:

- curated meta snapshots
- environment-specific risk analysis
- trend notes with confidence labels

Required before hard meta claims:

- source provenance
- timestamped snapshot
- sample methodology
- confidence policy

Without these, meta claims stay refused or low-confidence.

### Phase 5. Battle Simulation / Recommendation Layer

Capabilities:

- scenario simulation
- matchup explanation
- set-aware recommendations
- replacement suggestions

Required gates:

- deterministic scoring
- case evidence
- confidence labels
- refusal when data is insufficient

## Public Release Gate

First public release is not ready until all P0 gates pass.

P0 release gates:

- app-facing response contract exists and is tested.
- API backend exists and passes contract tests.
- mobile app can complete one chat analysis flow.
- species search works through API.
- evidence drawer exists.
- default persona is original and public-safe.
- persona cannot alter factual evidence or confidence.
- deterministic fallback works without live model.
- user API-key/provider errors are handled cleanly.
- no official character assets or names ship in public default.
- Docker or equivalent local run path exists.
- API keys are never committed, logged, or bundled.

## Risk Register

### R1. IP / Persona Risk

Risk:

- using official Enzo name, artwork, or promotional framing can trigger IP,
  trademark, or platform takedown risk.

Mitigation:

- ship only original default persona.
- allow local user-defined personas without bundling infringing content.
- add public disclaimer.
- add IP guard tests for default persona assets/content.

### R2. Contract Drift

Risk:

- mobile app breaks because backend response shape changes.

Mitigation:

- define app-facing contract.
- generate sample fixtures.
- add contract tests.
- version the API.

### R3. Runtime Monolith

Risk:

- `advisor/runtime.py` grows into a product monolith.

Mitigation:

- extract `agent_core` boundaries before API/mobile work.
- keep CLI as compatibility shell.

### R4. Unsupported Claims

Risk:

- persona or LLM makes authoritative claims without evidence.

Mitigation:

- preserve confidence policy.
- validate evidence-backed outputs.
- keep confirmed facts limited to Engine/SQL/static docs.

### R5. Provider/API-Key Handling

Risk:

- user keys leak through logs, crash reports, or mobile storage.

Mitigation:

- do not log keys.
- redact provider config.
- store locally with platform secure storage if mobile handles keys.
- prefer backend-side provider config for hosted deployment.

## Recommended Next Assignment

Next bounded implementation request:

```text
Implement P0a App-Facing Contract Normalization.

Create `agent_core/contracts.py` and adapter logic from current
`advisor.contracts.AdvisorResponse` to the app-facing `AgentResponse`.
Add full contract tests that validate required fields, evidence shape,
confidence note shape, tool status enum, and JSON serialization.

Do not add API, mobile, persona rendering, case retrieval, embeddings,
web-in-loop, formal message_history, cross-session persistence, data ingestion
changes, backend policy changes, or intentional CLI output changes.
```

Reason:

- mobile and API should not start on an unstable response shape.
- this is the smallest high-leverage boundary before productization.
