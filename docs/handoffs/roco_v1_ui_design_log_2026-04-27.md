# Roco V1 UI Design Log

Date: 2026-04-27

This document records why the Roco V1 UI reached its current shape. It is a
design-decision log, not the implementation source of truth. For current RN
implementation details, start from:

- `mobile/ROCO_RN_UI_FILE_GUIDE.md`
- `mobile/README.md`
- `ui_handoff/roco_v1_rn/specs/rn_implementation_spec.md`
- `ui_handoff/roco_v1_rn/specs/prototype_parity_addendum.md`

## 1. Initial Product Boundary

Roco V1 was locked as a single-Agent Chat product, not a multi-tool app.

The main product surface should be:

- chat stream
- prompt composer
- Agent avatar
- right-edge settings drawer

Team, Species, Calculator, Dex, evidence/debug surfaces, and raw tool payloads
were treated as Agent-internal capabilities, not first-class user navigation.

The reason was product clarity. V1 needed to feel like a focused mobile chat
assistant, not an operational dashboard with multiple partially complete tools.

## 2. Early Managed Persona Brief Was Superseded

The earliest UI direction discussed a managed-persona selector contract:

```json
{
  "kind": "managed",
  "persona_id": "xxx",
  "version": "draft.v1",
  "revision": 1
}
```

That work was useful for backend/public-selector boundaries, but it was not the
final V1 UI direction. The product later clarified that Roco V1 is a single
Agent Chat app. Persona switching therefore moved out of global settings or
tool panels and became an avatar-centered interaction.

Final V1 persona rule:

- long-press Agent avatar to open a radial persona wheel
- UI uses public selector objects only
- UI never builds internal encoded selectors
- add-persona remains a reserved seam, not a creation flow

## 3. Visual Direction From Reference Screens

The accepted visual language came from a simplified version of the Roco
Kingdom-inspired mobile screenshots the user provided:

- bright yellow outer shell
- cream paper reading surface
- thick black hand-drawn outlines
- sticker-like avatars
- minimal chat flow
- richer card treatment only for long analytical content

Several visual elements were explicitly rejected:

- fake phone status bar
- top black notch
- persistent online chip
- bottom navigation
- per-message timestamps
- dense multi-tool icon navigation

The design target became: keep the interface close to a minimal mobile chat,
but give the reading surface and key controls enough stylized identity to avoid
a generic messenger look.

### Visual Intent And Tradeoffs

The visual direction deliberately sits between two extremes:

- pure WeChat-style minimalism
- dense Roco Kingdom-style game UI

Pure messenger minimalism was too generic. It did not give Roco a memorable
product identity, and it made long analytical answers look like ordinary
assistant text. Full game UI was too noisy for a daily mobile chat product. It
introduced too many badges, tabs, decorative controls, and visual competition
around the actual conversation.

The chosen compromise:

- keep the chat structure simple enough for repeated mobile use
- use the yellow shell and paper surface as the main brand signal
- keep bubbles restrained so reading remains comfortable
- reserve richer chrome for cards and secondary surfaces

This means the UI should not chase every detail from the reference screenshots.
The references define material language and mood, not a requirement to recreate
the original app's navigation density.

### Material Strategy

The paper surface is the emotional anchor of the interface. It provides a
"magical academy / notebook" reading feeling without adding a visible header or
bottom navigation. Because it occupies most of the screen, its fidelity matters
more than almost any individual icon.

The yellow shell exists to frame the paper, not to become a second content area.
It should be visible around the paper edge and right handle, but should not
create extra panels behind the composer or messages.

The message bubbles intentionally stay quieter than the paper:

- Agent bubble: cream, readable, conversational
- user bubble: yellow, compact, right-aligned
- card shell: stronger header and border for long-response scanning

This hierarchy prevents the UI from becoming a one-note yellow theme.

## 4. Figma Make / Web Prototype

A Figma Make Web prototype was created at:

```text
figma/Minimal Chat Interface Design
```

The prototype established the accepted V1 visual and interaction direction:

- yellow shell
- natural paper container
- user and Agent chat bubbles
- prompt composer inside the paper surface
- avatar-anchored persona wheel
- connected right-edge settings handle/drawer
- long-press message action menu
- generic long-response card shell

The prototype was not treated as production code. Its CSS, DOM layout,
framer/motion behavior, and mock data were explicitly marked as visual
reference only.

Key handoff document:

```text
specs/roco_v1_ui_prototype_handoff_2026-04-26.md
```

