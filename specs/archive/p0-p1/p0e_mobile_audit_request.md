# P0e Mobile MVP Scaffold Audit Request

## Purpose

Audit the completed P0e mobile scaffold before P0f public-release hardening or
any post-P0 feature expansion begins.

This is a verification task. Do not expand scope.

## Context

P0e implementation reported:

- `mobile/` Expo + React Native + TypeScript workspace created
- screens:
  - chat
  - team editor
  - species search
  - settings
  - response/evidence inspection panel
- Product API endpoints wired:
  - `GET /health`
  - `GET /metadata`
  - `POST /chat`
  - `POST /team/analyze`
  - `GET /species/search`
  - `GET /species/{species_id}`
- mobile uses typed API client and treats `AgentResponse` as the contract
- no CLI shell-out
- no SQLite access
- no provider calls
- no provider-key input/storage
- no duplicated battle logic or species DB logic
- no official IP assets or official-positioning text

## Audit Scope

### 1. API-boundary correctness

Verify mobile only talks to the Product API and does not:

- import Python modules
- read SQLite files
- call CLI commands
- call model providers directly
- recreate deterministic battle logic locally
- recreate species DB access locally

### 2. Contract correctness

Verify the mobile client is typed against the current API/`AgentResponse`
contract and can safely render:

- base `answer`
- `persona.rendered_answer`, when present
- evidence items
- confidence notes
- tool results at compact/debug level

### 3. Screen scope correctness

Verify the implemented screens match bounded P0e scope:

- chat
- team editor
- species search
- settings for local API base URL
- evidence/response inspection

No hidden extra scope such as:

- authentication
- payments
- push notifications
- durable persistence
- provider-key management
- public release infra

### 4. IP/product safety

Verify mobile bundle/source does not include:

- official Enzo/恩佐 persona
- official screenshots
- official art
- official icons/logos
- official dialogue imitation
- wording implying Tencent, 洛克王国, Roco Kingdom, or official authorization

### 5. Validation quality

Verify reported validation is real and sufficient:

- mobile install/typecheck commands
- backend regression commands
- any static boundary checks

If mobile lacks lint/test scripts, that is acceptable for P0e, but record it
plainly.

### 6. Local-run usability

Verify the scaffold can be reasonably run in local development and the run
instructions are coherent:

- backend local uvicorn
- Expo local start
- API base URL handling for simulator/emulator/device

## Non-Goals

Do not add or request:

- public deployment hardening
- Docker/infra
- provider-key management
- hosted key management
- durable persistence
- cross-device persistence
- case retrieval
- embeddings
- web-in-loop
- crawler/database changes
- LLM persona rewriting
- official assets
- CLI/runtime rewrites

## Required Checks

Run:

```bash
cd /Users/okfin3/project/GitHub/OKFin33/Roco/mobile && npm run typecheck
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

Add bounded source inspection checks for:

- Python imports from mobile
- SQLite/path access from mobile
- provider key fields/storage from mobile
- official-IP strings in mobile source

## Deliverable

Return:

- verdict: `PASS` | `PASS_WITH_FINDINGS` | `FAIL` | `BLOCKED`
- P0f readiness: `ready_for_P0f_hardening` |
  `needs_targeted_mobile_refactor` | `blocked`
- API-boundary judgement
- contract/render judgement
- screen-scope judgement
- IP/product-safety judgement
- validation judgement
- local-run judgement
- findings with severity and file references
- exact commands run and results

## Copy-Paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0e_mobile_audit_request.md` first.

You are the test / architecture-audit thread. Audit the completed P0e Mobile MVP Scaffold before P0f public-release hardening or any post-P0 feature expansion begins.

Focus on API-boundary correctness, `AgentResponse` contract/render correctness, screen-scope correctness, IP/product safety, validation quality, and local-run usability.

Do not add public deployment hardening, Docker/infra, provider-key management, hosted key management, durable persistence, case retrieval, embeddings, web-in-loop, crawler/database changes, LLM persona rewriting, official assets, or CLI/runtime rewrites.

Run `cd /Users/okfin3/project/GitHub/OKFin33/Roco/mobile && npm run typecheck`, `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Add bounded source inspection for Python imports, SQLite access, provider-key fields/storage, and official-IP strings in `mobile/`.

Return verdict, P0f readiness, API-boundary/contract-render/screen-scope/IP-safety/validation/local-run judgements, findings with severity and file references, and exact commands/results.
```
