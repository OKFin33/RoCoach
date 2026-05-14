# Roco V1 RN UI File Guide

Date: 2026-04-27

This guide describes the current Expo React Native implementation of the Roco V1 mobile UI. It is for future collaborators who need to continue development without reverse-engineering the Web prototype.

## Source Of Truth

Use these first:

- `ui_handoff/roco_v1_rn/specs/rn_implementation_spec.md`
- `ui_handoff/roco_v1_rn/contracts/roco_v1_ui_contract.ts`
- `ui_handoff/roco_v1_rn/specs/prototype_parity_addendum.md`
- `mobile/ROCO_P8_TEAM_BUILDER_UI_HANDOFF.md`
- `mobile/src/roco/rocoTheme.ts`
- `mobile/src/roco/rocoPersona.ts`
- `mobile/src/roco/rocoPresentation.ts`

Do not inspect or copy Web prototype CSS, Tailwind classes, DOM layout, or browser gesture logic. The Web prototype is only a visual reference when the RN handoff does not answer a visual question.

## Runtime Entry Points

### `mobile/App.tsx`

Top-level app wiring.

- Owns runtime settings loaded from `mobile/src/runtime/runtimeSettings.ts`.
- Owns settings drawer open/close state.
- Owns active persona UI state and backend `persona_selector`.
- Renders the single V1 product route: `ChatScreen`.
- Renders the connected right-edge `SettingsDrawer`.

Important rule: keep V1 as a single Agent chat surface. Do not add Team, Species, Calculator, or Dex product tabs here.

### `mobile/src/screens/ChatScreen.tsx`

Main Roco chat screen.

- Renders `PaperSurface`, bounded `ScrollView`, and `PromptComposer`.
- Sends `/chat` requests through `ProductApiClient`.
- Always sends the current public `persona_selector` unless the selected persona seam is `add_persona`.
- Resolves Agent text with `resolveVisibleReply`.
- Maps backend presentation into `AnalysisCard` with `buildAnalysisCardModel`.
- Implements local message actions: copy, latest-user rewrite, delete, disabled regenerate.
- Opens `PersonaWheel` from Agent avatar long press.
- Opens `MessageActionMenu` from message bubble long press.

Important layout rule: `PromptComposer` is a sibling of the chat `ScrollView` inside `PaperSurface`. Do not move the composer into the `ScrollView`.

## Shared Roco Model Files

### `mobile/src/roco/rocoTheme.ts`

The local production copy/adaptation of the RN UI contract.

Contains:

- UI types: `RocoChatMessage`, `RocoPersonaUiId`, `PersonaSelector`, action menu state, persona wheel state.
- `ROCO_V1_ASSETS`: canonical asset names.
- `ROCO_V1_COPY`: visible copy.
- `ROCO_V1_PARITY`: layout constants for paper, message rows, composer, persona wheel, drawer, action menu, and analysis card.
- Helper functions:
  - `computePaperContentInset`
  - `personaWheelOffsets`
  - `computeMessageActionMenuPosition`
  - `actionsForMessage`

When tuning layout, prefer changing this file first if the value is a shared parity constant. For one-off component-specific fixes, keep the change in the component.

### `mobile/src/roco/rocoPersona.ts`

Persona UI-to-backend mapping.

Current V1 defaults:

- UI default: `you_know_who`
- Public label: `You know who`
- Persona boundary: Enzo-derived distilled persona layer, public-safe outward
  codename only
- Backend selector default: `{ kind: "managed", persona_id: "you_know_who", version: "draft.v1", revision: 1 }`
- `ai_assistant` maps to `{ kind: "built_in", persona_id: "lattice_support_coach" }`
- `add_persona` is a reserved seam and returns `null`

`you_know_who` is intentionally both the UI option id and managed persona id for
the default distilled persona. `obsidian_tactical_coach` is a legacy alias only.
Do not send UI-only ids such as `ai_assistant` or `add_persona` as backend
persona ids. Built-in `you_know_who` remains only a backend fallback when the
managed materialization path is unavailable.

### `mobile/src/roco/rocoPresentation.ts`

Backend response-to-visible UI mapping.