## 5. Paper Asset Decision

The paper container became the biggest fidelity risk.

The first RN handoff direction tried to express the paper as SVG/path geometry.
That was rejected because the result looked too mechanical and failed to match
the natural paper feeling from the accepted concept.

The accepted correction was:

- use the raster paper shell image directly
- source asset: `paper_shell.png`
- source size: `915 x 1616`
- render through RN `ImageBackground`
- use `resizeMode="stretch"`
- optionally overlay `paper_outline.png` above content so notches/edges remain
  visually dominant

The SVG `paper_frame.svg` remains only as a fallback/reference. It must not be
used as the P0 implementation source.

### Paper Tradeoff

SVG/path paper was attractive because it seemed scalable and RN-native. In
practice, it produced the wrong feeling: too symmetric, too clean, and too
obviously artificial. This is why the accepted implementation uses a raster
shell despite the normal engineering preference for vector frames.

The tradeoff is acceptable because:

- the paper is a large background asset with stable proportions
- its natural edge quality matters more than perfect parametric scalability
- RN `ImageBackground` with explicit insets is simple and robust
- the optional outline overlay protects the visual edge when content scrolls
  near the top notch

Do not "optimize" this back into hand-written SVG paths unless a future asset
pipeline can match the raster fidelity.

## 6. Chat Layout Decisions

The chat layout was repeatedly tightened around mobile ergonomics.

Locked decisions:

- no custom header
- paper contains both scroll area and composer
- composer is a sibling of the chat `ScrollView`, not inside it
- the `ScrollView` must be bounded with `flex: 1`
- long chat scrolls independently and never pushes the composer off screen
- keyboard opening should preserve the composer and latest-message visibility

Message rows:

- Agent row: avatar first, bubble second
- user row: bubble first, avatar second
- Agent avatar anchors to the spoken bubble, not the analysis card
- analysis card renders below the spoken bubble in a card lane

This distinction matters because long analytical cards are readability
containers, not replacements for the Agent's conversational reply.

### Chat Density Tradeoff

The chat screen should feel calm during long use. This drove several removals:

- no per-message timestamps
- no persistent online state
- no header text competing with messages
- no visible tool buttons near the composer

The cost is that the UI has fewer explicit controls. That is intentional. Roco
V1 relies on natural-language chat and a few mobile-native gestures rather than
a visible toolbar.

The composer remains visually important but not heavy. It lives inside the
paper because the paper is the reading/writing surface. It stays outside the
scroll view because the composer is a fixed input affordance, not part of chat
history. This sibling relationship is a hard layout rule.

## 7. Analysis Card Boundary

The visual prototype included a strategy card, but that card was never accepted
as a backend data contract.

The current backend-supported fields are:

```text
response.answer
response.persona?.rendered_answer
response.presentation?.reply
response.presentation?.why
response.presentation?.visible_warnings
response.presentation?.detail_sections
response.presentation?.followup_prompts
```

Therefore V1 implements a generic `AnalysisCard`:

- summary from `presentation.why`
- warnings from `presentation.visible_warnings`
- public-safe sections from `presentation.detail_sections`
- optional followup prompts

The UI must suppress `raw` and `tool_trace` sections unless a future backend
contract marks a section public-safe for UI rendering.

The UI must not hardcode mock strategy fields such as "核心问题 / 推荐调整 /
风险点" unless a future backend card contract exists.

### Card Tradeoff

Cards are for readability, not for pretending that every answer is structured
data. Normal Agent replies should remain bubbles. A card is appropriate when
the response would otherwise become a long text wall or when backend
presentation fields provide clear sections.

The current `AnalysisCard` is intentionally generic. It gives the product a
high-quality visual container while avoiding a false backend contract. This
keeps the UI honest: it can improve scanability without inventing data fields
that the Agent/backend cannot reliably provide.

Future typed cards should be added only after backend contracts define stable
fields, not by reverse-engineering the mock strategy screenshot.

## 8. Persona Decisions And ID Drift

Persona naming changed during the project and required correction.

Earlier references used `obsidian_tactical_coach` as the backend id for the
black-cloaked default persona. Later backend/runtime direction made
`you_know_who` the intentional public-safe runtime id for the default distilled
persona layer, with `obsidian_tactical_coach` only as a legacy compatibility
alias.

Current V1 mapping:

