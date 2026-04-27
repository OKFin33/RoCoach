# Current Task Allocation

## Purpose

This document is the current execution board for the Roco advisor project.

It assigns all near-term work to the correct thread type:

- main thread
- main development thread
- test / audit thread
- crawler / database thread

It exists to prevent scope drift and thread misuse.

It also records the allowed use of GUI automation as a forwarding courier.

## Current Status

As of `2026-04-20`:

- `Advisor CLI MVP complete`
- conversational Advisor CLI exists
- backend policy is `auto`
- `auto` is native-first, not native-only
- `pydantic_ai_native` has bounded failure / timeout behavior
- deterministic fallback exists for supported flows
- first dogfood audit findings are fixed
- runtime hygiene ResourceWarning cleanup is complete
- historical full suite after earlier dogfood hardening: `Ran 57 tests`, `OK`
- Retrieval Phase A eval completed with fixes and is acceptable for Advisor MVP
  dogfood
- native failure-path audit completed
- native status enum alignment completed
- native default readiness is ready for main-thread decision
- second dogfood audit completed with non-blocking findings
- MVP prompt/runtime tuning completed
- current full suite reported by implementation thread after tuning:
  `Ran 68 tests`, `OK`
- final MVP readiness check returned `PASS_WITH_FINDINGS`
- final MVP readiness recommendation returned `ready_to_declare_mvp_complete`
- main thread accepted the non-blocking P3 native-provider validation finding
- P0a App-Facing Contract Normalization is complete
- P0b Minimal Agent Core Extraction is complete
- P0c FastAPI Backend is complete
- P0c API Audit returned `PASS`
- P0d/mobile readiness returned `ready_for_next_P0_track`
- P0d Persona V1 + IP Guard implementation completed
- current full suite reported after P0d implementation: `Ran 93 tests`, `OK`
- P0d Persona/IP Guard Audit returned `PASS`
- mobile readiness returned `ready_for_P0e_mobile_scaffold`
- P0e Mobile MVP Scaffold implementation completed
- P0e Mobile MVP Scaffold Audit returned `PASS`
- P0f readiness returned `ready_for_P0f_hardening`
- P0f Public-Release Hardening implementation completed
- current full suite reported after P0f implementation: `Ran 96 tests`, `OK`
- P0f Public-Release Hardening Audit returned `PASS`
- post-P0 readiness returned `ready_for_post_P0_planning`
- P0 scope is complete
- product-direction update: default UX must be coach-style conversation, not
  raw structured analytical payload
- post-P0 SSD update completed for reasoning/synthesis, conversational
  presentation, and pluggable persona direction
- persona-creation pipeline SSD completed:
  - source adapter
  - artifact ingestion
  - managed creation pipeline
- P1 locked execution plan written to prevent stage drift
- GUI courier protocol added for thread forwarding through `Computer Use`
- Enzo integration review completed
- execution-state scaffold completed:
  - `specs/p1_execution_state.yaml`
  - `specs/task_packet_template.md`
- clean PM-console thread handoff prepared:
  - `specs/pm_console_thread_handoff.md`
- `P1a synthesis implementation spec` drafted and accepted:
  - `specs/p1a_synthesis_implementation_spec.md`
- Gate 2 is open
- next unlocked step is `P1a implementation`
- bounded implementation packet prepared for `主开发线程`:
  - `specs/p1a_implementation_task_packet.md`

Current retrieval reality:

- SQL-first structured retrieval exists through `BattleDexRepository`
- doc retrieval exists as curated / keyword-bounded snippets in
  `advisor/retrieval.py`
- no embeddings
- no case retrieval
- no web retrieval

## Active Priorities

### Priority 1: Post-P0 Planning

Owner:

- main thread

Goal:

- lock the post-P0 direction around:
  - LLM as the core analysis/synthesis unit
  - deterministic / SQL / approved docs as truth sources
  - coach-style conversation as the default product surface
