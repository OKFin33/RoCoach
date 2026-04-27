---
title: "Burst Trigger And Entry Actions"
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
persona_free: true
---

# Burst Trigger And Entry Actions

## Claim

`迸发` is an entry-linked first-action trigger, not a normal permanent buff.

Current-version reviewed working model:

- `迸发` triggers on the first action after entry
- it is not limited to attack skills
- current working assumption is that passive replacement entry also counts

The last point remains provisional and should be stated with care.

## Strategic Use

For advisor reasoning, burst mechanics matter because they convert entry timing
into tempo and payoff.

The advisor should ask:

- can this team repeatedly generate high-value entries
- does the species want active switch, forced leave/return loops, or defensive
  cycling to access burst
- is the burst payoff worth the board cost of leaving and re-entering
- is the user's plan relying on one burst turn or on repeated burst cycling

## Evidence

The 18-type tutorial names `迸发` as the defining electric-type trigger and
explains it as an effect that occurs on the first action after entry.

The same source ties burst to leave/return loops and to entry sequencing rather
than to one specific move category.

The current thread adds a user-reviewed current-version interpretation:

- first-action trigger after entry
- not limited by move type
- passive replacement likely also counts, but this remains slightly uncertain

## Confidence

`provisional`.

High confidence:

- burst is an entry-linked first-action trigger
- burst is not restricted to attack moves only
- burst is central to electric-type rhythm and leave/return play

Medium confidence:

- whether passive replacement always counts as entry for burst
- whether any entry subtype is excluded in edge cases

## A-Layer Boundary

This page does not define executable entry-type classification.

A-layer formalization would likely need fields such as:

- burst_trigger_on_entry
- burst_trigger_on_first_action
- burst_valid_entry_types
- burst_consumed_after_first_action

## Known Failure Modes

- describing burst as a generic damage buff
- assuming burst only works on attack moves
- assuming all entry types are identical without marking uncertainty
- recommending burst loops without checking whether the team can safely create
  repeated entries

