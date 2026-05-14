# Advisor Final MVP Readiness Check

## Purpose

This request is for a **test / product-audit thread**.

It is the final bounded dogfood check before the main thread decides whether to
declare the conversational Advisor CLI MVP complete.

This is not a feature request.
This is not a scope-expansion request.
This is not a crawler, GUI, RAG-platform, or architecture task.

## Source State

The main development thread reports that
`specs/advisor_mvp_tuning_request.md` is complete.

Latest reported validation:

- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 68 tests`, `OK`

Recently fixed findings:

- repeated native timeout pain under `--backend auto`
- generic future/live-meta refusal copy

Current approved runtime boundary:

- `--backend auto` is native-first, not native-only
- `auto` may fall back to deterministic for supported flows
- explicit `--backend pydantic_ai_native` must not silently fall back
- CLI remains session-local only
- no formal runtime-level `message_history`
- no case retrieval
- no embeddings
- no web-in-loop
- no GUI
- no data ingestion changes

## Required Audit

### 1. Regression tests

Run:

```bash
.venv/bin/python -m unittest discover -s tests
```

If this fails, return `FAIL` and stop.

### 2. Backend behavior

Test these paths:

- `--backend deterministic`
- `--backend auto` with missing env
- `--backend auto` with syntactically complete but unreachable native env
- explicit `--backend pydantic_ai_native` with missing env
- explicit `--backend pydantic_ai_native` with unreachable provider config
- valid local native env if already available locally

Do not put live keys in the repo.
Do not ask for live keys.

Expected:

- deterministic path works
- auto missing env falls back to deterministic
- auto native failure/timeout falls back to deterministic for supported flows
- repeated messages in the same auto session do not repeatedly pay long native
  timeout windows after native is marked unhealthy
- explicit native missing config exits/refuses cleanly
- explicit native provider failure/timeout returns bounded native failure/refusal

### 3. Product dogfood scenarios

Run at least these flows:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend deterministic \
  --message "/set-team 草 地 龙 翼 火 水" \
  --message "分析这队联防" \
  --message "/species 豆丁鱼" \
  --message "它适合干什么"
```

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "/set-team 草 地 龙 翼 火 水" \
  --message "分析这队联防" \
  --message "/species 豆丁鱼" \
  --message "它适合干什么"
```

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "帮我看看 草 地 龙 这队有洞吗"
```

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "/species 不存在的精灵"
```

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "帮我预测明天官方会不会加强豆丁鱼"
```

Expected:

- six-slot team analysis is useful and evidence-backed
- partial team input visibly carries a partial-team caveat
- species facts are SQL-backed where available
- semantic role judgement remains provisional
- unknown species refuses cleanly
- future/live-meta request explicitly says current MVP has no web/live official
  balance feed and cannot predict future buffs/nerfs or live meta changes
- doc/context evidence remains visible when retrieval ran
- no unsupported hard recommendation is made

### 4. Session state

Run one short same-process session:

1. `/set-team 草 地 龙 翼 火 水`
2. `分析这队联防`
3. `/species 豆丁鱼`
4. `它适合干什么`
5. `/clear`
6. `/show-team`
7. `它还适合干什么`

Expected:

- follow-up works before `/clear`
- `/clear` removes team and species context
- post-clear pronoun follow-up refuses or asks for context
- no cross-session persistence appears

### 5. Contract discipline

Check sampled outputs / raw objects if needed:

- tool statuses are only `ok`, `degraded`, `refused`, `failed`
- confirmed claims trace to Engine or SQL facts
- semantic claims are provisional
- unsupported claims are refused or downgraded
- no case retrieval, web retrieval, embeddings, GUI, or formal message history
  behavior appears

## Deliverable

Return:

1. `Verdict`
   - `PASS`
   - `PASS_WITH_FINDINGS`
   - `FAIL`
   - `BLOCKED`
2. `MVP readiness recommendation`
   - `ready_to_declare_mvp_complete`
   - `one_targeted_hardening_pass`
   - `blocked`
3. `Backend behavior`
4. `Product dogfood behavior`
5. `Findings`
   - severity
   - scenario
   - observed behavior
   - expected behavior
   - file reference if code-level
6. `Tests run`

Do not implement fixes unless the finding is a trivial test-harness issue.
Report implementation findings back to the main thread.

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_final_mvp_readiness_check.md` first.

You are the test / product-audit thread. Execute the final bounded MVP readiness dogfood check.

Do not expand scope. Do not add case retrieval, embeddings, web-in-loop, GUI, formal message_history, cross-session persistence, or data ingestion changes. Do not change backend policy.

Run the required regression tests, backend behavior checks, product dogfood scenarios, session-state checks, and contract discipline checks.

Return verdict, MVP readiness recommendation, backend behavior, product dogfood behavior, findings with severity, and exact tests run.
```
