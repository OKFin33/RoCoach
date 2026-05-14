# P10h Expert Demonstration Extraction Manual

## Status

Agent-executable draft v1.

This manual is for processing one high-player video transcript or cleaned note
into D-layer Expert Demonstration candidate cases.

No runtime code, gold case pool, or original source file may be modified by this
manual unless a separate task explicitly requests that.

## 0. Objective

Input:

- one source transcript or cleaned note;
- optional source group metadata;
- existing P10h name-resolution overlays and A-layer Battle Dex database.

Output:

- multiple candidate Expert Demonstration cases;
- source manifest;
- name-resolution notes;
- A-layer validation tasks;
- PM fidelity-review packet;
- extraction summary.

Core unit:

- `judgement moment`, not the whole video.

The executing Agent must extract how an expert judged a concrete situation. Do
not convert the video into a generic tactical rulebook.

## 1. Required Project Context

Roco uses the following knowledge layers:

| Layer | Name | Responsibility |
|---|---|---|
| A | Battle Dex Structured Facts | Species, moves, fixed ability, stats, forms, selected team context |
| B | Battle Wiki / Knowledge Materials | Mechanics docs, terminology, cleaned source material |
| C | Governance & Runtime Policy | Trust tiers, prompt boundaries, privacy, uncertainty, retrieval-use rules |
| D | Expert Demonstration Case Memory | PM fidelity-reviewed expert judgement examples |
| Persona | Expression Layer | Writing voice only; never tactical truth |

This manual produces D-layer candidates only. A/B/C may be referenced for
grounding and governance, but the output of this task is not itself runtime
material.

Relevant specs:

- `specs/p10h_tactical_coach_policy_distillation_plan.md`
- `specs/p10h_casebank_seed_schema.yaml`
- `specs/p10h_full_spectrum_draft_extraction_plan.md`
- `specs/p10h_expert_demo_extraction_manual.md`
- `artifacts/p10h_name_resolution_cleanup/`

## 2. Layer Zero: Domain Anchor And Bias Guard

The executing Agent must not assume it understands 洛克王国世界 by analogy to
Pokemon, generic RPGs, card games, or MOBAs.

World declaration:

- This is 洛克王国世界 / Roco Kingdom context.
- Species, move, fixed ability, form, stat, and move-access facts must come from
  Roco project data sources, not from memory or cross-game analogy.
- Expert judgement must come from cited source spans.
- Mechanic/strategy terminology can come from B-layer docs or source text, but
  must be marked unresolved when unclear.

Fact-source boundary:

| Claim Type | Source Of Truth |
|---|---|
| species identity / form / fixed ability / stats | A-layer Battle Dex, preferably through `advisor/battle_dex.py` or SQLite |
| move existence / move text / move access | A-layer Battle Dex |
| combat mechanics and Roco terminology | B-layer docs or source text, with uncertainty marked |
| expert decision pattern | cited transcript/source span |
| runtime usage rules | C-layer specs |

Do not say every useful term must exist in Battle Dex. Tactical words such as
`中转`, `压制`, `卖掉`, `节奏`, or `残局路线` may be source/B-layer terms. Battle
Dex is authoritative for structured facts, not for every tactical phrase.

Forbidden imported assumptions:

- Do not import Pokemon rules, terminology, team-building defaults, or combat
  frameworks.
- Do not use EV / effort-value / item / held-item / tera / nature-effort
  frameworks.
- Do not assume abilities are selectable. In Roco, ability is fixed per
  species/form unless A-layer data proves otherwise.
- Do not assume standard Pokemon speed tiers or type-chart-only analysis.
- Do not default to generic RPG cultivation, leveling, resource farming, or
  training advice.
- Do not treat a single species baseline as a fixed team role across all teams.

Common contamination patterns:

| Pattern | Forbidden Behavior | Correct Behavior |
|---|---|---|
| Pokemon analogy | "这个技能类似剑舞/钉子/太晶..." | Describe only with Roco source terms or mark unresolved |
| Type-chart shortcut | Reducing analysis to attribute restraint only | Check move text, energy/resource, marks/status, fixed ability, and team role when relevant |
| Selectable ability assumption | Treating ability as a build option | Treat ability as fixed per species/form unless A-layer proves otherwise |
| Item/EV import | Mentioning held items, EV spreads, effort values, tera | Use Roco terms: selected moves, nature, 个体增益, fixed ability |
| Generic RPG scope | Giving leveling/cultivation/farming advice | Reject as outside current battle-analysis scope unless explicitly grounded |

Required grounding behavior:

- Use Battle Dex for species, move, ability, form, and stat facts.
- Use the transcript/source span for expert judgement.
- Mark unknown mechanics as unresolved instead of guessing.
- Preserve 洛克王国世界 terminology when known.
- Keep source claims provisional unless supported by A-layer facts or PM review.

Terminology policy:

```yaml
terminology_policy:
  game_domain: 洛克王国世界
  hp_display: 生命
  individual_value_bonus: 个体增益
  fixed_ability: fixed per species/form unless A-layer says otherwise
  selected_move_count: 0_to_4
  team_size: 0_to_6
```

Mechanic hierarchy:

| Layer | Examples | Extraction Rule |
|---|---|---|
| Global battle resources | energy/resource windows, action timing | Check when the source or case makes them relevant |
| Persistent/layered mechanics | marks, status, weather/field-like effects, ongoing effects | Record stack/count/trigger language when present |
| Move structure | move slot, cost, category, power, response/priority/trigger text | Verify from A-layer if used as fact |
| Species fixed facts | type, fixed ability, stats, form | Verify from A-layer |
| Team structure | lead, pivot, closer, defensive/offensive coverage, tempo axis | Extract from source; do not globalize |
| Type-affordance mechanics | `迅捷` and similar type-linked mechanics | Treat as a mechanic family, not a universal resource |

Type-affordance mechanic policy:

```yaml
type_affordance_mechanics_policy:
  rule: >-
    迅捷 is an example of a type-affordance mechanic, not a universal battle
    resource. Do not make it a mandatory checklist item unless the source,
    selected type, move text, or case context makes it relevant.
  required_behavior:
    - treat similar type-linked mechanics as a family
    - verify exact mechanic text from A/B materials before using it
    - do not overgeneralize one type's mechanic to all matchups
```

Pre-final self-check:

- Did the output mention Pokemon, EV, effort values, items, tera, or unrelated
  game systems?
- Did it make a fixed ability look selectable?
- Did it invent a species, move, skill effect, stat, or matchup fact?
- Did it treat expert opinion as current meta truth?
- Did it use cultivation/leveling/resource-farming language outside the current
  product scope?
- Did it overuse `迅捷` as if it were a global mechanic?

If yes, fix the output before finalizing.

## 3. Input Requirements

Required:

- `source_path`: path to one transcript or cleaned source.
- `source_group_id`: stable id derived from source directory/name.
- `source_kind`: one of `expert_video_transcript`,
  `expert_video_cleaned_note`, `unreviewed_community_transcript`, or
  `reviewed_community_note`.

Preferred:

- cleaned markdown source with line numbers recoverable;
- original raw transcript path;
- source title/date/version context;
- existing name-resolution notes.

If the input is raw transcript:

- do light cleanup only for readability;
- preserve original wording and line/spans;
- do not destructively edit source files.

## 4. Output Directory

Use this layout:

```text
artifacts/p10h_expert_demo_extraction/{source_group_id}/
  source_manifest.yaml
  candidate_cases.yaml
  name_resolution_notes.yaml
  a_layer_validation_tasks.yaml
  case_comparison_report.yaml
  pm_review_packet.md
  extraction_summary.md
```

Do not write to `data/expert_demonstrations/gold_cases.yaml` during extraction.
Gold promotion is a separate PM review step.
Do not auto-ingest any case, even if the extraction looks clean.

## 5. Case Taxonomy

Each candidate case must have exactly one primary family and exactly one case
type. Additional meaning belongs in retrieval tags.

### Primary Families

