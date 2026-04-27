# Roco V1 UI Prototype Handoff

Date: 2026-04-26

## One-Line Summary

The current Figma Make prototype is the accepted V1 visual and interaction direction for Roco's single-Agent mobile chat shell. Use it to guide mobile implementation, but do not treat mock analysis cards or mock message data as backend contracts.

Engineering note: for Expo React Native implementation, use the RN-specific handoff package first:

```text
ui_handoff/roco_v1_rn/
```

This Web/Figma Make handoff is now a visual reference and decision record, not the implementation source of truth.

## Where To View

Prototype directory:

```text
/Users/okfin3/project/GitHub/OKFin33/Roco/figma/Minimal Chat Interface Design
```

Run locally:

```bash
cd "/Users/okfin3/project/GitHub/OKFin33/Roco/figma/Minimal Chat Interface Design"
npm run dev -- --host 127.0.0.1 --port 5178
```

Open:

```text
http://127.0.0.1:5178/
```

Build check:

```bash
npm run build
```

Current build status: passed after the latest UI changes.

## Relevant Prototype Files

- `src/app/components/ChatScreen.tsx`
- `src/app/components/PromptComposer.tsx`
- `src/app/components/AgentAvatar.tsx`
- `src/app/components/PersonaWheel.tsx`
- `src/app/components/SettingsDrawer.tsx`
- `src/app/components/ArtifactCard.tsx`
- `public/assets/roco-paper-shell.png`
- `public/assets/roco-paper-outline.png`

## Product Decisions Locked By This Prototype

Roco V1 is a single-Agent Chat product.

The main surface is only:

- chat stream
- prompt composer
- Agent avatar
- right-edge settings handle/drawer

Do not add visible product tabs or entry points for Team, Species, Calculator, or Dex. Those remain internal Agent capabilities and may only appear through conversational results.

The visual direction is:

- minimal mobile chat structure
- bright yellow outer shell
- cream paper chat surface
- thick black hand-drawn outline language
- sticker-like Agent/user avatars
- restrained message chrome
- richer visual treatment only inside long-response cards

The prototype intentionally removed:

- fake phone status bar
- top black notch
- persistent online indicator
- per-message timestamps
- bottom navigation
- multi-tool dashboard entries

## Main Screen Behavior

The paper container is the primary reading surface. It extends behind the composer and uses image assets for a more natural, less symmetrical paper outline.

Normal dialogue should stay as bubbles:

- user message: yellow bubble, right aligned
- Agent message: cream bubble, left aligned, anchored by Agent avatar

Long analytical output may use a card-like container for readability, but the current card is a mock rendering pattern, not a final typed artifact contract.

## Message Actions

Long-press or context-click a message opens message actions.

User messages:

- latest user message: `复制 / 改写 / 删除`
- older user messages: `复制 / 删除`

Agent messages:

- `复制 / 重新生成 / 删除`

Copy writes to the normal system clipboard. It must not copy content into the prompt composer.

Rewrite is inline inside the latest user bubble. Submitting the rewrite updates that node, removes following messages, and regenerates the Agent response from that point. This matches the intended conversation-tree behavior without exposing a full branch UI in V1.

Delete currently has a confirmation step in the action menu.

## Persona Interaction

Persona switching is anchored to the Agent avatar, not a standalone settings panel.

Current behavior:

- long-press Agent avatar to open radial wheel
- wheel appears around the avatar on the main screen
- tap outside to dismiss
- selected persona updates the main Agent avatar

Prototype personas:

- `You know who`: default black-clad Agent avatar
- `默认AI助手`: direct/default LLM assistant
- `添加人格`: placeholder entry to a future persona creation page

The UI must output only public persona selectors:

```json
{
  "kind": "built_in",
  "persona_id": "you_know_who"
}
```

or, later:

```json
{
  "kind": "managed",
  "persona_id": "xxx",
  "version": "draft.v1",
  "revision": 1
}
```

Do not use internal encoded selectors in UI.

## Settings Drawer

Settings opens from the right-edge handle. The handle should feel connected to the drawer and move with it, simulating that the page is being pulled open.

Current settings include:

- API key input
- mask/reveal/clear affordance
- provider
- model
- endpoint
- explicit safety copy that the API key is user-managed and currently session-local/in-memory

Removed from settings:

- local/cloud mode
- local model mode
- duplicate current-persona text under the drawer title
- top-right close button

