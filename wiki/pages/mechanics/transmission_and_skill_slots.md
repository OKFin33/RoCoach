---
title: "Transmission And Skill Slots"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "user_mechanism_batch_v2"
human_confirmed:
  - "传动游戏内描述: 回合开始时, 带有传动X的技能会向下移动X个位置, 该效果可叠加"
persona_free: true
---

# Transmission And Skill Slots

## Claim

`传动` is a skill-slot movement mechanism, not a normal buff/debuff.

Current-version reviewed working model:

- at round start, a skill carrying `传动X` moves downward by `X` positions
- skill slots form a 4-slot cycle
- overflow wraps around, so slot `5` is slot `1`
- if multiple carried skills have transmission, movement resolves step by step
  rather than as one simultaneous collapse

## Strategic Use

For advisor reasoning, `传动` means the skill bar itself is part of the battle
engine.

The advisor should ask:

- which slot does the team need to preserve or rotate into a premium position
- whether a species wants to move a payoff move into a cheaper/boosted/support
  position
- whether multiple transmission effects create a reliable loop or a fragile one
- whether the user's current explanation depends on exact slot order or only on
  the general fact that slots are being rotated

## Evidence

The 18-type tutorial treats `传动` as the defining machine-type mechanism and
describes it through skill-position movement and position-dependent payoff.

The current thread adds a more explicit user-confirmed current-version wording:

`回合开始时，带有“传动X”的技能会向下移动X个位置，该效果可叠加。`

The user also supplied a worked `传动1` multi-skill example that implies:

- cyclic 4-slot wrapping
- sequential resolution when more than one carried skill has transmission

These points are sufficient for a first reviewed provisional page even though
the full family of transmission variants is not yet modeled in A-layer fields.

## Confidence

`provisional`.

High confidence:

- transmission moves skills by slot at round start
- `传动X` means moving downward by `X` positions
- the effect can stack
- the slot system is cyclic

Medium confidence:

- the exact generic rule for every future/current transmission variant
- whether some traits or special skills rewrite the default movement order

## A-Layer Boundary

This page does not define executable slot-order code.

If transmission is formalized into A-layer later, the model should own fields
such as:

- slot_count
- transmission_delta
- transmission_timing
- multi_transmission_resolution_order
- trait_rewrite_flags

## Known Failure Modes

- treating transmission as a damage buff instead of slot movement
- resolving multiple transmission skills as simultaneous when the intended order
  matters
- forgetting cyclic wraparound
- describing a species as slot-independent when its payoff clearly depends on
  slot rotation

