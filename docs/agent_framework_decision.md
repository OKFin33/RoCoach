# Agent Framework Decision

## Purpose

Record the current decision on whether the Roco battle-analysis system should adopt a full agent runtime, a lightweight agent SDK, or a custom thin harness.

This document exists to prevent repeated framework re-litigation without explicit trigger conditions.

## Current Decision

As of `2026-04-14`, the project should **not** adopt a heavyweight agent runtime such as DeerFlow.

The approved near-term architecture is:

1. use an `Agent-led` product surface
2. implement that surface with `PydanticAI`
3. keep deterministic Engine tools for structural calculations and hard facts
4. allow constrained LLM semantic judgement where the project does not yet have complete structured features
5. adopt a `hybrid local RAG` design instead of open-ended retrieval
6. keep business contracts independent from any specific runtime
7. reassess heavier framework adoption once runtime complexity, not product semantics, becomes the dominant problem

Runtime status note:

- `PydanticAI` is approved as the near-term advisor runtime
- `PydanticAI` is **partially instantiated in code**
- current repo state contains:
  - approved architecture and tool contracts
  - validated data / importer / SQLite substrate
  - an optional `PydanticAI` report generator under `reporting/`
  - a non-conversational Phase 1.5 report CLI
  - no production multi-turn advisor agent, battle-dex-aware retrieval path, or conversational Agent CLI yet

## Why DeerFlow Is Not the Current Fit

DeerFlow is positioned as a long-horizon super-agent runtime with:

- sandboxed execution
- long- and short-term memory
- planning and sub-tasking
- tools and skills
- subagents
- persistent execution environment

Those capabilities are valuable for:

- long-running research tasks
- automated ingestion pipelines
- autonomous multi-step execution
- multi-agent collaboration

They are not required for the current product milestone, which is now:

- Agent-led Phase 1 team analysis
- controlled knowledge retrieval
- deterministic structure tools
- constrained semantic judgement over approved battle context
- lightweight multi-turn advisory interaction

Adopting DeerFlow now would likely shift effort toward runtime integration, state plumbing, and framework-specific orchestration before the product semantics are stable.

## What Counts As "Paying Infrastructure Tax"

The project is paying infrastructure tax when implementation time is dominated by:

- learning framework-specific lifecycle and state models
- adapting business logic to framework primitives
- debugging runtime orchestration instead of product logic
- wiring provider configuration, sessions, memory, tracing, and execution recovery before the report layer is validated

If those costs exceed the saved implementation work, the framework is a net loss at the current stage.

## Lightweight Framework Candidates

### PydanticAI

Current assessment:

- good fit for typed Python applications
- provider-agnostic
- strong structured output and validation story
- good fit for FastAPI-based services
- supports tools, multi-turn state, graphs, evals, and durable execution

Why it is attractive here:

- aligns with Python + FastAPI stack
- encourages explicit contracts instead of prompt soup
- can support a gradual path from report generation to a real advisory agent
- fits the new split where some analysis remains tool-backed and some remains schema-constrained LLM work

Current judgement:

- best candidate if the project wants a lightweight framework soon
- still should be introduced only after the report-layer contracts are fixed

### OpenAI Agents SDK

Current assessment:

- intentionally lightweight
- small set of primitives: agents, tools, handoffs, guardrails, sessions
- built-in tracing

Why it is attractive here:

- quick to use
- good default loop for tool calling
- useful if the project standardizes on OpenAI models

Current judgement:

- good candidate if OpenAI lock-in is acceptable
- weaker strategic fit than PydanticAI because the project should remain provider-flexible

### LangGraph

Current assessment:

- lower-level orchestration framework
- explicitly designed for reliable complex task handling
- strong when workflows become graph-shaped and stateful

Current judgement:

- too heavy for the current milestone
- appropriate later if the advisor becomes a genuinely complex multi-step runtime

### Agno

Current assessment:

- broader agent framework with SDK plus AgentOS / deployment posture
- more production-facing than the project currently needs

