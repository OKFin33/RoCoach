# Runtime Hygiene Follow-up Handoff

## Purpose

This handoff is for a separate **implementation / test thread**.

Its job is to clean up runtime hygiene issues and rerun native-runtime parity
checks after the main thread's native hardening patch.

This is not a product-design thread.
This is not a scope-expansion thread.

## Thread Role

The new thread should be positioned as:

- `runtime hygiene implementation worker`
- `native parity / failure-path test worker`
- verification-focused
- implementation-focused only when needed to remove confirmed runtime defects

It must not decide whether `pydantic_ai_native` becomes the default CLI backend.
That decision stays with the main thread.

## Minimal Project Context

Project:

- Roco battle advisor MVP
- repository root: `/Users/okfin3/project/GitHub/OKFin33/Roco`

Current implementation reality:

- conversational advisor CLI exists at:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
- runtime has two paths:
  - `deterministic`
  - `pydantic_ai_native`
- battle-dex retrieval exists at:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/battle_dex.py`
- advisor runtime exists at:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- current live MVP tools are:
  - `analyze_team_structure`
  - `get_species_profile`
  - `get_species_available_moves`
  - `retrieve_doc_context`
  - `analyze_species_semantics`

Approved constraints:

- deterministic Engine / SQL facts are the only source allowed to produce
  `confirmed`
- semantic species/team judgement defaults to `provisional`
- insufficient evidence must downgrade or refuse
- no formal `message_history` runtime state
- no case retrieval in current MVP live tool set
- no web-in-loop
- no cross-session persistence

## Current Main-thread Status

The previous audit reported `CODE DRIFT`.

Main thread has already applied a code-only hardening patch:

- native unknown-species handling now permits typed refusal
- native provider/runtime exceptions are wrapped into bounded advisor responses
- `BattleDexRepository` was changed away from a shared SQLite connection
- native species evidence now includes ability evidence
- native team confidence notes now include the provisional dual-type warning

Validation after that patch:

- targeted advisor tests: `Ran 11 tests`, `OK`
- full suite: `Ran 49 tests`, `OK`

Residual issue:

- full suite still emitted multiple `sqlite3 ResourceWarning` warnings
- the source of those warnings has not been isolated
- this must be fixed before the main thread considers making
  `pydantic_ai_native` the default CLI backend

## Task Allocation

### 1. `sqlite3 ResourceWarning`定位与修复

适合：实现线程 / 测试线程

不适合：主线程

原因：

- 这是低层 runtime hygiene
- 需要跑 warning-as-error、tracemalloc、逐个 callsite 排查
- 主线程继续手修会污染架构上下文

Required work:

- reproduce the ResourceWarning deterministically
- use `-W error::ResourceWarning` and/or `tracemalloc` to identify the exact
  callsite
- fix the leaking SQLite connection(s)
- do not silence warnings globally
- do not use warning filters as the fix
- add or adjust tests only as needed to prevent regression

Recommended commands:

```bash
PYTHONTRACEMALLOC=25 .venv/bin/python -W error::ResourceWarning -m unittest discover -s tests
PYTHONTRACEMALLOC=25 .venv/bin/python -W default::ResourceWarning -m unittest discover -s tests
```

If the warning only appears under system `python3`, also run:

```bash
PYTHONTRACEMALLOC=25 python3 -W error::ResourceWarning -m unittest discover -s tests
PYTHONTRACEMALLOC=25 python3 -W default::ResourceWarning -m unittest discover -s tests
```

### 2. Native parity / failure-path rerun

适合：测试线程

不适合：主线程

原因：

- 这是 verification，不是设计
- 独立线程视角更有审查价值
- 主线程自己测自己可信度更低

Required checks:

- unknown species returns clean typed refusal
- invalid native provider/runtime failure returns bounded advisor response
- repository supports native-style concurrent lookup
- native species response includes SQL-backed ability evidence when available
- native team response includes:
  - confirmed deterministic-engine note
  - provisional dual-type-baseline note
- deterministic/native output shape remains aligned for:
  - team analysis
  - species query
  - same-session follow-up

### 3. Native default backend decision

适合：主线程拍板

不适合：实现线程自行决定

Reason:

- making `pydantic_ai_native` the default CLI backend is a product/runtime
  strategy decision
- implementation/test thread must report readiness only
- do not change CLI default backend in this task

### 4. Docs / log updates

执行事实：

- implementation/test thread may update
  `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

决策变更：

- only main thread should update specs/logs for product/runtime strategy

## Files To Read First

Read these first:

1. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/native_runtime_audit_handoff.md`
2. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
3. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_response_contract.yaml`
4. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md`
5. `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Then inspect:

6. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
7. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/battle_dex.py`
8. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
9. `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`

## Hard Rules

Do not:

- expand MVP tool scope
- add case retrieval
- add web-in-loop
- add cross-session persistence
- promote `message_history` into formal session state
- store live API keys in the repo
- make `pydantic_ai_native` the default backend
- silence ResourceWarning without fixing the leak
- redesign architecture

## Expected Deliverable

Return:

1. `Verdict`
   - `FIXED`
   - `PARTIAL`
   - `BLOCKED`

2. `ResourceWarning result`
   - callsite found
   - files changed
   - whether warning-as-error now passes

3. `Parity / failure-path result`
   - pass/fail for each required check

4. `Tests run`
   - exact commands
   - exact results

5. `Native default readiness`
   - `ready_for_main_thread_decision`
   - `not_ready`
   - this is only a readiness report, not a decision

## Copy-Paste Prompt For New Thread

Use this prompt in the new thread:

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/runtime_hygiene_followup_handoff.md` first.

You are a runtime hygiene implementation / test worker for the Roco advisor MVP.
Do not redesign architecture. Do not expand MVP scope. Your task is:

1. Locate and fix the remaining `sqlite3 ResourceWarning` shown by full tests after native runtime hardening.
2. Rerun native parity and failure-path validation.
3. Report whether the runtime is ready for the main thread to decide on making `pydantic_ai_native` the default CLI backend.

You may update code/tests and log execution facts. You must not change product strategy specs, add case retrieval, add web-in-loop, add message_history state, or make native the default backend.

Return only: verdict, ResourceWarning result, parity/failure-path result, tests run, and native default readiness.
```
