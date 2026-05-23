# P0d Persona V1 + IP Guard Request

Supersession note, 2026-04-27:

This historical P0d request used `obsidian_tactical_coach` / `黑曜战术官` as
the original public-safe working identity. Current V1 runtime uses
`you_know_who` with public label `You know who` for the Enzo-derived distilled
persona layer. `obsidian_tactical_coach` is retained only as a legacy
compatibility alias.

## Purpose

Implement the first public-safe persona boundary for the Roco advisor product.

This is a bounded product-layer implementation task. It must not change battle
facts, tool execution, retrieval, data ingestion, or backend policy.

## Context

P0c FastAPI Backend has passed API audit and is ready for the next P0 track.

Existing product-side boundaries:

- `agent_core/contracts.py`
- `agent_core/orchestrator.py`
- `agent_core/persona.py`
- `agent_core/safety.py`
- `agent_core/adapters/advisor.py`

Current persona behavior is metadata-only:

- `PersonaBoundary.attach_metadata(...)`
- `PersonaEnvelope`
- `facts_locked=true`
- `fact_policy=persona_may_not_alter_facts`

P0d should turn this into a usable, public-safe persona boundary without
letting persona mutate facts.

## Required Behavior

### 1. Public-safe default persona

Add a default original persona.

Approved default:

- `persona_id`: `obsidian_tactical_coach`
- Chinese display candidate: `黑曜战术官`
- style: cold, precise, high-pressure, tactical

The persona must be original. It must not present itself as an official Roco
character.

### 2. IP guardrails

Add IP guard checks that prevent the public default persona from using:

- official Enzo / 恩佐 name
- official Enzo / 恩佐 artwork references
- official character identity claims
- official dialogue imitation
- wording that implies Tencent, 洛克王国 / Roco Kingdom, or official
  authorization

The guard may be conservative. A safe refusal or sanitized persona fallback is
better than leaking official-IP positioning.

### 3. Fact lock

Persona rendering must not alter:

- `status`
- `analysis_type`
- `backend`
- `tool_results`
- `evidence`
- `confidence_notes`
- `followup_options`
- refusal decisions

Persona may only add or update:

- `response.persona`
- `response.persona.rendered_answer`

The original `response.answer` must remain factual/base-layer output unless a
spec explicitly approves replacing it later.

### 4. Persona rendering boundary

Implement a small deterministic renderer or formatter.

It may rewrite the answer into `persona.rendered_answer`, but it must preserve
the factual content and confidence boundaries. Keep it intentionally simple.

Do not call an LLM for persona rendering in P0d.

### 5. API exposure

Expose persona metadata through existing `AgentResponse.persona`.

API may optionally accept a safe persona selector only if it does not add
provider keys, persistence, or unbounded user-defined persona prompts.

If request-side persona selection is too invasive, keep API behavior fixed to
the default persona or leave request selection deferred. Do not overbuild.

## Non-Goals

Do not add:

- mobile app
- GUI
- official Enzo persona
- official art or screenshot assets
- LLM-based persona rewriting
- case retrieval
- embeddings
- web-in-loop
- durable persistence
- hosted provider-key management
- public deployment hardening
- battle-dex ingestion changes
- backend policy changes
- CLI output changes unless required by tests and explicitly scoped

Do not move:

- deterministic analyzer
- battle-dex repository
- AdvisorAgent internals

## Acceptance Criteria

Tests must prove:

- default persona metadata can be attached.
- `facts_locked` is always true.
- `fact_policy` remains `persona_may_not_alter_facts`.
- persona rendering does not alter facts, evidence, confidence, tool results,
  follow-up options, status, backend, or refusal decisions.
- public default persona contains no official Enzo/恩佐/Tencent/洛克王国
  official-authorized positioning.
- unsafe official-IP persona requests are refused or sanitized.
- existing CLI/advisor/API tests still pass.

Required test commands:

```bash
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Deliverable

Return:

- files changed
- exact behavior added
- whether API request-side persona selection was implemented or deferred
- exact test results
- confirmation that scope stayed within P0d

## Copy-Paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0d_persona_ip_guard_request.md` first.

You are the main development thread. Implement P0d Persona V1 + IP Guard under the bounded scope in that spec.

Keep persona as a presentation boundary only. Do not let persona alter `status`, `analysis_type`, `backend`, `tool_results`, `evidence`, `confidence_notes`, `followup_options`, or refusal decisions. The base `answer` should remain factual/base-layer output unless the spec explicitly says otherwise; persona copy should live in `response.persona.rendered_answer`.

Add the public-safe default persona `obsidian_tactical_coach` / `黑曜战术官`. Add conservative IP guardrails against official Enzo/恩佐/Tencent/洛克王国 official-authorization positioning.

Do not add mobile, GUI, official Enzo persona, official assets, LLM-based persona rewriting, case retrieval, embeddings, web-in-loop, durable persistence, hosted provider-key management, public deployment hardening, battle-dex ingestion changes, backend policy changes, deterministic analyzer moves, battle-dex moves, AdvisorAgent rewrites, or intentional CLI output changes.

Run `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return files changed, exact behavior added, whether API request-side persona selection was implemented or deferred, exact test results, and confirmation that scope stayed within P0d.
```