- `resolveVisibleReply(response)` uses:
  1. `response.persona?.rendered_answer`
  2. `response.presentation?.reply`
  3. `response.answer`
- `buildAnalysisCardModel(response)` only keeps public-safe presentation fields.
- Raw/tool-trace sections are filtered out by `PUBLIC_ANALYSIS_SECTION_KINDS`.

Do not render raw `tool_results.payload` directly in the mobile UI.

## Roco Component Files

### `mobile/src/components/roco/PaperSurface.tsx`

Owns the yellow shell and cream paper surface.

- Uses `mobile/assets/paper/paper_shell.png` through `ImageBackground`.
- Uses `mobile/assets/paper/paper_outline.png` as a top overlay so the paper edge and notch stay visually above content.
- Computes safe content insets from `computePaperContentInset`.

Do not replace this with `paper_frame.svg` for P0.

### `mobile/src/components/roco/MessageBubble.tsx`

Owns user and Agent message rows.

- Agent row: avatar first, bubble second.
- User row: bubble first, avatar second.
- Agent analysis card renders below the spoken bubble in the card lane.
- Handles inline latest-user rewrite UI.
- Measures bubble rects for action menu placement.

If changing chat spacing, check both `MessageBubble.tsx` and `ROCO_V1_PARITY.messageRow`.

### `mobile/src/components/roco/AnalysisCard.tsx`

Generic public-safe card for long Agent responses.

- Renders summary, warnings, detail sections, and followup prompts from `RocoAnalysisCardModel`.
- It is not a typed tool artifact renderer.

Future typed cards should be added separately after backend contracts are explicit.

### `mobile/src/components/roco/PromptComposer.tsx`

Bottom input composer inside the paper.

- Placeholder comes from `ROCO_V1_COPY.composerPlaceholder`.
- Send button is circular and disabled when empty or while editing/loading.
- Composer is intentionally outside the chat `ScrollView`.

Keyboard and scroll fixes should preserve this sibling relationship.

### `mobile/src/components/roco/PersonaWheel.tsx`

Avatar-anchored radial persona picker.

- Triggered by long-pressing the Agent avatar.
- Positions options from `personaWheelOffsets`.
- Open animation mirrors the Web prototype: backdrop fade, 86 px anchor halo
  scale-in, and staggered spring medallions from the avatar center.
- Outside tap closes the wheel.
- `add_persona` is pressable but only a reserved seam in V1.

If options are added, update `rocoPersona.ts`, `rocoTheme.ts`, and backend selector contracts together.

### `mobile/src/components/roco/MessageActionMenu.tsx`

Long-press message action menu.

- User latest message: copy, rewrite, delete.
- Older user message: copy, delete.
- Agent message: copy, disabled regenerate, delete.
- Delete uses confirmation state.

Regenerate must stay disabled until a real backend regenerate endpoint exists.

### `mobile/src/components/roco/SettingsDrawer.tsx`

Right-edge connected settings drawer.

- Drawer and handle move together under one animated rail.
- Home page has three product cards:
  - `队伍设置`
  - `API 设置`
  - `人格设置`
- `API 设置` contains the current API base URL, provider key, provider base URL, model, clear/save/reload/test actions.
- Runtime mode, transport mode, local/cloud, native/deterministic are internal and not shown in normal V1 UI.
- Save derives `runtimeMode`:
  - complete provider config -> `native`
  - incomplete provider config -> `deterministic`

Current `队伍设置` page is an authorized reserved settings entry per latest
product direction. It is a future roster/context configuration surface intended
to reduce repeated manual team entry in chat. It may later host a graphical
local-species database picker for team selection, moves, and individual tuning.
It is not a Team Analyze entrance, Team Editor, Species, Calculator, Dex, or
independent analysis workflow. Do not wire it to `TeamEditorScreen`,
`/team/analyze`, or any non-chat product route in V1 unless product scope
explicitly changes again.

### `mobile/src/components/roco/AgentAvatar.tsx`

TSX `react-native-svg` implementation of Agent and persona wheel avatars.

- `you_know_who`
- `ai_assistant`
- `persona_add`
- selection badge

