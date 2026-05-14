# Data Mapping

## Current Available Backend Fields

Use only these fields for production rendering until a new contract lands:

```ts
response.answer
response.persona?.rendered_answer
response.presentation?.reply
response.presentation?.why
response.presentation?.visible_warnings
response.presentation?.detail_sections
response.presentation?.followup_prompts
```

Preferred display priority:

```ts
visibleText =
  response.persona?.rendered_answer
  ?? response.presentation?.reply
  ?? response.answer
```

## Basic Agent Reply

Bubble text:

```text
response.persona?.rendered_answer
  OR response.presentation?.reply
  OR response.answer
```

If `persona.sanitized === true`, show a small non-blocking status note only when needed:

```text
已安全调整人格表达
```

Do not expose resolver/materialization/internal selector details.

## Generic AnalysisCard Mapping

Current backend can support a generic readable card, but not the exact mock strategy card.

Mapping:

```text
Card title <- fixed by UI based on response.analysis_type:
  team_analysis -> "分析摘要"
  species_analysis -> "精灵判断"
  unsupported/refused/failed -> no analysis card unless needed for error detail
  default -> "Roco 摘要"

Card summary <- response.presentation?.why

Warnings <- response.presentation?.visible_warnings

Sections <- public-safe response.presentation?.detail_sections
  section.id <- section.section_id
  section.label <- section.label
  section.content <- section.content
  section.defaultExpanded <- section.default_visibility === "expanded"

Followups <- response.presentation?.followup_prompts
```

Suppress these `content_kind` values in V1 public UI:

```text
raw
tool_trace
```

Allowed by default:

```text
analytical_base
evidence
confidence
followup
```

If backend later adds an explicit public-safe/sanitized flag per section, this rule may be revisited.

## Mock Strategy Card Mapping

The Web prototype card shows:

```text
策略摘要
核心问题
推荐调整
风险点
查看详细分析
```

Current backend does not provide stable fields for these rows.

Do not map them as if they exist.

Possible temporary mapping for UI preview only:

```text
策略摘要标题 <- fixed copy "分析摘要"
核心问题 <- not available
推荐调整 <- not available
风险点 <- visible_warnings[0]?.message, but only as warning, not as a strategic row
查看详细分析 <- detail_sections collapsed/expanded toggle, not followup_prompts
```

Production rule:

- If the product wants this exact card shape, define a public `ui_artifacts` or `analysis_summary` contract first.
- Do not parse natural-language `reply` text to extract "core issue", "recommendation", or "risk".
- Do not consume raw `tool_results.payload` directly for production UI cards.

## Persona Selector

True API-default/unselected state only:

```ts
persona_selector: undefined
```

V1 visual default exception:

- The UI default selected persona is `You know who`.
- `You know who` is the public-safe outward codename for the Enzo-derived
  distilled persona layer.
- It comes from the internal Enzo doctrine sample after abstraction and IP
  sanitization. Public UI must not claim this is Enzo/恩佐, an official
  character, official lore, official dialogue, or official art.
- Therefore initial chat state should not be treated as "no persona selected".
- Initial state should use the built-in selector for `you_know_who` unless backend default is explicitly verified to match it.
- Only omit `persona_selector` for a true API-default/unselected state that does not visually show the black-cloaked persona.

Built-in:

```json
{
  "kind": "built_in",
  "persona_id": "you_know_who"
}
```

Legacy selector alias:

```json
{
  "kind": "built_in",
  "persona_id": "obsidian_tactical_coach"
}
```

The legacy alias should be accepted for compatibility but should not be emitted
by new mobile UI.

Default AI assistant:

```json
{
  "kind": "built_in",
  "persona_id": "lattice_support_coach"
}
```

Managed later:

```json
{
  "kind": "managed",
  "persona_id": "xxx",
  "version": "draft.v1",
  "revision": 1
}
```

UI must not build internal encoded selectors.

### UI Persona Mapping

The UI labels/option ids are product-facing and do not equal backend built-in `persona_id`.

Use this mapping:

| UI label | UI option id | Backend `persona_selector` |
| --- | --- | --- |
| `You know who` | `you_know_who` | `{ "kind": "built_in", "persona_id": "you_know_who" }` |
| `默认AI助手` | `ai_assistant` | `{ "kind": "built_in", "persona_id": "lattice_support_coach" }` |
| `添加人格` | `add_persona` | no selector; opens reserved persona creation seam |

Rules:

- `you_know_who` is intentionally both the UI option id and backend runtime id
  for the default distilled persona.
- Never send UI-only ids such as `ai_assistant` or `add_persona` to the backend.
- Store UI id locally only for visual selection state.
- Store/send backend selector separately.
- If backend built-in ids change, update this table and the mobile mapping function together.

## Runtime Settings

Current mobile engineering path:

- `mobile/src/runtime/runtimeSettings.ts`
- provider key: SecureStore key `roco.runtime.provider_key.v1`
- non-secret runtime settings: SecureStore key `roco.runtime.non_secret.v1`
- headers:
  - `X-Roco-Provider-Key`
  - `X-Roco-Provider-Base-Url`
  - `X-Roco-Model`
  - `X-Roco-Runtime-Mode`

UI copy must match this unless product explicitly changes persistence policy.

## Not Available Yet

No current backend field provides:

- typed strategy rows
- species sticker/icon URL
- damage range card
- team resistance matrix
- card-level action schema
- branch/history metadata for rewritten messages
- server-side delete semantics

See `new_backend_contract_needed.md`.
