---
title: "Energy Actions And Focus"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/raw/source_notes/2026-03-23_bilibili_basic_pvp_type_bloodline_move_categories.md"
  - "docs/research/luoke_world_pvp_domain_primer_v2.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "mechanism_completion_pass"
human_confirmed:
  - "聚能恢复5能量"
  - "聚能属于状态动作"
  - "聚能被打断则失效; 被应对不等于被打断"
persona_free: true
---

# Energy Actions And Focus

## Claim

`聚能` is a baseline resource action, not a normal species-exclusive move.

Current reviewed working model:

- `聚能` restores `5` energy
- `聚能` is treated as a status action
- if interrupted, `聚能` fails
- being responded to is not the same as being interrupted

## Strategic Use

For advisor reasoning, `聚能` matters because it creates one of the clearest
tempo tradeoffs in the game:

- surrender a turn now
- recover future action capacity later

The advisor should ask:

- is the team trying to force the opponent into a focus turn
- can the opponent punish focus with response or interruption
- is the species energy-starved enough that focus is a realistic line

## Response Versus Interrupt

Current reviewed doctrine must keep these distinct:

- `应对`
  - conditional extra payoff if the opponent used the expected category
- `打断`
  - explicit effect that makes the target action fail

So for `聚能`:

- it may be responded to because it is a status action
- but it only fails if the opposing move/effect explicitly interrupts it

## Evidence

The 18-type tutorial and the earlier basic battle-system note both describe
`聚能` as the default energy-recovery action and classify it as status-type.

The current thread adds the more operational clarification:

- restore 5 energy
- if interrupted, it fails
- being responded to is not equivalent to being interrupted

## Confidence

`provisional`.

High confidence:

- focus restores 5 energy
- focus is a status action
- response and interrupt must not be collapsed

Medium confidence:

- exact ordering against every future interrupt-bearing effect
- whether any special species/form rewrite changes focus behavior

## A-Layer Boundary

This page does not define executable default-action code.

A-layer formalization would likely need fields such as:

- default_focus_action
- focus_energy_gain
- focus_action_category
- focus_interruptible

## Known Failure Modes

- treating focus as an ordinary equipped move
- treating every successful response to focus as if focus failed
- forgetting that focus is one of the main windows for tempo punishment

