# P0e Mobile MVP Scaffold Request

## Purpose

Create the first mobile app scaffold for the Roco advisor product.

This is a bounded mobile shell task. It should prove that the product API and
`AgentResponse` contract are usable from a mobile client without duplicating
advisor logic.

## Context

Completed prerequisites:

- P0a App-Facing Contract Normalization
- P0b Minimal Agent Core Extraction
- P0c FastAPI Backend and API audit
- P0d Persona V1 + IP Guard and audit

P0d audit returned:

- verdict: `PASS`
- mobile readiness: `ready_for_P0e_mobile_scaffold`

## Required Stack

Use:

- React Native
- Expo
- TypeScript

Do not switch to a different frontend/mobile stack without main-thread
approval.

## Required Scope

Create a `mobile/` workspace that contains:

- `package.json`
- Expo app config
- TypeScript config
- source layout under `mobile/src/`
- API client wrapper for the existing FastAPI backend
- typed client-side representation of `AgentResponse`
- minimal navigation or screen switching

Initial screens:

- chat screen
- team editor screen
- species search screen
- evidence drawer or evidence panel
- settings screen for local API base URL

The app should target local development first.

## API Contract Boundary

Mobile must call the existing Product API:

- `GET /health`
- `GET /metadata`
- `POST /chat`
- `POST /team/analyze`
- `GET /species/search`
- `GET /species/{species_id}`

Mobile must not:

- shell out to CLI
- read SQLite directly
- call LLM providers directly
- duplicate deterministic battle logic
- duplicate species database logic
- accept or store provider API keys in P0e

`AgentResponse` should be treated as the primary response contract.

## UX Requirements

Keep the UI minimal but usable:

- user can configure local API base URL
- user can send a chat message
- user can enter a team and request team analysis
- user can search species
- user can inspect:
  - base `answer`
  - `persona.rendered_answer`, when present
  - evidence items
  - confidence notes
  - tool results at a compact/debug level
- error states are visible and recoverable

No visual polish sprint is required. Do not spend P0e on brand identity, art, or
animation.

## Persona/IP Boundary

Mobile may display persona metadata returned by the API.

Mobile must not bundle:

- official Enzo/恩佐 persona
- official art
- official screenshots
- official icons/logos
- official dialogue imitation
- wording that implies Tencent, Roco Kingdom, 洛克王国, or official
  authorization

Use plain UI text and the API-provided public-safe persona metadata.

## Non-Goals

Do not add:

- public deployment hardening
- Docker/infra
- backend changes except tiny CORS/API typing fixes if absolutely required
- durable session persistence
- cross-device persistence
- provider-key management
- hosted key management
- push notifications
- authentication
- payments
- case retrieval
- embeddings
- web-in-loop
- crawler/database changes
- LLM persona rewriting
- official assets

Do not rewrite:

- FastAPI backend
- `AdvisorAgent`
- deterministic analyzer
- battle-dex repository

## Acceptance Criteria

The implementation must demonstrate:

- mobile scaffold exists under `mobile/`
- TypeScript typecheck passes, if the scaffold defines a typecheck command
- basic mobile tests/lint pass, if the scaffold defines them
- API client can serialize requests matching existing API contracts
- mobile UI does not import Python files, SQLite files, or generated data files
- mobile UI has no official Enzo/恩佐/Tencent/洛克王国 official-positioning text
- existing Python backend/advisor tests still pass

Required backend regression:

```bash
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

Required mobile validation:

- run the mobile package manager install only if needed
- run the scaffold's typecheck/test/lint scripts if present
- if a script cannot run because dependencies are missing, report the exact
  blocker and do not fake success

## Deliverable

Return:

- files changed
- created mobile layout
- supported screens
- API endpoints wired
- validation commands and exact results
- any local run instructions
- confirmation that mobile does not duplicate backend logic or bundle official
  IP assets

## Copy-Paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0e_mobile_mvp_scaffold_request.md` first.

You are the main development thread. Implement P0e Mobile MVP Scaffold under the bounded scope in that spec.

Use React Native + Expo + TypeScript. Create a `mobile/` workspace with a minimal but usable local-development app: chat screen, team editor screen, species search screen, evidence drawer/panel, settings screen for local API base URL, and typed API client for the existing FastAPI backend.

Mobile must call the Product API and treat `AgentResponse` as the response contract. Do not shell out to CLI, read SQLite, call LLM providers directly, duplicate battle logic, duplicate species DB logic, or accept/store provider API keys in P0e.

Do not add public deployment hardening, Docker/infra, durable persistence, cross-device persistence, provider-key management, hosted key management, authentication, payments, case retrieval, embeddings, web-in-loop, crawler/database changes, LLM persona rewriting, official assets, official Enzo/恩佐 persona, official screenshots, or official-authorization positioning.

Run backend regression: `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Run mobile typecheck/test/lint scripts if present. If mobile dependencies are missing, install only what the scaffold needs and report exact commands/results. Do not fake validation.

Return files changed, created mobile layout, supported screens, API endpoints wired, validation commands/results, local run instructions, and confirmation that mobile does not duplicate backend logic or bundle official IP assets.
```
