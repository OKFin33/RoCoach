# Visual Parity Spec

## Purpose

This file is the practical "make it look like the approved UI" guide for Expo RN implementation.

Use it with:

- `../tokens.json`
- `layout.md`
- `components.md`
- `interactions.md`
- `../screens/*.png`

The screenshots are visual references. The values below are the implementation constraints.

## Parity Target

The RN app should preserve:

- single chat surface, no header
- yellow shell
- cream paper frame
- thick black hand-drawn outline
- sticker-like avatars
- minimal message stream
- card treatment only for long analysis
- right-edge pull handle
- avatar-anchored persona wheel

Pixel-perfect parity with Web is not required because RN text rendering and safe areas differ across iOS/Android. The target is visual identity parity: same layout hierarchy, proportions, colors, stroke weight, and interaction states.

## Reference Canvas

Base design reference:

```text
logical width: 390
logical height: 844
```

Current exported screenshots are 399x710 because they were captured from the in-app browser viewport. Treat them as composition references, not absolute mobile dimensions.

Scale rules:

```ts
const scale = screenWidth / 390;
const s = (value: number) => Math.round(value * scale);
```

Only scale large layout values. Keep text sizes mostly fixed for readability:

- message body: 15
- card body: 13-14
- card title: 18
- input text: 16

Do not scale fonts directly with viewport width.

## Shell

RN style:

```ts
shell: {
  flex: 1,
  backgroundColor: tokens.color.shellYellow,
  paddingHorizontal: 10,
  paddingTop: 8,
  paddingBottom: 8,
}
```

No fake phone status bar.

No top app header.

No persistent online chip.

## Paper Frame

Use:

```text
assets/paper/paper_shell.png
```

Do not use `paper_frame.svg` as the P0 source. It is a fallback/reference only. The approved visual correction is the raster paper shell.

Recommended layout:

```ts
paperWrap: {
  flex: 1,
  position: "relative",
}

paperImage: {
  position: "absolute",
  left: 0,
  right: 0,
  top: 0,
  bottom: 0,
}

paperContent: {
  flex: 1,
  paddingTop: scaledInsetTop,
  paddingRight: scaledInsetRight,
  paddingBottom: scaledInsetBottom,
  paddingLeft: scaledInsetLeft,
}
```

Render:

```tsx
<ImageBackground
  source={paperShell}
  resizeMode="stretch"
  style={styles.paperWrap}
  imageStyle={styles.paperImage}
>
  <View style={[styles.paperContent, contentInset]}>{children}</View>
</ImageBackground>
```

Insets from raster source:

```text
source size: 915 x 1616
top: 72
right: 52
bottom: 58
left: 52
```

If content appears too close to outline on small Android screens, add `+4` to left/right content padding before reducing message widths.

Bitmap scaling:

```ts
const xScale = paperWidth / 915;
const yScale = paperHeight / 1616;

const contentInset = {
  top: Math.max(30, Math.round(72 * yScale)),
  right: Math.max(20, Math.round(52 * xScale)),
  bottom: Math.max(24, Math.round(58 * yScale)),
  left: Math.max(20, Math.round(52 * xScale)),
};
```

P0 rule:

- Use the approved bitmap even if it stretches slightly across devices.
- Do not recreate the paper with hand-written SVG paths unless a later UI review accepts the result.
- `paper_outline.png` may be layered as an optional overlay if `paper_shell.png` needs stronger edge contrast.

## Chat Scroll

Message stack:

```ts
chatList: {
  flex: 1,
  paddingHorizontal: 8,
  paddingTop: 6,
  paddingBottom: composerHeight + 10,
  gap: 12,
}
```

Use `FlatList` if implementing real chat history. Use `ScrollView` only for MVP simplicity.

Do not show per-message timestamp.

Do not show date divider unless product explicitly enables session grouping. The Web prototype includes a small date divider only as a reference artifact; RN can omit it.

## Agent Bubble

Layout:

```ts
agentRow: {
  flexDirection: "row",
  alignItems: "flex-end",
  alignSelf: "flex-start",
  maxWidth: "88%",
  gap: 8,
}
```

Avatar:

```ts
agentAvatar: {
  width: 34,
  height: 34,
}
```

Bubble:

```ts
agentBubble: {
  backgroundColor: tokens.color.agentBubble,
  borderColor: tokens.color.ink,
  borderWidth: 2.6,
  borderTopLeftRadius: 17,
  borderTopRightRadius: 17,
  borderBottomRightRadius: 17,
  borderBottomLeftRadius: 6,
  paddingHorizontal: 14,
  paddingVertical: 10,
}
```

Tail:

- RN can implement via a small rotated `View` or SVG triangle.
- Tail color matches bubble fill.
- Tail sits on the left side near bottom `9`, width `11`, height `12`, visually connected to bubble.
- Tail uses left/bottom ink strokes, matching the Web prototype.

