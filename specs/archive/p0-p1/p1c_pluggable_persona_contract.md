# P1c Pluggable Persona Contract

## Purpose

Define a safe, pluggable persona contract above the conversational presentation
layer.

Persona is now part of the primary product surface, but it still does not own
facts or reasoning.

This track should adopt the five-layer doctrine shape defined in:

- `specs/persona_doctrine_contract.yaml`
- `specs/persona_source_adapter_contract.yaml`
- `specs/persona_artifact_ingestion_contract.yaml`

## Core Rule

Persona controls how synthesized and presented material is spoken, not what is
true and not what the system has concluded.

## Approved Flow

`A facts + B doctrine -> synthesis -> Reply/Why presentation -> persona render`

Not approved:

`facts/tools -> persona improv -> final answer`

## Allowed Controls

Persona may influence:

- tone
- diction
- pacing
- challenge style
- how strongly recommendations are framed
- how follow-up suggestions are phrased
- reasoning style only through the approved doctrine-facing subset

Persona may not influence:

- factual claims
- evidence attribution
- confidence tier
- refusal decisions
- native/deterministic routing
- official-IP positioning

## Persona Contract

Each approved persona should define at least:

- `persona_id`
- `display_name`
- `expression_dna`
- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`
- `facts_locked`
- `fact_policy`
- `ip_safety_profile`

## Default Product Policy

The architecture should be pluggable from the start.

The shipped product may still expose only one default persona at first.

This means:

- architecture: pluggable
- initial UX: single safe default persona is acceptable
- internal-only or dev personas may exist before public-safe filtering, but the
  public/default path must still enforce IP safety
- persona creation should later route through managed source adapters and
  ingestion, not ad hoc direct prompt blobs

## Acceptance Criteria

P1c is acceptable when:

- multiple safe personas can render the same grounded `Reply + Why`
  differently
- the underlying synthesis/evidence/confidence/refusal remain invariant
- unsafe or official-IP persona selectors fall back safely
- persona improves product feel without weakening trust boundaries
