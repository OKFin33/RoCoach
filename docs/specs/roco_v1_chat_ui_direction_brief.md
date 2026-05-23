# Roco V1 Chat UI Direction Brief

Supersession note, 2026-04-27:

- This is the original visual/interaction brief. For Expo RN implementation, `ui_handoff/roco_v1_rn/` is the current source of truth.
- Later product decisions override this brief where they differ: no visible local/cloud control, API key storage uses the mobile SecureStore path, and the visual default `You know who` maps to backend `you_know_who` rather than omitting `persona_selector`. `You know who` is the public-safe outward codename for the Enzo-derived distilled persona layer; public UI must not expose Enzo/恩佐 or official-character positioning.

One-line context for downstream UI work:

> Roco V1 is a single-Agent Chat product, not a multi-tool app. The main screen is only the chat stream and prompt input; Team, Species, Calculator, and Dex are internal Agent tools, not user entry points. Persona switches through a long-press radial wheel on the Agent avatar; Settings opens from a right-edge left swipe. Mobile currently has a minimum functional skeleton, and the next step is final visual style and UI language. The UI only outputs public `persona_selector` and must not use internal encoded selectors.

## 1. Product Model

Roco V1 has one primary surface:

- Chat stream
- Prompt composer
- Agent avatar as the persona interaction anchor
- Right-edge Settings drawer

Do not redesign Roco as a multi-function dashboard. There are no visible `Team`, `Species`, `Calculator`, or `Dex` tabs, buttons, home cards, or side entrances in V1.

Internal Agent tools may appear only as inline result artifacts inside the conversation after the Agent uses them. The user asks naturally in chat; the product does not expose tool routing as navigation.

The current `PersonaSelectorPanel` is a temporary functional skeleton. Do not use its text fields, dense debug metadata, or panel layout as the visual baseline.

## 2. Visual Direction

### Art Keywords

- Mobile chat first
- Roco-like yellow academy UI
- Minimal WeChat chat structure
- Tactical mentor
- Black-clad Agent
- Sun-yellow background
- Cream paper panels
- Thick black hand-drawn outlines
- Sticker-like avatars and icons
- Torn-paper edges used sparingly
- Rounded capsule controls
- Playful fantasy UI, but not a multi-feature game lobby

The design should feel like a private WeChat-style conversation wrapped in the reference game's yellow, bold, sticker-like UI language. It must not become a grid inventory, profile dashboard, or tabbed game portal.

### Moodboard References

Use these as directional references, not as IP copying:

- WeChat conversation structure: stable message stream, simple composer, no decorative app chrome beyond what supports the chat
- Reference screenshots supplied by the user: bright yellow shell, cream content cards, black chunky typography, thick rounded outlines, playful sticker icons, soft gray name pills, bottom torn-paper black navigation treatment
- Fantasy academy stationery only as a secondary layer: paper panels, seals, book tabs, small class-card details
- Tactical assistant UI: compact metadata only when it explains a response or artifact, visually softened by the playful shell

Avoid direct use of official Roco, Tencent, WeChat mini-program chrome, logos, or character assets unless the project already has licensed local assets. Recreate the language with original shapes and assets.

### Color Direction

Core palette:

- `sun-yellow`: dominant app shell and top background
- `cream-paper`: message and panel surfaces
- `ink`: near-black text and Agent silhouette
- `soft-gray`: secondary pills, dividers, disabled controls
- `accent-yellow`: send button, active persona, selected state
- `academy-blue`: Agent/managed status accent
- `leaf-green`: success/active secondary accent
- `warning-orange`: fallback and caution
- `danger-red`: unavailable/error only

Brightness strategy:

- The outer app shell can be bright yellow, but the chat reading area must be cream/off-white.
- Keep message bubbles mostly neutral for long sessions.
- Use black outlines and yellow active states rather than glow-heavy fantasy effects.
- Reserve saturated accents for persona selection, send, retry, and short status feedback.
- Do not place busy motifs behind message text.

### Materials

- App shell: yellow paper texture with faint icon pattern.
- Chat reading surface: cream paper sheet with thick black or dark-gray outline.
- Bubbles: soft rounded rectangles with restrained hand-drawn border irregularity.
- User bubble: warm yellow or cream with yellow edge, depending on readability.
- Agent bubble: cream/white with black outline and small avatar anchor.
- Drawer: cream card sliding over yellow shell, with a dark outline and right-edge handle.
- Persona wheel: sticker medallions expanding from the Agent avatar, selected by yellow ring and black check.

