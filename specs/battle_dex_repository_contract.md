# Battle Dex Repository Contract

## Purpose

Define the approved SQL retrieval interface for the advisor runtime.

This exists so runtime code does not scatter ad hoc SQL across the project.

## Backend

Primary backend:

- SQLite battle dex

Current runtime source:

- latest write-eligible importer run materialized into runtime SQLite

## Repository Responsibilities

The repository layer should:

- expose typed query methods
- centralize SQL access
- preserve provenance fields
- raise clean domain errors for missing entities or ambiguous lookup

The repository layer should not:

- contain semantic judgement
- contain retrieval policy for docs or cases
- mutate battle-dex facts during normal advisor runtime

## Required Query Methods

### get_species_profile

Input:

- `species_key`

Output:

- species identity fields
- type fields
- base stats
- ability name/effect text
- provenance

### get_species_available_moves

Input:

- `species_key`
- `limit`

Output:

- move pool rows with:
  - move name
  - move type
  - category
  - access channel
  - unlock level
  - move detail when available

### get_move_detail

Input:

- `move_name` or `move_id`

Output:

- move identity
- move type
- category
- power
- energy cost
- effect text
- provenance

### get_ability_detail

Input:

- `ability_name`

Output:

- ability identity
- effect text
- confidence
- provenance

## Required Error Modes

The repository must distinguish:

- not found
- ambiguous match
- runtime DB unavailable
- malformed row / contract break

These should be surfaced as clean repository-level errors, not raw sqlite errors.

## Contract Rule

Advisor runtime may only depend on repository methods, not inline SQL spread
across unrelated modules.

## Provenance Rule

Every repository result used for confirmed factual claims should expose enough
source information to support evidence summaries.