| Family | Meaning |
|---|---|
| `construction_decision` | Pre-battle team, set, slot, coverage, or replacement decision |
| `in_battle_decision` | In-match decision under opponent/team/turn information |
| `review_decision` | Post-hoc analysis of an actual or hypothetical mistake |
| `meta_context` | Environment/threat context; usually support material, not runtime case mainline |

### Case Types

| Family | Case Type | Solves |
|---|---|---|
| `construction_decision` | `core_archetype` | How 2-3 core pieces form a loop |
| `construction_decision` | `species_set` | How one species should be configured in context |
| `construction_decision` | `slot_role_plan` | Lead/pivot/closer role plan before battle |
| `construction_decision` | `coverage_patch` | Attribute/mechanic/team-structure blind spot |
| `construction_decision` | `replacement_decision` | Which slot to replace and with what tradeoff |
| `in_battle_decision` | `lead_selection` | Lead choice after seeing opponent context |
| `in_battle_decision` | `switch_pivot` | Whether to switch/pivot and into what |
| `in_battle_decision` | `move_choice` | Which move/action to choose now |
| `in_battle_decision` | `resource_timing` | When to spend/hold energy, marks, timing, or key effects |
| `in_battle_decision` | `endgame_plan` | How to convert a late-game route |
| `in_battle_decision` | `opponent_intent_read` | What opponent behavior implies |
| `review_decision` | `mistake_localization` | Where the loss/bad line happened |
| `review_decision` | `alternative_line` | What line should have been taken instead |
| `meta_context` | `meta_trend` | What is common or rising in the environment |
| `meta_context` | `threat_profile` | What a common threat does and why it matters |

Cross-cutting tags:

- archetype tags: `poison_team`, `wingking_balance`, `starfall`, etc.
- tactical action tags: `pivot`, `pressure`, `sacrifice_branch`,
  `killline_conversion`, `stall_break`, etc.
- resource/mechanic tags: `energy`, `mark_count`, `status_stack`,
  `type_affordance`, etc.
- risk/boundary tags: `prediction_dependent`, `set_dependent`,
  `a_layer_unverified`, `source_conflict`, etc.

Retrieval granularity policy:

- Fine case types are for extraction precision and PM review.
- Runtime retrieval should not over-filter by fine case type while the pool is
  only 30-50 cases.
- Retrieval should first use coarse family, canonical entities, matchup tags,
  tactical action tags, resource/risk tags, and then lexical similarity.
- A case involving lead selection, pivot, and move choice may carry one primary
  case type plus multiple retrieval tags for the other decisions.

Tag quality policy:

- Tags are not decorative metadata. At probe scale, retrieval quality depends
  more on tag consistency than on the lexical scorer.
- Use the same tag for the same concept across sources. Do not create synonyms
  such as `poison_core`, `poison_team`, and `poison_archetype` unless a
  vocabulary file defines the relationship.
- Prefer stable coarse tags over clever one-off tags.
- Every candidate should include enough tags for an obvious future user query
  to retrieve it: at minimum coarse family, canonical species when known,
  matchup/archetype when relevant, tactical action, and risk/resource tags when
  relevant.
- If a useful tag is uncertain, record it in `tag_quality_notes` instead of
  silently omitting it.

## 6. Judgement Moment Criteria

A segment can become a candidate case only if it has:

- a concrete situation or question;
- an expert judgement, operation, recommendation, or exclusion;
- at least one stated or recoverable evidence point;
- a conclusion, recommended line, or rejected line;
- source span;
- future retrieval value.

Reject segments that are only:

- greeting, filler, streamer narration, or jokes;
- pure species introduction without judgement;
- a tier-list statement without context;
- ASR-corrupted beyond recovery;
- generic “this is strong” claims without why;
- exact fact claims that cannot be checked and do not contain judgement.

One transcript may produce many cases. Do not merge unrelated judgement moments
into one case just because they come from the same video.

## 7. Extraction Procedure

Use a three-pass workflow:

1. Scan: identify all judgement moments without writing final cases.
2. Extract: convert each selected moment into structured candidate data.
3. Format and validate: apply schema, A-layer checks, comparison, PM packet, and
   eval summary.

This prevents the executing Agent from anchoring too early on the first obvious
case and missing later segments.

### Pass 0: Build Source Manifest

