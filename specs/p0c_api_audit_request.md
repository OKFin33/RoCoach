# P0c FastAPI Backend Audit Request

## Purpose

This request is for a **test / architecture-audit thread**.

It audits the completed P0c FastAPI backend before P0d Persona/IP Guard, mobile
scaffold, or public-release hardening begins.

This is not a feature request.
This is not mobile work.
This is not persona rendering.
This is not deployment hardening.

## Source State

Main development thread reports P0c complete from:

- `specs/p0c_fastapi_backend_request.md`

Files changed:

- `requirements.txt`
- `api/__init__.py`
- `api/contracts.py`
- `api/dependencies.py`
- `api/main.py`
- `api/services/__init__.py`
- `api/services/advisor_service.py`
- `tests/test_api.py`
- `log/project_log.md`

Reported validation:

- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 89 tests`, `OK`

## Audit Focus

### 1. Endpoint Contract

Verify these endpoints exist and return bounded schemas:

```text
GET  /health
GET  /metadata
POST /chat
POST /team/analyze
GET  /species/search
GET  /species/{species_id}
```

Check:

- `/chat` and `/team/analyze` return app-facing `AgentResponse`.
- response payloads are JSON-serializable.
- `/species/search` and `/species/{species_id}` do not expose SQLite internals.
- `/metadata` does not expose local paths, env file paths, or secrets.

### 2. Agent Core Boundary

Verify:

- chat/team analysis go through `AgentOrchestrator` + `AdvisorRuntimeAdapter`
  where appropriate.
- API does not call battle engine directly.
- API does not call LLM providers directly.
- API does not shell out to CLI.
- API does not require mobile/frontend to read SQLite.

### 3. Session Continuity

Verify P0c's lightweight session model:

- `/chat` accepts optional `session_id`.
- `/chat` returns `session_id`.
- repeated calls with the same `session_id` preserve follow-up context.
- no durable persistence is introduced.
- no cross-device/session storage is introduced.
- no formal runtime-level `message_history` is introduced.
- no raw provider API keys are stored in session state.

### 4. Provider/API-Key Handling

Verify:

- API default backend is deterministic.
- `/chat` works without live provider/model key.
- request models do not accept provider API keys.
- metadata reports provider-key mode without leaking secrets.
- errors do not include `ROCO_OPENAI_API_KEY`, `test-key`, env file contents,
  or local secret paths.

### 5. Error Handling and Redaction

Verify bounded errors for:

- missing species.
- invalid team payload.
- unavailable battle-dex.
- invalid chat payload.
- unexpected internal failure if practical to simulate.

Check redaction:

- no SQLite DB path.
- no env file path.
- no provider key text.
- no traceback dump in API response.

### 6. Local API Basics

Verify:

- CORS config is local-development scoped.
- rate-limit placeholder exists but does not pretend to be real abuse control.
- `requirements.txt` contains only necessary API dependencies.

### 7. Regression

Run:

```bash
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Non-Goals

Do not:

- add mobile
- add persona rendering
- add case retrieval
- add embeddings
- add web-in-loop
- add durable cross-session persistence
- add hosted provider-key management
- add public deployment hardening beyond audit comments
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
2. `P0d/mobile readiness`
   - `ready_for_next_P0_track`
   - `needs_targeted_api_refactor`
   - `blocked`
3. endpoint contract judgement
4. agent-core boundary judgement
5. session continuity judgement
6. provider/key handling judgement
7. error/redaction judgement
8. findings with severity and file references
9. tests run and exact results

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0c_api_audit_request.md` first.

You are the test / architecture-audit thread. Audit the completed P0c FastAPI backend before P0d Persona/IP Guard, mobile scaffold, or public-release hardening begins.

Focus on endpoint contracts, AgentResponse serialization, agent_core boundary usage, session continuity, provider/API-key handling, bounded error behavior, redaction, local CORS/rate-limit placeholder, and CLI regression.

Do not add mobile, persona rendering, case retrieval, embeddings, web-in-loop, durable cross-session persistence, hosted provider-key management, public deployment hardening, data ingestion changes, backend policy changes, intentional CLI output changes, deterministic analyzer moves, battle-dex moves, or AdvisorAgent rewrites.

Run `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return verdict, P0d/mobile readiness, endpoint/agent-core/session/provider/redaction judgements, findings with severity, and exact tests run.
```
