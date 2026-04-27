---
title: "Response Counterplay"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "data/runtime/battle_dex.sqlite"
  - "docs/research/luoke_world_pvp_domain_primer_v2.md"
  - "wiki/pages/mechanics/marks_and_persistence.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
  - "specs/battle_dex_sqlite_schema_v1.sql"
  - "data/reference/luoke_world_type_database_v2.json"
last_reviewed: "2026-04-20"
reviewed_by: "systematic_database_check"
persona_free: true
---

# Response Counterplay

## Claim

Many Roco skills are conditional packages, not single flat effects. The advisor
must parse `应对X: Y` as:

```text
base effect
response condition: opponent uses X category
response-success effect: Y
```

The response-success effect should not be applied when the response condition
fails.

## Strategic Use

Response clauses are one of the main sources of turn-level skill expression.
They can convert a defensive turn into resource gain, mark creation, debuff,
forced switch, damage reflection, cooldown reduction, or setup.

For recommendations, the advisor should distinguish:

- what the move does unconditionally
- what it is trying to answer
- what extra payoff happens only on successful response
- whether the response payoff is worth the energy, cooldown, and tempo cost
- whether the opponent can avoid the response by choosing another category

## Parsing Rule

For any `effect_text` containing `应对攻击`, `应对状态`, or `应对防御`:

- `应对攻击` triggers only when the opponent uses an attack skill.
- `应对状态` triggers only when the opponent uses a status skill.
- `应对防御` triggers only when the opponent uses a defense skill.
- Text before the response clause remains the base effect unless the effect says
  `改为`, which may replace the base outcome under the response condition.
- Text after the response clause is conditional response payoff.
- `打断` is an additional response payoff, not automatically implied by every
  response.

## Examples

From the current battle-dex move table, there are many response-bearing moves:
117 moves contain `应对` in `effect_text`, distributed as 46 defense, 31 physical
attack, 26 status, and 14 magical attack moves.

Representative patterns:

| Move | Category | Effect Pattern | Advisor Interpretation |
|---|---|---|---|
| 冥想 | 防御 | `减伤80%,应对攻击:敌方获得2层星陨印记。` | Base: defense and 80% damage reduction. If the opponent uses an attack skill, response succeeds and the opponent gains 2 layers of 星陨印记. |
| 壁垒 | 防御 | `减伤90%,应对攻击:防御技能冷却-1。` | Base: high mitigation. Response success reduces defense-skill cooldown. |
| 报复 | 防御 | `减伤70%,应对攻击:敌方失去3能量。` | Base: mitigation. Response success converts the defended attack into enemy energy loss. |
| 水刃 | 物攻 | `造成物伤,应对状态:本技能能耗永久-4。` | Base: physical damage. If it catches a status skill, the move gains permanent energy-cost reduction. |
| 瞬间零度 | 状态 | `本回合敌方使用的技能能耗+3,应对防御:改为全技能能耗+3。` | Base: current enemy skill cost pressure. If it catches defense, the outcome changes into all-skill cost pressure. |
| 天火 | 状态 | `敌方获得10层灼烧,应对防御:改为获得30层。` | Base: burn stacking. If it catches defense, the burn result is replaced by a stronger burn stack. |

## Evidence

The current SQLite battle-dex stores move fields as raw native game data:

```text
move_name
category_raw
move_type
energy_cost
power
effect_text
```

A direct database check on 2026-04-20 found 117 moves whose `effect_text`
contains `应对`.

The domain primer already treats response as a core Roco-native mechanism and
states that successful response can trigger extra effects while not every
response necessarily interrupts the opponent.

## Confidence

`provisional`.

High confidence:

- `应对X: Y` should be treated as conditional structure.
- `冥想` should be read as a defense move with 80% damage reduction and a
  conditional attack-response payoff that gives 2 layers of 星陨印记.
- Not every response includes interruption.

Medium confidence:

- exact timing and priority for every response subtype
- interaction order between response payoff, damage, mark trigger, switching,
  and fainting
- whether all `改为` texts can be mechanically parsed by a simple replacement
  rule

## A-Layer Boundary

This page defines advisor interpretation, not executable battle resolution.

A-layer modeling should eventually split `effect_text` into structured fields:

```text
base_effects
response_condition.category
response_success_effects
replacement_semantics
interrupt_flag
timing_hook
```

Until then, the advisor may reason over text but must preserve uncertainty for
edge cases.

## Known Failure Modes

- Applying response-success effects even when the opponent did not use the
  required category.
- Treating every response as interruption.
- Treating base defensive mitigation as if it requires successful response.
- Treating a response-created mark as the same thing as the response skill's
  own defensive effect.
- Ignoring `改为`, where response success may replace the base result rather
  than simply add to it.

## Draft Review Questions

- Which response effects trigger before damage, after damage, or at end of
  round?
- Which response effects interrupt the target skill, and which only add payoff?
- Should the first structured parser be regex-based for common cases or
  LLM-assisted with human review for rare texts?
- Should response parsing live in battle-dex importer, an Agent supplement, or
  both?
