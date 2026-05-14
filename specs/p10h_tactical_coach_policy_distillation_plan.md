# P10h Expert Demonstration Casebank Plan

## Status

Draft v2 route pivot. This replaces the previous heuristic-first Coach Policy
distillation route.

Runtime remains unchanged until PM acceptance, D-layer schema acceptance, and
blind eval acceptance.

## Trigger

P10/P7 real Agent chat can call live LLM providers, consume A-layer Battle Dex
facts, and consume P8 structured team context. What is still missing is not more
persona wording or a larger hand-written tactical rulebook. The missing layer is
a reliable way for the Agent to imitate high-quality battle judgement.

The previous P10h route treated cases and B-layer docs as inputs to distill
candidate heuristics and compiled Coach Policy slices. That route is now
downgraded because:

- tactical advice quality is hard to optimize with small automatic evals;
- hand-written or LLM-distilled rules become brittle as meta changes;
- high-level heuristics lose the texture of expert judgement;
- PM can reliably fidelity-review extracted expert demonstrations even when PM
  should not be the final tactical authority.

## New Core Thesis

P10h should build a D-layer Expert Demonstration Casebank.

The main runtime asset should be reviewed examples of expert judgement, not a
large tactical ruleset. The Agent should receive:

1. A-layer facts for correctness;
2. B-layer mechanics/materials for domain grounding;
3. D-layer retrieved expert demonstrations for judgement imitation;
4. C-layer policy for safety, provenance, uncertainty, and answer boundaries;
5. persona layer for expression only.

## Layer Model

| Layer | Name | Content | Runtime Responsibility |
|---|---|---|---|
| A | Battle Dex Structured Facts | Species, moves, fixed ability, stats, team slots | Hard factual grounding |
| B | Battle Wiki / Knowledge Materials | Mechanics docs, terminology, cleaned source notes, community materials | Background knowledge and source material |
| C | Governance & Runtime Policy | Trust tiers, prompt boundaries, routing, privacy, uncertainty policy | Rules for how A/B/D may be used |
| D | Expert Demonstration Case Memory | High-player judgement cases with fidelity review | Few-shot / RAG judgement imitation |
| Persona | Expression Layer | `you_know_who` and other persona artifacts | Voice, not tactical truth |

## Relationship To Existing Work

Keep:

- `specs/p10h_casebank_seed_schema.yaml` as the base container, extended for
  expert demonstrations;
- `specs/p10h_expert_demo_extraction_manual.md` as the execution manual for
  turning one transcript/cleaned source into candidate D-layer cases and PM
  review packets;
- full-spectrum extraction outputs as a candidate pool;
- name-resolution cleanup as a required promotion gate;
- `candidate_heuristics.yaml` as tags, summaries, and audit material.

Demote:

- `candidate_heuristic` artifacts from runtime tactical rules to internal
  retrieval labels and review notes;
- `compiled_policy_slice` from a default runtime target to a possible future
  thin protocol artifact only.

Reject for P10h:

- building a comprehensive rulebook;
- optimizing prompts with DSPy-style automatic metric loops before a large eval
  set exists;
- injecting unreviewed transcript text directly into runtime;
- treating any single community video as meta truth.

Identifier convention:

- D-layer Expert Demonstration case ids use the `dc_` prefix.
- Older `tc_` ids belong to pre-pivot tactical-case drafts and should not be
  used for new D-layer gold demonstrations.

## D-Layer Artifact Family

Canonical storage target:

```text
data/expert_demonstrations/
  candidates/
  gold/
  index/
  review/
  rejected/
```

Extraction tasks may write draft artifacts under `artifacts/`, but runtime
retrieval must only read compiled files under `data/expert_demonstrations/`
after PM acceptance.

### 1. Expert Demonstration Gold Case

Purpose:

- preserve a concrete expert judgement moment;
- let the runtime model imitate how the expert weighed evidence;
- keep source fidelity review separate from tactical truth claims.

Required shape:

```yaml
case_id: dc_poison_vs_starfall_water_jellyfish_branch_001
source_refs:
  - path_or_url: wiki/cache/...
    source_kind: expert_video_transcript
    source_span: timestamp_or_line_range
expert_context:
  expert_label: community_high_rank_player_or_unknown
  patch_or_version_context: 2026-04
review:
  status: pm_fidelity_reviewed
  reviewed_by: PM
  reviewed_at: 2026-05-01
  fidelity_question: Did the extraction preserve what the expert meant?
task_types:
  - matchup_response
  - team_structure
situation:
  user_question_equivalent: 毒队遇到星陨怎么处理？
  friendly_context: partial_or_full_team
  opponent_context: known_or_inferred_core
observed_evidence:
  a_layer_facts:
    - species_identity
    - selected_moves_if_known
  source_evidence:
    - expert says lead X because...
    - expert warns Y branch fails when...
expert_reasoning_summary:
  - short source-faithful reasoning step
  - no hidden chain-of-thought request
expert_conclusion:
  recommendation: ...
  confidence: provisional
  caveats:
    - depends_on_move_set
    - depends_on_mark_count
negative_examples:
  - mistake: ...
    why_bad: ...
retrieval_tags:
  archetypes:
    - poison_team
    - starfall
  tactical_actions:
    - pivot
    - pressure
    - sacrifice_branch
answer_shape:
  product_facing_summary: ...
```

### 2. Candidate Demonstration Pool

Purpose:

- hold draft extractions from transcripts;
- allow low-confidence broad extraction without contaminating runtime.

Rules:

- all broad extraction starts as `draft / low_confidence`;
- ASR names must go through name-resolution overlay before promotion;
- candidate cases may cite raw transcript spans;
- candidate cases cannot enter runtime retrieval.

### 3. Gold Case Index

Purpose:

- support retrieval of 2-3 similar cases by task type, species, moves, team
  archetype, matchup, and tactical action.

Index fields:

- task types;
- canonical species IDs and aliases;
- selected moves and move roles;
- archetype tags;
- tactical action tags;
- bottleneck tags;
- source patch/date;
- confidence and review status;
- counterexample links.

Tag quality is a first-class retrieval dependency. With a 30-50 case pool, the
main failure mode is not the retrieval algorithm; it is sparse, inconsistent, or
overly clever tags. The probe stage must verify tags before comparing algorithms.

Tag discipline:

- use canonical entity tags from A-layer where possible;
- keep coarse family tags stable across sources;
- normalize archetype, matchup, tactical action, `resource_or_mechanic`, and
  `risk_or_boundary` tags;
- prefer a small controlled tag vocabulary plus aliases over one-off synonyms;
- record missing or uncertain tags as review defects, not harmless metadata.

### 4. Thin Coach Protocol

Purpose:

- define how the Agent uses cases;
- not encode tactical knowledge as a large rulebook.

Protocol requirements:

- A-layer facts override D-layer examples;
- D-layer examples are analogies, not deterministic facts;
- if retrieved cases conflict, mention that the source cases imply different
  branches instead of forcing fake consensus;
- do not expose internal labels or source bookkeeping to the user;
- do not reveal hidden chain-of-thought;
- answer with concise analysis process and result.

## New Workflow

### Stage 0: Route Pivot Contract

Task:

- accept Expert Demonstration Casebank as P10h mainline;
- mark heuristic-first distillation as superseded for runtime;
- keep existing extraction artifacts as migration inputs.

Outputs:

- updated P10h plan;
- updated casebank schema;
- updated heuristic schema status;
- log entry.

Gate:

- PM accepts D-layer as a separate layer from B and C.

### Stage 1: Source Quality Triage

Task:

- score video transcript/source groups by judgement density, source clarity,
  ASR cleanliness, and current-meta usefulness;
- pick the first 5-8 high-density sources instead of blindly processing all
  sources equally.

Inputs:

- `wiki/cache/`;
- `artifacts/p10h_cache_inventory/`;
- `artifacts/p10h_full_spectrum_extraction_merged_v2/`;
- `artifacts/p10h_name_resolution_cleanup/`.