Reason: Roco V1 is mobile-first and should not imply local model execution. Endpoint remains because users may use OpenAI-compatible cloud/proxy gateways.

## Card / Long Response Position

The current strategy card is a visual proof only.

What is validated:

- long analytical replies should not become plain text walls
- cards can improve readability inside chat
- cards should be inline Agent response content, not external tool pages
- Agent avatar anchors to the spoken bubble, not to the card

What is not yet locked:

- final card fields
- card taxonomy
- tool-specific artifact layouts
- backend `ui_artifacts` or `message_parts` schema

Current backend has `presentation.reply`, `presentation.why`, `visible_warnings`, `detail_sections`, and `followup_prompts`. It does not yet have a stable UI artifact/card contract.

Recommendation:

- implement a generic `AnalysisCard` first for long presentation output
- defer tool-specific cards until backend exposes a public artifact schema
- do not render cards directly from raw `tool_results.payload` in production UI

## Backend Contract Reality Check

Existing public API response:

- `ChatResponse.session_id`
- `ChatResponse.response: AgentResponse`

`AgentResponse` currently includes:

- `answer`
- `tool_results`
- `evidence`
- `confidence_notes`
- `followup_options`
- `synthesis`
- `presentation`
- `persona`

`presentation` currently includes:

```ts
type PresentationResult = {
  presentation_version: string;
  reply: string;
  why: string;
  visible_warnings: VisibleWarning[];
  detail_sections: DetailSection[];
  followup_prompts: string[];
  presentation_metadata: PresentationMetadata;
};
```

This supports a product-facing reply and expandable details. It does not yet support typed UI cards such as `strategy_summary`, `species_profile`, or `damage_calc`.

If cards are needed in production, add a small public contract later, for example:

```ts
type UiArtifact = {
  id: string;
  kind: "analysis_summary" | "species_profile" | "damage_calc" | "dex_snippet";
  title: string;
  summary?: string;
  rows?: Array<{
    label: string;
    value: string;
    tone?: "neutral" | "good" | "warning" | "danger";
  }>;
  actions?: Array<{
    label: string;
    action: string;
  }>;
};
```

Do not treat this example as approved schema. It is a direction for the main thread to formalize.

## Implementation Guidance For Mobile

Use the prototype as visual guidance, not as drop-in production code.

Port first:

- app shell and paper reading surface
- chat bubble styles
- prompt composer
- right-edge settings drawer model
- Agent avatar long-press persona wheel
- message action menu
- generic analysis-card visual language

Defer:

- full persona creation flow
- full tool artifact taxonomy
- typed card schema
- complete branch/history UI for rewritten messages
- native gesture polish beyond the V1 minimum

Avoid:

- adding visible Team/Species/Calculator/Dex entry points
- exposing tool names as navigation
- exposing artifact paths, env vars, internal selectors, resolver/materialization terminology
- assuming API keys are securely persisted
- assuming local model execution exists on mobile

## Suggested Main-Thread Prompt

Use this prompt to continue implementation from the main thread:

```text
Read specs/roco_v1_ui_prototype_handoff_2026-04-26.md and specs/roco_v1_chat_ui_direction_brief.md.

Treat the Figma Make prototype at figma/Minimal Chat Interface Design as the current accepted V1 UI direction for Roco's single-Agent mobile chat shell. Use it to guide the real mobile implementation, but do not copy mock data or assume the mock strategy card is a backend contract.

Priority:
1. Preserve the single Chat product model.
2. Implement the paper-shell chat surface, user/Agent bubbles, prompt composer, message actions, right-edge settings drawer, and avatar-anchored persona wheel.
3. Keep Team/Species/Calculator/Dex as internal Agent tools only.
4. Send only public persona_selector values from UI.
5. Render long Agent analysis through a generic readable card/container where possible, but do not consume raw tool_results.payload as production UI.
6. If production cards require structure beyond presentation.reply/why/detail_sections, define a public UI artifact contract before implementation.

Do not redesign Roco into a multi-tool app. Do not expose internal selector strings, artifact paths, env vars, resolver/materialization language, or local model mode.
```

## Current Assessment

This prototype is sufficient for V1 visual direction and interaction handoff.

Further work should move into:

- mobile implementation
- presentation/card contract design
- representative response examples for long analysis rendering

Do not keep polishing the Figma Make prototype unless a mobile implementation blocker is discovered.
