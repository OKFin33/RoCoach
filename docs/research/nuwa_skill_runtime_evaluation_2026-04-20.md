# Nuwa Skill Runtime Evaluation (Zero-Context External Document)

## Purpose

This document explains, for a zero-context external reader:

- what `nuwa-skill` is trying to do
- how it can actually be run in practice
- how an execution thread used it in a real bounded task
- what artifacts it produced
- what kind of persona output it ultimately generated
- how to evaluate whether a Nuwa run was real or just "Nuwa-style"

This document is intentionally written to be reusable outside the current
project. It is about the operational understanding and evaluation of
`nuwa-skill`, not about any single product architecture.

As of: `2026-04-20`

## 1. What Nuwa Skill Is

`nuwa-skill` is not just a "persona prompt".

Its intended value is to distill a target person or character into a structured
"operating system" rather than a pile of vibes. The public framing of the
upstream project emphasizes extracting:

- how the target speaks
- how the target thinks
- how the target judges
- what the target refuses to do
- where the target admits uncertainty or limitation

In practice, this means a good Nuwa run should produce something closer to a
persona doctrine than to a simple style sheet.

## 2. The Upstream Method, In Plain Language

The upstream project describes a workflow that is roughly:

1. collect public source material from multiple angles
2. split the collection into several research tracks
3. merge and normalize the evidence
4. build a temporary Nuwa-style skill artifact
5. run quality checks against that artifact
6. derive a stable distillation result

The important operational point is:

**A real Nuwa run leaves provenance.**

If there is no workdir, no research-track files, no merge step, no validation
step, and no template-shaped artifact, then the result is probably just a
manual persona summary inspired by Nuwa rather than a real Nuwa execution.

## 3. How This Evaluation Was Actually Done

This evaluation used the upstream repository directly rather than pretending the
skill was magically built into the local environment.

### 3.1 Local Repo Usage

The execution thread:

- cloned the upstream repository into `/tmp/nuwa-skill`
- used commit:
  - `26cc17eabe18ff1c629fe5eba193ecf08e09a771`
- explicitly read:
  - `README.md`
  - `SKILL.md`
  - `references/extraction-framework.md`
  - `references/skill-template.md`

This matters because it proves the thread was not merely inventing a fake
"Nuwa-style" process after the fact.

### 3.2 Workdir Creation

The execution thread created a dedicated local workdir:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/personas/nuwa_enzo_round`

Inside that directory, it created the six research tracks typically associated
with the Nuwa method:

- `01-writings.md`
- `02-conversations.md`
- `03-expression-dna.md`
- `04-external-views.md`
- `05-decisions.md`
- `06-timeline.md`

It also created a temporary Nuwa-style:

- `SKILL.md`

That file was used as the validation target for the upstream quality checker.

### 3.3 Bounded Execution Mode

The thread was intentionally run in a bounded, artifact-only mode:

- no runtime code changes
- no API changes
- no UI changes
- no mobile changes
- no automatic product integration

The only goal was to generate and validate persona distillation artifacts.

This is the correct way to evaluate a persona distillation workflow. If the
first step is already "inject it into runtime", the experiment is contaminated.

## 4. What the Execution Thread Actually Ran

The thread reported, and local verification confirmed, that it used the
upstream scripts:

- `merge_research.py`
- `quality_check.py`

The observed validation claims were:

- six dimensions present
- `15` tracked sources
- `6/6` quality checks passed

The important point is not the number itself. The important point is that the
run produced:

- a source trail
- a structured workdir
- a temporary Nuwa-style skill artifact
- script-validated output

That is enough to distinguish it from a freeform manual summary.

## 5. What Artifacts a Good Nuwa Run Should Produce

In this case, the thread produced three useful end artifacts:

### 5.1 Distillation Memo

This is the research explanation layer.

It should include:

- what sources were used
- which sources were trusted more
- which sources were weak or disputed
- what the distilled five-layer result is
- what remains ambiguous
- how the thread validated consistency

This artifact answers:

**"Why should I trust this persona summary at all?"**

### 5.2 Persona Doctrine Draft

This is the structured persona payload.

It should include fields roughly equivalent to:

- identifier / display name
- expression layer
- mental models
- decision heuristics
- anti-patterns
- honesty boundaries
- fact policy
- IP safety policy

This artifact answers:

**"What exactly did the system distill?"**

### 5.3 Mapping Note

This is the integration bridge.

It should include:

- which persona traits are for reasoning
- which persona traits are for rendering
- which traits are metadata only
- what would need sanitization before any public deployment

This artifact answers:

**"How would I actually use this in another system?"**

Without a mapping note, a persona distillation is still interesting, but not yet
implementation-ready.

## 6. The Enzo Case: What Was Distilled

The example target for this evaluation was an internal `Enzo` persona draft.

This was **not** treated as public-safe product copy. It was treated as an
internal doctrine candidate.

### 6.1 High-Level Persona Shape

The distilled `Enzo` is not mainly "evil", "mysterious", or "dramatic".

The core shape is:

**a high-control rationalist who values capability above comfort when facing
irreversible loss**

In plain terms, the persona treats these as central:

- power matters when the problem cannot be reversed
- institutions often protect order before truth
- failed orthodoxy weakens the moral force of prohibition
- hesitation has real cost
- sentiment without capability does not actually protect what matters

### 6.2 Top Mental Models

The distilled top mental models were summarized as:

1. power is for irreversible problems
2. institutions protect order before truth
3. prohibition must be re-examined after method failure
4. tragedy is usually prepaid by hesitation
5. sentiment without capability protects nothing

These are not just "quotes". They are intended as the stable internal lenses
through which the persona evaluates situations.

### 6.3 Top Decision Heuristics

The distilled top heuristics were summarized as:

1. escalate method when approved process fails
2. cut ornamental or fake paths quickly
3. judge plans by real cost transfer, not moral packaging
4. compress toward one hard recommendation once causality is clear
5. keep pressure controlled instead of melodramatic

This is important because it turns the persona from a style layer into a
judgement layer.

### 6.4 Anti-Patterns

The anti-patterns are what keep the persona from becoming generic.

Examples from this run:

- empty reassurance
- rule worship detached from consequence
- comfort-preserving half-measures
- competence-free moral posturing
- fake optionality when the causal picture is already clear

This is often the most useful section in practice, because it defines what the
persona will reject before it defines what the persona will say.

### 6.5 Honesty Boundaries

The distilled `Enzo` draft also included explicit honesty boundaries, such as:

- disputed lore must stay disputed
- inferred inner motives must be labeled as inference
- persona may not override grounded facts, warnings, confidence, or refusals
- dark methods should not be romanticized without evidence
- the draft is internal-only and unsafe for public default use

This is one of the strongest parts of the output, because it keeps the persona
from becoming a hallucination machine.

## 7. What the Final Output Looked Like

The final doctrine artifact was a structured YAML, not a blob of prose.

It included:

- `persona_id`
- `display_name`
- `expression_dna`
- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`
- `fact_policy`
- `ip_safety_profile`

