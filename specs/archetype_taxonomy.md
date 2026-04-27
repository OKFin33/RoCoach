# Archetype Taxonomy Specification

## Purpose

Define the canonical team-style vocabulary used by the battle-analysis system so that team-level conclusions are stable across Engine logic, reports, and Agent explanations.

## Scope

This document defines:

- canonical team archetypes
- what each archetype means operationally
- the key signals used to score an archetype
- how archetype reports should be expressed

## Non-goals

This document does not define:

- species role labels
- exact scoring weights
- environment-specific tiering
- matchup odds against named meta teams

## Core Rules

1. Archetype classification is `multi-score`, not one-hot.
2. A team may score meaningfully on more than one archetype.
3. The system must report both the `primary_archetype` and the score spread.
4. Archetypes must be inferred from structured team evidence, not tone or flavor.

## Canonical Archetypes

### `stall`

Definition:
A low-tempo, high-sustain team centered on denial, repeated switching, status pressure, and exhausting opposing progress.

Typical signals:

- multiple walls or bulky pivots
- strong sustain profile
- status pressure
- low dependence on immediate speed races

### `balance`

Definition:
A mixed-pressure team with both defensive backbone and offensive conversion tools, without overcommitting to either extreme.

Typical signals:

- at least one stable defensive core
- at least one credible breaker
- moderate sustain
- moderate tempo
- role distribution with low redundancy

### `bulky_offense`

Definition:
A pressure-oriented team that uses above-average natural bulk to preserve momentum and trade efficiently.

Typical signals:

- multiple offensive pieces with usable switch-in value
- limited but non-zero sustain
- stronger tempo than balance
- less defensive redundancy than stall or classic balance

### `hyper_offense`

Definition:
A high-tempo team centered on setup, speed pressure, sacrifice lines, and short-game offensive conversion.

Typical signals:

- strong setup presence
- high speed pressure
- low sustain
- limited defensive redundancy
- multiple roles optimized for trading or snowballing

### `pivot_offense`

Definition:
An offense-oriented team that wins by maintaining initiative through repeated positioning and matchup cycling.

Typical signals:

- strong pivot move presence
- tempo-focused role compression
- multiple offensive or utility pivots
- moderate speed and pressure

### `anti_meta`

Definition:
A team intentionally optimized to target expected common threats, common cores, or common lines in the current environment.

Typical signals:

- concentrated matchup tech
- multiple specific coverage decisions
- role or move choices that make more sense against the environment than in a vacuum

This archetype requires meta context. Without meta input, its score must stay conservative.

## Required Scoring Dimensions

Every archetype score must be derived from at least these dimensions:

- `tempo_score`
- `sustain_score`
- `pivot_score`
- `setup_score`
- `anti_setup_score`
- role distribution
- defensive redundancy
- offensive conversion pressure

## Primary Archetype Rule

The `primary_archetype` must be the highest scoring archetype only if:

- its score is clearly above nearby alternatives, and
- the evidence does not directly contradict the label

If scores cluster tightly, the report should say the team is hybrid.

Example:

- acceptable: `balance (0.78), bulky_offense (0.71)` with a note saying “balance-leaning hybrid”
- bad: forcing `stall` because the team has two bulky slots despite weak sustain and strong tempo bias

## Report Contract

Every team archetype report must include:

- ordered archetype scores
- `primary_archetype`
- `tempo_score`
- `sustain_score`
- `pivot_score`
- `setup_score`
- `anti_setup_score`
- explanation evidence

## Evaluation Checklist

- Are all archetypes from the canonical set in this document?
- Does the report show the score distribution instead of only one label?
- Does the evidence support the chosen primary archetype?
- Is hybrid ambiguity surfaced when scores are close?
- Is `anti_meta` kept conservative when no meta snapshot exists?
