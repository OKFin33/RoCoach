# Roco V1 RN UI Handoff

Date: 2026-04-27

## Purpose

This package translates the approved Roco V1 Web/Figma Make prototype into an Expo React Native implementation handoff.

The Web prototype remains a visual reference only. Engineering should not read Web CSS, Tailwind classes, DOM layout, framer/motion code, lucide-react icons, or browser pointer-event logic to infer production behavior.

## Target Runtime

- Expo React Native
- iOS and Android phones
- React Native primitives: `View`, `Text`, `Image`, `ImageBackground`, `Pressable`, `TextInput`, `Animated`, `PanResponder`
- `react-native-svg` is required for SVG avatars; add it to `mobile/package.json` before implementation
- Clipboard requires an explicit mobile dependency; use `expo-clipboard` unless the engineering thread chooses another RN clipboard package
- Secrets should use the existing SecureStore path in `mobile/src/runtime/runtimeSettings.ts`

## Files

```text
ui_handoff/roco_v1_rn/
  README.md
  tokens.json
  contracts/
    roco_v1_ui_contract.ts
  screens/
  assets/
    paper/
      paper_shell.png
      paper_outline.png
      paper_frame.svg              # fallback/reference only; not P0 source
      paper_visual_reference_shell.png
      paper_visual_reference_outline.png
    avatars/
      agent_you_know_who.svg
      agent_ai_assistant.svg
      persona_add.svg
      user_default.svg
  specs/
    rn_implementation_spec.md
    layout.md
    interactions.md
    components.md
    visual_parity.md
    data_mapping.md
    new_backend_contract_needed.md
```

## Implementation Priority

P0 RN migration:

- single chat screen
- paper frame surface
- prompt composer
- user and Agent bubbles
- generic analysis card container
- right-edge settings drawer
- long-press Agent avatar persona wheel
- message action menu

P1:

- real loading/error/keyboard polish
- native gesture tuning
- settings validation copy
- analysis-card examples from real backend responses

P2:

- typed tool artifact cards
- complete persona creation flow
- conversation branch/history UI

## Product Rules

- Roco V1 is a single-Agent Chat product.
- No Team, Species, Calculator, or Dex visible entrances.
- Internal tools may only appear as inline conversation results.
- No local model/local cloud mode language in product UI.
- Users provide their own OpenAI-compatible provider key.
- Provider key is stored through platform SecureStore on device and sent only as request headers when native runtime mode is used.
- Provider key must never be visible to Agent messages, logs, presentation output, tool traces, or persona metadata.
- UI sends only public `persona_selector`; no internal encoded selector.

## Required Mobile Dependencies

Current `mobile/package.json` does not include the visual/runtime dependencies needed by this handoff.

Add:

```bash
cd mobile
npx expo install react-native-svg expo-clipboard
```

Rationale:

- `react-native-svg`: renders avatar SVGs in Expo RN.
- `expo-clipboard`: implements message copy through the system clipboard.

Do not replace these with Web DOM APIs or browser clipboard APIs.

## Current Prototype Relationship

Web prototype path:

```text
figma/Minimal Chat Interface Design
```

Run:

```bash
cd "figma/Minimal Chat Interface Design"
npm run dev -- --host 127.0.0.1 --port 5178
```

Use the prototype only to inspect visual intent. Use this RN handoff package for implementation.

## Source Of Truth Order

For RN implementation, use this order:

1. `specs/rn_implementation_spec.md` for build scope and acceptance criteria.
2. `contracts/roco_v1_ui_contract.ts` for typed UI/data boundaries.
3. `specs/visual_parity.md` for exact visual replication rules.
4. `tokens.json` for colors, spacing, radius, stroke, type, and motion values.
5. `specs/layout.md`, `specs/components.md`, and `specs/interactions.md` for structure and state behavior.
6. `specs/data_mapping.md` for backend mapping.
7. `screens/*.png` only as visual references.

Do not implement by reverse-engineering the Web prototype CSS.