Current judgement:

- not the best first choice for this project stage
- viable only if the roadmap expands quickly toward larger agent infrastructure needs

## Recommended Near-Term Path

The near-term target is a **thin battle advisor**, not a full autonomous runtime.

The approved user-facing target is now:

- **conversational Agent CLI**

That advisor should use `PydanticAI` as the orchestration layer for:

- typed outputs
- tool calling
- short multi-turn state
- validation-oriented generation
- controlled semantic analysis passes

That advisor should use `hybrid local RAG` for knowledge access:

- SQL / typed retrieval for structured battle-dex facts
- lightweight snippet retrieval for approved mechanics and methodology docs
- representative tactical case retrieval for role and archetype priors
- no open-ended web retrieval inside the live analysis loop

That harness should contain:

- `KnowledgeRetriever`
- `ContextBuilder`
- `BattleDexRepository`
- `CasebankRetriever`
- `StructureAnalyzerTool`
- `SemanticAnalysisTool`
- `ReportGenerator`
- `ReportValidator`
- `ConversationStateStore` interface
- `TraceRecorder` interface

The implementation should remain simple:

- no long-term memory
- no autonomous subagents
- no background task planner
- no durable workflow engine
- no open-ended web reasoning in the analysis loop

What blocks immediate high-confidence semantic role judgement:

- move / ability / mechanics semantics are only partially converted into stable derived features
- role taxonomy exists, but role-label extraction rules and evaluation examples are not yet operationalized
- mechanics such as `印记系统` still live mainly in supplement text, not deterministic feature tables
- no acceptance benchmark yet defines what counts as an acceptable `主C / 副C / 联防 / 辅助` judgement
- no shipped confidence / refusal policy yet limits when semantic output is safe to show to users
- no representative tactical casebank yet anchors pattern induction for team-conditional role understanding
- no formal set/configuration layer yet distinguishes baseline species understanding from actual equipped role

This does **not** block building the Agent now.

It means the first Agent must expose semantic judgement as:

- evidence-backed
- uncertainty-bearing
- overrideable by later deterministic tooling
- clearly weaker than hard structure analysis in trust level

It also means the first Agent should treat many species-level judgements as:

- `role hypotheses`
- `case-supported analogies`
- `team-conditional interpretations`

rather than canonical one-line truth labels.

## Upgrade Triggers

Reassess adoption of a more complete framework when at least `3` of the following become true:

1. multi-turn state management becomes non-trivial
2. tool orchestration spans several dependent steps per request
3. the system needs async or recoverable long-running tasks
4. observability and replay become operational requirements
5. provider switching and adapter maintenance become painful
6. custom harness glue code grows beyond a small, stable orchestration layer

## Immediate Action

Before expanding the advisor, the project should first keep these documents aligned:

- `docs/battle_analysis_architecture.md`
- `specs/report_layer.md`
- `specs/report_schema.yaml`
- `specs/report_confidence_policy.md`
- `specs/agent_tool_contracts.yaml`

Implementation should begin only from these constrained contracts, not from runtime-first experimentation.

Immediate architecture note:

- the current SQLite battle dex should be treated as a `RAG-ready substrate`, not a finished RAG system
- a finished near-term RAG layer for this project should remain lightweight and local-first
- the next milestone is not “build a giant retrieval platform”; it is “make battle-dex facts, approved docs, and tactical cases queryable from the conversational advisor”

## Current Recommendation

For the next implementation phase, adopt:

1. `PydanticAI`

and use it for:

- Agent-led team analysis entry
- deterministic structure tool orchestration
- constrained semantic judgement on species / role / tactic questions when hard structured scoring is incomplete
- conversational CLI interaction as the first delivery surface

Keep as fallback candidates only:

1. `OpenAI Agents SDK`

Do not introduce:

- DeerFlow
- LangGraph
- any long-horizon multi-agent runtime

until the project has proven it needs runtime complexity rather than just stronger report-layer design.
