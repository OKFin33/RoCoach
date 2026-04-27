# Role Taxonomy Specification

## Purpose

Define a stable role vocabulary for species-level and team-level analysis in the Roco battle-analysis system.

The taxonomy exists to prevent ambiguous labels such as "output", "support", or "tank" from drifting across implementations, prompts, and reports.

## Scope

This document defines:

- canonical role labels
- what each role means
- what evidence is required before a role can be assigned
- how primary and secondary roles should be reported

## Non-goals

This document does not define:

- exact numeric scoring formulas
- team archetype definitions
- move database schema
- meta-specific viability rankings

## Core Rules

1. Roles are `multi-score`, not one-hot.
2. Every species can have one `primary_role` and zero or more `secondary_roles`.
3. A role label must be backed by structured evidence from stats, typing, abilities, move features, or explicit set data.
4. The system must never assign a role from flavor text or LLM intuition alone.
5. If evidence is weak or conflicting, the report must surface low confidence instead of forcing a confident label.

## Canonical Roles

### `primary_breaker`

Definition:
High immediate damage source intended to force progress against neutral or defensive targets.

Typical evidence:

- high attack or special attack pressure
- strong STAB profile or high-coverage attacks
- wallbreaking utility such as self-boosting, defense-breaking, or burst damage

Common anti-signals:

- very low offensive pressure
- no reliable damage options

### `secondary_breaker`

Definition:
Supplementary damage source that supports the main breaker or punishes specific defensive gaps.

Typical evidence:

- above-average damage pressure
- narrower coverage or less consistent threat profile than a primary breaker
- contributes progress without being the main win condition

### `cleaner`

Definition:
A species that converts an already weakened board into endgame pressure, usually via speed, priority, or snowball tools.

Typical evidence:

- high speed
- priority access
- setup move with endgame orientation
- strong revenge-kill profile

### `bulky_pivot`

Definition:
A species that can repeatedly absorb pressure and maintain tempo through switching, pivoting, or threat compression.

Typical evidence:

- above-average defensive profile or strong resist profile
- pivot move or equivalent switch-pressure tool
- broad role compression such as status, recovery, or utility

### `wall`

Definition:
A species whose main purpose is to absorb attacks, deny progress, and anchor a defensive core.

Typical evidence:

- high bulk
- recovery or long-term sustain
- status, phazing, debuff, or direct denial utility

Common anti-signals:

- highly tempo-driven set with no sustain
- purely offensive stat spread and move profile

### `support`

Definition:
A species that primarily improves team function rather than dealing damage itself.

Typical evidence:

- status spread
- healing, screen, terrain, weather, or field support
- ally enablement or anti-setup utility

### `speed_control`

Definition:
A species whose main contribution is altering speed dynamics for the team or the opponent.

Typical evidence:

- very high speed tier
- priority
- paralysis or other speed-lowering tools
- tailwind-like or scarf-like operational profile if applicable

### `hazard_setter`

Definition:
A species that reliably establishes battlefield pressure through hazard-like mechanics.

Typical evidence:

- access to hazard setup
- sufficient bulk, forcing power, or lead utility to deploy it consistently

### `hazard_control`

Definition:
A species that removes, blocks, or punishes hazard pressure.

Typical evidence:

- direct hazard removal
- anti-hazard interaction

### `status_spreader`

Definition:
A species that reliably applies disruptive status and changes long-game dynamics.

Typical evidence:

- consistent access to poison, burn, paralysis, sleep, freeze, or analogous disruption
- repeatable application instead of low-probability incidental effects

### `setup_sweeper`

Definition:
A species that aims to convert one or more setup turns into a snowballing win condition.

Typical evidence:

- setup move
- speed or priority support after setup
- enough offensive scaling to threaten multiple KOs

### `revenge_killer`

Definition:
A species that enters after a loss or forced sack and immediately threatens a KO or tempo reset.

Typical evidence:

- strong speed tier
- priority
- immediate damage without setup

### `tech_slot`

Definition:
A species or set used mainly to cover a specific matchup, lure, denial line, or information gap.

Typical evidence:

- unusual coverage or utility aimed at a narrow target class
- role value concentrated in specific matchups rather than broad baseline output

## Role Assignment Requirements

### Minimum Evidence Requirement

Every reported role must cite at least two evidence dimensions from this list:

- type profile
- base stats
- move feature flags
- selected ability
- selected move set
- known sustain or utility access

### Primary Role Rule

The `primary_role` must be:

- the highest scoring role, and
- at least meaningfully separated from the second role

If the top two role scores are too close, the report must note ambiguity.

### Secondary Role Rule

A role can be reported as secondary only if it contributes materially to team construction.

Weak incidental capabilities do not qualify.

Bad example:

- calling a pure breaker `support` because one move has a minor debuff chance

Good example:

- calling a bulky pivot `support` because it has repeatable status pressure and team utility

## Report Contract

Every species role report must include:

- `primary_role`
- ordered `secondary_roles`
- `pressure_profile`
- `evidence`
- optional ambiguity note if the role boundary is weak

## Evaluation Checklist

- Are all roles drawn from the canonical list in this document?
- Does each assigned role have structured evidence?
- Is the primary role actually the dominant job rather than a cosmetic label?
- Are incidental or low-value capabilities excluded from secondary roles?
- Is ambiguity surfaced instead of hidden?
