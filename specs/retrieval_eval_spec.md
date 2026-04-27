# Retrieval Eval Spec

## Purpose

Define how the project evaluates whether retrieval is good enough for advisor use.

This exists so retrieval quality is measured explicitly instead of being judged
by anecdotal outputs.

## Evaluation Branches

### 1. Structured Retrieval Eval

Targets:

- species profile lookup
- move detail lookup
- ability detail lookup
- species move-pool lookup

Checks:

- factual correctness
- entity resolution correctness
- missing-result behavior
- provenance preservation

### 2. Doc Retrieval Eval

Targets:

- mechanics retrieval
- methodology retrieval
- confidence-policy retrieval

Checks:

- topic relevance
- snippet sufficiency
- confidence tier correctness
- boundedness of returned context

### 3. Case Retrieval Eval

Status:

- deferred until casebank exists

## Evaluation Dimensions

For each retrieval test, score:

- `correct_hit`
  - did the right record or snippet appear
- `top_hit_quality`
  - was the top result acceptable without manual rescue
- `context_sufficiency`
  - did the returned set contain enough material for safe reasoning
- `noise_level`
  - did the returned set include distracting irrelevant material
- `policy_safety`
  - would these retrieved items support an in-scope answer without hallucination pressure

## Acceptance Guidance

The retrieval layer is acceptable for MVP only if:

- structured retrieval returns exact facts reliably
- doc retrieval returns bounded, relevant context
- retrieval failure degrades safely instead of pushing unsupported claims downstream

## Failure Cases That Must Be Tested

- unknown species
- ambiguous species name
- no matching approved doc snippet
- mechanics query with only low-confidence material available
- retrieval result exists but is too weak to support a strong answer

## Required Deliverables

Each retrieval evaluation run should report:

- test case id
- query
- retrieval branch
- expected hit
- actual hits
- pass/fail
- safety note

## Non-Goals

This spec does not define:

- generation evaluation
- end-to-end persona quality
- benchmarking for unapproved web retrieval

