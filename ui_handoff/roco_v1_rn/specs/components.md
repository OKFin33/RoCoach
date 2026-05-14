# Component Spec

## ChatSurface

Purpose:

- Owns the paper frame, scroll area, composer, and overlays.

RN primitives:

- `View`
- `ScrollView` or `FlatList`
- `KeyboardAvoidingView`
- `ImageBackground`

Required dependencies:

- `react-native-svg` only if SVG avatars are imported or converted as components

Props:

```ts
type ChatSurfaceProps = {
  messages: ChatMessage[];
  thinking: boolean;
  error?: ChatError | null;
  activePersonaUiId: RocoPersonaUiId;
  activePersonaSelector?: PersonaSelector | null;
  onSend: (text: string) => void;
  onRetry: (messageId?: string) => void;
  onPersonaSelect: (uiId: RocoPersonaUiId, selector: PersonaSelector) => void;
  onAddPersonaPress: () => void;
};
```

Header:

- none

Empty state:

- no fake chat conversation unless onboarding examples are explicitly enabled
- recommended empty copy: `问问 Roco...`
- optional natural-language chips are allowed, but not tool entries

## MessageBubble

Variants:

- `user`
- `agent`
- `thinking`
- `error`

Agent avatar:

- anchored to the spoken bubble
- not anchored to a card rendered below the bubble
- Agent row order: avatar first, bubble second
- Agent avatar size: `34`

User avatar:

- user row order: bubble first, avatar second
- avatar stays on the right edge of the user row
- User avatar size: `30`

Text:

- body size: `15`
- line height: `23`
- max width: 88% of paper content width

User bubble:

- yellow gradient approximation can be implemented as a flat yellow if RN gradient is not available
- if using `expo-linear-gradient`, use `userBubbleTop -> userBubbleBottom`

Agent bubble:

- cream fill
- black outline
- left tail

Analysis card:

- rendered below the Agent spoken row
- left offset equals avatar lane: `42`
- never replaces the Agent spoken bubble

## PromptComposer

Placeholder:

```text
问问 Roco...
```

Send button:

- enabled: yellow fill, ink paper-plane icon or textless send icon
- disabled: muted fill, ink opacity 0.42

Input:

- multiline
- min height: 48
- max height: 108
- return key sends only if single-line behavior is explicitly chosen; otherwise use send button

Keyboard:

- composer stays above keyboard
- scroll area follows latest message

## AnalysisCard

Purpose:

- readable container for long Agent analysis
- not a typed tool artifact renderer

Use when:

- `presentation.why` is non-trivial
- `presentation.visible_warnings` has entries
- `presentation.detail_sections` has content useful to inspect
- Agent answer would become a long text wall

Do not assume fields like `核心问题`, `推荐调整`, or `风险点` exist unless backend adds a contract.

Suggested visual:

- yellow header strip
- cream body
- thick ink outline
- 2-4 compact sections
- collapsed detail affordance

Props:

```ts
type AnalysisCardProps = {
  title: string;
  summary?: string;
  warnings?: VisibleWarning[];
  sections: Array<{
    id: string;
    label: string;
    content: string;
    defaultExpanded: boolean;
  }>;
  followupPrompts?: string[];
};
```

## PersonaWheel

RN primitives:

- `View`
- `Pressable`
- `Animated`

Asset dependency:

- avatar SVGs require `react-native-svg`

Option layout:

- position each option around anchor center
- avoid labels by default on mobile
- if labels are necessary, put them above avatars and keep z-index above avatars

Add persona:

- keep as pressable reserved seam
- recommended V1 placeholder copy: `人格创建稍后接入`
- implementation should route through a single `onAddPersonaPress` callback so later flow can replace placeholder

## SettingsDrawer

RN primitives:

- `Animated.View`
- `PanResponder`
- `Pressable`
- `TextInput`

Fields:

- Product API base URL
- Provider key
- Provider base URL
- model
- runtime mode if already present in engineering settings
- unsafe LAN HTTP override if present in engineering settings

Security copy hierarchy:

1. short heading: `API 密钥安全提示`
2. body: `密钥仅保存在本机安全存储中。发送请求时会作为请求头交给 Roco 后端，不会进入聊天内容、日志或人格资料。`
3. debug note if needed: `SecureStore 不可用时，不保存密钥。`

Do not say session-local unless product changes away from SecureStore.
