# Prototype Parity Addendum

This file closes the remaining handoff gap between the accepted Web/Figma Make prototype and the Expo RN implementation.

Goal: an implementation thread should not inspect Web CSS, infer interaction behavior, regenerate assets, or invent substitute visuals.

## Source Of Truth Order

Use these files in this order:

1. `specs/rn_implementation_spec.md` for product and backend contract.
2. `contracts/roco_v1_ui_contract.ts` for typed UI data mapping.
3. `specs/prototype_parity_addendum.md` for exact prototype-to-RN parity rules.
4. `specs/layout.md`, `specs/components.md`, `specs/interactions.md`, `specs/visual_parity.md` for implementation detail.
5. `screens/*.png` only for visual comparison.
6. `figma/Minimal Chat Interface Design` only as a last-resort visual reference.

Do not reverse-engineer production rules from the Web prototype. It contains browser-only code and older mock copy.

## Asset Parity Rules

### Paper Shell

P0 must use the supplied raster paper asset.

| Purpose | RN asset | Web prototype source | Required behavior |
| --- | --- | --- | --- |
| Main cream paper container | `assets/paper/paper_shell.png` | `figma/Minimal Chat Interface Design/public/assets/roco-paper-shell.png` | Use directly with RN `ImageBackground` / `Image`, `resizeMode="stretch"`. Do not recreate with SVG paths. |
| Optional outline overlay | `assets/paper/paper_outline.png` | `figma/Minimal Chat Interface Design/public/assets/roco-paper-outline.png` | Use only if edge contrast is too weak after RN scaling. |
| SVG fallback/reference | `assets/paper/paper_frame.svg` | hand-authored lower-fidelity fallback | Do not use for P0 implementation. |

Paper dimensions:

- source image: `915 x 1616`
- source safe content inset: top `72`, right `52`, bottom `58`, left `52`
- x scale = rendered paper width / `915`
- y scale = rendered paper height / `1616`
- minimum content inset after scaling: top `30`, right `20`, bottom `24`, left `20`

Do not use image generation, SVG tracing, CSS masks, blend modes, or hand-drawn replacement paths for the paper shell. The approved correction was the natural raster shell.

### Avatars

Use supplied avatar assets. Do not replace them with official Roco/Tencent/WeChat assets.

| Persona/UI use | Asset | Source basis | Notes |
| --- | --- | --- | --- |
| `You know who` Agent | `assets/avatars/agent_you_know_who.svg` | Web `AgentAvatar` black-cloaked SVG logic | Default visible Agent identity and public-safe codename for the Enzo-derived distilled persona layer. Must be readable at 32/40/48/64 px. |
| `默认AI助手` | `assets/avatars/agent_ai_assistant.svg` | Web `AgentAvatar` AI variant | Blue AI medallion. |
| Add persona | `assets/avatars/persona_add.svg` | Web persona wheel plus medallion | Pressable reserved seam, not a disabled decoration. |
| User avatar | `assets/avatars/user_default.svg` | Web `UserAvatar` SVG logic | Right-side user bubble avatar. |

Avatar implementation options:

- Preferred: convert SVG contents into TSX components using `react-native-svg`.
- Acceptable: configure Expo SVG imports and render the supplied `.svg` files.
- Not acceptable: use emoji, generic initials, stock icons, official game characters, or regenerated images as replacements for the shipped default avatars.

### Icons

Do not import `lucide-react`; it is Web-only in this context.

For RN:

- Implement simple icons as TSX `Svg` components through `react-native-svg`.
- Required icons: send plane, eye, eye-off, clear/x, drawer grip, check, warning triangle, copy, rewrite, regenerate, delete.
- Keep icon strokes close to prototype language: rounded caps, ink color `tokens.color.ink`, stroke around `2` to `2.6`.

## Layout Parity Rules

Must match the prototype decisions:

- no custom header
- no fake phone status bar
- no notch
- no online chip
- no per-message timestamp
- no bottom nav
- no visible Team/Species/Calculator/Dex entry
- yellow shell outside paper
- cream paper shell contains both chat scroll and composer

