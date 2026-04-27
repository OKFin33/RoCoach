# Managed Persona Public Selector Contract

## Purpose

Expose reviewed managed personas through a product-facing API selector without
leaking internal registry, projection, materialization, or encoded resolver
syntax.

This contract is backend/API only. Mobile UX integration is deferred to P2b.

## Request Shape

`/chat` and `/team/analyze` accept an optional `persona_selector` object:

```json
{
  "kind": "managed",
  "persona_id": "public_safe_runtime_persona",
  "version": "draft.v1",
  "revision": 1
}
```

For built-in personas:

```json
{
  "kind": "built_in",
  "persona_id": "obsidian_tactical_coach"
}
```

Backward compatibility:

- Existing `persona_id` remains accepted for current clients.
- If both `persona_selector` and `persona_id` are present, `persona_selector`
  takes precedence.
- Internal encoded selectors such as `persona@version#revision` are not the
  public contract. They remain implementation detail / legacy local-run
  compatibility only.

## Selection Rules

- `kind=managed` requires exact `persona_id`, `version`, and `revision`.
- `kind=built_in` uses exact built-in `persona_id`.
- No cross-version promotion.
- No fuzzy matching.
- No alias auto-promotion.
- Missing, malformed, unsafe, unsupported, or unavailable managed personas fall
  back to the built-in public-safe default.
- Public API runtime uses public-safe materialized profile artifacts only.

## Response Invariants

- `AgentResponse.answer` remains canonical.
- `response.presentation.reply` remains canonical and equal to the user-facing
  answer.
- Persona selection may only affect `response.persona` metadata and
  `response.persona.rendered_answer`.
- Fallback/sanitization must not expose local materialization paths, environment
  variables, secrets, or artifact contents.

## Non-Goals

- No mobile UI in this milestone.
- No managed persona creation workflow.
- No Nexus original-design adapter.
- No public release policy changes.
- No raw doctrine, activation, projection, or registry ledger access from API
  selector code.

## P2b Mobile Handoff

Mobile should consume `persona_selector` instead of constructing internal
encoded strings. Minimum UI data needed:

- `kind`: `built_in` or `managed`
- `persona_id`
- for managed personas only: `version` and `revision`

The backend response schema is unchanged; mobile should continue reading
`response.persona` for effective persona metadata and rendered answer.
