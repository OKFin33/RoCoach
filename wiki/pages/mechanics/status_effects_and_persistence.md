---
title: "Status Effects And Persistence"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
  - "wiki/pages/mechanics/burn_timing_and_full_combustion.md"
  - "wiki/pages/mechanics/weather_and_field_effects.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
  - "data/reference/luoke_world_type_database_v2.json"
last_reviewed: "2026-04-21"
reviewed_by: "mechanism_completion_pass"
human_confirmed:
  - "冻结判定条件可抽象为: 每当 frozen_hp 或 current_hp 变化时, 若 current_hp <= frozen_hp, 立即力竭"
  - "寄生当前版本为扣除对方6%最大生命值并回复给自己, 不是草系伤害"
  - "中毒和中毒印记均为3%毒系伤害, 但中毒印记不按普通毒免逻辑处理"
persona_free: true
---

# Status Effects And Persistence

## Claim

Ordinary status effects should not be collapsed into one bucket. For advisor
reasoning, the key distinction is:

- whether the effect is attached to the individual spirit
- whether it persists through switching
- whether it is typed damage or untyped chip
- whether it checks defeat only at round end or on every relevant state change

Current reviewed scope for this page covers:

- `冻结`
- `中毒`
- `寄生`

`灼烧` has a dedicated reviewed page because its timing and `充分燃烧`
interaction already warranted standalone treatment.

## Strategic Use

For recommendations and explanations, the advisor should ask:

- does the status survive switching on the same individual
- does the opponent have type-based immunity to the ordinary status form
- is the status meant to pressure over time, force specific switches, or create
  a hard threshold for immediate defeat
- is the user actually asking about a status mark variant rather than the
  ordinary status itself

## Freeze

Current reviewed working model:

- each layer of freeze corresponds to `5%` of max HP as frozen HP pressure
- every time `frozen_hp` or `current_hp` changes, the game checks the defeat
  condition again
- defeat condition: `current_hp <= frozen_hp`
- ice spirits are immune to freeze
- switching preserves freeze on the same individual spirit, but the next spirit
  does not inherit it

This means freeze is an individual persistent state, not a field-wide inherited
status.

## Poison

Current reviewed working model:

- ordinary poison deals `3%` poison-type damage per stack
- ordinary poison is distinct from `中毒印记`
- `中毒印记` also deals `3%` poison-type damage
- poison-mark damage does not follow the same ordinary poison-immunity logic as
  standard poison

This distinction matters because many user questions casually say "poison" when
they really mean either ordinary poison or poison mark pressure.

## Leech / 寄生

Current reviewed working model:

- at round end, `寄生` drains `6%` of the target's max HP
- the drained amount is healed to the user
- this is not treated as grass-type damage

For advice, this means grass sustain can remain strategically relevant even when
type-based damage intuition would otherwise mislead the reader.

## Evidence

The 18-type tutorial and later current-thread review together support:

- freeze as a persistent individual state with a max-HP threshold check
- poison as an ordinary typed damage-over-time state distinct from poison mark
- leech as fixed max-HP drain-and-heal rather than a typed grass-damage packet

The current thread adds the cleaner engineering abstraction for freeze:

`whenever frozen_hp or current_hp changes, re-check; if current_hp <= frozen_hp,
the spirit is exhausted immediately`

## Confidence

`provisional`.

High confidence:

- freeze uses a threshold check rather than only a one-time round-end check
- poison and poison mark should not be collapsed
- leech currently drains 6% max HP and heals the user for the same amount

Medium confidence:

- exact ordering between ordinary status damage and every future edge-case
  mechanic
- whether any future version introduces exceptions to current poison/freeze
  handling

## A-Layer Boundary

This page does not define executable battle hooks.

A-layer formalization would likely need fields such as:

- status_kind
- persists_on_same_individual_switch
- typed_damage_flag
- threshold_check_hook
- immunity_model
- mark_variant_link

## Known Failure Modes

- treating freeze as if it passes to the next switched-in spirit
- treating poison and poison mark as identical
- treating leech as grass-type damage
- assuming all status effects resolve only at round end