Outputs:

- `artifacts/p10h_expert_demo/source_quality_ranking.yaml`;
- `artifacts/p10h_expert_demo/first_wave_source_plan.md`.

Gate:

- each first-wave source has enough judgement moments, not only team lists.

### Stage 2: Expert Demonstration Extraction

Task:

- extract judgement moments, not general rules;
- each case must preserve situation, evidence, expert reasoning summary,
  conclusion, caveats, and failure branches.

Scale target:

| Stage | Gold cases | Purpose |
|---|---:|---|
| Probe | 8-12 | Verify extraction fidelity, retrieval recall, and answer-shape improvement |
| MVP | 15-25 | Cover major reasoning patterns for realistic dogfood usage |
| V1 usable | 30-50 | Support repeated real usage across high-frequency construction and in-battle questions |
| Continuous | 50+ | Add new patch/meta/species coverage; do not expand mechanically |

First-wave extraction should target 15-20 candidate demonstrations and promote
8-12 probe gold cases after PM fidelity review.

Coverage target:

- prioritize reasoning-pattern breadth over equal subtype coverage;
- do not require every case subtype to have the same number of cases;
- high-value patterns include core loop construction, set tradeoff, replacement
  cost, lead selection, pivot/sacrifice branch, resource/mark timing, failure
  branch, and mistake localization.

Outputs:

- `data/expert_demonstrations/candidates/*.yaml`;
- `data/expert_demonstrations/source_notes/*.md`.

Gate:

- no case is gold without source span and fidelity review fields.
- gold selection optimizes for source fidelity, reasoning completeness,
  transferability, A-layer grounding, and boundary quality.
- reasoning completeness is the main ranking signal only after fidelity and
  factual grounding pass.

### Stage 3: Name And Fact Grounding

Task:

- resolve ASR/community names to A-layer canonical species/moves;
- attach A-layer IDs where available;
- leave unresolved names as blockers, not silent assumptions.

Name resolution strategy:

1. Exact A-layer lookup:
   - species/form, move, fixed ability, and selected move access;
   - use `advisor/battle_dex.py` or direct SQLite as appropriate.
2. Fuzzy and alias candidate generation:
   - use string similarity, known ASR overlays, source-local aliases, and
     community shorthand notes;
   - never auto-promote fuzzy matches to canonical facts.
3. Contextual disambiguation:
   - use source role, move mentions, archetype tags, type profile, and adjacent
     species to rank candidates;
   - record evidence, not just the guessed name.
4. Human/PM adjudication:
   - unresolved or medium-confidence names become review items;
   - PM can confirm mapping as source-fidelity editor when context is enough.

Escalation threshold:

- If more than 20% of candidate cases in a first-wave source are blocked by
  unresolved canonical names, create a dedicated name-resolution pass before PM
  review.
- If one high-value source has more than 5 unresolved recurring ASR names,
  pause gold promotion for that source and build a source-local alias table.

Outputs:

- `data/expert_demonstrations/name_resolution_overlay.yaml`;
- `data/expert_demonstrations/fact_grounding_report.md`.

Gate:

- gold cases cannot contain `_ASR` canonical names.

### Stage 4: PM Fidelity Review

Task:

- PM reviews whether extraction faithfully reflects expert source intent;
- PM does not need to decide whether the expert is universally correct.

Review statuses:

- `pm_fidelity_reviewed`;
- `needs_source_recheck`;
- `rejected_distorted_source`;
- `rejected_low_signal`;

Outputs:

- `data/expert_demonstrations/gold_cases.yaml`;
- `data/expert_demonstrations/rejected_cases.yaml`;
- `data/expert_demonstrations/review_notes.md`.

Gate:

- runtime retrieval may only consume `pm_fidelity_reviewed` or stronger cases.

Gold quality priority:

1. `source_fidelity`: the extraction preserves what the expert meant.
2. `factual_grounding`: A-layer facts are verified or unresolved blockers are
   explicit.
