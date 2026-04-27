# P0d Persona V1 + IP Guard Audit Request

## Purpose

Audit the completed P0d Persona V1 + IP Guard implementation before mobile
scaffold or public-release hardening begins.

This is a verification task. Do not expand product scope.

## Context

P0d implementation reported:

- default public-safe persona:
  - `persona_id=obsidian_tactical_coach`
  - `display_name=黑曜战术官`
  - `display_style=cold_precise_high_pressure_tactical`
- `PersonaEnvelope.display_name`
- deterministic `response.persona.rendered_answer`
- base `response.answer` remains unchanged
- `facts_locked=True`
- `fact_policy=persona_may_not_alter_facts`
- conservative persona metadata sanitization for Enzo/恩佐/Tencent/洛克王国/
  official/artwork/dialogue/character-positioning markers
- bounded API request-side persona selection through optional `persona_id`
- unsupported/unsafe persona selectors sanitize to default

## Audit Scope

### 1. Fact-lock boundary

Verify persona rendering does not alter:

- `status`
- `analysis_type`
- `backend`
- `answer`
- `tool_results`
- `evidence`
- `confidence_notes`
- `followup_options`
- refusal decisions

Persona output may only affect:

- `response.persona`
- `response.persona.rendered_answer`

### 2. Default persona safety

Verify default persona metadata is public-safe:

- no `Enzo`
- no `恩佐`
- no `Tencent`
- no `腾讯`
- no official-character positioning
- no official authorization implication
- no official art/screenshot/dialogue positioning

### 3. IP guard behavior

Verify unsafe persona metadata or selector requests are refused or sanitized.

At minimum sample:

- `Enzo`
- `恩佐`
- `Tencent`
- `腾讯`
- `洛克王国官方`
- `official`
- `官方授权`
- `官方立绘`
- `官方台词`

The API must not echo these markers through persona metadata.

### 4. Rendered-answer risk check

Specifically inspect whether `persona.rendered_answer` can reintroduce
official-IP markers from base `response.answer`.

If it can, classify whether this is acceptable because it is factual/base-answer
content, or a P1/P2 boundary issue because persona presentation is now carrying
official-IP-sensitive text.

Do not automatically fix it in the audit thread unless the issue is trivial and
fully bounded.

### 5. API behavior

Verify:

- `/chat` accepts optional safe `persona_id`
- `/team/analyze` accepts optional safe `persona_id`
- unsupported/unsafe persona selectors sanitize to default
- request models still do not accept provider keys as configuration
- no provider key, env path, DB path, or traceback leaks
- metadata exposes persona feature safely

### 6. Regression

Run existing tests and inspect for accidental scope drift:

- no mobile
- no GUI
- no official Enzo persona
- no official assets
- no LLM-based persona rewriting
- no case retrieval
- no embeddings
- no web-in-loop
- no durable persistence
- no hosted provider-key management
- no backend policy change
- no AdvisorAgent rewrite
- no intentional CLI output change

## Required Test Commands

```bash
.venv/bin/python -m unittest tests.test_agent_core_orchestrator
.venv/bin/python -m unittest tests.test_api
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest tests.test_agent_core_contracts
.venv/bin/python -m unittest discover -s tests
```

Add bounded ad-hoc checks if needed for unsafe persona selector behavior.

## Deliverable

Return:

- verdict: `PASS` | `PASS_WITH_FINDINGS` | `FAIL` | `BLOCKED`
- mobile readiness: `ready_for_P0e_mobile_scaffold` |
  `needs_targeted_persona_refactor` | `blocked`
- fact-lock judgement
- default persona safety judgement
- IP guard judgement
- rendered-answer risk judgement
- API persona selector judgement
- regression judgement
- findings with severity and file references
- exact tests run

## Copy-Paste Prompt

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p0d_persona_ip_guard_audit_request.md` first.

You are the test / architecture-audit thread. Audit the completed P0d Persona V1 + IP Guard implementation before mobile scaffold or public-release hardening begins.

Focus on fact-lock boundaries, public-safe default persona metadata, unsafe persona selector sanitization, rendered-answer IP-risk behavior, API persona selector behavior, redaction, and regression.

Do not add mobile, GUI, official Enzo persona, official assets, LLM-based persona rewriting, case retrieval, embeddings, web-in-loop, durable persistence, hosted provider-key management, backend policy changes, AdvisorAgent rewrites, or intentional CLI output changes.

Run `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`, `.venv/bin/python -m unittest tests.test_api`, `.venv/bin/python -m unittest tests.test_advisor`, `.venv/bin/python -m unittest tests.test_agent_core_contracts`, and `.venv/bin/python -m unittest discover -s tests`.

Return verdict, mobile readiness, fact-lock/default-persona/IP-guard/rendered-answer/API-selector/regression judgements, findings with severity and file refs, and exact tests run.
```