### Typography

- Primary UI font: rounded system sans for mobile readability.
- Display accents: chunky rounded black display style for short labels only, similar to the reference screenshots.
- Message text must remain plain, high-contrast, and comfortable at small sizes.
- Avoid ornate fantasy fonts inside bubbles, composer, API key fields, and error states.
- Chinese UI labels should feel bold and playful, but chat body text must stay readable.

### Visual Density

Roco is a daily mobile chat product. Density should be medium:

- Message stream stays spacious enough for long reading.
- Tool artifacts are compact cards inside the chat, not full panels.
- Persona state is visible through avatar ring/chip, not persistent banners.
- Settings drawer can be denser because it is secondary and task-based.
- Reference-style thick UI is heavy; use it on shell, cards, icons, and key controls, not on every message edge.
- Prefer fewer visible controls. The screen should feel like a chat first and a themed game UI second.

### Minimalism Rules

- Do not include the phone/system status bar in product mockups.
- Do not show `online`, presence, or connection status in the chat header.
- Do not show timestamps on every message.
- Do not add decorative icons beside every message.
- Do not add a bottom navigation strip, even if the reference screenshots use one.
- Keep the number of visible buttons on the main screen to the send button and subtle settings handle.
- Put structured complexity into inline artifact cards, not into global navigation or chat chrome.

## 3. Core Screen Design

### Main Chat Screen

Required structure:

- App content starts below the native/system status bar. Do not design or render the phone status bar as part of Roco.
- Top app chrome is optional and should be minimal: at most a small `Roco` label or Agent avatar anchor.
- Scrollable message stream.
- Assistant messages anchored by the Agent avatar.
- Prompt composer fixed at bottom with safe-area padding.
- No bottom tab bar.
- No standalone tool launcher.
- No online indicator. Roco is a single Agent, and online presence is not meaningful for V1.

Visual shell:

- Yellow background behind the safe area and page edges.
- Cream chat sheet fills the main reading area.
- Thick black/dark outline may frame the chat sheet, but keep it outside the message text path.
- Optional torn-paper black strip can appear only as a decorative bottom edge behind the composer, not as navigation.

The Agent avatar should be the strongest persistent identity mark. Default avatar: black-clad masked/silhouette mentor, sticker-like academy style, original asset.

### User Message Bubble

- Right aligned.
- Cream or pale yellow rounded bubble.
- Thin black outline or subtle shadow; avoid heavy outline on long text bubbles.
- Optional small yellow corner mark for identity.
- Text-first; no decorative frame that reduces reading area.
- Delivery state is subtle: sending, sent, failed.
- Do not show a timestamp on every message. Use a rare centered day/session divider only if needed.

### Agent Message Bubble

- Left aligned with Agent avatar.
- White/cream rounded bubble with soft gray base and black outline.
- Supports text, inline result artifacts, and retry affordance.
- Effective persona appears as avatar ring or compact metadata chip, not as a large header.
- Do not show per-message timestamp or online state.

### Prompt Input

Required elements:

- Multiline text input
- Send button
- Attachment/tool disclosure only if already required by product scope; do not expose Team/Species/Calculator/Dex buttons
- Loading-disabled state while request is in flight, or explicit stop/cancel if implemented

Visual treatment:

- Bottom composer should be close to WeChat: input pill plus send icon/button.
- Surface: cream pill on yellow/cream base.
- Send button: yellow circular or rounded icon button with black icon.
- Optional black torn-paper edge can sit behind the composer as a visual signature, but must not imply bottom navigation.

### Empty State

Goal: invite chat, not explain the whole app.

Recommended content:

- Agent avatar centered or slightly above composer.
- One concise line: `Ask Roco about teams, strategy, or species.`
- Optional prompt chips are allowed only if they are natural-language examples, not tool entrances.

Do not label chips as `Team`, `Dex`, `Calculator`, or `Species` modules.

### Loading / Thinking

Agent thinking should appear inside the chat stream:

