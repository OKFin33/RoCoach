# Combat Ontology

## Purpose

Define the minimum battle-analysis ontology for `洛克王国世界`.

This document exists to prevent schema design from importing assumptions from other games.

It is a discovery-and-alignment artifact, not a final database schema.

## Scope

This ontology currently covers only the entities required for battle analysis planning:

- `species`
- `move`
- `ability`

It does not yet cover:

- item
- location / acquisition
- lore
- art assets
- encyclopedia-only metadata

## Core Rule

The ontology must describe only what can be evidenced in `洛克王国世界`.

It must not import fields simply because they are common in:

- Pokemon-like systems
- legacy assumptions from other monster battlers
- community shorthand without primary evidence

## Entity: Species

Definition:

- a battle-usable creature entry

Battle-analysis relevance:

- type profile
- stat profile
- ability access
- move access
- form distinction

Important ontology note:

- `species` and `form` must remain conceptually distinct
- the base creature identity is not always the same thing as the playable battle form

## Entity: Form

Definition:

- a specific battle-relevant variation of a species entry

Examples of why this matters:

- alternate battle forms
- special variants
- stateful variants if the game presents them as distinct encyclopedia or battle records

Current ontology rule:

- treat `form` as a first-class concept during field alignment
- final storage design may still colocate it with species if evidence shows no meaningful divergence
- after the 2026-04-13 wiki recon, keep `精灵形态` and `地区形态名称` separate until a broader crawl proves they can be safely merged

## Entity: Move

Definition:

- a battle action selectable by a species

Battle-analysis relevance:

- offensive pressure
- defensive utility
- setup
- sustain
- control
- pivot value

Critical ontology warning:

- do not assume classic RPG or Pokemon-style fields unless they are confirmed in this game
- especially avoid default assumptions about:
  - accuracy
  - PP
  - conventional priority semantics

Current source model:

- wiki detail pages expose `{{技能信息}}`
- confirmed raw fields include `技能名称`, `属性`, `技能类别`, `威力`, `耗能`, and `效果`
- `技能类别` must preserve game-native labels such as `状态`, `防御`, `物攻`, and `魔攻`
- `accuracy`, `PP`, and `cooldown` remain `forbidden_by_default`

Acquisition boundary:

- a canonical battle move is the move itself, such as `光刃`
- a skill-stone page title such as `技能石/光刃` is acquisition evidence, not a separate battle move
- species move access channels such as level-up, skill-stone, and bloodline are source/provenance distinctions
- first-pass Engine analysis should use the union of these access channels
- bloodline mutual-exclusion and acquisition legality belong to a later legality layer

## Entity: Ability

Definition:

- a passive or triggered battle trait attached to a species or form

Battle-analysis relevance:

- durability
- damage shaping
- immunity / mitigation
- tempo influence
- status interaction
- anti-setup or utility shaping

Ontology rule:

- store raw effect text if present
- extract structured tags only when the meaning is stable enough
- as of the 2026-04-13 wiki recon, ability data is embedded in species `{{精灵信息}}` fields `特性` and `特性描述`
- do not assume standalone ability pages or categories exist
- if a separate ability table is created, it is a derived local entity with source traceability back to species pages

## Entity: Derived Feature

Definition:

- a normalized battle-analysis tag derived from raw move or ability descriptions

Examples:

- `recovery`
- `pivot`
- `setup`
- `speed_control`
- `status_spread`
- `anti_setup`
- `burst_damage`

Purpose:

- bridge raw textual game data into deterministic Engine features

Ontology rule:

- derived features are interpretation products
- they must remain traceable back to source text

## Entity: Source Confidence

Definition:

- the trust status attached to a field or interpretation

Allowed states:

- `confirmed`
- `provisional`
- `forbidden_by_default`

Meaning:

- `confirmed`: strong enough to enter schema and runtime usage
- `provisional`: may be stored, but cannot silently become a hard runtime assumption
- `forbidden_by_default`: must not be introduced without explicit evidence and review

## Battle-Analysis Boundary

This ontology is only for data needed by:

- structure analysis
- species evaluation
- role analysis
- archetype analysis
- recommendation ranking
- later meta risk evaluation

It is not meant to support a general encyclopedia product at this stage.

## Immediate Design Consequence

Before Phase 2 schema work begins, each candidate field for:

- species
- move
- ability

must appear in the field alignment matrix with:

- confidence state
- evidence source
- usage note

No field should enter the schema by intuition alone.
