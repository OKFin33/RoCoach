---
title: "Entry, Exit, And Replacement Timing"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-21_user_reviewed_mechanism_batch_v2.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/pages/mechanics/speed_priority_and_swift.md"
  - "wiki/pages/mechanics/burst_trigger_and_entry_actions.md"
  - "wiki/pages/mechanics/marks_and_persistence.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "mechanism_completion_pass"
persona_free: true
---

# Entry, Exit, And Replacement Timing

## Claim

`入场`、`离场`、`脱离`、`换人` are not interchangeable words.

Current reviewed doctrine requires at least this distinction:

- active player switch
- active leave caused by a skill/effect
- passive replacement after faint
- forced replacement

Some effects care about the reason for leaving. Some care only that a
replacement occurred.

## Strategic Use

This timing cluster matters because multiple other mechanisms depend on it:

- `迅捷`
- `迸发`
- `降灵印记`
- `棘刺印记`

For advisor reasoning, ask:

- is the current event a player-chosen switch, a skill-driven leave, or a faint
  replacement
- does the mechanism care about "active leave" specifically
- does it only care that a new spirit entered, regardless of cause

## Current Working Distinction

- `主动换人`
  - player-operated switch choice
- `主动离场`
  - a leave event caused by the player's chosen action or a self-driven effect
- `脱离`
  - a leave/replacement event caused by a move/effect rather than ordinary
    manual switching
- `被击败替换`
  - passive replacement after faint
- `强制离场`
  - replacement caused by an external effect

Current reviewed thread guidance:

- player-operated switch and active leave are coupled but not identical
- some effects only care that the opponent changed the fielded spirit,
  regardless of reason

## Consequence For Other Mechanisms

- `迅捷` and `迸发` must not be explained without clarifying what kind of entry
  event is involved
- `降灵印记` is sensitive to active-leave wording
- `棘刺印记` can punish replacement more broadly and should not be over-narrowed
  to one leave subtype unless the move text requires that

## Evidence

The 18-type tutorial repeatedly relies on leave/entry distinctions:

- wing/swift material distinguishes active switch entry from passive
  post-faint replacement
- ghost material distinguishes active leave
- electric burst logic depends on what counts as entry and first action after
  entry

The current thread adds the explicit PM correction that some effects should care
about any replacement event, not only one named leave subtype.

## Confidence

`provisional`.

High confidence:

- these leave/entry words should not be treated as synonyms
- several reviewed mechanisms already depend on this distinction

Medium confidence:

- the exact engine classification for every future/current leave subtype
- which effects observe reason-for-leave versus replacement-as-such in every
  edge case

## A-Layer Boundary

This page does not define executable event-taxonomy code.

A-layer formalization would likely need fields such as:

- entry_event_type
- leave_event_type
- is_active_leave
- is_faint_replacement
- is_forced_replacement
- effect_scope_on_replacement

## Known Failure Modes

- treating all replacement events as the same
- assuming a mechanism that says active leave also triggers on faint
- assuming a mechanism that punishes replacement only works on manual switching
- explaining swift or burst without clarifying the entry subtype

