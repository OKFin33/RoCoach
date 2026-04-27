# Enzo Internal Mapping Note

## Purpose

This note maps the completed Nuwa round into the project's persona doctrine
contract and explicitly separates synthesis-facing, rendering-facing, and
metadata-only layers.

Primary provenance for this mapping:

- upstream Nuwa repo: `/tmp/nuwa-skill`
- Nuwa workdir: `docs/personas/nuwa_enzo_round/`
- final doctrine artifact:
  - `docs/personas/enzo_internal_persona_doctrine.yaml`

## Synthesis-Facing Fields

These are the only doctrine fields that should shape synthesis under
`specs/p1a_reasoning_synthesis_layer.md`:

- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`

Expected synthesis effect:

- more consequence-first and anti-naive judgement
- stronger pruning of fake optionality
- more willingness to challenge institutionally comfortable framings
- explicit uncertainty retention when lore evidence is disputed

Hard rule:

- these fields may shape reasoning style only
- they may not alter facts, confidence, evidence attribution, surfaced warnings,
  or refusals

## Rendering-Facing Fields

- `display_name`
- `expression_dna`
- `ip_safety_profile`

Expected rendering effect:

- colder, tighter sentence shape
- earlier diagnosis and harder conclusion
- less reassurance by default
- pressure through control, not noise

Hard rule:

- rendering is expression-only
- it must not introduce factual drift or confidence drift

## Metadata-Only Fields And Notes

These should not directly enter synthesis or rendering:

- source provenance from the memo
- confidence tiers by source class
- stable-vs-disputed lore split
- Nuwa workflow evidence:
  - upstream repo commit `26cc17eabe18ff1c629fe5eba193ecf08e09a771`
  - use of `merge_research.py`
  - use of `quality_check.py`
- sample-question consistency checks
- integration caution that this is an internal-only candidate

Recommended metadata to carry alongside the doctrine:

- `facts_locked: true`
- `integration_review_pending`
- `generated_via: upstream_nuwa_round`
- `nuwa_workdir: docs/personas/nuwa_enzo_round`

## Field Mapping From Nuwa Round To Doctrine Contract

Nuwa round artifact -> doctrine field:

- `SKILL.md` expression rules -> `expression_dna`
- `SKILL.md` core mental models -> `mental_models`
- `SKILL.md` decision heuristics -> `decision_heuristics`
- `SKILL.md` value rejection / anti-pattern language -> `anti_patterns`
- `SKILL.md` honest boundary section -> `honesty_boundaries`
- project architecture constraints -> `fact_policy`
- project IP guard constraints -> `ip_safety_profile`

## Public-Safe Sanitization Required Before Any Broader Use

1. Remove all direct official-IP identifiers from renderable persona surfaces.
2. Replace canon-specific tragedy anchors with transportable abstract doctrine.
3. Strip continuity-dependent references that require franchise context.
4. Preserve only safe transferable patterns:
   - compressed severity
   - consequence-first judgement
   - anti-mediocrity framing
   - explicit uncertainty under disputed evidence

## Integration Review Verdict

This doctrine draft is ready for integration review as an internal candidate.
It is not ready for:

- public-safe runtime selection
- default shipping
- any product surface that implies official character authorization