- Avatar ring softly pulses in yellow/blue.
- Bubble placeholder uses short copy: `Thinking...`
- Optional tiny sticker-glyph bounce inside the bubble.

Motion must be light and non-blocking. The composer should not jump.

### Error / Retry

Error state belongs on the failed Agent bubble or request row:

- Badge: `Could not answer`
- Copy: `Connection or model request failed.`
- Primary action: `Retry`
- Secondary action: `Edit prompt` if supported

Use danger-red sparingly. Do not turn the whole screen red.

### Internal Tool Result Presentation

Team, Species, Calculator, and Dex are internal Agent tools. When used, show inline result artifacts:

- Team analysis: compact academy report card with score rows and notes.
- Species lookup: small cream bestiary card with sticker icon, type chips, traits, and evidence.
- Calculator result: compact formula strip, not a full calculator panel.
- Dex evidence: source/evidence chips inside the Agent answer.

Artifact rules:

- Artifacts are embedded in the conversation.
- Artifacts are collapsible if long.
- Artifacts never look like persistent navigation.
- Artifacts do not expose backend tool names unless useful to the user-facing explanation.
- Artifact cards may borrow the reference style: yellow header strip, black icon, cream body, thick outer border.
- Artifact cards are the main place where richer UI is allowed. Normal chat bubbles stay minimal.

## 4. Persona Interaction Design

### Entry Point

Persona switching is triggered by long-pressing the Agent avatar.

No permanent persona dropdown in the composer. No Settings-first persona selection. The avatar is the interaction anchor because persona changes who is speaking.

### Default Agent Avatar

Default avatar requirement:

- Black-clad Agent mentor.
- Calm, tactical, slightly mysterious.
- Original sticker-like fantasy-academy styling.
- Clear silhouette at 32-48px.

Avatar states:

- Default/API default: neutral ink ring.
- Active persona: yellow ring with black check.
- Fallback: orange shield/ring.
- Unavailable: muted gray/red broken ring only inside selector, not as persistent alarm.

### Radial Wheel

Long-press behavior:

1. User long-presses Agent avatar.
2. Background chat dims slightly.
3. Radial wheel expands from avatar as sticker medallions.
4. User drags or taps a persona medallion.
5. Release confirms highlighted persona.
6. Tap outside or slide back to center cancels.

Wheel structure:

- Center: `Default`
- First ring: built-in personas
- Outer/secondary arc: managed personas
- Final slot: `Add persona` placeholder

Built-in and managed personas share one selector because the user chooses one speaking style. They are visually tiered, not separated into different controls.

### Current Persona Selected State

Selected persona should show:

- Yellow avatar ring.
- Small check glyph on wheel medallion.
- One-line label near finger-safe area.
- Haptic/light visual confirmation if native layer supports it.

After selection:

- Avatar ring updates immediately.
- Next request sends public `persona_selector`.
- Response effective persona still comes from backend response metadata.

### Add Persona Placeholder

`Add persona` is a semi-transparent plus avatar:

- Looks available but secondary.
- Opens only a placeholder/shell for future persona creation.
- V1 must not design or implement the full creation flow.

Copy:

- Label: `Add persona`
- Disabled/placeholder note if needed: `Coming later`

### New Persona Default Avatar

When a managed persona has no custom avatar:

- Use first initial on an academy medallion.
- Deterministic color from persona id/display name.
- Keep ring and fallback states consistent with normal personas.

### Persona State Copy

Default:

- Label: `Default`
- Meaning: only a true API-default/unselected state
- Request behavior: omit `persona_selector`

V1 visual default:

- Label: `You know who`
- Meaning: black-cloaked tactical Agent
- Request behavior: send `{ "kind": "built_in", "persona_id": "you_know_who" }`
- Boundary: public-safe codename for the Enzo-derived distilled persona layer;
  do not expose Enzo/恩佐, official lore, official dialogue, official art, or
  authorization language.

Active:

- Label: `Active`
- Copy: `Using {display_name}`

Fallback:

- Badge: `Safe fallback`
- Copy: `Selected persona was unavailable or unsafe. Roco used the safe default for this reply.`

Unavailable:

- Badge: `Unavailable`
- Copy: `This persona cannot be used right now.`

Tone must be calm and operational. Do not expose resolver, materialization, artifact path, env, registry, projection, or internal selector language.

### Version / Revision