3. `reasoning_completeness`: the case exposes a reusable judgement chain.
4. `transferability`: the judgement pattern can help similar future questions.
5. `boundary_quality`: caveats, failure branches, and uncertainty are preserved.

Do not promote a case with high reasoning completeness if source fidelity or
A-layer factual grounding is broken. Good-looking invented reasoning is worse
than a shallow but faithful rejected candidate.

### Stage 5: D-Layer Retrieval Index

Task:

- build a small local retrieval index over gold cases;
- use tag filtering plus lightweight lexical scoring for the 30-50 case stage;
- defer embedding retrieval until case volume or recall failures justify it.
- treat tag consistency as the primary quality gate for probe retrieval.

Outputs:

- `data/expert_demonstrations/index.json`;
- `data/expert_demonstrations/index_manifest.yaml`;
- `data/expert_demonstrations/tag_vocabulary.yaml`;
- `artifacts/p10h_retrieval_probe/tag_quality_report.md`;
- `artifacts/p10h_retrieval_probe/recall_smoke_report.md`;

Contract:

- `specs/p10h_d_layer_retrieval_contract.yaml`

Retrieval priority:

1. coarse retrieval family: construction, in-battle, review, or meta;
2. exact task type when it helps, but do not over-filter by fine subtype;
3. canonical species/move overlap;
4. archetype/matchup overlap;
5. tactical action/resource/risk tag overlap;
6. BM25/simple lexical similarity over situation, conclusion, and answer shape;
7. optional semantic embedding only after the probe index shows lexical recall
   failures.

Fallback behavior:

- if no D-layer case passes threshold, skip D-layer and answer from A-layer
  facts plus B-layer mechanics and normal C-layer uncertainty policy;
- do not force a weak analogy into prompt context;
- if only low-similarity cases exist, they may be used for internal routing
  diagnostics but not injected as demonstrations.

Conflict behavior:

- if two retrieved gold cases conflict under similar context, include both as
  separate analogies and instruct the model to preserve branch conditions;
- do not ask the model to invent consensus;
- user-facing output may say that similar expert cases point to different
  branches depending on concrete conditions, but must not expose internal case
  ids.

Gate:

- tag quality probe passes before algorithm comparison:
  - PM defines 5 user-like questions that have clear expected matching cases;
  - BM25/simple lexical plus tags must retrieve the expected case in top-3 for
    at least 4 of 5 questions;
  - each failure is triaged first as tag vocabulary, canonical entity, query
    wording, or source-case quality defect;
  - do not switch to embeddings until tag defects have been fixed or ruled out;
- broader probe recall smoke passes:
  - create at least one query per probe gold case from its
    `user_question_equivalent`;
  - top-3 retrieval must recover the source case for at least 80% of probe
    queries after the 5-question smoke passes;
  - every high-priority construction/in-battle reasoning pattern must have at
    least one obvious query that retrieves a relevant case;
  - failed recalls are triaged as tagging, name-resolution, or scoring defects.

### Stage 6: Blind Eval

Task:

- compare baseline vs baseline + D-layer retrieved cases;
- evaluate tactical usefulness, grounding, and answer quality.

Scenario classes:

- species role query;
- partial team analysis;
- full team analysis;
- matchup/counterplay;
- move selection;
- replacement question;
- speed/control question.

Acceptance:

- D-layer improves tactical usefulness;
- no increase in unsupported facts;
- model does not overclaim examples as universal truth;
- model output does not leak source bookkeeping.

### Stage 7: Runtime Integration

Task:

- route user query;
- query A-layer facts;
- retrieve 0-3 D-layer gold cases;
- optionally retrieve B-layer mechanics docs;
- apply C-layer thin protocol;
- generate final answer through persona expression.

Prompt structure:

1. global safety/scope boundary;
2. route task;
3. A-layer facts/tool outputs;
4. B-layer mechanics snippets if needed;
5. D-layer retrieved gold cases as analogies;
6. thin Coach Protocol;
7. persona expression constraints;
8. final answer requirements.

