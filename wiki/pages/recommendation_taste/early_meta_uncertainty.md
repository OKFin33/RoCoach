---
title: "Early Meta Uncertainty"
content_class: "recommendation_taste"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/cache_inventory_2026-04-20.md"
  - "wiki/raw/source_notes/2026-03-26_mainstream_pvp_archetype_deck.md"
  - "wiki/cache/超长精灵评级0412/NoteGPT_一口气讲明白所有宠物强度？！洛克王国世界pvp排行榜.txt"
  - "wiki/cache/熟悉热门技能特性0417/NoteGPT_洛克王国PVP焚决·上集（缓解精灵培养焦虑，熟悉热门技能特性）.txt"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-20"
reviewed_by: "first_wiki_closure"
persona_free: true
---

# Early Meta Uncertainty

## Claim

Early-release PvP recommendations must separate stable mechanics taste from
volatile current-meta claims.

The advisor may use community rankings and weekly team reports to detect
patterns, but should not present them as durable truth.

## Strategic Use

Default recommendation posture:

- prefer explaining why a team works over claiming it is best
- label source date and volatility for ratings or weekly reports
- distinguish mechanic stability from exact species ranking
- give counterplay and failure modes with any strong recommendation
- avoid hard claims when the game has recently patched or released new tools

Good answer shape:

```text
This team appears to be a mark-protection long-game shell. The durable lesson is
the energy loop and mark protection. The exact member ranking is volatile and
should be checked against current battle-dex and recent reports.
```

## Evidence

The first cache inventory includes many early-release sources: March archetype
deck, April ranking snapshot, current skill/trait videos, and weekly team
recommendations. These are valuable but patch-sensitive.

The 2026-03-26 archetype deck itself mixes beta history and public-release
prediction, so it is useful for archetype doctrine but unsafe as current-meta
authority.

## Confidence

`provisional`.

High confidence:

- early community meta sources are volatile
- ratings and teamlists require date and confidence labels
- mechanics interpretation is more stable than exact tier ranking

Medium confidence:

- which specific April claims have already gone stale

## A-Layer Boundary

Current species, move, trait, and exact set viability must be checked through
A-layer data and recent reviewed sources. B Wiki can store taste and caution,
not live ranking authority.

## Known Failure Modes

- Recommending a stale tier-list pick as if it were current.
- Hiding source date.
- Turning one creator's preference into generic doctrine.
- Ignoring patch volatility in a game that is still settling.
- Using model-generated team logic without review.

## Draft Review Questions

- What is the maximum age for a source to drive hard recommendations?
- Should weekly reports expire automatically unless reviewed?
- What confidence label should be assigned to model-synthesized team reviews?