Default UI hides version and revision.

Advanced settings may show public `version` and `revision` as technical details, but must never show internal encoded selector syntax such as `persona@version#revision`.

## 5. Settings Drawer Design

### Entry

Settings opens by swiping left from the right edge.

Optional visible hint:

- A thin black/yellow edge rail or small handle on the right edge.
- It must not read as a main navigation tab.

### Drawer Layout

Right-side drawer:

- Width: about 86-92% mobile viewport.
- Background: cream paper panel over yellow shell.
- Border: thick black/dark outline with subtle sticker-card irregularity.
- Chat behind it dims and slightly blurs.
- Top section: account/session/runtime status.
- Middle sections: API key and model settings.
- Bottom section: advanced/debug only if enabled.

### API Key Controls

Required controls:

- API key input
- Mask/reveal button
- Clear button
- Provider selector
- Model selector/input
- Endpoint input

Do not expose local/cloud mode in V1 UI.

Security copy hierarchy:

- Primary warning near key field: `Your API key is user-managed and stored on this device.`
- Secondary warning: `Do not screenshot, upload, or paste keys into chats.`
- Technical note: `Roco stores the key through the mobile SecureStore path and sends it only with model requests.`

This warning should be visible but not panic-styled. Use orange/yellow info treatment, not red error styling.

### Settings Persona Detail

Settings may show current persona details as secondary information:

- Current display name
- Kind: default, built-in, or managed
- Fallback status if last response fell back
- Advanced public version/revision only behind disclosure

Primary persona switching remains the avatar radial wheel.

## 6. Interaction / Motion

### Drawer Motion

- Right-edge left swipe opens drawer.
- Drag follows finger with spring settle.
- Tap dimmed chat or swipe right closes.
- Respect safe areas.
- Drawer should not block existing in-flight response unless the user edits runtime settings.

### Persona Wheel Motion

- Long press threshold: native-feeling, roughly 350-500ms.
- Wheel expands from Agent avatar with scale/fade.
- Medallions should snap to readable positions.
- Highlight follows finger.
- Confirmation uses quick ring pulse on avatar.

### Message Motion

- Sent user message slides/fades into stream.
- Agent thinking appears in place with pulsing avatar ring.
- Tool artifacts unfold vertically inside Agent response.
- Retry replaces failed state without shifting the whole conversation unexpectedly.

Motion budget: lightweight. Chat readability wins over spectacle.

## 7. Component Contract

The UI exports only public selector objects.

Managed:

```json
{
  "kind": "managed",
  "persona_id": "xxx",
  "version": "draft.v1",
  "revision": 1
}
```

Built-in:

```json
{
  "kind": "built_in",
  "persona_id": "you_know_who"
}
```

Default:

```json
{}
```

Contract rules:

- If no persona is selected, do not send `persona_selector`.
- If a true API-default/unselected state is selected, do not send `persona_selector`.
- If the visible default is `You know who`, send `{ "kind": "built_in", "persona_id": "you_know_who" }`.
- Do not construct, parse, display, or store internal encoded selectors.
- Do not expose raw `persona_id` editing in production UI.
- Map typed persona option records to the public `persona_selector`.
- Response UI reads effective state from `response.persona`; it must not assume the requested selector was honored.

Suggested value model:

```ts
type PersonaSelectorValue =
  | { mode: "default"; persona_selector?: undefined }
  | { mode: "explicit"; persona_selector: PersonaSelector };
```

Suggested option model:

```ts
type PersonaOption = {
  label: string;
  description: string;
  avatar?: string;
  initials?: string;
  selector?: PersonaSelector;
  category: "default" | "built_in" | "managed" | "add";
  availability: "available" | "unavailable" | "placeholder";
};
```

## 8. Handoff Specs

### Color Tokens

```ts
export const colors = {
  sunYellow: "#F7CF45",
  sunYellowDeep: "#E8B92E",
  creamPaper: "#FFF8E8",
  creamRaised: "#FFFDF3",
  ink: "#171717",
  inkSoft: "#2D2D2A",
  softGray: "#D8D2C2",
  grayPill: "#E8E0CF",
  academyBlue: "#4B8FD8",
  leafGreen: "#65B96A",
  warningOrange: "#D8892E",
  dangerRed: "#B83A4B",
  veil: "rgba(17, 17, 17, 0.42)"
};
```

