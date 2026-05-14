# You Know Who Minimal Mapping Note

## Purpose

This note maps the sanitized `You know who` doctrine into the project persona
contract and separates synthesis-facing, rendering-facing, and metadata-only
layers.

Primary source:

- internal Enzo Nuwa draft artifacts under `docs/personas/`

Public-surface target:

- `persona_id`: `you_know_who`
- `display_name`: `You know who`

## Synthesis-Facing Fields

These fields may shape advisory reasoning style:

- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`

Expected synthesis effect:

- stronger consequence-first diagnosis
- faster pruning of fake optionality
- less empty reassurance
- clear separation between viable structure and decorative preference

Hard rule:

- these fields may not alter facts, evidence, confidence, warnings, refusals,
  scores, or final team-building decisions

## Rendering-Facing Fields

- `display_name`
- `expression_dna`
- `rendering_flavor_rules`
- `ip_safety_profile`

Expected rendering effect:

- colder, tighter sentence shape
- more direct boundary setting
- mild expression-only hostility when grass-type context triggers
  `grass_type_hostility`

Hard rule:

- rendering is expression-only
- it must not introduce factual drift or recommendation drift

## Metadata-Only Fields And Notes

These should not directly enter synthesis or rendering:

- internal Enzo source provenance
- Nuwa workflow history
- internal source confidence tiers
- sanitization rationale
- any official-character or franchise-origin explanation

Recommended metadata to carry alongside the doctrine:

- `facts_locked: true`
- `generated_via: sanitized_minimal_public_surface_abstraction`
- `source_internal_only: docs/personas/enzo_internal_*`
- `public_label: You know who`

## Field Mapping From Internal Draft To Public Doctrine

Internal draft field -> public doctrine field:

- internal `expression_dna` -> abstracted `expression_dna`
- internal `mental_models` -> generalized `mental_models`
- internal `decision_heuristics` -> generalized `decision_heuristics`
- internal `anti_patterns` -> public-safe `anti_patterns`
- internal `honesty_boundaries` -> public-safe `honesty_boundaries`
- product flavor request -> `rendering_flavor_rules.grass_type_hostility`
- project IP guard constraints -> `ip_safety_profile`

## Public-Safe Sanitization Applied

1. Removed direct official-IP identity markers from public identity.
2. Replaced canon-specific tragedy/lore anchors with transferable advisory
   mechanics.
3. Preserved only safe abstract patterns:
   - compressed severity
   - consequence-first judgement
   - anti-mediocrity framing
   - helplessness debt without naming a specific loss
   - suspicion of systems that smooth over failed methods
   - taboo-method scrutiny without romanticizing forbidden knowledge
   - delay as hidden accumulated cost
   - explicit uncertainty under incomplete evidence
4. Kept `fact_policy: persona_may_not_alter_facts`.

## Integration Review Verdict

This doctrine is acceptable as a minimal managed persona candidate for local
runtime insertion and further PM/design review.

It is still not final brand copy. Before broad distribution, run explicit
`public_safe_release` validation and live output QA.
