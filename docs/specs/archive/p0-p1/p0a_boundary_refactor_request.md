# P0a Boundary Refactor Request

## Purpose

This request is for the **main development thread**.

It addresses the P0a architecture audit finding before P0b minimal agent-core
extraction begins.

This is a boundary cleanup task.
It must not change runtime behavior, CLI output, backend policy, or product
scope.

## Source

P0a contract audit result:

- verdict: `PASS_WITH_FINDINGS`
- P0b readiness: `conditional_not_ready_until_boundary_refactor`
- boundary judgement: `refactor_before_P0b`

Blocking finding:

- `agent_core/contracts.py` imports `advisor.contracts`
- adapter logic lives in the same module as pure product-facing contracts

Audit decision:

- acceptable as a P0a bridge
- not acceptable as the foundation for P0b extraction

## Required Work

### 1. Keep pure contracts pure

Refactor:

- `agent_core/contracts.py`

So that it contains only app/API-facing product models and product enums.

It must not import:

- `advisor.contracts`
- `advisor.runtime`
- `advisor.battle_dex`
- CLI/runtime-specific modules

Allowed imports include:

- standard library typing / enum
- Pydantic
- shared reporting contracts if needed for confidence enum reuse

### 2. Move Advisor adapter logic

Create an adapter module such as:

- `agent_core/adapters/__init__.py`
- `agent_core/adapters/advisor.py`

Move Advisor-specific imports and functions there:

- `agent_response_from_advisor`
- Advisor-specific evidence conversion
- Advisor-specific status inference
- Advisor-specific analysis type inference
- Advisor-specific confidence-note inference

Advisor adapter may import:

- `advisor.contracts`
- `agent_core.contracts`

### 3. Preserve compatibility imports if needed

If existing tests or downstream code import:

- `agent_core.contracts.agent_response_from_advisor`
- `AgentResponse.from_advisor_response`

Prefer updating tests/imports to the new adapter path.

If keeping compatibility shims, they must not reintroduce Advisor imports into
`agent_core/contracts.py`.

Recommendation:

- remove `AgentResponse.from_advisor_response` from pure model if it requires
  Advisor imports.
- use `agent_core.adapters.advisor.agent_response_from_advisor` instead.

### 4. Tighten tests

Add or update tests to assert:

- `agent_core.contracts` can import without importing `advisor.contracts`
- adapter imports live under `agent_core.adapters.advisor`
- contract shape remains unchanged
- adapter behavior remains unchanged
- evidence refs still resolve to top-level evidence IDs
- CLI behavior remains unchanged

### 5. Preserve P0a behavior

No behavior changes are intended.

Validation:

```bash
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Non-Goals

Do not:

- add P0b orchestrator extraction
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
- improve evidence attribution precision beyond preserving current behavior

## Expected Deliverable

Return:

1. files changed
2. boundary refactor summary
3. import boundary proof
4. adapter path after refactor
5. behavior compatibility notes
6. tests added/updated
7. tests run and exact results
8. whether P0b is ready for main-thread scheduling

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0a_boundary_refactor_request.md` first.

You are the main development thread. Execute the P0a boundary refactor required before P0b.

Refactor `agent_core/contracts.py` so it contains only pure app/API-facing models and product enums, with no imports from `advisor.*`. Move Advisor-specific adapter logic into `agent_core/adapters/advisor.py` or an equivalent adapter module. Preserve current app-facing contract shape, adapter behavior, evidence_refs behavior, CLI behavior, and backend policy.

Add/update tests proving `agent_core.contracts` does not import `advisor.contracts`, adapter imports live under `agent_core.adapters.advisor`, contract JSON shape remains stable, and all existing advisor tests still pass.

Do not add P0b orchestrator extraction, FastAPI, mobile, persona rendering, case retrieval, embeddings, web-in-loop, formal message_history, cross-session persistence, data ingestion changes, backend policy changes, intentional CLI output changes, or evidence attribution redesign.

Run `.venv/bin/python -m unittest tests.test_agent_core_contracts`, `.venv/bin/python -m unittest tests.test_advisor`, and `.venv/bin/python -m unittest discover -s tests`.

Return files changed, boundary refactor summary, import boundary proof, adapter path, behavior compatibility notes, tests run, and whether P0b is ready for main-thread scheduling.
```