```text
You know who -> ui_id you_know_who -> { kind: "built_in", persona_id: "you_know_who" }
默认AI助手 -> ui_id ai_assistant -> { kind: "built_in", persona_id: "lattice_support_coach" }
添加人格 -> ui_id add_persona -> no selector; reserved seam
```

Important boundary:

- `You know who` is a public-safe codename for a distilled persona layer.
- Public UI must not claim this is Enzo/恩佐.
- Public UI must not use official character art, official lore, official
  dialogue, or authorization language.

## 9. Persona Wheel Interaction

The persona selector initially risked becoming a panel or settings dropdown.
That was rejected because persona is part of the Agent identity, not a generic
configuration row.

Final interaction:

- long-press Agent avatar
- radial wheel opens around the avatar on the same chat screen
- no visible text labels by default on mobile
- selected persona shows a ring and check mark
- hover-only check marks are forbidden
- tap outside dismisses without changing persona
- selecting a persona immediately changes the main Agent avatar

`添加人格` remains pressable as a reserved seam so future persona creation can
be added without redesigning the wheel.

### Persona Interaction Tradeoff

Putting persona selection in Settings would have been easier to discover, but
it would make persona feel like a generic configuration field. The product
intent is different: persona is the Agent's current identity. Anchoring the
wheel to the Agent avatar makes the interaction spatially meaningful.

The wheel avoids visible labels by default because mobile labels around a
radial menu quickly collide with bubbles and paper edges. Accessibility labels
carry the option names. If labels are later needed, they should be small,
above-avatar labels with higher z-index, not permanent text boxes.

Long press was accepted despite lower discoverability because it minimizes
mis-taps in the main chat flow. Persona switching is secondary; sending and
reading messages remain primary.

## 10. Settings Drawer Decisions

The right-edge drawer exists for secondary settings, especially API key and
provider configuration.

Interaction decisions:

- open by right-edge left swipe or connected handle
- handle and drawer move together as one animated rail
- no separate top-right close button
- backdrop tap closes

Runtime/product language decisions:

- no visible local/cloud mode
- no local-model implication on mobile
- no visible `Runtime mode`, `Native`, or `确定性` control in normal V1 UI
- provider key is user-owned and stored through Expo SecureStore
- provider key must not enter chat content, logs, persona metadata, or
  presentation output

The settings drawer later gained an authorized settings home with:

- `队伍设置`
- `API 设置`
- `人格设置`

This was a product-scope clarification, not permission to restore a multi-tool
app. The `队伍设置` entry is a reserved roster/context configuration surface. It
must not call `/team/analyze`, wire to `TeamEditorScreen`, or become an
independent analysis route in V1. Agent analysis remains in Chat.

### Drawer Tradeoff

The right-edge handle was chosen over a visible settings button because the main
screen has no header. A header button would reintroduce chrome the prototype
removed. The handle keeps settings available while preserving the chat-first
composition.

The handle and drawer must move as one rail. Earlier versions where only the
handle moved felt broken: the user appeared to drag a tab instead of pulling a
drawer. The connected rail gives the interaction a physical model.

The settings home was introduced to support authorized secondary configuration
without crowding the API form. The tradeoff is that it resembles a menu. This
is only acceptable because the entries are settings/configuration surfaces, not
Agent tool routes.

`人格设置` in the drawer is informational/status-oriented. It must not replace
the avatar long-press selector as the primary persona interaction.

## 11. Message Actions

Message actions were added for mobile chat usefulness:

User messages:

- latest user message: copy, rewrite, delete
- older user messages: copy, delete

Agent messages:

- copy
- regenerate, disabled until backend support exists
- delete

Copy uses the system clipboard. It must not copy message content into the
composer.

Rewrite is V1-local conversation repair:

1. edit the latest user bubble inline
2. replace that message text locally
3. remove later visible messages
4. send the rewritten text to `/chat` with the same `session_id` and current
   `persona_selector`

This is not a full branch/history UI.

### Message Action Tradeoff

Visible action buttons on every bubble were rejected because they add clutter to
the reading flow. Long press matches mobile chat expectations and keeps the
surface clean.

Rewrite is limited to the latest user message because editing older turns would
imply branching or replay semantics that V1 does not expose. This keeps the
feature useful for immediate typo/intent repair without pretending to manage a
full conversation tree.

Regenerate remains visible but disabled only if product wants the future seam to
be discoverable. It must not fake success until the backend has a real
regenerate or node-replay contract.

## 12. RN Handoff Reset

After the Web prototype was accepted, a dedicated RN handoff package was created:

