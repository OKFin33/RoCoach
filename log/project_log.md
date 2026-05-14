# Project Log

## Purpose

This file records the working context, major decisions, deferred items, and active execution focus for the Roco project.

It exists to support:

- later review and retrospection
- cross-session continuity
- handoff to new agents
- explicit tracking of deferred work that should not be forgotten

## Working Model

### Roles

- User (Tamerael): PM / product owner
- Codex: V1 release engineering (mobile/desktop/API)
- Clé: P10h experiment, D-layer, Meta Graph (V2 architecture + execution)

### Collaboration Agreement

- The user defines goals, non-goals, constraints, and priorities.
- Codex converts them into specs, contracts, implementation, and verification.
- Tradeoff discussions should focus on:
  - correctness
  - implementation cost
  - future extension cost
- The project is now `Agent-led` at the product surface and `hybrid` in analysis internals.
- Deterministic structure analysis stays in Engine tools.
- Semantic judgement is allowed in the Agent layer when the question is not yet fully captured by approved deterministic features.

### Current Core Stack

- Python
- FastAPI
- Pydantic
- SQLite initially
- SQLAlchemy
- pytest
- CLI first, frontend later if needed

### 2026-04-21: P1a Mechanism Guard Hardening + Preliminary Audit

Completed:

- hardened team analysis so user-supplied teams default to
  `unknown_quality_team` instead of being treated as implicitly coherent
- added a bounded `TeamSemanticGuard` contract with:
  - `candidate_plan`
  - `supporting_evidence`
  - `counterevidence`
  - `coherence_verdict`
  - `coherence_score`
- added mechanism-aware retrieval that scans A-layer ability text and move
  effect text for:
  - `迅捷`
  - `先手`
  - `速度`
  - `传动`
  - `迸发`
  - `蓄力`
  - `印记`
  - `天气`
  - `应对`
  - `奉献`
  - `萌化`
- wired runtime so reviewed mechanism pages are auto-inserted into evidence when
  available, while missing reviewed pages force explicit downgrade
- added reviewed wiki page:
  - `wiki/pages/mechanics/speed_priority_and_swift.md`
- fixed native runtime trace merge so post-tool validation can overwrite early
  generic doc retrieval with mechanism-aware payloads
- removed persona contamination from default synthesis doctrine by replacing
  `internal_enzo_pattern_pack` with `generic_battle_doctrine_pack`

Verification:

- `python3 wiki/schema/compile_wiki.py`
- `.venv/bin/python -m unittest tests.test_retrieval tests.test_advisor`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts tests.test_agent_core_orchestrator`

Audit Takeaway:

- `P1a synthesis seam` is now materially safer for A+B bridging than before
- current B-layer wiki is sufficient for a bounded first bridge:
  - compiled reviewed pages exist
  - runtime can consume reviewed mechanism pages through compiled exports
  - missing reviewed pages degrade honestly instead of being improvised
- bridge is still incomplete for a broader live model-backed doctrine layer
  because reviewed coverage is still missing for mechanisms such as:
  - `传动`
  - `迸发`
  - `蓄力`
  - `奉献`
  - `萌化`
- team/case semantics are still shallow and should not yet be marketed as
  fully mature B-layer battle understanding

### 2026-04-21: Battle Wiki Mechanism Coverage Completion Pass

Completed:

- added reviewed provisional mechanism pages:
  - `wiki/pages/mechanics/status_effects_and_persistence.md`
  - `wiki/pages/mechanics/entry_exit_and_replacement_timing.md`
  - `wiki/pages/mechanics/energy_actions_and_focus.md`
- expanded runtime mechanism lexicon beyond the first bounded core to cover:
  - status terms:
    - `灼烧`
    - `冻结`
    - `中毒`
    - `寄生`
  - resource terms:
    - `聚能`
    - `魔力`
  - entry/exit timing terms:
    - `换人`
    - `离场`
    - `脱离`
    - `回场`
    - `入场`
    - `替换上场`
    - `主动离场`
  - weather names:
    - `雨天`
    - `沙暴`
    - `雪天`
    - `暴风雪`
  - mark subtype and mark-operation terms:
    - `棘刺印记`
    - `光合印记`
    - `蓄势印记`
    - `龙噬印记`
    - `中毒印记`
    - `降灵印记`
    - `攻击印记`
    - `湿润印记`
    - `减速印记`
    - `蓄电印记`
    - `风起印记`
    - `星陨印记`
    - `清印记`
    - `驱散印记`
    - `偷印记`
    - `覆盖印记`
    - `转换印记`
  - response-adjacent term:
    - `打断`
- kept `复活` deferred as a standalone runtime token even though
  `morale_and_revive.md` remains the parent reviewed page
- preserved bug-traceability by adding:
  - `meta/wiki/mechanism_registry_2026-04-21.md`
  - `meta/wiki/mechanism_review_checklist_2026-04-21.md`
- updated battle-wiki governance notes so later debugging can reconstruct:
  - which mechanism has a page
  - which token triggers auto-retrieval
  - which items still remain deferred

Verification:

- `python3 wiki/schema/compile_wiki.py`
- `.venv/bin/python -m unittest tests.test_retrieval tests.test_advisor`

Maintenance Note:

- this pass intentionally leaves `meta/wiki/mechanism_registry_2026-04-21.md`
  with an explicit transition note rather than silently rewriting historical
  table states
- if later retrieval bugs appear, audit in this order:
  1. runtime token present in `advisor/retrieval.py`
  2. reviewed page exists and compiles into `wiki/compiled/`
  3. test coverage exists for the relevant token family

Weather clarification:

- `雪天` and `暴风雪` should be treated as two names for the same in-game
  weather mechanism
- updated weather doctrine/source-note wording accordingly so later debugging
  does not reopen this naming split as an unresolved issue

Console handoff note:

- added `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_console_handoff_2026-04-22.md`
- this file is intentionally placed under `specs/` because it is an
  implementation-facing cross-session handoff for the console/main thread
- canonical governance remains under `meta/wiki/`; the handoff spec points back
  to those docs instead of duplicating ownership

### 2026-04-22: Battle Wiki Thread Closure Pass

Completed:

- refreshed `meta/wiki/mechanism_registry_2026-04-21.md` so it now reflects the
  actual runtime/token state after the 2026-04-21 coverage completion pass
- added `meta/wiki/compile_use_contract_2026-04-22.md` as the current Battle
  Wiki governance contract for:
  - reviewed page usage
  - compiled export expectations
  - runtime downgrade boundary
  - parent-topic retrieval rule
- kept implementation-facing console handoff under `specs/`, while keeping
  canonical governance under `meta/wiki/`

Result:

- the Battle Wiki thread now has its own current governance baseline
- remaining work after this point is primarily console/main-thread work rather
  than additional Battle Wiki boundary convergence

### 2026-04-22: Battle Wiki Governance Consistency Fix

Completed:

- updated `meta/wiki/battle_wiki_decision_convergence_2026-04-21.md` so it no
  longer reports already-completed mechanism coverage as missing
- marked `meta/wiki/mechanism_review_checklist_2026-04-21.md` as a historical
  review-pass artifact rather than a live TODO list
- updated `specs/battle_wiki_architecture_spec.md` so governance ownership now
  matches the current `meta/ = C` split

Result:

- Battle Wiki governance docs are now materially closer to a single current
  story
- the main remaining non-data gap is not missing mechanism pages, but future
  cross-thread implementation work

### 2026-04-22: Wiki Entrypoint Drift Guard

Completed:

- updated directory entrypoint READMEs for:
  - `wiki/pages/mechanics/`
  - `wiki/pages/casebank/`
  - `wiki/pages/team_building/`
- added a compile-time README inventory drift guard in
  `wiki/schema/compile_wiki.py`

Result:

- reviewed page directories with `Current reviewed pages:` now fail compile if
  their README inventory drifts from actual reviewed page files
- Battle Wiki infrastructure is less likely to silently rot at the directory
  entrypoint layer

### 2026-04-19: SSD Shift To LLM-Centric Reasoning + Conversational Product Surface

Completed:

- updated SSD to reflect that the default product surface must feel like
  talking to a tactical coach
- clarified that raw structured analytical payloads are internal protocol and
  inspectable detail, not the default first screen
- clarified that LLM should be the core analysis/synthesis unit, while
  deterministic Engine / SQL / approved docs remain the source-of-truth unit
- updated roadmap and task allocation so post-P0 priority shifts to:
  - `P1a Reasoning / Synthesis Layer`
  - `P1b Conversational Presentation Layer`
  - `P1c Pluggable Persona Contract`
- separated analytical/runtime contracts, synthesis contracts, and
  presentation-layer contracts

Files:

- `specs/product_architecture_roadmap.md`
- `specs/current_task_allocation.md`
- `specs/report_layer.md`
- `specs/report_schema.yaml`
- `specs/advisor_response_contract.yaml`
- `specs/advisor_runtime_spec.md`
- `specs/conversation_cli_spec.md`
- `specs/agent_tool_contracts.yaml`
- `specs/reasoning_synthesis_contract.yaml`
- `specs/presentation_response_contract.yaml`
- `specs/p1a_reasoning_synthesis_layer.md`
- `specs/p1b_conversational_presentation_layer.md`
- `specs/p1c_pluggable_persona_contract.md`

Notes:

- CLI may remain more explicit/debug-oriented than the future public/mobile
  default surface
- the product-facing answer should eventually flow as:
  - grounded analytical substrate (`A`)
  - approved doctrine pack (`B`)
  - LLM synthesis
  - `Reply + Why` presentation
  - persona render
- persona is now treated as part of the primary presentation surface, but still
  cannot alter facts, evidence, confidence, or refusal boundaries
- this change does not reopen battle-dex, engine, crawler, or retrieval-scope
  specs

### 2026-04-19: P1 Refactor Skeleton For Deep Persona Integration

Completed:

- added a bounded P1 refactor plan instead of treating persona as a thin skin
- added a persona doctrine contract inspired by the Nuwa five-layer model
- clarified that persona doctrine splits into:
  - reasoning-facing subset for synthesis
  - rendering-facing subset for final expression
- kept the refactor bounded above the analytical substrate; Engine, SQL, API,
  and mobile foundations remain intact

Files:

- `specs/p1_architecture_refactor_plan.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/p1a_reasoning_synthesis_layer.md`
- `specs/p1c_pluggable_persona_contract.md`
- `specs/reasoning_synthesis_contract.yaml`
- `specs/product_architecture_roadmap.md`
- `specs/current_task_allocation.md`

Notes:

- persona is no longer modeled as presentation-only flavor
- post-P0 design now explicitly supports deep persona integration without
  allowing persona to own facts
- this SSD layer should be finalized before running a Nuwa-based persona
  distillation thread

### 2026-04-20: Persona Creation Pipeline SSD Added

Completed:

- added SSD for persona source adapters
- added SSD for persona artifact ingestion / review
- added SSD for a managed persona creation pipeline
- clarified that user-facing "one-step persona creation" still resolves
  internally as:
  - source adapter
  - artifact bundle
  - ingestion
  - registry
  - runtime

Files:

- `specs/persona_source_adapter_contract.yaml`
- `specs/persona_artifact_ingestion_contract.yaml`
- `specs/managed_persona_creation_pipeline_spec.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/p1_architecture_refactor_plan.md`
- `specs/p1c_pluggable_persona_contract.md`
- `specs/product_architecture_roadmap.md`
- `specs/current_task_allocation.md`

Notes:

- `nuwa_distillation_adapter` is the first planned upstream adapter
- future `nexus_original_design_adapter` is explicitly reserved
- manual BYO upload does not need to be a public-facing feature, but
  BYO-compatible ingestion remains an internal requirement

### 2026-04-20: P1 Locked Execution Plan Added

Completed:

- wrote a hard execution-order spec for the next phase
- locked the sequence:
  - Enzo integration review
  - P1a synthesis spec
  - P1a implementation
  - P1a audit
  - P1b presentation spec
  - P1b implementation
  - P1b audit
  - only then revisit later persona-creation implementation tracks

Files:

- `specs/p1_locked_execution_plan.md`
- `specs/current_task_allocation.md`

Notes:

- this is intended to stop thread-level opportunism
- later P1 specs existing on disk do not mean they are unlocked for
  implementation

### 2026-04-19: Nuwa Distillation Thread Spec Prepared

Completed:

- wrote a bounded handoff spec for a separate Nuwa-style persona distillation
  thread
- set the thread goal to produce an internal `Enzo` doctrine draft rather than
  runtime code or public-release persona behavior

Files:

- `specs/nuwa_persona_distillation_enzo_request.md`

Notes:

- the distillation thread should consume the already-updated P1 SSD
- its output should map into `persona_doctrine_contract.yaml`
- integration remains a later main-thread review decision

### 2026-04-14: Agent-Led Hybrid Analysis Direction Approved

Completed:

- replaced the earlier `Engine-first report wrapper` framing with an `Agent-led, hybrid-analysis` framing
- approved `PydanticAI` as the near-term Agent shell, not just a report formatter
- clarified that structure analysis remains deterministic, while semantic battle judgement may be LLM-led under evidence and confidence constraints

Files:

- `docs/agent_framework_decision.md`
- `docs/battle_analysis_architecture.md`
- `specs/report_layer.md`
- `specs/agent_tool_contracts.yaml`
- `docs/model_centric_option_c.md`

Notes:

- this is not approval for freeform Agent reasoning
- it is approval for an Agent-first product surface with a hybrid core:
  - deterministic tools for hard structure facts
  - constrained semantic analysis for role / tactic / mechanics interpretation

### 2026-04-15: Advisor Runtime Alignment With Main Thread

Completed:

- aligned the repo against main-thread decision `019d84da-c0ce-7441-a1c8-17fbcd5156ab`
- recorded that `PydanticAI` is no longer just an optional hook for the conversational advisor
- approved a migration-safe dual-track period:
  - current deterministic path may coexist temporarily with `pydantic_ai_native`
  - runtime direction is now explicitly toward native `PydanticAI`
- clarified MVP-required live tool set for the conversational advisor:
  - `analyze_team_structure`
  - `get_species_profile`
  - `get_species_available_moves`
  - `retrieve_doc_context`
  - `analyze_species_semantics`
- reaffirmed MVP deferrals:
  - `retrieve_case_context`
  - tactical casebank retrieval
  - runtime-level `message_history` as formal session state
  - native deterministic semantic scorer
  - web-in-loop retrieval

Files:

- `specs/advisor_runtime_spec.md`
- `specs/conversation_cli_spec.md`
- `specs/agent_tool_contracts.yaml`
- `log/project_log.md`

Notes:

- alignment verdict was `Spec-only`
- no new product scope was approved
- no confidence-policy relaxation was approved

### 2026-04-15: Advisor CLI Auto Backend Policy

Completed:

- changed CLI default backend policy to `auto`
- `auto` selects `pydantic_ai_native` when valid local native model config exists
- `auto` falls back to `deterministic` when native model config is absent
- explicit backend overrides remain supported:
  - `--backend deterministic`
  - `--backend pydantic_ai_native`
- no MVP scope expansion was introduced

Files:

- `advisor/conversation_cli.py`
- `tests/test_advisor.py`
- `README.md`
- `specs/conversation_cli_spec.md`
- `specs/advisor_runtime_spec.md`
- `specs/agent_mvp_impl_handoff.md`
- `log/project_log.md`

## Timeline

### 2026-04-13: Attribute Model Bootstrapped

Completed:

- Built a canonical type chart from screenshot-derived data
- Implemented a Python type model
- Added tests for single-type and dual-type effectiveness

Files:

- `data/roco_world_type_chart.json`
- `roco_world_model.py`
- `tests/test_roco_world_model.py`

Notes:

- Initial local model used multiplicative dual-type assumptions inherited from familiar monster-battle conventions
- This later became a breaking-change risk after external research suggested `×3 / ÷3` dual-type rules instead

### 2026-04-13: Cross-Check Against External JSON/XLSX/SQLite

Completed:

- Compared the local model against three external structured files
- Found only one content mismatch at that time:
  - `火` status immunity was corrected from `烧伤` to `灼烧`

Notes:

- The three user-provided external files matched each other
- That comparison did not yet include the later `v2` dataset

### 2026-04-13: Architecture and SSD Surface Established

Completed:

- Wrote architecture doc
- Wrote core data model spec
- Wrote Agent tool contracts
- Wrote Python contracts for future Engine and Agent implementation

Files:

- `docs/battle_analysis_architecture.md`
- `specs/battle_data_model.yaml`
- `specs/agent_tool_contracts.yaml`
- `battle_engine/contracts.py`

### 2026-04-13: Missing SSD Documents Added

Completed:

- Added canonical role taxonomy
- Added canonical archetype taxonomy
- Added scoring system spec
- Added change policy

Files:

- `specs/role_taxonomy.md`
- `specs/archetype_taxonomy.md`
- `specs/scoring_system.md`
- `specs/change_policy.md`

Notes:

- These docs define the project’s current SSD baseline
- `scoring_system.md` is the bridge between labels and deterministic implementation rules

### 2026-04-13: External PvP Domain Research Requested and Reviewed

Completed:

- Wrote an external research execution spec for a domain primer
- Staged the returned external research report and updated external dataset
- Reviewed the returned report and separated mechanism content from low-confidence meta claims
- Wrote the internal canonical domain primer

Files:

- `docs/domain_primer_research_spec.md`
- `docs/research/luoke_world_pvp_domain_primer_v2.md`
- `data/reference/luoke_world_type_database_v2.json`
- `docs/domain_primer.md`

Key Result:

- Mechanism content can be provisionally adopted into the project context
- Environment and meta claims must remain low-confidence references only

### 2026-04-13: Critical Mechanic Shift Identified

Important finding:

- External `v2` data and the external domain primer both assert that dual-type effectiveness is not multiplicative:
  - double super effective = `×3`
  - double resisted = `÷3`
  - super effective + resisted = `×1`

Impact:

- This conflicts with the earlier local assumption of standard multiplicative combination
- It is a breaking-change candidate for Phase 1
- It has not yet been integrated into the active local Engine implementation

Status:

- Accepted into the domain system as `Provisional mechanism`
- Not yet adopted into runtime logic

### 2026-04-13: Phase 1 Runtime Updated To New Dual-Type Baseline

Completed:

- Updated `specs/scoring_system.md` to explicitly reject multiplicative dual-type assumptions
- Updated `roco_world_model.py` so dual-type effectiveness now follows the accepted provisional rule:
  - `2x + 2x => 3.0`
  - `0.5x + 0.5x => 0.333...`
  - `2x + 0.5x => 1.0`
- Updated tests to reflect the new baseline

Files:

- `specs/scoring_system.md`
- `roco_world_model.py`
- `tests/test_roco_world_model.py`

Remaining uncertainty:

- The dual-type rule is still treated as a provisional domain mechanic pending higher-confidence external confirmation

### 2026-04-13: Phase 1 Team Structure Analyzer Implemented

Completed:

- Implemented deterministic team structure analysis for type-only teams
- Added defensive coverage table generation
- Added repeated weakness and missing resistance detection
- Added STAB-only offensive coverage summary
- Added patch-type suggestion ranking
- Added CLI entry point for Phase 1 analysis

Files:

- `battle_engine/team_structure.py`
- `battle_engine/phase1_cli.py`
- `tests/test_team_structure.py`

Notes:

- Offensive coverage is intentionally limited to represented team types in Phase 1 because no move-pool data exists yet
- Patch suggestions currently rank single types only, not species or dual-type inserts

### 2026-04-13: Phase 1 CLI Extended For Agent/Human Use

Completed:

- Added file-based input support for Phase 1 CLI
- Added JSON output mode for downstream agent/tool consumption
- Added example team fixture

Files:

- `battle_engine/phase1_cli.py`
- `examples/phase1_sample_team.json`
- `tests/test_team_structure.py`

Notes:

- The CLI now supports both ad hoc slot input and structured file input
- JSON mode is intended to reduce future integration friction with agents or APIs

### 2026-04-13: Phase 1 Patch Suggestions Extended To Type Combinations

Completed:

- Updated Phase 1 suggestion logic to rank both single-type and dual-type patch candidates
- Added a small complexity penalty so dual-type recommendations only rise when they materially improve structure
- Kept the feature within Phase 1 scope by recommending type combinations only, not species

Files:

- `specs/scoring_system.md`
- `battle_engine/team_structure.py`
- `tests/test_team_structure.py`

Notes:

- Suggested patch outputs may now include values like `火/地`
- Recommendation logic still uses only type-level evidence and STAB-only offensive assumptions

## Current Product Direction

### Confirmed Scope

Current active goal:

- Build `Phase 1` team defensive structure analysis

Required input:

- six team members
- each with one or two attributes

Expected output:

- defensive coverage summary
- repeated weakness detection
- missing resistance detection
- offensive coverage summary
- structural strengths and weaknesses

### Confirmed Non-goals

- No species database integration yet
- No frontend yet
- No live meta analysis yet

### Priority Order

1. Correctness
2. Stable spec and contract alignment
3. Explanation quality
4. Broader agent features

## Current Source-of-Truth Hierarchy

### Stable Internal Docs

- `docs/battle_analysis_architecture.md`
- `docs/domain_primer.md`
- `specs/battle_data_model.yaml`
- `specs/agent_tool_contracts.yaml`
- `specs/role_taxonomy.md`
- `specs/archetype_taxonomy.md`
- `specs/scoring_system.md`
- `specs/change_policy.md`

### External Research Inputs

- `docs/research/luoke_world_pvp_domain_primer_v2.md`
- `data/reference/luoke_world_type_database_v2.json`

Policy:

- External research inputs do not automatically become runtime truth
- They must be reviewed and then either:
  - adopted into internal specs, or
  - kept as low-confidence reference only

## Deferred / Parked Items

These items are intentionally parked and should not be forgotten.

### Community Meta Signal Ingestion

Context:

- A community-generated PVP weekly report was surfaced as a possible information source
- It may contain useful weak-signal data such as:
  - popular teams
  - ranking examples
  - emerging teams
  - popular species
  - community terminology

Current judgement:

- valuable as `community meta signal`
- not valid as hard truth
- should not directly enter Engine rules

Deferred action:

- define a dedicated spec for community meta signal ingestion and confidence tagging

Recommended future artifact:

- `specs/community_meta_sources.md`

### Phase 2 Species Database

Context:

- still needed for role analysis
- not needed for current Phase 1 execution

Deferred action:

- decide ingestion source strategy for species, abilities, moves, and learnsets

### Phase 3 Meta Snapshot System

Context:

- ultimately needed for serious environment analysis
- currently blocked by lack of trustworthy usage data

Deferred action:

- define the `meta_snapshot` ingestion pipeline once enough source quality exists

## Active Execution Focus

The project must now return to `Phase 1 SSD development`.

Immediate next step:

- update Phase 1 scoring and/or change specs to reflect the currently accepted provisional dual-type mechanic

Execution principle:

- do not widen scope into species database or meta ingestion before Phase 1 is stable

## Open Risks

- The provisional `×3 / ÷3` dual-type rule may still require higher-confidence verification
- If adopted, it will require coordinated changes across:
  - internal specs
  - type data
  - runtime calculation logic
  - tests
- Meta terminology may drift if community vocabulary is imported without controlled taxonomy mapping

## Maintenance Rule

Any meaningful decision, scope change, or deferred item should be appended here before or alongside implementation work.

## 2026-04-13 - Phase 1 Patch Suggestion Semantics Refined

Context:

- mixed single-type and dual-type patch suggestions were technically valid
- however, the output semantics were too aggressive for product use
- dual-type suggestions should not read like direct composition advice

Decision:

- Phase 1 now separates patch suggestions into two layers:
  - `primary_patch_types`
  - `conditional_dual_patch_types`
- single-type suggestions are the default recommendation layer
- dual-type suggestions are conditional guidance only:
  - "if an appropriate A/B species exists, consider it"

Implementation impact:

- updated scoring spec language
- updated runtime contract shape
- updated CLI report fields
- updated tests and serialization expectations

Reasoning:

- this preserves Phase 1 purity
- it avoids overclaiming at the type-combination layer
- it aligns the report semantics with the later product packaging direction

## 2026-04-13 - Report Layer Direction And Framework Decision

Context:

- discussion shifted from pure CLI output toward a product-grade report layer
- the intended top-level experience is moving toward a "battle advisor" / "battle master" concept
- concern was raised that a custom harness might become ad-hoc technical debt
- DeerFlow was considered as a possible direct runtime adoption

Decision:

- Phase 1.5 should introduce a constrained report / advisor harness
- deterministic Engine outputs remain the source of truth
- RAG is allowed only as context for explanation, not as replacement for Engine conclusions
- persona is a presentation skin only
- DeerFlow is rejected for the current milestone
- lightweight framework candidates may be reconsidered later, with PydanticAI as the strongest current candidate

Why:

- current product complexity is still report-centric, not runtime-centric
- heavy frameworks would likely shift effort toward orchestration infrastructure too early
- the correct next bottleneck is report schema and confidence policy, not multi-agent execution

Follow-up:

- formalize this in `docs/agent_framework_decision.md`
- next report-layer specs should define:
  - report schema
  - confidence policy
  - harness boundaries

## 2026-04-13 - Hybrid Route Approved

Context:

- the PM approved the hybrid direction after explicit comparison between:
  - pure custom harness
  - lightweight framework adoption
- the selected route is:
  - deterministic Engine remains fully custom
  - report / advisor harness adopts `PydanticAI`

Decision:

- `PydanticAI` is now the approved near-term orchestration layer for the report / advisor surface
- business contracts must remain runtime-independent
- the report layer must be specified before implementation begins

Artifacts created:

- `docs/agent_framework_decision.md`
- `specs/report_layer.md`
- `specs/report_schema.yaml`
- `specs/report_confidence_policy.md`

Reasoning:

- this gives the project typed structured generation and lightweight tool-capable interaction
- this avoids premature adoption of a heavyweight long-horizon runtime
- this reduces the risk of hand-written glue code expanding into accidental infrastructure

## 2026-04-13 - Model-Centric Option C Recorded

Context:

- a model-centric future architecture was raised as a serious possibility
- in that design, a sufficiently strong LLM would become the primary high-level advisor
- the concern was whether this should replace the current engine-first reasoning model

Decision:

- record Option C as a formal future architecture candidate
- do not approve it for current implementation
- define explicit preconditions before any future adoption discussion

Artifacts:

- `docs/model_centric_option_c.md`

Required preconditions captured there:

- stable structured data layer
- deterministic engine support for hard calculations
- harness validation and confidence controls
- real product need for multi-turn advisory synthesis
- sufficiently capable model quality

Why:

- this preserves the strategic option without derailing the current roadmap
- it prevents future re-litigation from devolving into vague "let the model handle it" discussion

## 2026-04-13 - Phase 1.5 Report MVP Implemented

Context:

- P0 required a clear SSD-driven implementation of the report / advisor layer
- the approved route was:
  - deterministic Engine remains custom
  - report / advisor harness uses PydanticAI
  - the MVP must still run locally even without live model access

Decision:

- implement a Phase 1.5 report service with two backends:
  - `deterministic`
  - `pydantic_ai`
- keep deterministic generation as the default local-safe path
- keep the PydanticAI backend optional but wired and dependency-declared

Artifacts created:

- `reporting/contracts.py`
- `reporting/knowledge.py`
- `reporting/generator.py`
- `reporting/validator.py`
- `reporting/service.py`
- `reporting/phase15_cli.py`
- `tests/test_reporting.py`
- `requirements.txt`

Supporting spec updates:

- `specs/agent_tool_contracts.yaml`
- `README.md`

Validation:

- all local tests pass
- local report CLI smoke test passes
- isolated `.venv` install confirms `pydantic_ai` import path and service import

Reasoning:

- this completes a usable P0 without blocking on external API keys
- it preserves the approved PydanticAI route
- it keeps report generation grounded by Engine output, curated retrieval, and validator checks

## 2026-04-13 - P1a Field Discovery Direction Locked

Context:

- schema planning risked importing assumptions from other games
- the PM explicitly flagged that some default fields, such as accuracy, may not even exist in 洛克王国世界
- wiki crawling had already been judged technically feasible, with the main difficulty in field convergence and cleaning

Decision:

- split P1 into:
  - `P1a`: field discovery and ontology alignment
  - later source strategy and schema work
- P1a remains battle-analysis only
- current entities are restricted to:
  - `species`
  - `move`
  - `ability`
- every candidate field must be tagged as:
  - `confirmed`
  - `provisional`
  - `forbidden_by_default`
- wiki is the primary structured source

Artifacts created:

- `docs/combat_ontology.md`
- `docs/data_source_strategy.md`
- `specs/field_alignment_matrix.yaml`

Reasoning:

- this prevents Pokemon-like schema contamination
- this keeps Phase 2 data work grounded in game-native evidence
- this lets ingestion start from clean field boundaries rather than from raw crawl volume

## 2026-04-13 - Wiki Field Discovery Spec Added

Context:

- after `P1a` alignment was accepted, the next execution question was whether wiki reconnaissance itself also needed a spec
- the answer was yes: discovery work needs execution boundaries before any crawler is written

Decision:

- add a dedicated discovery-spec artifact for wiki page reconnaissance
- keep it strictly scoped to field discovery, not ingestion

Artifact:

- `specs/wiki_field_discovery_spec.md`

Why:

- this prevents a reconnaissance script from turning into an unbounded crawler
- this keeps page sampling, evidence capture, and candidate-field aggregation aligned with `P1a`

## 2026-04-13 - Biligame Species Wiki Crawl Route Validated

Context:

- the PM requested a practical assessment of how hard it would be to crawl the rocom wiki species dex
- the key uncertainty was whether this would require brittle HTML scraping or whether the site exposed a cleaner structured path

Decision:

- treat the wiki as a `MediaWiki API + template parsing` target
- do not use frontend DOM scraping as the primary ingestion route
- do not use browser automation for current species discovery work

Verified findings:

- `https://wiki.biligame.com/rocom/精灵图鉴` is a rendered shell page, not the real source of truth
- the index delegates to subpages and `#ask` queries over `[[分类:精灵]]`
- species detail pages expose structured `{{精灵信息}}` templates in page wikitext
- anonymous `api.php` access works
- `分类:精灵` was observed at approximately `591` pages during this session
- category enumeration and batched revision fetches both returned `500` entries per request with continuation

Implication:

- species discovery should start from category enumeration and revision-content fetches
- the next correct implementation target is a `P1a` species field discovery script
- parsing should prefer a real wikitext/template parser over regex-only extraction

Artifact:

- `specs/爬session.md`

Why:

- this keeps the project aligned with the accepted `P1a` discovery scope
- this avoids building a brittle HTML crawler for a problem the API already solves
- this gives future threads a concrete continuation contract instead of requiring chat-history recovery

## 2026-04-13 - P1a Wiki Recon Script And Field Discovery Artifacts Created

Context:

- the PM requested execution of `specs/wiki_field_discovery_spec.md`
- the target was field discovery only, not database ingestion
- required outputs were raw page samples, candidate-field aggregation, field frequency, examples, confidence recommendations, and a findings memo

Implementation:

- added a bounded MediaWiki API recon tool
- used `mwparserfromhell` for wikitext/template extraction
- sampled species, move, and ability-relevant structures
- kept ability discovery evidence-backed by recording that standalone ability pages/categories were not found and that ability fields are embedded in species templates

Artifacts:

- `tools/wiki_field_discovery_recon.py`
- `data/wiki_field_discovery/2026-04-13/raw_page_samples.json`
- `data/wiki_field_discovery/2026-04-13/candidate_field_aggregate.json`
- `data/wiki_field_discovery/2026-04-13/findings_memo.md`
- `data/wiki_field_discovery/2026-04-13/run_metadata.json`

Key findings:

- sampled `9` species detail pages and `4` species index pages
- sampled `8` move detail pages and `2` move index pages
- sampled `9` ability embedded species-detail records
- discovered `47` aggregate candidate fields
- recommendations currently split into:
  - `25` confirmed
  - `10` provisional
  - `12` forbidden_by_default

Validation:

- script syntax validation passed
- generated JSON artifacts parse successfully
- full pytest suite was not run because the local `.venv` does not currently include `pytest`

Next action:

- review the aggregate artifact and update `specs/field_alignment_matrix.yaml` only where the recommendations are accepted
- do not begin production ingestion until move/ability entity modeling is explicitly approved

## 2026-04-13 - Session Handoff Files Split

Context:

- the project needed a handoff artifact for:
  - crawl-only continuation
  - full project continuation in a completely new thread

Decision:

- rename the crawl-specific handoff to:
  - `specs/爬session.md`
- create a full-project handoff at:
  - `specs/总session.md`

Why:

- this separates the crawl track from the total project state
- this reduces ambiguity when opening a new thread with a focused objective

## 2026-04-14 - Wiki Field Discovery Review Integrated Into SSD

Context:

- the crawl thread reported successful bounded wiki recon output
- the PM provided the run summary back to the main development thread
- the next required action was to review the artifacts and update SSD, not ingest data

Review result:

- confirmed the recon artifacts exist under `data/wiki_field_discovery/2026-04-13/`
- confirmed the field recommendation split:
  - `25` confirmed
  - `10` provisional
  - `12` forbidden_by_default
- accepted the key page-structure finding:
  - species uses `{{精灵信息}}`
  - move uses `{{技能信息}}`
  - ability is currently embedded in species fields `特性` / `特性描述`

Changes:

- updated `specs/field_alignment_matrix.yaml` from version `1` to version `2`
- promoted evidenced move fields `威力` and `耗能` to confirmed
- split raw names from normalized IDs:
  - raw ability names are confirmed
  - ability IDs remain provisional
  - raw move names are confirmed
  - move IDs remain provisional
- marked `dex_no` as provisional because current evidence is index-projection only
- updated `docs/combat_ontology.md` with source-model constraints from recon
- added `docs/wiki_field_discovery_review_2026-04-13.md`

Guardrails:

- do not model standalone ability pages unless stronger evidence appears
- keep `accuracy`, `PP`, and `cooldown` forbidden by default
- keep cosmetic and encyclopedia fields out of the battle schema

## 2026-04-14 - Defense Skill Cooldown Captured As Provisional Mechanic

Context:

- the PM clarified from gameplay experience that defense skills appear to have a default cooldown / reuse-lock rule
- this clarification affects mechanics modeling, but does not change the wiki source-field evidence from P1a

Captured rule:

- defense skills default to a `2` turn cooldown / reuse-lock and cannot be used in consecutive turns
- there is at least one special ground-type defense skill exception
- that exception reduces damage by `90%`
- if it successfully responds to an attack, cooldown is reduced by `1`

Decision:

- keep `move.cooldown` forbidden as a raw wiki field because sampled `{{技能信息}}` templates did not expose it
- add `defense_move_reuse_lock_rule` as a provisional mechanics rule in `specs/field_alignment_matrix.yaml`
- update `docs/domain_primer.md` with the provisional mechanism
- mark `specs/battle_data_model.yaml` as deprecated pre-P1a because it still contains imported assumptions such as `accuracy`, `PP`, and non-game-native move categories

## 2026-04-14 - P1b Minimal Battle Dex Schema Drafted

Context:

- after P1a field discovery was reviewed, the project needed a minimal schema before any formal crawl or ingestion
- the PM clarified that skill source channels should not fragment the first analysis layer; Engine should reason over a theoretical available move pool

Decision:

- create a raw-first, source-traceable battle dex schema
- keep source access channels in storage
- expose a unified `species_available_moves` view to Engine consumers
- model ability as `derived_ability` because current evidence is embedded in species pages, not standalone wiki pages
- keep defense cooldown as a provisional mechanics rule rather than a raw move field

Artifacts:

- `specs/p1b_minimal_battle_dex_schema.md`
- `specs/battle_dex_schema.yaml`

Open PM decisions:

- whether `derived_ability` should be materialized immediately in SQLite or generated as a view
- whether `source_version` belongs in the main move table or source metadata only
- whether bloodline moves are always included in enemy theoretical move pools

## 2026-04-14 - P1c Crawler And Cleaner Contract Drafted

Context:

- after P1b schema definition, the next blocker was a strict handoff contract for crawler and cleaner outputs
- the goal is to let a crawler thread generate artifacts without mutating SQLite or inventing fields