The handoff asset names still exist in the contract, but the RN implementation uses TSX SVG components to avoid bundler complexity.

### `mobile/src/components/roco/UserAvatar.tsx`

TSX `react-native-svg` implementation of the default user avatar.

### `mobile/src/components/roco/RocoIcons.tsx`

Small RN SVG icons used by composer, settings, analysis cards, and menus.

Do not import `lucide-react`; it is Web-only.

## Runtime And API Files Used By UI

### `mobile/src/api/client.ts`

Product API client used by `ChatScreen` and `SettingsDrawer`.

The V1 UI should call Product API endpoints only. It must not call provider APIs directly.

### `mobile/src/api/types.ts`

Backend request/response types consumed by the UI mapping layer.

### `mobile/src/runtime/runtimeSettings.ts`

Runtime settings and SecureStore persistence.

- Provider key secret key: `roco.runtime.provider_key.v1`
- Non-secret settings key: `roco.runtime.non_secret.v1`
- Native headers are only injected when `runtimeMode === "native"`.
- Provider keys are blocked over non-HTTPS Product API URLs except loopback HTTP.

Do not put provider keys into request bodies, logs, chat messages, persona metadata, or presentation output.

## Assets

### `mobile/assets/paper/paper_shell.png`

Approved raster paper shell. Required P0 source.

### `mobile/assets/paper/paper_outline.png`

Approved raster outline overlay. Used to keep paper edges/notch visually above content.

## Removed Legacy UI

The older scaffold components and screens were removed during the UI merge
closeout to avoid accidental V1 product-scope regression:

- old top-level `mobile/src/components/*` chat/settings components
- old `SettingsScreen`
- old `TeamEditorScreen`
- old `SpeciesSearchScreen`

Active user-facing Roco V1 code lives in:

- `mobile/src/roco/*`
- `mobile/src/components/roco/*`
- `mobile/src/screens/ChatScreen.tsx`
- `mobile/App.tsx`

Do not reintroduce Team/Species screens into V1 product navigation unless
product scope changes. The authorized `队伍设置` drawer entry is a settings
placeholder only; it does not change the single Agent Chat product boundary.
Future GUI roster selection should save reusable team context for Chat instead
of producing separate analysis output.

## Common Change Paths

### Tune chat visual layout

Start with:

- `mobile/src/roco/rocoTheme.ts`
- `mobile/src/components/roco/MessageBubble.tsx`
- `mobile/src/components/roco/PaperSurface.tsx`
- `mobile/src/components/roco/PromptComposer.tsx`

Run:

```bash
cd mobile && npm run typecheck
```

Then manually verify long chat, keyboard open, persona wheel, and action menu.

### Change persona behavior

Update:

- `mobile/src/roco/rocoPersona.ts`
- `mobile/src/roco/rocoTheme.ts`
- `mobile/src/components/roco/PersonaWheel.tsx`
- backend persona selector contract if adding real managed personas

Verify that `/chat` still sends public `persona_selector`, not UI ids.

### Change backend response rendering

Update:

- `mobile/src/api/types.ts`
- `mobile/src/roco/rocoPresentation.ts`
- `mobile/src/components/roco/AnalysisCard.tsx`

Keep raw/tool-trace content suppressed unless a public-safe backend flag is added.

### Change settings

Update:

- `mobile/src/components/roco/SettingsDrawer.tsx`
- `mobile/src/runtime/runtimeSettings.ts`
- `mobile/App.tsx`

Do not expose engineering-only runtime or transport concepts in normal V1 settings.

## Required Verification

Always run:

```bash
cd mobile && npm run typecheck
```

Recommended manual checks:

- Long chat scrolls independently and composer remains visible.
- Keyboard open does not hide composer.
- Default message sends `you_know_who`.
- Switching to `默认AI助手` sends `lattice_support_coach`.
- Persona wheel opens from Agent avatar long press and outside tap closes it.
- Message action menu is above bubbles.
- Rewrite latest user message does not scroll to bottom before the rewritten position is visible.
- Settings drawer has no runtime/local/cloud/native/deterministic wording.
- Paper uses raster PNG and outline remains visually above content.
