---
title: "Marks And Persistence"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-07_bilibili_mark_tutorial_screenshot.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
  - "wiki/cache/PVP扫盲0419/NoteGPT_一口气让你彻底学会精灵对战！PVP扫盲，新手必看！.txt"
  - "docs/manual_battle_data_supplement_2026-04-14.md"
a_layer_refs:
  - "docs/manual_battle_data_supplement_2026-04-14.md"
  - "data/reference/luoke_world_type_database_v2.json"
last_reviewed: "2026-04-20"
reviewed_by: "user_confirmed_ocr_corrections"
persona_free: true
---

# Marks And Persistence

## Claim

Marks are persistent battle attachments that should be modeled separately from
ordinary buffs, debuffs, weather, and skill effects.

The advisor should reason about marks as long-horizon pressure or long-horizon
resource support:

- positive marks create resource or damage windows for the marked side
- negative marks create persistent pressure that switching alone does not solve
- mark replacement and mark clearing create a dedicated layer of turn-by-turn
  counterplay

## Strategic Use

Marks matter because they survive the basic rotation patterns that clear many
ordinary effects. This makes them one of the main tools for converting early
setup into later advantage.

For team reasoning, the advisor should ask:

- What mark is this team trying to establish?
- Is the mark a resource engine, a damage engine, a speed-control tool, or a
  delayed burst condition?
- Which member creates the mark reliably?
- Which member converts the mark into pressure?
- What happens if the opponent clears, steals, replaces, or ignores the mark?
- Does the team have enough tempo to spend a turn creating the mark?

## Known Mark Registry

This registry is provisional. It is suitable for B-layer reasoning, but exact
execution semantics still need A-layer representation before engine use.

| Mark | Likely Sign | Direct Skill In Screenshot | Skill Type / Cost | Primary Effect |
|---|---|---|---|---|
| 棘刺印记 | negative | 棘刺 | 普通 / 2 | When the marked fielded spirit leaves, the entering replacement loses 6% HP per layer. |
| 光合印记 | positive | 光合作用 | 草系 / 4 | At end of round, gain 1 energy per layer. |
| 蓄势印记 | positive | 蓄势待发 | 地系 / 4 | All attack-skill power +30%; energy cost +1. |
| 龙噬印记 | positive | 龙威 | 龙系 / 5 | After using a 3-cost skill and dealing damage, gain physical and magical attack +30%. |
| 中毒印记 | negative | 疫病吐息 | 毒系 / 3 | At end of round, deal poison-type damage equal to 3% HP per layer. |
| 降灵印记 | negative | 降灵 | 幽系 / 2 | When the marked fielded spirit leaves, the entering replacement loses 1 energy per layer. |
| 攻击印记 | positive | 主场优势 | 普通 / 3 | All skill power +10%. |
| 湿润印记 | positive | 打湿 | 水系 / 4 | All skill energy cost -1 per layer. |
| 减速印记 | negative | 速冻 | 冰系 / 4 | Speed -10 per layer; `速冻` gives 2 layers. |
| 蓄电印记 | positive | 增压电池 | 电系 / 2 | Attack skills gain 迸发: current power +10. |
| 风起印记 | positive | 风起 | 翼系 / 4 | When attacking first, current skill power +20%. |
| 星陨印记 | negative | 冥想 | 幻系 / 4 | When a non-幻系 skill attacks the marked spirit, consume all layers and deal extra 幻系 damage. |

## Starfall Boundary

Do not collapse `冥想` and `星陨印记`.

`冥想` is the direct skill shown in the screenshot. Its skill effect includes:

- damage taken -80%
- response to attack
- if the response condition is met, the enemy gains 2 layers of 星陨印记

`星陨印记` is the mark created by that skill. Its mark effect is triggered by a
non-幻系 skill attacking the marked spirit. The trigger is based on skill type,
not on the attacker's species type.

The current battle-dex also stores `冥想` as a defense move with the effect text
`减伤80%,应对攻击:敌方获得2层星陨印记。` This should be parsed as a conditional
response package, not as an unconditional mark application.

## Evidence

The 2026-04-07 mark screenshot lists 12 marks and direct mark-producing skills,
including skill type and cost. The user corrected OCR and interpretation in the
current thread on 2026-04-20.

The 2026-04-19 PvP beginner sweep independently supports several global mark
claims: marks differ from ordinary buffs/debuffs, marks can be positive or
negative, one positive and one negative mark can coexist, positive marks can
replace positive marks, and marks cannot be removed merely by switching.

The manual supplement already confirms `湿润印记` as an effect name rather than
a canonical move name, confirms its energy-cost reduction, and places mark
semantics in a later mechanics/Agent layer instead of first-pass raw move schema.

## Confidence

`provisional`.

High confidence:

- mark persistence through switching
- one positive and one negative mark limit
- `湿润印记` cost reduction
- `光合印记` end-of-round energy gain
- `减速印记` speed reduction per layer

Medium confidence:

- exact scaling for every mark by layer
- timing of end-of-round effects against weather, poison, burn, freeze, and
  fainting checks
- whether all likely-positive and likely-negative signs listed above are final
  for replacement-limit purposes

## A-Layer Boundary

This page does not define executable mark mechanics.

A future A-layer mark registry should own:

- canonical mark names
- positive/negative classification
- layer limit, stacking, replacement, and clear rules
- exact timing hooks
- exact damage formulas
- exact skill-to-mark creation mappings
- trait/form/leader-effect sources of marks
- interactions with weather, ordinary buffs/debuffs, and switching

The screenshot's direct skills are not exhaustive. Some species traits or other
effects may also create marks.

## Known Failure Modes

- Treating a direct mark-producing skill as the only possible source of a mark.
- Treating `冥想`'s damage reduction and response as the intrinsic effect of
  星陨印记.
- Making 星陨印记 depend on the attacker's species type instead of the attacking
  skill type.
- Forgetting that 棘刺印记 and 降灵印记 punish replacement after the marked
  fielded spirit leaves, and that the punishment stacks by layer.
- Recommending a mark-centered team without checking whether it can protect its
  mark engine from clear/steal/replacement counterplay.
- Treating all mark claims as patch-stable in an early-release metagame.

## Draft Review Questions

- Are there exactly 12 current marks, or does the game expose additional marks
  through traits/forms not shown in the tutorial table?
- What are the canonical Chinese names for all marks in battle logs?
- Which skills clear, steal, replace, convert, or protect marks?
- What is the exact timing order for end-of-round energy, damage, weather, and
  mark triggers?
- Should mark logic be represented as a standalone A-layer table or attached to
  move/effect ontology?