Decision:

- formalize a bounded dry-run artifact directory under `data/wiki_ingestion_runs/{run_id}/`
- require JSON/JSONL artifacts for source pages, raw templates, normalized candidates, validation events, rejected fields, and dry-run diff
- require raw field preservation and source trace for every normalized record
- keep ability crawling limited to embedded species fields unless a future discovery run proves standalone ability pages
- update Agent tool contract with `refresh_battle_dex` and mark `refresh_species_database` as legacy

Artifacts:

- `specs/p1c_crawler_cleaner_contract.md`
- `specs/wiki_crawler_cleaner_contract.yaml`
- updated `specs/agent_tool_contracts.yaml`

Gate:

- P1d may begin only after bounded P1c artifacts parse successfully and accepted records contain no hard rejects

Follow-up maintenance:

- updated `specs/爬session.md` so crawl-focused handoff points to P1c dry-run artifacts instead of obsolete P1a species discovery
- updated `specs/总session.md` so general handoff points to P1c/P1d rather than obsolete P1a field discovery

## 2026-04-14 - P1d Bounded Wiki Battle Dex Dry-Run Implemented

Context:

- after P1c contract definition, the project needed an executable dry-run tool that emits contract artifacts without mutating SQLite
- the implementation should reuse the existing MediaWiki API and template parsing approach

Implementation:

- added `tools/wiki_battle_dex_dry_run.py`
- added `tools/validate_p1c_artifacts.py`
- added helper tests in `tests/test_wiki_battle_dex_dry_run.py`
- the dry-run emits all required P1c artifacts under `data/wiki_ingestion_runs/{run_id}/`
- the dry-run preserves raw template snapshots and source trace
- species move access channels are preserved in storage artifacts while unresolved names remain visible for review
- ability candidates are derived from species `特性` / `特性描述`

Executed dry-run:

- run directory: `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run/`
- species detail limit: `5`
- move detail limit: `5`
- source pages: `10`
- species candidates: `5`
- move candidates: `5`
- derived ability candidates: `5`
- species move pool candidates: `226`
- hard rejects: `0`
- warnings: `229`
- unresolved move names: `154`
- ability conflicts: `0`

Validation:

- `python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run` passed
- `.venv/bin/python -m unittest discover -s tests` passed: `26` tests
- `python3 -m unittest discover -s tests` passed with dependency-gated skips for wiki dry-run helper tests

Operational note:

- Biligame API returned intermittent `567` server errors during immediate rerun attempts
- the dry-run tool now falls back from category enumeration to preferred titles when category listing fails
- avoid repeated immediate reruns; use bounded limits and sleep intervals

Next action:

- run a broader bounded dry-run when the wiki API is stable
- reduce unresolved move names by increasing move detail sample coverage
- only after that design SQLite ingestion dry-run

## 2026-04-14 - Bounded Dry-Run Request Prepared For External Session

Context:

- the PM requested a concrete requirement handoff for session `019d8685-2728-7c50-b102-59a5ee5f43ef`
- the target is a broader bounded `P1d` dry-run, not a full crawl
- SSD discipline must be preserved

Artifact:

- `specs/p1d_bounded_dry_run_request_019d8685.md`

Instructions captured:

- read current SSD files before execution
- run bounded dry-run with `species=50`, `move=200` if API is stable
- fall back to `species=30`, `move=50` with longer sleep if Biligame API returns `567`
- validate with `tools/validate_p1c_artifacts.py`
- run `.venv` tests
- report counts, hard rejects, warnings, unresolved move names, ability conflicts, and API stability
- do not mutate SQLite
- do not perform full production crawl

## 2026-04-14 - Bounded P1d Dry-Run Blocked By Biligame API 567

Context:

- executed the bounded P1d request from `specs/p1d_bounded_dry_run_request_019d8685.md`
- preferred command was attempted first:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --species-limit 50 --move-limit 200 --sleep-seconds 0.5 --run-id 2026-04-14Tbounded_p1d_s50_m200`
- Biligame API returned `567` during direct species page fetch after bounded internal retries
- fallback command was then attempted:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --species-limit 30 --move-limit 50 --sleep-seconds 1.0 --run-id 2026-04-14Tbounded_p1d_s30_m50`
- fallback hit the same `567` on the same direct species title batch

Result:

- no successful new P1d run was produced
- no new P1c artifact set was available for validation
- per SSD instruction, execution stopped instead of increasing retry pressure
- no SQLite mutation was performed

Operational note:

- Biligame API instability currently blocks broader bounded P1d dry-run execution
- next attempt should wait for API stability rather than adding aggressive retry logic

## 2026-04-14 - P1d Fetch Resilience Verification And Bounded Retry Completed

Context:

- the main thread added fetch-resilience changes after the earlier `567` failure
- crawl-thread ownership is now bounded online dry-runs, API stability handling, and artifact generation
- current task was to verify the implemented `P1d crawler v2` behavior and run a small bounded retry

Verification:

- confirmed `tools/wiki_battle_dex_dry_run.py` supports:
  - `--execution-mode fetch-clean`
  - `--execution-mode clean-only`
  - `--clean-input-dir`
  - `failure_reason`
  - `fetch_strategy`
  - API preflight / degraded fetch strategy hooks
- baseline artifact validation passed for:
  - `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run`
- offline cleaner validation passed for:
  - `data/wiki_ingestion_runs/2026-04-14Tclean_only_validation`

Executed online retry:

- command:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --execution-mode fetch-clean --species-limit 30 --move-limit 50 --sleep-seconds 1.0 --run-id 2026-04-14Tbounded_p1d_s30_m50_retry`
- run directory:
  - `data/wiki_ingestion_runs/2026-04-14Tbounded_p1d_s30_m50_retry`
- status:
  - `completed_with_warnings`
- fetch strategy:
  - `limited_categorymembers`
- failure reason:
  - `null`

Run counts:

- source pages: `80`
- raw template snapshots: `80`
- species form candidates: `30`
- move candidates: `50`
- derived ability candidates: `15`
- species move pool candidates: `1288`
- validation events: `1281`
- rejected fields: `326`
- unresolved move names: `285`
- ability conflicts: `0`
- hard rejects: `0`
- warnings: `1281`

Top validation event codes:

- `move_name_unresolved`: `1225`
- `empty_description_text`: `50`
- `missing_optional_field`: `3`
- `missing_ability_text`: `3`

Comparison with baseline:

- baseline unique unresolved move names: `154`
- retry unique unresolved move names: `285`
- absolute unresolved count increased because species sample expanded from `5` to `30`
- matched move-pool rows improved from `2/226` to `63/1288`
- move match rate improved from approximately `0.88%` to `4.89%`

Validation:

- `python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14Tbounded_p1d_s30_m50_retry` passed
- `.venv/bin/python -m unittest discover -s tests` passed: `27` tests
- `python3 -m unittest discover -s tests` passed: `27` tests, `6` skipped
- SQLite mutation was not performed

Next action:

- main thread should review the bounded retry artifacts before approving larger sampling
- if the goal is to reduce absolute unresolved move names, move coverage must grow faster than species coverage or use a move-seed strategy derived from unresolved species move names

Main-thread decision:

- accept the blocked result from session `019d8685-2728-7c50-b102-59a5ee5f43ef`
- do not attempt another broader online run immediately
- keep `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run/` as the latest successful baseline
- next safe work is either:
  - offline importer/schema work against the baseline artifacts
  - or a new SSD spec for polite/resumable fetching before another online run

## 2026-04-14 - P1d Fetch Resilience Requirements Accepted

Context:

- crawl session analysis concluded the blocked P1d run exposed crawler design issues beyond transient API failure
- current fallback reduced limits and sleep, but still used the same failing direct title batch
- failed runs did not emit failed manifests even though P1c allows `status=failed`

Decision:

- accept the crawl session's critique
- update P1c contract to require:
  - API preflight
  - bounded/limited category enumeration
  - detail fetch fallback from batch to smaller batch to single-title fetch
  - failed artifact emission
  - fetch/clean separation
  - no aggressive retry pressure after Biligame `567`

Artifacts updated:

- `specs/p1c_crawler_cleaner_contract.md`
- `specs/wiki_crawler_cleaner_contract.yaml`

## 2026-04-14 - P1d Fetch Resilience Implemented

Context:

- main thread implemented the fetch-resilience requirements accepted after the blocked Biligame `567` run
- implementation stayed bounded and did not retry the live Biligame API with larger limits

Changes:

- `tools/wiki_battle_dex_dry_run.py`
  - added API preflight before broader fetches
  - limited category enumeration to bounded sample size
  - added detail fetch degradation: batch `40` -> batch `10` -> single title
  - added failed artifact emission with `run_manifest.status=failed`
  - added `--execution-mode clean-only` for offline cleaner validation from cached snapshots
- `tools/validate_p1c_artifacts.py`
  - now requires `failure_reason` and `fetch_strategy` in `run_manifest.json`
- `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run/run_manifest.json`
  - updated with `failure_reason: null` and `fetch_strategy: limited_categorymembers`

Validation:

- `python3 -m py_compile tools/wiki_battle_dex_dry_run.py tools/validate_p1c_artifacts.py`
- `.venv/bin/python -m unittest discover -s tests`
- `python3 -m unittest discover -s tests`
- `python3 tools/validate_p1c_artifacts.py data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run`
- clean-only validation artifact set generated at `data/wiki_ingestion_runs/2026-04-14Tclean_only_validation/`
- failed-preflight validation artifact set generated at `data/wiki_ingestion_runs/2026-04-14Tfailed_preflight_validation/`

Result:

- cleaner/schema changes can now be validated offline against cached snapshots
- API preflight failure now produces contract-valid failed artifacts instead of an incomplete run
- next broader P1d retry should use the same bounded limits and only run when Biligame API is stable

## 2026-04-14 - Move Acquisition Channel Boundary Clarified

Context:

- PM clarified that move acquisition channels are not first-pass strategic distinctions for battle-team analysis
- a page such as `技能石/光刃` is acquisition evidence for canonical move `光刃`, not a separate battle move entity

Decision:

- canonical move battle semantics must come from `{{技能信息}}` when available
- preserve source channel in `species_move_pool.access_channel`
- Engine-facing `species_available_moves` unions `level_up`, `skill_stone`, and `bloodline` by default
- bloodline mutual-exclusion and acquisition legality are deferred to a later legality layer

Artifacts updated:

- `docs/combat_ontology.md`
- `specs/battle_dex_schema.yaml`
- `specs/p1b_minimal_battle_dex_schema.md`
- `specs/p1c_crawler_cleaner_contract.md`
- `specs/wiki_crawler_cleaner_contract.yaml`
- `specs/field_alignment_matrix.yaml`
- `tools/wiki_battle_dex_dry_run.py`
- `tests/test_wiki_battle_dex_dry_run.py`

## 2026-04-14 - Move-Full Bounded Dry-Run Approved

Context:

- unresolved move names in current artifacts are dominated by insufficient move detail coverage
- expanding species first would increase unresolved noise
- fuller move dictionary coverage should make later species move-pool matching more meaningful

Decision:

- approve a move-first P1d dry-run under artifact-only constraints
- scope is limited to `分类:技能` and pages with `{{技能信息}}`
- do not expand species crawl in this task
- no SQLite mutation
- no standalone ability pages

Artifact:

- `specs/p1d_move_full_bounded_dry_run_request.md`

Required crawl-thread report:

- move count
- hard rejects
- category distribution
- empty descriptions
- invalid numeric fields
- API stability
- validation and test results

## 2026-04-14 - Policy B Accepted After Move-Full And Species-Full Dry-Runs

Context:

- crawl thread completed move-full and species-full(cached moves) artifact-only dry-runs
- current recommendation is to accept data-source policy B:
  - wiki canonical + manual verified supplement

Main-thread confirmation:

- accept manual supplement as a formal future resolver/importer input layer
- exclude the current 10 hidden special plot forms from the current battle dex target
- treat future same-pattern pages as `human-review-before-ingest`
- accept the current 4 manual supplement items:
  - `湿润印记`
  - `溶解液`
  - `龙之舞`
  - `溶解扩散`
- accept 印记 system baseline rules into a later mechanics / Agent supplement layer, not into raw wiki schema
- defer importer / SQLite next-step approval until these rules are reflected in resolver/importer design

Artifacts updated:

- `docs/data_source_strategy.md`
- `docs/manual_battle_data_supplement_2026-04-14.md`

Implication:

- importer work is no longer blocked on whether manual supplement is allowed
- importer work remains blocked on how policy B precedence, exclusion gates, and mechanics supplement boundaries are implemented

## 2026-04-14 - Resolver/Importer Contract Drafted

Context:

- main thread accepted policy B and needed to convert that approval into an implementation-facing contract
- importer work could not safely begin until precedence, exclusion gates, and provenance rules were explicit

Artifacts:

- `specs/change_specs/policy_b_resolver_importer_change_spec.md`
- `specs/resolver_importer_contract.md`

Result:

- policy B is now elevated from strategic approval to an implementation-facing SSD artifact
- next implementation step should be importer dry-run design, not direct SQLite writes

## 2026-04-14 - P1e Importer Dry-Run Spec Added

Context:

- after the resolver/importer contract was drafted, the next no-decision step was to define the first implementation target clearly

Artifact:

- `specs/p1e_importer_dry_run_spec.md`

Result:

- the project now has a concrete dry-run deliverable shape for the first importer implementation
- future implementation threads can start from dry-run outputs instead of inferring requirements from discussion history

## 2026-04-14 - P1e Importer Dry-Run Implemented

Context:

- after P1e dry-run requirements were specified, the next executable step did not require PM input
- implementation target was an offline importer dry-run consuming wiki canonical artifacts plus manual supplement under policy B

Artifacts:

- `tools/import_battle_dex_dry_run.py`
- `tools/validate_p1e_importer_artifacts.py`
- `tests/test_import_battle_dex_dry_run.py`
- `specs/agent_tool_contracts.yaml`

Validation:

- `python3 -m py_compile tools/import_battle_dex_dry_run.py tools/validate_p1e_importer_artifacts.py`
- `.venv/bin/python -m unittest discover -s tests`
- `python3 -m unittest discover -s tests`
- real dry-run executed:
  - `python3 tools/import_battle_dex_dry_run.py --canonical-artifact-dir data/wiki_ingestion_runs/2026-04-14Tspecies_full_cached_moves_p1d --supplement-path docs/manual_battle_data_supplement_2026-04-14.md --run-id 2026-04-14Tpolicy_b_importer_dry_run --output-dir data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`
- dry-run artifacts validated:
  - `python3 tools/validate_p1e_importer_artifacts.py data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`

Observed output:

- `resolved_species_forms`: `580`
- `resolved_moves`: `494`
- `resolved_derived_abilities`: `180`
- `excluded_entities`: `10`
- `review_required_entities`: `0`
- `supplement_backed_entities`: `4`
- `unresolved_entities`: `0`

Interpretation:

- policy B resolution now executes offline and reviewably
- hidden-form exclusions are being surfaced explicitly
- manual supplement currently closes the remaining unresolved move gap
- no SQLite mutation occurred

## 2026-04-14 - Move-Only Scope Implemented And Move-Full Dry-Run Executed

Context:

- the existing P1d crawler fetched species and moves together
- a move-first run needed to crawl only `分类:技能` / `{{技能信息}}`

Changes:

- `tools/wiki_battle_dex_dry_run.py`
  - added `--scope battle-dex|move`
  - default remains `battle-dex`
  - `--scope move` fetches only move detail pages
  - species, derived ability, and species move-pool artifact files still exist but are empty
  - manifest reports `scopes: ["move"]` and zero species/ability limits
- `tests/test_wiki_battle_dex_dry_run.py`
  - added coverage for move-only manifest scope and limits

Validation:

- baseline artifact validation passed for `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run`
- `.venv/bin/python -m unittest discover -s tests` passed: `29` tests
- move-only probe passed:
  - run directory: `data/wiki_ingestion_runs/2026-04-14Tmove_only_probe_m5`
  - source pages: `5`
  - move candidates: `5`
  - species/ability/species_move_pool candidates: `0`
  - unresolved move names: `0`

Move-full dry-run:

- command:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --execution-mode fetch-clean --scope move --move-limit 10000 --sleep-seconds 1.0 --run-id 2026-04-14Tmove_full_bounded_p1d`
- run directory:
  - `data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d`
- status:
  - `completed_with_warnings`
- failure reason:
  - `null`
- fetch strategy:
  - `limited_categorymembers`
- source pages:
  - `491`
- move candidates:
  - `491`
- species form candidates:
  - `0`
- derived ability candidates:
  - `0`
- species move-pool candidates:
  - `0`
- hard rejects:
  - `0`
- warnings:
  - `490`
- validation events:
  - `empty_description_text`: `489`
  - `unexpected_source_field`: `1`
- category distribution:
  - `物攻`: `174`
  - `状态`: `139`
  - `魔攻`: `132`
  - `防御`: `46`
- empty descriptions:
  - `489`
- invalid numeric fields:
  - `0`

Schema drift observation:

- page `强制重启` used source field `版本` instead of `技能版本`
- raw snapshot preserved the field
- normalized `source_version` remains null for that page until main-thread contract approves an alias

Operational result:

- artifact validator passed for `data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d`
- `.venv` unit tests passed after the run
- no standalone ability pages were crawled
- SQLite mutation was not performed
- Biligame API was stable during this run; no `567` observed

## 2026-04-14 - Species Scope With Cached Move Dictionary Executed

Context:

- full move dictionary artifacts already existed at `data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d`
- repeating online move fetches would add no value and would increase API pressure

Changes:

- `tools/wiki_battle_dex_dry_run.py`
  - added `--scope species`
  - added `--cached-move-input-dir`
  - species scope now fetches species detail pages online and loads cached move source pages / snapshots locally
  - cached move source pages are cloned into the new run and rebuilt into local `move_candidates`
- `tests/test_wiki_battle_dex_dry_run.py`
  - added species-scope manifest tests
  - added cached move artifact loading test
- new request spec:
  - `specs/p1d_species_cached_move_bounded_dry_run_request.md`

Validation:

- `.venv/bin/python -m unittest discover -s tests` passed: `31` tests
- `python3 -m py_compile tools/wiki_battle_dex_dry_run.py tools/validate_p1c_artifacts.py` passed

Species + cached-moves dry-run:

- command:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --execution-mode fetch-clean --scope species --cached-move-input-dir data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d --species-limit 50 --sleep-seconds 1.0 --run-id 2026-04-14Tspecies_cached_moves_s50`
- run directory:
  - `data/wiki_ingestion_runs/2026-04-14Tspecies_cached_moves_s50`
- status:
  - `completed_with_warnings`
- failure reason:
  - `null`
- fetch strategy:
  - `cached_source_pages,limited_categorymembers`
- source pages:
  - `541`
  - `491` cached move pages
  - `50` online species pages
- species form candidates:
  - `50`
- move candidates:
  - `491`
- derived ability candidates:
  - `24`
- species move-pool candidates:
  - `2059`
- unresolved move names:
  - `1`
  - `龙之舞`
- ability conflicts:
  - `0`
- hard rejects:
  - `0`
- warnings:
  - `505`

Top validation event codes:

- `empty_description_text`: `489`
- `missing_optional_field`: `7`
- `missing_ability_text`: `7`
- `unexpected_source_field`: `1`
- `move_name_unresolved`: `1`

Operational result:

- artifact validator passed for `data/wiki_ingestion_runs/2026-04-14Tspecies_cached_moves_s50`
- no online move-page fetch was required for this run
- SQLite mutation was not performed
- API was stable during this run

## 2026-04-14 - Full Species Crawl With Cached Move Dictionary Executed

Context:

- move dictionary was already available from `data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d`
- the next validation target was full species coverage without repeating online move fetches

Execution:

- command:
  - `.venv/bin/python tools/wiki_battle_dex_dry_run.py --execution-mode fetch-clean --scope species --cached-move-input-dir data/wiki_ingestion_runs/2026-04-14Tmove_full_bounded_p1d --species-limit 10000 --sleep-seconds 1.0 --run-id 2026-04-14Tspecies_full_cached_moves_p1d`
- run directory:
  - `data/wiki_ingestion_runs/2026-04-14Tspecies_full_cached_moves_p1d`

Result:

- status:
  - `completed_with_warnings`
- failure reason:
  - `null`
- fetch strategy:
  - `cached_source_pages,limited_categorymembers`
- source pages:
  - `1081`
  - `590` online species pages
  - `491` cached move pages
- species form candidates:
  - `580`
- move candidates:
  - `491`
- derived ability candidates:
  - `181`
- species move-pool candidates:
  - `22071`
- unresolved move names:
  - `3`
  - `湿润印记`
  - `溶解液`
  - `龙之舞`
- ability conflicts:
  - `1`
  - `溶解扩散`
- hard rejects:
  - `10`
  - all were species pages missing required base stat `生命`
- warnings:
  - `731`

Top validation event codes:

- `empty_description_text`: `489`
- `missing_optional_field`: `104`
- `missing_ability_text`: `104`
- `unexpected_source_field`: `27`
- `missing_required_field`: `10`
- `move_name_unresolved`: `4`
- `invalid_numeric_value`: `2`
- `ability_description_conflict`: `1`

Hard reject pages:

- `炽心勇狮（悲鸣的样子）`
- `炽焰狮（悲鸣的样子）`
- `圣羽翼王（被噩梦侵蚀的样子）`
- `松仔（悲鸣的样子）`
- `松叶羊（悲鸣的样子）`
- `水滴蛇（悲鸣的样子）`
- `水蛇锁（悲鸣的样子）`
- `小勇狮（悲鸣的样子）`
- `游蛇魔使（悲鸣的样子）`
- `针叶巡林（悲鸣的样子）`

Other observations:

- `里奥` and `灵羽勇士` exposed `技能解锁等级=legendary`; this was emitted as warning `invalid_numeric_value` with null unlock level
- `2058 / 2059` species move-pool rows matched a cached move ID in the earlier bounded species run, but full-species run still leaves three unresolved unique move names
- full-species run now exposes a real ability-text conflict for `溶解扩散`

Operational result:

- artifact validator passed for `data/wiki_ingestion_runs/2026-04-14Tspecies_full_cached_moves_p1d`
- `.venv` tests passed after the run
- no online move-page fetch was required
- SQLite mutation was not performed
- API was stable during this run; no `567` observed

Contract implication:

- because `hard_reject_count > 0`, importer work should stop pending main-thread review of the rejected species pages and handling policy

## 2026-04-14 - Manual Battle Supplement Layer Started

Context:

- PM confirmed that the 10 hard-reject hidden special forms should be excluded from the current battle dex target rather than patched with missing stats
- PM also provided manual move/mechanics corrections for some unresolved names that the wiki crawl did not resolve cleanly

Decision:

- keep wiki canonical crawl artifacts unchanged
- record PM knowledge in a separate manual supplement layer
- require human review before auto-including future hidden special forms that are not visible in the human-facing dex path

Artifact:

- `docs/manual_battle_data_supplement_2026-04-14.md`

Recorded manual supplement items:

- excluded hidden forms:
  - `炽心勇狮（悲鸣的样子）`
  - `炽焰狮（悲鸣的样子）`
  - `圣羽翼王（被噩梦侵蚀的样子）`
  - `松仔（悲鸣的样子）`
  - `松叶羊（悲鸣的样子）`
  - `水滴蛇（悲鸣的样子）`
  - `水蛇锁（悲鸣的样子）`
  - `小勇狮（悲鸣的样子）`
  - `游蛇魔使（悲鸣的样子）`
  - `针叶巡林（悲鸣的样子）`
- manual move supplements:
  - `湿润印记`
  - `龙之舞`
  - `溶解液` partial, move type still pending
- manual mechanics notes:
  - 印记 system baseline notes

Pending:

- human-confirmed current text for `溶解扩散` and move type for `溶解液` were later supplied by PM

Follow-up clarification:

- `溶解扩散` current manual-verified text:
  - `每携带1个毒系技能，水系技能使敌方中毒+1层。`
- `溶解液` move type:
  - `毒`

Unreleased form exclusion clarification:

- PM confirmed `卡瓦重（火山附近的样子）` is not live in the current game build.
- Treat this form as excluded from the current battle dex ingest target, not merely low-confidence.
- Importer dry-run policy was tightened so explicitly excluded forms do not remain in `resolved_species_forms`.
- Current included `卡瓦重` forms remain:
  - `卡瓦重|草地附近的样子`
  - `卡瓦重|沙地附近的样子`
  - `卡瓦重|雪山附近的样子`

## 2026-04-14 - Structured Supplement And SQLite Write Spec

Context:

- markdown-only manual supplement parsing would become a long-term importer fragility
- SQLite write work needed a formal boundary before any real database mutation

Decision:

- promote the manual supplement into a structured importer-facing artifact
- keep markdown as the human-readable briefing layer
- define the first SQLite DDL and write-path contract, but do not authorize writes yet

Artifacts:

- `specs/manual_battle_data_supplement_schema.yaml`
- `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
- `tools/export_manual_battle_data_supplement.py`
- `specs/p1f_sqlite_write_path_spec.md`
- `specs/battle_dex_sqlite_schema_v1.sql`

Implementation notes:

- `tools/import_battle_dex_dry_run.py` now prefers structured YAML/JSON supplement input and keeps markdown parsing as compatibility-only
- importer manifest now records `supplement_format`
- `tools/validate_p1e_importer_artifacts.py` now requires the new manifest field

Validation:

- `.venv/bin/python -m unittest discover -s tests`
- `python3 tools/import_battle_dex_dry_run.py --canonical-artifact-dir data/wiki_ingestion_runs/2026-04-14Tspecies_full_cached_moves_p1d --supplement-path data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml --run-id 2026-04-14Tpolicy_b_importer_dry_run --output-dir data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`
- `python3 tools/validate_p1e_importer_artifacts.py data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`
- SQLite schema smoke-tested in memory via `sqlite3.executescript`

## 2026-04-14 - SQLite Write Path Implemented

Context:

- policy B importer dry-run reached `unresolved_entities = 0`
- the project needed a real write-path to prove the schema is not paper architecture
- write-path validation exposed an upstream importer bug: duplicate canonical `species_id` rows for `权杖-V`

Decision:

- implement a dedicated P1f write-input validator before any SQLite write
- implement a transactional SQLite write tool with staging tables and deterministic upsert behavior
- tighten importer dry-run so duplicate canonical species ids are moved to `review_required` instead of guessed into `included`

Artifacts:

- `tools/validate_p1f_write_inputs.py`
- `tools/import_battle_dex_sqlite.py`
- `tests/test_import_battle_dex_sqlite.py`

Conflict handling update:

- `权杖-V` appeared from two wiki pages under the same canonical `species_id`
- because semantic fields conflicted (`II阶` vs `最终形态`), the importer now treats that entity as `review_required`
- current importer dry-run counts became:
  - `resolved_species_forms = 565`
  - `review_required_entities = 14`

Validation:

- `.venv/bin/python -m unittest discover -s tests`
- `python3 tools/validate_p1f_write_inputs.py data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run`
- `python3 tools/import_battle_dex_sqlite.py --importer-run-dir data/importer_runs/2026-04-14Tpolicy_b_importer_dry_run --db-path /tmp/roco_battle_dex_smoke.sqlite --write-run-id 2026-04-14Tpolicy_b_write_smoke`

Smoke result:

- `species_form = 565`
- `move = 494`
- `derived_ability = 180`
- `species_move_pool = 21924`
- `excluded_resolutions = 11`
- `review_required_resolutions = 14`
- `卡瓦重（火山附近的样子）` not present in final `species_form`

## 2026-04-14 - Minimal DB Sync Context Prepared For Crawl Thread

Context:

- database-side work now affects how crawl artifacts are interpreted downstream
- crawl thread should know the current importer/write baseline, but should not inherit unrelated Agent-surface decisions

Artifact:

- `specs/p1f_db_sync_min_ctx_for_crawl.md`

Key sync points:

- current importer dry-run baseline is `565 / 494 / 180` with `14` review-required entities
- duplicate canonical `species_id` collisions are now importer review gates, not auto-merge candidates
- current example: `权杖-V`

## 2026-04-14 - Placeholder Zero-Stat Species Batch Excluded

Context:

- PM reviewed the current `review_required` list and confirmed the placeholder all-zero species batch should be treated as non-live or cut content for the present product target
- only `权杖-V / 权杖-Ⅴ` remains as a true canonical-resolution issue

Decision:

- promote the 12 placeholder all-zero species pages from `review_required` to explicit manual exclusions
- keep `千棘海刺` excluded for the current formal version as well

Result after importer rerun:

- `resolved_species_forms = 565`
- `resolved_moves = 494`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 2`
- `unresolved_entities = 0`

Remaining review-required entities:

- `权杖-V`
- `权杖-Ⅴ`

Investigation note:

- both `权杖-V` and `权杖-Ⅴ` have full wiki detail pages
- the newer `权杖-Ⅴ` page has later revision timestamp and `更新版本 = 0.6`
- the older `权杖-V` page has `更新版本 = 0.1`
- both normalize to the same canonical `species_id`, but disagree on `精灵阶段` (`Ⅱ阶` vs `最终形态`)
- current importer therefore still keeps this pair in `review_required` rather than guessing

## 2026-04-14 - 权杖-V Canonical Override Accepted

Context:

- PM confirmed the `权杖-V / 权杖-Ⅴ` split is not a real gameplay distinction
- the difference is treated as naming / maintainer-style noise
- the final ingested record only needs to match the in-game dex baseline

Decision:

- add a structured manual species canonical override for `species_3d2f11185009b67c`
- prefer source page `source_bc1c2be5441bb830`
- normalize output to:
  - `display_name = 权杖-V`
  - `initial_species_name = 权杖-II`
  - `evolution_stage = 最终形态`
- preserve both wiki source refs in provenance instead of dropping the older page silently

Implementation:

- extend manual supplement schema with `species_canonical_overrides`
- add the override to `docs/manual_battle_data_supplement_2026-04-14.md`
- export it into `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
- update `tools/import_battle_dex_dry_run.py` to resolve duplicate playable species pages through an explicit supplement override

Result after importer rerun:

- `resolved_species_forms = 566`
- `resolved_moves = 494`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 0`
- `supplement_backed_entities = 5`
- `unresolved_entities = 0`

Operational note:

- duplicate canonical collisions remain review-gated by default
- `权杖-V` is now a narrow approved exception, not a general auto-merge rule

## 2026-04-14 - Review Backlog Closed And Agent-State Clarified

Context:

- the importer review backlog had to be fully closed before advisor-surface decisions could be made cleanly
- documentation had also drifted on one point: some files still implied that `PydanticAI` was not instantiated at all

Review closure result:

- current importer dry-run is now:
  - `resolved_species_forms = 566`
  - `resolved_moves = 494`
  - `resolved_derived_abilities = 180`
  - `excluded_entities = 23`
  - `review_required_entities = 0`
  - `supplement_backed_entities = 5`
  - `unresolved_entities = 0`
- write-input validation is green
- SQLite smoke write is green

Agent/runtime clarification:

- the repo already contains a narrow `Phase 1.5` report harness:
  - `reporting/service.py`
  - `reporting/generator.py`
  - `reporting/phase15_cli.py`
- this harness supports:
  - deterministic report generation
  - optional `PydanticAI` narrative generation
  - curated snippet retrieval from approved project documents
- this harness does **not** yet constitute the approved target product runtime because it still lacks:
  - a conversational Agent CLI
  - session state handling for multi-turn advice
  - species-level semantic role tools
  - team-semantic tools beyond Phase 1.5 report shaping
  - a proper battle-dex-backed retrieval path over SQLite

Decision-support framing for the next PM call:

- current database is a usable structured battle-dex substrate, not a finished RAG system
- current `reporting/` code is a partial PydanticAI foothold, not the final Agent shell
- the next product-facing milestone should target a conversational Agent CLI rather than more ingestion work unless a data blocker reappears

## 2026-04-14 - Lightweight RAG And Tactical Casebank Direction Confirmed

Context:

- PM asked whether the current SQLite battle dex already counts as RAG and whether the next product stage should move toward a lightweight advisor Agent
- the answer is yes for `Agent + lightweight RAG`, but no for “current system already is a full RAG stack”

Clarified system shape:

- current battle dex = `RAG-ready substrate`
- current retrieval in `reporting/knowledge.py` = curated snippet selector, not a complete retrieval layer
- target advisor = `conversational Agent CLI`
- target retrieval = `hybrid local RAG`

Approved retrieval split:

- `structured retrieval`
  - SQLite battle-dex facts
  - species / moves / abilities / learnsets / provenance
- `doc retrieval`
  - mechanics notes
  - domain primer
  - taxonomy / scoring / confidence policy
- `case retrieval`
  - representative tactical team cases
  - representative species set examples
  - used as role / archetype priors rather than encyclopedic truth

Important role-understanding decision:

- the system should not try to memorize one canonical usage for every species
- the tactical casebank exists to teach the Agent what resource patterns usually imply:
  - what kinds of stats / move pools / abilities tend to support what roles
  - how the same species may occupy different roles in different teams
  - how different sets of the same species may imply different tactical positions

Constraint:

- early semantic role judgement is allowed
- but it must be:
  - evidence-backed
  - uncertainty-bearing
  - team-conditional
  - weaker in trust than deterministic structure analysis

Next SSD implication:

- stop expanding ingestion by default
- move next into:
  - advisor runtime spec
  - retrieval architecture spec
  - tactical casebank spec
  - conversation CLI spec

## 2026-04-14 - SQL vs Embedding Retrieval Boundary Recorded

Context:

- PM requested a precise explanation of `SQL`, `embedding`, and whether the project will later need embeddings
- this distinction matters because the next advisor architecture should not confuse fact lookup with semantic retrieval

Decision:

- keep `SQL-first` for structured battle-dex facts
- reserve `embedding` primarily for document and tactical-case retrieval once those corpora justify it
- do not treat the presence of SQLite as equivalent to a complete RAG system

Practical split:

- `SQL`
  - exact fact lookup
  - filtering, sorting, aggregation, joins
  - examples: stats, types, move pool membership, ability text, provenance
- `embedding retrieval`
  - semantic similarity over non-structured or weakly structured text
  - examples: mechanics explanations, tactical case analogies, role/archetype prior retrieval

Project implication:

- the next advisor should launch even if doc retrieval initially uses curated/keyword retrieval only
- embeddings are likely a later improvement for docs and casebank, not a prerequisite for the first conversational Agent CLI

## 2026-04-15 - Agent MVP Implementation Handoff Prepared

Context:

- the current thread has converged architecture and SSD enough to justify a fresh implementation-focused thread
- continuing implementation inside the current long thread would increase context pollution risk

Artifact:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_mvp_impl_handoff.md`

Purpose:

- provide a clean implementation handoff for the next thread
- keep it focused on:
  - battle-dex repository
  - doc retrieval
  - advisor runtime skeleton
  - conversational Agent CLI

## 2026-04-15 - Native Runtime Audit Handoff Prepared

Context:

- after `pydantic_ai_native` integration, the highest-risk concern is no longer feature absence
- the highest-risk concern is contract drift:
  - deterministic/native output mismatch
  - failure-path weakness
  - runtime silently expanding scope

Artifact:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/native_runtime_audit_handoff.md`

Purpose:

- support a fresh thread positioned explicitly as a `project test / audit thread`
- keep its scope narrow:
  - parity
  - failure paths
  - scope discipline

## 2026-04-15 - Advisor Contract Hardening Specs Added

Context:

- after Agent MVP implementation, the main-thread priority is contract hardening rather than GUI work
- the key missing pieces were:
  - advisor response contract
  - retrieval evaluation spec
  - semantic role policy
  - battle-dex repository contract

Artifacts added:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_response_contract.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_eval_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/semantic_role_policy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md`

Intent:

- give deterministic/native parity a concrete contract target
- define how retrieval quality is judged
- define what semantic role output is allowed, downgraded, or refused
- stop runtime code from growing uncontrolled ad hoc SQL access

## 2026-04-15 - Queen Bee Chain Supplement Corrected

Context:

- PM provided a screenshot showing the current playable `花魁蜂后 -> 女王蜂` chain uses:
  - `花魁蜂后 / 虫群突袭 / 攻防速+10%`
  - `女王蜂 / 虫群鼓舞 / 攻防速+15%`
- this conflicts with the current wiki pages, which invert the practical strength ordering on the ability text side

Changes:

- updated `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/manual_battle_data_supplement_2026-04-14.md`
- regenerated `/Users/okfin3/project/GitHub/OKFin33/Roco/data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`
- extended `species_canonical_overrides` to allow species-scoped `override_ability_name` / `override_ability_effect_text`
- importer dry-run now applies those species-scoped overrides to resolved species rows
- removed `湿润印记` from manual move supplements after PM clarified the canonical move is `打湿` and `湿润印记` is the印记/effect name

Validation:

- `.venv/bin/python -m unittest tests.test_import_battle_dex_dry_run` passed
- `python3 -m py_compile tools/import_battle_dex_dry_run.py tools/export_manual_battle_data_supplement.py` passed
- new importer dry-run:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-15Tqueenbee_correction_dry_run`

Observed result:

- `resolved_species_forms` now shows:
  - `花魁蜂后` as supplement-backed with `虫群突袭 +10%`
  - `女王蜂` as supplement-backed with `虫群鼓舞 +15%`
- `湿润印记` now remains as the single unresolved move reference instead of being incorrectly promoted to a canonical move supplement

Residual caveat:

- `resolved_derived_abilities` still reflects wiki-derived ability text grouping by ability name
- therefore `虫群鼓舞` in the derived-ability layer still shows the wiki-consistent `+10%` variant
- fixing that cleanly requires a later main-thread decision on whether ability entities are global-by-name or may vary by species/stage

Correction:

- PM later clarified the exact chain should be:
  - `一窝蜂 / 黄蜂后 / 花魁蜂后 = 虫群鼓舞 +10%`
  - `女王蜂 = 虫群突袭 +15%`
- the earlier intermediate correction (`花魁蜂后 = 虫群突袭 +10%`, `女王蜂 = 虫群鼓舞 +15%`) was superseded and should be treated as stale

Updated artifact:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-15Tqueenbee_chain_corrected_dry_run`

Final alignment:

- importer no longer resolves `derived_abilities` directly from stale wiki ability candidates
- it now rebuilds the final ability layer from `resolved_species_forms`, then falls back to raw wiki ability candidates only for names not present in resolved species data
- this keeps species-scoped supplement corrections and the derived-ability layer in sync
- importer-side ability grouping now also tolerates punctuation-only text drift such as `,` vs `，`

Validated aligned artifact:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-15Tqueenbee_ability_layer_aligned_v2_dry_run`

Aligned result:

- `resolved_species_forms`
  - `花魁蜂后 = 虫群鼓舞 +10%`
  - `女王蜂 = 虫群突袭 +15%`
- `resolved_derived_abilities`
  - `虫群鼓舞 = +10%` with source species `一窝蜂 / 黄蜂后 / 花魁蜂后`
  - `虫群突袭 = +15%` with source species `女王蜂`
- counts returned to:
  - `resolved_derived_abilities = 180`
  - `unresolved_entities = 1`
  - remaining unresolved entity = species move reference `湿润印记`

Final alias resolution:

- added explicit manual move alias rule:
  - `湿润印记 -> 打湿`
- this alias is importer/resolver-only and does not mutate raw wiki crawl artifacts
- rationale:
  - PM confirmed `湿润印记` is the印记/effect name
  - canonical move already exists in move dex as `打湿`
  - current known stale source occurrence came from the excluded `千棘海刺` page

Final full-library dry-run after alias:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/importer_runs/2026-04-15Tfull_policy_b_alias_checked_dry_run`

Final counts:

- `resolved_species_forms = 566`
- `resolved_moves = 493`
- `resolved_derived_abilities = 180`
- `excluded_entities = 23`
- `review_required_entities = 0`
- `supplement_backed_entities = 9`
- `unresolved_entities = 0`

## 2026-04-15 - LLM Wiki / RAG Necessity Review Memo Prepared

Context:

- PM asked whether the project really needs a full `LLM Wiki`, Markdown page layer, or vector RAG layer
- current evidence suggests most near-term advisor queries should use structured battle-dex lookup, not embedding retrieval

Artifact:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md`

Recommendation:

- near-term target should be `Agent-ready structured KB`
- keep `hybrid local RAG` wording only if interpreted as:
  - structured facts first
  - curated text second
  - embeddings later and only for docs/cases when justified
- defer full Markdown entity-page generation
- defer full LLM Wiki platform work
- if needed, implement only lightweight LLM maintenance jobs:
  - review memo generator
  - drift summary generator
  - mechanics gap detector

Reason:

- recent `花魁蜂后 -> 女王蜂` correction proves stale wiki text can mislead naive RAG
- resolver/supplement/provenance path is higher trust for exact battle facts

## 2026-04-15 - Native runtime audit follow-up hardening

Implemented code-only fixes against the project test/audit thread findings. Scope unchanged; this was runtime hardening and parity repair only.

Files changed:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/battle_dex.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`

Applied fixes:

- native species query validator now accepts clean typed refusal when `get_species_profile` returns `species_not_found:*`
- native species miss is normalized into bounded refusal text instead of retry/fail loop
- native provider/model/runtime exceptions are wrapped into bounded advisor responses
- battle-dex repository no longer reuses a shared SQLite connection across native tool execution; queries now use per-call connections
- native species evidence parity now includes SQL-backed ability evidence when available
- native team confidence-note parity now includes the provisional dual-type-baseline warning

Validation:

- `python3 -m py_compile advisor/runtime.py advisor/battle_dex.py tests/test_advisor.py`
- `.venv/bin/python -m unittest tests.test_advisor`
- `.venv/bin/python -m unittest discover -s tests`

Observed result:

- targeted advisor tests: `Ran 11 tests`, `OK`
- full suite: `Ran 49 tests`, `OK`

## 2026-04-15 - Runtime hygiene follow-up handoff

Created a separate implementation/test-thread handoff for the remaining runtime
hygiene work:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/runtime_hygiene_followup_handoff.md`

Task allocation is now explicit:

- `sqlite3 ResourceWarning`定位与修复 belongs to implementation/test thread
- native parity / failure-path rerun belongs to test thread
- deciding whether `pydantic_ai_native` becomes the default CLI backend remains
  a main-thread decision
- implementation/test thread may update execution logs, but product/runtime
  strategy spec changes stay with the main thread

No product scope changed.

## 2026-04-15 - Advisor dogfood audit result received

Dogfood audit verdict:

- `PASS_WITH_FINDINGS`

Backend behavior:

- `auto` with missing env file fell back to deterministic and completed the
  team/species/follow-up flow correctly
- explicit `--backend deterministic` completed team analysis, species lookup,
  pronoun follow-up, `/clear`, and `/show-team`
- explicit `--backend pydantic_ai_native` with missing env exited cleanly with
  config-required message
- explicit native with invalid/unreachable provider returned a bounded advisor
  response
- `auto` with syntactically complete but unreachable native config selected
  native and returned native failure rather than deterministic fallback
- local valid native env selected `pydantic_ai_native`, but CLI smoke test
  produced no output after ~30s and was killed

Findings accepted for follow-up:

- `P1`: `--backend auto` with syntactically complete but unreachable native
  config should fall back to deterministic, not stay on native failure
- `P1`: native provider calls need bounded timeout / no-hang behavior
- `P2`: incomplete team input such as 3 slots should be explicitly caveated,
  downgraded, or prompt for missing slots
- `P3`: CLI rendering hides doc evidence when engine evidence consumes the
  first six evidence slots

Main-thread routing:

- next action is code hardening
- assign to main development thread
- test/product-audit thread has completed its audit role
- crawler / database thread remains paused
- no product scope expansion approved

## 2026-04-15 - Advisor dogfood hardening implemented

Completed bounded hardening for the accepted dogfood findings:

- `auto` backend now means native-first, not native-only
- native provider/model failure under `auto` falls back to deterministic for
  supported flows
- explicit `--backend pydantic_ai_native` keeps bounded native failure behavior
  and does not silently fall back
- native runtime calls now have a configured timeout path
- partial-team inputs are explicitly caveated and ask for missing slots
- CLI evidence rendering keeps output compact but exposes a doc/context snippet
  when doc retrieval ran

Files:

- `advisor/runtime.py`
- `advisor/conversation_cli.py`
- `tests/test_advisor.py`
- `README.md`
- `specs/conversation_cli_spec.md`
- `specs/advisor_runtime_spec.md`
- `log/project_log.md`

Scope control:

- no case retrieval added
- no web-in-loop added
- no GUI added
- no formal `message_history` state added
- no data ingestion changes made

Validation:

- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 19 tests`
  - `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 57 tests`
  - `OK`

Final rerun after replacing worker-thread timeout with bounded signal timeout:

- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 19 tests`
  - `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 57 tests`
  - `OK`

## 2026-04-15 - Runtime hygiene follow-up result received

Test / implementation thread completed the runtime hygiene follow-up.

Verdict:

- `FIXED`
- native default readiness: `ready_for_main_thread_decision`

ResourceWarning result:

- remaining `sqlite3 ResourceWarning` source was found in
  `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/battle_dex.py`
- cause: `with sqlite3.connect(...) as conn` manages transaction scope but does
  not close the connection
- fix: short-lived SQLite query connections now use
  `contextlib.closing(sqlite3.connect(...))`
- no warning filters were added
- no warnings were globally silenced

Validation reported by the test thread:

- `PYTHONTRACEMALLOC=25 .venv/bin/python -W error::ResourceWarning -m unittest discover -s tests`
  - `Ran 49 tests`, `OK`
  - no sqlite3 ResourceWarning
- `PYTHONTRACEMALLOC=25 .venv/bin/python -W default::ResourceWarning -m unittest discover -s tests`
  - `Ran 49 tests`, `OK`
  - no sqlite3 ResourceWarning
- `.venv/bin/python -m unittest -q tests.test_advisor`
  - `Ran 11 tests`, `OK`

Native parity / failure-path checks reported as passing:

- unknown species clean typed refusal
- invalid native provider/runtime bounded advisor response
- native-style concurrent repository lookup
- native species SQL-backed ability evidence
- native team confirmed deterministic-engine note
- native team provisional dual-type-baseline note
- deterministic/native output shape for team analysis
- deterministic/native output shape for species query
- deterministic/native output shape for same-session follow-up

Scope discipline preserved:

- no case retrieval
- no web-in-loop
- no formal `message_history`
- no cross-session persistence
- `pydantic_ai_native` was not made default by the worker

## 2026-04-15 - Advisor dogfood audit spec

Created a separate dogfood audit spec:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_dogfood_audit_spec.md`

Definition:

- dogfood audit = using the current conversational advisor MVP as a real user,
  then judging product behavior, evidence quality, refusal quality, and backend
  behavior
- this is not unit testing and not feature expansion

Task allocation:

- dogfood audit goes to the test / product-audit thread
- main development thread remains paused unless dogfood finds small approved
  code defects
- crawler / database thread remains paused
- main thread receives the report and decides the next product/runtime action

No product scope changed.

## 2026-04-15 - Main-thread acknowledgement for dogfood hardening

Main-thread verdict:

- `ACKNOWLEDGED`

Accepted status:

- dogfood audit findings fixed
- MVP scope unchanged
- `auto` backend policy now behaves as native-first, not native-only
- explicit `--backend pydantic_ai_native` still does not silently fall back
- native timeout and fallback behavior are implemented
- partial-team caveat is implemented
- CLI doc evidence visibility is implemented

Reported validation:

- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 19 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 57 tests`, `OK`

Next priority:

- improve native runtime failure-path coverage

Deferred scope remains deferred:

- no case retrieval
- no web-in-loop
- no GUI
- no formal runtime-level `message_history`
- no data ingestion changes

## 2026-04-16 - Retrieval implementation status and Phase A eval request

Current advisor retrieval reality:

- structured facts retrieval is SQL-first through `BattleDexRepository`
- doc retrieval is implemented in
  `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`
- current doc retrieval is a static curated rule table
- it filters by `analysis_type`, scores keyword matches, deduplicates by topic,
  and caps results by `limit`
- it returns bounded `DocContextSnippet` objects with source, topic,
  confidence, content, and retrieval reason
- no embeddings
- no FTS
- no automatic document chunking
- no case retrieval
- no web retrieval

Updated:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
  now records the current Phase A implementation snapshot

Created:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_phase_a_eval_request.md`

Task allocation:

- retrieval Phase A eval/hardening goes to a test / implementation thread
- do not give this to crawler / database thread
- do not implement embeddings or case retrieval yet
- main thread should review the eval result before reopening retrieval scope

## 2026-04-16 - Current task allocation board

Created the current task allocation board:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md`

Updated:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/总session.md`

Current near-term execution split:

- native failure-path audit -> test / audit thread
- native failure-path code fixes -> main development thread only if audit finds
  concrete defects
- Retrieval Phase A eval / small hardening -> test / implementation thread
- second dogfood audit -> test / product-audit thread after the first two items
- MVP completion decision -> main thread

Paused:

- crawler / database thread
- GUI
- case retrieval
- embeddings
- web-in-loop
- formal runtime-level `message_history`

This supersedes the previous single-task framing around retrieval only.

## 2026-04-16 - Retrieval Phase A eval completed

Worker role:

- test / implementation thread

Completed:

- added focused retrieval eval coverage for the current curated/rule-based
  `DocContextRetriever`
- verified representative topic retrieval:
  - team structure / 联防 -> `engine_grounding`
  - confidence / evidence -> `confidence_guard`
  - dual-type / 双属性 / 抗性 -> `dual_type_baseline`
  - species role / 主C / 辅助 -> `team_conditional_roles`
  - scope / 支持 / 范围 -> `scope_boundary`
- verified boundedness:
  - `limit` is strictly respected
  - duplicate topics are not returned
  - irrelevant `analysis_type` snippets do not leak
- verified weak unrelated retrieval stays limited to baseline guardrails
- verified deterministic CLI team and species paths expose doc/context evidence
  when doc retrieval runs

Small hardening fix:

- `advisor/retrieval.py` now returns an empty list for `limit <= 0`
- this closes a boundedness gap where `limit=0` or a negative limit could still
  return one snippet

Files changed:

- `advisor/retrieval.py`
- `tests/test_retrieval.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_retrieval`
  - `Ran 7 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 64 tests`, `OK`

Verdict:

- `PASS_WITH_FIXES`

Scope discipline preserved:

- no embeddings
- no FTS
- no case retrieval
- no web-in-loop
- no advisor tool expansion
- no retrieval architecture redesign
- no backend policy change
- no crawler/database pipeline change
- no GUI
- no formal runtime-level `message_history`

Phase A retrieval is acceptable for Advisor MVP dogfood after the boundedness
fix.

## 2026-04-16 - Native failure-path audit result received

QA-1 verdict:

- `PASS_WITH_FINDINGS`

Validation:

- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 57 tests`, `OK`
- `PYTHONPATH=. .venv/bin/python /tmp/roco_native_failure_audit.py`
  - `ALL_NATIVE_FAILURE_AUDIT_CHECKS_PASS`

Covered checks:

- provider unreachable explicit bounded failure
- provider unreachable auto fallback
- provider timeout bounded time
- provider timeout explicit bounded failure
- provider timeout auto fallback
- malformed native output explicit bounded failure
- malformed native output auto fallback
- tool partial failure explicit bounded failure
- tool partial failure auto fallback
- retrieval empty native continues with Engine evidence
- repository unavailable explicit clean refusal
- repository unavailable auto clean refusal

Accepted finding:

- `P2`: response status enum drift in failure/refusal paths
  - observed runtime emits `ToolStatus.UNAVAILABLE` / `unavailable`
  - `advisor_response_contract.yaml` only permits `ok`, `degraded`, `refused`, `failed`
  - required follow-up: code/spec alignment

Non-blocking quality note:

- explicit native tool partial failure is safe but coarse
- future improvement may degrade to profile-only / partial answer when safe
- not a blocker for MVP safety

Main-thread routing:

- assign enum alignment to main development thread as bounded code/spec hardening
- do not expand MVP scope
- native default readiness remains `not_ready` until enum drift is closed

## 2026-04-16 - Native status enum alignment completed

Source request:

- `specs/native_status_enum_alignment_request.md`
- source of truth: `specs/advisor_response_contract.yaml`

Execution facts:

- `advisor.contracts.ToolStatus` now matches the response contract exactly:
  - `ok`
  - `degraded`
  - `refused`
  - `failed`
- removed runtime/code dependency on `ToolStatus.UNAVAILABLE`
- native tool refusal paths now emit contract-compatible `refused`
  - no team in session
  - missing species query
  - unknown species
  - absent battle-dex repository in native tool path
- provider/model/timeout behavior is unchanged
  - explicit native failure remains a bounded native refusal with no tool results
  - auto-selected native still falls back to deterministic on provider/model/timeout failure
- added focused contract guard:
  - `tests/test_advisor_response_contract.py`
  - asserts `ToolStatus` matches `advisor_response_contract.yaml`
  - asserts serialized tool statuses cannot be `unavailable`
- updated native unknown-species test to assert `get_species_profile` returns `refused`

Files changed:

- `advisor/contracts.py`
- `advisor/runtime.py`
- `tests/test_advisor.py`
- `tests/test_advisor_response_contract.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_advisor_response_contract`
  - `Ran 2 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 20 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 67 tests`, `OK`

Readiness assessment:

- QA-1 enum drift is closed.
- Native default readiness is now `ready_for_main_thread_decision`.
- No scope expansion was made:
  - no case retrieval
  - no web-in-loop
  - no GUI
  - no formal runtime-level `message_history`
  - no backend policy change
  - no data ingestion change

## 2026-04-16 - Main-thread acknowledgement for native status enum alignment

Main-thread verdict:

- `ACKNOWLEDGED`

Accepted status:

- QA-1 response status enum drift is fixed
- `ToolStatus` now matches `advisor_response_contract.yaml`
- serialized advisor tool statuses are limited to:
  - `ok`
  - `degraded`
  - `refused`
  - `failed`
- native default readiness is `ready_for_main_thread_decision`

Updated:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md`

Next action:

- run second dogfood audit via test / product-audit thread

Do not reopen deferred scope:

- no GUI
- no case retrieval
- no embeddings
- no web-in-loop
- no formal runtime-level `message_history`
- no data ingestion changes

## 2026-04-16 - Second dogfood audit result received

Second dogfood audit verdict:

- `PASS_WITH_FINDINGS`

Backend behavior:

- `auto` with missing env fell back to deterministic cleanly
- `auto` with valid local native config attempted `pydantic_ai_native`, timed
  out, then fell back to deterministic with visible confidence note
- explicit `deterministic` worked across team/species/follow-up/refusal flows
- explicit `pydantic_ai_native` timed out in the sampled call and returned
  bounded refusal
- explicit native with missing env exited cleanly with config requirement

Evidence / status checks:

- sampled tool result statuses used only contract-compatible values
- no sampled rendered output contained `unavailable`
- doc/context evidence remained visible when retrieval ran
- `/clear` cleared team and species context

Accepted findings:

- `P2`: native-backed `auto` can create long user-visible stalls before fallback
- `P3`: unsupported future/live-meta request refusal is safe but generic

Main-thread decision:

- do not declare MVP complete yet
- run one bounded prompt/runtime tuning pass
- do not reopen retrieval, crawler, GUI, casebank, embeddings, web-in-loop, or
  formal `message_history`

Created:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_mvp_tuning_request.md`

Updated:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md`

Next owner:

- main development thread

## 2026-04-16 - Advisor MVP prompt/runtime tuning completed

Source request:

- `specs/advisor_mvp_tuning_request.md`

Execution facts:

- implemented session-local native health gating for `auto`
  - first native provider/model failure or timeout under `auto` still attempts
    native, then falls back to deterministic for supported flows
  - later supported messages in the same CLI process skip native and use
    deterministic fallback directly
  - skipped fallback responses keep backend label `auto_fallback_deterministic`
    and add a confidence note explaining native was marked unhealthy in the
    current CLI process
- explicit `--backend pydantic_ai_native` behavior is unchanged
  - it still attempts native
  - it still returns bounded native failure/refusal
  - it does not silently fall back to deterministic
- added targeted future/live-meta refusal copy
  - says current MVP has no web/live official-balance feed
  - says current MVP cannot predict future buffs/nerfs or live meta changes
  - points to supported nearby actions: team structure analysis, battle-dex
    fact query, and provisional species-role discussion from current facts
- documentation aligned without changing backend policy or MVP scope

Files changed:

- `advisor/runtime.py`
- `tests/test_advisor.py`
- `README.md`
- `specs/advisor_runtime_spec.md`
- `specs/conversation_cli_spec.md`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 68 tests`, `OK`

Scope discipline:

- no case retrieval
- no embeddings
- no web-in-loop
- no GUI
- no formal runtime-level `message_history`
- no cross-session persistence
- no data ingestion change

Readiness assessment:

- second dogfood audit P2/P3 tuning findings are closed.
- Advisor CLI is `ready_for_final_mvp_readiness_dogfood_check`.

## 2026-04-16 - Main-thread final MVP readiness check assigned

Source:

- main development thread reported completion of
  `specs/advisor_mvp_tuning_request.md`

Main-thread acknowledgement:

- accepted implementation report as the current repo status for task planning
- did not declare MVP complete yet
- assigned final dogfood/readiness check to the test / product-audit thread

Created:

- `specs/advisor_final_mvp_readiness_check.md`

Updated:

- `specs/current_task_allocation.md`

Next owner:

- test / product-audit thread

Next decision gate:

- if final check returns `PASS` with
  `ready_to_declare_mvp_complete`, main thread may declare Advisor CLI MVP
  complete
- if final check returns findings, main thread will decide whether to allow one
  targeted hardening pass or block completion

Scope remains unchanged:

- no case retrieval
- no embeddings
- no web-in-loop
- no GUI
- no formal runtime-level `message_history`
- no cross-session persistence
- no data ingestion change

## 2026-04-16 - Advisor CLI MVP completion decision

Source:

- QA-1 final MVP readiness check

QA-1 verdict:

- `PASS_WITH_FINDINGS`

QA-1 recommendation:

- `ready_to_declare_mvp_complete`

Main-thread decision:

- `Advisor CLI MVP complete`

Reason:

- all required backend behavior checks passed
- deterministic backend works
- `auto` missing-env fallback works
- `auto` native timeout/provider failure fallback works
- repeated messages in the same auto session skip repeated native timeout
  windows after native is marked unhealthy
- explicit `pydantic_ai_native` remains native-only and bounded
- six-slot team analysis, partial-team caveat, species lookup, pronoun
  follow-up, unknown-species refusal, future/live-meta refusal, and `/clear`
  session reset all passed
- contract discipline passed:
  - sampled tool statuses remained within `ok`, `degraded`, `refused`,
    `failed`
  - confirmed claims traced to Engine, SQL facts, or approved docs
  - semantic role claims stayed provisional
- full suite passed:
  - `.venv/bin/python -m unittest discover -s tests`
  - `Ran 68 tests in 3.160s`, `OK`

Accepted non-blocking finding:

- `P3`: local native provider was not validated as successful native output
  because sampled native call timed out under `--native-timeout 2`

Why non-blocking:

- bounded `auto` fallback is the approved MVP behavior
- deterministic output remains usable
- explicit native failure remains bounded
- live provider quality is a post-MVP runtime reliability task, not a blocker
  for CLI MVP completion

Created:

- `specs/advisor_mvp_completion_record.md`

Updated:

- `specs/current_task_allocation.md`

Next phase:

- post-MVP planning

Deferred until explicitly reopened:

- GUI
- case retrieval / casebank
- embeddings / vector retrieval
- web-in-loop
- formal runtime-level `message_history`
- cross-session persistence
- crawler/database expansion
- native provider quality investigation

## 2026-04-16 - Post-MVP roadmap aligned and P0a assigned

Source:

- main-thread review of `specs/product_architecture_roadmap.md`

Roadmap updates:

- split short-term P0 into ordered tracks:
  - `P0a App-Facing Contract Normalization`
  - `P0b Minimal Agent Core Extraction`
  - `P0c FastAPI Backend`
  - `P0d Persona V1 + IP Guard`
  - `P0e Mobile MVP Scaffold`
  - `P0f Public-Release Hardening`
  - `P0g Native Provider Reliability`
- added API-key handling boundary:
  - local-user-key mode vs backend-managed-key mode must be explicit
  - provider config must remain behind interfaces and redacted logs/errors
- added session-continuity boundary:
  - mobile cannot rely on hidden CLI process state
  - full durable persistence can stay P1, but P0 API must define how follow-up
    context is carried
- moved public-release hardening out of vague P1-only framing:
  - local run path, `.env.example`, healthcheck, log redaction, version
    endpoint, provider validation, and public disclaimer are P0 release gates
- kept case retrieval, embeddings, web-in-loop, GUI, crawler expansion, and
  formal message history deferred

Created:

- `specs/p0a_app_facing_contract_request.md`

Updated:

- `specs/product_architecture_roadmap.md`
- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- main development thread

Next task:

- implement `P0a App-Facing Contract Normalization`

Blocking rule:

- do not start FastAPI, mobile, persona rendering, case retrieval, embeddings,
  web-in-loop, crawler/database expansion, or native provider reliability work
  until P0a is complete or explicitly blocked.

## 2026-04-16 - P0a app-facing contract normalization completed

Source request:

- `specs/p0a_app_facing_contract_request.md`

Execution facts:

- created `agent_core` as the app/API-facing contract boundary
- added typed response models:
  - `AgentResponse`
  - `AgentToolResult`
  - `EvidenceItem`
  - `ConfidenceNote`
  - `FollowupOption`
  - `PersonaEnvelope`
- app-facing `AgentResponse` preserves:
  - `schema_version`
  - aggregate response `status`
  - `backend`
  - `analysis_type`
  - user-visible `answer`
  - tool results
  - evidence items
  - structured confidence notes
  - follow-up options
  - optional persona envelope with `facts_locked=true`
- evidence-reference decision:
  - `AgentToolResult.evidence_refs` is required
  - refs point to stable top-level `EvidenceItem.id` values such as `ev_001`
  - adapter assigns refs by tool/source type:
    - `analyze_team_structure` -> engine evidence
    - species tools -> fact evidence
    - `retrieve_doc_context` -> doc evidence
    - unknown tools -> all evidence
- added adapter:
  - `agent_core.contracts.agent_response_from_advisor`
  - `AgentResponse.from_advisor_response`
  - maps current `advisor.contracts.AdvisorResponse` without changing CLI
    runtime behavior or rendering
- adapter behavior:
  - preserves `backend` and user-visible answer
  - infers aggregate status:
    - `ok` for normal supported responses
    - `degraded` for `auto_fallback_deterministic`
    - `refused` for scope/refusal responses
    - `failed` for native runtime failure responses
  - infers `analysis_type` from tools/refusal/failure shape
  - converts raw string confidence notes into structured
    `{claim_scope, confidence, note}` objects
  - converts follow-up strings into stable `{id, label, action}` objects
- added contract tests covering:
  - required app-facing fields
  - status enum values
  - evidence item shape
  - evidence refs to top-level evidence IDs
  - structured confidence notes
  - normal team adapter output
  - species adapter output
  - refusal adapter output
  - degraded auto-fallback adapter output
  - JSON serialization and persona fact-lock policy

Files changed:

- `agent_core/__init__.py`
- `agent_core/contracts.py`
- `tests/test_agent_core_contracts.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 74 tests`, `OK`

Scope discipline:

- no FastAPI
- no mobile
- no persona rendering
- no case retrieval
- no embeddings
- no web-in-loop
- no formal runtime-level `message_history`
- no cross-session persistence
- no data ingestion change
- no backend policy change
- no intentional CLI output change

Readiness assessment:

- P0a is complete.
- P0b minimal agent-core extraction still requires main-thread scheduling and
  later audit clearance.

## 2026-04-16 - Main-thread P0a review and contract audit assignment

Source:

- main development thread reported P0a completion

Main-thread acknowledgement:

- P0a implementation is accepted as completed for planning purposes
- do not schedule P0b yet
- run a bounded architecture audit first because the new product-facing
  `agent_core/contracts.py` currently imports `advisor.contracts`

Reason:

- P0a tests pass and contract shape is in place
- however, product-facing contracts should ideally stay independent from the
  CLI/advisor layer
- adapter code may depend on `advisor`, but pure contract models should not
  unnecessarily depend on CLI runtime types before P0b extraction

Created:

- `specs/p0a_contract_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next decision gate:

- if audit returns `PASS` and `ready_for_P0b`, schedule P0b
- if audit returns `refactor_before_P0b`, assign one bounded refactor pass
- if audit returns `blocked`, stop P0b scheduling

## 2026-04-16 - P0a contract audit received; boundary refactor assigned

Source:

- QA architecture audit for P0a

QA verdict:

- `PASS_WITH_FINDINGS`

P0b readiness:

- `conditional_not_ready_until_boundary_refactor`

Judgements:

- contract judgement: `PASS`
- evidence judgement: `PASS_WITH_CAVEAT`
- adapter judgement: `PASS`
- boundary judgement: `refactor_before_P0b`

Accepted findings:

- `P1 boundary coupling`
  - `agent_core/contracts.py` imports `advisor.contracts`
  - Advisor-specific adapter logic lives beside pure product-facing models
  - must be refactored before P0b
- `P3 evidence attribution precision`
  - current evidence refs are source-type heuristic
  - acceptable for P0a
  - keep contained in adapter code

Main-thread decision:

- do not schedule P0b yet
- assign one bounded P0a boundary refactor to the main development thread

Created:

- `specs/p0a_boundary_refactor_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- main development thread

Next task:

- move Advisor-specific adapter logic out of `agent_core/contracts.py`
- keep `agent_core/contracts.py` pure app/API-facing model definitions
- preserve current contract shape, adapter behavior, evidence refs, CLI output,
  and backend policy

## 2026-04-16 - P0a boundary refactor completed

Source request:

- `specs/p0a_boundary_refactor_request.md`

Execution facts:

- `agent_core/contracts.py` now contains only app/API-facing product enums and
  typed models
- removed Advisor imports and Advisor-specific adapter logic from
  `agent_core/contracts.py`
- moved Advisor-specific conversion logic to:
  - `agent_core/adapters/advisor.py`
- added adapter package marker:
  - `agent_core/adapters/__init__.py`
- updated `agent_core/__init__.py` to export only pure contract models/enums
- removed pure-model convenience API:
  - `AgentResponse.from_advisor_response`
  - adapter usage is now explicitly
    `agent_core.adapters.advisor.agent_response_from_advisor`

Import boundary proof:

- isolated import check:
  - import `agent_core.contracts`
  - `advisor.contracts in sys.modules == False`
- adapter import check:
  - import `agent_core.adapters.advisor`
  - `advisor.contracts in sys.modules == True`
  - `agent_response_from_advisor.__module__ == "agent_core.adapters.advisor"`
- test coverage asserts `agent_core/contracts.py` source contains no:
  - `advisor.contracts`
  - `from advisor`
  - `import advisor`

Behavior compatibility:

- app-facing JSON shape is unchanged
- `AgentResponse` fields remain unchanged
- `AgentToolResult.evidence_refs` remains required
- evidence refs still point to top-level `EvidenceItem.id`
- current heuristic evidence attribution is preserved in adapter code:
  - team structure -> engine evidence
  - species tools -> fact evidence
  - doc retrieval -> doc evidence
  - unknown tools -> all evidence
- aggregate status inference is unchanged
- structured confidence note conversion is unchanged
- CLI runtime/rendering and backend policy are unchanged

Files changed:

- `agent_core/__init__.py`
- `agent_core/contracts.py`
- `agent_core/adapters/__init__.py`
- `agent_core/adapters/advisor.py`
- `tests/test_agent_core_contracts.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 77 tests`, `OK`

Scope discipline:

- no P0b orchestrator extraction
- no FastAPI
- no mobile
- no persona rendering
- no case retrieval
- no embeddings
- no web-in-loop
- no formal runtime-level `message_history`
- no cross-session persistence
- no data ingestion change
- no backend policy change
- no intentional CLI output change
- no evidence attribution redesign

Readiness assessment:

- P0a boundary refactor is complete.
- P0b is now `ready_for_main_thread_scheduling`.

## 2026-04-16 - P0a fully complete; P0b assigned

Source:

- main development thread reported P0a boundary refactor completion

Main-thread decision:

- accept P0a boundary refactor as complete
- mark P0a fully complete
- schedule P0b Minimal Agent Core Extraction

Reason:

- `agent_core/contracts.py` is now pure app/API-facing product model code
- Advisor-specific adapter logic is isolated in:
  - `agent_core/adapters/advisor.py`
- latest reported full suite:
  - `.venv/bin/python -m unittest discover -s tests`
  - `Ran 77 tests`, `OK`

Created:

- `specs/p0b_minimal_agent_core_extraction_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- main development thread

Next task:

- implement P0b minimal agent-core extraction

Boundary:

- add product-side orchestration/protocol/safety/persona boundaries
- wrap existing `advisor.runtime.AdvisorAgent` through adapter code
- do not move battle engine, battle-dex, CLI runtime behavior, backend policy,
  API, mobile, persona rendering, case retrieval, embeddings, or web-in-loop

## 2026-04-18 - P0b minimal agent-core extraction completed

Source request:

- `specs/p0b_minimal_agent_core_extraction_request.md`

Execution facts:

- added product-side `agent_core` orchestration boundary without moving
  Advisor runtime, battle engine, or battle-dex code
- added pure runtime/tool protocol:
  - `agent_core/tools.py`
  - `AgentRuntimeAdapter.handle_message(message: str) -> AgentResponse`
- added minimal orchestrator:
  - `agent_core/orchestrator.py`
  - delegates one user message to a runtime adapter
  - applies safety before runtime execution
  - attaches persona metadata after runtime execution
  - does not call battle engine, SQLite, LLM providers, or CLI commands
- added minimal safety boundary:
  - `agent_core/safety.py`
  - default `SafetyGuard` allows requests
  - `SafetyDecision.refuse(...)` can produce a structured refused
    `AgentResponse` without calling the runtime adapter
- added minimal persona boundary:
  - `agent_core/persona.py`
  - attaches only `PersonaEnvelope` metadata
  - forces `facts_locked=true`
  - forces `fact_policy=persona_may_not_alter_facts`
  - does not modify answer, evidence, confidence notes, tool results, status,
    or refusal decisions
- extended Advisor compatibility adapter:
  - `agent_core/adapters/advisor.py`
  - added `AdvisorRuntimeAdapter`
  - wraps existing `advisor.runtime.AdvisorAgent`
  - converts Advisor responses via existing `agent_response_from_advisor`

Import boundary proof:

- pure-module isolated import check loaded:
  - `agent_core.contracts`
  - `agent_core.tools`
  - `agent_core.safety`
  - `agent_core.persona`
  - `agent_core.orchestrator`
- result:
  - no `advisor.*` modules loaded
- adapter import check:
  - `AdvisorRuntimeAdapter.__module__ == "agent_core.adapters.advisor"`
  - `agent_response_from_advisor.__module__ == "agent_core.adapters.advisor"`
  - importing the adapter loads `advisor.contracts` and `advisor.runtime`, as
    intended

Files changed:

- `agent_core/__init__.py`
- `agent_core/tools.py`
- `agent_core/safety.py`
- `agent_core/persona.py`
- `agent_core/orchestrator.py`
- `agent_core/adapters/advisor.py`
- `tests/test_agent_core_orchestrator.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 83 tests`, `OK`

Scope discipline:

- no deterministic analyzer move
- no battle-dex code move
- no AdvisorAgent rewrite
- no intentional CLI output change
- no FastAPI
- no mobile
- no persona rendering
- no case retrieval
- no embeddings
- no web-in-loop
- no formal runtime-level `message_history`
- no cross-session persistence
- no data ingestion change
- no backend policy change
- no native provider behavior change

Readiness assessment:

- P0b is complete.
- P0c/P0d scheduling remains a main-thread product decision; P0b is not
  blocked.

## 2026-04-18 - P0b implementation accepted for audit; architecture audit assigned