That is the right shape for a serious persona system, because it can be:

- inspected
- revised
- validated
- partially mapped into reasoning
- partially mapped into rendering

This is much more reusable than a monolithic natural-language character prompt.

## 8. How the Mapping Worked

The most useful part of the run was that it explicitly split the distilled
result into three usage layers:

### 8.1 Reasoning-Facing

Used to shape how the system thinks:

- `mental_models`
- `decision_heuristics`
- `anti_patterns`
- `honesty_boundaries`

### 8.2 Rendering-Facing

Used to shape how the system sounds:

- `display_name`
- `expression_dna`
- `ip_safety_profile`

### 8.3 Metadata-Only

Used for governance, not runtime reasoning:

- source provenance
- confidence of sources
- stable vs disputed lore
- workflow evidence
- integration caution

This split is what makes the output useful for other projects. Without this
split, most persona distillations remain stuck at the "interesting writing
exercise" level.

## 9. Was This a Good Run

Short answer:

**Yes, as an internal doctrine run. No, as an immediately shippable persona.**

### Why It Was Good

- it used the upstream repository directly
- it left a real artifact trail
- it produced a contract-shaped doctrine draft
- it included uncertainty handling
- it separated reasoning from rendering
- it explicitly refused public-safe status

### Why It Was Not Final

- the target canon is fragmented
- exact chronology and motive weighting remain disputed
- the draft is character-specific and still contaminated by official-IP context
- the output is not automatically ready for public product use

So the correct rating is:

- **good internal doctrine candidate**
- **not final public persona**

## 10. How to Judge Whether Another Team Actually Used Nuwa

If you want to evaluate another run, look for these signals:

### Strong signals that the run was real

- upstream repo / commit recorded
- required source framework files read
- dedicated workdir created
- six research tracks populated
- temporary Nuwa-style `SKILL.md` generated
- merge and quality scripts executed
- output contains provenance and uncertainty notes

### Red flags that it was mostly fake

- only a final persona paragraph exists
- no workdir
- no six-track evidence
- no mention of merge / validation
- no uncertainty handling
- no split between reasoning-facing and rendering-facing traits

## 11. What Other Projects Can Reuse

Even outside the current project, the reusable lessons are:

1. **Do not store persona as one blob**
   - split reasoning doctrine from rendering style

2. **Do not skip provenance**
   - a persona with no source trail is just fanfiction with better formatting

3. **Distill anti-patterns and honesty boundaries**
   - they are often more valuable than tone adjectives

4. **Treat public-safe release as a separate review step**
   - an internally useful character doctrine is not automatically safe to ship

5. **Use Nuwa as a distillation workflow, not just as a prompt aesthetic**

## 12. Final External Summary

This evaluation shows that `nuwa-skill` can be used as a serious persona
distillation workflow if it is run with:

- upstream provenance
- structured evidence collection
- explicit validation
- doctrine-shaped output
- reasoning/rendering split

In the Enzo case, the result was not a shallow "cool villain persona". It was a
structured internal doctrine describing a consequence-first, capability-driven,
high-control rationalist with explicit anti-patterns and honesty boundaries.

That is strong evidence that Nuwa can produce useful persona substrates for
other systems, provided the team treats the result as doctrine to be integrated,
not as a ready-made runtime prompt.
