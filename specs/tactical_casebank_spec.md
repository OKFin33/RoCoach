# Tactical Casebank Spec

## Purpose

Define a representative tactical casebank used by the advisor for:

- role priors
- archetype priors
- team-conditional judgement
- case-based analogies

This casebank is not a build encyclopedia.

## Core Principle

The casebank should `teach patterns`, not `memorize answers`.

It should help the advisor infer:

- what kinds of attributes, stats, abilities, and move structures usually support what roles
- how team context changes role interpretation
- how different sets of the same species may imply different tactical positions

## Scope Boundary

The casebank should not aim to cover:

- every species
- every common ladder team
- every viable set

The casebank should aim to cover:

- representative archetypes
- representative role distributions
- representative set patterns
- representative conditional role shifts

## Recommended Initial Size

Target first-pass size:

- `20-30` team cases
- `30-60` species set examples

This is enough for pattern induction without creating an annotation swamp.

## Core Entities

### 1. TeamCase

Fields:

- `case_id`
- `title`
- `source_kind`
- `source_ref`
- `confidence_tier`
- `archetype_labels`
- `team_summary`
- `tactical_notes`
- `species_sets`

### 2. SpeciesSetExample

Fields:

- `species_key`
- `ability`
- `moves`
- `item_or_equivalent` if relevant later
- `role_labels`
- `role_confidence`
- `set_summary`
- `team_function_notes`
- `conditional_notes`

### 3. RolePrior

Fields:

- `prior_id`
- `pattern_features`
- `suggested_roles`
- `counter_examples`
- `confidence_tier`
- `supporting_case_ids`

This entity is derived from cases and should not be hand-written first.

## Annotation Rules

Every case should distinguish:

- `species baseline`
- `selected set`
- `team role`
- `team context`

This is critical because:

- a species does not have one globally correct role
- a species set can function differently in different teams

## Confidence Tiers

### Confirmed

- directly evidenced by strong in-game material or well-verified manual review

### Provisional

- inferred from credible competitive examples but not officially canonical

### Low Confidence

- weak community claim
- not approved as default training prior

Default advisor retrieval should prefer:

- `confirmed`
- then `provisional`

and avoid `low_confidence` unless explicitly requested.

## Source Policy

Allowed source classes:

- PM-reviewed example teams
- manually reviewed competitive case notes
- future curated community examples with explicit confidence labeling

Not allowed as default:

- unreviewed forum dumps
- uncited social screenshots
- anonymous one-off teamlists

## Retrieval Usage

Case retrieval should support:

- nearest archetype comparison
- nearest role pattern comparison
- “same species, different role” examples
- “same role, different species” examples

Cases should never override facts from battle-dex retrieval.

## Derivation Path

The casebank should later support a derived `role prior` layer.

That layer should summarize patterns like:

- bulky stat spread + recovery / reduction / pivot tools -> bulky pivot or wall
- speed plus setup plus burst coverage -> cleaner or setup sweeper
- status / control / force-switch toolkit -> support or tempo piece

This is the correct bridge between examples and generalization.

## Non-Goals

Do not build:

- a full meta database
- a crowd-sourced build encyclopedia
- a noisy pile of unlabeled screenshots

