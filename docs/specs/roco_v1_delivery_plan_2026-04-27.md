# Roco V1 Delivery Plan

Date: 2026-04-27

## Priority Order

The next delivery order is:

1. P4g Runtime Release Readiness Summary
2. P5 Mobile UI Prototype Migration and Visual Parity Rework
3. P6 Residual Runtime Security QA
4. P7 Real Agent Chat Core
5. P8 Team Builder Structured Context MVP

This order is deliberate. The runtime path has enough software-level coverage to
stop blocking product shape work, but it still needs a concise readiness verdict
before the project pivots back to UI. UI migration should then create the user
experience that makes the product feel real. Additional security QA remains a
release gate, not the next product-shaping blocker.

Update, 2026-04-27:

- P7 is now `Real Agent Chat Core`.
- P8 is now `Team Builder Structured Context MVP`.
- P8 was previously drafted as P7, but PM clarified that real Agent chat is the
  core feature and must precede team-builder work.
- P6 remains a release/security gate. P7/P8 are product-capability tracks.

## P4g Runtime Release Readiness Summary

Goal: consolidate P4a-P4f into one PM-readable release verdict.

Inputs:

- `specs/llm_runtime_security_contract.md`
- `.launchpad/accepted_truth/p4a_llm_runtime_security_contract_completed.yaml`
- `.launchpad/accepted_truth/p4b_backend_request_scoped_native_runtime_completed.yaml`
- `.launchpad/accepted_truth/p4c_mobile_secure_settings_storage_completed.yaml`
- `.launchpad/accepted_truth/p4d_e2e_agent_tool_loop_qa_completed.yaml`
- `.launchpad/accepted_truth/p4f_securestore_platform_runtime_resolution_completed.yaml`

Required output:

- Runtime path readiness verdict.
- What is accepted: backend request-scoped runtime, mobile secure settings,
  fake-native tool-loop QA, iOS Simulator SecureStore save/reload/clear/delete.
- What remains residual manual QA: Android emulator/physical Android,
  physical iOS Keychain, live device traffic/log inspection, moderate Expo
  transitive advisories.
- Recommendation: proceed to UI migration while carrying residual security QA as
  a later release gate.

## P5 Mobile UI Prototype Migration

Goal: migrate the accepted Figma Make visual/interaction direction into the real
Expo mobile app.

Inputs:

- `specs/roco_v1_ui_prototype_handoff_2026-04-26.md`
- `specs/roco_v1_chat_ui_direction_brief.md`
- `figma/Minimal Chat Interface Design`

P5 should preserve the V1 product model:

- single Agent chat surface
- paper-shell chat reading surface
- prompt composer
- right-edge settings handle/drawer
- Agent avatar long-press persona wheel
- message action menu
- generic long-analysis card/container

P5 must not:

- expose Team, Species, Calculator, Dex, or tools as visible product tabs
- implement persona creation
- use internal encoded persona selectors
- assume a final typed `ui_artifacts` backend contract
- render production UI directly from raw `tool_results.payload`
- imply local model execution on mobile

### P5b QA Result

P5b QA blocked P5 acceptance. The P5a implementation preserved important
functional boundaries but did not match the accepted prototype closely enough.
The blocker is not backend/API behavior; it is visual and interaction parity.

Failed parity areas:

- paper shell assets were not ported into mobile
- right-edge settings handle and drawer were not implemented as a connected rail
- persona selection remained a bottom scaffold instead of an avatar-anchored radial wheel
- Chinese copy and message action labels did not match the prototype
- spacing, hierarchy, empty state, and composer integration diverged materially

### P5c Mobile UI Visual Parity Rework

Goal: use `figma/Minimal Chat Interface Design` as the UI truth source and port
its accepted shell into Expo React Native while retaining the real mobile
runtime/API wiring.

P5c must port:

- `roco-paper-shell.png` and `roco-paper-outline.png`
- paper reading surface and composer integration
- connected settings drawer rail
- avatar-anchored radial persona wheel
- Chinese labels and message actions
- generic long-analysis card visual treatment

P5c must preserve:

- real `apiClient.chat`
- session continuity as internal state
- SecureStore provider-key handling
- request-scoped native runtime headers
- public `persona_selector` payloads only
- no visible Team/Species/Calculator/Dex/Evidence/debug/tool navigation

## P6 Residual Runtime Security QA

Goal: close or consciously accept the residual runtime security risks after UI
migration has made the real product surface testable.

Candidate checks:

- Android emulator SecureStore save/reload/clear/delete
- physical iOS Keychain behavior
- physical Android Keystore behavior
- live mobile-to-Product-API traffic capture
- log inspection for provider-key leakage
- dependency policy for remaining moderate Expo transitive advisories

P6 should not block P5 unless P4g discovers a new software-level blocker.

## P7 Real Agent Chat Core

Goal: make `/chat` behave like a real Agent loop for natural-language prompts,
not just a rule-router backed command shell.

Inputs:

- `specs/p7_real_agent_chat_core.md`
- accepted P4 request-scoped native runtime work
- current `/chat` mobile/backend integration
- current persona and presentation contracts

P7 should:

- introduce an LLM-backed planner/router for native runtime
- keep deterministic routing as offline/safety fallback
- decide when to call A-layer data, B-layer doctrine, deterministic team tools,
  or ask clarifying questions
- preserve public-safe persona rendering and fact-lock boundaries
- keep provider keys request-scoped and redacted

P7 must not:

- expose tools as product navigation
- render raw tool traces in mobile UI
- invent game facts without approved data/tool grounding
- implement Team Builder UI

## P8 Team Builder Structured Context MVP

Goal: reduce repeated manual team entry by letting the user configure one
structured team context from A-layer database lookups, then attach it to Chat.

Inputs:

- `specs/p8_team_builder_structured_context_mvp.md`
- P7 Real Agent Chat Core
- existing species search/profile endpoints

P8 should:

- use Settings -> `队伍设置` as the reserved entry
- keep Chat as the only analysis output surface
- attach structured team context to `/chat`
- mark unknown moves/tuning as user-supplied or unresolved

P8 must not:

- revive legacy `TeamEditorScreen`
- create a standalone Team Analyze/Dex/Calculator product page
- let mobile read SQLite directly
- block P7 Agent Chat work

## Current Product Rule

Roco V1 is not a multi-tool application. It is one Agent chat product. The user
enters prompts; Agent uses internal capabilities; persona presentation shapes
the answer. UI migration must make that product legible, not expose backend
tools as product modules.
