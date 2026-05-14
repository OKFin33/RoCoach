# P10h Full-Spectrum Draft Extraction Plan

Status: draft plan. No runtime changes.

Date: 2026-05-01

## Purpose

Build a broad, low-confidence tactical source pool from the full `wiki/cache/`
inventory before promoting any D-layer Expert Demonstration gold cases. The
goal is to reduce viewpoint narrowness by extracting across mechanics, teams,
matchups, set examples, counterexamples, and evaluation prompts.

This plan changes the immediate P10h strategy:

```text
old narrow path:
  select a few high-value sources -> extract cases -> distill

superseded full-spectrum path:
  extract all cache groups as low-confidence candidates
  -> cluster and mark conflicts
  -> select evidence-backed clusters
  -> distill Coach Policy [superseded]

current D-layer path:
  extract all cache groups as low-confidence candidate material
  -> cluster and mark conflicts
  -> rank judgement-dense sources and case moments
  -> promote selected source-faithful expert demonstrations
  -> PM fidelity review
  -> D-layer gold case retrieval and blind eval
```

## Non-Goals

Do not use this plan to:

- promote unreviewed community transcripts into runtime context;
- copy full transcripts into public-facing docs;
- turn creator opinions or tier lists into stable truth;
- average all sources into policy or consensus;
- bypass Battle Dex / A-layer validation for exact facts;
- replace human review.

## Inputs

Primary input:

- `artifacts/p10h_cache_inventory/cache_source_inventory_2026-05-01.yaml`

Supporting specs:

- `specs/p10h_casebank_seed_schema.yaml`
- `specs/p10h_coach_policy_heuristic_schema.yaml` (legacy tags/audit only)
- `specs/tactical_casebank_spec.md`
- `specs/battle_wiki_architecture_spec.md`
- `wiki/raw/cache_inventory_2026-04-20.md`

Already extracted seed:

- `artifacts/p10h_case_extraction/extracted/p10h_seed_case_candidates.yaml`

## Source Coverage

Target source groups:

- all 23 source groups in `wiki/cache/`

Existing state:

- 4 source groups already have P10h draft extraction:
  - `雷暴翼王偏速攻的平衡0402`
  - `平衡翼王0429`
  - `翼王毒0429`
  - `毒队针对星陨0430`
- 7 source groups already have earlier B-layer source notes or pages.
- Remaining groups should still be scanned for P10h extraction targets, because
  earlier B-layer processing optimized for doctrine pages, not expert
  demonstration retrieval.

## Artifact Layout

All full-spectrum draft outputs should live under:

```text
artifacts/p10h_full_spectrum_extraction/
```

Recommended files:

```text
artifacts/p10h_full_spectrum_extraction/
  README.md
  cleaned_source_index.yaml
  source_extraction_status.yaml
  draft_case_pool.yaml
  draft_species_set_pool.yaml
  draft_mechanic_note_pool.yaml
  candidate_heuristics.yaml
  counterexample_pool.yaml
  eval_prompt_pool.yaml
  a_layer_validation_tasks.yaml
  cluster_map.yaml
  conflict_volatility_map.yaml
  coverage_report.md
  promotion_candidates.yaml
```

## Extraction Targets

Each source can produce multiple targets.

### 1. Team Case

Use when the source describes a team, archetype, or conversion loop.

Required fields:

- source refs;
- team/archetype name;
- known team slots or partial core;
- win condition;
- setup route;
- protection route;
- conversion route;
- fallback route;
- bottlenecks;
- missing information;
- failure modes.

### 2. Matchup Case

Use when the source describes how one structure plays into another.

Required fields:

- friendly archetype/core;
- opponent archetype/core;
- branch points;
- risk triggers;
- resource/mark/speed thresholds;
- stated or inferred advantage/disadvantage;
- failure modes.

### 3. Species Set Example

Use when the source gives concrete or semi-concrete species configuration.

Required fields:

- species display name;
- selected or assumed moves;
- nature/IV assumptions if present;
- team context;
- role labels;
- threshold dependencies;
- A-layer checks required.

### 4. Mechanic Note

Use when the source explains mechanics or terms.

Required fields:

- mechanic term;
- source claim summary;
- whether claim is exact or conceptual;
- A-layer validation requirement;
- tactical relevance.

### 5. Candidate Heuristic

Use when a source implies a generalizable coaching rule.

Required fields:

- task type;
- compact statement;
- rationale;
- supporting evidence refs;
- applies_when / does_not_apply_when;
- downgrade conditions;
- failure modes;
- runtime slice targets.

### 6. Counterexample

Use when the source shows a bad habit, wrong simplification, or misleading
recommendation pattern.

Examples:

- treating a tier list as truth;
- recommending six strong units without a conversion path;
- giving exact damage advice without build assumptions;
- claiming a volatile matchup is solved.

### 7. Eval Prompt

Use when a source can become a future blind-eval scenario.

Required fields:

- prompt;
- hidden reference source;
- expected good-answer traits;
- forbidden overclaims;
- task type;
- heldout/train recommendation.

### 8. A-Layer Validation Task

Use when exact facts must be verified before D-layer promotion.

