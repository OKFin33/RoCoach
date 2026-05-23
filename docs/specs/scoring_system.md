# Scoring System Specification

## Purpose

Define the first-pass deterministic scoring rules for the Roco battle-analysis Engine.

This document is the bridge between abstract labels and implementable logic. It specifies how the Engine should score deterministic subproblems such as team structure, and later any structured role or archetype scoring that is mature enough to leave the semantic Agent layer.

## Scope

This document covers:

- team structure scoring from attribute data
- species role scoring from structured features
- team archetype scoring from team composition and role outputs
- output evidence requirements

## Non-goals

This document does not cover:

- exact move viability rankings
- meta matchup simulation
- probabilistic battle outcome models
- training-based classifiers

## Scoring Principles

1. Every score must be deterministic for the same input payload.
2. Every score must be explainable through reusable evidence lines.
3. Scores should be normalized to `0.0` to `1.0` unless otherwise stated.
4. Scores may be heuristic, but the heuristic must be written here before implementation.
5. If a score uses missing data, the report must include a confidence penalty or uncertainty note.

## Section A: Team Structure Scoring

### Inputs

- up to six team slots
- each slot includes primary type and optional secondary type
- type chart from `data/roco_world_type_chart.json`
- dual-type combination rule from `docs/domain_primer.md`

### A0. Dual-Type Combination Rule

Phase 1 must not assume multiplicative dual-type effectiveness.

Current accepted project baseline:

- `2x + 2x => 3.0`
- `0.5x + 0.5x => 0.333...`
- `2x + 0.5x => 1.0`
- `1x + 1x => 1.0`
- `2x + 1x => 2.0`
- `0.5x + 1x => 0.5`

Equivalent interpretation:

- count `2x` matches
- count `0.5x` matches
- compare the two counts
- if strong count exceeds weak count, result is `3.0` when the margin is 2, otherwise `2.0`
- if weak count exceeds strong count, result is `0.333...` when the margin is 2, otherwise `0.5`
- if counts are equal, result is `1.0`

This rule applies only to combining an attack against a two-type defender. Single-type effectiveness remains unchanged.

### A1. Defensive Coverage Table

For each attacking type in the chart:

- count how many team slots take `2x or more`
- count how many team slots take `0.5x or less`
- count how many remain neutral

Derived labels:

- `repeated_weakness`: at least 2 weak slots
- `critical_weakness`: at least 3 weak slots
- `missing_resistance`: 0 resist slots
- `thin_resistance`: exactly 1 resist slot

For Phase 1 defensive classification:

- a slot is counted as `weak` if its final multiplier is greater than `1.0`
- a slot is counted as `resist` if its final multiplier is less than `1.0`
- a slot is counted as `neutral` if its final multiplier equals `1.0`

### A2. Offensive Coverage Table

For each attack type represented on the team:

- list all target types hit for `2x`
- list all target types hit for `0.5x`

Derived labels:

- `coverage_gap`: no team member hits a target category super effectively when that category is a known structural threat
- `coverage_overlap`: multiple members provide the same narrow offensive value with low additional utility

### A3. Structural Score

The initial team `structural_score` should be computed from:

- defensive resilience score
- offensive coverage score
- weakness concentration penalty
- resistance redundancy bonus

Recommended first-pass formula:

```text
structural_score =
    0.45 * defensive_resilience +
    0.30 * offensive_coverage +
    0.15 * resistance_redundancy +
    0.10 * role_flex_placeholder -
    weakness_penalty
```

Where:

- `defensive_resilience` increases when the team has broad resist coverage and few critical weaknesses
- `offensive_coverage` increases when the team threatens many target types with low redundancy
- `resistance_redundancy` increases when important resist profiles are covered by more than one slot
- `role_flex_placeholder` is set to `0.5` in Phase 1 until role analysis is implemented
- `weakness_penalty` grows with repeated and critical weaknesses

Recommended first-pass weakness penalties:

- `0.05` per repeated weakness
- additional `0.08` per critical weakness
- additional `0.05` per missing resistance on a critical attacking type

Dual-type outputs influenced by the `×3 / ÷3` rule must still be classified by their final relation:

- `3.0` counts as weak
- `0.333...` counts as resist
- `1.0` counts as neutral

### A4. Suggested Patch Types

Patch suggestions should be ranked by estimated gain on:

- reducing repeated weaknesses
- adding missing resistances
- preserving current offensive coverage

Phase 1 suggestions may recommend:

- a primary single-attribute patch suggestion, or
- a conditional attribute combination of up to two attributes