- prioritize:
  - `P1a Reasoning / Synthesis Layer`
  - `P1b Conversational Presentation Layer`
  - `P1c Pluggable Persona Contract`
  - `P1d Persona Source Adapter Contract`
  - `P1e Persona Artifact Ingestion`
  - `P1f Managed Persona Creation Pipeline`
  ahead of persistence and deeper advisory intelligence tracks

Current state:

- P0c implementation completed
- P0c API audit returned `PASS`
- P0d implementation completed
- P0d audit returned `PASS`
- mobile readiness is `ready_for_P0e_mobile_scaffold`
- P0e implementation completed
- P0e audit returned `PASS`
- P0f readiness is `ready_for_P0f_hardening`
- P0f implementation completed
- implementation thread reported full suite: `Ran 96 tests`, `OK`
- P0f audit returned `PASS`
- post-P0 readiness is `ready_for_post_P0_planning`
- new product constraint:
  - structured output remains internal protocol / inspectable detail
  - default user-facing output should feel like chatting with a coach
  - LLM should be the core analysis unit, but not the source-of-truth unit
- SSD baseline for that direction is now written:
  - `specs/p1_locked_execution_plan.md`
  - `specs/p1_architecture_refactor_plan.md`
  - `specs/persona_doctrine_contract.yaml`
  - `specs/persona_source_adapter_contract.yaml`
  - `specs/persona_artifact_ingestion_contract.yaml`
  - `specs/managed_persona_creation_pipeline_spec.md`
  - `specs/p1a_reasoning_synthesis_layer.md`
  - `specs/reasoning_synthesis_contract.yaml`
  - `specs/presentation_response_contract.yaml`
  - `specs/p1b_conversational_presentation_layer.md`
  - `specs/p1c_pluggable_persona_contract.md`
- execution control baseline is now written:
  - `specs/p1_execution_state.yaml`
  - `specs/task_packet_template.md`
  - `specs/pm_console_thread_handoff.md`
- operational forwarding rule:
  - main thread still chooses the next task and target thread
  - GUI automation may only forward approved packets
  - default forwarding whitelist:
    - `主开发线程`
    - `QA-1`
    - `女娲线程`
- `specs/enzo_integration_review.md` is complete
- `specs/p1a_synthesis_implementation_spec.md` is accepted
- integration review verdict:
  - accept Enzo as an internal doctrine sample
  - use it for internal pattern extraction only
  - do not treat it as a public-safe or default runtime persona
- Gate 2 is open
- next unlocked stage:
  - `P1a implementation`

Do not:

- reopen any completed P0 track without a concrete regression
- expand scope without a new bounded spec
- treat raw `AgentResponse` fields as the final default user-facing surface
- treat raw deterministic outputs as final user-facing analysis
- let LLM invent facts outside grounded Engine / SQL / approved-doc boundaries
- let persona bypass facts/evidence/confidence/refusals
- couple persona runtime directly to a single upstream creation tool
- skip ingestion/review because a persona was system-generated
- break the locked P1 execution sequence without explicit main-thread unlock
- let GUI automation choose tasks or target threads on its own

### Priority 2: Regression protection

Owner:

- test / audit thread

Goal:

- keep the completed P0 baseline stable when post-P0 work starts
- run targeted regression checks for any new bounded track

### Priority 3: Paused non-priority work

Owner:

- crawler / database thread or future implementation threads, only when
  explicitly reopened

Goal:

- remain paused until main-thread product sequencing reopens them

The main thread must not personally perform low-level runtime/test cleanup
unless all worker routes are blocked.

## GUI Courier Rule

When `Computer Use` is used in this project, it is a courier only.

It may:

- open a whitelisted thread
- paste a main-thread-approved packet
- send the packet

It may not:

- infer the next unlocked stage
- reroute work to another thread
- shorten or rewrite the packet
- decide whether a returned result passes review