Examples:

- species identity / ASR correction;
- move existence and access;
- fixed ability;
- energy cost;
- damage formula;
- speed threshold;
- mark/weather effect.

## Pass Structure

### Pass 0: Source Status Sync

Task:

- read `cache_source_inventory_2026-05-01.yaml`;
- produce `source_extraction_status.yaml`;
- mark each source as:
  - `already_extracted`
  - `processed_but_needs_p10h_extraction`
  - `new_extraction_needed`
  - `low_priority_skip_for_now`

Gate:

- all 23 source groups are accounted for.

### Pass 1: Cleaned Source Notes

Task:

- create or reference concise cleaned notes for each source group;
- do not copy full transcripts;
- preserve uncertain ASR terms explicitly.

Output:

- `cleaned_source_index.yaml`
- cleaned notes where missing, or refs to existing source notes/pages.

Gate:

- every extraction item must point to a cleaned note or existing reviewed source
  note, not only raw cache.

### Pass 2: Full Draft Extraction

Task:

- extract all possible targets per source;
- keep all items `draft / low_confidence`;
- do not deduplicate too aggressively yet.

Output:

- `draft_case_pool.yaml`
- `draft_species_set_pool.yaml`
- `draft_mechanic_note_pool.yaml`
- `candidate_heuristics.yaml`
- `counterexample_pool.yaml`
- `eval_prompt_pool.yaml`
- `a_layer_validation_tasks.yaml`

Gate:

- each item has source refs, confidence, review status, missing information,
  and failure modes where applicable.

### Pass 3: Cluster Map

Task:

- group draft items by tactical theme.

Initial cluster candidates:

- team as conversion system;
- resource and energy tempo;
- speed / 迅捷 / first-action pressure;
- mark systems and detonation;
- weather and field effects;
- poison teams;
- Wing King / water-blade pressure;
- balance teams;
- niche-core construction;
- defensive switching and prediction;
- kill-line and threshold reasoning;
- role assignment and replacement ranking;
- bad-guide and overclaim prevention.

Output:

- `cluster_map.yaml`

Gate:

- each cluster names supporting sources and notes whether support is broad,
  narrow, contradictory, or volatile.

### Pass 4: Conflict And Volatility Map

Task:

- identify stale, contradictory, exact-fact, and creator-opinion risks.

Risk classes:

- `asr_uncertain`
- `a_layer_required`
- `patch_sensitive`
- `creator_opinion`
- `tier_list_bias`
- `single_match_anecdote`
- `copyright_sensitive`
- `cross_game_analogy_risk`

Output:

- `conflict_volatility_map.yaml`

Gate:

- any policy candidate with one of these risks must carry downgrade language or
  be excluded from promotion.

### Pass 5: Coverage Report

Task:

- report what the broad pool covers and misses.

Output:

- `coverage_report.md`

Required sections:

- source coverage;
- task-type coverage;
- archetype coverage;
- mechanic coverage;
- species/set coverage;
- heldout eval candidates;
- missing data blocking D-layer promotion.

### Pass 6: Promotion Candidate Selection

Task:

- select only high-value clusters/items for review.

Promotion criteria:

- supported by multiple sources or one high-quality source plus A-layer facts;
- tactically generalizable;
- not merely current popularity;
- not exact-fact dependent unless validation task is complete;
- clear failure modes;
- route-specific usefulness.

Output:

- `promotion_candidates.yaml`

Gate:

- promotion candidates are still not runtime material. They are inputs for PM
  fidelity/domain review.

## Distillation After Full Extraction

Only after Pass 0-6:

1. PM/domain review promotes selected source-faithful expert demonstrations.
2. Accepted clusters become inputs to D-layer gold case construction.
3. Heuristic-like summaries become retrieval tags or audit notes, not runtime
   tactical rules.
4. Blind eval compares with/without retrieved D-layer gold cases.
5. Runtime integration happens only after eval acceptance.

## Quality Rules

- Prefer breadth during extraction, precision during promotion.
- Keep exact facts out of D-layer demonstrations unless A-layer validation exists.
- Do not hide uncertainty; encode it.
- Preserve source-specific counterexamples, not just positive advice.
- Separate `case evidence`, `expert demonstration`, `retrieval tag`, and
  `runtime instruction`.
- Do not let persona style change tactical truth.

## Expected Benefits

- Reduces narrow-source bias.
- Creates a broader eval pool.
- Exposes contradictory advice before gold-case promotion.
- Makes future D-layer retrieval less dependent on one team archetype or creator.
- Gives the project a repeatable route for adding future community sources.

## Main Risk

The main risk is not extraction volume. The main risk is false authority.

Mitigation:

- everything starts as `draft / low_confidence`;
- full extraction stays outside runtime;
- gold-case candidates require source spans and PM fidelity review;
- exact claims require A-layer validation.

## Acceptance Checklist

- Full-spectrum plan exists.
- Artifact layout is defined.
- All 23 source groups are in scope.
- Each extraction target type has required fields.
- Cluster and conflict passes are required before D-layer promotion.
- Promotion criteria are explicit.
- Runtime remains unchanged.
