# Advisor Dogfood Hardening Request

## Purpose

This request is for the **main development thread**.

It converts the dogfood audit findings into a bounded code-hardening task.

Do not expand product scope.
Do not redesign architecture.
Do not touch crawler / database ingestion.

## Context

Dogfood audit verdict:

- `PASS_WITH_FINDINGS`

Current CLI backend policy:

- `--backend auto` should prefer native only when native runtime is usable
- otherwise it should preserve deterministic local usability

Current MVP boundary:

- team conversational structure analysis
- species discussion backed by battle-dex facts
- bounded approved doc evidence
- session-local follow-up

Deferred / forbidden in this task:

- case retrieval
- web-in-loop
- GUI
- long-term memory
- formal runtime-level `message_history`
- new data ingestion
- making hard species-role recommendations

## Required Fixes

### P1. Auto backend should fall back on native runtime failure

Finding:

- `--backend auto` with syntactically complete but unreachable native config
  selected `pydantic_ai_native`
- runtime returned bounded native failure, but did not fall back to deterministic

Expected:

- `auto` means native-first, not native-only
- if native runtime/provider fails, auto should return deterministic response
  for supported deterministic/species flows
- explicit `--backend pydantic_ai_native` should keep bounded native failure
  behavior and must not silently fall back

Suggested implementation direction:

- runtime/config should preserve whether backend was selected by `auto`
- native failure fallback should be enabled only for `auto`, not explicit native

### P1. Native provider calls need bounded no-hang behavior

Finding:

- local valid native env selected `pydantic_ai_native`
- CLI smoke test produced no output after ~30s and had to be killed

Expected:

- native calls must either return useful output or degrade/refuse within a
  bounded time
- no CLI command should hang indefinitely

Suggested implementation direction:

- add bounded timeout around native runtime execution
- on timeout:
  - in `auto`, fall back to deterministic when possible
  - in explicit native, return bounded advisor response

### P2. Incomplete team input needs caveat / downgrade

Finding:

- input like `帮我看看 草 地 龙 这队有洞吗` was parsed as 3 slots and analyzed
  as a normal confirmed team structure

Expected:

- because product goal is six-slot team analysis, incomplete teams should be
  explicitly caveated
- acceptable behavior:
  - warn that this is a partial-team structure analysis
  - downgrade or caveat interpretation
  - ask for missing slots in follow-up options

Do not reject partial-team analysis entirely unless implementation proves that
is simpler and cleaner.

### P3. CLI renderer should expose doc evidence when retrieval ran

Finding:

- `retrieve_doc_context` retrieved snippets
- CLI renderer displays only first six evidence items
- engine facts consume the visible evidence slots, hiding approved doc evidence

Expected:

- rendered CLI output should expose at least one doc / confidence-policy snippet
  when doc retrieval was performed
- do not dump all evidence
- keep output readable

## Files Likely In Scope

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/conversation_cli_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Do not edit data pipeline files unless a direct test failure proves they are
involved.

## Validation Requirements

Minimum:

```bash
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

Required new/updated tests:

- auto native provider failure falls back to deterministic
- explicit native provider failure still returns bounded native failure
- native timeout is bounded
- partial team input includes a visible caveat or follow-up for missing slots
- rendered CLI evidence includes at least one doc item when doc retrieval ran

## Expected Deliverable

Return:

1. files changed
2. behavior changes by finding
3. tests run and exact results
4. whether dogfood findings are now fixed / partially fixed / blocked

## Copy-paste Prompt For Main Development Thread

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_dogfood_hardening_request.md` first.

You are the main development thread. Execute exactly this bounded hardening request from the dogfood audit.

Fix:
1. auto backend fallback on native runtime/provider failure
2. bounded no-hang behavior for native provider calls
3. explicit partial-team caveat / missing-slot follow-up
4. CLI evidence rendering so doc evidence is visible when retrieval ran

Do not expand MVP scope. Do not add case retrieval, web-in-loop, GUI, formal message_history, or ingestion changes. Explicit --backend pydantic_ai_native must not silently fall back to deterministic.

Run the required tests and update `log/project_log.md` with execution facts.

Return files changed, behavior changes, tests run, and whether dogfood findings are fixed.
```
