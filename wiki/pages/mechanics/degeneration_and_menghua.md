---
title: "Degeneration And 萌化"
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
persona_free: true
---

# Degeneration And 萌化

## Claim

`萌化` is a debuff-driven regression mechanic, not a percentage stat shrink.

Current-version reviewed working model:

- each layer regresses the spirit by one evolution stage
- regression continues until the initial form
- base-form-linked stats and traits revert to the regressed form
- current HP does not automatically rescale to the new max HP
- max HP itself changes with the regressed form

## Strategic Use

For advisor reasoning, `萌化` is important because it changes form-linked power
structure rather than merely applying a generic minus-stat effect.

The advisor should ask:

- does the target lose a key evolved trait after regression
- does the target's max HP and bulk profile change enough to alter kill ranges
- is the team using degeneration as hard disruption, or as setup for a later
  finisher

## Evidence

The 18-type tutorial presents `萌化` as regression / de-evolution and ties it
to stage rollback rather than a normal buff/debuff arithmetic model.

The current thread adds a sharper current-version interpretation:

- `萌化` is a debuff
- each layer means one-stage regression
- regression stops at the initial form
- the regressed form's base-form-linked stats and traits take over
- current HP does not automatically rescale along with the max-HP change

## Confidence

`provisional`.

High confidence:

- degeneration is stage-based, not ratio-based
- it regresses one stage per layer
- it bottoms out at the initial form

Medium confidence:

- exact combat-log wording for stacked degeneration
- whether all future/current form-linked properties always revert under the same
  model

## A-Layer Boundary

This page does not define executable form-rewrite code.

A-layer formalization would likely need fields such as:

- degeneration_layers
- degeneration_stage_delta
- degeneration_floor_stage
- reverted_trait_mode
- max_hp_recompute
- current_hp_preserve_mode

## Known Failure Modes

- treating degeneration as a simple percentage debuff
- assuming current HP is automatically renormalized to the new max HP
- forgetting that trait identity may change with form rollback
- recommending degeneration lines without checking whether the target still
  functions well enough even in a lower form