Create `source_manifest.yaml`:

```yaml
source_group_id: wingking_poison_0429
source_path: wiki/cache/...
source_kind: expert_video_transcript
title: null
date_or_patch_context: null
input_quality:
  transcript_quality: unknown
  asr_risk: medium
  judgement_density: unknown
related_existing_artifacts:
  - artifacts/p10h_name_resolution_cleanup/
```

### Pass 1: Full-Source Scan

Read the full source once. Segment by:

- construction explanation;
- species/set explanation;
- opponent/team preview;
- lead choice;
- turn or branch decision;
- resource or killline decision;
- mistake/review section;
- meta context.

Record candidate spans before writing cases.

Create a scan list before extraction:

```yaml
scan_candidates:
  - candidate_id: scan_001
    source_span: lines 36-43
    primary_family_guess: in_battle_decision
    case_type_guess: switch_pivot
    one_line_summary: source switches 水母 after poison stacking
    why_this_is_judgement: expert chooses one branch and rejects/risks another
    extraction_priority: high
```

For each possible moment, include:

- short title;
- source span;
- primary family;
- case type;
- why this is a judgement moment;
- whether it is likely worth PM review.

### Pass 2: Per-Case Extraction

For each accepted candidate moment, fill:

```yaml
case_id: dc_{source_group_id}_{short_slug}
source_group_id: string
source_path: string
source_span: string
source_kind: expert_video_transcript
review_status: draft
demonstration_status: candidate
confidence: low_confidence
eval_split: train_or_holdout_recommendation
primary_family: construction_decision
case_type: species_set
task_types:
  - species_role
situation_summary: string
user_question_equivalent: string_or_null
observed_evidence:
  - evidence_type: source_stated | source_implied | agent_inferred_from_source | a_layer_fact
    text: source-faithful evidence point
    source_span: string_or_null
expert_reasoning_summary:
  - step_type: source_stated | source_implied | agent_inferred_from_source
    text: concise source-faithful judgement rationale
    source_span: string
expert_conclusion: string
caveats:
  - boundary or uncertainty
negative_or_failure_branches:
  - branch: string
    why_it_fails_or_downgrades: string
canonical_entities:
  species:
    - raw_name: string
      canonical_candidate: string_or_null
      species_id: string_or_null
      resolution_status: exact | alias | likely_alias | unresolved
  moves:
    - raw_name: string
      canonical_candidate: string_or_null
      move_id: string_or_null
      resolution_status: exact | alias | likely_alias | unresolved
name_resolution_notes:
  - string
retrieval_tags:
  archetypes: []
  matchup_tags: []
  tactical_actions: []
  resource_or_mechanic: []
  risk_or_boundary: []
  canonical_species: []
  canonical_moves: []
tag_quality_notes:
  - string
answer_shape:
  product_facing_summary: string_or_null
fidelity_review_prompt: >-
  Did this extraction faithfully preserve the expert's judgement in the
  cited source span?
```

Evidence trace rules:

- `source_stated`: the source explicitly says it.
- `source_implied`: the source strongly implies it through adjacent statements.
- `agent_inferred_from_source`: the Agent filled a small missing bridge from
  source context. This must cite the source span and remain reviewable.
- `a_layer_fact`: verified through Battle Dex.

Do not use long verbatim excerpts. Keep direct source quotes short and rely on
source spans for review.

### Pass 3A: A-Layer Fact Grounding

Prefer project repository accessors when available, especially
`advisor/battle_dex.py`. Direct SQLite lookup is acceptable for extraction
artifacts when faster or when no accessor covers the query.

Use A-layer data to verify:

- species/form identity;
- move existence;
- fixed ability;
- selected move access where available;
- type/stat facts if referenced.

Use exact matches first. Use fuzzy/alias only as notes. Do not silently promote
alias guesses to canonical truth.

If unresolved:

- keep `resolution_status: unresolved`;
- add a task to `a_layer_validation_tasks.yaml`;
- block gold promotion for that entity.

### Pass 3B: Name Resolution Notes

Create `name_resolution_notes.yaml` with:

