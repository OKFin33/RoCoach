# Layout Spec

## Screen Model

Roco V1 has no custom app header in the chat surface.

Use native safe area:

- iOS: respect top and bottom safe areas through `SafeAreaView` or `react-native-safe-area-context`.
- Android: respect status/navigation bars through safe-area provider or equivalent padding.
- Do not render a fake phone status bar, notch, online chip, or browser-like top chrome.

## Base Screen

Recommended hierarchy:

```tsx
<SafeAreaView style={screen}>
  <View style={shell}>
    <PaperSurface>
      <ChatScrollView />
      <PromptComposer />
    </PaperSurface>
    <SettingsDrawer />
    <PersonaWheelOverlay />
    <MessageActionOverlay />
  </View>
</SafeAreaView>
```

## Shell

- Fill screen.
- Background: `tokens.color.shellYellow`.
- Optional faint pattern may be added later with a low-opacity bitmap, but must not sit behind readable text.
- Horizontal padding: `10`.

## Paper Surface

Use `assets/paper/paper_shell.png` as the P0 implementation source.

Do not use `paper_frame.svg` as the P0 implementation source. It is retained only as a fallback/reference because the SVG path recreation was lower fidelity than the approved bitmap paper.

Recommended implementation:

- Render `paper_shell.png` with `ImageBackground`.
- Put scroll content and composer inside the safe content inset.
- Keep the image absolute and non-interactive.

Paper source:

- `assets/paper/paper_shell.png`
- source size: `915 x 1616`
- source safe content inset:
  - top: `72`
  - right: `52`
  - bottom: `58`
  - left: `52`
- non-stretch areas:
  - corners
  - top notch
  - side nicks
  - bottom rounded corners
- stretch model:
  - use `ImageBackground` / `Image` with `resizeMode="stretch"` for P0
  - this is an explicit exception to the earlier SVG preference because visual fidelity of the paper container is more important here
  - content inset scales independently:
    - horizontal inset scale: `renderedWidth / 915`
    - vertical inset scale: `renderedHeight / 1616`
  - minimum content insets after scaling:
    - top: `30`
    - right: `20`
    - bottom: `24`
    - left: `20`
  - if the bitmap looks too vertically stretched on an unusual device, adjust paper bounds before changing asset strategy; do not replace with SVG without UI review

Recommended rendered bounds:

- 390x844 reference screen: x=10, y=10, width=370, height=810 minus safe area
- 430x932 large phone: x=12, y=12, width=406, height=896 minus safe area
- narrow Android 360 width: x=8, y=8, width=344, height available minus safe area

## Scroll Area

The chat scroll area lives inside the paper surface above the composer.

Insets:

- top: paper inset top + `4`
- left/right: paper inset left/right + `8`
- bottom: composer height + `10`

Use `ScrollView` or `FlatList` with:

- `keyboardShouldPersistTaps="handled"`
- bottom content inset equal to composer height
- auto-scroll to bottom on new Agent/user message
- no per-message timestamp

## Prompt Composer Placement

The composer is inside the paper surface, aligned to the bottom of the paper content inset.

Do not put a separate rectangular background band behind the composer. The composer sits directly on the cream paper fill.

Composer layout:

- left optional plus button is deferred for V1 unless attachment flow is approved
- text input center
- send button right
- min height: `48`
- max input height: `108`
- bottom spacing from frame: `12`

## Keyboard Opened

When the keyboard opens:

- keep the paper frame visible
- move composer above keyboard using `KeyboardAvoidingView` or platform-specific keyboard handling
- keep the latest message visible
- do not resize the paper frame into a cramped shape; let scroll area shrink first

Reference behavior:

```text
keyboard visible -> composer moves above keyboard -> scroll inset increases -> latest message remains visible
```