Source:

- main development thread reported P0b completion

Main-thread acknowledgement:

- P0b implementation is accepted as completed for planning purposes
- do not schedule P0c FastAPI or P0d Persona yet
- run a bounded architecture audit first

Reason:

- P0b introduced new product boundary modules
- before API work depends on them, verify:
  - pure `agent_core` modules do not import `advisor.*`
  - orchestrator does not mutate facts/evidence/confidence/refusal decisions
  - safety refusal does not call runtime adapter
  - persona boundary only attaches fact-locked metadata
  - Advisor compatibility adapter remains isolated under
    `agent_core.adapters.advisor`

Created:

- `specs/p0b_agent_core_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next decision gate:

- if audit returns `PASS` and `ready_for_P0c`, schedule P0c FastAPI or decide
  whether P0d should precede it
- if audit returns `needs_targeted_refactor`, assign one bounded refactor pass
- if audit returns `blocked`, stop P0c/P0d scheduling

## 2026-04-18 - P0b audit passed; P0c FastAPI assigned

Source:

- QA architecture audit for P0b

QA verdict:

- `PASS`

P0c readiness:

- `ready_for_P0c`

Judgements:

- pure-boundary judgement: `PASS`
- orchestrator judgement: `PASS`
- safety/persona judgement: `PASS`
- adapter judgement: `PASS`
- JSON/contract stability: `PASS`
- findings: none

Validation reported by QA:

- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 83 tests`, `OK`

Main-thread decision:

- P0b is complete
- schedule P0c FastAPI Backend

Created:

- `specs/p0c_fastapi_backend_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- main development thread

Next task:

- implement minimal FastAPI product service over the existing `agent_core`
  boundary

Boundary:

- local/product API only
- no mobile
- no persona rendering
- no case retrieval
- no embeddings
- no web-in-loop
- no durable cross-session persistence
- no hosted provider-key management
- no public deployment hardening beyond local API basics

## 2026-04-18 - P0c FastAPI backend completed

Source request:

- `specs/p0c_fastapi_backend_request.md`

Execution facts:

- added local FastAPI product API package:
  - `api/__init__.py`
  - `api/contracts.py`
  - `api/dependencies.py`
  - `api/main.py`
  - `api/services/__init__.py`
  - `api/services/advisor_service.py`
- added dependencies:
  - `fastapi>=0.115,<1.0`
  - `uvicorn>=0.34,<1.0`
  - `httpx>=0.27,<1.0`
- installed those dependencies into `.venv` for local validation
- exposed endpoints:
  - `GET /health`
  - `GET /metadata`
  - `POST /chat`
  - `POST /team/analyze`
  - `GET /species/search`
  - `GET /species/{species_id}`
- `/chat` uses:
  - `AgentOrchestrator`
  - `AdvisorRuntimeAdapter`
  - existing `AdvisorAgent`
  - app-facing `AgentResponse`
- `/team/analyze` maps API team slots to the existing Advisor natural-language
  team-analysis path, then returns `AgentResponse`
- species search/profile endpoints use `BattleDexRepository` through the API
  service layer and do not expose the SQLite path

Session continuity decision:

- `/chat` accepts optional `session_id`
- `/chat` returns `session_id`
- server stores an in-memory `AgentOrchestrator` / `AdvisorAgent` per
  `session_id`
- no durable persistence
- no cross-device persistence
- no formal runtime-level `message_history`
- no raw provider keys in session state

Provider/API-key handling decision:

- API default backend is deterministic
- `/chat` works without a live model key
- request models do not accept provider API keys
- metadata reports provider mode as `server_local_config_only_no_request_keys`
- no hosted provider-key management was added
- no backend policy change was made to the CLI

Error/redaction behavior:

- missing species returns bounded `404 species_not_found`
- unavailable battle-dex returns bounded `503 battle_dex_unavailable`
- invalid message/team payload returns bounded validation errors
- unhandled exceptions are converted to a generic `internal_error`
- metadata and error responses do not expose:
  - local SQLite path
  - env file contents
  - provider API keys

Local API basics:

- minimal local CORS allowlist added for localhost development
- `rate_limit_placeholder` dependency added as a future hook without building
  a full abuse-control system

Files changed:

- `requirements.txt`
- `api/__init__.py`
- `api/contracts.py`
- `api/dependencies.py`
- `api/main.py`
- `api/services/__init__.py`
- `api/services/advisor_service.py`
- `tests/test_api.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 89 tests`, `OK`

Scope discipline:

- no mobile
- no persona rendering
- no case retrieval
- no embeddings
- no web-in-loop
- no durable cross-session persistence
- no hosted provider-key management
- no public deployment hardening beyond local API basics
- no deterministic analyzer move
- no battle-dex code move
- no AdvisorAgent rewrite
- no intentional CLI output change
- no data ingestion change
- no backend policy change beyond API-local deterministic configuration

Readiness assessment:

- P0c is complete.
- P0d/P0e scheduling remains a main-thread product decision; P0c is not
  blocked.

## 2026-04-18 - P0c implementation accepted for audit; API audit assigned

Source:

- main development thread reported P0c completion

Main-thread acknowledgement:

- P0c implementation is accepted as completed for planning purposes
- do not schedule P0d Persona/IP Guard, mobile scaffold, or public-release
  hardening yet
- run a bounded API architecture audit first

Reason:

- P0c introduced the first product HTTP boundary
- before mobile or persona work depends on it, verify:
  - endpoint contracts are stable
  - `/chat` and `/team/analyze` return `AgentResponse`
  - API goes through `agent_core` instead of bypassing it
  - session continuity behaves as specified
  - provider/key handling remains deterministic/no-request-key by default
  - error responses are bounded and redacted
  - local CORS/rate-limit placeholder does not pretend to be public hardening

Created:

- `specs/p0c_api_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next decision gate:

- if audit returns `PASS` and `ready_for_next_P0_track`, main thread may choose
  P0d Persona/IP Guard, mobile scaffold, or another bounded P0 track
- if audit returns `needs_targeted_api_refactor`, assign one bounded API
  refactor pass
- if audit returns `blocked`, stop next-track scheduling

## 2026-04-18 - P0c API audit passed; P0d Persona/IP Guard scheduled

Source:

- test / architecture-audit thread reported P0c API audit result

Audit verdict:

- `PASS`

P0d/mobile readiness:

- `ready_for_next_P0_track`

Judgements:

- endpoint contract judgement: `PASS`
- agent-core boundary judgement: `PASS`
- session continuity judgement: `PASS`
- provider/key handling judgement: `PASS`
- error/redaction judgement: `PASS`
- local CORS/rate-limit judgement: `PASS_FOR_P0c_LOCAL`
- findings: none

Validation:

- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 6 tests in 0.442s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests in 0.080s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 6 tests in 0.077s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.726s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 89 tests in 3.595s`, `OK`

Additional audit evidence:

- manual TestClient sanity script confirmed required endpoint inventory
- invalid chat returned `422`
- extra `api_key` field was ignored with `200`
- simulated internal failure returned bounded
  `500 {"code":"internal_error","message":"Request failed safely."}`
- no `ROCO_OPENAI_API_KEY`, `test-key`, env path, local DB path, or traceback
  leaked in sampled error path

Main-thread decision:

- P0c FastAPI Backend is complete.
- P0d Persona V1 + IP Guard is the next ordered P0 track.
- Mobile scaffold remains blocked until P0d implementation/audit completes.

Created:

- `specs/p0d_persona_ip_guard_request.md`

Updated:

- `specs/product_architecture_roadmap.md`
- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- main development thread

Next request:

- implement P0d Persona V1 + IP Guard under
  `specs/p0d_persona_ip_guard_request.md`

## 2026-04-18 - P0d Persona V1 + IP Guard implemented

Source:

- main development thread executed `specs/p0d_persona_ip_guard_request.md`

Implementation facts:

- Added public-safe default persona metadata:
  - `persona_id=obsidian_tactical_coach`
  - `display_name=黑曜战术官`
  - `display_style=cold_precise_high_pressure_tactical`
- Added deterministic persona rendering into `response.persona.rendered_answer`.
- Preserved base `response.answer` and all factual/control fields:
  `status`, `analysis_type`, `backend`, `tool_results`, `evidence`,
  `confidence_notes`, `followup_options`, and refusal decisions.
- Added conservative IP guard sanitization for official Enzo/恩佐/Tencent/
  洛克王国/official-authorization positioning in persona metadata requests.
- Added bounded API request-side persona selection via optional `persona_id`.
  Only the approved public-safe default is exposed; unsupported or unsafe
  selector values sanitize to the default persona.

Files changed:

- `agent_core/contracts.py`
- `agent_core/persona.py`
- `api/contracts.py`
- `api/main.py`
- `api/services/advisor_service.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_api.py`
- `log/project_log.md`

Validation:

- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.087s`, `OK`
- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.476s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.773s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests in 0.076s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 93 tests in 3.560s`, `OK`

Scope confirmation:

- No mobile, GUI, official Enzo persona, official assets, LLM-based persona
  rewriting, case retrieval, embeddings, web-in-loop, durable persistence,
  hosted provider-key management, public deployment hardening, battle-dex
  ingestion change, backend policy change, deterministic analyzer move,
  battle-dex move, AdvisorAgent rewrite, or intentional CLI output change was
  introduced.

Status:

- P0d implementation is complete and ready for audit/main-thread decision.

Main-thread handling:

- acknowledged P0d implementation report
- did not release mobile scaffold yet
- created bounded P0d audit request

Created:

- `specs/p0d_persona_ip_guard_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `specs/product_architecture_roadmap.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next request:

- audit P0d Persona V1 + IP Guard under
  `specs/p0d_persona_ip_guard_audit_request.md`

## 2026-04-18 - P0d audit passed; P0e Mobile MVP Scaffold scheduled

Source:

- test / architecture-audit thread reported P0d Persona/IP Guard audit result

Audit verdict:

- `PASS`

Mobile readiness:

- `ready_for_P0e_mobile_scaffold`

Judgements:

- fact-lock judgement: `PASS`
- default-persona judgement: `PASS`
- IP-guard judgement: `PASS`
- rendered-answer risk judgement: `PASS_WITH_CAVEAT`
- API-selector judgement: `PASS`
- regression judgement: `PASS`
- findings: none

Accepted caveat:

- `persona.rendered_answer` can copy terms like `官方` from the factual base
  answer.
- audit classified this as acceptable for P0d because the persona layer is
  echoing base factual content and adding a boundary disclaimer, not inventing
  official identity, authorization, art, or dialogue positioning.

Validation:

- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.075s`, `OK`
- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.448s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.712s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
  - `Ran 9 tests in 0.076s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 93 tests in 3.582s`, `OK`

Ad-hoc checks:

- unsafe selectors tested:
  - `Enzo`
  - `恩佐`
  - `Tencent`
  - `腾讯`
  - `洛克王国官方`
  - `official`
  - `官方授权`
  - `官方立绘`
  - `官方台词`
- all sanitized to:
  - `obsidian_tactical_coach`
  - `黑曜战术官`

Main-thread decision:

- P0d Persona V1 + IP Guard is complete.
- P0e Mobile MVP Scaffold is scheduled.
- P0e remains a local-development mobile shell only; no public hardening,
  provider-key management, persistence, case retrieval, embeddings, web-in-loop,
  or official IP assets.

Created:

- `specs/p0e_mobile_mvp_scaffold_request.md`

Updated:

- `specs/current_task_allocation.md`
- `specs/product_architecture_roadmap.md`
- `log/project_log.md`

Next owner:

- main development thread

Next request:

- implement P0e Mobile MVP Scaffold under
  `specs/p0e_mobile_mvp_scaffold_request.md`

## 2026-04-18 - P0e implementation acknowledged; mobile audit assigned

Source:

- main development thread reported P0e Mobile MVP Scaffold completion

Implementation facts accepted for audit:

- `mobile/` Expo + React Native + TypeScript workspace created
- screens implemented:
  - chat
  - team editor
  - species search
  - settings
  - response/evidence inspection
- Product API endpoints wired:
  - `GET /health`
  - `GET /metadata`
  - `POST /chat`
  - `POST /team/analyze`
  - `GET /species/search`
  - `GET /species/{species_id}`
- mobile treats `AgentResponse` as the response contract
- implementation thread reported:
  - mobile `npm run typecheck`: exit `0`
  - backend regression:
    - `.venv/bin/python -m unittest discover -s tests`
    - `Ran 93 tests in 3.729s`, `OK`

Main-thread decision:

- do not close P0e yet
- run bounded P0e mobile audit first
- do not schedule P0f hardening until audit returns readiness

Created:

- `specs/p0e_mobile_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next request:

- audit P0e Mobile MVP Scaffold under
  `specs/p0e_mobile_audit_request.md`

## 2026-04-18 - P0e audit passed; P0f Public-Release Hardening scheduled

Source:

- test / architecture-audit thread reported P0e mobile audit result

Audit verdict:

- `PASS`

P0f readiness:

- `ready_for_P0f_hardening`

Judgements:

- API-boundary judgement: `PASS`
- contract/render judgement: `PASS`
- screen-scope judgement: `PASS`
- IP/product-safety judgement: `PASS`
- validation judgement: `PASS`
- local-run judgement: `PASS`
- findings: none

Validation:

- `cd /Users/okfin3/project/GitHub/OKFin33/Roco/mobile && npm run typecheck`
  - `tsc --noEmit`, `OK`
- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.437s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.077s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.687s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 93 tests in 3.455s`, `OK`

Audit summary:

- mobile is confirmed to call the Product API only
- `AgentResponse` contract/render boundary is usable from mobile
- no Python imports, CLI shell-out, SQLite access, provider calls, or local
  battle/species logic duplication were found in mobile source
- no official Enzo/恩佐 persona, official assets, or official-authorization
  positioning were found in mobile source

Main-thread decision:

- P0e Mobile MVP Scaffold is complete.
- P0f Public-Release Hardening is scheduled.
- P0f remains bounded to local/public-prep hardening, not cloud infra, auth,
  payments, persistence, case retrieval, embeddings, or web-in-loop.

Created:

- `specs/p0f_public_release_hardening_request.md`

Updated:

- `specs/current_task_allocation.md`
- `specs/product_architecture_roadmap.md`
- `log/project_log.md`

Next owner:

- main development thread

Next request:

- implement P0f Public-Release Hardening under
  `specs/p0f_public_release_hardening_request.md`

## 2026-04-18 - P0f implementation acknowledged; hardening audit assigned

Source:

- main development thread reported P0f Public-Release Hardening completion

Implementation facts accepted for audit:

- added `.env.example`
- added local run scripts:
  - `scripts/run_local_api.sh`
  - `scripts/run_mobile.sh`
- added config validation in `advisor/config.py`
- added release/version constants in `api/release.py`
- tightened `/health` and `/metadata`
- added bounded logging/redaction helpers
- preserved bounded timeout/provider-failure behavior
- added public unofficial disclaimer copy
- added `tests/test_public_hardening.py`

Reported validation:

- `.venv/bin/python -m unittest tests.test_public_hardening`
  - `Ran 3 tests in 0.550s`, `OK`
- `cd mobile && npm run typecheck`
  - `tsc --noEmit`, exit code `0`
- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.567s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.147s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.940s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 96 tests in 3.995s`, `OK`

Main-thread decision:

- do not close P0f yet
- run bounded hardening audit first
- do not open post-P0 roadmap work until audit returns readiness

Created:

- `specs/p0f_public_release_hardening_audit_request.md`

Updated:

- `specs/current_task_allocation.md`
- `specs/product_architecture_roadmap.md`
- `log/project_log.md`

Next owner:

- test / architecture-audit thread

Next request:

- audit P0f Public-Release Hardening under
  `specs/p0f_public_release_hardening_audit_request.md`

## 2026-04-18 - P0f audit passed; P0 formally closed

Source:

- test / architecture-audit thread reported P0f hardening audit result

Audit verdict:

- `PASS`

Post-P0 readiness:

- `ready_for_post_P0_planning`

Judgements:

- config-hygiene judgement: `PASS`
- local-run-path judgement: `PASS`
- health/metadata/version judgement: `PASS`
- logging/redaction judgement: `PASS`
- timeout/provider-failure judgement: `PASS`
- disclaimer/public-safety judgement: `PASS`
- regression/scope judgement: `PASS`
- findings: none

Validation:

- `.venv/bin/python -m unittest tests.test_public_hardening`
  - `Ran 3 tests in 0.428s`, `OK`
- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.440s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.079s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.727s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 96 tests in 3.978s`, `OK`
- `cd /Users/okfin3/project/GitHub/OKFin33/Roco/mobile && npm run typecheck`
  - `tsc --noEmit`, `OK`

Audit summary:

- sample config is safe and does not activate native runtime accidentally
- local run scripts/docs are coherent
- `/health` and `/metadata` are coherent and release-safe
- logging/redaction remains bounded with no user-facing secret/path leakage
- disclaimer copy is neutral, unofficial, and not misleading
- no post-P0 scope drift was found in the hardening surface

Main-thread decision:

- P0 scope is complete.
- do not reopen any completed P0 track without a concrete regression
- enter post-P0 planning from a clean baseline

Updated:

- `specs/current_task_allocation.md`
- `specs/product_architecture_roadmap.md`
- `log/project_log.md`

## 2026-04-18 - P0e Mobile MVP Scaffold implemented

Source:

- main development thread executed `specs/p0e_mobile_mvp_scaffold_request.md`

Implementation facts:

- Created `mobile/` Expo + React Native + TypeScript workspace.
- Added typed Product API client for:
  - `GET /health`
  - `GET /metadata`
  - `POST /chat`
  - `POST /team/analyze`
  - `GET /species/search`
  - `GET /species/{species_id}`
- Added client-side `AgentResponse` TypeScript representation and related
  API request/response types.
- Added minimal in-app screen switching without adding a navigation dependency.
- Added screens:
  - Chat
  - Team Editor
  - Species Search
  - Evidence Panel
  - Settings for local API base URL
- Added `mobile/README.md` and root README local run instructions.

Boundary facts:

- Mobile calls the Product API only.
- Mobile does not shell out to CLI, read SQLite, import Python modules, call
  model providers, accept provider API keys, duplicate battle logic, duplicate
  species DB logic, or bundle official IP assets.
- API base URL setting is process-local UI state only; no durable persistence
  was added.

Install/validation:

- `cd mobile && npm install`
  - added 537 packages
  - audited 538 packages
  - `found 0 vulnerabilities`
  - warnings observed for transitive deprecated packages:
    `inflight@1.0.6`, `rimraf@3.0.2`, `glob@7.2.3`
- `cd mobile && npm run typecheck`
  - `tsc --noEmit`
  - passed with exit code `0`
- no mobile lint/test scripts are defined in P0e scaffold.

Backend regression:

- `.venv/bin/python -m unittest tests.test_api`
  - `Ran 8 tests in 0.473s`, `OK`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
  - `Ran 8 tests in 0.075s`, `OK`
- `.venv/bin/python -m unittest tests.test_advisor`
  - `Ran 21 tests in 0.796s`, `OK`
- `.venv/bin/python -m unittest discover -s tests`
  - `Ran 93 tests in 3.729s`, `OK`

Static boundary checks:

- `rg` over `mobile/src` and `mobile/App.tsx` found no Enzo/恩佐/Tencent/
  洛克王国/official-authorization positioning text.
- `rg` over `mobile/src`, `mobile/App.tsx`, and `mobile/package.json` found no
  Python imports, SQLite access, provider API key fields, or model-provider
  calls. The only battle-dex string is the Product API metadata field
  `battle_dex_available`.

Files changed:

- `README.md`
- `mobile/package.json`
- `mobile/package-lock.json`
- `mobile/.gitignore`
- `mobile/app.json`
- `mobile/tsconfig.json`
- `mobile/README.md`
- `mobile/App.tsx`
- `mobile/src/api/client.ts`
- `mobile/src/api/types.ts`
- `mobile/src/components/ResponsePanel.tsx`
- `mobile/src/screens/ChatScreen.tsx`
- `mobile/src/screens/TeamEditorScreen.tsx`
- `mobile/src/screens/SpeciesSearchScreen.tsx`
- `mobile/src/screens/SettingsScreen.tsx`
- `mobile/src/styles/theme.ts`
- `log/project_log.md`

Status:

- P0e implementation is complete and ready for mobile scaffold audit.

## 2026-04-18 - P0f Public-Release Hardening implemented

Source:

- main development thread executed `specs/p0f_public_release_hardening_request.md`

Hardening areas implemented:

- local run path:
  - added `scripts/run_local_api.sh`
  - added `scripts/run_mobile.sh`
  - updated root/mobile README local run instructions to use those scripts
- config hygiene:
  - added safe sample config `.env.example`
  - documented separation between safe sample config and live local secrets
  - tightened native config validation so placeholder or malformed values do
    not activate native runtime
- health/metadata/version coherence:
  - added central release constants under `api/release.py`
  - updated `/health` and `/metadata` with coherent service name, release
    stage, API version, unofficial notice, and placeholder rate-limit mode
- logging/redaction:
  - added small API logging helpers
  - startup and unhandled-exception logging now records only bounded event
    shape and exception type, not raw secret/path payloads
- timeout/provider-failure hardening:
  - preserved existing bounded native timeout/provider-failure behavior
  - added hardening tests for sample-config fallback and bounded unhandled API
    failures
- public disclaimer copy:
  - added neutral unofficial/not-authorized/not-official-asset-affiliation
    copy to API metadata and docs

Files changed:

- `.env.example`
- `README.md`
- `advisor/config.py`
- `api/contracts.py`
- `api/dependencies.py`
- `api/logging_utils.py`
- `api/main.py`
- `api/release.py`
- `api/services/advisor_service.py`
- `mobile/README.md`
- `mobile/src/api/types.ts`
- `mobile/src/screens/SettingsScreen.tsx`
- `scripts/run_local_api.sh`
- `scripts/run_mobile.sh`
- `tests/test_api.py`
- `tests/test_public_hardening.py`
- `log/project_log.md`

Validation:

- hardening-specific:
  - `.venv/bin/python -m unittest tests.test_public_hardening`
    - `Ran 3 tests in 0.550s`, `OK`
  - `cd mobile && npm run typecheck`
    - `tsc --noEmit`, exit code `0`
- required backend regression:
  - `.venv/bin/python -m unittest tests.test_api`
    - `Ran 8 tests in 0.567s`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
    - `Ran 8 tests in 0.147s`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`
    - `Ran 21 tests in 0.940s`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`
    - `Ran 96 tests in 3.995s`, `OK`

Intentional non-goal gaps left unchanged:

- no hosted deployment stack or cloud infra
- no authentication or payments
- no provider-key management platform
- no durable persistence or cross-device sync
- no case retrieval, embeddings, or web-in-loop
- no crawler/database expansion
- no battle-engine redesign
- no mobile feature expansion beyond release-hardening adjustments

Status:

- P0f implementation is complete and ready for hardening audit/main-thread
  decision.
- `2026-04-20`: Main thread updated execution SSD to support GUI-based thread
  forwarding without changing gate ownership. `Computer Use` is now explicitly
  treated as a courier-only mechanism: it may open approved threads, paste
  approved packets, and send them, but may not choose the next task, choose the
  target thread, rewrite a packet, or approve completion. Whitelisted default
  forwarding targets are `主开发线程`, `QA-1`, and `女娲线程`.
- `2026-04-20`: Main thread completed `Enzo integration review` and created
  `specs/enzo_integration_review.md`. Review verdict: accept the verified
  Nuwa-based Enzo draft as an internal doctrine sample for pattern extraction,
  not as a public-safe or default runtime persona. Classified outputs into
  retain / abstract / sanitize / forbid buckets, identified generic reusable
  tactical-persona patterns, and documented task-adaptation implications for
  team analysis, species role analysis, patch-direction synthesis, and
  low-evidence handling. Gate 1 is now open; next unlocked step is
  `P1a synthesis implementation spec`.
- `2026-04-20`: Main thread implemented plan-driven semi-automation scaffold
  for P1 execution. Added `specs/p1_execution_state.yaml` as the
  machine-readable gate/status file, `specs/task_packet_template.md` as the
  canonical transport envelope for worker handoff, and
  `specs/pm_console_thread_handoff.md` as a clean-thread control-console
  bootstrap. Current recorded state: Gate 1 open, `Enzo integration review`
  complete, next unlocked step is `P1a synthesis implementation spec`. The new
  state file recommends opening a fresh PM-console thread now that execution
  state exists, while keeping the current thread as the authoritative build log
  until the handoff is accepted.
- `2026-04-20`: Main thread extracted the PM Console idea into a standalone
  zero-context migration pack under `docs/pm_console_ctx_pack/`. The pack
  includes a product brief, operating model, core artifact description, and
  migration note. This formally marks the PM Console as a separate future
  project direction rather than a long-term subsystem of `Roco`.
- `2026-04-20`: PM control-console thread recorded main-thread acceptance of
  `specs/p1a_synthesis_implementation_spec.md`. Execution state advanced to
  Gate 2 open, `P1a implementation` became the next unlocked step, and a
  bounded worker handoff was created at
  `specs/p1a_implementation_task_packet.md` for `主开发线程`. No forwarding was
  performed automatically.
- `2026-04-20`: LaunchPad skill was adopted as the local control runtime for
  Roco project delivery. Initialized `.launchpad/` with a mirrored locked plan,
  execution state, packet, decision log, risk log, and PM-facing Intent Check
  for `P1a implementation`. The active LaunchPad next action is `send`, pending
  PM confirmation to dispatch the reusable executor subagent.
- `2026-04-20`: Repaired the source-control boundary by initializing
  `/Users/okfin3/project/GitHub/OKFin33/Roco` as its own Git worktree on
  branch `main`. Added a root `.gitignore`, recorded source-control and
  A-layer SQLite policy in `docs/source_control_policy.md`, migrated the
  Battle Wiki context pack into `wiki/meta/handoff_2026-04-20/`, and left
  redirect notes under `docs/battle_wiki_ctx_pack/`.

## 2026-04-27 - RN UI Closeout, Persona Id Clarification, And P7/P8 Replan

Context:

- Recent work advanced the V1 mobile surface from a functional scaffold toward
  the accepted single Agent Chat product model.
- The UI path now uses the RN handoff/prototype parity direction rather than
  the older top-level scaffold screens.
- PM review identified that the product still lacks a true natural-language
  Agent Chat core even though `/chat` is wired end-to-end.

Recorded decisions:

- Public/default persona label is `You know who`.
- Runtime/backend persona id is `you_know_who`.
- `obsidian_tactical_coach` is retained only as a legacy compatibility alias.
- `You know who` is the public-safe outward codename for an Enzo-derived
  distilled persona layer; public UI must not expose Enzo/恩佐, official
  character positioning, official lore, official dialogue, official art, or
  authorization language.
- RN UI must use the approved raster paper assets, not a low-fidelity SVG path
  recreation.
- Avatar persona wheel behavior is part of UX quality: it should use the Web
  prototype's pop-out model, including backdrop fade, anchor halo scale-in, and
  staggered spring medallions from the avatar center.

Implementation state recorded:

- Mobile active V1 route is the single Chat surface through `mobile/App.tsx`
  and `mobile/src/screens/ChatScreen.tsx`.
- Active Roco UI code lives under `mobile/src/roco/*` and
  `mobile/src/components/roco/*`.
- Older top-level scaffold UI files were removed so they cannot be accidentally
  rewired as product routes.
- Mobile settings preserve the single-chat product boundary: `队伍设置` is a
  reserved future roster/context entry, not a visible Team Analyze/Dex product
  route.
- Provider API key handling remains request-scoped and SecureStore-backed on
  mobile; runtime/local/cloud language is not exposed as normal V1 UI.

Validation recorded:

- `cd mobile && npm run typecheck` passed after UI/persona changes.
- `.venv/bin/python -m unittest tests.test_persona_profile_resolver tests.test_agent_core_orchestrator tests.test_api`
  passed with `Ran 52 tests`, `OK`.

Planning correction:

- A prior conversational answer used temporary `P8/P9` labels. That was not an
  accepted project plan and is superseded.
- PM decision: `Real Agent Chat Core` is now P7.
- PM decision: `Team Builder Structured Context MVP` is now P8.
- The former `specs/p7_team_builder_structured_context_mvp.md` was moved to
  `specs/p8_team_builder_structured_context_mvp.md`.
- New planning spec added: `specs/p7_real_agent_chat_core.md`.

Rationale:

- Team Builder improves input accuracy and reduces repeated team entry, but it
  does not fix the core product if the Agent Chat loop remains rule-router
  dominant.
- P7 must make arbitrary natural-language prompts flow through a real Agent
  planner/router with approved A/B data/tool grounding, clarifying questions,
  deterministic fallback, and persona-safe presentation.
- P8 should plug structured team context into that P7 Agent loop rather than
  becoming a separate product route.

## 2026-04-27 - P7 Real Agent Chat Core Contract And First Implementation

Context:

- PM requested P7 development, contract completion, and LaunchPad continuity.
- The identified blocker was that mobile already called `/chat`, but backend
  natural-language prompts still fell through to deterministic unsupported
  fallback when they did not match bounded router patterns.

Implemented:

- Added `specs/p7_real_agent_chat_contract.yaml`.
- Updated `specs/p7_real_agent_chat_core.md` with the implementation contract.
- Added `Intent.GENERAL_CHAT` in `advisor/runtime.py`.
- Valid native-runtime prompts now use Agent-first routing unless they are
  explicit local slash control commands.
- Deterministic router is retained as a route hint/fallback surface, not the
  default gate for native runtime.
- Natural-language help/product guidance such as "我现在该怎么用你来优化队伍？"
  now reaches Agent chat instead of local command-help text.
- Added app/API `AnalysisType.CHAT_RESPONSE` and mobile TypeScript support for
  `chat_response`.
- Added regression coverage in `tests/test_advisor.py` and `tests/test_api.py`.

LaunchPad:

- Added `.launchpad/slices/p7_real_agent_chat_core.yaml`.
- Added `.launchpad/stage_returns/p7_real_agent_chat_core_stage_return.yaml`.
- Added `.launchpad/accepted_truth/p7_real_agent_chat_core_completed.yaml`.
- Active LaunchPad surface now points to `p7b_real_agent_chat_live_provider_qa`.

Validation:

- `.venv/bin/python -m unittest tests.test_advisor tests.test_api tests.test_agent_core_contracts tests.test_agent_core_orchestrator tests.test_persona_profile_resolver`
  passed with `Ran 91 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 199 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Residual risk:

- Live provider behavior still needs QA because current validation used fake and
  TestModel native runtimes.

Correction after review:

- PM clarified that default behavior should be Agent chat; if deterministic
  router is deciding the primary UX, that is effectively a failure mode.
- P7 implementation was corrected accordingly: native runtime is Agent-first by
  default, and deterministic routing is only compatibility/fallback/hinting.

## 2026-04-27 - P7b Live Provider QA Blocked

Context:

- PM dispatched `p7b_real_agent_chat_live_provider_qa`.
- Local native runtime config exists, but secrets were not printed.

Execution:

- Ran three request-scoped native `/chat` scenarios:
  - general help/product guidance
  - missing team context clarification
  - known species grounding through dex tools
- Stored redacted summary at `artifacts/p7b/live_provider_qa_summary.json`.

Result:

- P7b verdict: `blocked`.
- All live scenarios returned `backend=pydantic_ai_native`,
  `status=failed`, `analysis_type=runtime_failure`.
- Safe surfaced reason was `provider/model failure: ModelHTTPError`.
- No provider key/base URL/model/header-name leakage was observed in recorded
  response text.

Code correction made during QA:

- Native team analysis without team context now asks for team details instead
  of requiring successful `analyze_team_structure`.
- Added regression coverage in `tests/test_advisor.py`.

Validation:

- `.venv/bin/python -m unittest tests.test_advisor tests.test_api tests.test_agent_core_contracts tests.test_agent_core_orchestrator tests.test_persona_profile_resolver`
  passed with `Ran 92 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 200 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Next:

- Need `p7c_native_provider_compatibility_diagnostic` to determine whether the
  configured provider/model supports basic chat, structured output, tool calls,
  and the PydanticAI OpenAIProvider path.

## 2026-04-28 - DeepSeek v4-pro Compatibility Fix And P7b Live QA Pass

Context:

- PM clarified the target live model is `deepseek-v4-pro`.
- DeepSeek direct `/chat/completions`, PydanticAI text output, and tool calls
  were reachable with the configured key/base URL.
- PydanticAI default structured output failed for DeepSeek with an unsupported
  `tool_choice` path.

Reference:

- DeepSeek official Tool Calls guide documents OpenAI-compatible function calls
  for `model="deepseek-v4-pro"` and confirms that the application executes the
  function and returns tool results to the model.
- The same guide describes strict mode as a beta path requiring
  `base_url="https://api.deepseek.com/beta"` and strict JSON Schema constraints,
  so Roco did not switch the runtime to strict mode.

Implemented:

- `advisor/runtime.py` now uses PydanticAI `PromptedOutput(AdvisorResponse)` for
  DeepSeek-compatible configs.
- `advisor/runtime.py` now normalizes species tool arguments and prefers
  deterministic router species query over model-supplied argument drift.
- `api/services/advisor_service.py` now applies a bounded 90s timeout for
  DeepSeek request-scoped native runtime.
- Added regression coverage in `tests/test_advisor.py` and `tests/test_api.py`.

Live QA:

- Artifact: `artifacts/p7b/live_provider_qa_summary_deepseek_v4_pro.json`.
- `general_help_agent_first`: pass, `analysis_type=chat_response`, 18.928s.
- `missing_team_clarify`: pass, `analysis_type=team_analysis`, 21.084s.
- `known_species_tool_grounding`: pass, `analysis_type=species_analysis`,
  tools included `get_species_profile`, 86.539s.
- No provider key/base URL/model/header-name leakage was observed.

Validation:

- `.venv/bin/python -m unittest tests.test_advisor tests.test_api tests.test_agent_core_contracts tests.test_agent_core_orchestrator tests.test_persona_profile_resolver`
  passed with `Ran 95 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 203 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Result:

- P7b live provider QA is now accepted.
- LaunchPad accepted truth advanced to
  `p7b_real_agent_chat_live_provider_qa_completed`.
- Remaining risk: `deepseek-v4-pro` native species grounding is slow; mobile UX
  needs progress/streaming later.

## 2026-04-28 - P8 Team Builder Structured Context Spec And Contract

Context:

- PM chose to proceed with P8 before deeper P7 optimization because structured
  team context changes the main Agent input substrate.
- P8 remains a single Chat context feature, not a Dex, Calculator, Simulator, or
  standalone Team product route.

Product decisions:

- First release supports one active team context, but every team has `team_id`
  so later multi-team switching does not require a contract rewrite.
- Team context persists locally in non-secret mobile storage; SecureStore is
  forbidden for team context.
- Team size is 0..6 selected species.
- Species UX is database search/filter plus result selection. Free-text species
  cannot become structured slot data.
- Move UX is search/filter inside the selected species' backend available move
  list. Free-text moves cannot become structured selected moves.
- No `unresolved` or `user_supplied` move state is allowed in P8 structured
  team context.
- Each selected species has fixed backend ability, one nature, 0..3
  individual-value bonus stats, and 0..4 selected moves.

Artifacts:

- `specs/p8_team_builder_structured_context_mvp.md`
- `specs/p8_team_builder_structured_context_contract.yaml`
- `.launchpad/slices/p8_team_builder_structured_context_mvp.yaml`

Next:

- P8 implementation can dispatch from this contract.
- Implementation must add `/species/{species_id}/moves`, extend `/chat` with
  `context_attachments`, validate database-grounded team context, add local
  mobile team-context storage, and attach active team context to Chat requests.

## 2026-04-28 - P8 Team Builder Structured Context MVP Implementation

Implemented:

- Added backend `TeamContextAttachment` contracts for `team_context.v1`.
- Added `GET /species/{species_id}/moves`.
- Extended `/chat` request handling with `context_attachments`.
- Added backend validation that:
  - rejects species not found in battle-dex
  - rejects selected moves not available for the selected species
  - rejects invalid team context shape through API validation
  - preserves existing session team state when no context attachment is present
- Added structured runtime injection from validated context into Advisor
  session state; no message concatenation fallback is used.
- Added mobile team-context types and API client method for species moves.
- Added `mobile/src/roco/teamContext.ts` for local non-secret FileSystem JSON
  persistence.
- Added `TeamContextBuilder` inside Settings drawer:
  - species database search/filter and selection
  - selected-species move search/filter and selection
  - one nature per selected species
  - 0..3 individual-value bonus stats
  - 0..4 selected database moves
- Chat now attaches active non-empty team context to `/chat` and renders a
  compact team chip.

Validation:

- `.venv/bin/python -m unittest tests.test_api.ApiTests.test_species_moves_endpoint_returns_available_moves_without_paths tests.test_api.ApiTests.test_chat_accepts_database_grounded_team_context_attachment tests.test_api.ApiTests.test_chat_rejects_team_context_species_not_in_battle_dex tests.test_api.ApiTests.test_chat_rejects_team_context_move_not_available_for_species tests.test_api.ApiTests.test_chat_rejects_invalid_team_context_shape`
  passed.
- `.venv/bin/python -m unittest tests.test_api tests.test_advisor` passed with
  `Ran 67 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 208 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Result:

- P8 code-level implementation is accepted.
- LaunchPad accepted truth advanced to
  `p8_team_builder_structured_context_mvp_completed`.
- Recommended next slice is simulator QA for the actual Settings builder touch
  flow and Chat attachment behavior.

## 2026-04-28 - P8 IV Rule Grounding And P8b Simulator QA

Context:

- PM asked to confirm whether the precise `7-10` individual-value rule existed
  in local data before closing P8.
- Source of truth was found outside SQLite:
  `data/reference/luoke_world_type_database_v2.json` defines
  `stat_formula.iv_rules.initial_range: 7-10`, `max_boosted_stats: 3`, PvP
  multiplier `6`, and PvP range `42-60`.
- `wiki/raw/source_notes/2026-03-25_bilibili_iv_nature_stat_training.md`
  independently records the same 7-10 IV, max-three boosted stats, and nature
  modifier information.

Implemented:

- Backend `TeamIndividualValueBonus.value` is now constrained to integer
  `7..10`.
- Mobile Team Builder displays `个体增益属性 0-3 · 数值 7-10`.
- Mobile IV controls now expose chips `7`, `8`, `9`, and `10` after selecting
  a bonus stat.
- P8 spec and contract were updated to cite the A-layer reference JSON as the
  range source.
- Added API regression test rejecting IV value `11`.

P8b simulator QA:

- Device: iPhone 17 simulator, iOS 26.4.
- Opened Settings -> `队伍设置`.
- Searched `豆丁鱼` and selected the backend result.
- Verified selected species editor shows fixed ability `洄游`, nature controls,
  IV controls, and backend available move list.
- Selected IV bonus `精力=10`.
- Selected move `潮涌`.
- Saved the team and returned to Chat.
- Chat displayed `队伍上下文 · 1/6 · 豆丁鱼`.

Validation:

- `.venv/bin/python -m unittest tests.test_api tests.test_advisor` passed with
  `Ran 68 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 209 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Result:

- P8b simulator QA is accepted for iOS.
- LaunchPad accepted truth advanced to
  `p8b_team_builder_simulator_qa_completed`.
- Android simulator QA remains open.
- No paid live LLM request was sent from the simulator during P8b; backend
  attachment behavior is covered by contract tests.

## 2026-04-28 - P8 Team Builder Regional Form Disambiguation

Context:

- PM identified a Team Builder ambiguity for same-name species with distinct
  regional forms, e.g. `皇家狮鹫` has both `崖间地的样子` and `高山地的样子`.
- The runtime database already stores `form_name` and `regional_form_name` in
  `species_form`, but `/species/search` did not expose them to mobile.
- Product decision: whenever `regional_form_name` is present, UI displays
  `display_name（regional_form_name）`; otherwise it displays `display_name`.
  The structured identity remains `species_id`.

Implemented:

- `SpeciesSearchHit` and API `SpeciesSearchItem` now include `form_name` and
  `regional_form_name`.
- `BattleDexRepository.search_species()` now selects the two form fields from
  SQLite.
- Mobile `SpeciesSearchItem` type was updated.
- Team Builder search results now show disambiguated labels such as
  `皇家狮鹫（崖间地的样子）`.
- Selected team slots store the same public display label while preserving
  backend `species_id` for validation and chat context.
- Search result metadata includes initial form, form name, and type line.
- Added API regression coverage for `皇家狮鹫` returning both regional forms.

Validation:

- `.venv/bin/python -m unittest tests.test_api` passed with `Ran 40 tests`,
  `OK`.
- `cd mobile && npm run typecheck` passed.

Result:

- Same-name regional forms are now distinguishable before and after selection.
- No search rule change was made; species search still matches species name or
  initial species name containing the keyword.

## 2026-04-28 - P8 Team Builder UI Handoff Correction

Context:

- UI design thread completed a later Team Builder handoff:
  `mobile/ROCO_P8_TEAM_BUILDER_UI_HANDOFF.md`.
- The handoff clarified that Chat main screen should not show an active team
  chip. Saved team context is still sent silently with chat requests through
  `context_attachments`.
- The handoff also confirmed the visible stat label for internal `hp` is
  `生命`, not `精力`.

Verification:

- `mobile/src/screens/ChatScreen.tsx` no longer renders a visible team chip.
- It still sends `context_attachments: activeChatContextAttachments(teamContextStore)`.
- iOS simulator accessibility tree no longer exposes `队伍上下文 · 1/6 · 豆丁鱼`.

Log handling:

- Earlier P8b entries that recorded a visible Chat chip and `精力=10` are left
  intact as historical observations.
- LaunchPad stage return and accepted truth received post-hoc correction fields
  instead of destructive rewrites.
- Current active surface and P8 contract now state the current requirement:
  `生命=10` in UI wording and silent team context attachment in Chat.

## 2026-04-28 - P9 DeepSeek Runtime Config QA Contract

Context:

- Simulator Agent Chat currently reaches the backend/native runtime but fails
  with `provider/model failure: ModelHTTPError`.
- The simulator is configured with `deepseek-v4-flash`; prior P7b live QA pass
  was with `deepseek-v4-pro`.
- PM wants to test `flash/pro` and thinking-mode combinations, then choose a
  sane recommended configuration while preserving custom provider settings for
  open-source users.

Reference:

- DeepSeek official docs list `deepseek-v4-flash` and `deepseek-v4-pro` under
  OpenAI-compatible `https://api.deepseek.com`.
- DeepSeek docs say both support thinking modes, JSON output, and tool calls.
- DeepSeek docs say thinking defaults to enabled and can be controlled with
  `thinking` plus `reasoning_effort`.
- DeepSeek docs warn that thinking+tool calls require preserving/replaying
  `reasoning_content`.

Artifacts:

- Added `specs/p9_deepseek_provider_qa_plan.md`.
- Added `specs/p9_deepseek_runtime_config_contract.yaml`.
- Updated `.launchpad/slices/p9_agent_latency_loading_and_flash_probe.yaml`.

Decision state:

- P9 is contract-ready, not implementation-ready.
- Next step is PM acceptance to run the one-shot live QA matrix.
- Live QA may consume DeepSeek tokens.

## 2026-04-28 - P9 DeepSeek Live Matrix

Execution:

- Ran `.venv/bin/python artifacts/p9/run_deepseek_matrix.py`.
- Artifacts:
  - `artifacts/p9/deepseek_matrix_summary.json`
  - `artifacts/p9/deepseek_matrix_summary.md`
  - `artifacts/p9/redaction_check.txt`

Results:

- Direct provider basic chat passed for:
  - `deepseek-v4-flash` thinking disabled
  - `deepseek-v4-flash` thinking enabled/high
  - `deepseek-v4-pro` thinking disabled
  - `deepseek-v4-pro` thinking enabled/max
- Direct provider minimal tool-call probe passed for all four combinations.
- Roco `/chat` general Agent chat passed:
  - flash: 3.787s
  - pro: 15.412s
- Roco species grounding failed:
  - flash returned `chat_response` and did not call `get_species_profile`.
  - pro refused/unsupported and did not call `get_species_profile`.
- Roco P8 team-context chat failed quality:
  - responses did not use the selected species name `豆丁鱼`
  - responses asked for context already supplied by `context_attachments`
- Invalid model negative diagnostic produced bounded runtime failure.
- Redaction check passed.

Conclusion:

- DeepSeek provider availability is not the blocker.
- Roco-side native grounding and team-context prompt injection are the blocker.
- `deepseek-v4-flash` is a credible fast simple-chat candidate.
- No grounded-analysis preset should be recommended until P9b repair passes.

## 2026-04-28 - P9b Runtime Config And Grounding Repair

Execution:

- Added request-scoped reasoning headers:
  - `X-Roco-Reasoning-Mode`
  - `X-Roco-Reasoning-Effort`
- Added backend model-service diagnostic endpoint:
  - `POST /runtime/model-diagnostic`
- Updated mobile Settings:
  - Product API test does not send provider key.
  - Model service test sends provider key only on explicit user action.
  - DeepSeek-oriented recommended mode, thinking toggle, and reasoning effort
    controls are now represented in runtime settings.
- Repaired grounding:
  - compact species prompts resolve against SQLite before model synthesis.
  - P8 team context preserves display name, ability, selected moves, nature,
    IV bonuses, and base stats.
  - known species/team routes use deterministic pre-grounding for facts.

Validation:

- `.venv/bin/python -m unittest tests.test_api tests.test_advisor tests.test_agent_core_orchestrator tests.test_agent_core_contracts`
  - pass, 93 tests.
- `npm run typecheck` in `mobile/`
  - pass.
- `.venv/bin/python artifacts/p9/run_roco_grounding_focus.py`
  - pass, focused live QA `overall_ok=true`.
- `artifacts/p9/p9b_redaction_check.txt`
  - `redaction=pass`.

Conclusion:

- `deepseek-v4-flash` with thinking disabled is now a valid V1 fast candidate
  for simple chat and repaired grounded known-fact routes.
- Balanced/deep presets are still not accepted as defaults.
- P9c should convert the result into release-safe preset QA and simulator
  settings verification.

## 2026-04-29 - P9c Direction Correction: Call Policy Before Preset UI

Context:

- PM challenged whether Roco had ever systematically designed Agent call/loop
  policy.
- Current conclusion: prior P7-P9 work established provider connectivity,
  grounding data, team context, persona boundaries, and safety rails, but did
  not define a complete call/loop policy.
- Deterministic/pre-grounding is not the final Agent experience. It is the data
  preparation layer that supplies facts to LLM synthesis.

Decision:

- P9c is re-scoped from preset UI QA to Agent Call Policy and Loop Policy
  contract design.
- V1 default should be 0-2 LLM calls per `/chat` message.
- Adaptive loop is disabled by default and forbidden for unknown intent.
- Unknown intent must clarify or refuse safely, not enter autonomous search.

Artifacts:

- Added `specs/p9c_agent_call_policy_contract.yaml`.
- Added `specs/p9c_agent_loop_policy_contract.yaml`.
- Replaced `.launchpad/slices/p9c_deepseek_preset_release_qa.yaml` with
  `.launchpad/slices/p9c_agent_call_policy_contract.yaml`.
- Updated `.launchpad/active_surface.md`.

Current open questions:

- Whether `team_build_advice` and `complex_strategy` should be V1 supported or
  postponed.
- Whether L3 two-call strategy planning is acceptable for token cost.
- Which model policy should be accepted after call-policy QA, beyond the
  current fast candidate `deepseek-v4-flash + thinking disabled`.

## 2026-04-29 - P9c Blind Strategy Eval Planning

Context:

- PM requested preparation for blind testing before running provider calls.
- The core comparison is `flash/off` vs `flash/on` vs `pro/off` vs `pro/on`
  on real Roco strategy tasks.
- The goal is to select a call policy, not crown a globally best model.

Artifacts:

- Added `specs/p9c_strategy_blind_experiment_design.md`.
- Added `specs/p9c_strategy_eval_rubric.yaml`.
- Added `specs/p9c_strategy_blind_execution_plan.md`.

Design:

- Test call scenes:
  - `grounded_synthesis`
  - `strategy_generation`
  - `strategy_critique`
  - `complex_strategy_2call`
- Use blinded answer ids so model/config identity is hidden during quality
  scoring.
- Hide latency/cost until quality scores are locked.
- Score grounding fidelity, strategic depth, actionability, risk awareness,
  constraint following, concision, persona fit, and clarify/refusal quality.

Execution boundary:

- No live provider QA was run in this step.
- The live blind run is a separate dispatch because it consumes provider tokens.

## 2026-04-29 - P9c Minimal Blind Strategy Eval Scored

Context:

- A separate execution thread completed the minimal blind generation under
  `artifacts/p9c_strategy_eval/`.
- Generated set: 5 scenarios, 20 anonymous answers, 0 failed calls.
- Redaction check passed.

Scoring boundary:

- Scoring used only the anonymous review packet, score sheet template,
  redaction summary, generation summary, and the rubric.
- `raw_answers.json` and `reveal_map.json` were intentionally not read during
  scoring.
- Scores are locked before reveal.

Artifacts:

- Added `artifacts/p9c_strategy_eval/score_sheet_completed.csv`.
- Added `artifacts/p9c_strategy_eval/blind_scoring_summary.md`.

Blind winners by scenario:

- S1: `S1_C`.
- S4: `S4_A`.
- S6: `S6_B`.
- S7: `S7_C`.
- S8: `S8_B`.

Next action:

- Reveal model/config identity after locked scoring, then compare quality with
  latency/cost and decide the recommended P9 call policy.

## 2026-04-29 - P9d Protocol Continuity Infrastructure Gap Fixed

Context:

- PM correctly identified a broader risk class: Roco had been assuming some
  foundational Agent infrastructure existed when it did not.
- The immediate blocker was DeepSeek thinking+tool long-dialog stitching.
- Prior runtime continuity only preserved business state such as current team
  and species context; it did not preserve provider/model message history.

Severity:

- This is recorded as a serious architecture miss, not a minor prompt issue.
- It invalidates any attempt to accept `pro_max` loop behavior before protocol
  continuity is live-tested.

Implementation:

- Added native model protocol history fields to `AdvisorSessionState`.
- Native PydanticAI runtime now passes prior `message_history` when the same
  provider/model/thinking configuration continues.
- Successful native runs now store `result.all_messages()`.
- Request-scoped user-key runtime now reuses an in-memory state store by
  `session_id` without persisting API keys or native orchestrators.
- Native protocol history is capped to avoid unbounded growth.
- Request-scoped native session stores now have TTL/eviction.
- Added focused coverage for both direct advisor runtime and `/chat`
  request-scoped runtime.

Artifacts:

- Added `specs/p9d_reasoning_effort_loop_eval_design.md`.
- Added `specs/p9d_reasoning_effort_loop_execution_plan.md`.
- Added `specs/p9d_foundational_infrastructure_audit.md`.

Verification:

- `.venv/bin/python -m unittest tests.test_advisor tests.test_api`
- Result: 75 tests passed.

Residual risk:

- Protocol history support is implemented, but DeepSeek thinking+tool
  long-dialog behavior still needs P9d S10 live-provider validation.
- Native message history now has count/TTL guards, but still needs semantic
  compaction and stronger hidden-reasoning redaction tests before long public
  sessions.

## 2026-04-29 - P9d Full Gated Run Blocked At S10

Context:

- A separate P9d execution thread ran the gated provider/capability workflow.
- Output directory: `artifacts/p9d_reasoning_effort_loop_eval/`.
- Scenario count: 1.
- Answer count: 2.
- Failed calls: 1.
- Redaction: pass.

Result:

- Provider capability probe passed for `flash_disabled`, `flash_high`,
  `pro_disabled`, `pro_high`, and `pro_max`.
- S10 `pro_high_long_context` completed and reused prior tool evidence.
- S10 `pro_max_long_context` failed with `empty_final_answer`.
- There was no provider 400, no hidden reasoning leak, and the prior
  tool/reasoning history was included.

Interpretation:

- The immediate blocker is not basic DeepSeek thinking+tool protocol.
- The blocker is controlled-loop/finalization infrastructure: `pro_max` kept
  requesting tools until the S10 call budget ended, leaving no final synthesis.

Artifact:

- Added `artifacts/p9d_reasoning_effort_loop_eval/blocker_analysis.md`.

Next required repair:

- Add loop finalization control before rerunning full P9d:
  - reserve one final LLM call after the last tool observation,
  - disable tools when only final-call budget remains,
  - maintain a compact evidence ledger for "不要重查",
  - record explicit stop reasons.

## 2026-04-29 - P9d S10 Executor Finalization Repair

Context:

- The P9d S10 blocker was traced to the artifact executor, not to a provider
  400 or hidden-reasoning leak.
- `pro_max_long_context` spent the sixth S10 model call on another tool request
  and had no remaining model call for final synthesis.

Repair:

- Updated `artifacts/p9d_reasoning_effort_loop_eval/run_full_gated_eval.py`.
- Added explicit S10 constants for max LLM calls, tool calls, final-call
  reserve, and local rounds per turn.
- S10 now reserves the final call, disables tools during final synthesis, and
  injects a finalization prompt with the compact evidence ledger.
- Added evidence ledger tracking from tool observations so Turn 2 can receive
  already-checked evidence instead of relying only on prompt memory.
- Added trace fields for remaining LLM calls, tools-enabled state, stop reason,
  and evidence ledger summary.

Verification:

- `.venv/bin/python -m py_compile artifacts/p9d_reasoning_effort_loop_eval/run_full_gated_eval.py`
- `.venv/bin/python artifacts/p9d_reasoning_effort_loop_eval/run_full_gated_eval.py`
  correctly refuses live provider calls without `--yes-live`.

Residual risk:

- This repair has not rerun live DeepSeek calls.
- If S10 quality drops because five tool-capable calls plus one final call is
  too tight, the next experiment should compare the fixed 6-call budget against
  an explicit expanded 8-call budget instead of silently raising the cap.

## 2026-04-29 - Terminal Response Phase Promoted To Global Policy

Decision:

- The P9d S10 failure exposed a broader runtime invariant: every `/chat`
  execution needs a terminal response phase owned by Roco runtime, not by the
  model.
- This is broader than loop policy. It applies to fixed workflows, tool-call
  workflows, multi-call generate/critic workflows, and future controlled loops.

Contract updates:

- `specs/p9c_agent_call_policy_contract.yaml` now defines
  `terminal_response_policy`.
- `specs/p9c_agent_loop_policy_contract.yaml` now inherits that policy and
  requires future loops to reserve terminal synthesis budget.
- `.launchpad/slices/p9c_agent_call_policy_contract.yaml` acceptance criteria
  now include terminal response reservation.

Boundary:

- This does not mean every request needs an extra LLM call.
- L0/static/refusal/data-missing paths can terminally answer deterministically.
- If final natural-language synthesis is needed after tools, grounding, or
  internal generation, the last LLM call must be reserved with tools disabled.

## 2026-04-29 - P9d Live Rerun After S10 Repair

Run:

- Command: `.venv/bin/python artifacts/p9d_reasoning_effort_loop_eval/run_full_gated_eval.py --yes-live`
- Output directory: `artifacts/p9d_reasoning_effort_loop_eval/`.
- Elapsed seconds: `843.385`.
- Scenario count: `6`.
- Answer count: `12`.
- Redaction: pass.
- Stop gate triggered: false.

Result:

- S10 passed for both `pro_max_long_context` and `pro_high_long_context`.
- `pro_max_long_context` used 5 LLM calls, reused prior tool evidence, and
  recorded `final_call_reserved=true`.
- `pro_high_long_context` completed in 4 LLM calls, reused prior tool evidence,
  and did not need the reserved final budget because it produced an answer
  before the last round.
- S9 still failed both loop configs:
  - `pro_max_loop`: `no_final_answer_before_call_limit`.
  - `pro_high_loop`: `tool_call_limit_exceeded`.

Interpretation:

- The S10 fix worked.
- The same terminal-response invariant must be applied to S9 and any future
  loop harness; otherwise loop eval can still produce expensive non-answers.

Follow-up repair:

- Updated `run_full_gated_eval.py` S9 controlled-loop executor to reserve the
  final LLM call, disable tools during final synthesis, pass the evidence
  ledger, and record terminal-budget trace fields.
- Verification: Python compile check passed; non-live invocation still refuses
  provider calls unless `--yes-live` is set.

Residual risk:

- P9d should be rerun once more after the S9 executor repair before accepting
  loop-policy conclusions.

## 2026-04-29 - Production Native Runtime Terminal Budget Guard

Context:

- PM clarified that terminal response reservation must be enforced from the
  production `/chat` runtime, not only in P9d artifact executors.
- Current production native path uses PydanticAI `Agent.run_sync`, so Roco does
  not directly own each raw provider round the way the P9d OpenAI harness does.

Implementation:

- Added native runtime usage limits by route in `advisor/runtime.py`.
- General chat now receives a one-request, zero-tool budget.
- V1 team/species native tool paths receive bounded request/tool budgets that
  include the terminal response phase.
- If PydanticAI raises `UsageLimitExceeded`, Roco now returns a controlled
  terminal budget response instead of an empty answer or unbounded retry.
- Added tests that assert native runtime passes usage limits and returns a
  terminal budget response on usage-limit exhaustion.

Boundary:

- This is a production guard for budget and non-empty terminal behavior.
- It does not yet replace PydanticAI with a raw per-round executor that can
  forcibly remove tool definitions on the final provider request.
- Final response model selection is still call-policy work; this change does
  not hardcode final responses to `pro_on`.

Verification:

- `.venv/bin/python -m py_compile advisor/runtime.py tests/test_advisor.py`
- `.venv/bin/python -m unittest tests.test_advisor`
- `.venv/bin/python -m unittest tests.test_advisor tests.test_api`
- Result: `77` tests passed for advisor+API suite.

## 2026-04-29 - P9d Targeted S9 Terminal Fix Smoke

Run:

- Targeted live smoke only for S9 controlled loop configs.
- Artifact: `artifacts/p9d_reasoning_effort_loop_eval/s9_targeted_terminal_fix_smoke.json`.
- Result: both configs still failed because models exhausted tool budget before
  final response.

Repair:

- Updated S9 executor so over-budget tool requests receive refused tool
  observations instead of aborting the run.
- Once tool budget is exhausted, the next model call is forced into final
  synthesis with tools disabled.

Run:

- Targeted live smoke v2 only for S9 controlled loop configs.
- Artifact: `artifacts/p9d_reasoning_effort_loop_eval/s9_targeted_terminal_fix_smoke_v2.json`.
- Elapsed seconds: `370.935`.

Result:

- `pro_high_loop`: final answer produced, `final_call_reserved=true`, within
  180s.
- `pro_max_loop`: final answer produced, `final_call_reserved=true`, but took
  `204.781s`, exceeding the S9 180s hard timeout.
- Both configs requested one tool over budget; the executor refused the excess
  tool and still produced final synthesis.

Follow-up:

- Updated S9 executor timeout handling so an over-180s final answer is still
  marked `loop_timeout` in future runs.
- Do not treat `pro_max_loop` as accepted under the current S9 budget.

## 2026-04-30 - P9e Runtime Policy Closure Prepared

Decision:

- P9 should no longer aim at a user-facing fast/balanced/deep preset matrix.
- The mainstream open-source mode is `custom_single_model`: user supplies
  provider base URL, API key, model id, and supported reasoning settings; all
  calls use that one model configuration.
- Roco's maintained recommendation is one `roco_deepseek_v4_reference` profile,
  where Roco may route by call role using DeepSeek v4 flash/pro and thinking
  settings after QA.

Contract changes:

- Added `specs/p9e_runtime_policy_closure_contract.yaml`.
- Added `.launchpad/slices/p9e_runtime_policy_closure.yaml`.
- Updated `specs/p9_deepseek_runtime_config_contract.yaml` away from
  fast/balanced/deep preset wording.
- Updated `specs/p9c_agent_call_policy_contract.yaml` to name
  `custom_single_model` as primary user mode and DeepSeek v4 as the certified
  reference profile candidate.
- Updated LaunchPad active surface/runtime state to P9e.

Current evidence carried into P9e:

- S10 long-context thinking/tool continuity passes for pro high/max after
  terminal reservation repair.
- S9 terminal control now produces final answers for pro high/max targeted
  smoke v2.
- `pro_max_loop` exceeds the current 180s S9 latency budget and should not be
  recommended without explicitly changing budget.
- Production native `/chat` has a usage-limit terminal guard but still relies
  on PydanticAI for internal raw provider rounds.

Next:

- Dispatch P9e to close contracts and draft the DeepSeek v4 reference profile.
- Decide whether full P9d rerun is worth the token/time cost after targeted
  S9/S10 evidence.

## 2026-04-30 - P9e Runtime Policy Closure Draft Completed

Dispatch result:

- Completed P9e draft closure.
- Added `specs/p9e_deepseek_v4_reference_profile.yaml`.
- Added `specs/p9e_custom_single_model_support_level.yaml`.
- Updated `specs/p9e_runtime_policy_closure_contract.yaml` dispatch result and
  acceptance criteria.
- Marked `.launchpad/slices/p9e_runtime_policy_closure.yaml` as
  `completed_draft`.
- Updated LaunchPad runtime surface to PM Acceptance Check.

DeepSeek v4 reference profile draft:

- Simple chat / honesty / routine grounded synthesis: `deepseek-v4-flash` with
  thinking disabled.
- Complex strategy and critique/arbitration: `deepseek-v4-pro` with thinking
  enabled and reasoning effort `high`.
- Controlled loop: disabled by default in V1; if explicitly enabled later,
  only `pro_high_loop` remains a candidate under the current budget.
- `pro_max_loop` is not recommended under the current S9 180s timeout because
  targeted S9 smoke v2 took `204.781s`.

Custom single-model support:

- Defined as the mainstream open-source mode.
- All LLM calls use the user's chosen provider/base URL/model/reasoning config.
- Roco guarantees runtime safety, redaction, budget, timeout, and controlled
  failure; Roco does not certify arbitrary provider quality or latency.

Verification:

- YAML parse passed for P9e contracts, updated P9 contracts, and LaunchPad
  runtime state.

PM options:

- Accept P9e draft as the P9 policy closure baseline.
- Request full P9d rerun before acceptance.
- Revise call-role mapping in the DeepSeek reference profile.

## 2026-04-30 - P9e Review Finding Fixes

Fixes:

- Replaced residual DeepSeek preset naming with reference-profile naming in
  `specs/p9_deepseek_runtime_config_contract.yaml`.
- Changed P9 QA matrix wording so pro thinking reference default is `high`; max
  is marked experimental latency risk only.
- Clarified complex strategy reference profile: default is one `pro_high` LLM
  call; two calls are only allowed when candidate generation/comparison needs a
  separate terminal synthesis and latency budget permits it.
- Replaced old `upgrade_candidates` in `p9c_agent_call_policy_contract.yaml`
  with `historical_evidence_only` to avoid recreating a multi-preset matrix.

Rationale:

- `max_llm_calls=2` is a V1 product/runtime budget, not a model capability
  limit. It exists to keep normal `/chat` latency, cost, and QA surface bounded.
- Any workflow needing more than two LLM calls should be treated as controlled
  loop or future advanced workflow, not ordinary V1 chat.

## 2026-04-30 - P9e Runtime Policy Closure Accepted

Acceptance:

- PM accepted P9e as the P9 policy closure baseline.
- Added `.launchpad/accepted_truth/p9e_runtime_policy_closure_completed.yaml`.
- Marked `.launchpad/slices/p9e_runtime_policy_closure.yaml` as completed.
- Marked `specs/p9e_runtime_policy_closure_contract.yaml` as accepted.
- Updated LaunchPad runtime state to `Next Stage Check`.

Accepted baseline:

- Mainstream open-source mode: `custom_single_model`.
- Certified reference profile draft: `roco_deepseek_v4_reference`.
- No V1 fast/balanced/deep user preset matrix.
- No V1 ordinary-user advanced per-role routing UI.
- V1 controlled loop remains disabled by default.
- `pro_max_loop` remains not recommended under current 180s S9 budget.

Next recommended stage:

- `p10_v1_release_integration_plan`: integrate P7 real Agent chat, P8 team
  builder structured context, and P9 runtime/model policy into the V1 app
  release path.

## 2026-04-30 - P10 V1 Release Integration Plan Draft Completed

Dispatch result:

- Created `specs/p10_v1_release_integration_plan.yaml`.
- Created `.launchpad/slices/p10_v1_release_integration_plan.yaml`.
- Updated LaunchPad runtime state to PM Acceptance Check for P10.
- Updated active surface with P10 acceptance/dispatch options.

Integrated baseline:

- P7 real Agent chat is the default product path for valid native-runtime
  natural-language prompts.
- P8 team context is built from database-selected species/moves and sent as
  `team_context.v1` through `/chat`.
- P8b's later UI correction is preserved: active team context may be attached,
  but the main Chat surface must not show the old visible
  `队伍上下文 · 1/6 · ...` chip.
- P9e runtime policy is the release baseline: mainstream custom single-model
  plus one Roco DeepSeek v4 reference profile; no fast/balanced/deep preset
  matrix in V1.

Next executable slices:

- `p10a_mobile_settings_policy_alignment`: remove residual recommended-mode
  preset wording and align Settings/README with P9e.
- `p10b_chat_contract_integration_audit`: verify persona, team context,
  provider headers, and public-safe presentation all work together.
- `p10c_release_smoke_qa`: run backend/mobile/simulator/security release smoke,
  with paid live provider smoke only after explicit PM approval.

Carry-forward risks:

- Android SecureStore/simulator QA is still open.
- Slow DeepSeek pro calls still need progress/loading UX.
- PydanticAI still owns part of raw provider-round control despite production
  usage-limit terminal guards.
- `mobile/README.md` may have paper asset path drift.

## 2026-04-30 - P10 Accepted And P10a Mobile Settings Policy Alignment

Acceptance:

- PM dispatch accepted `p10_v1_release_integration_plan`.
- Added `.launchpad/accepted_truth/p10_v1_release_integration_plan_completed.yaml`.
- Advanced active LaunchPad slice to `p10a_mobile_settings_policy_alignment`.

P10a implementation:

- Replaced mobile runtime settings public preset fields with `modelProfile`.
- Supported values are now:
  - `custom_single_model`
  - `deepseek_v4_quick_setup`
- Removed user-visible `manual/fast/balanced/deep` Settings controls.
- Removed `recommended mode` wording from `mobile/README.md`.
- Kept backward-compatible migration from old stored DeepSeek/preset values to
  `deepseek_v4_quick_setup`.
- Preserved request-scoped native runtime provider headers for the custom
  single-model path.

Important boundary:

- P10a does not yet implement backend per-call-role reference routing.
- Current DeepSeek mobile selection is only a quick setup path that still uses
  the release-compatible concrete model header path.
- This avoids falsely presenting the future `roco_deepseek_v4_reference`
  call-role router before backend routing exists.

Verification:

- `cd mobile && npm run typecheck` passed.

## 2026-05-01 - P10h Pivot Rollup For Redteam

Purpose:

- This entry is the current compact summary of the P10h strategy pivot.
- Earlier P10h entries are preserved as historical log, including the original
  heuristic-first plan and full-spectrum extraction work.
- Some older P10h/P10b entries are not perfectly chronological in this file, so
  this rollup should be used as the redteam entry point.

Former route:

- P10h originally aimed to use B-layer materials and extracted cases to produce
  `candidate_heuristics`, then compile route-specific Coach Policy slices for
  runtime injection.
- Full-spectrum extraction from `wiki/cache/` produced useful candidate pools,
  tags, counterexamples, validation tasks, and name-resolution issues.

Redteam conclusion:

- DSPy-style prompt optimization is not a good fit yet because Roco lacks a
  large stable eval set and tactical advice quality is hard to auto-score.
- A large hand-written or LLM-distilled tactical rulebook is also not the right
  first runtime asset because it is brittle, meta-sensitive, and loses expert
  judgement texture.
- The better route is example-first: expert demonstrations from high-player
  videos/transcripts, PM-reviewed for source fidelity, retrieved as analogies
  at runtime.

Current route:

- P10h mainline is now D-layer Expert Demonstration Case Memory.
- D-layer gold cases are not facts and not governance rules. They are
  source-faithful examples of how an expert judged a concrete situation.
- PM's role is editor/fidelity reviewer: check whether extraction preserves the
  expert's source meaning, not whether PM is the final tactical authority.
- Runtime target is eventually:
  A-layer facts + optional B-layer mechanics + 0-3 retrieved D-layer gold cases
  + C-layer use protocol + persona expression.

Scale decision:

- Probe: 8-12 PM-reviewed gold cases.
- MVP: 15-25 PM-reviewed gold cases.
- V1 usable: 30-50 PM-reviewed gold cases.
- Continuous: 50+ only for patch/meta/species coverage, not mechanical growth.
- Coverage target is reusable reasoning-pattern breadth, not equal counts across
  every subtype.

Quality priority:

1. source fidelity;
2. factual grounding;
3. reasoning completeness;
4. transferability;
5. boundary quality.

Boundary:

- Reasoning completeness is only a ranking signal after source fidelity and
  A-layer factual grounding pass.
- Complete but invented reasoning must be rejected.
- D-layer cases cannot override A-layer facts.
- Candidate cases cannot enter runtime retrieval until PM fidelity review.
- Heuristics are now tags, audit summaries, or future thin-protocol candidates,
  not runtime tactical rules.

Current artifacts:

- `specs/p10h_tactical_coach_policy_distillation_plan.md` is the current D-layer
  plan despite the legacy filename.
- `specs/p10h_expert_demo_extraction_manual.md` is the Agent-executable manual
  for processing one transcript.
- `specs/p10h_casebank_seed_schema.yaml` contains expert demonstration fields,
  evidence trace types, and quality-score dimensions.
- `specs/p10h_coach_policy_heuristic_schema.yaml` is explicitly deprecated for
  runtime mainline.
- `artifacts/p10h_name_resolution_cleanup/` remains a required pre-gold
  promotion gate.

Next intended execution:

- Run P10h-C on one or a small first wave of transcript sources using the
  extraction manual.
- Output candidate cases, source spans, A-layer validation tasks, comparison
  report, and PM review packet.
- Do not modify runtime and do not auto-ingest gold cases.

## 2026-05-01 - P10h CC Redteam Fixes Applied

Trigger:

- External review agreed with the D-layer pivot but identified execution-layer
  gaps: retrieval/generation seam too thin, name resolution under-specified,
  prompt case formatting absent, fine case types possibly over-filtering, and a
  schema legacy-field overlap.

Changes:

- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md` with:
  - explicit initial retrieval decision: tag filtering plus BM25/simple lexical
    scoring; embeddings deferred until recall failures justify them;
  - retrieval fallback behavior when no case matches;
  - conflict-case behavior: preserve branch conditions, do not force consensus;
  - recall@top3 smoke gate: at least 80% recovery on probe
    `user_question_equivalent` queries;
  - D-layer prompt block shape and separation from A-layer facts;
  - name-resolution strategy with exact lookup, fuzzy/alias candidates,
    contextual disambiguation, and PM adjudication;
  - unresolved-name escalation thresholds.
- Updated `specs/p10h_casebank_seed_schema.yaml` so
  `accepted_interpretation` is no longer required and is marked
  backward-compatible only.
- Updated `specs/p10h_expert_demo_extraction_manual.md` with retrieval
  granularity policy and name-resolution escalation rules.

Decisions:

- Fine case types remain useful for extraction and review, but runtime retrieval
  should first use coarse family and tags while the pool is small.
- Gold promotion remains blocked by unresolved canonical names, but a dedicated
  source-local alias pass is required when unresolved-rate is high.

## 2026-05-01 - P10h Name Resolution Cleanup Pass 1 Completed

Trigger:

- PM flagged that community/ASR names such as `霹莉花`, `球卡`, `水母`, and
  `修罗` may be hard to recognize and should be cleaned before Coach Policy
  promotion.

Result:

- Added `artifacts/p10h_name_resolution_cleanup/README.md`.
- Added `artifacts/p10h_name_resolution_cleanup/suspect_name_inventory.yaml`.
- Added `artifacts/p10h_name_resolution_cleanup/battle_dex_lookup_results.yaml`.
- Added `artifacts/p10h_name_resolution_cleanup/merged_v2_name_cleanup_overlay.yaml`.
- Added `artifacts/p10h_name_resolution_cleanup/name_resolution_review_table.md`.
- Added `artifacts/p10h_name_resolution_cleanup/patch_plan.md`.

Key findings:

- Safe/canonical examples include `水母` -> `琉璃水母`, `花狐`/`狐仙` ->
  `尖嘴狐仙`, `提塔` -> `缇塔`, and `力毒修罗` -> `厉毒修萝`.
- Medium-confidence overlays include `霹莉花` -> `奇丽花`, `球卡` -> `裘卡`,
  `修罗` -> `厉毒修萝`, `布枯咕`/`不哭咕` -> `怖哭菇`, and
  `韩医蛇`/`寒医蛇` -> `寒音蛇`.
- Existing canonical names such as `贝古斯`, `电球咩咩`, `黑猫巫师`,
  `声波缇塔`, and `尖嘴狐仙` are now marked `exact_no_change`.

Boundary:

- The merged v2 case pool was not destructively rewritten.
- Medium-confidence ASR corrections remain overlay-only until A-layer
  role/move/matchup validation confirms the semantics.

Verification:

- YAML validation passed for all generated cleanup YAML files.

## 2026-05-01 - P10h Name Resolution Cleanup PM Corrections Added

Trigger:

- PM requested `水母` context before deciding, and corrected several ASR
  mappings.

Result:

- Added `artifacts/p10h_name_resolution_cleanup/water_jellyfish_context.md`.
- Updated `merged_v2_name_cleanup_overlay.yaml`,
  `battle_dex_lookup_results.yaml`, and `name_resolution_review_table.md`.
- Updated `patch_plan.md` with PM-confirmed corrections.

PM-confirmed mappings:

- `星光师` / `金光师` -> `星光狮`.
- `化电城铁` -> `画间沉铁兽`.

Current `水母` recommendation:

- Keep `水母` / `水母_ASR` as source aliases.
- Normalize promoted artifacts to `琉璃水母` unless PM rejects after reviewing
  the focused context file.

## 2026-05-01 - P10h Pivoted To Expert Demonstration Casebank

Trigger:

- PM accepted the critique that P10h should not optimize around a large
  heuristic/rule distillation route. Final tactical quality has priority over
  preserving the previous plan.

Decision:

- P10h mainline is now D-layer Expert Demonstration Case Memory.
- High-player video transcripts are treated as expert demonstration sources.
- PM review checks source fidelity, not universal tactical correctness.
- Runtime should eventually retrieve 0-3 PM-reviewed gold cases as analogies,
  while A-layer facts remain authoritative.

Changes:

- Rewrote `specs/p10h_tactical_coach_policy_distillation_plan.md` around the
  D-layer Expert Demonstration Casebank route.
- Updated `specs/p10h_casebank_seed_schema.yaml` to include
  `expert_demonstration` fields, `pm_fidelity_reviewed`, source spans,
  retrieval tags, caveats, and negative/failure branches.
- Updated `specs/p10h_coach_policy_heuristic_schema.yaml` to mark the
  heuristic route as deprecated for runtime mainline; heuristics are now tags,
  audit notes, or future thin-protocol candidates only.

Boundary:

- No runtime changes were made.
- Existing full-spectrum extraction remains useful as a candidate pool, not as
  direct runtime material.

## 2026-05-01 - P10h Expert Demo Extraction Manual Added

Trigger:

- PM requested an Agent-executable manual for processing one high-player video
  transcript into D-layer candidate cases, including context, steps, eval, and
  domain-bias protection.

Result:

- Added `specs/p10h_expert_demo_extraction_manual.md`.
- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md` to reference
  the manual as the P10h-C execution protocol.

Manual scope:

- Input is one transcript or cleaned source.
- Unit of extraction is a `judgement moment`, not a whole video.
- Output is a candidate-case bundle plus PM fidelity-review packet.
- It includes domain-bias guards against Pokemon/generic RPG contamination.
- It treats `迅捷` as one example of a type-affordance mechanic family, not as
  a universal resource/checklist item.
- It requires A-layer species/move/ability grounding and explicit unresolved
  blockers.

Boundary:

- The manual does not approve runtime changes or gold-case promotion.

## 2026-05-01 - P10h Expert Demo Manual Updated From CC Review

Trigger:

- PM provided an external Agent outline and requested review-driven updates to
  the existing extraction manual.

Absorbed:

- Strengthened the opening domain anchor and fact-source boundary.
- Added common Pokemon/generic-RPG contamination patterns.
- Reworked extraction into a three-pass flow: scan, per-case extraction, then
  format/validate.
- Added `source_stated`, `source_implied`, `agent_inferred_from_source`, and
  `a_layer_fact` evidence markers.
- Added `case_comparison_report.yaml` for duplicate/conflict/complement checks
  against existing cases.
- Added explicit prohibition on auto-ingesting cases into the gold pool.
- Added later-stage drift/eval checks once the gold pool reaches at least 20
  cases.

Rejected:

- Did not make Battle Dex the only source for every tactical term. It remains
  authoritative for structured facts, while tactical terminology may come from
  B-layer docs or source spans.
- Did not require multi-agent E/V/C/Q separation for a single transcript. The
  manual keeps those concerns as phases inside one executable workflow.

## 2026-05-01 - P10h Case Pool Scale And Quality Targets Updated

Trigger:

- PM asked to reconsider the D-layer case pool size under the assumption that
  current frontier models can generalize from a smaller set of high-quality
  demonstrations.

Decision:

- Treat D-layer cases as reasoning-pattern demonstrations, not an answer
  database.
- Do not optimize for equal subtype coverage in the first wave.
- Prioritize broad coverage of reusable judgement patterns.

Updated scale targets:

- Probe: 8-12 PM-reviewed gold cases.
- MVP: 15-25 PM-reviewed gold cases.
- V1 usable: 30-50 PM-reviewed gold cases.
- Continuous: 50+ only for patch/meta/species coverage, not mechanical growth.

Updated quality priority:

1. source fidelity;
2. factual grounding;
3. reasoning completeness;
4. transferability;
5. boundary quality.

Boundary:

- Reasoning completeness is the main ranking signal only after source fidelity
  and A-layer factual grounding pass.
- Complete but invented reasoning must be rejected.

Changes:

- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md`.
- Updated `specs/p10h_expert_demo_extraction_manual.md`.
- Updated `specs/p10h_casebank_seed_schema.yaml` with evidence trace types and
  quality-score dimensions.

## 2026-04-30 - P10h Four Community Sources Cleaned And Seed-Extracted

Trigger:

- PM provided four community source folders and asked to clean the drafts first,
  then attempt tactical information extraction.

Result:

- Added cleaned source notes under
  `artifacts/p10h_case_extraction/cleaned_sources/`.
- Added structured draft extraction in
  `artifacts/p10h_case_extraction/extracted/p10h_seed_case_candidates.yaml`.
- Added extraction summary in
  `artifacts/p10h_case_extraction/extraction_summary.md`.
- Extended `specs/p10h_casebank_seed_schema.yaml` with
  `unreviewed_community_transcript` so raw transcript cases do not masquerade
  as reviewed community notes.

Extracted draft material:

- Team cases: 雷暴翼王偏速攻平衡队, 平衡翼王/无敌平衡队 2.0,
  毒队/平衡毒结构候选, 翼王毒队结构候选.
- Matchup cases: 毒队针对星陨队, 翼王毒击杀线/应对惩罚.
- Species-set example: 翼王毒队中的 Wing King kill-line set.
- Candidate heuristics: team-as-conversion-system, matchup branch reasoning,
  threshold-condition downgrade, energy-state option-space checks.

Correction:

- The first extraction pass classified `毒队针对星陨0430` and `翼王毒0429`
  only as matchup-heavy material.
- PM clarified these should still be preserved as team sources.
- Added separate team/archetype cases for poison/balance-poison and Wing King
  poison without deleting the original matchup cases.

Boundary:

- These are unreviewed extraction artifacts, not accepted B-layer pages and not
  runtime Coach Policy.
- ASR-uncertain species/move names remain unresolved until Battle Dex matching.
- Exact damage/speed/kill-line claims require A-layer or calculator validation
  before policy use.

## 2026-05-01 - P10h Cache Source Multi-Label Inventory Round 1

Trigger:

- PM asked whether all previously cleaned/cache B materials can be used as
  cases and methodology-distillation raw material, with the clarification that
  each source may have multiple labels.

Result:

- Added
  `artifacts/p10h_cache_inventory/cache_source_inventory_2026-05-01.yaml`.
- Added
  `artifacts/p10h_cache_inventory/cache_source_inventory_2026-05-01.md`.
- Inventoried 23 `wiki/cache/` source groups with multi-label source profiles,
  extraction targets, existing handling refs, priority, and risk notes.

Key decision:

- Treat `wiki/cache/` as a source pool, not runtime knowledge.
- A single source can yield multiple artifacts: team case, matchup case,
  species-set example, candidate heuristic, counterexample, eval prompt,
  glossary note, or A-layer validation task.
- All extraction starts as unreviewed/low-confidence until promoted.

Recommended next batch:

- `p10h_batch_02_high_value_team_cases`:
  `光合武队0414`, `主流阵容0326`, and `联防先读0327`.
- Reason: these sources best support Coach Policy methodology by explaining
  conversion paths, battle branches, and team decision logic.

Boundary:

- No runtime prompt, compiled Battle Wiki export, or reviewed wiki page was
  changed by this inventory.

## 2026-05-01 - P10h Full-Spectrum Draft Extraction Plan Added

Trigger:

- PM preferred a broader extraction pass before Coach Policy distillation, to
  reduce viewpoint limitation from only using a few hand-picked high-value
  sources.

Plan:

- Added `specs/p10h_full_spectrum_draft_extraction_plan.md`.
- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md` with P10h-B
  full-spectrum extraction direction.
- Updated
  `artifacts/p10h_cache_inventory/cache_source_inventory_2026-05-01.md` so
  Batch 02/03/04 are prioritization lanes inside the full pass, not the whole
  strategy.

Execution model:

- Extract all 23 `wiki/cache/` source groups into draft/low-confidence pools.
- Then cluster by tactical theme, mark conflicts/volatility, and select
  promotion candidates.
- Coach Policy distillation happens only after review/promotion, not directly
  from raw extraction volume.

Boundary:

- No extraction execution started in this step.
- No runtime prompt, Coach Policy slice, compiled Battle Wiki export, or
  reviewed wiki page was changed.

## 2026-05-01 - P10h Full-Spectrum Draft Extraction V1 Completed

Trigger:

- PM asked whether the full extraction plan was executable and requested
  execution if feasible.

Result:

- Added `artifacts/p10h_full_spectrum_extraction/`.
- Covered all 23 `wiki/cache/` source groups.
- Produced source status, cleaned/source-note refs, draft case pool, draft
  species/set pool, mechanic note pool, candidate heuristics, counterexamples,
  eval prompts, A-layer validation tasks, cluster map, conflict/volatility map,
  promotion candidates, and coverage report.

Draft pool counts:

- Team cases: 16.
- Matchup cases: 4.
- Species-set examples: 7.
- Role-prior signals: 3.
- Mechanic notes: 8.
- Candidate heuristics: 10.
- Counterexamples: 7.
- Eval prompts: 8.
- A-layer validation task groups: 6.
- Tactical clusters: 8.
- Promotion candidates: 5.

Recommended review-first candidates:

- `pc_team_conversion_system`.
- `pc_threshold_claims_require_inputs`.
- `pc_matchup_branch_points`.
- `pc_rating_sources_hypothesis_only`.
- `pc_marks_as_stored_threat`.

Boundary:

- Everything remains `draft / low_confidence`.
- No runtime prompt, Coach Policy slice, compiled Battle Wiki export, or
  reviewed wiki page was changed.
- Exact claims remain blocked on A-layer validation.

## 2026-05-01 - P10h Blind Pass2 Recovered And Compared

Trigger:

- PM dispatched a subagent for independent blind full-spectrum extraction pass2
  and then requested result recovery and comparison.

Recovery:

- Direct `wait_agent` recovery returned `not_found`, but pass2 files were
  present under `artifacts/p10h_full_spectrum_extraction_pass2/`.
- YAML validation passed for all pass2 YAML files.

Pass2 summary:

- Covered all 23 source groups.
- Extracted 11 team cases, 8 matchup cases, 18 species-set examples, 17
  mechanic notes, 19 candidate heuristics, 10 counterexamples, 12 eval prompts,
  30 A-layer validation tasks, 10 clusters, and 8 promotion candidates.

Comparison result:

- Added
  `artifacts/p10h_full_spectrum_extraction_comparison/comparison_report.md`.
- Added
  `artifacts/p10h_full_spectrum_extraction_comparison/findings.yaml`.
- Added
  `artifacts/p10h_full_spectrum_extraction_comparison/merge_plan.md`.

Decision:

- Use V1 as canonical base because it is more conservative and policy-oriented.
- Merge selected pass2 deltas because pass2 is stronger on matchup branches,
  species/set signals, mechanic guardrail granularity, and executable A-layer
  validation tasks.
- Do not wholesale replace V1 with pass2.

Boundary:

- No merged v2 artifact was created yet.
- No runtime prompt, Coach Policy slice, compiled Battle Wiki export, or
  reviewed wiki page was changed.

## 2026-05-01 - P10h Full-Spectrum Extraction Merged V2 Completed

Trigger:

- PM requested completion of the v1/pass2 merge after comparison.

Result:

- Added `artifacts/p10h_full_spectrum_extraction_merged_v2/`.
- Used v1 as the canonical base.
- Merged selected pass2 deltas for matchup branch detail, species/set role
  signals, mechanic guardrail granularity, validation tasks, counterexamples,
  eval prompts, clusters, and promotion candidates.

Merged v2 counts:

- Team cases: 17.
- Matchup cases: 9.
- Species-set examples: 17.
- Role-prior signals: 3.
- Mechanic notes: 16.
- Glossary notes: 3.
- Candidate heuristics: 18.
- Counterexamples: 17.
- Eval prompts: 19.
- A-layer validation tasks: 36.
- Clusters: 18.
- Promotion candidates: 8.

Review queue:

- `pc_team_conversion_system`.
- `pc_threshold_and_exact_fact_validation_gate`.
- `pc_matchup_branch_points`.
- `pc_rating_volatility_guardrail`.
- `pc_mark_team_diagnostic`.
- `pc_weather_window_diagnostic`.
- `pc_photosynthesis_martial_deep_dive`.
- `pc_poison_vs_starfall_holdout_eval`.

Validation:

- YAML validation passed for all merged v2 YAML files.
- Search found no runtime references to merged v2 outside planning/comparison
  artifacts.

Boundary:

- Everything remains `draft / low_confidence`.
- No runtime prompt, Coach Policy slice, compiled Battle Wiki export, or
  reviewed wiki page was changed.

## 2026-04-30 - P10h Persona Identity Prompt Boundary Completed

Trigger:

- PM observed native Agent replies such as `欢迎来到洛克王国世界！我是Roco，你的精灵对战顾问`,
  which exposes app/job framing instead of following the selected persona layer.

Finding:

- The exact Chinese welcome phrase was not hardcoded in repo.
- The native P7 prompt did define the model as `the Roco conversational advisor`,
  which can cause the model to convert internal task role into public
  self-identity.
- `You know who` is currently a built-in public-safe persona profile
  (`you_know_who`) plus selector/safety boundaries. It is insertable as a
  built-in persona, but not yet a full materialized Nuwa/persona artifact set
  with rich Enzo-derived expression rendering.

Change:

- Updated `advisor/runtime.py` so native Agent system prompt answers through the
  selected public persona and forbids self-introduction, app naming, or job-title
  claims unless the user explicitly asks.
- Added a route-level guard that persona identity is supplied by the persona
  layer and battle-advice role is task context, not self-identity.
- Added a regression test preventing restoration of the old `Roco conversational
  advisor` self-identity prompt.

Boundary:

- The role can still guide internal task behavior.
- Public self-identity should come from persona output policy, not backend route
  or app naming.

## 2026-04-30 - P10i Managed Persona Artifact Materialization Entry Completed

Trigger:

- PM clarified the required persona-layer insertion chain:
  user description / Nuwa output can wait, but reviewed distillation artifacts
  must be convertible into runtime artifacts that the system can consume.

Finding:

- Existing P1/P2 infrastructure already covered artifact ingestion, registry
  admission, activation projection, profile materialization, resolver loading,
  API env/config injection, and `/chat` / `/team/analyze` selector consumption.
- The missing operational piece was a standard executable entry point for
  turning a reviewed distillation bundle into `materialized_profiles.yaml`,
  selector output, and a local runtime env snippet.

Changes:

- Added `scripts/materialize_persona_artifacts.py`.
- The script consumes a reviewed bundle containing:
  `distillation_or_design_memo.md`,
  `normalized_persona_doctrine_draft.yaml`,
  `mapping_or_usage_note.md`, and `provenance_metadata.yaml`.
- It writes ingestion, registry, activation, projection, materialization,
  selector, env snippet, and summary artifacts.
- Updated `README.md` with the supported boundary and command usage.
- Added `tests/test_persona_materialization_script.py` covering public-safe
  successful materialization and blocked public-scope preservation without
  approval.

Boundary:

- This does not implement the user-description to Nuwa distillation UI/process.
- Public-safe approval remains explicit; no artifact becomes public runtime
  selectable by accident.

Validation:

- `.venv/bin/python -m unittest tests.test_persona_materialization_script tests.test_persona_profile_materialization tests.test_persona_profile_resolver tests.test_api`
  passed with `Ran 67 tests`, `OK`.

## 2026-04-30 - P10j Self-Managed Persona Scope And Flavor Rules Completed

Trigger:

- PM asked whether open-source users should be blocked by the default
  public-safe managed persona scope, and whether the future `You know who`
  persona can include expression-only menu rules such as mild hostility toward
  grass-type species.

Decision:

- Keep `public_safe_release` as the explicit public-distribution validation
  gate.
- Use `internal_only_runtime` as the local/self-managed default so open-source
  users can load private artifacts locally without implying public Roco release
  approval.
- Add structured rendering flavor rules as expression-only persona menu entries.
  They may change wording but must not change facts, scores, recommendations,
  warnings, refusals, tool results, or team-building decisions.

Changes:

- Added `ROCO_MANAGED_PERSONA_SCOPE`, defaulting to `internal_only_runtime`.
- API/service resolver construction still supports explicit
  `public_safe_release` scope for release/distribution validation.
- Added `PersonaRenderingFlavorRule` and preserved it through doctrine schema,
  materialization, resolver round-trip, and persona envelopes.
- Added built-in `you_know_who` `grass_type_hostility` rendering flavor rule.
- Updated `scripts/materialize_persona_artifacts.py` so generated
  `runtime_env_snippet.env` includes both materialization path and matching
  scope.
- Generated an internal-only Enzo scope probe at
  `artifacts/persona_runtime/enzo_internal_nuwa_draft_scope_probe/runtime/`.

Validation:

- `.venv/bin/python -m unittest tests.test_persona_materialization_script tests.test_persona_profile_resolver tests.test_persona_profile_materialization tests.test_api tests.test_public_hardening tests.test_agent_core_contracts`
  passed with `Ran 88 tests`, `OK`.

## 2026-04-30 - P10k Managed Persona Runtime Scope Default Reversed

Trigger:

- PM clarified that open-source/default runtime should not behave like a
  public-release review gate. User/self-managed persona behavior should be
  unrestricted by default, while `public_safe_release` should remain available
  for public distribution validation.

Decision:

- Preserve both scopes.
- Default runtime/materialization scope is now `internal_only_runtime`.
- `public_safe_release` remains an explicit gate for public defaults,
  screenshots, official distribution, and future sharing/marketplace flows.
- Internal runtime scope can consume both internal-only and public-safe
  materialized profiles. Public-safe scope blocks internal-only profiles.

Changes:

- Updated API env default, service resolver default, resolver/config defaults,
  materialization script default, `.env.example`, README, and tests.
- Updated resolver compatibility so `internal_only_runtime` is a superset for
  local/self-managed execution, while `public_safe_release` remains strict.

Validation:

- `.venv/bin/python -m unittest tests.test_persona_materialization_script tests.test_api tests.test_public_hardening tests.test_persona_profile_resolver tests.test_persona_profile_materialization`
  passed with `Ran 76 tests`, `OK`.

## 2026-04-30 - P10l Minimal Managed You Know Who Artifact Completed

Trigger:

- PM requested minimum desensitization/optimization so `You know who` can be
  inserted as a managed persona artifact, then explained as a working file chain.

Changes:

- Added `docs/personas/you_know_who_minimal/` with standard reviewed-bundle
  files:
  - `distillation_or_design_memo.md`
  - `normalized_persona_doctrine_draft.yaml`
  - `mapping_or_usage_note.md`
  - `provenance_metadata.yaml`
- The doctrine uses `persona_id=you_know_who`, display name `You know who`,
  public-safe IP profile, fact-locked policy, and the
  `grass_type_hostility` rendering-only flavor rule.
- Generated managed runtime artifacts in
  `artifacts/persona_runtime/you_know_who_minimal/`.
- Generated selector: `you_know_who@draft.v1#1`.
- Confirmed API consumption through managed `persona_selector`.
- Added regression coverage that the checked-in minimal bundle materializes and
  resolves with the expected selector, display name, public-safe flag, and
  flavor rule.

Boundary:

- This is minimum viable desensitization, not final brand/persona writing.
- Internal Enzo references remain in source provenance and forbidden-marker
  safety metadata; they are not the public persona id/display name.

Validation:

- `.venv/bin/python -m unittest tests.test_persona_materialization_script tests.test_persona_profile_resolver tests.test_api tests.test_public_hardening`
  passed with `Ran 67 tests`, `OK`.

## 2026-04-30 - P10n Managed You Know Who Default Path Connected

Trigger:

- PM asked to execute the actual default-path insertion after the managed
  `you_know_who@draft.v1#1` artifact was generated and validated.

Changes:

- Updated `scripts/run_local_api.sh` so local API startup automatically points
  to `artifacts/persona_runtime/you_know_who_minimal/materialized_profiles.yaml`
  when no explicit `ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH` is configured.
- Kept `ROCO_MANAGED_PERSONA_SCOPE` defaulted to `internal_only_runtime`.
- Updated mobile default persona selector so `You know who` sends:
  `{ kind: "managed", persona_id: "you_know_who", version: "draft.v1", revision: 1 }`.
- Updated mobile README/file guide to document the managed default and built-in
  fallback boundary.
- Added API regression coverage that the checked-in managed `You know who`
  runtime artifact is consumed with `sanitized=false`, `public_safe=true`, and
  `grass_type_hostility`.

Boundary:

- Built-in `you_know_who` remains a backend fallback if the local
  materialization path is missing or invalid.
- UI still exposes only the public label `You know who`; it must not surface
  materialization paths or internal provenance.

Validation:

- `cd mobile && npm run typecheck` passed.
- `.venv/bin/python -m unittest tests.test_api tests.test_persona_materialization_script tests.test_public_hardening`
  passed with `Ran 55 tests`, `OK`.

## 2026-04-30 - P10m Enhanced Sanitized You Know Who Completed

Trigger:

- PM asked whether the sanitized persona can retain a small shadow of the
  internal draft's story structure without retaining recognizable IP
  fingerprints.

Changes:

- Enhanced `docs/personas/you_know_who_minimal/normalized_persona_doctrine_draft.yaml`
  with abstract shadow models:
  - `helplessness_debt`
  - `institutions_smooth_over_failure`
  - `forbidden_knowledge_is_not_automatically_false`
  - `delay_creates_hidden_loss`
- Added a refusal-safe heuristic for forbidden paths:
  `examine forbidden paths as high-cost hypotheses, not as romance`.
- Added honesty boundary `taboo_method_or_forbidden_path_appears`.
- Updated mapping/memo docs to state that the persona preserves only structural
  shadows, not concrete story markers.
- Re-materialized `you_know_who@draft.v1#1` in
  `artifacts/persona_runtime/you_know_who_minimal/`.
- Updated regression tests to assert the enhanced shadow models survive
  materialization and resolver loading.

Boundary:

- No public identity uses Enzo/恩佐 or official-character naming.
- Internal source/provenance can still reference original evidence for audit;
  product UI must not surface those references.

Validation:

- `.venv/bin/python -m unittest tests.test_persona_materialization_script tests.test_persona_profile_resolver tests.test_api tests.test_public_hardening`
  passed with `Ran 67 tests`, `OK`.

## 2026-04-30 - P10c Release Smoke QA Draft Completed

Dispatch result:

- PM dispatch accepted P10b.
- Added `.launchpad/accepted_truth/p10b_chat_contract_integration_audit_completed.yaml`.
- Added `specs/p10c_release_smoke_qa.yaml`.
- Added `.launchpad/slices/p10c_release_smoke_qa.yaml`.
- Added `artifacts/p10c_release_smoke_qa/release_smoke_summary.md`.
- Updated active LaunchPad surface to P10c PM Acceptance Check.

Automated smoke:

- Backend full unittest discovery passed:
  - `.venv/bin/python -m unittest discover -s tests`
  - `Ran 218 tests in 5.608s`
  - `OK`
- Mobile typecheck passed:
  - `cd mobile && npm run typecheck`
- Static scan found no visible `队伍上下文` chip string under `mobile/src` or
  `mobile/README.md`.
- Static scan confirmed Chat request body types do not include provider key,
  provider base URL, or model fields.

Warnings observed:

- PydanticAI emitted a deprecation warning: `OpenAIModel` renamed to
  `OpenAIChatModel`.
- Python tests emitted a ResourceWarning for an unclosed asyncio event loop.

Not executed:

- iOS simulator interaction smoke was not run because no booted simulator was
  detected.
- Android simulator/device QA was not run.
- Paid live provider smoke was not run because P10 requires explicit PM
  approval before token-consuming checks.

Carry-forward:

- P10d should run simulator/manual smoke if PM wants release interaction proof.
- Paid custom-single-model / DeepSeek quick-setup live smoke should only run
  after explicit PM approval.

## 2026-04-30 - P10d Simulator And Live Provider Smoke Draft Completed

Dispatch result:

- PM dispatched P10d and explicitly approved live provider smoke.
- Added `.launchpad/accepted_truth/p10c_release_smoke_qa_completed.yaml`.
- Added `specs/p10d_simulator_and_optional_live_smoke.yaml`.
- Added `.launchpad/slices/p10d_simulator_and_optional_live_smoke.yaml`.
- Added `artifacts/p10d_simulator_and_live_smoke/live_smoke_summary.md`.
- Added `artifacts/p10d_simulator_and_live_smoke/live_smoke_summary.json`.
- Added `artifacts/p10d_simulator_and_live_smoke/simulator_smoke_summary.md`.
- Captured simulator screenshots under `artifacts/p10d_simulator_and_live_smoke/`.

Simulator smoke:

- Booted iPhone 17 iOS 26.4 simulator.
- Expo app launched and rendered the V1 chat shell.
- Composer accepted pasted input and sent a message.
- Before local backend startup, the app displayed a controlled connection/model
  error.
- After local backend startup, retry reached the backend and rendered a
  controlled native runtime failure because the simulator did not have provider
  settings configured.

Live provider smoke:

- `custom_single_model_model_diagnostic` passed with configured
  `deepseek-v4-pro` in `2.499s`.
- `deepseek_quick_setup_realistic_agent_chat` passed with
  `deepseek-v4-flash` in `3.786s`, returning ok `chat_response` through
  `pydantic_ai_native`.
- Secret redaction passed; provider key was not written to artifacts.
- A meta smoke-test prompt was refused/unsupported and is preserved as evidence
  that meta diagnostics are not a normal product path.

Release interpretation:

- P10d is `passed_with_notes`, not full release-ready.
- Remaining blockers are Android QA, simulator-side provider Settings success,
  production screenshot/build evidence, slow-call progress UX, and true
  `roco_deepseek_v4_reference` backend call-role routing.
- Confirmed `mobile/assets/paper/paper_shell.png` exists, so the README paper
  asset path is not currently drifted.

## 2026-04-30 - P10e Runtime Config UX Repair Started

Trigger:

- PM observed that simulator still only said `模型使用失败`, making it look as
  if real Agent chat was not implemented.

Clarification:

- P10d live provider smoke proved backend Agent chat can call DeepSeek through
  request-scoped runtime config.
- P10d did not prove simulator-side live success because the simulator did not
  have complete provider settings.
- The issue is therefore not "Agent chat absent"; it is an unsafe UX ambiguity
  between missing device config and missing backend capability.

Changes:

- Added `specs/p10e_runtime_config_ux_repair_and_simulator_live_smoke.yaml`.
- Added `.launchpad/accepted_truth/p10d_simulator_and_optional_live_smoke_completed.yaml`
  without hiding P10d residual risks.
- Added `.launchpad/slices/p10e_runtime_config_ux_repair_and_simulator_live_smoke.yaml`.
- Updated `.launchpad/runtime_state.yaml` and `.launchpad/active_surface.md`.
- Updated `mobile/src/roco/rocoPresentation.ts` so runtime failures render
  setup/test-model instructions and do not produce normal analysis cards.
- Updated `mobile/src/components/roco/SettingsDrawer.tsx` so model diagnostic
  output includes backend diagnostic code/message.

Verification:

- `cd mobile && npm run typecheck` passed.

Pending:

- Start local backend and iOS Expo app.
- Configure simulator provider settings without leaking secrets.
- Run simulator-side model diagnostic and live Agent chat smoke.

## 2026-04-30 - P10e Simulator Live Smoke Completed

Execution:

- PM approved writing the local env DeepSeek provider key into simulator
  SecureStore and executing token-consuming model/chat smoke.
- The key was copied through local clipboard and pasted into the simulator
  secure field; it was not printed to terminal output.
- iOS prompted to save the API key in password autofill; selected `以后` and did
  not save it to system password autofill.

Results:

- Before replacing the stale simulator key, Settings model diagnostic returned
  `Model: failed · invalid_or_unauthorized_provider_key`.
- After replacing the key, Settings model diagnostic returned `Model: ok · ok`.
- Simulator chat sent a normal user prompt and returned a non-runtime-failure
  assistant response.
- Backend logs showed `POST /runtime/model-diagnostic HTTP/1.1` `200 OK` and
  `POST /chat HTTP/1.1` `200 OK`.

Artifacts:

- `artifacts/p10e_runtime_config_ux_repair/ios_model_diagnostic_ok.png`
- `artifacts/p10e_runtime_config_ux_repair/ios_chat_live_success.png`
- `artifacts/p10e_runtime_config_ux_repair/simulator_live_smoke_summary.md`

Interpretation:

- Agent chat is implemented and the simulator-side live success path is now
  proven for local-dev prototype.
- The earlier simulator failure was caused by stale/invalid device provider
  configuration, not missing Agent chat implementation.
- Remaining release blockers are Android QA, production screenshot/build
  evidence, slow-call progress UX, and true DeepSeek reference call-role
  routing.

## 2026-04-30 - P10f Chat Reply Simplification Completed

Trigger:

- PM observed that the simulator reply was not human-readable and that analysis
  card information should likely be removed for now.

Changes:

- Added `specs/p10f_chat_reply_simplification.yaml`.
- Updated `mobile/src/roco/rocoPresentation.ts` so V1 chat bubbles use a
  compacted user-facing reply instead of exposing internal prefixes, doctrine
  tails, and partial-team boundary phrasing verbatim.
- `buildAnalysisCardModel` now intentionally returns `null` for V1.
- Updated `mobile/src/screens/ChatScreen.tsx` so new messages no longer attach
  `analysis_card`.
- Updated `mobile/src/components/roco/MessageBubble.tsx` so agent bubbles no
  longer import or render `AnalysisCard`.

Boundary:

- Backend presentation/detail-section contracts remain in place for future use.
- The card component source remains available but is no longer reachable from
  the active V1 chat surface.
- This is a product-surface fix, not the final persona writing-style pass.

Validation:

- `cd mobile && npm run typecheck` passed.

## 2026-04-30 - P10g User-Facing Answer Boundary Completed

Trigger:

- PM clarified the product boundary: users should consume only analysis process
  and result, without software permission/runtime metadata.

Decision:

- Main V1 chat replies may say what Roco considered, how it reasoned, and what
  the result is.
- Main V1 chat replies must not expose backend/runtime/route/provider labels,
  evidence ids, raw source labels, confidence tiers, tool traces,
  product-boundary wording, doctrine/grounding jargon, or analysis-card
  detail-section content.

Changes:

- Added `specs/p10g_user_facing_answer_boundary.yaml`.
- Updated `agent_core/synthesis.py` so visible judgements, `why_summary`, and
  warning messages use product-language Chinese instead of software-policy
  language.
- Updated `agent_core/presentation.py` to remove the `答复：` wrapper and use
  user-facing `注意：` warning wording.
- Updated `agent_core/persona.py` so the default public persona returns the
  answer directly; the alternate support persona keeps only light style
  variation without evidence/confidence/followup sections.
- Updated `mobile/src/roco/rocoPresentation.ts` with a final software-metadata
  scrubber for stale/legacy replies.
- Updated tests that were previously protecting old internal wording.

Validation:

- `cd mobile && npm run typecheck` passed.
- `.venv/bin/python -m unittest tests.test_agent_core_contracts tests.test_agent_core_orchestrator tests.test_api`
  passed with `Ran 66 tests`, `OK`.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 218 tests`,
  `OK`.

Residual:

- Final persona writing style still needs a dedicated design pass.
- Analysis cards remain disabled until a public UI artifact contract exists.

## 2026-04-30 - P10h Tactical Coach Policy Distillation Plan Drafted

Trigger:

- PM reframed the missing analysis layer as a bidirectional optimization loop
  between a richer, human-labeled B-layer and a Coach Policy distilled from that
  B-layer.

Decision:

- Do not hand-write a full battle-coach policy from intuition.
- Do not ask an LLM to invent tactical methodology from vague prompts.
- Treat `what is known` (B-layer facts, docs, cases, labels), `how to judge`
  (Coach Policy), and `how to speak` (persona layer) as separate assets.

Plan:

- Added `specs/p10h_tactical_coach_policy_distillation_plan.md`.
- The plan defines B-layer asset requirements, casebank seed requirements,
  distillation workflow, human-review gate, compiled route-specific policy
  slices, blind eval, and eventual runtime integration.
- Existing `specs/tactical_casebank_spec.md`,
  `specs/battle_wiki_architecture_spec.md`, and
  `docs/battle_analysis_architecture.md` are treated as inputs, not replaced.

Boundary:

- P10h is a plan only. No Coach Policy runtime injection is approved yet.
- Runtime prompt changes from P10g/P10 follow-up remain separate from P10h.

## 2026-04-30 - P10h-A B-Layer Inventory And Schema Drafts Completed

Trigger:

- PM accepted trying P10h-A and asked whether the B-layer asset base still needs
  additional content before Coach Policy distillation.

Result:

- Added `artifacts/p10h_b_layer_inventory/asset_inventory.md`.
- Added `artifacts/p10h_b_layer_inventory/blockers.yaml`.
- Added `specs/p10h_casebank_seed_schema.yaml`.
- Added `specs/p10h_coach_policy_heuristic_schema.yaml`.
- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md` with P10h-A
  output references.

Key conclusion:

- Roco already has enough B-layer material to start a seed distillation workflow:
  SQLite facts, reviewed Battle Wiki mechanics/methodology pages, a small
  reviewed casebank, and raw/cache community source packs.
- The blocker is not lack of raw information. The blocker is lack of normalized
  labels and evidence mapping: case labels, human review metadata,
  candidate-heuristic records, derived feature tags, and held-out eval split.

Boundary:

- No runtime Coach Policy injection was made.
- Runtime remains blocked until normalized case labels and heuristic evidence
  maps are accepted.

## 2026-04-30 - P10b Chat Contract Integration Audit Draft Completed

Dispatch result:

- PM dispatch accepted P10a.
- Added `.launchpad/accepted_truth/p10a_mobile_settings_policy_alignment_completed.yaml`.
- Added `specs/p10b_chat_contract_integration_audit.yaml`.
- Added `.launchpad/slices/p10b_chat_contract_integration_audit.yaml`.
- Updated active LaunchPad surface to P10b PM Acceptance Check.

P10b findings and fixes:

- Default persona selector is now explicit in ChatScreen:
  `activePersonaSelector ?? DEFAULT_PERSONA_SELECTOR`.
- Team context remains attached through `context_attachments` and no visible
  main Chat team-context chip was found.
- Provider runtime config remains header-only; provider key is not inserted into
  Chat request body or URL.
- `resolveVisibleReply` no longer trusts `persona.rendered_answer` unless the
  persona envelope is both `public_safe` and `sanitized`.
- Mobile DeepSeek Settings wording was downgraded from reference-profile
  language to `deepseek_v4_quick_setup` because backend call-role reference
  routing does not exist yet.

Boundary:

- P9e still defines `roco_deepseek_v4_reference` as the maintained target
  profile.
- Mobile must not claim that full reference profile is active until backend
  routing exists.

Verification:

- `cd mobile && npm run typecheck` passed.

## 2026-05-01 - Current Redteam Entry Pointer

- For the current P10h strategy state, start from
  `2026-05-01 - P10h Pivot Rollup For Redteam`.
- The rollup records the accepted transition from heuristic-first Coach Policy
  distillation to D-layer Expert Demonstration Case Memory, including scale,
  quality priorities, boundaries, current artifacts, and next execution.
- Earlier P10h entries below/above it remain historical context and should not
  be treated as the current execution plan if they conflict with the rollup.

## 2026-05-01 - P10h Retrieval And Tag Quality Plan Tightened

Trigger:

- PM accepted the D-layer Expert Demonstration Casebank direction but flagged
  the real retrieval risk: BM25 plus tags fails if tags are sparse,
  inconsistent, or over-filtered.

Decision:

- Keep probe-scale retrieval simple: tag filtering plus BM25/simple lexical
  scoring.
- Treat tag quality as the first retrieval gate, before algorithm comparison.
- Do not move to embeddings or LLM reranking until tag/canonical-entity defects
  have been fixed or ruled out.

Changes:

- Updated `specs/p10h_tactical_coach_policy_distillation_plan.md` with
  canonical `data/expert_demonstrations/` storage, tag discipline, concrete
  P10h-C/P10h-D sequencing, and the 5-question obvious-match recall gate.
- Added `specs/p10h_d_layer_retrieval_contract.yaml`.
- Updated `specs/p10h_expert_demo_extraction_manual.md` so extraction agents
  must produce retrieval-useful tags and `tag_quality_notes`.
- Updated `specs/p10h_casebank_seed_schema.yaml` with tag-quality notes and
  validation rules.

Acceptance impact:

- Probe D-layer retrieval now begins with 5 PM-authored user-like questions that
  have known expected matching cases.
- Pass condition: expected case appears in top-3 for at least 4 of 5 questions.
- Broader per-case recall smoke only runs after this tag-quality gate.

Boundary:

- No runtime code changed.
- No gold case auto-ingest approved.

## 2026-05-01 - P10h Cross-Document Schema Alignment

Trigger:

- Redteam review accepted the spec package but found two cross-document
  alignment defects:
  - `retrieval_tags` did not expose the same resource/risk groups required by
    the retrieval contract.
  - Plan/manual examples used `dc_` demonstration-case ids while schema still
    required the pre-pivot `tc_` prefix.

Changes:

- Updated `specs/p10h_casebank_seed_schema.yaml` so new D-layer case ids use
  `^dc_[a-z0-9_]+$`.
- Added `resource_or_mechanic` and `risk_or_boundary` retrieval tag groups to
  schema.
- Kept `bottleneck_tags` as a backward-compatible alias instead of deleting it.
- Updated plan/manual wording to use `resource_or_mechanic` and
  `risk_or_boundary`.

Boundary:

- This is a spec alignment fix only.
- No existing candidate pool was rewritten.
- No runtime code changed.

## 2026-05-01 - P10h-C First-Wave Extraction Acceptance Review

Trigger:

- P10h-C execution thread returned first-wave Expert Demonstration extraction
  artifacts for acceptance.

Result:

- Accepted P10h-C as a draft artifact generation stage with notes.
- Reviewed artifacts under:
  - `artifacts/p10h_expert_demo/`
  - `artifacts/p10h_expert_demo_extraction/first_wave_2026_05_01/`
- Added acceptance review artifact:
  `artifacts/p10h_expert_demo/p10h_c_acceptance_review.md`.

Validation:

- YAML parse passed for all reviewed YAML artifacts.
- `candidate_cases.yaml` contains 20 candidates.
- All candidates use `dc_` ids.
- All candidates include required review/extraction fields.
- All candidates include contract-aligned `resource_or_mechanic` and
  `risk_or_boundary` retrieval tag groups.
- All source spans resolve to existing cleaned source files and valid line
  ranges.
- `runtime_allowed: false` and `gold_ingest_allowed: false` are preserved.
- No files were written under `data/expert_demonstrations`.
- No Pokemon/EV/tera/item contamination was found in generated artifacts.

Notes:

- `extraction_summary.md` lists `cache_balance_wingking_0429: 6 candidates`,
  while `candidate_cases.yaml` has 5 cases for that source. Total count is
  still 20, so this is a summary typo, not a candidate-data defect.
- The 10 recommended probe-gold candidates are PM-facing in
  `pm_review_packet.md`, not machine-readable flags in candidate YAML.

Next:

- PM fidelity review of the 10 recommended candidates.
- Resolve or explicitly defer gold-blocking names/mechanics.
- Only after 8-12 PM-reviewed gold cases exist, start P10h-D retrieval index
  construction and 5-question obvious-match recall smoke.

## 2026-05-01 - P10h PM Review Overlay Recorded

Trigger:

- PM reviewed the first-wave P10h-C recommended candidates and supplied
  source-fidelity/context corrections, name decisions, and mechanic notes.

Artifacts:

- Added `artifacts/p10h_expert_demo/p10h_pm_review_overlay_2026_05_01.yaml`.
- Added `artifacts/p10h_expert_demo/p10h_pm_review_decision_brief_2026_05_01.md`.

Recorded case corrections:

- 狐仙降速 case is valid but must be explained through bulky 狐仙 taking the
  hit, then using 高温回火 to rotate out after the opponent acts.
- 雷暴翼王贝古斯 single-backbone case is valid but overphrased; 贝古斯 is a
  critical support/compression piece, while the team remains offense-first.
- 斩杀线 case should generalize to all build-dependent kill-line claims, while
  preserving high-rank percentage heuristics as source-side evidence.
- 翼王毒 vs 贝古斯 4-energy branch must include 倾泻 mark-clear pressure,
  火焰护盾/倾泻 energy fork, and 圣羽翼王 迅捷水刃 acting before 贝古斯.
- 闪电鳗鱼 lead case should include scouting unknown leads and countering
  common openers, not only thunderburst setup.

Recorded name decisions:

- `Wing King` / `翼王` / `仙翼王` -> `圣羽翼王`.
- `闪击翼王` is a build/archetype label, not a separate species.
- `迅捷水刃` means `水刃` gaining 迅捷 through 圣羽翼王's ability.
- `星兔` -> `落陨星兔`.
- `Pal` / `帕尔` -> `龙息帕尔`.
- `古龙` -> `寂灭骨龙`.
- `群法` / `球法` -> `裘卡`; context recorded in
  `artifacts/p10h_expert_demo/group_fa_context_2026_05_01.md`.
- `圣剑` -> `圣剑-X`.
- `独角兽` -> leader-form `彩虹独角兽`.
- `寒音蛇` -> 萌+毒 `寒音蛇`.
- `棋齐垒` is valid; form only matters if the case needs it.

Mechanic/tag boundary:

- `rotation_damage_transfer` accepted with PM clarification through
  高温回火 rotation timing.
- `morale_magic`, `warning_effect`, `backend_detonation`,
  `magnetism_transfer`, and `wish_force_line` remain source-local/recheck tags
  until exact source/B-layer wording is established.

Additional extraction risk:

- PM upgraded the risk: if the current list is treated as the complete set of
  major judgement chains for poison-vs-Starfall, then P10h-C likely under-
  recalled judgement chains across all first-wave videos. Recall-oriented second
  passes are required before treating any first-wave source as fully extracted.

Boundary:

- No original candidate artifact was destructively rewritten.
- No runtime code changed.
- No gold cases promoted.

## 2026-05-01 - P10h-C1.5 Conservative Transcript Cleaning

Trigger:

- PM requested cleaner transcript substrates for the four first-wave community
  videos before further extraction, because current case extraction likely under-
  recalled judgement chains and several ASR names required correction.

Artifacts:

- Added `artifacts/p10h_transcript_cleaning/scripts/generate_verbatim_cleaned.py`.
- Added `artifacts/p10h_transcript_cleaning/README.md`.
- Added four paragraph-addressable cleaned transcript drafts under
  `artifacts/p10h_transcript_cleaning/verbatim_cleaned/`.
- Added `artifacts/p10h_transcript_cleaning/transcript_cleaning_qa.md`.

Coverage:

- `毒队针对星陨0430`: 14 paragraphs.
- `翼王毒0429`: 10 paragraphs.
- `平衡翼王0429`: 7 paragraphs.
- `雷暴翼王偏速攻的平衡0402`: 34 paragraphs.

Cleaning policy:

- Preserve raw ASR text in `原文`.
- Write conservative `校订` lines with PM-confirmed canonical names and high-
  confidence ASR repairs only.
- Keep uncertainty visible in `校订注记`; do not silently convert source-local
  mechanics into gold facts.
- Mark source-side Pokemon analogy as transcript-only contamination, forbidden
  for generated case reasoning.

Validation:

- Re-generated all four files after fixing chained alias replacement defects
  such as `落落陨星兔`.
- Checked cleaned lines for common chained/legacy ASR residues; no hits.

Boundary:

- These files are transcript substrates only.
- No case extraction, runtime code, or gold demonstration ingestion happened in
  this step.

## 2026-05-01 - P10h-C1.5 Corrected-Only Transcript Copies

Trigger:

- PM requested four documents containing only the corrected transcript text for
  a second manual pass.

Artifacts:

- Added `artifacts/p10h_transcript_cleaning/corrected_only/`.
- Generated one corrected-only Markdown file per first-wave video.

Validation:

- Paragraph counts match the conservative cleaned transcript source files:
  14 / 10 / 7 / 34.

Boundary:

- These are convenience review copies only.
- No source transcript, case extraction, runtime code, or gold demonstration
  artifact was modified.

## 2026-05-01 - P10h-C2 Second-Wave Corrected Text Extraction

Trigger:

- PM requested a new analysis pass over the four corrected transcript texts.
- During the pass, PM clarified that high-player background explanations, such
  as a short explanation of Starfall team's design intent, are valuable learning
  material even when they are not the video's main decision point.

Artifacts:

- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/source_manifest.yaml`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/candidate_cases.yaml`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/expert_context_primitives.yaml`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/name_resolution_notes.yaml`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/coverage_report.md`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/pm_review_packet.md`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/extraction_summary.md`.

Output:

- 28 candidate Expert Demonstration cases.
- 9 expert context primitives.
- Sources processed: 4.

Design adjustment:

- Concrete judgement/construction decisions remain in `candidate_cases.yaml`.
- Background explanations, archetype summaries, mechanic explanations, role
  maps, and hard matchup boundaries are now captured separately as
  `expert_context_primitives.yaml`.
- This avoids discarding high-signal expert framing while preserving a stricter
  boundary for full D-layer decision cases.

Validation:

- YAML parse passed for all generated YAML files.
- Confirmed no files were written under `data/expert_demonstrations`.

Boundary:

- No runtime code changed.
- No gold cases promoted.

## 2026-05-01 - P10h First D-Layer Expert Tactical Memory Pack

Trigger:

- PM asked whether we can execute the new plan now or should first define
  maintenance/writeback. Decision: do a thin maintenance/writeback contract first,
  then generate the first D-layer pack.

Artifacts:

- Added `artifacts/p10h_intuition_demo_pack/d_layer_maintenance_and_writeback_contract.md`.
- Added `artifacts/p10h_intuition_demo_pack/tactical_intuition_primitives.yaml`.
- Added `artifacts/p10h_intuition_demo_pack/expert_tactical_priors.yaml`.
- Added `artifacts/p10h_intuition_demo_pack/long_demonstrations.yaml`.
- Added `artifacts/p10h_intuition_demo_pack/cluster_notes.md`.
- Added `artifacts/p10h_intuition_demo_pack/pm_review_packet.md`.
- Added `artifacts/p10h_intuition_demo_pack/eval_probe_design.md`.

Output:

- D1 attention primitives: 8.
- D2 expert tactical priors: 9.
- D3 long demonstrations: 4.

Validation:

- YAML parse passed for all D-pack YAML files.

Boundary:

- Runtime integration not performed.
- No gold cases promoted.
- Pack remains draft until PM review and ablation/probe testing.

## 2026-05-01 - P10h Intuition + Long Demonstration Plan

Trigger:

- PM challenged the efficiency and few-shot alignment of reviewing many small
  extracted cases one by one.
- PM proposed a sharper D-layer target: high-player tactical intuition
  primitives plus a few long, rigorous, imitable reasoning demonstrations.

Artifact:

- Added `artifacts/p10h_intuition_long_demo_execution_plan_2026_05_01.md`.

Plan shift:

- Stop full review of 28+9 micro-items as the primary path.
- Cluster existing extracted material into:
  - 10-15 tactical intuition primitives;
  - 5-8 long demonstrations;
  - a narrow PM review packet;
  - a retrieval/evaluation probe.

Subagent:

- Spawned an external-context red-team reviewer with no inherited thread
  context. It was given only the plan file path and asked to challenge coherence,
  source fidelity, disguised-rulebook risk, and minimal eval criteria.

Red-team result:

- Strategic shift is coherent only if primitives are strictly scoped as
  attention/retrieval hints and long demonstrations remain the primary few-shot
  examples.
- Main risks: primitives becoming a disguised rulebook, compression losing
  source fidelity, retrieval probes being too easy, and ablation lacking
  falsifiable thresholds.

Plan updates applied:

- Added `authority: attention_hint_only`, `claim_trace`, `requires_context`,
  `not_applicable_when`, and `counterexamples` to intuition primitive shape.
- Added claim-level trace and `not_to_infer` to long demonstrations.
- Added negative/control, near-miss, and transfer retrieval probes.
- Added ablation modes separating metadata-only primitives from prompt-injected
  primitives.
- Added rubric and failure criteria.
- Added PM spot-check requirements for cluster compression.

Boundary:

- No runtime code changed.
- No gold cases promoted.

## 2026-05-01 - P10h PM Review Context Packet Update

Trigger:

- PM reviewed early second-wave items and requested the remaining review list
  include concrete source context.

PM decisions recorded:

- `dc_sw2_poison_starfall_threat_model`: `accept_with_revision`; 迅捷水刃 should
  be anchored as a 圣羽翼王打法, with 水刃 as the canonical move.
- `ctx_sw2_starfall_archetype_design_intent`: same 迅捷水刃 correction applies.
- `dc_sw2_poison_starfall_shura_vs_pal_rps_branch`: `accept_with_revision`;
  缠丝进 should be corrected to 缠丝劲.

Artifacts:

- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/pm_review_updates_2026_05_01.yaml`.
- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/pm_case_review_with_source_context.md`.
- Marked the older `pm_case_review_list.md` as superseded for active review.

Boundary:

- No runtime code changed.
- No gold cases promoted.

## 2026-05-01 - No-D-Layer Runtime Test Planning

Trigger:

- PM asked whether Roco Agent can work normally before D-layer Expert
  Demonstration retrieval is connected, and requested test planning.

Findings:

- Current `/chat` runtime path goes through `AdvisorService`,
  `AgentOrchestrator`, and `AdvisorAgent`.
- Runtime uses A-layer Battle Dex, B-layer doc retrieval, team context,
  persona/presentation, and request-scoped provider config.
- Runtime does not read `data/expert_demonstrations`.
- P10h materials remain draft artifacts/specs, not runtime inputs.

Validation:

- `.venv/bin/python -m unittest tests.test_api tests.test_agent_core_orchestrator tests.test_advisor`
  passed: 92 tests.
- `.venv/bin/python -m unittest tests.test_public_hardening tests.test_persona_profile_resolver`
  passed: 19 tests.

Artifact:

- Added `artifacts/p10h_no_d_layer_runtime_test_plan_2026_05_01.md`.

Interpretation:

- D-layer is a tactical-quality enhancement, not a prerequisite for the V1
  baseline Agent chat path.
- Real LLM chat still requires valid request-scoped provider configuration.

## 2026-05-01 - P10h Prebattle Ablation Experiment Plan

Trigger:

- PM asked to revise Cle's experiment design into a complete executable plan.

Artifacts:

- Added `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md`.
- Added `specs/p10h_prebattle_ablation_experiment_plan.md` as a short pointer.

Key corrections:

- Split D-layer into `L3-exact` and `L3-transfer` to separate same-source
  answer-leakage upper bound from true reusable demonstration value.
- Marked L4 as future/optional because D-layer runtime retrieval and index do
  not exist yet.
- Defined `L4-retrieval-only` as retrieval-loss measurement and `L4-e2e` as
  full end-to-end gap; these must not be conflated.
- Required answer keys before generation.
- Corrected preview information boundary: fixed species facts are A-layer
  facts, while moves/nature/individual bonuses/wish-force configuration may be
  hidden or uncertain.
- Forbid storing hidden chain-of-thought/provider reasoning traces.
- Replaced statistical significance language with directional signal and error
  mode analysis.

Boundary:

- No experiment execution happened.
- No runtime code changed.
- No gold cases promoted.
- Source-only Pokemon analogy remains marked as contamination and is forbidden
  for generated tactical reasoning.

## 2026-05-01 - P10h External Agent Brief

Trigger:

- PM requested a short handoff document for external Agent Cle explaining what
  the current workstream is doing, with references instead of inlining all
  context.

Artifact:

- Added `artifacts/p10h_cle_external_agent_brief_2026_05_01.md`.

Boundary:

- No runtime code changed.
- No extraction artifacts were modified.
- No gold cases promoted.

## 2026-05-01 - P10h PM Case Review List

Trigger:

- PM requested every extracted case to be listed for review.

Artifact:

- Added `artifacts/p10h_expert_demo_extraction/second_wave_corrected_text_2026_05_01/pm_case_review_list.md`.

Content:

- 28 candidate cases listed with source span, family/type, situation,
  extracted conclusion, reasoning pattern, failure branch, tags, and PM review
  placeholders.
- 9 expert context primitives listed separately with summary, value, suggested
  use, review questions, and PM review placeholders.

Boundary:

- No runtime code changed.
- No gold cases promoted.

## 2026-05-01 - P10h D2 / B-Layer Boundary Correction

Trigger:

- PM identified that concrete archetype-specific priors in the first D2 draft
  are closer to B-layer knowledge than runtime-near general D-layer coach
  priors.

Changes:

- Rewrote
  `artifacts/p10h_intuition_demo_pack/expert_tactical_priors.yaml` from mixed
  D2 priors into `D2_general_expert_tactical_priors`.
- Added
  `artifacts/p10h_intuition_demo_pack/b_layer_archetype_prior_candidates.yaml`
  to preserve concrete Starfall/Poison/Wing King/Begus/Fox knowledge as
  retrievable B-layer candidates instead of always-on D-layer memory.
- Updated the D-layer maintenance contract, PM review packet, eval probe design,
  and cluster notes to reflect the new boundary.

Boundary:

- No runtime integration changed.
- No B-layer gold ingest happened.
- No `data/expert_demonstrations` writes happened.
- This is a draft artifact-layer correction before PM review/eval.

## 2026-05-02 - P10h App-Path Experiment Harness

Trigger:

- PM asked to prepare the P10h experiment so the harness uses the current app
  Agent path and can access A/B/C/D layers intentionally.

Changes:

- Added `advisor/experiment_layers.py`, an experiment-only retriever that wraps
  the production `DocContextRetriever` and conditionally exposes draft Bplus,
  D1, D2, and D3 snippets through the existing `retrieve_doc_context` tool.
- Added optional `doc_retriever_factory` injection to `AdvisorService`; default
  app behavior remains unchanged.
- Added `tools/p10h_experiment_harness.py`, which calls
  `AdvisorService.chat -> AdvisorAgent`, matching the app `/chat` backend path.
- Added `artifacts/p10h_agent_harness_probe/README.md` documenting layer access
  and live/static commands.
- Added `tests/test_p10h_experiment_layers.py` to guard layer-diverse retrieval
  and negative-query non-injection.

Validation:

- `.venv/bin/python -m py_compile advisor/experiment_layers.py tools/p10h_experiment_harness.py api/services/advisor_service.py`
- `.venv/bin/python tools/p10h_experiment_harness.py --condition A_B_C_Bplus_D1_D2_D3 --output-dir artifacts/p10h_agent_harness_probe/smoke_static`
- `.venv/bin/python -m unittest tests.test_p10h_experiment_layers tests.test_retrieval tests.test_api -q`

Boundary:

- The smoke run without `--native` only validates app-path plumbing; it does not
  evaluate real tactical answer quality because deterministic MVP routing is
  intentionally limited.
- Bplus/D1/D2/D3 remain draft experiment assets and are not production runtime
  gold.

## 2026-05-02 - P10h Controlled L0-L3 Ablation Harness

Trigger:

- PM asked to ensure the previous ablation plan remains meaningful and to avoid
  improvising the experiment at execution time.
- PM also compared Cle's initial pre-work checklist with the later optimized
  plan and asked whether the optimized version is more complete.

Changes:

- Added `tools/p10h_prebattle_ablation_harness.py`, a controlled offline
  harness for the canonical L0/L1/L2/L3-exact/L3-transfer experiment defined in
  `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md`.
- Added scaffolded prebattle case YAML templates under
  `artifacts/p10h_prebattle_ablation/inputs/`.
- Added per-level prompt/grounding pack generation under
  `artifacts/p10h_prebattle_ablation/{grounding_packs,prompts}`.
- Added blind-review packet generation and score-sheet scaffolding under
  `artifacts/p10h_prebattle_ablation/blind_review/`.
- Added tests in `tests/test_p10h_prebattle_ablation_harness.py`.

Plan alignment:

- This harness implements the optimized plan rather than Cle's earlier
  checklist-only version: it preserves clean L0-L3 grounding isolation,
  separates L3-exact from L3-transfer, blocks generation until PM answer keys
  are filled, and keeps app-path/L4 evaluation separate.
- L2 includes Bplus archetype-prior candidates because the current boundary
  decision moved concrete archetype knowledge out of always-on D2 and into
  B-like experiment context.
- L3 currently injects D3 long demonstrations only; app-path access to D1/D2/D3
  is covered separately by `tools/p10h_experiment_harness.py`.

Validation:

- `.venv/bin/python -m py_compile tools/p10h_prebattle_ablation_harness.py tests/test_p10h_prebattle_ablation_harness.py`
- `.venv/bin/python -m unittest tests.test_p10h_prebattle_ablation_harness tests.test_p10h_experiment_layers tests.test_retrieval tests.test_api -q`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py scaffold --output-dir artifacts/p10h_prebattle_ablation --overwrite`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --allow-incomplete-answer-key`

Boundary:

- The normal build correctly blocks live generation because current scaffolded
  answer keys still contain TODO values.
- The `--allow-incomplete-answer-key` mode is for prompt/grounding inspection
  only and should not be used for live evaluation.

## 2026-05-02 - P10h Ablation Plan / Scoring Protocol Update

Trigger:

- PM asked to incorporate CC's updated scoring-plan direction and to make the
  experiment plan sufficient for any external Agent with repo access to execute
  without guessing.

Changes:

- Updated
  `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md` from an
  executable draft into a harness-backed execution manual.
- Added external-Agent quickstart, canonical file list, current implementation
  state, explicit harness mapping, build/run commands, and answer-key gate
  behavior.
- Added answer-key requirements and optional source/scoring notes so judge
  scoring is anchored to source material rather than post-hoc PM taste.
- Expanded blind-review/scoring protocol with current harness artifact names,
  hard flags, normalized score bands, and the temporary boundary for external
  LLM judge execution before a dedicated judge script exists.
- Updated `specs/p10h_prebattle_ablation_experiment_plan.md` pointer to reflect
  the current harness-backed plan.

Validation:

- `.venv/bin/python -m py_compile tools/p10h_prebattle_ablation_harness.py tests/test_p10h_prebattle_ablation_harness.py`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --allow-incomplete-answer-key`

Boundary:

- No live model generation was run.
- Normal build still correctly blocks because PM answer keys remain TODO.
- The scoring protocol is specified; a dedicated `run_llm_judge.py` remains
  future work unless an external judge Agent performs the scoring manually from
  the blind packet.

## 2026-05-02 - P10h External Plan Update Ingested

Trigger:

- PM reported that an external agent updated the P10h experiment plan and asked
  Codex to receive/check it.

Findings:

- External update changed the case answer keys from the older flat
  `lead_recommendation/key_matchups/game_tree/risk` schema to a D-layer
  diagnostic schema:
  `archetype_recognition`, `d1_attention_order`, `d2_activated_priors`,
  `d3_reasoning_chain`, `conditional_knowledge`, `evaluation_checklist`, and
  `what_if_questions`.
- The plan claimed normal build/run should no longer block, but the harness
  still validated the old flat schema and failed on all three updated cases.

Changes:

- Updated `tools/p10h_prebattle_ablation_harness.py` validation to accept the
  new D1/D2/D3 structured answer-key schema while retaining legacy schema
  compatibility.
- Updated prompt assembly so What-If sub-questions are included in the model
  task and must be answered after the main prebattle answer.
- Updated blind-review score template from old lead/matchup dimensions to
  D-layer diagnostic dimensions: `d1_alignment`, `d2_alignment`,
  `d3_alignment`, `what_if`, `answer_usefulness`, plus hard flags.
- Updated `tests/test_p10h_prebattle_ablation_harness.py` for the new structured
  schema.
- Cleaned the canonical plan's leftover old answer-key and scoring sections so
  it no longer contradicts the external D1/D2/D3 scoring design.

Validation:

- `.venv/bin/python -m py_compile tools/p10h_prebattle_ablation_harness.py tests/test_p10h_prebattle_ablation_harness.py`
- `.venv/bin/python -m unittest tests.test_p10h_prebattle_ablation_harness -q`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --repeats 3`

Result:

- Controlled build now passes with `case_count=3`, `levels=5`, `repeats=3`,
  `call_count=45`, and `validation_errors=[]`.
- No live model generation was run.

## 2026-05-02 - P10h Completeness Report Reconciled

Trigger:

- PM provided an external completeness report that marked the experiment docs
  and harness mostly complete, but flagged missing what-if integration and
  unselected L3 D-layer material as pre-run blockers.

Findings:

- What-if subquestions were already integrated into
  `tools/p10h_prebattle_ablation_harness.py` and generated prompts.
- The real remaining blocker was L3 D material selection: the harness still
  used lexical same-source / overlap fallback, which made `L3-exact` and
  `L3-transfer` less controlled than the experiment design required.

Changes:

- Added `demo_wingking_poison_snake_lead_water_jellyfish` to
  `artifacts/p10h_intuition_demo_pack/long_demonstrations.yaml` so Case A has
  a direct same-source D3 demonstration for the 寒音蛇 / 琉璃水母 lead logic.
- Added
  `artifacts/p10h_prebattle_ablation/d_layer_selection_manifest.yaml` to pin
  first-pass L3-exact and L3-transfer D3 demo ids for each case.
- Updated `tools/p10h_prebattle_ablation_harness.py` so the D selection manifest
  takes precedence over lexical auto-selection.
- Updated the canonical plan, pointer spec, and experiment README to document
  manifest-pinned D selection.

Validation:

- `.venv/bin/python -m py_compile tools/p10h_prebattle_ablation_harness.py tests/test_p10h_prebattle_ablation_harness.py`
- `.venv/bin/python -m unittest tests.test_p10h_prebattle_ablation_harness -q`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --repeats 3`

Result:

- Build passes with `case_count=3`, `levels=5`, `repeats=3`,
  `call_count=45`, and `validation_errors=[]`.
- What-if subquestions appear in 15 prompts.
- L3 D material is now explicit and reviewable; no live model generation was
  run.

## 2026-05-02 - P10h Primitive-Level Failure Logging Added

Trigger:

- PM clarified that the experiment must not only score D-layer usefulness, but
  also reveal what the current D layer lacks so D1/D2/D3 can be repaired after
  the run.

Changes:

- Updated the judge contract in
  `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md` so any
  non-full D1/D2/D3/what-if score must include `failed_checks`.
- Added a primitive failure schema with `primitive_id`, `if_fail`,
  `failure_type`, `repair_target`, and `suggested_fix`.
- Updated `tools/p10h_prebattle_ablation_harness.py` so blind packet generation
  writes:
  - `blind_review/score_sheet_template.csv` with `failed_checks_count` and
    `failed_checks_json`;
  - `blind_review/primitive_failure_log_template.csv` for row-level failed
    checklist items.
- Updated the pointer spec and experiment README to document primitive-level
  failure logging.
- Added a harness unit test that asserts blind packet generation includes the
  primitive failure templates.

Validation:

- `.venv/bin/python -m py_compile tools/p10h_prebattle_ablation_harness.py tests/test_p10h_prebattle_ablation_harness.py`
- `.venv/bin/python -m unittest tests.test_p10h_prebattle_ablation_harness -q`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --repeats 3`
- `.venv/bin/python tools/p10h_prebattle_ablation_harness.py blind --output-dir artifacts/p10h_prebattle_ablation`

Result:

- Tests pass.
- 45-call build still passes with `validation_errors=[]`.
- Blind review templates now include primitive-level D-layer repair fields.
- No live model generation was run.

## 2026-05-02 - P10h Smoke Acceptance and Prompt Metadata Guard

Trigger:

- PM asked whether the completed P10h smoke run can be accepted.

Findings:

- Smoke produced 5 output JSON files and `raw_results.json`.
- All 5 calls completed with `status=ok`.
- API key/provider URL redaction passed; provider base URL appears only as
  `[REDACTED]`.
- Blind packet and reveal map were generated for the smoke set.
- Content smoke exposed a preventable prompt contamination: some answers
  mentioned internal metadata such as `B+` and `grounding/source material`.

Changes:

- Updated `tools/p10h_prebattle_ablation_harness.py` prompt assembly to forbid
  user-visible internal metadata: `grounding`, `A-layer/B-layer/D-layer`, `B+`,
  `L0-L3`, retrieval, model, prompt, source/material labels, and standard-answer
  labels.
- Updated the canonical plan and pointer spec so judge scoring treats internal
  metadata leakage as answer-usefulness/prompt repair signal.

Result:

- Technical smoke is accepted.
- Full generation should use the patched prompt and rerun smoke first; the old
  smoke outputs are useful as diagnostics but should not be mixed into the
  final 45-call dataset.

## 2026-05-02 - P10h Second Smoke Found Source-Label Echo

Trigger:

- The experiment executor reran a 5-call smoke with the prompt metadata guard.

Findings:

- Technical smoke passed again: 5/5 calls `ok`, redaction clean, blind packet
  and templates regenerated.
- Content guard was clean for `B+`, `grounding`, A/B/D-layer labels, L0-L3,
  retrieval, model, prompt, and source.
- One L0 output repeated `源素材` in the What-If answer because the Case C
  What-If question itself contained `源素材的高玩评价`.

Changes:

- Reworded Case C What-If from `源素材的高玩评价` to `目前已知信息里有什么明确评价`.
- Reworded the matching key point from `源素材没有展开分析` to `当前已知信息没有展开分析`.
- Updated the canonical plan to state that What-If task text must not contain
  source/material labels that induce final-answer metadata echo.

Result:

- Patched inputs/prompts should be rebuilt before the next smoke.
- The second smoke remains a useful diagnostic artifact but should not be mixed
  into the final 45-call dataset.

## 2026-05-02 - P10h Final Mini-Smoke Passed

Trigger:

- The experiment executor reran the patched 5-call mini-smoke after removing
  source/material labels from the What-If task text.

Result:

- 5/5 calls completed with `status=ok`.
- `raw_results.json` count: 5.
- blind packet count: 5.
- score and primitive failure templates regenerated.
- API key leak scan clean.
- answer-only internal metadata leak scan: 0 hits.
- Executor did not read `reveal/reveal_map.json`.

Decision:

- Smoke gate is accepted.
- Full 45-call generation is approved from the execution-readiness gate.
- The final dataset should be generated from the patched prompts, not from
  earlier smoke outputs.

## 2026-05-02 - P10h Full 45-Call Generation Passed

Trigger:

- The experiment executor ran the formal full generation after the final
  mini-smoke passed.

Command:

```bash
.venv/bin/python tools/p10h_prebattle_ablation_harness.py run \
  --output-dir artifacts/p10h_prebattle_ablation \
  --model deepseek-v4-pro \
  --reasoning-mode enabled \
  --reasoning-effort high \
  --repeats 3