The model must not receive:

- raw unreviewed transcript dumps;
- low-confidence candidate cases;
- provider secrets;
- official-IP-sensitive persona source markers;
- internal review labels in user-visible answer.

D-layer prompt block shape:

```text
Relevant expert demonstrations (analogies, not facts):

Case 1:
- Task family: in_battle_decision
- Situation: ...
- Source-grounded evidence: ...
- Expert reasoning summary: ...
- Expert conclusion: ...
- Caveats / failure branches: ...
- Use boundary: Treat this as an analogy. A-layer facts above override it.
```

Prompt rules:

- Do include compact source-fidelity and factual-grounding status in the hidden
  prompt block when useful for weighting.
- Do not include raw transcript excerpts unless explicitly approved; prefer
  reviewed summaries and source spans.
- Do not expose case ids, review status, quality scores, or source bookkeeping
  in the user-facing answer.
- Keep A-layer facts and D-layer demonstrations in separate prompt sections.
- If no D-layer case is injected, the model should not mention that absence.

## Migration From Existing P10h Outputs

Existing broad extraction is still useful, but its job changes.

| Existing output | New role |
|---|---|
| `cleaned_source_index.yaml` | source manifest |
| `draft_case_pool.yaml` | candidate demonstration source |
| `draft_species_set_pool.yaml` | species-role candidate source |
| `candidate_heuristics.yaml` | retrieval tags / audit summaries only |
| `promotion_candidates.yaml` | first-wave source/case prioritization input |
| `a_layer_validation_tasks.yaml` | fact-grounding checklist |
| `name_resolution_cleanup/` | required pre-gold promotion gate |

## Open Decisions

1. Which 5-8 sources become first-wave expert demonstration sources?
2. What is the minimum source-span format for current transcript files:
   line range, paragraph ID, timestamp, or both?
3. What unresolved-name rate is acceptable after the first dedicated
   name-resolution pass, and which names need PM-maintained alias entries?
4. What is the first runtime target: matchup response only, or matchup plus
   team analysis?
5. What initial controlled tag vocabulary is accepted for probe cases?

Resolved decisions:

- Initial D-layer retrieval should use tag filtering plus BM25/simple lexical
  scoring. Embedding retrieval is deferred until recall smoke shows a need.
- Fine-grained case type remains useful for labeling, but retrieval should first
  use coarse family and tags to avoid over-filtering a small 30-50 case pool.
- Gold D-layer cases live under `data/expert_demonstrations/`.
- The first retrieval test is a PM-authored 5-question obvious-match recall
  smoke, because tag quality is more important than algorithm selection at
  probe scale.

## Recommended Next Dispatch

P10h-C should not distill heuristics. It should:

1. use `specs/p10h_expert_demo_extraction_manual.md` as the execution protocol;
2. rank sources by judgement density and ASR/name-resolution risk;
3. choose the first 3-5 sources, not all sources;
4. extract 15-20 candidate demonstrations from those sources;
5. produce PM review packets and recommend 8-12 probe gold candidates;
6. draft an initial controlled tag vocabulary from the extracted cases;
7. define 5 obvious-match retrieval questions for the probe set;
8. produce a no-runtime-change acceptance gate.

P10h-D should begin only after PM fidelity review promotes 8-12 probe gold
cases. It should build the first `data/expert_demonstrations/` index and run the
5-question tag/BM25 recall smoke before any runtime integration.

## Acceptance Checklist

- P10h plan names D-layer Expert Demonstration Casebank as mainline.
- Case schema supports source-faithful expert judgement moments.
- Extraction manual exists and includes domain-bias guard, case taxonomy,
  A-layer grounding, PM review, and eval.
- D-layer retrieval contract exists and treats tag quality as the first probe
  gate.
- Heuristic schema is demoted from runtime target to tags/audit material.
- Existing P10h artifacts have migration roles.
- Runtime remains unchanged.
- Next dispatch can produce PM-reviewable gold-case candidates.
