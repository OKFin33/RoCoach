---
title: "Bug Contribution (奉献)"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/raw/source_notes/2026-03-26_mainstream_pvp_archetype_deck.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "user_mechanism_batch_v2"
human_confirmed:
  - "当前版本奉献触发来源只有虫群和啃咬"
persona_free: true
---

# Bug Contribution (奉献)

## Claim

`奉献` is a team-held contribution mechanic, not a mark and not a normal buff.

Current-version reviewed working model:

- contribution belongs to the team rather than to one current on-field spirit
- it persists across spirits
- current-version confirmed trigger sources are only `虫群` and `啃咬`
- current reviewed contribution effects include:
  - apply 2 layers of poison
  - gain 10% lifesteal
  - combo count +1
  - power +20
  - energy cost -2

## Strategic Use

For advisor reasoning, `奉献` means early actions can be invested into later
team payoff rather than only immediate board value.

The advisor should ask:

- who is creating contribution
- who is cashing it out
- whether the team can survive long enough to profit from banked contribution
- whether the user is describing a front-loaded bug team or a back-loaded
  contribution finisher

## Evidence

The 18-type tutorial describes bug-type play around `奉献` as a hidden
team/backline contribution rather than a normal mark or ordinary buff.

The current thread adds explicit current-version clarifications:

- `奉献` is team-held
- it persists across spirits
- only `虫群` and `啃咬` are currently confirmed trigger sources
- the current reviewed effect set contains five concrete payoff variants

## Confidence

`provisional`.

High confidence:

- contribution is not a mark
- contribution belongs to the team, not only to one current spirit
- current confirmed trigger sources are `虫群` and `啃咬`

Medium confidence:

- exact storage/display behavior in battle UI
- whether future versions add more trigger sources or more contribution variants

## A-Layer Boundary

This page does not define executable team-contribution storage.

A-layer formalization would likely need fields such as:

- contribution_source
- contribution_variant
- contribution_team_scope
- contribution_persistence
- contribution_consume_rule

## Known Failure Modes

- describing contribution as if it were a regular self-buff
- confusing contribution with marks
- analyzing a contribution team as if every member needs immediate individual
  payoff
- assuming unconfirmed trigger sources exist without evidence

