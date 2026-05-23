# Advisor CLI MVP Completion Record

## Decision

Status:

- `Advisor CLI MVP complete`

Decision date:

- `2026-04-16`

Decision owner:

- main thread

Basis:

- final MVP readiness check returned `PASS_WITH_FINDINGS`
- final MVP readiness recommendation returned
  `ready_to_declare_mvp_complete`

## Completed MVP Scope

The completed MVP includes:

- conversational CLI
- session-local team context
- session-local species context
- `/set-team`
- `/show-team`
- `/analyze`
- `/species <name>`
- `/clear`
- `/exit`
- deterministic team/type structure analysis
- SQLite battle-dex repository lookups
- bounded curated doc retrieval
- deterministic backend
- `pydantic_ai_native` backend
- `auto` backend policy
- native-first routing with deterministic fallback for supported flows
- bounded native timeout/failure behavior
- partial-team caveats
- unknown-species refusal
- future/live-meta refusal
- evidence and confidence discipline

## Confidence Boundary

Confirmed claims are limited to:

- deterministic Engine output
- SQL-backed battle-dex facts
- approved static doc snippets

Provisional claims include:

- species role judgement
- team fit interpretation
- semantic battle advice based on current facts

Refused / unsupported in the completed MVP:

- future official balance prediction
- live meta prediction
- web-in-loop claims
- hard species recommendations not backed by available evidence

## Final Readiness Check Summary

Verdict:

- `PASS_WITH_FINDINGS`

Recommendation:

- `ready_to_declare_mvp_complete`

Regression tests:

- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 68 tests in 3.160s`, `OK`

Key passes:

- deterministic backend works
- `auto` missing env falls back immediately
- `auto` unreachable native config falls back to deterministic
- repeated messages after native failure skip repeated native timeout windows
- explicit `pydantic_ai_native` missing env exits cleanly
- explicit `pydantic_ai_native` unreachable provider returns bounded native
  refusal
- six-slot team analysis is useful and evidence-backed
- partial team input includes visible caveat
- species facts are SQL-backed where available
- pronoun follow-up works before `/clear`
- `/clear` removes session-local team/species context
- unknown species refuses cleanly
- future/live-meta request explicitly refuses due to no web/live official
  balance feed
- tool statuses stay within `ok`, `degraded`, `refused`, `failed`
- no case retrieval, embeddings, web-in-loop, GUI, formal message history,
  cross-session persistence, or ingestion behavior appeared

## Accepted Non-Blocking Finding

Finding:

- `P3`: local native provider was not validated as successful native output

Observed:

- local env exists and resolves to `pydantic_ai_native`
- sampled native call timed out under `--native-timeout 2`
- `auto` fallback returned deterministic output correctly

Decision:

- not blocking for MVP completion

Reason:

- approved `auto` behavior is bounded fallback for supported flows
- deterministic path is usable
- explicit native failure remains bounded
- validating provider quality is a post-MVP runtime reliability task, not a
  blocker for the completed CLI MVP

## Deferred Post-MVP Work

Still deferred:

- GUI
- case retrieval / casebank
- embeddings / vector retrieval
- web-in-loop
- formal runtime-level `message_history`
- cross-session persistence
- crawler/database expansion
- native provider quality investigation

## Next Decision

The next main-thread decision is post-MVP prioritization:

- product polish / prompt quality
- GUI
- case retrieval / casebank
- embeddings / retrieval upgrade
- crawler/database expansion
- native provider reliability
