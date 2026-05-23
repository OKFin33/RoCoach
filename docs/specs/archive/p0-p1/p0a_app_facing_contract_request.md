# P0a App-Facing Contract Normalization Request

## Purpose

This request is for the **main development thread**.

It implements the first post-MVP productization step from
`specs/product_architecture_roadmap.md`.

Goal:

- define a stable app/API-facing response contract before FastAPI, mobile,
  persona rendering, case retrieval, embeddings, or web-in-loop work begins.

This is a contract-boundary task, not a feature-expansion task.

## Context

Current completed baseline:

- `Advisor CLI MVP complete`
- deterministic backend exists
- `pydantic_ai_native` backend exists
- `auto` backend exists
- `auto` is native-first with deterministic fallback for supported flows
- SQLite battle-dex retrieval exists
- bounded curated doc retrieval exists
- CLI remains the regression harness

Known gap:

- `specs/advisor_response_contract.yaml` is not fully aligned with current
  Pydantic models.

Current YAML expects:

- `tool_results[].evidence_refs`
- `confidence_notes[]` as structured objects
- `evidence_summary[]` as strings

Current code provides:

- `AdvisorToolResult` without `evidence_refs`
- `confidence_notes: list[str]`
- `evidence_summary: list[AdvisorEvidenceItem]`

This is acceptable for the completed CLI MVP, but not acceptable for API/mobile
release.

## Required Work

### 1. Create `agent_core` contract boundary

Create:

- `agent_core/__init__.py`
- `agent_core/contracts.py`

Define app-facing typed models, at minimum:

- `AgentResponse`
- `AgentToolResult`
- `EvidenceItem`
- `ConfidenceNote`
- `FollowupOption`
- `PersonaEnvelope`

The contract must preserve:

- response status
- backend
- analysis type
- user-visible answer
- tool results
- evidence
- structured confidence notes
- follow-up options
- refusal / degraded / failed states
- optional persona envelope without allowing persona to alter facts

### 2. Define evidence-reference policy

Decide and encode one rule:

- either `AgentToolResult.evidence_refs` is required and points to
  `EvidenceItem.id`
- or evidence is only top-level and tool results carry no refs

If choosing the second option, document why the app can still render traceable
evidence.

Recommendation:

- prefer `evidence_refs` for product/API usage.

### 3. Add adapter from `AdvisorResponse`

Create adapter logic from:

- `advisor.contracts.AdvisorResponse`

to:

- `agent_core.contracts.AgentResponse`

The adapter may live in one of:

- `agent_core/contracts.py`
- `agent_core/adapters.py`
- `advisor/runtime.py` only if the boundary stays clean

The adapter must not change runtime behavior.

### 4. Add contract tests

Add tests that validate:

- required fields exist
- tool status enum is only `ok`, `degraded`, `refused`, `failed`
- evidence shape is stable
- confidence notes are structured objects, not raw strings
- JSON serialization is stable
- adapter handles:
  - normal team analysis response
  - species response
  - refusal response
  - degraded/fallback response if existing fixtures make this practical

Tests should fail if a required field is removed or changes shape.

### 5. Preserve CLI compatibility

Existing CLI behavior must remain unchanged.

Minimum validation:

```bash
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
- change battle-dex schema
- change backend policy
- change CLI output intentionally
- move battle engine or battle-dex code

## Expected Deliverable

Return:

1. files changed
2. app-facing contract shape summary
3. evidence-reference decision
4. adapter behavior
5. tests added/updated
6. tests run and exact results
7. whether P0a is complete or blocked

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0a_app_facing_contract_request.md` first.

You are the main development thread. Implement P0a App-Facing Contract Normalization.

Create `agent_core/contracts.py` and app/API-facing typed models. Add adapter logic from current `advisor.contracts.AdvisorResponse` to `agent_core.contracts.AgentResponse`. Add full contract tests validating required fields, evidence shape, structured confidence notes, tool status enum, and JSON serialization.

Do not add FastAPI, mobile, persona rendering, case retrieval, embeddings, web-in-loop, formal message_history, cross-session persistence, data ingestion changes, backend policy changes, or intentional CLI output changes.

Run `.venv/bin/python -m unittest tests.test_advisor` and `.venv/bin/python -m unittest discover -s tests`.

Return files changed, contract shape summary, evidence-reference decision, adapter behavior, tests run, and whether P0a is complete or blocked.
```