The output must still suggest `types`, not `species`, in Phase 1.

Recommended ranking policy:

- always expose single-type recommendations as the default patch direction
- evaluate dual-type candidates by the same structural criteria
- expose dual-type candidates as conditional follow-up guidance, not as the default recommendation layer
- apply a small complexity penalty to dual-type candidates so they are not recommended unless they provide real additional value

Recommended output shape:

- `primary_patch_types`: top-ranked single attributes that improve structure
- `conditional_dual_patch_types`: top-ranked dual-type combinations to consider only if an appropriate species exists

Phase 1 must not:

- recommend specific species
- assume learnsets
- assume abilities
- assume move coverage beyond the represented team-type baseline

## Section B: Species Role Scoring

### Inputs

- base stats
- primary and secondary type
- abilities
- derived move features
- selected set data if available

### B1. Pressure Profile

The Engine must compute these normalized profile scores:

- `offense`
- `bulk`
- `speed`
- `utility`
- `sustain`

Recommended initial interpretation:

- `offense`: based on offensive stats, offensive typing, burst features, setup access
- `bulk`: based on HP, defenses, defensive typing, mitigation abilities
- `speed`: based on base speed and speed-control features
- `utility`: based on hazard, pivot, status, anti-setup, support features
- `sustain`: based on recovery and long-game stability

### B2. Role Score Construction

Each role score should be a weighted combination of relevant profile dimensions plus discrete feature bonuses.

Examples:

- `primary_breaker`
  - high offense weight
  - medium speed weight
  - bonus for setup or burst features
- `bulky_pivot`
  - high bulk weight
  - medium utility weight
  - bonus for pivot and sustain features
- `wall`
  - high bulk weight
  - high sustain weight
  - bonus for status or denial utility
- `cleaner`
  - high speed weight
  - medium offense weight
  - bonus for priority or setup

### B3. Primary vs Secondary Role

Recommended first-pass rule:

- highest score becomes `primary_role`
- any additional role above the secondary threshold becomes `secondary_role`

Recommended thresholds:

- secondary threshold: `>= 0.60`
- ambiguity warning: top two roles within `0.08`

### B4. Evidence Requirement

Every role score explanation must include:

- at least one stat-based reason
- at least one feature-based or typing-based reason

Bad example:

- “This looks like a bulky pivot.”

Good example:

- “Assigned `bulky_pivot` because bulk profile is high, sustain is above threshold, and the set includes repeatable pivot utility.”

## Section C: Team Archetype Scoring

### Inputs

- team structure report
- per-species role reports
- optional selected set data

### C1. Core Team Metrics

The Engine must compute:

- `tempo_score`
- `sustain_score`
- `pivot_score`
- `setup_score`
- `anti_setup_score`

### C2. Archetype Construction

Recommended first-pass interpretations:

- `stall`
  - high sustain
  - high bulk
  - high denial utility
  - low tempo
- `balance`
  - moderate sustain
  - moderate tempo
  - mixed role distribution
  - no extreme skew
- `bulky_offense`
  - high offense
  - moderate bulk
  - moderate tempo
- `hyper_offense`
  - high tempo
  - high setup or speed concentration
  - low sustain
- `pivot_offense`
  - high pivot score
  - moderate to high tempo
  - multiple pivots plus breakers/cleaners
- `anti_meta`
  - score stays low without meta evidence
  - rises only when team tech clearly maps to active threats

### C3. Primary Archetype Rule

The highest score becomes `primary_archetype` only if:

- it exceeds the second score by at least `0.05`, or
- the report explicitly marks the team as a hybrid leaning toward the top score

## Section D: Confidence and Missing Data

### D1. Confidence Penalty

If required data is absent:

- reduce affected score confidence
- do not fabricate missing features
- include an uncertainty note in the report

Examples:

- unknown moveset reduces confidence for `support`, `setup_sweeper`, `hazard_setter`
- unknown ability reduces confidence where the ability materially changes role value

### D2. Phase Fallback Rules

- Phase 1 can run from types only
- Phase 2 requires species feature data
- Phase 3 requires at least role outputs and team structure outputs
- Phase 4 requires a meta snapshot

## Output Contract

All score-bearing reports must include:

- raw or normalized score values
- ordered labels
- evidence lines
- uncertainty note if confidence is reduced

## Evaluation Checklist

- Can the same inputs reproduce the same score?
- Is every reported label traceable to declared inputs?
- Are ambiguity cases surfaced instead of hidden?
- Are missing-data penalties applied instead of guessed around?
- Can the score logic be implemented without reading prior chat history?
