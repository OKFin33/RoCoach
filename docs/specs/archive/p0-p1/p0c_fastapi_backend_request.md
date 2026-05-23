# P0c FastAPI Backend Request

## Purpose

This request is for the **main development thread**.

It implements P0c from `specs/product_architecture_roadmap.md`.

Goal:

- expose the completed Advisor product boundary as a local/product API service
- make mobile/frontend work possible without shelling out to CLI, reading
  SQLite, or duplicating battle logic
- keep CLI working as a regression harness

This is not a public deployment hardening task.
This is not mobile work.
This is not persona rendering.

## Source State

Completed prerequisites:

- Advisor CLI MVP is complete.
- P0a app-facing contract normalization is complete.
- P0b minimal agent-core extraction is complete.
- P0b audit returned:
  - verdict: `PASS`
  - P0c readiness: `ready_for_P0c`
- `agent_core.contracts.AgentResponse` is the app/API-facing response payload.
- `agent_core.orchestrator.AgentOrchestrator` can delegate to a runtime adapter.
- `agent_core.adapters.advisor.AdvisorRuntimeAdapter` wraps existing
  `advisor.runtime.AdvisorAgent`.

Latest reported validation:

- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 83 tests`, `OK`

## Required Work

### 1. Dependencies

Add API dependencies to `requirements.txt`:

- `fastapi`
- `uvicorn`
- `httpx` if needed for FastAPI/Starlette test client compatibility

Do not add frontend/mobile dependencies.

### 2. API module layout

Create a minimal API package, likely:

- `api/__init__.py`
- `api/main.py`
- `api/contracts.py`
- `api/dependencies.py`
- `api/services/advisor_service.py`
- route modules if useful

Keep it small.

Do not move Advisor runtime, battle engine, or battle-dex code.

### 3. Endpoints

Implement:

```text
GET  /health
GET  /metadata
POST /chat
POST /team/analyze
GET  /species/search
GET  /species/{species_id}
```

Expected behavior:

- `GET /health`
  - returns service status and schema/API version.
- `GET /metadata`
  - returns battle-dex/runtime metadata needed by clients.
  - must not leak local secret paths or provider keys.
- `POST /chat`
  - accepts a user message.
  - returns app-facing `AgentResponse`.
  - uses `AgentOrchestrator` + `AdvisorRuntimeAdapter`.
  - must work deterministically without live model key.
- `POST /team/analyze`
  - accepts team slots/types in API form.
  - returns app-facing `AgentResponse`.
  - may internally map to the existing Advisor message path if that is the
    thinnest safe bridge.
- `GET /species/search`
  - searches species through `BattleDexRepository`.
  - does not expose SQLite path.
- `GET /species/{species_id}`
  - returns species profile facts through repository/service layer.
  - response shape can be a dedicated API model, not `AgentResponse`, if clearer.

### 4. Session continuity contract

P0c must define how follow-up context works over HTTP.

Use a lightweight P0 approach:

- API accepts optional `session_id` for `/chat`.
- API returns `session_id`.
- server may keep an in-memory session-local AdvisorAgent per `session_id`.
- no durable persistence.
- no cross-device persistence.
- no formal runtime-level `message_history`.
- no raw provider API keys stored in session state.

This is enough for mobile/local frontend follow-up behavior while keeping full
session persistence deferred to P1.

### 5. Backend/provider policy

Default API behavior:

- deterministic backend must work without live model config.
- do not require user API key for `/chat`.
- do not log API keys.
- do not add hosted key management.

If provider config is accepted in request models, keep it behind an explicit
redacted interface and tests. Otherwise, document it as deferred.

Recommendation for P0c:

- default to deterministic or existing safe `auto` behavior based on local
  config.
- do not implement mobile user-key storage in this step.

### 6. Error handling and redaction

Add bounded error responses for:

- missing/invalid species.
- invalid team payload.
- missing battle-dex DB or bootstrap failure.
- runtime/provider failure.

Errors must not leak:

- API keys.
- provider config secrets.
- full local env file contents.

### 7. CORS and rate-limit placeholder

Add:

- minimal CORS config suitable for local/mobile development.
- a basic rate-limit hook or placeholder interface.

Do not build a full abuse-control system in P0c.

### 8. Tests

Add API tests covering:

- `GET /health`
- `GET /metadata`
- `POST /chat` deterministic flow without live model key
- `/chat` session continuity using `session_id`
- `POST /team/analyze`
- `GET /species/search`
- `GET /species/{species_id}`
- error/redaction behavior
- app-facing `AgentResponse` serialization for `/chat` and team analysis

Existing tests must still pass.

## Non-Goals

Do not:

- add mobile app
- add persona rendering
- add case retrieval
- add embeddings
- add web-in-loop
- add formal runtime-level `message_history`
- add durable cross-session persistence
- add hosted provider-key management
- add public deployment hardening beyond local API basics
- move deterministic analyzer code
- move battle-dex repository code
- rewrite `AdvisorAgent`
- change CLI output intentionally
- change backend policy unless explicitly needed for API configuration
- change data ingestion

## Required Validation

Run:

```bash
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

If API tests are in a separate file, run them explicitly as well.

## Expected Deliverable

Return:

1. files changed
2. API module layout
3. endpoint behavior summary
4. session continuity decision
5. provider/API-key handling decision
6. error/redaction behavior
7. tests added/updated
8. tests run and exact results
9. whether P0c is complete or blocked

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0c_fastapi_backend_request.md` first.

You are the main development thread. Implement P0c FastAPI Backend.

Expose the Advisor through a minimal FastAPI product service using `AgentResponse` and the existing `agent_core` boundary. Implement `GET /health`, `GET /metadata`, `POST /chat`, `POST /team/analyze`, `GET /species/search`, and `GET /species/{species_id}`. Use `AgentOrchestrator` + `AdvisorRuntimeAdapter` for chat/team analysis where appropriate. Add lightweight session continuity via optional `session_id` with in-memory session-local state only; do not add durable persistence or formal message_history.

Add FastAPI/uvicorn/httpx dependencies as needed. Add API tests for all endpoints, deterministic `/chat` without live model key, session continuity, species search/profile, error handling, redaction, and `AgentResponse` serialization.

Do not add mobile, persona rendering, case retrieval, embeddings, web-in-loop, durable cross-session persistence, hosted provider-key management, public deployment hardening beyond local API basics, deterministic analyzer moves, battle-dex moves, AdvisorAgent rewrites, intentional CLI output changes, data ingestion changes, or backend policy changes beyond API configuration plumbing.

Run `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return files changed, API layout, endpoint behavior summary, session continuity decision, provider/API-key handling decision, tests run, and whether P0c is complete or blocked.
```
