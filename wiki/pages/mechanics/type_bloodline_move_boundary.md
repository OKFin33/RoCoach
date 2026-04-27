---
title: "Type, Bloodline, And Move Boundary"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-03-23_bilibili_basic_pvp_type_bloodline_move_categories.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
a_layer_refs:
  - "docs/domain_primer.md"
  - "docs/combat_ontology.md"
  - "data/runtime/battle_dex.sqlite"
  - "specs/battle_dex_sqlite_schema_v1.sql"
last_reviewed: "2026-04-20"
reviewed_by: "first_wiki_closure"
persona_free: true
---

# Type, Bloodline, And Move Boundary

## Claim

Roco PvP reasoning must keep these concepts separate:

```text
species type / 系别
bloodline / 血脉
move type / 技能属性
```

The advisor must not collapse them into one generic "attribute" field.

## Strategic Use

This boundary prevents three common reasoning errors:

- treating bloodline as if it changes a species' defensive type profile
- treating the attacker's species type as the direct source of restraint
- ignoring that a move or resonance action can pressure a target through a
  different type channel than the user's species identity suggests

In team advice, this means the advisor should distinguish:

- what the species can safely receive
- what the species can threaten with selected moves
- what bloodline-enabled tools or resonance actions may add
- what the current A-layer facts actually confirm

## Evidence

The 2026-03-23 beginner PvP tutorial states that bloodline is separate from a
species' own type and should not be read as changing that species into a
dual-type defensive profile.

The 2026-04-02 battle-system tutorial independently states that defensive type
is fixed by species `系别`, while bloodline affects available tools and
`愿力冲击`-style type behavior.

Project domain documents already require avoiding imported Pokemon-like schema
assumptions and keeping Roco-evidenced fields separate.

## Confidence

`provisional`.

The high-level separation is strongly supported by two early tutorial sources
and by existing project ontology discipline. Exact implementation details, such
as bloodline defaults, resonance type derivation, and move access rules, still
require A-layer validation.

## A-Layer Boundary

This page does not define exact type charts, species types, bloodline access,
move pools, or resonance rules.

Exact facts must come from:

```text
data/runtime/battle_dex.sqlite
data/reference/
data/manual_supplements/
specs/battle_dex_sqlite_schema_v1.sql
```

or future approved battle-dex API/tool contracts.

## Known Failure Modes

- Overstating a bloodline as a defensive type.
- Recommending a matchup based on species label while ignoring selected move
  type.
- Treating early tutorial examples as permanent exact mechanics.
- Do not import Pokemon dual-type intuition into Roco without Roco evidence.
- Using `愿力冲击` claims without checking current resonance rules.

## Draft Review Questions

- Is `bloodline does not alter defensive type` confirmed enough for reviewed
  doctrine?
- Is `move type against target species type` the correct phrasing for Roco
  restraint calculation?
- Which A-layer table or API should expose bloodline, move access, and resonance
  behavior?
- Should resonance type derivation live on this page or a dedicated
  `resonance_magic.md` page?
