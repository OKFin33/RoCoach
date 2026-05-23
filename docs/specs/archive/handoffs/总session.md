# 总 Session Handoff Spec

## Purpose

Provide a full-session continuation artifact so a completely new thread can resume the current project state without hidden context.

This is the project-wide handoff, not the crawl-only handoff.

It captures:

- current roadmap position
- accepted technical and product decisions
- implemented deliverables
- active specs
- deferred work
- immediate next actions

## Project Snapshot

As of `2026-04-16`, the project state is:

- `Phase 1` deterministic team structure analysis is implemented
- `Phase 1.5` report MVP is implemented
- wiki crawl / cleaner / importer / SQLite write path are implemented and validated
- current importer review backlog is closed
- current battle dex is a usable structured substrate for a lightweight advisor
- conversational Advisor CLI MVP exists
- CLI backend policy is `auto`
  - valid native env selects `pydantic_ai_native`
  - missing/invalid native config falls back to `deterministic`
  - native failure/timeout under `auto` falls back to deterministic for supported flows
- first dogfood audit findings have been fixed
- current next work is tracked in:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md`

Current approved architecture:

- deterministic `Battle Engine` remains the factual core
- report / advisor harness uses `PydanticAI`
- report generation is grounded by Engine output, retrieval, and validation
- retrieval should evolve into `hybrid local RAG`:
  - SQLite / typed retrieval for battle-dex facts
  - lightweight doc retrieval for mechanics and methodology
  - tactical case retrieval for role / archetype priors
- `Option C` model-centric advisor architecture is recorded only as a future candidate

## Current Product Direction

The current product is evolving from:

- structure analyzer

toward:

- grounded team-analysis report layer
- then conversational lightweight advisor behavior

The current scope is still:

- team analysis from attributes
- constrained species-level semantic judgement may be introduced with explicit uncertainty
- no authoritative meta analysis

## Implemented Work

### A. Type System

Implemented:

- canonical type chart
- single-type effectiveness
- dual-type baseline rule using current project interpretation:
  - `2x + 2x => 3.0`
  - `0.5x + 0.5x => 1/3`
  - `2x + 0.5x => 1.0`
- visible status immunities

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/roco_world_model.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/roco_world_type_chart.json`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/reference/luoke_world_type_database_v2.json`

### B. Phase 1 Team Structure Engine

Implemented:

- defensive coverage table
- repeated weakness detection
- missing resistance detection
- STAB-only offensive coverage
- structural score
- patch guidance:
  - `primary_patch_types`
  - `conditional_dual_patch_types`

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/team_structure.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/contracts.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/battle_engine/phase1_cli.py`

### C. Phase 1.5 Report MVP

Implemented:

- curated retrieval
- deterministic narrative generator
- optional `PydanticAI` backend adapter
- report validator
- Phase 1.5 report CLI

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/contracts.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/knowledge.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/generator.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/validator.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/service.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/reporting/phase15_cli.py`

### D. P1a Spec Layer

Implemented:

- combat ontology
- data source strategy
- field alignment matrix
- wiki field discovery spec

Key files:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/combat_ontology.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/data_source_strategy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_field_discovery_spec.md`

### E. Battle Dex Pipeline

Implemented:

- wiki field discovery reconnaissance
- bounded dry-run crawl / clean artifacts
- manual supplement promotion into structured YAML
- importer dry-run under policy B
- SQLite write-path validator and smoke write
- duplicate-page manual canonical override handling

Current importer baseline:

- `resolved_species_forms = 566`
- `resolved_moves = 494`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 0`
- `supplement_backed_entities = 5`
- `unresolved_entities = 0`

## Core Decisions That Must Not Drift

### 1. Agent-Led, Engine-Grounded

The product surface is Agent-led, but the deterministic Engine remains the source of truth for hard facts and repeatable analysis.

### 2. Report Layer Boundaries

The report layer may:

- explain
- organize
- contextualize
- support lightweight advisory interaction

It may not:

- invent species-level guidance in Phase 1.5
- override Engine facts
- make hard meta claims

### 3. PydanticAI Route

The approved near-term orchestration layer is:

- `PydanticAI`

Not approved now:

- `DeerFlow`
- `LangGraph`
- long-horizon multi-agent runtime

### 4. Patch Guidance Semantics

Patch outputs are split into:

- `primary_patch_types`
- `conditional_dual_patch_types`

Dual-type suggestions are conditional only.

### 5. Retrieval Shape

The project should not treat the current SQLite battle dex as a finished RAG system.

Approved near-term retrieval shape:

- `structured retrieval`
  - species / move / ability / learnset facts from SQLite
- `doc retrieval`
  - approved mechanics / methodology / confidence docs
- `case retrieval`
  - representative tactical examples for role and archetype priors

This is a `hybrid local RAG` design, not an open-ended web-search loop.

### 6. P1a Scope

Current field discovery scope is strictly:

- `species`
- `move`
- `ability`

Every candidate field must be tagged:

- `confirmed`
- `provisional`
- `forbidden_by_default`

### 7. Source Strategy

For P1a:

- wiki = primary structured source
- official / in-game evidence = mechanic verification source
- community material = low-confidence supplement only

### 8. Team-Conditional Role Understanding

The system should not assume a species has one globally correct role.

Role judgement should depend on:

- species baseline
- selected set / configuration
- team context
- tactical plan

Early role outputs should therefore be framed as:

- `role_hypothesis`
- `role_scores`
- `uncertainty_notes`

## Most Important Specs

New thread should prioritize reading:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/domain_primer.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/agent_framework_decision.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/scoring_system.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_layer.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_schema.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_confidence_policy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_runtime_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_response_contract.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_eval_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/semantic_role_policy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/tactical_casebank_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/conversation_cli_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/combat_ontology.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_field_discovery_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1f_db_sync_min_ctx_for_crawl.md`

## Current Runtime / Environment Notes

- `requirements.txt` includes `pydantic-ai-slim[openai]`
- repo-local `.venv` was created and validated for `pydantic_ai` import
- system Python on this machine is externally managed; do not use `pip install` globally
- prefer repo-local `.venv` for Python dependency setup

## Validated Commands

Tests:

```bash
python3 -m unittest discover -s tests
```

Phase 1 CLI:

```bash
python3 -m battle_engine.phase1_cli --input-file examples/phase1_sample_team.json
```

Phase 1.5 CLI:

```bash
python3 -m reporting.phase15_cli --input-file examples/phase1_sample_team.json
```

Repo-local venv setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Open Risks

- the `x3 / 1/3` dual-type baseline is still provisional
- ability currently has no confirmed standalone wiki page source and should remain embedded/derived unless stronger evidence appears
- Biligame wiki API returned intermittent `567` server errors during P1d rerun attempts
- taxonomy and methodology are still stronger than the current role-feature layer beneath them
- current repo lacks a proper conversational Agent CLI
- current repo lacks a battle-dex-aware retrieval layer over SQLite
- current repo lacks a tactical casebank for pattern induction
- community meta signal ingestion is still deferred

## Deferred Work

- community meta signal ingestion
- Phase 2 species database
- Phase 3 meta snapshot system
- future consideration of model-centric `Option C`

## Immediate Next Recommended Action

The highest-value next action is:

- define and implement the conversational advisor runtime contracts
- define lightweight local RAG contracts over SQLite + docs + tactical cases
- define tactical casebank contracts and seed strategy
- defer any further crawl expansion unless a new data blocker appears
- continue with offline importer/schema work only against the existing successful baseline artifacts

Why:

- P1a field discovery is complete and reviewed
- P1b minimal battle dex schema is drafted
- P1c crawler/cleaner contract is drafted
- P1d artifact-producing dry-run exists and validates
- the next online bottleneck is API stability, not schema design
- it does not require reopening architecture decisions
- it will validate schema and cleaner assumptions before SQLite mutation

If the next thread is crawl-focused, use:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/爬session.md`

## Suggested Opening Prompt For A New General Thread

> Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/总session.md`, `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`, `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/agent_framework_decision.md`, and `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md`. Then continue the project from the current approved state, preserving the Agent-led hybrid-analysis direction, the PydanticAI advisor route, and the P1a field discovery boundaries.
