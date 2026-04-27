# P0f Public-Release Hardening Request

## Purpose

Implement the first bounded hardening pass that makes the current Roco advisor
stack operable and safer for local/public-prep use.

This is not a cloud deployment project. It is a release-hardening pass over the
existing Python API, advisor runtime, and mobile scaffold boundaries.

## Context

Completed prerequisites:

- P0a App-Facing Contract Normalization
- P0b Minimal Agent Core Extraction
- P0c FastAPI Backend and audit
- P0d Persona V1 + IP Guard and audit
- P0e Mobile MVP Scaffold and audit

P0e audit returned:

- verdict: `PASS`
- P0f readiness: `ready_for_P0f_hardening`

## Required Scope

Implement a bounded hardening pass covering:

### 1. Local run path

Provide a clean documented local run path for:

- backend API
- mobile app

This may include:

- lightweight helper scripts
- startup docs
- environment examples without secrets

Do not require live provider keys to boot the deterministic path.

### 2. Config hygiene

Add or tighten:

- `.env.example` or equivalent safe sample config
- explicit separation between safe sample config and real local secrets
- config validation for expected fields where needed
- no secret values in repo

### 3. Health / version / metadata

Ensure release-facing inspection endpoints are coherent and documented:

- `/health`
- `/metadata`

If a small version endpoint improvement is needed and fits current API shape,
implement it in a bounded way. Do not redesign the API.

### 4. Logging / redaction

Tighten logs and error handling so that:

- provider keys are never logged
- env file contents are never logged
- local DB paths are not leaked in user-facing errors
- unexpected failures remain bounded

Structured logging is allowed if kept small and local. Do not build a full
observability platform.

### 5. Timeout / provider failure hardening

Keep current bounded behavior intact and add tests where useful for:

- unreachable native provider
- timeout path
- deterministic fallback where approved
- explicit native bounded failure where approved

Do not change backend policy unless a bug forces a minimal correction.

### 6. Rate-limit / abuse-control placeholder hygiene

Current API has a placeholder. Make sure it is explicitly documented as a
placeholder and does not pretend to be production abuse control.

### 7. Public disclaimer copy

Add or tighten plain product copy stating:

- unofficial tool
- no official authorization
- no official character/art asset affiliation

Keep the wording neutral and product-safe.

## Non-Goals

Do not add:

- hosted deployment stack
- cloud infra
- authentication
- payments
- provider-key management platform
- durable persistence
- cross-device sync
- case retrieval
- embeddings
- web-in-loop
- crawler/database expansion
- redesign of battle engine
- mobile feature expansion beyond minor release-hardening adjustments

Do not rewrite:

- `AdvisorAgent`
- battle-dex repository
- deterministic analyzer
- mobile architecture

## Acceptance Criteria

The result must demonstrate:

- clean local run instructions from repo docs
- safe sample env/config exists if needed
- no real secrets committed
- user-facing/log-facing errors stay redacted
- deterministic local path works without live provider key
- current tests stay green
- any new hardening tests pass
- disclaimer/unofficial positioning is present and not misleading

Required validation:

```bash
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

If you add hardening-specific tests, include them explicitly.

If you add Node/mobile validation changes, run them only if the touched area
requires it.

## Deliverable

Return:

- files changed
- hardening areas implemented
- exact docs/config/logging/error-handling changes
- whether `.env.example` or equivalent was added/updated
- exact test commands/results
- any known remaining non-goal gaps intentionally left for later

## Copy-Paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0f_public_release_hardening_request.md` first.

You are the main development thread. Implement P0f Public-Release Hardening under the bounded scope in that spec.

Focus on local run path, safe sample config, health/metadata/version coherence, logging/redaction, bounded timeout/provider failure hardening, rate-limit placeholder hygiene, and unofficial/public-safe disclaimer copy.

Do not add hosted deployment stack, cloud infra, authentication, payments, provider-key management platform, durable persistence, cross-device sync, case retrieval, embeddings, web-in-loop, crawler/database expansion, battle-engine redesign, or mobile feature expansion beyond minor release-hardening adjustments.

Run `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`. Add hardening-specific tests if needed and report them explicitly.

Return files changed, hardening areas implemented, exact docs/config/logging/error-handling changes, whether `.env.example` or equivalent was added/updated, exact test results, and any intentional remaining non-goal gaps.
```
