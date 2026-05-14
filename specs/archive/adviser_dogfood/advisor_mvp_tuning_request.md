# Advisor MVP Tuning Request

## Purpose

This request is for the **main development thread**.

It converts the second dogfood audit findings into a bounded prompt/runtime
tuning task.

This is not a scope-expansion request.

## Source

Second dogfood audit verdict:

- `PASS_WITH_FINDINGS`

Recommended next action:

- `prompt/runtime tuning`

## Accepted Findings

### P2. Native-backed auto can create long user-visible stalls before fallback

Scenario:

- `--backend auto` with valid local native config

Observed:

- native path was selected
- sampled native call timed out
- deterministic fallback worked
- but each native-routed message waited for the timeout window first
- a multi-message session can therefore accumulate long user-visible stalls

Expected:

- safe fallback already exists
- MVP UX should not repeatedly spend long timeout windows before returning a
  deterministic answer when native is unhealthy

Follow-up type:

- runtime tuning

### P3. Unsupported future / meta request refusal is safe but generic

Scenario:

- user asks future/live-meta question such as:
  - `帮我预测明天官方会不会加强豆丁鱼`

Observed:

- CLI refused safely using a generic MVP scope message

Expected:

- still refuse
- but explicitly state that live official-balance prediction / web/meta
  information is not available in the current MVP

Follow-up type:

- copy/runtime tuning

## Required Work

### 1. Reduce repeated native timeout pain under `auto`

Implement one small local mechanism that avoids repeated long stalls after a
native runtime failure within the same CLI process.

Acceptable options:

- session-local native health flag after timeout/failure
- short cooldown after native failure
- preflight/health gate before routing subsequent `auto` messages to native

Requirements:

- `auto` remains native-first when native appears healthy
- after native failure/timeout, subsequent messages in the same process should
  avoid repeated long native timeout windows
- deterministic fallback must remain available for supported flows
- explicit `--backend pydantic_ai_native` must still attempt native and return
  bounded native failure/refusal; it must not silently fall back

Do not:

- add cross-session persistence
- add background health checks
- add long-term memory
- add external monitoring
- add new tools

### 2. Improve unsupported future/meta refusal copy

When user asks for unsupported future/live/meta prediction, the response should
clearly say:

- current MVP has no web/live official balance feed
- current MVP cannot predict future buffs/nerfs or live meta changes
- supported nearby actions are:
  - analyze current team structure
  - query battle-dex facts
  - discuss provisional species role from current facts

Do not add web search.

## Files Likely In Scope

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/conversation_cli_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

## Required Tests

Add or update tests for:

- `auto` native timeout/failure marks native unhealthy for the current process
  or otherwise avoids repeated timeout windows
- subsequent supported request under `auto` returns deterministic fallback
  without another native timeout attempt
- explicit `pydantic_ai_native` still returns bounded native failure/refusal
- unsupported future/meta request returns specific no-live-meta/no-web refusal

Minimum validation:

```bash
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest discover -s tests
```

## Non-goals

Do not:

- add case retrieval
- add embeddings
- add web-in-loop
- add GUI
- add formal runtime-level `message_history`
- add cross-session persistence
- change data ingestion
- change battle-dex schema
- make hard species recommendations

## Expected Deliverable

Return:

1. files changed
2. behavior changes by finding
3. tests added/updated
4. tests run and exact results
5. whether Advisor CLI is ready for final MVP readiness dogfood/check

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_mvp_tuning_request.md` first.

You are the main development thread. Execute this bounded prompt/runtime tuning request from the second dogfood audit.

Fix:
1. Reduce repeated native timeout pain under `--backend auto` within the same CLI process.
2. Improve unsupported future/live-meta refusal copy so it explicitly says current MVP has no web/live official balance feed and cannot predict future buffs/nerfs or live meta changes.

Do not expand scope. Do not add case retrieval, embeddings, web-in-loop, GUI, formal message_history, cross-session persistence, or data ingestion changes. Explicit `--backend pydantic_ai_native` must still not silently fall back.

Add/update tests, run required tests, and update `log/project_log.md` with execution facts.

Return files changed, behavior changes, tests run, and whether Advisor CLI is ready for final MVP readiness dogfood/check.
```