## Completed Work

### Native failure-path audit / enum alignment

Status:

- completed

Result:

- QA-1 audit: `PASS_WITH_FINDINGS`
- enum alignment fixed by main development thread
- `ToolStatus` now matches `advisor_response_contract.yaml`:
  - `ok`
  - `degraded`
  - `refused`
  - `failed`
- no serialized `unavailable` status remains in advisor responses
- native default readiness is `ready_for_main_thread_decision`

### Retrieval Phase A eval / hardening

Status:

- completed

Result:

- `PASS_WITH_FIXES`
- Phase A retrieval acceptable for Advisor MVP dogfood
- no embeddings / FTS / case retrieval added

### Second dogfood audit

Status:

- completed

Result:

- `PASS_WITH_FINDINGS`
- Advisor usefulness and evidence quality are good enough for MVP dogfood
- accepted findings:
  - native-backed `auto` can create repeated timeout stalls before fallback
  - unsupported future/live-meta refusal is safe but generic

### MVP prompt/runtime tuning

Status:

- completed

Result:

- implemented session-local native health gate for `--backend auto`
- repeated supported messages in one CLI process skip native after native is
  marked unhealthy
- explicit `--backend pydantic_ai_native` remains native-only and bounded
- future/live-meta refusal now explicitly mentions no web/live official balance
  feed and no future buff/nerf or live meta prediction
- implementation thread reported:
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 68 tests`, `OK`

### Final MVP readiness dogfood/check

Status:

- completed

Result:

- verdict: `PASS_WITH_FINDINGS`
- MVP readiness recommendation: `ready_to_declare_mvp_complete`
- full suite:
  - `.venv/bin/python -m unittest discover -s tests`
  - `Ran 68 tests in 3.160s`, `OK`
- accepted non-blocking finding:
  - local native provider was not validated as successful native output
  - sampled local native call timed out under `--native-timeout 2`
  - approved `auto` fallback behavior worked
- main-thread decision:
  - `Advisor CLI MVP complete`

Record:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/advisor_mvp_completion_record.md`

### P0a App-Facing Contract Normalization

Status:

- implementation completed
- architecture audit completed
- boundary refactor completed
- fully complete

Result reported by main development thread:

- created `agent_core/__init__.py`
- created `agent_core/contracts.py`
- added app/API-facing models:
  - `AgentResponse`
  - `AgentToolResult`
  - `EvidenceItem`
  - `ConfidenceNote`
  - `FollowupOption`
  - `PersonaEnvelope`
- made `AgentToolResult.evidence_refs` required
- initially added adapter:
  - `agent_core.contracts.agent_response_from_advisor`
  - `AgentResponse.from_advisor_response`
- this initial adapter location was superseded by the completed P0a boundary
  refactor below
- added tests in `tests/test_agent_core_contracts.py`
- validation:
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 74 tests`, `OK`

Main-thread review note:

- initial boundary coupling was audited and fixed.
- current pure contract module no longer imports `advisor.contracts`.

### P0a Contract Audit

Status:

- completed

Result:

- verdict: `PASS_WITH_FINDINGS`
- P0b readiness: `conditional_not_ready_until_boundary_refactor`
- contract judgement: `PASS`
- evidence judgement: `PASS_WITH_CAVEAT`
- adapter judgement: `PASS`
- boundary judgement: `refactor_before_P0b`

Blocking finding:

- `agent_core/contracts.py` imports `advisor.contracts`
- Advisor-specific adapter logic lives in the same module as pure
  product-facing contracts

Required next action:

- split pure app-facing models from Advisor adapter code before P0b.

### P0a Boundary Refactor

Status:

- completed

Result reported by main development thread:

- `agent_core/contracts.py` now contains only pure app/API-facing models/enums
- Advisor-specific adapter logic moved to:
  - `agent_core/adapters/advisor.py`
- `agent_core/__init__.py` exports only pure contract models/enums
- `AgentResponse.from_advisor_response` removed from pure model
- adapter usage is explicitly:
  - `agent_core.adapters.advisor.agent_response_from_advisor`
- import boundary proof:
  - importing `agent_core.contracts` does not import `advisor.contracts`
  - importing `agent_core.adapters.advisor` imports `advisor.contracts`
- validation:
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 77 tests`, `OK`

