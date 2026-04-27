# Retrieval Phase A Eval Request

## Purpose

This request is for a separate **test / implementation thread**.

Its job is to evaluate and harden the current Phase A retrieval layer.

Do not implement embeddings.
Do not implement case retrieval.
Do not add web retrieval.

## Current Retrieval Reality

Structured battle-dex facts:

- implemented through `BattleDexRepository`
- SQL-first
- exact typed retrieval
- not embedding retrieval

Doc retrieval:

- implemented in `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`
- current implementation is a static curated rule table
- it returns bounded `DocContextSnippet` objects
- scoring is keyword/rule based
- no embeddings
- no FTS
- no automatic document chunking

Case retrieval:

- deferred
- not part of current MVP

## Task Boundary

Allowed:

- add retrieval eval tests
- add small retrieval fixture cases
- improve current curated/rule retrieval if tests expose obvious gaps
- update logs with execution facts

Not allowed:

- add embeddings
- add vector database
- add tactical casebank retrieval
- add web-in-loop
- expand advisor tool set
- change backend default policy
- redesign retrieval architecture

## Required Eval Coverage

### 1. Doc retrieval topic coverage

Test that representative queries retrieve expected topics:

- team structure / 联防 query retrieves `engine_grounding`
- confidence / 证据 query retrieves `confidence_guard`
- dual-type / 双属性 / 抗性 query retrieves `dual_type_baseline`
- species role / 主C / 辅助 query retrieves `team_conditional_roles`
- scope / 支持 / 范围 query retrieves `scope_boundary`

### 2. Boundedness

Verify:

- `limit` is respected
- duplicate topics are not returned
- irrelevant `analysis_type` snippets do not leak

### 3. Safe empty/weak retrieval behavior

Verify:

- unrelated query returns only baseline guardrails if appropriate, or empty
  bounded output if no rule matches
- retrieval output does not force unsupported claims downstream

### 4. Integration smoke

Verify at least one team-analysis CLI path and one species-query CLI path show
doc/context evidence when doc retrieval ran.

## Suggested Files

Likely in scope:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`
- optionally a new focused test file:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_retrieval.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Do not modify data ingestion or crawler files.

## Validation

Minimum:

```bash
.venv/bin/python -m unittest discover -s tests
```

If adding a focused retrieval test:

```bash
.venv/bin/python -m unittest tests.test_retrieval
```

## Expected Deliverable

Return:

1. verdict:
   - `PASS`
   - `PASS_WITH_FIXES`
   - `BLOCKED`
2. retrieval eval coverage added
3. files changed
4. tests run and exact results
5. whether current Phase A retrieval is acceptable for Advisor MVP dogfood

## Copy-paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_phase_a_eval_request.md` first.

You are the Roco retrieval Phase A eval worker. Your job is to evaluate and harden the current curated/rule-based doc retrieval layer.

Do not add embeddings. Do not add case retrieval. Do not add web-in-loop. Do not expand the advisor tool set. Do not redesign retrieval architecture.

Add focused retrieval eval coverage for current `advisor/retrieval.py`, improve only small local rule gaps if tests expose them, run full tests, and update `log/project_log.md` with execution facts.

Return verdict, coverage added, files changed, tests run, and whether Phase A retrieval is acceptable for Advisor MVP dogfood.
```
