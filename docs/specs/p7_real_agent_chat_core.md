# P7 Real Agent Chat Core

Date: 2026-04-27

Implementation contract:

- `specs/p7_real_agent_chat_contract.yaml`

## Purpose

Make Roco V1 a real Agent Chat product instead of a chat-shaped UI backed
primarily by deterministic intent rules.

The user-facing contract is:

1. user enters a natural-language prompt
2. Agent interprets intent
3. Agent decides whether it needs A-layer battle data, B-layer reasoning
   doctrine, current session context, or clarifying questions
4. Agent calls only approved tools/data paths
5. persona layer shapes the final answer without changing facts

## Current Gap

The mobile app already calls the backend `/chat` endpoint and preserves
`session_id` plus public `persona_selector`.

The backend currently routes through a rule-first `ToolRouter`. When the prompt
does not match bounded command/team/species intents, the response falls back to
a fixed MVP message rather than letting an LLM planner understand the query.

This is not sufficient for V1 product feel. The UI can look correct while the
core experience still feels fake because arbitrary prompts are not handled as
Agent work.

## Product Position

P7 is the next core product capability after the P5 RN UI closeout.

P8 Team Builder remains important, but it is downstream of P7. Team Builder
improves input quality and reduces repeated manual team entry; it does not
replace the need for a real Agent Chat loop.

## Required Behavior

### Natural Prompt Handling

For any non-empty user prompt, the Agent should do one of:

- answer using available context and approved tools
- ask a clarifying question when required information is missing
- refuse safely when the request is outside product/safety scope
- explain that a capability is not available yet without pretending it ran

It should not default to the current "MVP only supports..." response merely
because the wording does not match deterministic router patterns.

### LLM Planner / Router

Introduce an LLM-backed planner/router for request-scoped native runtime.

The planner decides:

- user intent
- whether existing session team context is sufficient
- whether A-layer data lookup is needed
- whether B-layer doctrine/reasoning guidance is needed
- whether deterministic team structure analysis should be invoked
- whether the user should be asked for missing team/species details

The existing deterministic router remains as:

- offline fallback
- safety fallback
- command compatibility path
- regression baseline

It should not be the primary behavior when the user has configured a valid
native model service.

The implementation-level contract is:

- valid native runtime is Agent-first for non-empty natural-language prompts
- deterministic router may still classify known team/species paths as route
  hints for approved tool use, but it is not the primary entry gate
- explicit local slash control commands (`/help`, `/clear`, `/show-team`,
  `/set-team`, `/exit`) may bypass native runtime for compatibility
- if a prompt is natural-language help/product guidance or otherwise
  `unsupported`, it enters the native chat path instead of command-help text or
  the old MVP fallback
- `general_chat` returns `analysis_type=chat_response` at the app/API layer
- the old "当前 MVP 只支持..." fallback remains allowed only for deterministic
  unsupported prompts or degraded fallback paths

### Tool/Data Boundaries

The LLM must not directly invent game facts. It may only ground factual claims
through approved sources:

- A-layer battle database/repository
- deterministic battle/team structure tools
- approved B-layer doctrine or reasoning contracts
- current session state
- future P8 structured team context

Tool traces and raw payloads remain internal. Presentation exposes only
public-safe summaries, warnings, evidence, and follow-up prompts.

### Persona Boundary

P7 must preserve the existing persona rule:

- facts are locked before persona rendering
- `You know who` uses runtime id `you_know_who`
- persona may shape tone and structure
- persona must not create facts, evidence, or unsupported claims

## Backend Work

Likely implementation surfaces:

- `advisor/runtime.py`
- `agent_core/orchestrator.py`
- `agent_core/contracts.py`
- `agent_core/synthesis.py`
- `api/services/advisor_service.py`
- tests under `tests/test_api.py`, `tests/test_agent_core_orchestrator.py`,
  and `tests/test_advisor.py`

Expected additions:

- planner result contract
- approved tool-call decision contract
- native planner path for arbitrary prompts
- deterministic fallback path
- explicit clarifying-question response type or presentation convention
- no-secret logging/redaction coverage

## Mobile Work

Mobile already sends `/chat`; P7 should require minimal UI work.

Mobile must continue to:

- send `message`
- send `session_id`
- send current public `persona_selector`
- inject request-scoped runtime headers only from secure settings
- render public presentation/persona output

If the Agent asks a clarifying question, it should render as a normal Agent
message, not a separate tool panel.

## Acceptance Criteria

- With valid model settings, a natural prompt that does not match the old rule
  router is handled by the Agent instead of fixed MVP fallback.
- Agent can ask for missing team details when the user asks for team analysis
  without providing enough context.
- Agent can use A-layer species lookup when a prompt names a known species.
- Agent can use deterministic team structure tools when enough team context is
  available.
- Agent output preserves public-safe presentation and persona boundaries.
- Provider key and runtime headers are never echoed in responses, logs, or
  presentation fields.
- Deterministic mode still works as a bounded offline fallback.
- Backend regression tests and mobile typecheck pass.

## Non-Goals

- no P8 Team Builder UI
- no graphical dex or calculator
- no direct mobile SQLite access
- no durable multi-session memory beyond existing session mechanics
- no web browsing or live meta lookup
- no raw tool-trace rendering in mobile UI

## Relationship To P8

P8 Team Builder will attach structured team context to `/chat`.

P7 should be designed so P8 can plug in as an additional structured context
source, not as a separate product route.
