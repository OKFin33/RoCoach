# Battle Wiki Lint Rules

The wiki linter must enforce these rules before compiled exports are trusted.

## Required Metadata

Fail if a reviewed page is missing:

- `title`
- `content_class`
- `status`
- `confidence`
- `sources`
- `last_reviewed`
- `persona_free: true`

## Cross-Game Contamination

Fail on unapproved cross-game mechanic migration.

Terms such as `Pokemon`, `宝可梦`, `STAB`, `check`, `counter`, `stall`,
`balance`, and `offense` require explicit Roco-specific framing when used.

Allowed use:

```text
This is an approximate analysis term, redefined here for Roco.
```

Forbidden use:

```text
Imported mechanic semantics without Roco evidence.
```

## Persona Contamination

Fail on default B pages that introduce:

- Enzo identity
- persona voice
- character roleplay framing
- persona-specific taste as generic truth

## A-Layer Duplication

Warn or fail when pages include hand-maintained exact fact tables for:

- species stats
- move power
- move energy
- ability text
- type-chart data

Exact facts must be referenced through A-layer sources.
