---
title: "Synthetic Team Review Protocol"
content_class: "casebank"
status: "reviewed"
confidence: "provisional"
sources:
  - "specs/battle_wiki_architecture_spec.md"
  - "wiki/schema/provenance_policy.md"
  - "wiki/pages/team_building/core_team_construction.md"
  - "wiki/pages/recommendation_taste/early_meta_uncertainty.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-20"
reviewed_by: "first_wiki_closure"
persona_free: true
---

# Synthetic Team Review Protocol

## Claim

Model-inferred team logic can be stored as useful learning material only after
review. It must never enter the wiki as raw authority.

The correct class is reviewed case material, not A-layer fact.

## Strategic Use

For a weekly report or user-provided team:

1. Extract the team list, source date, and source confidence.
2. Retrieve A-layer facts: types, stats, moves, energy, traits, known mechanics.
3. Retrieve B-layer doctrine: roles, loops, marks, weather, response, stat
   selection, uncertainty policy.
4. Infer the team logic: win condition, setup, conversion, protection,
   counterplay, and failure modes.
5. Review the inference for fact errors and overclaiming.
6. Store only reviewed conclusions with confidence and source trail.

## Storage Shape

Use a casebank page or raw battle review note with:

```yaml
source_date: ""
source_confidence: ""
team_input: "summary, not full copyrighted dump"
inferred_loop: ""
key_roles: []
a_layer_checks: []
review_status: "needs_human_review | reviewed"
confidence: "provisional | low_confidence"
volatile_until: "next_patch_or_meta_shift"
```

## Evidence

The architecture spec defines B Wiki as reviewable doctrine and explicitly
forbids raw LLM output presented as authority. The provenance policy allows
LLM-generated drafts only after human review.

## Confidence

`provisional`.

High confidence:

- model synthesis must be review-gated
- synthesized team logic belongs in B/casebank, not A
- exact facts must be checked against A-layer sources

Medium confidence:

- exact schema for future casebank automation

## A-Layer Boundary

Synthetic case notes cannot create new species, move, trait, weather, mark, or
damage facts. They may only cite A-layer facts or mark unresolved assumptions.

## Known Failure Modes

- Letting the model write its own hallucination into the library.
- Storing a teamlist without source date.
- Storing a conclusion without A-layer checks.
- Treating one reviewed case as general archetype truth.
- Mixing persona taste into default doctrine.

## Draft Review Questions

- Should every synthetic case require human approval before compiled export?
- Should a reviewer score fact accuracy and tactical plausibility separately?
- What fields should become machine-validated in `chunks.jsonl`?