Clarification: the forbidden entry is a standalone tool/navigation entrance.
The authorized Settings `队伍设置` entry is a roster/context configuration
surface, not Team Analyze, Team Editor, Species, Calculator, or Dex navigation.
It may later embed a graphical local-species database picker so users can build a
team without retyping it into every chat. It must not produce independent
analysis outside the single Agent Chat flow in V1.

The composer is inside the paper surface. Do not add a separate bottom background band behind the composer.

Reference paper targets:

| Screen | Paper x/y | Paper width | Paper height rule |
| --- | --- | --- | --- |
| 390 x 844 | x `10`, y `10` | `370` | screen height minus safe area and vertical shell padding |
| 430 x 932 | x `12`, y `12` | `406` | screen height minus safe area and vertical shell padding |
| 360 narrow Android | x `8`, y `8` | `344` | screen height minus safe area and vertical shell padding |

If a device looks wrong, adjust paper bounds first. Do not replace the paper asset.

Scroll area:

- lives inside paper content inset
- bottom inset = measured composer height + `10`
- auto-scroll to bottom when a new user/Agent message is appended
- `keyboardShouldPersistTaps="handled"`

Composer:

- placeholder: `问问 Roco...`
- outer padding: horizontal `14`, bottom `7`
- row gap: `9`
- input pill background `#FFF8E8`, border `2.5`, radius `22`, padding horizontal `14`, vertical `8`
- text size `15`, line height `22`, max text height `100`
- send button right, circular `44 x 44`
- enabled send: ink fill, yellow send icon, `0 3px 0 rgba(17,17,17,0.35)` visual shadow
- disabled send: `rgba(23,23,23,0.25)` fill, cream icon, no shadow
- no attachment/tool launcher in V1

Keyboard:

- composer moves above keyboard
- latest message remains visible
- paper frame remains visually stable; shrink scroll area before resizing the paper shell

## Empty State Parity

If implementing the empty state from the Web prototype, replicate this structure:

```tsx
<View style={emptyState}>
  <AgentAvatar size={72} />
  <Text>向 Roco 提问队伍策略、精灵搭配，或对战技巧</Text>
  <View>{promptChips}</View>
</View>
```

Required layout:

- container fills available chat scroll area
- center aligned horizontally and vertically
- padding horizontal `24`, vertical `32`
- gap `20`
- Agent avatar size `72`
- invite text size `14.5`, muted color, centered, line height about `1.6`, max width `200`
- prompt chip column width `100%`, gap `9`

Prompt chips are optional for V1. If used, use only natural-language prompts:

```text
这套队伍先手够用吗？
推荐我几只穿透系精灵
对战火系队有没有克制？
```

Do not label chips as Team, Species, Calculator, Dex, or tool names.

## Message Layout Parity

Implement message rows as the prototype does. Do not reinterpret chat layout as a generic messenger style.

### Agent Message Row

Structure:

```tsx
<View style={agentMessageBlock}>
  <View style={agentSpokenRow}>
    <AgentAvatar />
    <AgentBubble />
  </View>
  {analysisCard ? <AnalysisCardLane /> : null}
</View>
```

Required layout:

- `agentMessageBlock` aligns left and uses `maxWidth: "88%"`.
- `agentSpokenRow` is row direction, `alignItems: "flex-end"`, gap `8`.
- Agent avatar comes first, bubble second.
- Agent avatar size is `34`.
- Agent avatar anchors to the spoken bubble only.
- Analysis cards render below the spoken bubble, not inside the avatar row.
- Analysis card lane starts after the avatar lane: `marginLeft: 42` (`34` avatar + `8` gap).
- Analysis card width is the agent message block width minus `42`.
- Thinking and error states keep the same avatar/bubble row.

Agent bubble:

- fill: `tokens.color.agentBubble`
- border: `2.6` ink
- radius order: top-left `17`, top-right `17`, bottom-right `17`, bottom-left `6`
- padding: horizontal `14`, vertical `10`
- text: size `15`, line height `23`, ink
- tail: left side, bottom aligned around `9`, width `11`, height `12`
- tail fill matches bubble fill and uses left/bottom ink strokes

### User Message Row

Structure:

```tsx
<View style={userSpokenRow}>
  <UserBubble />
  <UserAvatar />
</View>
```

Required layout:

- `userSpokenRow` aligns right with `alignSelf: "flex-end"`.
- row direction is normal left-to-right: bubble first, user avatar second.
- `justifyContent: "flex-end"`.
- row gap: `8`.
- max width: `"88%"`.
- User avatar size is `30`.
- User avatar is always to the right of the user bubble.

User bubble:

- fill: gradient `userBubbleTop -> userBubbleBottom` when `expo-linear-gradient` is installed; otherwise flat `tokens.color.userBubbleBottom`
- border: `2.6` ink
- radius order: top-left `17`, top-right `17`, bottom-right `6`, bottom-left `17`
- padding: horizontal `14`, vertical `10`
- text: size `15`, line height `23`, ink
- tail: right side, bottom aligned around `9`, width `11`, height `12`
- tail fill matches user bubble bottom color and uses right/bottom ink strokes

### Message Stack

Required stack behavior:

- message list gap: `12`
- chat list horizontal padding: `8`
- chat list top padding: `6`
- no per-message timestamp
- no sender names above bubbles
- no persistent persona label above bubbles
- no extra status check on the main Agent avatar
- delivery/error affordances are inline and subtle

### Long Content Rule

Long Agent analysis is split as:

1. one normal Agent spoken bubble with the conversational sentence
2. optional `AnalysisCard` in the card lane below it

Do not replace the spoken bubble with a card. Do not anchor the Agent avatar to the card.

## Interaction State Machines

Each interaction must be implemented as a state machine. Do not rely on incidental Web pointer behavior.

### Persona Wheel

State:

```ts
type PersonaWheelState =
  | { status: "closed" }
  | { status: "open"; anchor: { x: number; y: number }; highlightedId: RocoPersonaUiId | null };
```

Trigger:

1. User long-presses an Agent avatar.
2. RN measures avatar center in screen coordinates.
3. After `430ms`, open wheel anchored to that center.

Open UI:

- render on the same chat screen as an absolute overlay
- place options around the avatar center, not inside a separate page
- default option order mirrors prototype: upper/right/lower arc around the anchor
- radial distance: `86`
- angles: `you_know_who = -42`, `ai_assistant = 8`, `add_persona = 58`
- option medallion size: `52`
- anchor halo: `86` px yellow ring with a black outer ring, centered on the
  long-pressed avatar
- backdrop fade: `180ms`
- halo open animation: scale `0.82 -> 1`, opacity `0 -> 1`, duration `160ms`
- option open animation: each medallion starts at the avatar center with
  `scale=0`, `opacity=0`, and springs to its radial position with stiffness
  `380`, damping `26`
- option stagger: `50ms` between medallions
- avoid visible text labels by default on mobile
- use accessibility labels for option names
- if labels become necessary later, render small labels above avatars with higher z-index

Selection:

- hover-only check marks are forbidden
- highlighted-but-not-selected option may show yellow ring/glow only
- selected option shows yellow ring plus check mark
- after tap/release on available option: close wheel, update active avatar, update `active_persona_selector`

Dismiss:

- tap outside closes without changing persona
- Android hardware back closes wheel first
- selecting `添加人格` opens the reserved add-persona seam and does not send a selector

Persona mapping:

```text
You know who -> ui_id you_know_who -> { kind: "built_in", persona_id: "you_know_who" }
默认AI助手 -> ui_id ai_assistant -> { kind: "built_in", persona_id: "lattice_support_coach" }
添加人格 -> ui_id add_persona -> no selector; reserved seam
```

Initial state:

- visible avatar: `You know who`
- active selector: `{ kind: "built_in", persona_id: "you_know_who" }`
- do not omit `persona_selector` while showing the black-cloaked avatar unless backend default is explicitly verified to match it

