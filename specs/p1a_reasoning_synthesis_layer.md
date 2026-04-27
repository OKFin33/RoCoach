# P1a Reasoning / Synthesis Layer

## Purpose

Define the first post-P0 layer that turns grounded analytical substrate plus
approved battle doctrine into product-facing advisory reasoning.

This is the point where LLM becomes the product's core analysis unit, without
becoming the source-of-truth unit.

## Core Equation

The approved product direction is:

`Final advisory reasoning = Synthesize(A, B)`

Where:

- `A` = grounded analytical substrate
  - deterministic Engine output
  - SQL / battle-dex facts
  - bounded retrieval facts
  - validated confidence/refusal boundaries
- `B` = battle doctrine pack
  - approved mechanics interpretation
  - methodology guidance
  - role/archetype taxonomy
  - accepted tactical taste constraints
  - persona doctrine fields allowed by
    `specs/persona_doctrine_contract.yaml`

## Hard Rule

LLM is the core reasoning unit, not the source-of-truth unit.

Therefore synthesis may:

- interpret
- prioritize
- explain
- weigh tradeoffs
- generate concrete advisory judgement

But synthesis may not:

- invent facts outside `A`
- override Engine / SQL / approved-doc truth
- erase confidence boundaries
- suppress refusals

## Output Responsibility

The synthesis layer should produce:

- one concrete judgement
- one compact reasoning path
- one set of surfaced warnings
- one set of follow-up directions
- one stable handoff to presentation

## Responsibilities

The synthesis layer must:

1. consume `A` and `B`
2. answer the user's specific question
3. keep deterministic facts fixed
4. make non-deterministic judgement explicit but grounded
5. separate strong conclusions from provisional interpretation
6. use only the reasoning-facing subset of persona doctrine:
   - `mental_models`
   - `decision_heuristics`
   - `anti_patterns`
   - `honesty_boundaries`

The synthesis layer must not:

- directly render final user-facing persona style
- dump raw tool traces as if that were reasoning
- claim unsupported meta knowledge
- act as an open-ended agent planner

## Examples Of What Belongs Here

- why a team's real problem is not only repeated weakness, but compression of
  available patch directions
- why a species is acting more like a pivot than a primary closer in this team
- why the same species may occupy different jobs in different team structures
- how the same team issue may be framed differently under different persona
  doctrines without changing the underlying facts

## Acceptance Criteria

P1a is acceptable when:

- the system no longer relies on raw analytical payload formatting as the main
  analysis experience
- product-facing analysis is clearly synthesized from grounded inputs
- synthesis does not weaken fact/evidence/confidence discipline
- the output is usable as input to a later `Reply + Why` presentation layer