```yaml
source_group_id: string
notes:
  - raw_name: 水母
    canonical_candidate: 琉璃水母
    status: likely_alias
    evidence:
      - Battle Dex has water/poison 琉璃水母
      - source mentions poison pressure and 泡沫幻影
    affected_case_ids:
      - dc_...
    gold_blocker: false
  - raw_name: unknown_ASR
    canonical_candidate: null
    status: unresolved
    evidence: []
    affected_case_ids:
      - dc_...
    gold_blocker: true
```

Reference existing overlays in `artifacts/p10h_name_resolution_cleanup/` when
applicable.

Name-resolution escalation:

- First try exact A-layer lookup.
- Then generate fuzzy/alias candidates from known overlays, local source
  aliases, string similarity, and adjacent context.
- Then use contextual disambiguation: role, mentioned moves, archetype,
  attribute/type profile, and neighboring species.
- Do not auto-promote fuzzy/contextual guesses to canonical truth.
- If more than 20% of candidate cases are blocked by unresolved canonical names,
  stop gold-prep work for this source and produce a dedicated source-local
  alias table.
- If a source has more than 5 recurring unresolved ASR names, escalate before
  PM fidelity review.

### Pass 3C: Compare With Existing Cases

If a gold/candidate case pool is available, create
`case_comparison_report.yaml`.

Compare by:

- same canonical species plus same case type;
- same matchup/archetype tags;
- same source group;
- same conclusion;
- opposite conclusion under similar context.

Output shape:

```yaml
source_group_id: string
comparisons:
  - case_id: dc_...
    status: new | duplicate_candidate | conflict_candidate | complement_candidate | not_checked
    matched_case_ids:
      - dc_existing_...
    rationale: string
    action_recommendation: recommend_promote | escalate | reject | keep_candidate
```

Important:

- `recommend_promote` is not auto-ingest.
- Any conflict should be preserved as a conflict, not force-merged into one
  consensus.
- If no prior case pool exists, write `status: not_checked` and explain why.

### Pass 3D: PM Review Packet

Create `pm_review_packet.md` for a human reviewer.

For each case include:

- case id and title;
- source span;
- original excerpt, shortened but source-faithful;
- extracted situation;
- extracted expert reasoning summary;
- extracted conclusion;
- caveats/failure branches;
- unresolved names or facts;
- review question:
  `这段提取是否忠实反映了原视频/转写稿的判断？`
- review options:
  `accept`, `revise`, `reject_distorted_source`, `needs_source_recheck`,
  `reject_low_signal`.

Do not ask PM to decide whether the expert is universally correct unless the PM
chooses to comment on it.

### Pass 3E: Extraction Summary

Create `extraction_summary.md`:

- source path;
- number of candidate moments found;
- number of candidate cases emitted;
- type distribution;
- key unresolved names;
- A-layer validation blockers;
- duplicate/conflict/complement comparison counts;
- recommended PM review priority;
- rejected/ignored sections and why.

## 8. Evaluation

### Extraction Eval

Score the extraction against:

| Dimension | Pass Condition |
|---|---|
| Coverage | Major judgement moments are not missed |
| Granularity | Separate decisions are not merged into one vague case |
| Fidelity | Summary preserves source intent without adding tactics |
| Grounding | Species/move/ability facts are checked or marked unresolved |
| Domain Safety | No Pokemon/generic RPG contamination |
| Boundary | Expert opinion is not written as version truth |
| Usefulness | Case can answer a plausible future user query |
| Comparison | New/duplicate/conflict/complement status is recorded when possible |

Promotion quality priority:

1. `source_fidelity`: preserves what the expert meant.
2. `factual_grounding`: A-layer facts pass or unresolved blockers are explicit.
3. `reasoning_completeness`: contains a reusable judgement chain, not only a
   conclusion.
4. `transferability`: maps to plausible future user questions.
5. `boundary_quality`: preserves caveats, failure branches, and uncertainty.

Important:

- Reasoning completeness is the main ranking signal only after source fidelity
  and factual grounding pass.
- A complete but invented chain must be rejected.
- A faithful but shallow segment can remain a candidate or review note, but
  should not be promoted as a gold demonstration unless it still teaches a
  useful judgement pattern.

