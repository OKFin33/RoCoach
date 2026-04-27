---
title: "Morale And Revive"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/cache/数值基础0405/NoteGPT_玩懂PVP！洛克王国属性&伤害计算公式！「洛克王国：世界」.txt"
  - "wiki/cache/萌新百科0411/NoteGPT_【洛克王国：世界】保姆级萌新大百科.txt"
  - "wiki/raw/source_notes/2026-04-21_user_verified_morale_revive_rule.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "user_correction_after_dogfood"
persona_free: true
---

# Morale And Revive

## Claim

PvP loss pressure is tracked through morale/magic loss when spirits faint.
Revive effects create additional board presence, but they do not refund or
cancel morale/magic already lost from fainting.

If a revived spirit faints again, morale/magic is deducted again.

## Strategic Use

When judging revive traits such as `不朽`, separate two forms of value:

- board value: the spirit can return and act again after the revive condition
- morale/magic cost: every faint still matters for the losing side's PvP loss
  condition

This prevents overclaiming that a revive spirit is "free to die." It is better
described as a repeat-entry resource that can create tempo, absorb pressure,
force enemy energy spend, and reappear in a later state of the game.

For team reasoning, the advisor should ask:

- Did the first faint already cost morale/magic?
- Can the revive timing realistically matter before the game ends?
- Does the revived spirit force a second meaningful answer, or merely return
  as a low-tempo body?
- Does the team gain enough entry, energy, or setup value from the faint to
  justify the morale/magic cost?

## Evidence

The beginner PvP sources describe the general rule: when a spirit loses battle
capacity, the player loses morale/magic, and losing all morale/magic loses the
battle. User review on 2026-04-21 confirmed the revive edge case: death deducts
morale/magic; after revival, a later death deducts again.

The A-layer database records traits with explicit morale/magic modifiers, such
as `诈死` reducing morale/magic loss on faint and `御驾亲征` increasing faint
cost. This implies morale/magic loss is a first-class PvP resource and should
not be silently bypassed unless a trait says so.

## Confidence

`provisional`.

High confidence:

- normal fainting deducts morale/magic
- revive does not refund the earlier deduction
- a revived spirit fainting again deducts morale/magic again

Medium confidence:

- exact UI naming between morale and magic in all public materials
- exact ordering of revive timing relative to end-of-turn effects

## A-Layer Boundary

This page does not define executable battle timing. It records the strategic
rule that revive does not negate faint cost.

Exact trait text and future engine timing belong to:

```text
data/runtime/battle_dex.sqlite
```

## Known Failure Modes

- Calling a revive spirit a no-cost sacrifice.
- Ignoring that repeated deaths can consume repeated morale/magic.
- Treating revive value as guaranteed without checking turn count and tempo.
- Assuming a revive trait modifies morale/magic unless its A-layer text says so.

## Draft Review Questions

- What is the exact engine timing of `不朽` revival relative to turn count,
  switching, and end-of-turn effects?
- Does a revived spirit return with full health, partial health, or a specific
  state in all cases?
- Are there edge cases where a faint is prevented rather than followed by revive?