### Spacing

```ts
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32
};
```

### Radius

```ts
export const radius = {
  bubble: 16,
  composer: 24,
  drawer: 22,
  card: 12,
  medallion: 999
};
```

### Shadows

```ts
export const shadows = {
  bubble: "0 2px 8px rgba(17, 17, 17, 0.08)",
  cardLift: "0 5px 0 rgba(17, 17, 17, 0.16)",
  drawer: "0 18px 60px rgba(17, 17, 17, 0.24)",
  medallion: "0 8px 20px rgba(17, 17, 17, 0.18)",
  glowThinking: "0 0 14px rgba(75, 143, 216, 0.30)",
  glowPersona: "0 0 14px rgba(247, 207, 69, 0.38)"
};
```

### Border Tokens

```ts
export const borders = {
  hairline: "1px solid rgba(23, 23, 23, 0.12)",
  sticker: "2px solid #171717",
  heavySticker: "3px solid #171717",
  softCard: "2px solid rgba(23, 23, 23, 0.72)"
};
```

### Typography Scale

```ts
export const typography = {
  title: { size: 20, lineHeight: 26, weight: 700 },
  section: { size: 15, lineHeight: 20, weight: 650 },
  body: { size: 16, lineHeight: 23, weight: 400 },
  bubble: { size: 16, lineHeight: 24, weight: 400 },
  caption: { size: 12, lineHeight: 16, weight: 500 },
  micro: { size: 11, lineHeight: 14, weight: 600 }
};
```

### Component States

Persona avatar:

- `default`
- `active`
- `fallback`
- `unavailable`
- `thinking`

Persona wheel:

- `closed`
- `opening`
- `open`
- `highlighting`
- `confirming`
- `cancelled`

Message:

- `composing`
- `sending`
- `sent`
- `thinking`
- `streaming`
- `failed`
- `retrying`

Drawer:

- `closed`
- `dragging`
- `open`
- `saving`
- `error`

API key field:

- `empty`
- `masked`
- `revealed`
- `dirty`
- `cleared`
- `invalid`

### Breakpoints / Safe Area

- Primary target: mobile portrait.
- Minimum width: 360px.
- Comfortable width: 390-430px.
- Tablet/wide: keep chat column constrained; do not turn into dashboard.
- Always respect top and bottom safe-area insets.
- Composer height must remain stable when keyboard appears.

### Icon / Avatar Resource Requirements

Required original assets:

- Default black-clad Agent avatar, readable at 32/40/48/64px.
- Built-in persona medallion avatars or deterministic initials.
- Add persona translucent plus medallion.
- Status glyphs: active check, fallback shield, unavailable slash, thinking sparkle/glyph.
- Send icon, reveal/mask icon, clear icon, drawer handle.

Use vector icons for UI controls and bitmap/illustrated assets for avatars where possible.

## 9. Implementation Priority

Must implement for V1:

- Chat-only main screen.
- Prompt composer.
- User and Agent bubbles.
- Agent avatar long-press radial wheel.
- Visual default `You know who` sends `{ "kind": "built_in", "persona_id": "you_know_who" }`; only a true API-default/unselected state omits `persona_selector`.
- Explicit persona sends public `persona_selector`.
- Effective persona/fallback display from `response.persona`.
- Right-edge Settings drawer.
- API key mask/reveal/clear in drawer.
- Provider/model/endpoint controls in drawer; do not expose local/cloud mode in V1 UI.
- Security warning that keys are user-managed and stored through the current mobile SecureStore path.
- Internal tool results as inline chat artifacts only.

Polish after V1:

- Rich yellow paper texture tuning.
- Haptics.
- Persona wheel physics refinement.
- Animated glyph shimmer.
- Custom managed persona avatars.
- Advanced technical disclosure for public version/revision.
- Better inline artifact expand/collapse.

Explicitly forbidden:

- Redesigning Roco as a multi-function app.
- Adding Team/Species/Calculator/Dex user entrances.
- Changing the backend `persona_selector` contract.
- Designing a full persona creation flow in V1.
- Assuming API key persistence is secure before secure storage exists.
- Showing artifact path, env vars, internal selector, registry, projection, resolver, or materialization details in production UI.