Text:

```ts
messageText: {
  fontSize: 15,
  lineHeight: 23,
  color: tokens.color.ink,
}
```

## User Bubble

Layout:

```ts
userRow: {
  flexDirection: "row",
  alignItems: "flex-end",
  alignSelf: "flex-end",
  justifyContent: "flex-end",
  maxWidth: "88%",
  gap: 8,
}
```

Bubble:

```ts
userBubble: {
  backgroundColor: tokens.color.userBubbleBottom,
  borderColor: tokens.color.ink,
  borderWidth: 2.6,
  borderTopLeftRadius: 17,
  borderTopRightRadius: 17,
  borderBottomLeftRadius: 17,
  borderBottomRightRadius: 6,
  paddingHorizontal: 14,
  paddingVertical: 10,
}
```

If `expo-linear-gradient` is available:

```text
top: tokens.color.userBubbleTop
bottom: tokens.color.userBubbleBottom
```

User avatar:

```ts
userAvatar: {
  width: 30,
  height: 30,
}
```

User row order is bubble first, avatar second. The avatar remains on the right side of the row.

User tail:

- right side near bottom `9`
- width `11`, height `12`
- fill matches `tokens.color.userBubbleBottom`
- uses right/bottom ink strokes

## Inline Rewrite State

Do not add an inner white edit box. The approved direction is "same bubble, editable text".

Visual:

- same yellow user bubble
- text becomes `TextInput`
- cancel and confirm round buttons appear under/right inside bubble
- composer disabled while editing

Buttons:

```ts
rewriteButton: {
  width: 28,
  height: 28,
  borderRadius: 999,
  borderWidth: 2,
  borderColor: tokens.color.ink,
  alignItems: "center",
  justifyContent: "center",
}

cancelButton: {
  backgroundColor: tokens.color.paper,
}

confirmButton: {
  backgroundColor: tokens.color.ink,
}
```

## Thinking Bubble

Layout:

- Agent avatar left
- compact cream bubble
- three dots inside

Animation:

- opacity pulse or dot translate
- subtle
- no full-screen loader

Fallback if animation is deferred:

```text
...
```

inside Agent bubble is acceptable for MVP.

## Analysis Card

Width:

```ts
analysisCard: {
  marginLeft: 42, // avatar width + gap
  marginTop: 8,
  width: "calc content width minus avatar lane",
}
```

RN should compute this from container width:

```ts
const avatarLane = 42;
const cardWidth = contentWidth - avatarLane;
```

Container:

```ts
analysisCard: {
  backgroundColor: tokens.color.cardBody,
  borderColor: tokens.color.ink,
  borderWidth: 2.6,
  borderRadius: 14,
  overflow: "hidden",
}
```

Header:

```ts
analysisCardHeader: {
  minHeight: 48,
  backgroundColor: tokens.color.cardHeader,
  borderBottomWidth: 2.6,
  borderBottomColor: tokens.color.ink,
  paddingHorizontal: 14,
  flexDirection: "row",
  alignItems: "center",
  gap: 10,
}
```

Body:

```ts
analysisCardBody: {
  paddingHorizontal: 14,
  paddingVertical: 12,
  gap: 12,
}
```

Rows:

```ts
analysisRow: {
  flexDirection: "row",
  gap: 10,
  paddingVertical: 8,
  borderBottomWidth: 1,
  borderBottomColor: "rgba(23,23,23,0.10)",
}
```

Use icon chips sparingly. If icons are not ready, use simple black circular bullets.

Important:

- This card is `AnalysisCard`, not `ToolArtifactCard`.
- Do not hardcode the mock rows `核心问题 / 推荐调整 / 风险点` unless backend provides those fields.

## Prompt Composer

Position:

- inside paper
- bottom aligned
- horizontal layout

Style:

```ts
composerWrap: {
  flexDirection: "row",
  alignItems: "flex-end",
  gap: 9,
  paddingHorizontal: 14,
  paddingTop: 0,
  paddingBottom: 7,
}

composerInputBox: {
  flex: 1,
  minHeight: 44,
  maxHeight: 116,
  borderRadius: 22,
  borderWidth: 2.5,
  borderColor: tokens.color.ink,
  backgroundColor: "#FFF8E8",
  paddingHorizontal: 14,
  paddingVertical: 8,
}

sendButton: {
  width: 44,
  height: 44,
  borderRadius: 999,
  borderWidth: 2.5,
  borderColor: tokens.color.ink,
  alignItems: "center",
  justifyContent: "center",
}
```

Enabled send:

```ts
backgroundColor: tokens.color.ink
iconColor: tokens.color.shellYellow
shadow: "0 3px 0 rgba(17,17,17,0.35)"
```

Disabled send:

```ts
backgroundColor: "rgba(23,23,23,0.25)"
iconColor: tokens.color.settingsPanel
shadow: "none"
```

