# Agent MVP Implementation Handoff

## Purpose

Provide a clean handoff for a new thread that will implement the first usable
`conversational Agent CLI` for the Roco battle advisor.

This handoff is implementation-oriented.

It intentionally excludes most historical discussion unless it directly affects
current coding decisions.

## Current Project State

As of `2026-04-15`, the project has:

- a working deterministic Phase 1 structure engine
- a working Phase 1.5 report harness
- a validated battle-dex ingestion / importer / SQLite write path
- approved architecture for `Agent-led + hybrid local RAG`
- a usable conversational Agent CLI MVP
- a `PydanticAI` native runtime path implemented for the advisor
- deterministic and native runtime paths coexisting during migration
- CLI default backend policy is `auto`: valid native env config selects
  `pydantic_ai_native`, otherwise it falls back to `deterministic`

## Non-Negotiable Architecture

The implementation thread must preserve these decisions:

1. product surface is `Agent-led`
2. deterministic structure facts remain Engine-owned
3. runtime choice is `PydanticAI`
4. retrieval shape is `hybrid local RAG`
5. structured battle facts are `SQL-first`
6. embeddings are optional later, mainly for docs and casebank
7. semantic role judgement is allowed, but must be:
   - evidence-backed
   - uncertainty-bearing
   - team-conditional

## Current Working Substrate

### 1. Battle Engine

Implemented:

- team structure analysis
- repeated weaknesses
- missing resistances
- STAB-only offensive coverage
- patch direction output

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/team_structure.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/contracts.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/phase1_cli.py`

### 2. Report Harness

Implemented:

- deterministic report generator
- optional `PydanticAI` report generator
- report service
- Phase 1.5 report CLI

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/generator.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/service.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/phase15_cli.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/knowledge.py`

Important limitation:

- this is not the final semantic advisor
- case retrieval and advanced semantic scoring are still deferred

### 3. Battle Dex

Current importer dry-run baseline:

- `resolved_species_forms = 566`
- `resolved_moves = 494`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 0`
- `supplement_backed_entities = 5`
- `unresolved_entities = 0`

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_sqlite_schema_v1.sql`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tools/import_battle_dex_sqlite.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tools/import_battle_dex_dry_run.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`

Interpretation:

- the SQLite battle dex is a usable structured facts substrate
- it is not a complete RAG system by itself

## Specs The New Thread Must Read First

Required reading order:

1. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/总session.md`
2. `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
3. `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/agent_framework_decision.md`
4. `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md`
5. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
6. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
7. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/tactical_casebank_spec.md`
8. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/conversation_cli_spec.md`
9. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_confidence_policy.md`
10. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_tool_contracts.yaml`

## Implementation Goal

Advance the first usable `conversational Agent CLI` from MVP toward a cleaner
native runtime and stronger operational polish.

That means:

- user can describe a team or ask about a species
- advisor can call tools
- advisor can retrieve structured facts and bounded docs
- advisor can answer with evidence + confidence
- session can carry follow-up context
- native runtime configuration can be supplied locally without storing secrets in
  the repo

## Current Implemented Slice

Implemented:

### A. BattleDexRepository

- typed SQLite query layer
- lookup methods for species profile, species move pool, move detail, and ability detail
- runtime bootstrap helper that selects a write-eligible importer run

### B. Retrieval Layer

- doc retrieval over approved local docs
- curated / keyword-bounded Phase A implementation
- no embeddings required in current MVP

### C. Advisor Runtime Skeleton

- deterministic advisor path implemented
- `PydanticAI` native advisor path implemented
- tool routing, context builder, trace merge, and typed response object implemented
- native runtime remains bounded by current confidence policy

### D. Conversational CLI

- session-local state
- natural-language entry
- optional slash commands
- readable terminal output
- local env-file support for native runtime configuration outside the repo
- `auto` backend policy that preserves explicit backend overrides

## Explicitly Deferred

Do not expand into these unless blocked:

- tactical casebank ingestion implementation
- role prior induction pipeline
- meta ingestion
- web search in loop
- frontend
- long-term memory
- multi-agent runtime
- formal runtime-level `message_history` session field
- storing live API keys in project files

## Recommended Next Coding Order

1. improve native runtime operational ergonomics and docs
2. keep deterministic/native output parity where practical
3. add stronger native runtime tests against provider configuration and failure paths
4. decide when native runtime is robust enough to become the default CLI backend
5. only after that, reopen deferred retrieval or semantic scope

## Acceptance Standard For Current Delivery

Current delivery is successful if:

- it can analyze a team in conversational form
- it can discuss a species using battle-dex facts
- it can include approved doc evidence
- it does not claim unsupported hard role truth
- it surfaces uncertainty correctly
- it supports a native `PydanticAI` runtime path without storing secrets in the repo

## Important Warnings

- do not confuse the current report CLI with the target advisor runtime
- do not rebuild the data pipeline unless a real blocker appears
- do not replace SQL fact lookup with semantic retrieval
- do not let the LLM invent deterministic facts
- do not add `message_history` as formal runtime state unless explicitly approved
- do not make case retrieval an MVP dependency
- do not commit provider keys or env files under the project tree

## Suggested New-Thread Prompt

Use this prompt in the new thread:

> Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_mvp_impl_handoff.md` first, then read the files it lists under “Specs The New Thread Must Read First”. Continue from the current advisor MVP state: usable conversational CLI, deterministic and `PydanticAI` native runtime paths, SQL-first battle-dex retrieval, bounded doc retrieval, and evidence/confidence discipline already implemented. Focus next on operational polish, native-runtime hardening, and approved MVP-scope improvements. Do not reopen framework selection or expand into case retrieval / message_history unless a concrete approved change appears.