D-layer scale targets:

| Stage | PM-reviewed gold cases | Use |
|---|---:|---|
| Probe | 8-12 | Test extraction, retrieval, and answer-shape impact |
| MVP | 15-25 | Cover major reasoning patterns for dogfood usage |
| V1 usable | 30-50 | Support repeated real use across high-frequency questions |
| Continuous | 50+ | Add patch/meta/species coverage without mechanical expansion |

Do not force equal coverage across all subtypes. Prefer reasoning-pattern
coverage.

### Runtime Eval Later

Do not run runtime eval during this extraction task unless explicitly requested.

Future runtime eval should test:

- whether retrieval recalls the right cases;
- whether injected cases improve tactical usefulness;
- whether A-layer facts remain authoritative;
- whether answers avoid overgeneralizing one expert source;
- whether user-facing output hides internal source bookkeeping.

After the case pool reaches 8-12 PM-reviewed probe gold cases, start:

- first retrieval smoke test:
  - PM writes 5 user-like questions with clear expected matching cases;
  - tag filtering plus BM25/simple lexical scoring must retrieve the expected
    case in top-3 for at least 4 of 5 questions;
  - failures must be triaged as tag vocabulary, canonical entity, query wording,
    case quality, or scoring defects;
  - embeddings or algorithm swaps are not allowed as the first fix while tag
    defects remain plausible;
- then run broader retrieval smoke tests for obvious source-matched questions;
- blind comparison on 3-5 user-like prompts with and without retrieved cases;
- qualitative check: does the answer imitate expert judgement structure, or
  merely become longer?

After the case pool reaches at least 20 PM-reviewed gold cases, add:

- drift check for recurring contamination patterns, especially Pokemon/generic
  RPG imports;
- subtype coverage review for high-frequency user questions.

## 9. Completion Criteria

The task is complete only when:

- `source_manifest.yaml` exists;
- `candidate_cases.yaml` exists and is parseable YAML;
- every candidate case has source span;
- every candidate case has primary family and case type;
- every candidate case contains an expert judgement, not just notes;
- every inferred reasoning bridge is marked as `agent_inferred_from_source` and
  cites a source span;
- `name_resolution_notes.yaml` exists;
- `a_layer_validation_tasks.yaml` exists, even if empty;
- `case_comparison_report.yaml` exists, even if all entries are `not_checked`;
- `pm_review_packet.md` is directly reviewable;
- `extraction_summary.md` reports counts, type distribution, and blockers;
- no runtime code or gold pool was modified.

## 10. Failure Conditions

Stop and report blocked if:

- the transcript cannot be read;
- source spans cannot be preserved;
- ASR corruption prevents faithful extraction;
- the source contains no judgement moments;
- A-layer database is unavailable and the source depends heavily on exact
  species/move facts;
- the task requires deciding tactical truth instead of source fidelity.

## 11. Final Response Format For Executing Agent

Use this final format:

```text
Status: COMPLETE | BLOCKED

Source: {source_group_id}

Artifacts:
- artifacts/p10h_expert_demo_extraction/{source_group_id}/source_manifest.yaml
- artifacts/p10h_expert_demo_extraction/{source_group_id}/candidate_cases.yaml
- artifacts/p10h_expert_demo_extraction/{source_group_id}/name_resolution_notes.yaml
- artifacts/p10h_expert_demo_extraction/{source_group_id}/a_layer_validation_tasks.yaml
- artifacts/p10h_expert_demo_extraction/{source_group_id}/case_comparison_report.yaml
- artifacts/p10h_expert_demo_extraction/{source_group_id}/pm_review_packet.md
- artifacts/p10h_expert_demo_extraction/{source_group_id}/extraction_summary.md

Summary:
- candidate_cases: N
- type_distribution: ...
- unresolved_names: ...
- gold_blockers: ...
- comparison: new=N duplicate=N conflict=N complement=N not_checked=N

Validation:
- YAML parse: pass/fail
- A-layer lookup: pass/partial/blocked

No runtime changes made.
No gold-case auto-ingest performed.
```