Main-thread decision:

- P0a is fully complete.
- P0b is ready for scheduling.

### P0b Minimal Agent Core Extraction

Status:

- implementation completed
- awaiting architecture audit before P0c/P0d scheduling

Result reported by main development thread:

- added pure product-side runtime protocol:
  - `agent_core/tools.py`
  - `AgentRuntimeAdapter.handle_message(message: str) -> AgentResponse`
- added minimal orchestrator:
  - `agent_core/orchestrator.py`
  - delegates one user message to runtime adapter
  - applies safety before runtime execution
  - attaches persona metadata after runtime execution
- added minimal safety boundary:
  - `agent_core/safety.py`
  - default `SafetyGuard` allows
  - `SafetyDecision.refuse(...)` can return structured refused `AgentResponse`
    without calling runtime adapter
- added minimal persona boundary:
  - `agent_core/persona.py`
  - only attaches `PersonaEnvelope` metadata
  - forces `facts_locked=true`
  - forces `fact_policy=persona_may_not_alter_facts`
- extended Advisor compatibility adapter:
  - `agent_core/adapters/advisor.py`
  - added `AdvisorRuntimeAdapter`
  - wraps existing `advisor.runtime.AdvisorAgent`
  - converts through `agent_response_from_advisor`
- validation:
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 83 tests`, `OK`

Main-thread review note:

- P0b implementation matches the intended thin-boundary shape.
- Run architecture audit before scheduling P0c FastAPI or P0d Persona.

### P0b Agent Core Architecture Audit

Status:

- completed

Result:

- verdict: `PASS`
- P0c readiness: `ready_for_P0c`
- pure-boundary judgement: `PASS`
- orchestrator judgement: `PASS`
- safety/persona judgement: `PASS`
- adapter judgement: `PASS`
- JSON/contract stability: `PASS`
- findings: none
- validation:
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 83 tests`, `OK`

Main-thread decision:

- P0b is complete.
- P0c FastAPI Backend is ready for scheduling.

### P0c FastAPI Backend

Status:

- implementation completed
- API architecture audit completed
- fully complete

Result reported by main development thread:

- added dependencies:
  - `fastapi>=0.115,<1.0`
  - `uvicorn>=0.34,<1.0`
  - `httpx>=0.27,<1.0`
- added local FastAPI package:
  - `api/__init__.py`
  - `api/contracts.py`
  - `api/dependencies.py`
  - `api/main.py`
  - `api/services/__init__.py`
  - `api/services/advisor_service.py`
- exposed endpoints:
  - `GET /health`
  - `GET /metadata`
  - `POST /chat`
  - `POST /team/analyze`
  - `GET /species/search`
  - `GET /species/{species_id}`
- `/chat` uses `AgentOrchestrator + AdvisorRuntimeAdapter + AdvisorAgent`
  and returns app-facing `AgentResponse`
- `/team/analyze` maps API team slots to existing Advisor team-analysis path
- species endpoints use `BattleDexRepository` through API service layer
- session continuity:
  - optional `session_id`
  - in-memory per-process `AdvisorAgent` / `AgentOrchestrator`
  - no durable persistence
  - no formal `message_history`
- provider/API-key handling:
  - API default backend deterministic
  - request models do not accept provider keys
  - no hosted key management
