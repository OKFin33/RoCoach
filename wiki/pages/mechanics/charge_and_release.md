---
title: "Charge And Release"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "docs/manual_battle_data_supplement_2026-04-14.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "user_mechanism_batch_v2"
human_confirmed:
  - "当前版本带蓄力词条的技能均为3能耗"
persona_free: true
---

# Charge And Release

## Claim

`蓄力` is a two-step commitment mechanic.

Current-version reviewed working model:

- first turn: spend the move's energy and enter the charge state
- next turn: the player must choose that same charge move to release it
- other carried skills are unavailable while still holding the charge
- the player may choose `聚能` or switch out to cancel the charge
- current-version charge-keyword skills all cost `3` energy

Special rewrites already observed:

- `架势` lets the next charge move release directly
- `嫉妒` on 伊兰亚龙 allows other carried skills during the charge stage and
  reduces their displayed cost by the energy already spent on the charged move

## Strategic Use

For advisor reasoning, charge is not just delayed damage. It is visible
commitment with hidden target-move identity and specific cancellation routes.

The advisor should ask:

- is the team built to protect a charge turn
- does the charge user gain enough payoff to justify surrendering flexibility
- can the team exploit the fact that the opponent does not know which charge
  move is being prepared
- does the plan rely on a rewrite trait such as `嫉妒` or a setup move such as
  `架势`

## Evidence

The 18-type tutorial describes charge as: prepare now, resolve next turn.

The current thread adds a more exact current-version model:

- charge energy is paid on the first turn
- the second-turn release does not pay energy again
- the opponent does not know which specific move is being charged
- response-to-status attacks do not automatically break charge and do not gain
  their expected response payoff merely because the target is charging
- `聚能` and switching can cancel the charge state

The same thread also documents two explicit rewrites:

- `架势`
- `嫉妒`

## Confidence

`provisional`.

High confidence:

- charge is a two-step mechanic
- energy is spent on the first step, not again on the release step
- `聚能` and switching can cancel charge
- the current-version charge-keyword moves all cost `3`

Medium confidence:

- whether every current/future charge move shares every visibility and
  cancellation nuance identically
- exact UI/log wording for the charge state

## A-Layer Boundary

This page does not define executable charge-state code.

A-layer formalization would likely need fields such as:

- is_charge_move
- charge_cost_paid_on_prepare
- charge_release_requires_same_move
- charge_cancel_actions
- charge_visibility_model
- trait_or_move_charge_rewrites

## Known Failure Modes

- treating charge as simple delayed damage with no cancellation routes
- assuming the opponent knows the exact charged move
- charging ahead with a team that cannot protect the commitment turn
- treating `架势` and `嫉妒` as universal charge rules instead of explicit
  rewrites

