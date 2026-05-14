# P0b Agent Core Architecture Audit Request

## Purpose

This request is for a **test / architecture-audit thread**.

It audits the completed P0b minimal agent-core extraction before P0c FastAPI or
P0d Persona work begins.

This is not a feature request.
This is not a FastAPI, mobile, persona-rendering, case retrieval, embedding,
web-in-loop, or crawler task.

## Source State

Main development thread reports P0b complete from:

- `specs/p0b_minimal_agent_core_extraction_request.md`

Files changed:

- `agent_core/tools.py`
- `agent_core/orchestrator.py`
- `agent_core/safety.py`
- `agent_core/persona.py`
- `agent_core/adapters/advisor.py`
- `agent_core/__init__.py`
- `tests/test_agent_core_orchestrator.py`
- `log/project_log.md`

Reported validation:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 83 tests`, `OK`

## Audit Focus

### 1. Pure Boundary Imports

Verify pure product modules do not import `advisor.*`:

- `agent_core.contracts`
- `agent_core.tools`
- `agent_core.safety`
- `agent_core.persona`
- `agent_core.orchestrator`

Advisor imports must be isolated to:

- `agent_core.adapters.advisor`

### 2. Orchestrator Behavior

Verify `AgentOrchestrator`:

- delegates one user message to the runtime adapter
- returns an `AgentResponse`
- preserves answer, status, evidence, confidence notes, tool results, and
  follow-up options from the adapter output
- does not call battle engine, SQLite, LLM providers, or CLI commands directly
- does not know Roco-specific command routing

### 3. Safety Boundary

Verify:

- default `SafetyGuard` allows normal messages
- refusal can return a structured refused `AgentResponse`
- refusal path does not call the runtime adapter
- safety refusal does not invent evidence

### 4. Persona Boundary

Verify:

- `PersonaBoundary` only attaches `PersonaEnvelope` metadata
- `facts_locked` is forced to `true`
- `fact_policy` is forced to `persona_may_not_alter_facts`
- persona metadata does not alter factual fields:
  - status
  - answer
  - tool results
  - evidence
  - confidence notes
  - refusal decision

### 5. Advisor Compatibility Adapter

Verify:

- `AdvisorRuntimeAdapter` lives in `agent_core.adapters.advisor`
- it wraps existing `advisor.runtime.AdvisorAgent`
- it converts Advisor responses through `agent_response_from_advisor`
- it does not rewrite Advisor runtime behavior
- CLI tests still pass

### 6. Regression

Run:

```bash
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Non-Goals

Do not:

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
- change CLI output intentionally
- move deterministic analyzer code
- move battle-dex repository code
- rewrite `AdvisorAgent`

## Deliverable

Return:

1. `Verdict`
   - `PASS`
   - `PASS_WITH_FINDINGS`
   - `FAIL`
   - `BLOCKED`
2. `P0c readiness`
   - `ready_for_P0c`
   - `needs_targeted_refactor`
   - `blocked`
3. pure-boundary import judgement
4. orchestrator judgement
5. safety/persona judgement
6. Advisor adapter judgement
7. findings with severity and file references
8. tests run and exact results

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0b_agent_core_audit_request.md` first.

You are the test / architecture-audit thread. Audit the completed P0b minimal agent-core extraction before P0c FastAPI or P0d Persona work begins.

Focus on pure import boundaries, orchestrator delegation behavior, safety refusal behavior, persona facts-locked behavior, Advisor compatibility adapter behavior, JSON/contract stability, and CLI regression.

Do not add FastAPI, mobile, persona rendering, case retrieval, embeddings, web-in-loop, formal message_history, cross-session persistence, data ingestion changes, backend policy changes, intentional CLI output changes, deterministic analyzer moves, battle-dex moves, or AdvisorAgent rewrites.

Run `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return verdict, P0c readiness, pure-boundary/orchestrator/safety/persona/adapter judgements, findings with severity, and exact tests run.
```
