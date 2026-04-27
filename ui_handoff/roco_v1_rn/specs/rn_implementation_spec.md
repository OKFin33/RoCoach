# Roco V1 Expo RN Implementation Spec

## Purpose

Implement the approved Roco V1 single-Agent mobile chat UI inside `mobile/` using Expo React Native.

This spec is the first implementation target. It replaces Web prototype guessing with RN-native components and explicit contracts.

## Inputs

Use these as source of truth:

1. `ui_handoff/roco_v1_rn/contracts/roco_v1_ui_contract.ts`
2. `ui_handoff/roco_v1_rn/specs/visual_parity.md`
3. `ui_handoff/roco_v1_rn/tokens.json`
4. `ui_handoff/roco_v1_rn/specs/layout.md`
5. `ui_handoff/roco_v1_rn/specs/components.md`
6. `ui_handoff/roco_v1_rn/specs/interactions.md`
7. `ui_handoff/roco_v1_rn/specs/data_mapping.md`

Do not reverse-engineer `figma/Minimal Chat Interface Design` CSS.

## Required Dependencies

Add to `mobile/package.json` through Expo:

```bash
cd mobile
npx expo install react-native-svg expo-clipboard
```

Optional:

```bash
npx expo install expo-linear-gradient
```

If `expo-linear-gradient` is not added, implement user bubbles with flat `tokens.color.userBubbleBottom`.

## Target File Layout

Recommended implementation layout:

```text
mobile/src/roco/
  rocoTheme.ts
  rocoPersona.ts
  rocoPresentation.ts

mobile/src/components/roco/
  PaperSurface.tsx
  AgentAvatar.tsx
  UserAvatar.tsx
  MessageBubble.tsx
  MessageActionMenu.tsx
  PromptComposer.tsx
  AnalysisCard.tsx
  PersonaWheel.tsx
  SettingsDrawer.tsx

mobile/src/screens/ChatScreen.tsx
```

Existing debug/legacy components may remain, but the V1 user-facing route should use the new Roco components.

## P0 Implementation Scope

Must implement:

- single Chat screen with no custom header
- yellow shell and approved bitmap paper shell
- prompt composer inside paper
- user and Agent bubbles
- Agent avatar anchored to spoken bubble
- generic `AnalysisCard`
- right-edge settings drawer with attached handle
- long-press Agent avatar persona wheel
- message long-press action menu
- copy using system clipboard
- rewrite latest user message as local replacement + new `/chat` request
- regenerate shown but disabled if backend support is unavailable
- API key settings copy aligned with SecureStore
- persona UI id -> backend selector mapping

Must not implement:

- visible Team/Species/Calculator/Dex entrances
- local model/local cloud mode language
- direct raw `tool_results.payload` card rendering
- internal encoded persona selector usage
- fake phone status bar or online chip

## Persona Contract

Use UI ids for visual state only:

```ts
type RocoPersonaUiId = "you_know_who" | "ai_assistant" | "add_persona";
```

Send backend selectors:

```ts
you_know_who -> { kind: "built_in", persona_id: "obsidian_tactical_coach" }
ai_assistant -> { kind: "built_in", persona_id: "lattice_support_coach" }
add_persona -> no selector; reserved seam
```

V1 default:

- The UI visually defaults to `You know who`.
- Therefore the initial UI state must set:
  - `active_persona_ui_id = "you_know_who"`
  - `active_persona_selector = { kind: "built_in", persona_id: "obsidian_tactical_coach" }`
- Do not omit `persona_selector` while visually showing the black-cloaked persona unless backend default is explicitly verified to be `obsidian_tactical_coach`.
- A true API-default/unselected state may omit `persona_selector`, but it must not visually present itself as `You know who`.

## Response Rendering Contract

Visible Agent reply priority:

```ts
response.persona?.rendered_answer
  ?? response.presentation?.reply
  ?? response.answer
```