Boundary:

- `You know who` is the public-safe outward codename for the Enzo-derived
  distilled persona layer.
- Public UI must not claim the persona is Enzo/恩佐 or use official character
  names, lore, dialogue, art, or authorization language.
- `obsidian_tactical_coach` is a legacy compatibility alias and should not be
  emitted by new mobile UI.

### Settings Drawer

State:

```ts
type DrawerState =
  | { status: "closed"; progress: 0 }
  | { status: "dragging"; progress: number }
  | { status: "open"; progress: 1 };
```

Implementation:

- use `Animated.Value` for drawer progress
- drawer width: `screenWidth * 0.88`, matching the accepted Web prototype rail width
- panel and handle are one moving rail
- closed transform: `translateX(drawerWidth)`
- open transform: `translateX(0)`
- handle sits at the rail's left edge, visually connected to the panel
- handle size: `22 x 58`
- handle left offset: `-22`
- handle radius: `12 0 0 12`
- handle border: `3` ink, no right border
- handle grip: three vertical `4 x 4` ink dots, gap `4`
- no separate top-right close button

Triggers:

- press handle toggles open/closed
- drag handle left opens
- drag handle right closes
- tap backdrop closes
- Android hardware back closes drawer first

Drag thresholds:

- opening from closed: drag left exceeds `34px`
- closing from open: drag right exceeds `34px`
- otherwise spring back to previous state

Fields:

- Product API base URL
- Provider API key
- Provider base URL / endpoint
- model
- runtime mode only if already implemented by engineering, but do not label it as local model
- unsafe LAN HTTP dev override only if engineering requires it

Forbidden visible fields:

- local/cloud mode
- local model mode
- duplicate current-persona section under drawer title
- internal transport mode
- internal selector / encoded selector

Security copy:

```text
API 密钥安全提示
密钥仅保存在本机安全存储中。发送请求时会作为请求头交给 Roco 后端，不会进入聊天内容、日志或人格资料。
```

SecureStore unavailable copy:

```text
SecureStore 不可用时，不保存密钥。
```

### Message Actions

State:

```ts
type MessageActionState =
  | { status: "closed" }
  | { status: "open"; messageId: string; role: "user" | "agent"; canRewrite: boolean; confirmDelete: false }
  | { status: "open"; messageId: string; role: "user" | "agent"; canRewrite: boolean; confirmDelete: true };
```

Trigger:

- RN `Pressable` `onLongPress` on message bubble
- open menu near the bubble while clamping inside paper/screen bounds
- context-click is Web-only and must not be part of RN behavior
- menu backdrop is a very light dim layer: `rgba(17,17,17,0.08)`

Position formula from prototype:

```ts
const menuX = role === "user" ? bubbleRightInRoot - 192 : bubbleLeftInRoot;
const menuY = bubbleTopInRoot - 48;

const left = clamp(12, menuX, rootWidth - 212);
const top = clamp(20, menuY, rootHeight - 66);
```

User message actions:

- latest user message: `复制`, `改写`, `删除`
- older user messages: `复制`, `删除`

Agent message actions:

- `复制`, `重新生成`, `删除`

Copy:

- use `expo-clipboard` or chosen RN clipboard package
- copy to system clipboard
- never copy into `PromptComposer`

Rewrite:

- latest user message only
- inline edit inside that user bubble
- disable main composer while editing
- submit action:
  1. replace latest user message text locally
  2. remove later local Agent messages
  3. send new `/chat` request with same `session_id` and current `persona_selector`
  4. render returned response as new latest Agent response
- do not present this as a full branch/history UI

Regenerate:

- show disabled/greyed seam unless backend regenerate endpoint exists
- do not fake successful server-side regeneration

Delete:

- first tap switches menu to confirmation state
- confirmation deletes locally
- server-side deletion/history semantics are not defined in V1

Menu visual:

- background `#FFF8E8`
- border `2.5` ink
- radius `14`
- padding `6`
- row gap `4`
- shadow/elevation equivalent to `0 8px 0 rgba(17,17,17,0.16)` plus soft elevation
- button min width `54`, height `34`, radius `9`
- confirm-delete button min width `78`
- button gap between icon/text `5`
- button text size `12.5`, weight `800`
- danger action color `#B83A4B`, danger background `rgba(184,58,75,0.12)`
- action order:
  - latest user: `复制`, `改写`, `删除`
  - older user: `复制`, `删除`
  - Agent: `复制`, `重新生成`, `删除`
  - delete confirmation: `确认删除`, `取消`

### Loading, Error, Retry

Loading:

- append user bubble immediately
- disable send while pending
- show Agent thinking bubble anchored to Agent avatar
- use a subtle dot or ring animation; no full-screen loader

Success:

- remove thinking bubble
- render Agent reply text
- render generic `AnalysisCard` only if presentation fields justify it

Error:

- inline Agent-side error bubble/card
- suggested copy: `连接或模型请求失败。`
- primary action: `重试`
- do not show raw exception text to normal users

## Analysis Card Parity

The prototype strategy card is a visual proof, not a backend contract.

Allowed V1 generic card mapping:

- `presentation.why` -> summary
- public-safe `presentation.visible_warnings` -> warning rows
- public-safe `presentation.detail_sections` -> collapsible sections
- `presentation.followup_prompts` -> optional chips

Default suppressed section kinds:

- `raw`
- `tool_trace`

Do not hardcode:

- `核心问题`
- `推荐调整`
- `风险点`
- strategy-specific row structure
- raw tool payload fields

If exact typed cards are required, add a backend public artifact contract first.

Visual treatment for the generic card should still replicate the prototype card shell:

- outer border `2.5` ink
- radius `12`
- overflow hidden
- shadow/elevation equivalent to `0 5px 0 rgba(17,17,17,0.18)`
- top margin `8` inside the Agent card lane
- header background `#F7CF45`
- header padding vertical `9`, horizontal `12`
- header gap `8`
- header bottom border `2` ink
- header icon square `28 x 28`, black fill, radius `6`
- title size `15`, weight `800`, ink
- body background `#FFF8E8`
- body padding vertical `10`, horizontal `12`
- row gap `10`
- row padding top `9` except first row
- row padding bottom `9`
- divider `1px rgba(23,23,23,0.10)` except last row
- row title size `13`, weight `700`
- row body size `12.5`, muted ink, line height about `1.5`

## RN Dependency Rules

Allowed/required:

- `react-native-svg` for avatars and icons
- `expo-clipboard` for copy
- existing SecureStore path for provider key
- RN `Animated` / `PanResponder` for drawer and wheel

Forbidden as implementation dependencies:

- DOM APIs
- browser clipboard APIs
- CSS/Tailwind/framer-motion/lucide-react
- browser pointer events
- CSS masks or blend modes as the only way to render paper

## Parity Review Checklist

Before dispatching implementation as done:

- The paper shell uses `assets/paper/paper_shell.png`, not `paper_frame.svg`.
- The composer is inside the paper shell.
- The main screen has no header, phone status bar, online chip, bottom nav, or tool launcher.
- Agent avatars are anchored to spoken bubbles, not analysis cards.
- The selected persona changes the main Agent avatar immediately.
- The persona wheel can dismiss by tapping outside.
- The wheel check mark appears only on the selected persona, not on hover/highlight.
- The drawer handle and drawer panel move together as one rail.
- No visible local/cloud setting exists.
- Provider key copy references on-device SecureStore, not session-local memory.
- Copy uses the system clipboard and does not populate the composer.
- Rewrite is available only for the latest user message.
- Generic AnalysisCard does not expose `raw` or `tool_trace` sections.
- UI sends backend `persona_id` values, not UI option ids.
- Any Settings `队伍设置` surface remains roster/context configuration only and
  is not wired to `/team/analyze` or legacy Team/Species screens.
