# Roco Battle Wiki

This directory is the root B-layer doctrine surface for Roco.

It is for generic `洛克王国：世界` PvP battle doctrine:

- mechanics interpretation
- team-building methodology
- role and archetype reasoning
- tactical cases
- recommendation taste
- counterexamples
- confidence and provenance discipline

It is not the A-layer fact database.

Exact species, move, ability, type-chart, and provenance facts belong to:

```text
data/
```

System architecture and contracts belong to:

```text
specs/
```

## Layer Boundary

```text
A = Engine / SQLite battle-dex / structured facts
B = generic Battle Wiki doctrine
Persona = optional downstream presentation and style overlay
```

Default B doctrine must be persona-free.

## Directory Map

```text
wiki/
  README.md
  meta/
  raw/
  pages/
  schema/
  compiled/
```

## Current Architecture Spec

See:

```text
../docs/specs/battle_wiki_architecture_spec.md
```

## Hard Rules

- Roco is `洛克王国：世界`, not Pokemon.
- Do not import cross-game mechanics without explicit Roco evidence and review.
- Do not duplicate A-layer exact facts as wiki authority.
- Do not put Enzo or any other persona doctrine into default B.
- Do not commit unsafe raw sources.
