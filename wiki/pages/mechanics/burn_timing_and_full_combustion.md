---
title: "Burn Timing And Full Combustion"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_verified_burn_full_combustion_timing.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
  - "data/reference/luoke_world_type_database_v2.json"
last_reviewed: "2026-04-21"
reviewed_by: "user_confirmed_burn_timing"
human_confirmed:
  - "灼烧正常结算为每层 2% 最大生命值的火系伤害, 受属性克制影响"
  - "充分燃烧触发的额外灼烧伤害也按同一火系伤害逻辑理解"
  - "充分燃烧的即时灼烧伤害是额外结算, 不减层"
  - "回合结束仍会正常结算一次灼烧, 且该次正常减层"
persona_free: true
---

# Burn Timing And Full Combustion

## Claim

`灼烧` is a per-target damage-over-time status, not a mark. It creates two
different timing questions that the advisor must keep separate:

- the normal end-of-round burn resolution
- extra burn-damage triggers created by specific skills such as `充分燃烧`

`充分燃烧` should be modeled as an extra immediate burn-damage trigger that
does not itself consume burn stacks. The normal end-of-round burn resolution
still happens later and that normal round-end resolution does reduce stacks.

Current reviewed thread correction also treats normal burn as:

- `2%` max-HP damage per stack
- fire-type damage rather than typeless chip
- subject to type interaction
- the extra burn trigger from `充分燃烧` should be read under that same
  fire-damage model

## Strategic Use

For team reasoning, the advisor should ask:

- Is the burn team trying to win through repeated round-end attrition, or
  through amplified immediate conversion with `充分燃烧`?
- Does the team have a reliable way to stack burn before spending a turn on
  `充分燃烧`?
- Is the target likely to leave before the round-end burn trigger, making an
  immediate burn trigger more valuable?
- Does the team contain effects that change burn decay, such as `煤渣草`?
- Is the current plan relying on immediate lethal damage, or on preserving
  stacks into later turns?

## Core Timing Model

Current reviewed B-layer model:

1. Burn stacks exist on a specific target.
2. At normal round end, burn deals `2%` max-HP fire damage per stack.
3. Type interaction still applies to that round-end burn damage.
4. After the normal damage step, burn decays stacks.
5. `充分燃烧` first doubles the target's existing burn stacks.
6. `充分燃烧` then triggers one extra immediate burn-damage instance.
7. That immediate trigger is read under the same fire-damage model.
8. That extra immediate burn-damage instance does not itself reduce burn stacks.
9. Later in the same round, the normal round-end burn step still occurs.
10. The normal round-end burn step is the step that applies the usual stack
   decay.

## Evidence

The current A-layer move text for `充分燃烧` in
`data/runtime/battle_dex.sqlite` is:

`使敌方身上的灼烧翻倍,并触发1次灼烧伤害。`

This proves the move doubles burn and triggers an additional burn-damage event,
but the A-layer text alone does not specify whether that extra trigger consumes
stacks.

The early 18-type tutorial frames fire around `灼烧`, but its numeric and timing
detail is not stable enough to serve as final authority.

The current thread adds an explicit user confirmation on 2026-04-21:

- normal burn damage is `2%` max HP per stack
- burn damage is fire-type damage and is affected by type interaction
- the extra burn trigger from `充分燃烧` follows that same damage model
- the burn damage triggered by `充分燃烧` is extra and does not reduce stacks
- the normal end-of-round burn still resolves later
- that normal end-of-round burn step still reduces stacks

This user confirmation resolves the specific ambiguity that remained after the
database and public glossary checks.

## Confidence

`provisional`.

High confidence:

- normal burn damage is `2%` max HP per stack
- burn damage is fire-type damage and thus not typeless
- type interaction applies to normal burn damage
- the extra burn trigger from `充分燃烧` follows that same damage model
- `充分燃烧` doubles existing burn stacks
- `充分燃烧` triggers an extra immediate burn-damage instance
- that extra immediate burn-damage instance does not itself consume stacks
- the normal end-of-round burn still resolves separately
- the normal end-of-round burn step is the one that applies normal stack decay

Medium confidence:

- interaction ordering against simultaneous poison, freeze, weather, fainting,
  and revival checks still needs broader timing coverage

## A-Layer Boundary

This page does not define executable battle-engine timing.

A-layer modeling should eventually own:

- canonical burn status definition
- exact damage formula
- exact decay formula
- exact hook order for immediate burn triggers versus round-end burn
- interactions with traits such as `煤渣草`
- interactions with leave-field, faint, revive, and other round-end effects

## Known Failure Modes

- Treating the extra burn damage from `充分燃烧` as the same object as the
  normal round-end burn tick.
- Assuming `充分燃烧` immediately reduces stacks just because it triggers burn
  damage.
- Forgetting that the normal round-end burn still occurs after `充分燃烧` in the
  same round.
- Recommending `充分燃烧` as a value play when the target is about to switch and
  the team has no way to preserve burn pressure.
- Ignoring `煤渣草` or similar future effects that can rewrite burn decay.