Generic card:

- `presentation.why` -> card summary
- `presentation.visible_warnings` -> warning rows
- public-safe `presentation.detail_sections` -> collapsible/expandable sections
- `presentation.followup_prompts` -> followup chips if enabled

Suppress by default:

- `content_kind: "raw"`
- `content_kind: "tool_trace"`

Only show those in a debug/admin UI or if backend later adds an explicit public-safe/sanitized flag for the section.

Do not hardcode mock strategy rows.

## Rewrite Contract

V1 decision:

- enabled only for latest user message
- inline edit inside the user bubble
- disable composer while editing
- on submit:
  1. locally replace latest user message text
  2. remove later visible Agent messages
  3. send rewritten text to `/chat` with same `session_id`
  4. render returned Agent response

Limit:

- no branch/history UI
- no claim of true server-side node rewrite

## Regenerate Contract

V1 decision:

- show `重新生成` for Agent message actions only if product wants the affordance visible
- grey/disable it when no backend regenerate endpoint exists
- do not fake as successful production behavior

## Settings Contract

Use existing engineering model:

- `mobile/src/runtime/runtimeSettings.ts`
- `expo-secure-store`
- provider key stored under `roco.runtime.provider_key.v1`
- non-secret runtime settings under `roco.runtime.non_secret.v1`

Settings drawer fields should map to existing runtime settings:

- Product API base URL -> `apiBaseUrl`
- Provider key -> `providerKey`
- Provider base URL -> `providerBaseUrl`
- model -> `model`
- runtime mode -> `runtimeMode`, if exposed
- unsafe LAN HTTP dev override -> `allowUnsafeLanHttp`, if exposed
- transport mode -> internal storage only; do not render local/cloud as a visible V1 user setting

UI copy must say local secure storage. It must not say session-local unless product changes persistence.

## Asset Contract

P0 use:

- `assets/paper/paper_shell.png`
- `assets/paper/paper_outline.png` only if implementation wants separate overlay control
- `assets/avatars/agent_you_know_who.svg`
- `assets/avatars/agent_ai_assistant.svg`
- `assets/avatars/persona_add.svg`
- `assets/avatars/user_default.svg`

Do not use `paper_frame.svg` as the P0 implementation source. It remains only as a fallback/reference path because the SVG recreation is lower fidelity than the approved raster paper.

Implementation options:

1. Paper shell: use RN `ImageBackground`/`Image` with `paper_shell.png`.
2. Avatars: configure SVG import for Expo RN, or convert SVG contents into TSX `Svg` components.

Prefer TSX `Svg` components for avatars if the engineering thread wants fewer bundler changes.

Paper shell:

- source size: 915 x 1616
- P0 render mode: `resizeMode="stretch"` inside the paper bounds
- rationale: this bitmap is the accepted high-fidelity paper treatment; SVG/path recreation was rejected for visual quality
- safe content inset scales from source:
  - top: 72
  - right: 52
  - bottom: 58
  - left: 52
- see `visual_parity.md` for scaled inset formulas

## Acceptance Criteria

Implementation is acceptable when:

- `npx tsc --noEmit` passes in `mobile/`
- app runs in Expo on iOS or Android simulator
- chat screen has no custom header
- paper shell uses approved raster asset and fills the app surface without falling back to low-fidelity SVG recreation
- composer is inside paper
- persona wheel opens on long-press avatar and outside tap closes it
- settings drawer handle moves with drawer
- copy uses system clipboard
- rewrite latest user message follows V1 local replacement contract
- regenerate is disabled/greyed unless backend support exists
- API key copy matches SecureStore behavior
- no Team/Species/Calculator/Dex visible entrances
- no UI sends `you_know_who` or `ai_assistant` as backend persona ids
- default visible persona sends `obsidian_tactical_coach` unless backend default is verified to match
- AnalysisCard uses generic public-safe presentation mapping only