- validation:
  - `.venv/bin/python -m unittest tests.test_api`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 89 tests`, `OK`

Main-thread review note:

- P0c implementation matches the local/product API scope.
- API audit passed. P0d/mobile readiness is `ready_for_next_P0_track`.
- P0d Persona V1 + IP Guard is the next ordered roadmap item.

### P0c API Audit

Status:

- completed

Result:

- verdict: `PASS`
- P0d/mobile readiness: `ready_for_next_P0_track`
- endpoint contract judgement: `PASS`
- agent-core boundary judgement: `PASS`
- session continuity judgement: `PASS`
- provider/key handling judgement: `PASS`
- error/redaction judgement: `PASS`
- local CORS/rate-limit judgement: `PASS_FOR_P0c_LOCAL`
- findings: none
- validation:
  - `.venv/bin/python -m unittest tests.test_api`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_contracts`: `Ran 9 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`: `Ran 6 tests`, `OK`
  - `.venv/bin/python -m unittest tests.test_advisor`: `Ran 21 tests`, `OK`
  - `.venv/bin/python -m unittest discover -s tests`: `Ran 89 tests`, `OK`

Additional audit check:

- manual TestClient sanity script confirmed required route inventory, invalid
  chat `422`, extra `api_key` field ignored with `200`, and simulated internal
  failure returned bounded `500 {"code":"internal_error","message":"Request failed safely."}`
  without secret/path/traceback leakage.

Main-thread decision:

- P0c is complete.
- Schedule P0d Persona V1 + IP Guard.

## Paused Work

### Main development thread

Status:

- assigned to P0d Persona V1 + IP Guard

Allowed to resume only when:

- main thread assigns the next bounded request
- current assigned request is:
  - `specs/p0d_persona_ip_guard_request.md`

Not allowed now:

- GUI
- casebank
- new RAG platform
- crawler/database changes
- semantic scope expansion

### Crawler / database thread

Status:

- paused

Reason:

- data layer is not the current Advisor MVP blocker
- current battle-dex substrate is sufficient for present dogfood

Allowed to resume only when:

- main thread explicitly opens a data task
- test/dev proves a blocker originates in data artifacts

## Thread Assignment Summary

| Work item | Thread |
|---|---|
| Native failure-path audit | Completed |
| Native status enum alignment | Completed |
| Retrieval Phase A eval | Completed |
| Small retrieval rule hardening | Completed |
| Second dogfood audit | Completed |
| MVP prompt/runtime tuning | Completed |
| Final MVP readiness dogfood/check | Completed |
| MVP completion decision | Completed |
| Post-MVP roadmap alignment | Completed |
| P0a App-Facing Contract Normalization | Implementation completed |
| P0a Contract Audit | Completed |
| P0a Boundary Refactor | Completed |
| P0b Minimal Agent Core Extraction | Implementation completed |
| P0b Agent Core Architecture Audit | Completed |
| P0c FastAPI Backend | Completed |
| P0c API Audit | Completed |
| P0d Persona V1 + IP Guard | Implementation completed |
| P0d Persona/IP Guard Audit | Completed |
| P0e Mobile MVP Scaffold | Implementation completed |
| P0e Mobile MVP Scaffold Audit | Completed |
| P0f Public-Release Hardening | Completed |
| P0f Public-Release Hardening Audit | Completed |
| Post-P0 Planning | Main thread, next |
| P1a Reasoning / Synthesis Layer | Main thread SSD complete; next implementation candidate |
| P1b Conversational Presentation Layer | Main thread SSD complete; queued after P1a |
| P1c Pluggable Persona Contract | Main thread SSD complete; queued after P1b |
| P1d Persona Source Adapter Contract | Main thread SSD complete; implementation later |
| P1e Persona Artifact Ingestion | Main thread SSD complete; implementation later |
| P1f Managed Persona Creation Pipeline | Main thread SSD complete; implementation later |
| GUI | Post-MVP candidate |
| Case retrieval | Deferred |
| Embeddings | Deferred |
| Web-in-loop | Deferred |
| Crawler/database expansion | Paused |
