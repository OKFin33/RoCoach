# Interaction Spec

## Persona Wheel

Trigger:

- Long-press Agent avatar.
- Long-press duration: `tokens.motion.longPressMs` = `430ms`.
- Anchor is the Agent avatar center in screen coordinates.

UI state:

- Show a radial wheel around the avatar anchor.
- Dim outside content with transparent backdrop only if needed for tap target clarity.
- Tap outside dismisses.
- Selecting an available persona closes the wheel and updates the active Agent avatar.

Options:

- `You know who`
  - built-in default black-clad Agent
  - UI option id: `you_know_who`
  - backend selector: `{ "kind": "built_in", "persona_id": "obsidian_tactical_coach" }`
- `默认AI助手`
  - direct/default LLM assistant
  - UI option id: `ai_assistant`
  - backend selector: `{ "kind": "built_in", "persona_id": "lattice_support_coach" }`
- `添加人格`
  - reserved seam
  - should be pressable
  - V1 behavior: open a lightweight placeholder/reserved page or reserved-state panel
  - later behavior: route to persona creation flow without changing the wheel contract

Selected state:

- selected avatar has yellow ring and small check mark
- hover state from Web prototype is not relevant on mobile

Data action:

- store active `persona_selector` in chat UI state
- include it in `/chat` request when selected
- V1 initial state visually selects `You know who`; send `obsidian_tactical_coach` for that state unless backend default is explicitly verified to match
- only omit `persona_selector` for a true unselected/API-default state that is not visually showing the black-cloaked persona
- map UI option ids to backend `persona_id` through the table in `data_mapping.md`; do not send UI-only ids directly

Exit conditions:

- select persona
- tap outside
- hardware back on Android closes overlay first

## Settings Drawer

Trigger:

- Right-edge handle press or drag left.
- Handle is visually connected to drawer and moves with it.

Drawer:

- width: `min(screenWidth * 0.82, 340)`
- opens from right
- backdrop: `tokens.color.backdrop`
- handle remains attached to drawer left edge when open

Fields:

- Product API base URL
- Provider API key
- Provider base URL / endpoint
- model
- runtime mode if already implemented by engineering, but do not label it as local model
- unsafe LAN HTTP dev override if engineering requires it
- do not expose transport mode as a local/cloud segmented control in V1

API key rule:

- Current engineering path uses Expo SecureStore (`mobile/src/runtime/runtimeSettings.ts`).
- UI copy must state local device secure storage, not session-only memory.
- Key is user-managed and is sent only to the Product API as request headers for native runtime mode.
- Key must not be shown in chat messages, logs, Agent presentation, tool traces, or persona metadata.
- `transportMode` is internal storage only and must not appear as local/cloud product language.

Exit conditions:

- drag/press handle right
- tap backdrop
- hardware back on Android

## Message Actions

Trigger:

- Long-press message bubble.
- Context-click exists only in Web prototype and is not part of RN behavior.

User message actions:

- latest user message: `复制`, `改写`, `删除`
- older user messages: `复制`, `删除`

Agent message actions:

- `复制`, `重新生成`, `删除`

Copy:

- Call system clipboard.
- Do not copy text into PromptComposer.

Rewrite:

- V1 scope: latest user message only.
- UI state: inline edit inside that user bubble.
- V1 decision: enabled as local replacement plus a new `/chat` request.
- Data action:
  1. replace the latest user message text in local UI state
  2. remove later local Agent messages from the visible thread
  3. send the rewritten text to `/chat` with the same `session_id` and current `persona_selector`
  4. render the returned response as the new latest Agent response
- Limit copy: because backend does not yet support true branch-node rewrite, do not present this as a version-history feature.

Regenerate:

- Requires backend support to regenerate an Agent response from the previous user node.
- V1 decision: keep as visible seam but disabled/greyed if backend support is unavailable.
- If engineering implements a local-only seam, it must be clearly isolated and not described as server-side regeneration.

Delete:

- First tap switches menu to confirmation state.
- Confirmation deletes locally; server-side deletion/history semantics are not defined yet.

Exit conditions:

- select action
- tap outside
- cancel confirmation
- hardware back closes menu first

## Loading / Thinking

Trigger:

- User sends a message.

UI state:

- Append user bubble immediately.
- Disable send while request is pending.
- Show Agent thinking bubble anchored to Agent avatar.
- Use subtle dot animation; no global full-screen loader.

Exit conditions:

- success -> replace thinking with Agent reply/cards
- error -> remove thinking and show error state with retry affordance

## Error / Retry

Error state:

- inline Agent-side bubble or compact warning card
- message copy should be user-readable, not raw exception text
- suggested copy: `连接或模型请求失败。`

Actions:

- `重试`
- optional `复制错误` only in debug builds
