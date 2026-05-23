# P0a App-Facing Contract Audit Request

## Purpose

This request is for a **test / architecture-audit thread**.

It audits the completed P0a app-facing contract work before P0b minimal
agent-core extraction begins.

This is not a feature request.
This is not a FastAPI, mobile, persona, case retrieval, embedding, or crawler
task.

## Source State

Main development thread reports P0a complete from:

- `specs/p0a_app_facing_contract_request.md`

Files changed:

- `agent_core/__init__.py`
- `agent_core/contracts.py`
- `tests/test_agent_core_contracts.py`
- `log/project_log.md`

Reported validation:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 74 tests`, `OK`

## Audit Focus

### 1. Contract Shape

Verify `agent_core.contracts.AgentResponse` is suitable as an app/API-facing
boundary:

- stable `schema_version`
- aggregate `status`
- `backend`
- `analysis_type`
- user-visible `answer`
- `tool_results`
- top-level `evidence`
- structured `confidence_notes`
- structured `followup_options`
- optional `persona` envelope with facts locked

Check whether required fields are actually required and JSON-serializable.

### 2. Evidence References

Verify:

- every `AgentToolResult` has `evidence_refs`
- refs point to existing top-level `EvidenceItem.id`
- empty refs are allowed only when no evidence exists or the tool truly has no
  traceable evidence
- app/mobile can render evidence without looking into internal Advisor models

### 3. Boundary Cleanliness

Assess whether `agent_core/contracts.py` importing `advisor.contracts` is
acceptable for P0a or should be refactored before P0b.

The main-thread concern:

- product-facing contracts should ideally not depend on the CLI/advisor layer.
- adapter code may depend on `advisor`, but pure contract models should not need
  to.

Return one of:

- `acceptable_for_P0a`
- `refactor_before_P0b`
- `blocked`

### 4. Adapter Behavior

Check adapter behavior for:

- normal team response
- species response
- refusal response
- degraded `auto_fallback_deterministic` response
- native failure if easy to construct

Verify:

- CLI behavior is unchanged
- backend is preserved
- confidence strings become structured notes
- aggregate status mapping does not overclaim
- refusal/degraded/failed states are not collapsed into `ok`

### 5. Regression

Run:

```bash
.venv/bin/python -m unittest tests.test_agent_core_contracts
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

## Deliverable

Return:

1. `Verdict`
   - `PASS`
   - `PASS_WITH_FINDINGS`
   - `FAIL`
   - `BLOCKED`
2. `P0b readiness`
   - `ready_for_P0b`
   - `refactor_before_P0b`
   - `blocked`
3. contract shape judgement
4. evidence refs judgement
5. boundary cleanliness judgement
6. adapter behavior judgement
7. findings with severity and file references
8. tests run and exact results

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0a_contract_audit_request.md` first.

You are the test / architecture-audit thread. Audit the completed P0a app-facing contract before P0b begins.

Focus on contract shape, evidence_refs correctness, adapter behavior, JSON stability, CLI regression, and boundary cleanliness. In particular, judge whether `agent_core/contracts.py` importing `advisor.contracts` is acceptable for P0a or should be refactored before P0b.

Do not add FastAPI, mobile, persona rendering, case retrieval, embeddings, web-in-loop, formal message_history, cross-session persistence, data ingestion changes, backend policy changes, or intentional CLI output changes.

Run `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return verdict, P0b readiness, contract/evidence/boundary/adapter judgements, findings with severity, and exact tests run.
```