TextInput:

- font size `15`
- line height `22`
- max text area height `100`
- Enter-to-send is Web-only convenience. RN should send from the send button unless product explicitly enables keyboard send.

## Message Action Menu

Placement:

- absolute overlay above the long-pressed bubble
- clamp inside paper/screen bounds
- do not cover the selected bubble if avoidable
- backdrop is `rgba(17,17,17,0.08)`

Position:

```ts
const menuX = role === "user" ? bubbleRightInRoot - 192 : bubbleLeftInRoot;
const menuY = bubbleTopInRoot - 48;
const left = clamp(12, menuX, rootWidth - 212);
const top = clamp(20, menuY, rootHeight - 66);
```

Style:

```ts
messageActionMenu: {
  position: "absolute",
  backgroundColor: tokens.color.settingsPanel,
  borderColor: tokens.color.ink,
  borderWidth: 2.5,
  borderRadius: 14,
  padding: 6,
  flexDirection: "row",
  gap: 4,
  shadowColor: "#111111",
  shadowOpacity: 0.22,
  shadowRadius: 18,
  shadowOffset: { width: 0, height: 18 },
}
```

Button:

```ts
actionButton: {
  minWidth: 54,
  height: 34,
  borderRadius: 9,
  alignItems: "center",
  justifyContent: "center",
  paddingHorizontal: 8,
  gap: 5,
}
```

Text:

- font size `12.5`
- font weight `800`
- danger color `tokens.color.danger`
- danger background `rgba(184,58,75,0.12)`

Delete confirmation:

- same menu location
- replace actions with `确认删除` and `取消`
- `确认删除` min width `78`

## Persona Wheel

Wheel item:

```ts
personaItem: {
  width: 52,
  height: 52,
  borderRadius: 999,
  borderWidth: 3,
  borderColor: tokens.color.ink,
  backgroundColor: tokens.color.paper,
  alignItems: "center",
  justifyContent: "center",
}
```

Selected:

```ts
backgroundColor: tokens.color.shellYellow
```

Radial offsets from anchor center:

```ts
const RADIUS = 86;
const POSITIONS = [
  { id: "you_know_who", angle: -42 },
  { id: "ai_assistant", angle: 8 },
  { id: "add_persona", angle: 58 },
];

const dx = Math.cos(angle * Math.PI / 180) * RADIUS;
const dy = Math.sin(angle * Math.PI / 180) * RADIUS;
```

If the anchor is close to the screen edge, flip offsets inward so items remain visible.

Open motion:

- backdrop opacity fades from `0` to prototype dim amount in `180ms`
- anchor halo scales from `0.82` to `1` and fades in over `160ms`
- every option starts visually at the long-pressed avatar center with
  `scale=0`, `opacity=0`
- options spring to their radial positions with stiffness `380`, damping `26`
- options are staggered by `50ms`
- do not replace this with a static overlay; the pop-out motion is part of the
  wheel affordance

Labels:

- default: no visible labels
- use accessibility labels
- if product later wants labels, render tiny labels above avatars with high z-index

## Settings Drawer

Closed:

- handle aligned to right screen edge

Open:

- drawer width: `screenWidth * 0.88`, matching the accepted Web prototype rail width
- handle remains attached to drawer left edge

Handle:

```ts
drawerHandle: {
  width: 22,
  height: 58,
  borderTopLeftRadius: 12,
  borderBottomLeftRadius: 12,
  borderWidth: 3,
  borderRightWidth: 0,
  borderColor: tokens.color.ink,
  backgroundColor: tokens.color.shellYellowDeep,
  alignItems: "center",
  justifyContent: "center",
  gap: 4,
}
```

Handle grip:

- three vertical dots
- each dot is `4 x 4`
- dot fill `tokens.color.ink`

Panel:

```ts
drawerPanel: {
  width: drawerWidth,
  backgroundColor: tokens.color.settingsPanel,
  borderLeftWidth: 2.6,
  borderColor: tokens.color.ink,
  padding: 18,
}
```

No separate top-right close button. The connected handle and backdrop are enough.

## Visual QA Checklist

Before marking RN implementation done:

- Main screen has no custom header.
- Paper shell uses the approved raster asset `assets/paper/paper_shell.png`; `paper_frame.svg` is reference/fallback only.
- Composer is inside paper, not in a separate bottom band.
- Agent avatar aligns with spoken bubble, not analysis card.
- User and Agent bubbles use opposite alignment and matching tails.
- Long analysis appears as a card under Agent text, not as a new screen.
- Message action menu has correct actions for latest/older user messages.
- Persona wheel opens from Agent avatar and can dismiss by outside tap.
- Settings handle moves with drawer.
- API key copy says SecureStore/local device secure storage.
- No Team/Species/Calculator/Dex visible entrances.
- No local model/local cloud marketing language.
