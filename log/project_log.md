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

- User: PM / product owner
- Codex: implementation owner, architecture and engineering execution

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
