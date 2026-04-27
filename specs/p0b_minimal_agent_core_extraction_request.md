# P0b Minimal Agent Core Extraction Request

## Purpose

This request is for the **main development thread**.

It implements P0b from `specs/product_architecture_roadmap.md`.

Goal:

- stop treating `advisor/runtime.py` as the permanent product runtime boundary
- introduce a small `agent_core` orchestration boundary for future API/mobile
  usage
- preserve the completed CLI MVP as a regression harness

This is not an architecture rewrite.
This is not a FastAPI, mobile, persona-rendering, case retrieval, embedding, or
web task.

## Source State

Completed prerequisites:

- Advisor CLI MVP is complete.
- P0a app-facing contract normalization is complete.
- P0a boundary refactor is complete.
- `agent_core/contracts.py` is pure app/API-facing model code.
- Advisor-specific conversion lives in:
  - `agent_core/adapters/advisor.py`
- latest reported validation after boundary refactor:
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 77 tests`, `OK`

## Required Work

### 1. Add minimal `agent_core` orchestration boundary

Create small modules as needed, likely:

- `agent_core/orchestrator.py`
- `agent_core/tools.py`
- `agent_core/safety.py`
- `agent_core/persona.py`

Keep them intentionally thin.

The goal is to define boundaries, not to move business logic.

### 2. Define runtime/tool adapter protocol

Create a pure product-side protocol/interface that can execute one user message
and return `AgentResponse`.

It should not require API/mobile concepts yet.

It should not import `advisor.runtime` in pure protocol code.

Expected shape can be equivalent to:

```python
class AgentRuntimeAdapter(Protocol):
    def handle_message(self, message: str) -> AgentResponse: ...
```

Name can differ if the implementation is clearer.

### 3. Add minimal orchestrator

Create a small orchestrator that:

- accepts a runtime/tool adapter
- optionally applies a safety guard before execution
- optionally attaches or preserves persona metadata without rendering persona
  copy
- returns `AgentResponse`

The orchestrator must not:

- call battle engine directly
- call SQLite directly
- call LLM providers directly
- know CLI commands internally
- mutate facts, evidence, confidence notes, or refusal decisions

### 4. Add Advisor compatibility adapter

Extend or add adapter code under:

- `agent_core/adapters/advisor.py`

So existing `advisor.runtime.AdvisorAgent` can be wrapped behind the product
runtime adapter protocol.

Allowed:

- this adapter may import `advisor.runtime.AdvisorAgent`
- this adapter may use `agent_response_from_advisor`

Not allowed:

- `agent_core/orchestrator.py`, `agent_core/tools.py`, `agent_core/safety.py`,
  or `agent_core/persona.py` importing `advisor.*`

### 5. Add minimal safety/persona boundaries

Add only enough to enforce future boundary shape:

- safety guard can be a no-op default that returns allowed.
- persona layer can be a metadata envelope / policy object.
- persona must not alter facts, evidence, confidence, or refusal decisions.

Do not implement product persona rendering yet.

### 6. Tests

Add tests covering:

- pure `agent_core` modules do not import `advisor.*`
- Advisor compatibility adapter lives in adapter module and can import advisor
- orchestrator returns `AgentResponse`
- orchestrator preserves answer/evidence/confidence from adapter output
- safety refusal, if implemented, returns structured refused `AgentResponse`
  without calling the runtime adapter
- persona metadata, if attached, keeps `facts_locked=true` and does not alter
  factual fields
- existing Advisor CLI tests still pass

## Non-Goals

Do not:

- move deterministic analyzer code
- move battle-dex repository code
- rewrite `advisor.runtime.AdvisorAgent`
- intentionally change CLI output
- add FastAPI
- add mobile
- add persona rendering
- add case retrieval
- add embeddings
- add web-in-loop
- add formal runtime-level `message_history`
- add cross-session persistence
- change data ingestion
- change backend policy
- change native provider behavior

## Required Validation

Run:

```bash
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Expected Deliverable

Return:

1. files changed
2. new `agent_core` boundary summary
3. runtime/tool adapter protocol summary
4. Advisor compatibility adapter path
5. safety/persona boundary summary
6. tests added/updated
7. tests run and exact results
8. whether P0b is complete or blocked

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0b_minimal_agent_core_extraction_request.md` first.

You are the main development thread. Implement P0b Minimal Agent Core Extraction.

Create a small product-side `agent_core` orchestration boundary. Add pure protocols/interfaces for a runtime/tool adapter returning `AgentResponse`, a minimal orchestrator that delegates to that adapter, and minimal safety/persona boundaries that cannot alter facts/evidence/confidence/refusal decisions. Add or extend `agent_core/adapters/advisor.py` so existing `advisor.runtime.AdvisorAgent` can be wrapped behind the product adapter boundary.

Pure `agent_core` modules such as `orchestrator.py`, `tools.py`, `safety.py`, and `persona.py` must not import `advisor.*`; Advisor imports belong only in `agent_core/adapters/advisor.py`.

Do not move deterministic analyzer code, move battle-dex code, rewrite `AdvisorAgent`, change CLI output, add FastAPI, mobile, persona rendering, case retrieval, embeddings, web-in-loop, formal message_history, cross-session persistence, data ingestion changes, backend policy changes, or native provider behavior changes.

Add/update tests for pure import boundaries, orchestrator delegation, Advisor compatibility adapter, safety refusal if implemented, persona facts-locked behavior, and existing Advisor CLI regression.

Run `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return files changed, boundary summary, adapter protocol summary, Advisor compatibility adapter path, safety/persona boundary summary, tests run, and whether P0b is complete or blocked.
```