```text
ui_handoff/roco_v1_rn/
```

Reason: implementation was drifting when agents inferred behavior from Web CSS,
DOM structure, browser pointer events, and mock data.

The RN handoff package introduced:

- RN-specific layout/spec documents
- tokens and parity constants
- public data mapping
- interaction state machines
- asset requirements
- acceptance criteria

The rule became:

```text
Use the Web prototype for visual intent only.
Use ui_handoff/roco_v1_rn for implementation.
```

### Implementation Tradeoff

The Web prototype was valuable for visual exploration because it allowed fast
iteration through Figma Make/Vite. It was a bad production source for Expo RN:

- DOM layout does not map directly to RN `View` hierarchy
- CSS fixed positioning and masks do not map cleanly to mobile
- framer/browser pointer behavior is not RN gesture behavior
- lucide/react web icons are not a RN dependency strategy
- mock cards and mock messages can accidentally become fake contracts

The RN handoff exists to turn visual intent into mobile-safe primitives:

- `View`, `Text`, `ImageBackground`, `Pressable`, `TextInput`
- `Animated` and `PanResponder`
- `react-native-svg` for icons/avatars
- `expo-clipboard` for copy
- `expo-secure-store` for provider key persistence

The implementation rule is conservative: port the experience, not the Web code.

## 13. RN Implementation And QA Fixes

The Expo RN implementation was placed under:

```text
mobile/
```

Current active V1 route:

- `mobile/App.tsx`
- `mobile/src/screens/ChatScreen.tsx`
- `mobile/src/roco/*`
- `mobile/src/components/roco/*`

Important fixes made during QA:

- chat `ScrollView` was bounded with `flex: 1`
- composer stayed outside the scroll area
- debug runtime mode UI was removed from normal Settings
- settings save now derives runtime mode internally from provider config
- README was corrected away from stale SVG-paper and no-selector wording
- Settings `队伍设置` was documented as an authorized reserved settings entry
  only
- RN docs were updated to point maintainers away from legacy scaffold files

Code-level verification performed in this thread:

```bash
cd mobile && npm run typecheck
```

Result: passed after the reviewed fixes.

## 14. Current Source Of Truth

For future work, read in this order:

1. `mobile/ROCO_RN_UI_FILE_GUIDE.md`
2. `mobile/README.md`
3. `ui_handoff/roco_v1_rn/specs/rn_implementation_spec.md`
4. `ui_handoff/roco_v1_rn/specs/prototype_parity_addendum.md`
5. `ui_handoff/roco_v1_rn/contracts/roco_v1_ui_contract.ts`
6. `specs/roco_v1_ui_prototype_handoff_2026-04-26.md` only as historical
   visual/design context

When documents conflict, prefer the newer RN implementation guide and RN
handoff specs over older Web prototype notes.

## 15. Explicit Anti-Patterns

Do not reintroduce these without a fresh product decision:

- top app header, fake phone notch, fake status bar, or online chip
- bottom navigation or multi-tool dashboard
- Team Analyze, Team Editor, Species, Calculator, Dex, evidence, or debug tabs
  as product navigation
- wiring Settings `队伍设置` to `/team/analyze` in V1
- local/cloud mode, local model mode, visible `Runtime mode`, `Native`, or
  `确定性` controls
- hardcoded mock strategy card fields without backend contract
- rendering raw `tool_results.payload`
- using internal encoded persona selectors in UI
- sending `ai_assistant` or `add_persona` as backend persona ids
- publicly naming `You know who` as Enzo/恩佐 or using official character art
- replacing `paper_shell.png` with hand-authored SVG/path paper for P0
- moving `PromptComposer` into the chat `ScrollView`
- anchoring Agent avatar to analysis cards instead of spoken bubbles
- copying message text into the composer when user chooses copy
- enabling regenerate before backend support exists

These anti-patterns are listed because most of them already appeared as
tempting implementation shortcuts during the design process. They are not
abstract style preferences; they directly caused drift from the intended V1
product shape.

## 16. Remaining Open Checks

The remaining gap is visual/device QA, not code-level handoff completeness.

Still useful to capture:

- iOS simulator screenshots
- Android emulator screenshots
- empty chat
- populated chat
- long chat scroll
- keyboard open
- persona wheel open
- settings drawer home/API page
- message action menu
- generic analysis card

The goal of those screenshots is not to redesign the UI. It is to confirm the
RN implementation still converges to the accepted Web/Figma Make visual
direction after platform rendering differences.
