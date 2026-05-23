# Native Runtime Audit Handoff

## Purpose

This handoff is for a **separate audit / test thread**.

Its job is not feature development.

Its job is to verify that the current `Roco advisor MVP` implementation still
matches the approved contracts after `pydantic_ai_native` integration.

## Thread Role

The new thread should be positioned as:

- `project test / audit thread`
- verification-focused
- contract-discipline focused
- not an implementation expansion thread

## Minimal Context

Current repo reality:

- a first usable `conversational Agent CLI` MVP exists
- `BattleDexRepository` exists and reads from SQLite
- bounded local doc retrieval exists
- advisor runtime exists with two paths:
  - `deterministic`
  - `pydantic_ai_native`
- current live MVP tools include:
  - `analyze_team_structure`
  - `get_species_profile`
  - `get_species_available_moves`
  - `retrieve_doc_context`
  - `analyze_species_semantics`

Current approved constraints that must not drift:

- deterministic Engine / SQL facts are the only source allowed to produce `confirmed`
- semantic species/team judgement defaults to `provisional`
- insufficient evidence must downgrade or refuse
- no formal `message_history` runtime state
- no case retrieval in current MVP live tool set
- no web-in-loop
- current next priority from main thread is:
  - `improve deterministic/native output parity`

## Current Approved Files To Read

Read only these first:

1. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
2. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/conversation_cli_spec.md`
3. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_tool_contracts.yaml`
4. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_confidence_policy.md`
5. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_mvp_impl_handoff.md`
6. `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Then inspect implementation reality in:

7. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
8. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/conversation_cli.py`
9. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/battle_dex.py`
10. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`

## Audit Goals

The audit thread should answer:

1. does `pydantic_ai_native` preserve approved business contracts?
2. does native output stay aligned with deterministic output on supported requests?
3. does native fallback behavior obey refusal / downgrade policy?
4. did runtime integration silently expand product scope?

## Required Audit Scope

### 1. Output Parity

Compare `deterministic` vs `pydantic_ai_native` on representative supported flows:

- team structure analysis
- species discussion
- follow-up within same session

Check:

- output shape
- key conclusions
- evidence summary discipline
- confidence labels
- refusal behavior

### 2. Failure-Path Coverage

Check at least:

- missing provider config
- invalid provider config
- empty retrieval result
- unknown species query
- unsupported request type

### 3. Scope Discipline

Verify that runtime did not silently introduce:

- case retrieval as live MVP dependency
- cross-session persistence
- formal `message_history` state
- web-in-loop
- unsupported hard species recommendation

## Deliverable Format

The audit thread should return:

1. `Alignment verdict`
   - `ACKNOWLEDGED`
   - `SPEC DRIFT`
   - `CODE DRIFT`
   - `BLOCKED`

2. `Findings`
   - ordered by severity
   - with file references

3. `Parity judgement`
   - acceptable
   - acceptable with caveats
   - not acceptable

4. `Required follow-up`
   - `none`
   - `spec update`
   - `code update`
   - `both`

## Hard Rules

The audit thread must not:

- redesign architecture
- add new product scope
- require live keys to be committed into repo
- promote `message_history` into approved state
- reintroduce case retrieval into MVP-required live tools

If a behavior was only discussed historically but not approved in specs/logs:

- mark it out of scope
- do not treat it as required

## Copy-Paste Prompt For New Thread

> Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/native_runtime_audit_handoff.md` first. You are a **project test / audit thread**, not a feature thread. Your job is to audit the current `Roco advisor MVP` implementation against approved contracts after `pydantic_ai_native` integration. Focus on deterministic/native parity, failure-path coverage, and scope discipline. Do not redesign the system. Do not expand product scope. Return only an audit verdict, findings with file references, parity judgement, and required follow-up.