```

Result:

- `raw_results.json` count: 45.
- 45/45 calls completed with `status=ok`.
- `failed_count=0`.
- `blind_review_packet.json` count: 45.
- blind statuses: `ok`.
- score sheet template exists.
- primitive failure log template exists.
- API key leak scan clean.
- answer-only internal metadata leak scan clean, 0 hits.
- Old final mini-smoke artifacts were archived under:
  `artifacts/p10h_prebattle_ablation/analysis/archive/final_mini_smoke_before_full_45_20260502_215134`.

Boundary:

- `reveal/reveal_map.json` was generated by the harness but not read by the
  executor.
- No judge scoring has started yet.

Decision:

- Full generation is accepted.
- Next step is blind judge scoring without reading `reveal/reveal_map.json`.

## 2026-05-03 - P10h Blind Judge Scoring Complete

Trigger:

- The experiment executor completed Codex blind judge scoring for the full
  45-call generation dataset.

Result:

- `judge_scores` count: 45.
- `score_sheet_completed.csv` exists with 46 rows including header.
- `primitive_failure_log_completed.csv` exists with 344 rows including header.
- malformed judge JSON count: 0.
- uncertain score count: 0.
- failed checks total: 343.
- no-reveal boundary obeyed.

Boundary:

- Executor reported that `reveal/reveal_map.json`, `outputs/*.json`, and
  `run_order.json` were not read.
- No level aggregation was performed.

Decision:

- Blind scoring is accepted.
- Next step is reveal + aggregation + D-layer repair backlog.

## 2026-05-03 - P10h Reveal Aggregation Complete

Trigger:

- The experiment executor completed reveal, score aggregation, and D-layer
  repair backlog generation after blind judging.

Artifacts:

- `artifacts/p10h_prebattle_ablation/analysis/prebattle_ablation_report.md`
- `artifacts/p10h_prebattle_ablation/analysis/d_layer_repair_backlog.md`
- `artifacts/p10h_prebattle_ablation/analysis/score_summary_by_level.csv`
- `artifacts/p10h_prebattle_ablation/analysis/score_summary_by_case_level.csv`
- `artifacts/p10h_prebattle_ablation/analysis/primitive_failure_summary.csv`

Integrity:

- reveal rows: 45.
- score rows: 45.
- primitive failure rows: 343.
- per-level count: 9 each.
- per-case-level count: 3 each.

Key deltas:

- `L1 - L0 = +2.67 raw`.
- `L2 - L1 = +0.33 raw`.
- `L3-exact - L2 = +3.78 raw`.
- `L3-transfer - L2 = -0.67 raw`.
- `L3-exact - L3-transfer = +4.44 raw`.

Decision:

- A-layer has clear directional value.
- B-layer lift is weak in this run.
- Exact D gives large lift but likely same-source / answer-leakage value.
- Transfer D is not reliably reusable yet and should not be scaled blindly.
- Continue D-layer work only as targeted repair: D1/D2 primitive coverage, D3
  abstraction, prompt hidden-config guard, and case-specific transfer failures.

Correction:

- Fixed a misleading generated backlog line that said exact and transfer were
  "close overall"; data shows the opposite.

## 2026-05-03 - P10h D3 Transfer Use Rule Added

Trigger:

- PM questioned whether L3-transfer prompts explicitly told the model to treat
  D3 transfer material as meta-method demonstrations rather than current-case
  answers.

Finding:

- The L3-transfer prompt included D3 examples with `what_to_imitate` and
  `not_to_infer`, but lacked an outer instruction that the examples are
  non-identical transfer material. This means part of the poor L3-transfer
  result may be a prompt-seam artifact, not only weak D-layer content.

Changes:

- Added `_d_layer_use_rule()` to
  `tools/p10h_prebattle_ablation_harness.py`.
- L3-transfer grounding now states that D3 examples are related but
  non-identical and must be used only for method transfer, not copied species
  choices or conclusions.
- L3-exact grounding now states that same-source examples are high-relevance
  demonstrations but still must be reconstructed from current task input.
- Updated the canonical plan, experiment README, and D-layer repair backlog.

Boundary:

- No live rerun was performed. This patch should be validated by a targeted
  rerun before interpreting L3-transfer as content-only failure.

## 2026-05-03 - P10h-R1 Transfer Rule Targeted Rerun Complete

Trigger:

- The experiment executor ran a targeted rerun to test whether the new
  L3-transfer use rule improves transfer performance.

Setup:

- Output dir: `artifacts/p10h_prebattle_ablation_r1_transfer_rule`.
- Levels: `L2`, `L3-transfer`, `L3-exact`.
- Cases: same 3 original cases.
- Repeats: 3.
- Total calls: 27.
- Model: `deepseek-v4-pro`, thinking enabled, reasoning effort high.
- Manifest source: `original_p10h_manifest_fallback`.

Integrity:

- build passed with `validation_errors=[]`, `call_count=27`, `prompts=9`,
  `grounding_packs=9`.
- generation passed with 27/27 `status=ok`.
- blind scoring completed before reveal.
- reveal/aggregation completed with blind_id consistency.
- leak scans clean.

R1 deltas:

- old `L3-transfer - L2 = -0.67 raw`.
- R1 `L3-transfer - L2 = +0.00 raw`.
- improvement: `+0.67 raw`.
- old `L3-exact - L2 = +3.78 raw`.
- R1 `L3-exact - L2 = +2.44 raw`.
- old `L3-exact - L3-transfer = +4.44 raw`.
- R1 `L3-exact - L3-transfer = +2.44 raw`.

Decision:

- The transfer-use-rule patch helped: it removed the negative transfer effect.
- The patch is not sufficient: transfer did not become positive overall.
- Next work should move from prompt seam repair to D3 demo abstraction repair:
  convert concrete battle narratives into method cards / reasoning skeletons.

Correction:

- Fixed a generated R1 report line that incorrectly said exact was below
  transfer; table data shows exact remained above transfer by `+2.44 raw`.

## 2026-05-03 - P10h Full-Roster Input Correction

Trigger:

- PM pointed out that the P10h prebattle ablation cases did not match the
  originally intended full visible-team preview setup.
- The previous 45-call and R1 experiments used compressed/source-derived
  partial rosters. This remains useful as a diagnostic run, but not as the final
  full-roster prebattle evaluation.

Changes:

- Updated `tools/p10h_prebattle_ablation_harness.py` scaffold templates:
  - `prebattle_poison_vs_starfall`: our side now includes `翠顶夫人`, `千棘盔`;
    opponent now includes `权杖-V`, `怖哭菇`, `翠顶夫人`.
  - `prebattle_thunder_wingking_fast_balance`: our side now includes `岚鸟`;
    opponent roster replaced with `翠顶夫人`, `圣羽翼王`, `岚鸟`, `秩序鱿墨`,
    `朔夜伊芙`, `圆号鱼`.
  - `prebattle_wingking_poison_vs_snake_balance`: our side now includes
    `棋齐垒`, `翠顶夫人`; opponent now includes `圆号鱼`, `黑猫巫师`, `化蝶`.
- Updated active `artifacts/p10h_prebattle_ablation/inputs/*.yaml` rosters.
- Added `roster_revision_warning: TODO` to each active answer key so generation
  is blocked until scoring anchors/checklists are re-audited against the
  corrected full rosters.

Boundary:

- Existing outputs, blind scores, and analysis reports are intentionally left as
  historical artifacts for the old partial-roster diagnostic condition.
- Any corrected full-roster claim requires a fresh build/run in a new output
  directory after answer-key repair.

## 2026-05-03 - P10h Case Numbering Drift Guard

Trigger:

- PM flagged that the three scenario numbers and three task/file numbers might
  not correspond. This is a real experiment-contamination risk because the
  canonical plan used Case A/B/C, while filename/output order could be
  alphabetical.

Finding:

- Canonical plan order:
  - Case A / order 1: `prebattle_wingking_poison_vs_snake_balance`.
  - Case B / order 2: `prebattle_poison_vs_starfall`.
  - Case C / order 3: `prebattle_thunder_wingking_fast_balance`.
- Alphabetical filename order is B/C/A:
  - `prebattle_poison_vs_starfall.yaml`.
  - `prebattle_thunder_wingking_fast_balance.yaml`.
  - `prebattle_wingking_poison_vs_snake_balance.yaml`.
- Current attachment audit:
  - `贝古斯` 4-energy / 防御-倾泻互斥 belongs to Case A.
  - 星陨队 `落陨星兔` / `龙息帕尔` / `怖哭菇` branches belong to Case B.
  - The old `落陨星兔` what-if in Case C is orphaned for the corrected full
    roster and must not be used as an active scoring anchor.

Changes:

- Added `case_label` and `case_order` to the active case YAMLs and harness
  scaffold templates.
- Updated `tools/p10h_prebattle_ablation_harness.py` to sort loaded cases by
  `case_order` instead of filename order.
- Added `case_label` / `case_order` to run, reveal, and blind-review artifacts.
- Updated the P10h plan, pointer spec, and staleness audit to forbid bare
  `1/2/3` references. Use `Case A/B/C` or `case_id` only.
- Moved Case C old `落陨星兔` orphaned fragments out of `answer_key` to a
  top-level `orphaned_fragments` block so preserved evidence cannot be mistaken
  for active scoring anchors.
- Reworded Case C what-if Q1 to remove the model-visible "if information is
  insufficient" hint. The scoring key still tests whether the answer preserves
  uncertainty when evidence is thin.
- Added Case C what-if Q2 to test current full-roster role allocation across
  闪电鳗鱼, 画间沉铁兽, 贝古斯, and wing pressure slots.
- Corrected Case B Dragon-Breath Pal resource wording: Pal-caused KOs add 1
  extra magic loss, making the relevant faint cost 2; Pal's own faint also costs
  2. Updated the prompt/checklist wording away from vague "扣一点魔力".
- Corrected Case B what-if Q2 subject from opponent-side to our-side
  traditional poison vs balance poison.
- Re-corrected the 雷暴翼王 mechanism after PM clarification and A-layer check:
  the move is `双联脉冲`, not `双人脉冲`; its effect is "造成魔伤，迸发：本技能使用次数+1".
  `雷暴` has "造成魔伤，迸发：本技能获得所有生效过的迸发，每获得1种，本技能能耗+1，威力+10".
  闪电鳗鱼首发 value is 泡沫幻影 scouting/rotation, 双联脉冲 laying a reusable
  burst for later 雷暴, and potential pressure into common leads such as 圆号鱼.

Validation:

- `py_compile` passed for `tools/p10h_prebattle_ablation_harness.py`.
- `unittest tests.test_p10h_prebattle_ablation_harness -q` passed.
- Temporary build with `--allow-incomplete-answer-key` produced case order:
  Case A, Case B, Case C.
- Normal build still exits `2` because all active answer keys contain TODO, as
  intended.

## 2026-05-03 - V1 Alpha Handoff Created

Trigger:

- PM requested a zero-context handoff document so a future Agent can continue
  without reading the full conversation.

Artifact:

- `docs/ROCO_V1_ALPHA_HANDOFF_2026_05_03.md`

Content:

- Current phase: V1 Alpha release closure.
- Release framing: self-hosted/developer Alpha unless a hosted HTTPS backend is
  explicitly deployed.
- Release claim: A/B/C-layer grounded Agent chat only.
- D-layer/P10h status: post-V1 enhancement and not a release claim.
- Canonical read order for successor Agents.
- P7/P8/P9/P10 state summary.
- Proposed P11 closure slices:
  - release readiness audit;
  - slow-call loading UX minimum;
  - fresh iOS live smoke;
  - ABC coach smoke cases;
  - release docs and known limitations.
- Distribution reality:
  - mobile app is a client;
  - Python/FastAPI backend is external to the phone;
  - APK without backend is not standalone.

Decision:

- Future work should resume from P11 release closure, not P10h, unless PM
  explicitly pauses release work.

## 2026-05-03 - Desktop Developer Clone Shell

Trigger:

- PM decided V1 distribution should prioritize a desktop/developer-clone path
  before Windows packaging, because the current mobile shell still requires a
  separate backend and is not a normal standalone app distribution story.

Decision:

- Use the Web React visual prototype as the desktop UI base, not the Expo RN
  implementation. Electron can consume Web DOM/CSS directly, while the RN app
  remains a behavior/reference implementation for the mobile path.
- Implement developer-clone first. Windows installer / bundled backend remains
  a later packaging slice.

Changes:

- Added `desktop/` as an Electron + Vite + React + TypeScript app.
- Added Electron main/preload boundary:
  - renderer has no Node integration or filesystem access;
  - Product API requests go through preload IPC;
  - provider secrets are encrypted with Electron `safeStorage` before local
    persistence.
- Added `BackendManager` to reuse an existing `127.0.0.1:8000` Product API or
  start `.venv` uvicorn from the repo. A startup promise lock prevents
  duplicate concurrent backend spawns.
- Ported the paper-shell chat UI using the accepted PNG paper assets.
- Replaced prototype mock messages with live `/chat` calls, default
  `you_know_who` managed persona selector, compact visible reply handling, and
  provider runtime headers.
- Right drawer now has exactly three top-level entries:
  - `队伍设置`: search/select 0-6 species from Battle Dex and attach structured
    team context to chat.
  - `API 设置`: save provider key/base/model/thinking config and run Product API
    / model diagnostics.
  - `人格设置`: switch `You know who` and default built-in assistant; persona
    creation remains a reserved seam.
- Added `scripts/run_desktop_dev.sh` and README instructions.
- Added `.gitignore` entries for `desktop/node_modules/` and `desktop/dist/`.

Validation:

- `bash -n scripts/run_desktop_dev.sh` passed.
- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed, producing renderer/main/preload builds.
- `cd desktop && npm audit --json` reported zero vulnerabilities after moving
  Electron/Vite to patched versions.
- Backend API regression check passed:
  `.venv/bin/python -m unittest tests.test_api tests.test_advisor -q`.
- Short `npm start` smoke opened Electron and started one uvicorn backend. An
  initial double-spawn race was observed and fixed with the backend startup
  promise lock; the follow-up smoke no longer attempted a second bind to port
  8000.

Follow-up UI correction:

- Removed automatic DevTools opening in desktop dev mode.
- Switched the Electron window to a transparent frameless shell so the desktop
  app can move toward a Claudio-style integrated window instead of showing a
  normal macOS title bar.
- Removed the redundant top-left settings FAB. Settings now enter only through
  the right rail/handle.
- Fixed the closed drawer transform so only the rail handle is visible; the
  drawer panel no longer leaks large cards into the main chat surface.
- Tightened the default desktop window from `440x900` to `414x860` and reduced
  paper/content insets for better proportion.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- Short `npm start` smoke showed one Electron app and one uvicorn backend. All
  smoke processes were terminated afterward; port `8000` was clear.

## 2026-05-03 - RoCoach Naming And Persona Wheel Restoration

Trigger:

- PM flagged that persona switching had regressed from the avatar long-press
  wheel into a drawer submenu, and that `人格设置` should not become a secondary
  settings flow in V1.
- PM proposed `RoCoach` as the formal product name.

Decision:

- Adopt `RoCoach` as the desktop-facing product name. Keep internal package /
  backend naming mostly under Roco for now to avoid broad release-week rename
  risk.
- Restore persona switching to the chat surface: long-press the agent avatar to
  open the avatar-anchored wheel.
- Keep the right drawer top-level `人格设置` as informational only: current
  persona plus the tip "长按聊天页面头像切换人格".

Changes:

- Changed desktop window/app title and desktop package description to
  `RoCoach`.
- Removed the persona drawer route and persona secondary menu.
- Added a desktop persona wheel overlay with `You know who`, `默认AI助手`, and a
  disabled reserved add-persona seam.
- Updated desktop README wording for RoCoach and the new persona boundary.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up icon fidelity pass:

- PM found the sword and status icons still drifted from the approved PNG
  reference.
- Kept the inline SVG implementation, but redrew only the physical and status
  paths:
  - physical now reads as a short-hilt diagonal sword with a wider blade and a
    small gold inner stroke;
  - status now reads as a single rounded spiral stroke rather than a dense
    shell-like curve.
- No interaction or layout behavior was changed in this pass.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.

Desktop Team Builder species search recall fix:

- PM observed that searching `圣` did not show `圣羽翼王`, while searching
  `圣羽` did.
- Root cause:
  - desktop requested only the first 12 species search hits;
  - backend broad search ranked by short display-name length;
  - multi-form species such as `圣代甜甜` occupied many early slots;
  - `圣羽翼王` was present in the SQL-backed result set, but ranked outside the
    desktop-visible limit.
- Updated `BattleDexRepository.search_species`:
  - exact searches still preserve same-name form variants for disambiguation;
  - broad searches now diversify by `display_name` first, then append overflow
    form variants if there is remaining room;
  - prefix matches rank ahead of contains-only matches.
- Added API regression coverage proving `圣` with limit 12 includes
  `圣羽翼王` and does not let `圣代甜甜` fill the first page.

Validation:

- `.venv/bin/python -m unittest tests.test_api.ApiTests.test_species_search_and_profile tests.test_api.ApiTests.test_species_search_exposes_regional_form_for_disambiguation tests.test_api.ApiTests.test_species_search_diversifies_broad_single_character_matches`
  passed.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 237 tests`,
  `OK`.
- `cd desktop && npm run typecheck && npm run build` passed.

Desktop Team Builder slot focus persistence fix:

- PM observed that selecting a species in any non-first slot immediately jumped
  the editor back to slot 1.
- Root cause:
  - species selection updates the local draft and then triggers real-time save;
  - parent `teamContext` updates from that save;
  - `TeamSettings` synchronized the new `teamContext` by resetting
    `selectedSlotIndex` to the first existing slot.
- Changed the sync effect to preserve the current editing slot and only clamp it
  to the legal `1..6` range.
- This keeps real-time save behavior while preventing focus jumps.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.

Desktop Team Builder species search regional-suffix boundary:

- PM clarified that species search should not match regional/form suffix text.
  Example: searching `水` should not return `地鼠（枯水期的样子）` merely because
  the suffix contains `水`.
- Root cause:
  - the runtime SQLite stores some `initial_species_name` values with
    parenthetical form text, such as `地鼠(枯水期的样子)`;
  - search matched the raw field, so suffix-only hits leaked into the main
    species search.
- Updated `BattleDexRepository.search_species` to filter and rank candidates
  against:
  - `species_id`;
  - canonical `display_name`;
  - `initial_species_name` with parenthetical form suffix removed.
- This keeps base-name disambiguation working. For example, `小狮鹫` still
  returns its form variants, but `枯水` no longer matches the regional suffix.
- Added API regression coverage for `水`/`枯水`.

Validation:

- `.venv/bin/python -m unittest tests.test_api.ApiTests.test_species_search_exposes_regional_form_for_disambiguation tests.test_api.ApiTests.test_species_search_diversifies_broad_single_character_matches tests.test_api.ApiTests.test_species_search_ignores_regional_form_suffix_text`
  passed.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 238 tests`,
  `OK`.
- `cd desktop && npm run typecheck && npm run build` passed.

Desktop Team Builder empty-slot highlight fix:

- PM observed that opening an empty card slot and returning without selecting a
  species still made that slot appear highlighted on the board.
- Root cause:
  - the first-level board used `selectedSlotIndex` as a visual active state even
    when no slot data existed;
  - this mixed "currently inspected" with "configured".
- Updated the board so `active` only applies when the slot already has a
  species-backed `TeamContextSlot`.
- Split hover styling from active/filled styling:
  - empty slot hover gets only a light inspection affordance;
  - yellow filled/active treatment now means a configured card.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.

Desktop Team Builder search scope and limit update:

- PM approved raising Team Builder species search to 50 results and filtering
  entries such as `圣光迪莫` that are present in A-layer data but not usable as
  team-builder cards.
- Added `usage=team_builder` to `/species/search`.
- API limit is now up to 50, but service still clips ordinary/default searches
  to 20. Only `usage=team_builder` can consume the 50-result path.
- Team Builder now calls `/species/search?...&limit=50&usage=team_builder`.
- Team-builder eligibility is currently data-driven:
  - requires a non-empty fixed ability;
  - requires at least one available move in `species_available_moves`.
- Ordinary species search remains broader, so incomplete database entries are
  not deleted from A-layer knowledge access.
- Broad searches still diversify by display name first; form variants are
  appended after unique display-name candidates are exhausted.

Validation:

- `.venv/bin/python -m unittest tests.test_api.ApiTests.test_team_builder_species_search_filters_incomplete_entries_and_allows_50 tests.test_api.ApiTests.test_species_search_diversifies_broad_single_character_matches tests.test_api.ApiTests.test_species_search_ignores_regional_form_suffix_text`
  passed.
- `.venv/bin/python -m unittest discover -s tests` passed with `Ran 239 tests`,
  `OK`.
- `cd desktop && npm run typecheck && npm run build` passed.

Follow-up interaction correction:

- Removed the explicit Team Builder save action. Team context now auto-persists
  to local storage and the active chat context after roster/species/nature/IV/
  move edits.
- Replaced the high-weight save button with a passive `实时保存` status pill and
  kept only `清空` as the explicit destructive action.
- Updated the clear flow so it takes effect immediately instead of showing the
  stale `保存后生效` copy.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Second correction after screenshot review:

- PM flagged that the loadout board still had avoidable UI debt:
  - no-match search state was rendered as a bottom status line rather than as a
    search-panel state;
  - the panel did not account well enough for shorter/scaled windows;
  - per-slot replace/delete actions created ugly appended cards or low-value
    controls;
  - nature controls duplicated the selected nature label, lacked two-way
    plus/minus anchoring, and exposed impossible neutral plus/minus states;
  - IV rows and skill edit area were over-designed.
- Corrected by keeping one main loadout sheet:
  - search empty states now render inside the search/result panel;
  - added short-height responsive rules and `clamp()` sizing for the builder;
  - removed selected-slot replace/delete controls from the visible sheet;
  - nature plus/name/minus controls now resolve back to a valid nature option,
    and plus/minus selectors no longer expose `无`;
  - IV rows are smaller and include the PvP auto-adjustment tip;
  - skill editing uses a compact inline strip instead of a heavy duplicate card.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up avatar correction:

- Fixed empty-state avatar binding so it follows the active persona instead of
  always rendering `you_know_who`.
- Kept message avatars on the persona used for that reply, with fallback to the
  current active persona only when a message has no persona marker.
- Refactored desktop avatar CSS to scale eyes/text proportionally by avatar
  size so the main avatar and chat-row avatar preserve the same visual identity
  at different sizes.
- Removed default yellow ring from wheel avatars; wheel highlight now appears
  only on pointer hover. The active persona is indicated by the small check
  badge, not by making every wheel option glow.

Validation:

- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

## 2026-05-03 - RoCoach Desktop Team Builder Parity Pass

Trigger:

- PM asked the desktop developer-clone UI to replicate the mobile team builder
  logic instead of keeping the earlier low-fidelity species-only shortcut.
- PM also flagged the desktop shell black outer border and excessive hover glow.

Changes:

- Ported the mobile team builder interaction model into the desktop right
  drawer:
  - six fixed team slots with empty-slot selection;
  - species search using the A-layer rule "species name or initial form contains
    query";
  - species profile load for fixed ability and display labels;
  - per-species move pool search/selection, max four skills;
  - nature editor with plus/name/minus fields;
  - individual-value bonus editor, max three stat rows, values 7-10;
  - normalized save payload sent as `team_context.v1` on subsequent chat calls.
- Added desktop API client/types for `/species/{species_id}` and
  `/species/{species_id}/moves`.
- Removed the black outer shell stroke by replacing it with a yellow-integrated
  shadow, and reduced persona-wheel/avatar hover glow intensity.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up UI direction correction:

- A first "density pass" made the Team Builder smaller but still felt like a
  compressed settings form. PM rejected the result as lacking visual taste.
- Reworked the desktop Team Builder as a tactical loadout board instead:
  - top black "Battle Loadout" console with configured slot count and A-layer
    constraint copy;
  - six roster slots as compact formation tiles;
  - selected species rendered as a loadout sheet with grouped sections for
    nature, IV bonuses, and skill slots;
  - empty slots open directly into database search rather than a separate
    "choose species" button state;
  - save remains the only high-weight action, with clear demoted to a quiet
    danger action.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up card-board split:

- PM clarified that the Team Builder should first expose the top-level black
  board with six card slots, instead of dropping users directly into a dense
  single-species editor.
- Added a reversible Team Builder v2 entry state:
  - entering `队伍设置` now shows a dark "Battle Loadout" card board with six
    clickable creature-card slots;
  - filled slots show species name and type summary;
  - empty slots show a ghost card and jump into the existing species search
    detail flow when clicked;
  - the previous detailed editor remains available as the second-level fallback
    via card-slot click, with an internal "返回牌组" control;
  - autosave/clear behavior is preserved.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up less-is-more correction:

- PM rejected the remaining stacked-card feel and redundant realtime-save/clear
  controls.
- Simplified the Team Builder board:
  - board mode now uses the dark grid background as the whole page surface,
    instead of placing a separate black card on a pale page;
  - removed `实时保存` and `清空` controls from the Team Builder surface because
    persistence is already realtime;
  - removed board marketing/implementation copy and empty-slot "点击检索精灵"
    copy;
  - footer copy is now only `点击任意卡位进入单卡配置`;
  - detail mode no longer repeats the six-slot board above the single-species
    editor;
  - species header card in detail mode is now directly clickable, with hover
    affordance, to replace explicit replace/edit buttons.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up second-level card UI:

- PM clarified the second-level Team Builder page should no longer be the old
  stacked form fallback. It should directly become a creature-card
  configuration surface.
- Replaced the selected-slot detail layout with a single card-style config
  sheet:
  - species name and type pills are the card title and are clickable/hoverable
    to open species search;
  - central placeholder art frame and hanging fixed-ability tag are rendered as
    part of the card;
  - nature and individual-value bonuses are compact card fields, with hover
    edit affordance and small inline panels for editing;
  - IV display uses stat name plus four stacked horizontal blocks, filled from
    bottom to top;
  - skills render as a 2x2 card grid with small type/category badges and click
    to open the existing move picker;
  - empty slot detail remains a card-style species search entry, not a
    separate settings-form screen.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up card-page navigation and overlay editing:

- PM clarified that clicking a first-level card slot should enter the
  second-level card page directly, not a lower search form.
- Lifted Team Builder board/detail state to the drawer so the top drawer title
  can become `返回牌组` while in detail mode. Clicking the header back arrow from
  detail returns to the black card board.
- Removed the internal `返回牌组` pill from the detail page.
- Detail mode now uses the same dark grid background family as the first-level
  board.
- Empty slots now open an empty creature-card page first; clicking the species
  title opens species search.
- Species search, nature editing, IV editing, and move search now render as a
  semi-transparent overlay over the card page rather than as appended stacked
  cards below the card.
- Tightened card typography and proportions with smaller title/type/art/skill
  clamps to reduce layout breakage at the default desktop window ratio.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

Follow-up skill icon and card proportion pass:

- PM approved the final simplified generated skill-category icon direction.
- Added `desktop/src/renderer/assets/move_category_icons.png` as a compressed
  2x2 sprite for move categories:
  - physical attack: sword;
  - magical attack: wand;
  - defense: shield;
  - status/other: rune/swirl.
- Replaced skill category text placeholders such as `拳/星/盾/纹` with CSS
  sprite-backed icon badges.
- Reduced the nature/IV band height and typography.
- Increased skill-cell height and skill-name prominence so the card reads more
  like a configuration card than a compact form.
- Compressed the generated PNG from concept-art size to a UI sprite size
  (~61KB source, ~63KB built asset).
- PM then found the sprite still rendered as a miniature page inside the badge.
  Replaced the PNG sprite with inline SVG glyph components for the four move
  categories and removed the generated PNG from the desktop asset tree.
- PM then clarified that the category glyphs should stay closer to the approved
  generated icon style and should not sit inside a circular badge. The inline
  SVGs were adjusted accordingly:
  - magic now uses a star-headed wand with an inner sparkle;
  - physical uses a fuller sword silhouette;
  - defense uses a shield outline;
  - category icons are rendered without circular badge chrome, while move type
    still keeps the small circular type badge.
- PM provided the final reference set for the four icons. The inline SVGs were
  redrawn again to match that set more closely:
  - thick rounded brown outlines;
  - gold accent line in sword and shield;
  - gold filled inner sparkle in wand;
  - simple brown spiral for status.
- Tightened card typography one more step:
  - slightly smaller species title clamp;
  - smaller trait/nature labels and values;
  - shorter nature/IV band;
  - slightly smaller skill glyph badges and skill-name clamp.

Validation:

- `cd desktop && npm run typecheck` passed.
- `cd desktop && npm run build` passed.
- `cd desktop && npm audit --json` reported zero vulnerabilities.

## 2026-05-04: P10h 实验缺陷发现 & 全量数据重跑决策

### 发现

Clé 在审阅实验输出时发现大量虚构技能名（热水、冲浪、毒菱等），追查根因：

1. Harness 的 `_species_card()` 只取每个物种的 **前 8 个技能** 作为 `known available moves sample`
2. 实际 Battle Dex 中每个物种有 **30-45 个完整技能池**（如落陨星兔=45 个技能）
3. `sample` 措辞暗示模型"这不是全部，你可以补充"→ 模型用训练数据填补缺口 → 编造

### 后果

- 实验测的不是"A 层（全量 Battle Dex）对推理的贡献"，而是"8 个 sample 技能对推理的贡献"
- L0-L1 delta 被人为压低——Runtime Agent 能调用 `get_species_available_moves` 拿全量数据，实验低估了 A 层的实际价值
- 实验的 L1-L2-L3 相对比较仍然有效（所有 level 面临相同的截断），但 L1 绝对值不可用

### 决策

1. 修改 harness：移除 `[:8]` 截断 + `limit=12` 限制 + `sample` 措辞 → 全量技能池 + 封闭措辞
2. 重跑完整 45-call 实验，产出可与旧结果对比
3. 后续用 Runtime Agent 跑同一题目作为对照验证
4. 旧实验产物移到 `analysis/archive/` 保留供对比

### 相关文件

- `tools/p10h_prebattle_ablation_harness.py` — 待修改 `_species_card()` (line 470-484)
- `artifacts/p10h_prebattle_ablation/` — 旧产物将被归档
- `artifacts/p10h_prebattle_ablation_v2_full_roster/` — 新实验产物目录
- `specs/roco_agent_constitution.md` — 同步更新 §2 事实锚定原则

### 执行人

Clé 起草计划。Codex 改 harness。Clé/Codex 执行新实验。

## 2026-05-04 (continued): 转向 Runtime Agent 实验

### 决策

红队评审揭露 flat-prompt 实验的泄露链是结构性的——每修一个泄露就暴露下一个。Clé 提出用 Runtime Agent 本身跑实验，工具门控替代 prompt 拼装。

### 核心理由

1. 数据截断：flat prompt 每物种 8 个 sample vs 实际 30-45 个。Runtime Agent 调工具拿全量。
2. 泄露链不可终止：case_id 从哪里泄露到 grounding 头部，修不完。
3. Token 混淆：L0=1K vs L3=30K，跨 level 比较不公平。Runtime Agent 自主决定查多少。
4. 双重系统：实验测的不是上线系统。Runtime Agent 实验 = 上线系统。

### 架构

Harness → POST /chat + X-Roco-Tool-Allowlist header → AgentOrchestrator（工具门控）。

Level 定义：
- L0: 无工具（constitution + task only）
- L1: get_species_profile, get_species_available_moves
- L2: L1 + retrieve_doc_context, analyze_species_semantics
- L3-exact/L3-transfer: L2 + D-layer retrieval (pending implementation)

### 需要改动

- API: RequestRuntimeConfig 加 tool_allowlist
- Orchestrator: 工具注册时接受过滤
- Harness: 新建 p10h_runtime_agent_harness.py
- D 层检索工具: 暂未实现，先跑 L0-L2 (27 calls)

### 相关文件

- `artifacts/p10h_prebattle_ablation/runtime_agent_experiment_plan_2026_05_04.md`
- Flat-prompt V2 plan 废弃

## 2026-05-04 (continued): 第三次实验方案——独立 Harness Agent

### 前两次方案失败根因

1. Flat prompt：在 prompt 层模拟 Agent，泄露链结构性（修不完的 case_id/sample/物种名泄露）
2. Runtime Agent via API：生产架构（ToolRouter/validator/缓存）围绕 Agent 自主设计，不兼容 per-request 工具门控

共同根因：想在一个系统里同时满足 Agent 自主和实验者控制，两者在当前代码里不可调和。

### 第三方案：共享知识源，独立 Agent 循环

- Harness 创建自己的 pydantic-ai Agent 实例，按 level 选择性注册工具
- 共享：Battle Dex SQLite、工具实现、D 层 manifest、Constitution、LLM config
- 不共享：ToolRouter、output_validator、Agent 缓存、session 管理
- 生产代码零改动

### Harness 定位

诊断工具，用完即弃。Layer 1 消融实验跑完 → 拿到各层边际贡献 → harness 使命完成。
Layer 2 增量建设直接用 Runtime Agent（全量工具，不需要门控）。

### 相关文件

- `artifacts/p10h_prebattle_ablation/runtime_agent_experiment_plan_2026_05_04.md`（重写）

## 2026-05-07 - P11 Single Active Session KV QA Lock

Trigger:

- PM promoted P11 from review into QA after re-review returned launch_ready.

Decision:

- RoCoach V1 remains a single-chat product surface. P11 adds one persistent
  active backend Agent session, not a multi-session history UI.
- Old sessions are archived locally as JSONL summary/debug evidence for future
  import/support paths; they are not user-visible history lists in V1.
- Desktop may persist visible chat bubbles as UI-owned transcript state, but it
  must follow backend `session_event` directives. Rollover/clear clears active
  visible messages; native-history drops mark prior bubbles as stale record.

Implementation state:

- Backend active state is SQLite KV with JSONL archive.
- `/chat` is server-authoritative for the single active session id.
- `POST /session/clear` and chat `/clear` share the same archive/reset service.
- PM accepted dropping the earlier 7-day automatic rollover requirement for V1;
  the implemented rollover trigger is context pressure plus explicit clear.
- Desktop exposes only `清空当前对话`, preserving team/persona/API settings.
- Release metadata reports
  `single_active_session_sqlite_kv_with_local_archive`.

QA evidence:

- `.venv/bin/python -m unittest discover -s tests` passed.
- `cd desktop && npm run typecheck && npm run build` passed.
- `cd mobile && npm run typecheck` passed.
- `.venv/bin/python tools/p11_session_kv_e2e_smoke.py --port 8765` passed.
- LaunchPad runtime validate passed with active stage `qa`.

## 2026-05-04 (continued): 第三方案修正——共享数据源，薄 wrapper

### 红队发现

独立 Agent 方案的方向正确，但以下假设不成立：
1. 工具实现不可复用（_build_native_agent 闭包）
2. retrieve_d_layer_demo 不存在
3. Constitution §5 "V1 不引用 D 层" 与 L3 冲突
4. pydantic-ai 无 tool_names 属性

### 修正

- 不共享工具实现 → 共享数据源（BattleDexRepository 独立可导入）
- Harness 写薄的工具 wrapper 直接调 Repository
- L3 使用修改版 constitution（允许 D 层）
- 输出自由文本，不强制 AdvisorResponse 结构
- 工作量重估：~350 行新代码，全部在 tools/ 下，生产代码零改动

### 相关文件

- `artifacts/p10h_prebattle_ablation/runtime_agent_experiment_plan_2026_05_04.md`（v3 修正）

## 2026-05-04/05: Runtime Agent 实验执行完成 & 转入 Meta Graph 建设

### 执行

Harness 实现完成，三个文件 ~300 行：
- `tools/p10h_agent_tools.py` — A/B/D 层工具薄 wrapper，直调 BattleDexRepository
- `tools/p10h_agent_factory.py` — 按 level 创建 pydantic-ai Agent，选择性注册工具
- `tools/p10h_runtime_agent_harness.py` — 主逻辑：加载 case → 创建 Agent → 发送 task → 收集响应

全量实验：3 case × 5 level × 3 repeat = 45 calls。DeepSeek v4 Pro + thinking enabled。
45/45 完成，零报错。2/45 主回答被截断（<500 字符），但 what-if 回答完整。

### 关键发现

1. **工具门控工作正常。** L0 零工具调用，L1 调 A 层，L2 调 A+B，L3 调 A+B+D。物理隔离有效。

2. **A 层消除基础事实编造。** L0 把棋齐垒说成岩系/寒音蛇说成冰系。L1+ 类型、种族值、技能名全部来自工具返回，不再编造。这是最大、最稳定的单层 delta。

3. **B 层增加机制知识。** L2 引用了星陨印记循环、陨落特性（回合结束触发次数-1）、扩散侵蚀等 wiki 内容。L1 拿得到种族值但拿不到机制解释。

4. **D 层增加推理结构。** L3 输出比 L2 更倾向"先画体系图、再做分支推演、再标注不确定性"。D 层方法迁移可见——L3-exact 显式引用 D 层，L3-transfer 自然应用方法论。

5. **Constitution 反例污染。** Constitution §3 的反例写了"裘卡首发需要疫病吐息"。所有 level 的 system prompt 都包含此反例 → L0 不干净，L1+ 的裘卡分析可能被反例暗示而非纯工具驱动。

6. **速度瓶颈暴露。** 单 call 耗时 180-760s，主要来自 12 物种逐个调工具 + thinking per round。生产部署前需要批量工具和预加载优化。

### 决策：转入 Meta Graph 建设

实验诊断任务完成。不再深入 judge 评分——真正瓶颈不是"各层贡献了多少"，而是"没有精灵常见配置数据，Agent 只能从类型和种族值做表面分析"。

H-Graph（Human-seeded Graph）建设开始：
- 从社区配置讲解/评级视频提取 species_set 配置卡
- 首批 5-8 个当前 meta 核心精灵
- PM 扒视频 → Clé 提取结构化配置 → 写入 graph

### Harness 状态

- `tools/p10h_agent_tools.py` / `p10h_agent_factory.py` / `p10h_runtime_agent_harness.py` — 保留，不维护
- 诊断工具，Layer 1 完成即为使命完成
- 后续 Layer 2（增量建设）直接用 Runtime Agent，不需要 harness

### 未修

- Constitution §3 反例用了 Case A 中的物种（裘卡）和技能（疫病吐息）。如需重跑实验，应先替换为不在任何 case 中的物种。
- 2 个截断 call 未重跑。不影响方向性结论。

### 相关文件

- `tools/p10h_agent_tools.py` — 新建
- `tools/p10h_agent_factory.py` — 新建
- `tools/p10h_runtime_agent_harness.py` — 新建
- `artifacts/p10h_prebattle_ablation/outputs/` — 45 个输出 JSON
- `artifacts/p10h_prebattle_ablation/blind_review/blind_review_packet.json` — 45 条目盲评包
- `artifacts/p10h_prebattle_ablation/all_outputs.txt` — 全部输出汇总
- `specs/v2_battle_meta_graph_spec.md` — 下一步
