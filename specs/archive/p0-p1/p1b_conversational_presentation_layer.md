# P1b Conversational Presentation Layer

## Purpose

Define the layer that turns synthesized advisory reasoning into the default
coach-style conversational surface.

This layer exists because the product should feel like chatting with a coach,
not reading a mini report.

## Default Front-Stage Surface

The front-stage output should be:

- `Reply`
- `Why`

Where:

- `Reply` = the main coach-style answer
- `Why` = the compact explanation most users actually need

The user should not need to read raw evidence/confidence/tool fields to
understand the conclusion.

## Secondary Surface

The system must still expose, behind an inspectable detail layer:

- evidence
- confidence notes
- refusal boundaries
- tool traces
- analytical/base answer when needed

## Responsibilities

The presentation layer must:

1. consume synthesis output
2. render one strong `Reply`
3. render one concise `Why`
4. keep material warnings visible in `Reply` or `Why`
5. preserve follow-up affordances

The presentation layer must not:

- change factual meaning
- upgrade or downgrade confidence
- hide critical boundaries
- turn every answer into a verbose monologue

## Warning Policy

Material warnings must remain visible when triggered, including:

- partial-team analysis
- provisional-only interpretation
- deterministic fallback after native failure
- unsupported scope
- refusal due to missing context or missing species

## Acceptance Criteria

P1b is acceptable when:

- the default mobile/chat reply feels conversational
- `Reply + Why` is enough for most users
- evidence/confidence remain inspectable but not foregrounded
- rendering introduces no factual or confidence drift
