# Enzo Integration Review

## Purpose

Review the verified Nuwa-based internal `Enzo` doctrine draft and decide what
may be retained, abstracted, sanitized, or forbidden before the project moves
into `P1a Reasoning / Synthesis Layer` implementation planning.

This review is not a public-safety release approval. It is the main-thread
bridge between a character-specific doctrine draft and the generic persona
architecture.

## Inputs Reviewed

- `docs/personas/enzo_internal_persona_doctrine.yaml`
- `docs/personas/enzo_internal_mapping_note.md`
- `docs/personas/enzo_internal_distillation_memo.md`
- `specs/persona_doctrine_contract.yaml`
- `specs/p1a_reasoning_synthesis_layer.md`
- `specs/p1b_conversational_presentation_layer.md`
- `specs/p1c_pluggable_persona_contract.md`

## Review Verdict

Status: `accepted_for_internal_pattern_extraction`

Meaning:

- accepted as a valid internal doctrine sample
- not accepted as a public-safe persona
- not accepted as a direct runtime default persona
- accepted as the reference sample for shaping `P1a` synthesis and later
  persona-registry rules

## Retain / Abstract / Sanitize / Forbid

### Retain

These fields should remain intact in the internal `Enzo` sample and may be used
for internal synthesis/presentation experiments:

- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`
- `fact_policy`
- `expression_dna` as an internal rendering sample

Reason:

- they are structurally aligned with `persona_doctrine_contract.yaml`
- they demonstrate the difference between persona doctrine and shallow style
- they provide a high-pressure, consequence-first reasoning sample that is
  useful for `P1a`

### Abstract

The following should be extracted as generic reusable tactical-persona patterns
rather than left only as Enzo-specific doctrine:

- consequence-first judgement under irreversible stakes
- anti-fake-optionality pruning
- discomfort with ornamental process that fails the objective
- controlled severity instead of melodrama
- explicit uncertainty retention when evidence is disputed
- preference for one hard recommendation once causal structure is clear

These should become generic reusable concepts for the future persona system:

- `high_pressure_consequence_frame`
- `compressed_verdict_style`
- `anti_comfort_theater_heuristic`
- `disputed_evidence_honesty_rule`
- `method_over_moral_packaging_check`

### Sanitize

The following may be reused only after sanitization or abstraction:

- `display_name`
- direct lore anchors tied to academy/kingdom/forbidden-research narrative
- grief-specific causal framing when it depends on continuity-specific lore
- `ip_safety_profile.forbidden_markers` entries that are franchise-entity names

Sanitization target:

- convert franchise-specific tragedy and institutional conflict into transportable
  doctrine language
- preserve tactical cognition, remove official-character identifiers

### Forbid

The following must not enter the generic runtime layer, generic persona
registry, or any public-safe persona package in their current form:

- direct use of `Enzo` / `恩佐` as a public or default persona id
- direct use of franchise-specific names in renderable persona surfaces
- official-character implication in product messaging
- any attempt to treat disputed lore as factual doctrine input
- any persona behavior that weakens fact/evidence/confidence/refusal boundaries

## Generic Persona Patterns Identified

The Enzo sample yields the following transferable persona-pattern candidates:

1. **High-Control Consequence Analyst**
   - evaluates plans by consequence absorption, not appearance
   - useful for severe tactical personas

2. **Compressed Verdict Persona**
   - avoids comfort-buffet outputs
   - moves quickly toward one concrete recommendation

3. **Institution-Skeptical Diagnostic Frame**
   - useful when a persona should question conventional but ineffective lines
   - must remain bounded by facts and safety rules

4. **Disputed-Evidence Honesty Persona**
   - explicitly marks lore or evidence uncertainty instead of flattening it
   - highly reusable across future personas

5. **Controlled-Pressure Render Style**
   - pressure comes from structural diagnosis, not theatrical aggression
   - suitable for tactical-coach surfaces

## Task-Adaptation Implications

The Enzo sample is good enough to influence task-specific synthesis behavior.

### Team Structure Analysis

Expected adaptation:

- prioritize repeated exposure and cost transfer over cosmetic coverage
- collapse fake patch directions faster
- surface when a team is preserving comfort rather than solving the core hole

Approved use:

- synthesis weighting
- phrasing pressure

Not approved:

- inventing higher risk than the Engine shows

### Species Role Analysis

Expected adaptation:

- push toward clearer job assignment
- challenge ambiguous "can do everything" readings
- prefer one primary role hypothesis when grounded evidence is sufficient

Approved use:

- narrowing the interpretation
- why-summary framing

Not approved:

- presenting semantic role judgement as confirmed fact

### Patch Direction / Recommendation

Expected adaptation:

- reduce decorative recommendation spread
- prefer one hard direction plus one constrained alternative at most
- explain cost of delay or indecision when evidence supports it

Approved use:

- recommendation compression
- follow-up direction shaping

Not approved:

- suppressing mandatory warnings

### Low-Evidence / Disputed Context

Expected adaptation:

- explicitly mark disputed material
- treat inference as inference
- keep strong tone without pretending certainty

Approved use:

- honesty-boundary activation

Not approved:

- lore flattening for style coherence

## Integration Decision For P1a

`P1a` should not implement "Enzo runtime" first.

It should implement:

- a generic doctrine-aware synthesis path
- support for a reasoning-facing doctrine subset
- one internal sample doctrine fixture based on Enzo
- test coverage proving doctrine can shape reasoning without changing facts

## Gate Outcome

`Enzo integration review` is complete.

Gate effect:

- Gate 1 is now open
- the next unlocked step is:
  - `P1a synthesis implementation spec`

## Non-Goals Of This Review

- no public-safe persona approval
- no runtime registry implementation
- no second persona sample
- no Nexus adapter work
- no presentation implementation
