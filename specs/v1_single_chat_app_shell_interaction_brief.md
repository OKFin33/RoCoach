# V1 Single Chat App Shell Interaction Brief

## Purpose

Define the V1 app-shell interaction model after the managed persona contract
milestone. This brief is an implementation guide for the next mobile shell
slice, not final visual design.

## V1 Product Boundary

V1 has one primary user-facing product entrance: an Agent chat surface.

The user interacts with:

- A prompt input box.
- A WeChat-like message list.
- Agent output messages.
- The Agent avatar as the persona interaction anchor.
- A right-side settings drawer for user-owned runtime configuration.

The user should not see Team Analyze, Species Search/Profile, calculator, dex,
or other tool modules as primary navigation entries. Those capabilities remain
available only as internal Agent tools selected by the Agent runtime.

## Hidden Internal Tools

The following are internal capabilities, not visible V1 modules:

- Battle dex lookup and retrieval.
- Calculator-style deterministic helper tools.
- Team Analyze.
- Species Search/Profile.
- Evidence/detail panels that exist for debugging rather than normal chat use.
- Any future backend module that can be invoked from the Agent reasoning path.

Implementation implication: mobile navigation should collapse toward one chat
screen plus settings. Internal tool results may still inform Agent answers, but
the user consumes them through the chat transcript and optional compact evidence
disclosure inside an Agent message, not through separate product tabs.

## Chat Shell Interaction Model

The V1 shell should behave like a simple messenger:

- Message list: chronological vertical thread with user bubbles and Agent
  bubbles.
- Prompt box: fixed at the bottom, supports multiline text, submit action, and
  disabled/loading state.
- Agent avatar: shown beside Agent messages and in any top-level chat identity
  surface.
- User message state: pending, sent, failed retry.
- Agent message state: thinking/loading, streaming or loaded if streaming is
  later added, failed safe fallback.
- Empty state: one minimal prompt invitation and the default Agent avatar.
- Error state: safe user-readable error with no local paths, keys, provider
  secrets, materialization artifacts, or internal selector syntax.

Canonical response invariant:

- `AgentResponse.answer` remains the canonical answer.
- `response.presentation.reply` remains canonical when present.
- Persona rendering may appear as the visible Agent message style, but it must
  not mutate the canonical answer contract.

## Persona Radial Selector

Persona selection is anchored to the Agent avatar.

Trigger:

- Long-press the Agent avatar.
- Later desktop/tablet variants may use right-click or hover-plus-click, but
  mobile V1 should treat long-press as the primary gesture.

Interaction:

- Open a circular/radial wheel around the avatar.
- The currently active persona is visually selected.
- Tapping outside the wheel dismisses it without changing persona.
- Selecting an item updates local selector state for future chat requests.
- The selector must remain decoupled from final art direction and catalog
  layout; it is a behavior seam, not a locked visual system.

Required wheel entries:

- Default `You know who`: represented by a black-clad Agent avatar.
- Persona boundary: `You know who` is the public-safe outward codename for the
  Enzo-derived distilled persona layer. It must not expose Enzo/恩佐,
  official-character positioning, official lore, official dialogue, or official
  art.
- Add persona: represented by a translucent avatar with a plus mark.
- Newly added persona: defaults to a first-letter avatar until edited later.

Data output:

- Built-in persona entries output the public `persona_selector` object:

  ```json
  { "kind": "built_in", "persona_id": "you_know_who" }
  ```

- Managed persona entries output the public `persona_selector` object:

  ```json
  {
    "kind": "managed",
    "persona_id": "example_persona",
    "version": "draft.v1",
    "revision": 1
  }
  ```

The mobile UI must not construct internal encoded selectors such as
`persona@version#revision`.

## Persona Creation Seam

The add-persona wheel entry navigates to a later persona creation page. P3a does
not design or implement the full creation workflow.

The future page must support two entry modes:

- LLM-guided creation: the user gives a short description. The system follows a
  Nuwa-skill-centered flow to generate required files and insert the persona.
  The UI must show an explicit token-cost warning before model execution.
- Manual insertion: the user provides the required files the system needs to
  insert a persona without LLM generation.

Navigation seam:

- `PersonaRadialSelector` emits `add_persona`.
- Chat shell opens `PersonaCreationEntry`.
- `PersonaCreationEntry` returns either a public-safe managed persona selector
  candidate or a cancelled state.
- Runtime chat requests still consume only the public `persona_selector`
  contract after insertion.

Data seam:

- The creation page may collect descriptions or files.
- The chat shell receives only reviewed/selectable persona metadata needed to
  form a public selector.
- Raw doctrine, registry ledger, projection internals, materialized artifact
  paths, and internal encoded selector strings must not enter selector-facing
  UI state.

## Settings Drawer

Settings opens from the screen right edge by swiping left. This preserves the
single-chat primary surface while supporting open-source user-owned runtime
configuration.

Drawer contents:

- API key entry.
- Model selection.
- Endpoint/provider preferences.
- Local/cloud mode.
- API base URL if local development still needs it.
- Clear/delete controls for locally stored user configuration.

Interaction:

- Swipe left from the right edge opens the drawer.
- Swipe right or tap outside closes it.
- Settings changes apply to future requests, not messages already sent.
- The drawer should be structurally independent from chat rendering so it can be
  redesigned without changing request payload construction.

## API Key Security UX

API keys are user-owned local secrets.

Required warning copy concepts:

- Keys are supplied by the user for their own runtime.
- Keys must not be committed to the repository.
- Keys must not be uploaded in diagnostics, screenshots, issue templates, logs,
  crash reports, or support bundles.
- Local/cloud mode changes where requests are executed and should be shown
  clearly before use.

Required controls:

- Mask key values by default.
- Provide reveal/hide toggle.
- Provide clear/delete affordance.
- Avoid printing keys in app logs, error messages, analytics, metadata screens,
  or unhandled error UI.
- Do not store keys in repo files, bundled assets, or example artifacts.

## Persona Selector Contract Preservation

The UI outputs P2 public selector objects only:

- Built-in: `kind`, `persona_id`.
- Managed: `kind`, `persona_id`, `version`, `revision`.

The visual V1 default is `You know who`, so it sends
`{ "kind": "built_in", "persona_id": "you_know_who" }`. Only a true
API-default/unselected state sends no selector, and that state must not present
itself visually as `You know who`.

Version/revision should not be exposed in normal persona selection UI if a
catalog entry already has exact reviewed identity metadata. They may appear only
in advanced/manual mode where the user is explicitly editing managed selector
identity. Even then, the output remains the public object, not encoded syntax.

No cross-version promotion, fuzzy selector matching, or alias auto-promotion is
defined for V1.

## Future Visual Redesign Boundaries

This brief defines behavior and integration seams only.

Do not treat the following as final:

- Avatar art style.
- Radial wheel visual design.
- Message bubble visual language.
- Settings drawer layout.
- Persona creation page copy.
- Empty-state copy.
- Color system, typography, or motion style.

Next implementation should use replaceable components and keep selector state,
payload construction, and settings storage separate from presentation.

## Recommended Next Milestone

Recommended next slice: `p3b_single_chat_mobile_shell_scaffold`.

Cut:

- Remove Team, Species, and Evidence tabs from the V1 primary mobile navigation.
- Convert current Chat screen into the single app shell.
- Preserve current API client and public `persona_selector` helper.
- Add a minimal long-press avatar selector using placeholder avatar components.
- Add a right-edge settings drawer with local-only configuration controls.
- Keep Team Analyze and Species API calls available only behind Agent/internal
  tool paths or development-only code, not as primary user navigation.
- Run mobile typecheck and focused backend persona/API regression tests.
