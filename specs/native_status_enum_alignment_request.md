# Native Status Enum Alignment Request

## Purpose

This request is for the **main development thread**.

It addresses QA-1's native failure-path audit finding:

- runtime failure/refusal paths emit `ToolStatus.UNAVAILABLE`
- advisor response contract permits only `ok`, `degraded`, `refused`, `failed`

This is a bounded code/spec alignment task.

Do not expand MVP scope.

## Current Problem

Spec:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_response_contract.yaml`
- allowed `tool_results.status` enum:
  - `ok`
  - `degraded`
  - `refused`
  - `failed`

Code:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/contracts.py`
- current `ToolStatus` enum:
  - `ok`
  - `degraded`
  - `unavailable`

Runtime:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- native refusal/unavailable paths currently emit `ToolStatus.UNAVAILABLE`

QA-1 impact:

- failure paths are bounded
- but typed response status is not contract-clean enough for native-default
  promotion

## Required Decision

Use the spec enum as source of truth.

Target status semantics:

- `ok`: tool completed successfully
- `degraded`: tool completed with partial/low-confidence result
- `refused`: tool did not run or returned no result because the request is
  unsupported, missing required input, or entity was not found
- `failed`: tool attempted execution and encountered a runtime/provider/system
  failure

Do not preserve `unavailable` in final serialized advisor responses.

## Required Work

1. Update `ToolStatus`
   - add/align enum values with the response contract:
     - `OK = "ok"`
     - `DEGRADED = "degraded"`
     - `REFUSED = "refused"`
     - `FAILED = "failed"`

2. Replace current `ToolStatus.UNAVAILABLE` usages
   - missing repository / missing query / unknown species should generally be
     `REFUSED`
   - actual runtime/tool exceptions should be `FAILED`
   - if a path can safely return partial content, use `DEGRADED`

3. Update validator/helper logic
   - unknown species clean refusal must still pass native validation
   - explicit native failure must remain bounded
   - auto fallback behavior must remain unchanged

4. Update tests
   - assert no serialized `tool_results.status` equals `unavailable`
   - assert unknown species uses `refused`
   - assert missing repository/refusal paths use contract-compatible status
   - preserve existing native failure-path tests

5. Update docs/log if behavior wording changes

## Non-goals

Do not:

- add case retrieval
- add web-in-loop
- add GUI
- add formal runtime-level `message_history`
- change backend default policy
- redesign response schema
- change data ingestion
- implement profile-only partial native answer for tool partial failure

The P3 coarse partial-failure quality note is deferred.

## Validation

Minimum:

```bash
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

If adding focused contract tests:

```bash
.venv/bin/python -m unittest tests.test_advisor_response_contract
```

## Expected Deliverable

Return:

1. files changed
2. status mapping decisions
3. tests added/updated
4. tests run and exact results
5. whether native default readiness is now ready for main-thread decision

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/native_status_enum_alignment_request.md` first.

You are the main development thread. Fix QA-1's response status enum drift.

Use `specs/advisor_response_contract.yaml` as source of truth: allowed tool status values are `ok`, `degraded`, `refused`, `failed`. Replace runtime/code usage of `unavailable` with contract-compatible statuses. Preserve clean unknown-species refusal, explicit native bounded failure, and auto fallback behavior.

Do not expand scope. Do not add case retrieval, web-in-loop, GUI, formal message_history, backend policy changes, or data ingestion changes.

Run required tests, update `log/project_log.md` with execution facts, and report whether native default readiness is now ready for main-thread decision.
```
