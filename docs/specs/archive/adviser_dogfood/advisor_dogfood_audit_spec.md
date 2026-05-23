# Advisor Dogfood Audit Spec

## Purpose

Dogfood audit means using the current advisor MVP like a real user would, then
judging whether the product behavior is useful, grounded, and safe.

This is not unit testing.
This is not architecture redesign.
This is not feature expansion.

The audit should stress the conversational CLI with realistic Roco battle
advisor questions and report where the current MVP feels weak, misleading,
under-explained, or operationally brittle.

## Thread Role

Run this in a separate **test / product-audit thread**.

The thread should behave like:

- test operator
- product QA
- contract auditor

It should not behave like:

- feature designer
- framework selector
- data pipeline owner
- crawler implementer

## Current MVP Reality

Current repo root:

- `/Users/okfin3/project/GitHub/OKFin33/Roco`

Current advisor state:

- conversational CLI exists:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
- CLI backend policy is `auto`
  - valid native env config -> `pydantic_ai_native`
  - missing/invalid native env config -> `deterministic`
  - explicit backend flags still override
- runtime paths:
  - `deterministic`
  - `pydantic_ai_native`
- SQLite battle-dex retrieval exists
- bounded local doc retrieval exists
- no embeddings yet
- no case retrieval yet
- no web-in-loop
- no formal runtime-level `message_history`

Current live MVP tools:

- `analyze_team_structure`
- `get_species_profile`
- `get_species_available_moves`
- `retrieve_doc_context`
- `analyze_species_semantics`

## Approved Product Boundary

Allowed MVP behavior:

- team conversational structure analysis
- species discussion backed by battle-dex facts
- approved doc evidence
- follow-up context within one local session
- provisional semantic role discussion when evidence is bounded and uncertainty
  is explicit

Forbidden in this audit:

- adding case retrieval
- adding web search
- adding long-term memory
- adding formal `message_history`
- adding GUI
- changing backend default policy
- changing battle-dex ingestion
- making unsupported hard species recommendations

## What To Audit

### 1. CLI operational behavior

Run both backend situations if available:

- no native env / invalid native env -> `auto` should fall back to deterministic
- valid native env if locally configured -> `auto` should use native
- explicit `--backend deterministic` should work
- explicit `--backend pydantic_ai_native` should fail/refuse cleanly if config
  is missing or invalid

Do not put live keys in the repo.

### 2. Team analysis quality

Use at least 3 realistic team inputs:

- a balanced six-slot type team
- a team with obvious repeated weakness
- a team with awkward / incomplete user phrasing

Check:

- does the response identify structural weak points?
- does it mention evidence from deterministic engine?
- does it avoid pretending semantic judgement is confirmed?
- are follow-up options useful?
- does the answer read like an advisor, not a raw dump?

### 3. Species discussion quality

Use at least 3 species queries:

- one known species with profile + moves + ability
- one known species followed by a pronoun follow-up (`它适合干什么`)
- one unknown species

Check:

- profile facts are SQL-backed
- ability evidence appears when available
- move pool is summarized without overclaiming
- unknown species refuses cleanly
- semantic role output stays provisional

### 4. Session-local follow-up quality

Run one short session:

1. set a team
2. analyze team
3. query a species
4. ask a pronoun follow-up
5. clear session
6. verify state is cleared

Check:

- session context works within one process
- `/clear` clears local state
- no cross-session persistence appears
- no formal `message_history` assumption is introduced

### 5. Evidence and confidence discipline

For every output sampled, check:

- confirmed claims trace to deterministic engine or SQL facts
- semantic role interpretation is provisional
- unsupported claims are downgraded or refused
- evidence is not invented
- no hard meta claim is made

## Recommended Commands

Baseline deterministic:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend deterministic \
  --message "/set-team 草 地 龙 翼 火 水" \
  --message "分析这队联防" \
  --message "/species 豆丁鱼" \
  --message "它适合干什么"
```

Auto backend:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "/set-team 草 地 龙 翼 火 水" \
  --message "分析这队联防" \
  --message "/species 豆丁鱼" \
  --message "它适合干什么"
```

Unknown species:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend auto \
  --message "/species 不存在的精灵"
```

Full tests before/after if any code changes are made:

```bash
.venv/bin/python -m unittest discover -s tests
```

## Deliverable

Return a concise report with:

1. `Verdict`
   - `PASS`
   - `PASS_WITH_FINDINGS`
   - `FAIL`
   - `BLOCKED`

2. `Backend behavior`
   - auto fallback result
   - explicit deterministic result
   - explicit native result if tested

3. `Findings`
   - ordered by severity
   - each finding must include:
     - scenario
     - observed behavior
     - expected behavior
     - file reference if code-level
     - whether it requires code, spec, prompt, or data follow-up

4. `Product quality judgement`
   - advisor usefulness
   - evidence quality
   - refusal quality
   - follow-up quality

5. `Recommended next action`
   - `none`
   - `code hardening`
   - `prompt/runtime tuning`
   - `retrieval improvement`
   - `spec clarification`

## Logging Rule

If the dogfood thread makes no code changes, it may return the report without
editing files.

If it makes code/test changes, it must update:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Do not update product strategy specs unless explicitly authorized by the main
thread.

## Copy-paste Prompt For Test Thread

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_dogfood_audit_spec.md` first.

You are the Roco advisor dogfood audit thread. Your job is to use the current conversational CLI like a real user and judge product behavior, evidence quality, refusal quality, and backend behavior.

Do not redesign architecture. Do not add scope. Do not add case retrieval, web-in-loop, formal message_history, GUI, or ingestion changes. Do not change the backend default policy.

Execute the dogfood scenarios in the spec. If you find code-level defects, report them with severity and only patch if the fix is small, local, and clearly inside the approved MVP contract. If you patch, run full tests and update `log/project_log.md`.

Return only:
- verdict
- backend behavior
- findings
- product quality judgement
- recommended next action
```
