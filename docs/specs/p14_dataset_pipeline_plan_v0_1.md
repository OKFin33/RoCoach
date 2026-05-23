# Roco Dataset Pipeline Plan v0.1

Status: red-team revised plan
Date: 2026-05-22
Owner: PM direction + Agent execution
Scope: dataset construction pipeline contract
Runtime effect: none

This plan replaces the first skeleton draft. It is not a cosmetic patch. The
red-team finding was correct: a list of planning tasks is not yet a trustworthy
data-pipeline contract.

This document still does not authorize dataset production, batch ingest,
runtime promotion, graph materialization, automatic Gold Set acceptance, or
mutation of reviewed data.

## 0. PM Summary

A useful Roco dataset is not "a lot of Roco data". It is a governed data
product for a specific task:

```text
support PvP advisor answers about set, mechanism, teammate, counterplay,
configuration intent, and evidence-backed uncertainty.
```

The Roco dataset system has four connected products:

1. **Evidence KB**: preserves source-grounded video/text evidence and processing
   lineage.
2. **Meta Graph / KG**: stores structured set families, alter variants,
   mechanisms, relation claims, and review state.
3. **Gold/Eval Set**: calibrates extraction, canonicalization, merge/split,
   mechanism boundaries, negative cases, and review-surface quality.
4. **LLM Wiki / readable knowledge layer**: keeps human-readable explanations
   and synthesis separate from structured facts.

Upstream of these products, Roco also needs an **Acquisition Skill Layer**:
`social-media-reader` / Scribe-style tooling that can collect transcripts across
Bilibili, Douyin, Xiaohongshu, WeChat Channels, local video, and generic URLs.
That layer is input infrastructure only. It emits source bundles; it does not
create dataset entries.

Professional consequence: "more sources" is not success by itself. The pipeline
is only improving when it increases task usefulness, traceability,
measurability, or update safety.

## 1. Current Position

Roco already has a volume-capable P14 lane:

- source discovery and queue expansion;
- Bilibili ingest and subtitle/ASR fallback;
- AB-refined transcript and evidence foundation artifacts;
- Set Inventory L1a/L1b/L2/L3 schema;
- cross-source consolidation and split-blocker handling;
- family/reviewer/source-reliability/error ledgers;
- PM-readable autorun dashboards;
- Gold negative candidates and Gold Set v0 skeleton.

The current weakness is not collection. The weakness is governed dataset
readiness:

- cross-platform acquisition is not yet connected by a stable
  `source_transcript_bundle` contract;
- accepted Gold Set count is still zero;
- dataset card and versioned snapshot contract do not exist;
- provenance requirements are not yet field-level;
- quality metrics are not yet dashboarded;
- verifier / LLM-as-judge evaluation is not yet separated from data production;
- independent review / disagreement handling is not formalized;
- public/private distribution rules are not explicit;
- future data-production goals can still blur candidate data with reviewed or
  runtime data.

## 2. External Baseline Applied

This plan uses the following external practices as design pressure, not as a
foreign template to copy:

- **Datasheets for Datasets**: dataset consumers need motivation,
  composition, collection, processing, intended use, risks, and maintenance.
- **DataComp-LM**: data curation is an experimental variable; filtering,
  deduplication, and mixture choices must be measurable.
- **FineWeb**: curation choices such as filtering and deduplication should be
  documented and ablated, not treated as invisible cleanup.
- **RAG evaluation / Ragas**: retrieval quality, faithfulness, noise
  sensitivity, answer relevance, and continual update against drift matter.
- **DeepSeek-R1-style verifier lesson**: generated or model-produced material
  is useful only when a verifier/reward/rule/human loop filters it.

For Roco, this becomes:

```text
define task
-> preserve raw/evidence lineage
-> extract structured candidates
-> verify with A-layer/rules/model/human gates
-> calibrate with Gold/Eval
-> version snapshots
-> use errors and product evals to update the data recipe
```

## 3. Non-negotiable Principles

### 3.1 Task Usefulness

Every dataset component must say which PvP advisor task it improves:

- set existence and set-family identity;
- mechanism explanation and boundary;
- teammate/combo relation;
- counterplay / matchup claim;
- configuration intent;
- covered/uncovered answer behavior.

If a source or artifact cannot support any of those tasks, it can remain raw
research material but does not advance this dataset.

### 3.2 Traceability

Every promoted or Gold/Eval decision must be able to answer:

- source: where did it come from;
- time: when was it published / processed / reviewed;
- transform: which tools or repair passes changed it;
- reviewer: who or which role accepted/deferred/rejected it;
- confidence: why it is high/medium/low;
- evidence: which span supports it;
- lineage: which previous item it supersedes or depends on.

### 3.3 Measurability

Quality cannot mean "feels right". The pipeline must track:

- entity canonicalization accuracy;
- legal move assignment rate;
- unresolved ASR rate;
- required-field completeness;
- merge/split agreement against Gold Set;
- mechanism-boundary regression;
- review pass/defer/reject rates;
- RAG retrieval/faithfulness metrics;
- error taxonomy counts.

### 3.4 Continuous Update

Roco is a changing PvP domain. The dataset must handle:

- new sources and meta shifts;
- stale source detection;
- superseded set families;
- mechanism rule contradictions;
- drift in ASR/name normalization;
- regression after extractor or schema changes.

## 4. Dataset Products and Sample Units

### 4.1 Evidence KB

Sample unit: `evidence_segment`.

Minimum fields:

```yaml
segment_id: ""
source_id: ""
source_url: ""
published_at: ""
processed_at: ""
start_ms: 0
end_ms: 0
transcript_text: ""
repair_status: clean | repaired | partial | unresolved
asr_method: subtitle | bailian_asr | other
ab_refinement_version: ""
source_quality: good | usable | poor
runtime_allowed: false
```

Purpose:

- preserve source-grounded context;
- support retrieval and answer evidence;
- allow reprocessing when a term or mechanism is corrected.

### 4.2 Structured KG

Sample units:

- `claim_atom`
- `set_skeleton`
- `set_family`
- `alter_variant`
- `relation_claim`
- `mechanism_rule`
- `review_ledger_entry`

Required provenance for any KG candidate:

```yaml
kg_item_id: ""
kg_item_type: ""
source_ids: []
source_span_ids: []
claim_atom_ids: []
canonical_entities: []
a_layer_resolution:
  species: []
  moves: []
  abilities: []
transform_lineage:
  transcript_repair_ids: []
  extractor_version: ""
  normalization_version: ""
  consolidation_batch: ""
field_provenance:
  species: []
  moves: []
  nature: []
  iv: []
  bloodline: []
  role: []
  teammate_relations: []
  counter_relations: []
  mechanism_dependencies: []
review:
  status: candidate | agent_checked | review_packeted | pm_reviewed | runtime_promoted | deferred | rejected
  reviewer_role: ""
  extractor_agent_id: ""
  extractor_run_id: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
  review_packet: ""
quality:
  confidence: high | medium | low
  asr_risk: none | low | medium | high
  source_diversity: single_source | multi_source | independent_sources
runtime_allowed: false
```

Purpose:

- turn evidence into structured, queryable set/mechanism/relation data;
- keep candidates separate from reviewed/runtime data.

Legacy `species_set` cards are not automatically compliant with
`p14.kg_item.v0`. A reviewed card may stay in the current Set Graph card shape
only if it declares a KG projection boundary, records field-level provenance,
and follows `docs/specs/p14_species_set_kg_item_crosswalk_v0.md`.

### 4.3 Gold/Eval Set

Sample units:

- `gold_set_family`
- `gold_split_case`
- `gold_mechanism_boundary`
- `gold_stateful_form_boundary`
- `gold_negative_case`

Required fields:

```yaml
gold_id: ""
gold_type: ""
meta_snapshot: ""
decision:
  label: ""
  expected_behavior: ""
input_fixture_refs: []
expected_output:
  allowed: []
  forbidden: []
quality:
  confidence: high | medium | low
  reviewer_agreement: single_pm | double_reviewed | disputed | superseded
regression_tasks: []
runtime_allowed: false
```

Purpose:

- tell whether future extraction/recluster/canonicalization changes improve or
  regress the pipeline.

Gold candidate packets are only review inputs. They become accepted regression
items only through an explicit PM decision and
`docs/specs/p14_gold_candidate_to_item_mapping_v0.md`; candidate existence
must not change Gold manifest counts.

### 4.4 LLM Wiki

Sample unit: readable synthesis note.

Rule:

- readable notes may explain, summarize, and teach;
- they must not become primary structured facts without source span and
  structured KG extraction;
- if a wiki note contradicts KG/Gold evidence, the conflict is logged, not
  silently resolved.

## 5. Pipeline Contract

```text
Task definition
-> Acquisition skill layer
-> Source policy
-> Raw/evidence preservation
-> Cleaning / dedup / canonicalization
-> Extraction / annotation
-> Merge / split / recluster
-> Verifier layers
-> Human-in-the-loop review
-> Gold/Eval regression
-> Dataset snapshot / datasheet
-> Product/runtime promotion gate
-> Drift and update loop
```

### 5.0 Acquisition Skill Boundary

The acquisition layer may be improved independently from Roco dataset
production, but it must stop at a `source_transcript_bundle`.

Allowed acquisition outputs:

- source URL/platform metadata;
- transcript/subtitle/OCR artifacts;
- segment timestamps when available;
- acquisition method and tool version;
- rights/distribution state;
- quality notes and unresolved access/transcript issues.

Forbidden acquisition outputs:

- KG facts;
- Gold/Eval items;
- Set Graph cards;
- mechanism rules;
- D-layer cases;
- runtime data.

Roco import still requires:

```text
source_transcript_bundle
-> Roco source manifest
-> AB refinement
-> evidence spans
-> quality gate
-> candidate extraction
-> review / Gold / snapshot gates
```

Scribe or a strengthened `social-media-reader` can make source acquisition much
faster, especially for no-subtitle videos and non-Bilibili platforms. It cannot
replace provenance, A/B refinement, or review.

### 5.1 Source Policy

Source classes:

| Source type | Default use | Promotion weight |
|---|---|---|
| official / A-layer structured data | canonical entity and legality baseline | highest |
| mechanism tutorial | mechanism claims and contradictions | high, needs rule review |
| team explainer | set family, configuration, teammate relation | high if source spans clear |
| matchup/counterplay explainer | counters, threats, relation claims | medium-high, relation scoped |
| high-ladder gameplay with reasoning | tactical context and examples | medium |
| tier/ranking overview | coverage and discovery | low for direct facts |
| pure entertainment gameplay | coverage only or reject | low / usually no promotion |

Source queue rows must preserve:

- URL and platform id;
- uploader;
- publication date if available;
- discovered query/lane;
- source type;
- target entities/moves/archetype;
- subtitle/ASR status;
- source-quality prior;
- distribution state: internal_only | source_metadata_only | shareable_derived.

### 5.2 Raw Preservation

Raw media does not need to be duplicated, but the pipeline must preserve:

- source URL and platform id;
- transcript/subtitle artifact path;
- evidence spans with timestamps;
- repair logs and unresolved terms;
- transform lineage and extractor version.

If a correction is later discovered, the system must be able to trace which
claim atoms, set families, mechanism rules, and Gold items depended on the bad
surface form.

### 5.3 Cleaning / Dedup / Canonicalization

Canonicalization rules:

- A-layer exact match wins over fuzzy text.
- Known alias/ASR repairs must be recorded, not silently overwritten.
- Unresolved terms stay unresolved.
- Attribute-typed skill surfaces normalize to canonical skill plus attribute
  when mechanism supports it, e.g. `电愿力冲击` -> `愿力冲击` + `电`.
- Illegal species-move assignments are excluded and preserved as negative
  evidence, not deleted.

Dedup rules:

- duplicate source ids/BV ids are skipped;
- duplicate subtitle payloads are not new evidence;
- repeated claims across independent sources increase confidence;
- repeated claims inside one long source increase trace strength, not source
  diversity.

### 5.4 Extraction / Annotation

Annotation decisions must follow a guideline, not ad hoc Agent taste.

Required labels:

- `coverage_only`
- `set_skeleton`
- `build_configuration`
- `tactical_context`
- `set_family`
- `alter_variant`
- `separate_set`
- `split_blocked`
- `mechanism_claim`
- `relation_claim`
- `gold_negative`

Set identity rule:

```text
Set identity is inferred from tactical intent, not field equality.
```

Nature, IV, bloodline, moves, role wording, team context, and matchup duty are
signals. One field changing is not enough to split a set.

### 5.5 Merge / Split

Merge when:

- same species;
- stable core job;
- visible core move/mechanism overlap;
- differences look like flex slots;
- build signals do not imply different tactical intent.

Split when:

- multiple aligned signals imply different job, e.g. output vs bulk/control;
- role wording differs materially;
- move package and nature/IV/bloodline bundle point to another intent;
- source evidence supports a separate flow rather than a flex variant.

Block instead of deciding when:

- evidence is source-wide but not set-specific;
- ASR uncertainty touches a core field;
- same species has overwide move pools without flow-specific evidence;
- observed battle form may not equal roster species.

### 5.6 Verifier Layers

No candidate reaches review packet without checks from at least one appropriate
verifier layer:

- A-layer: species/move/ability legality and canonical names;
- rules: known error ledger and mechanism guardrails;
- model/LLM: extraction and paraphrase candidate generation only;
- LLM-as-judge: rubric evaluation of supplied evidence and candidate outputs,
  never primary fact creation;
- reviewer Agent: consistency, provenance, split/merge, source quality;
- PM: high-impact domain/product judgment.

LLM-generated or model-suggested data is candidate material. It enters the
dataset only after rule/A-layer/reviewer/PM gates appropriate to its risk.

LLM judge output is audit evidence about pipeline behavior. It is not source
evidence for Roco facts, and it cannot override deterministic legality,
provenance, Gold, or PM decisions.

## 6. Review Independence and Governance

Roles:

| Role | May do | Must not do |
|---|---|---|
| Collector | source discovery, queue rows | claim facts from metadata |
| Ingest/Normalizer | transcript, repair, canonicalization candidates | promote unresolved terms |
| Extractor | claim atoms, inventory, candidates | review its own high-risk outputs |
| Consolidator | merge/split proposals | finalize high-risk splits |
| Reviewer | audit candidates, run validators, build packet | silently accept disputed/high-risk items |
| PM | decide high-impact domain/product gates | review raw YAML/code |

Independence rule:

- High-risk items require a reviewer role distinct from the extractor role.
- Review artifacts must record extractor and reviewer identity at least as
  role, agent id, and run/context id.
- PM-reviewed items must record the packet and decision.
- Disagreements produce a `disagreement_log` or contradiction entry.
- Same-context self-review is allowed only for low-risk candidate hygiene, not
  for Gold acceptance, mechanism boundaries, runtime promotion, or changes to
  reviewed ledgers.

Reviewer agreement policy:

| Item type | Minimum review |
|---|---|
| low-risk coverage/set skeleton | extractor + validator |
| set family candidate | reviewer packet or family ledger policy |
| Gold item | PM decision, or PM-approved explicit batch policy |
| mechanism boundary | reviewer + PM if high impact or contradicted |
| runtime promotion | PM policy + validator + audit log |

Review packet budget:

- 3-6 required decisions;
- 8-12 low-risk candidates;
- 5-10 auto defer/reject rows;
- one screen of impact summary.

Exceeding this budget is a packet failure, not a PM failure.

## 7. Quality Metrics

### 7.1 Required Metrics

| Metric | Unit | Initial gate |
|---|---|---|
| entity resolution rate | promoted fields | 100% promoted fields resolve or mark unresolved outside promoted fields |
| move legality rate | promoted move assignments | 100% legal for species or excluded with reason |
| unresolved ASR rate | promoted fields | 0 unresolved ASR in promoted fields |
| source span coverage | Gold/reviewed claims | 100% have span refs |
| field completeness | set family candidates | report species/moves/role/config completeness; no universal pass gate yet |
| merge/split regression | Gold split/family cases | 100% no critical Gold violation for blocked/promoted changes |
| negative-case protection | Gold negative cases | 100% forbidden behavior absent |
| review pass/defer/reject rate | review packets | reported per packet |
| RAG evidence retrieval | eval questions | context precision/recall tracked before pass threshold |
| answer faithfulness | covered questions | no answer may contradict retrieved source spans |
| LLM judge calibration | judged review/eval items | baseline_needed until Gold/PM agreement exists |
| human escalation rate | judged candidates | reported; no universal pass gate yet |
| drift/staleness | source/meta snapshot | reported when source date or mechanism version matters |

### 7.2 Error Taxonomy

Minimum error categories:

- ASR entity hallucination;
- canonicalization overreach;
- illegal species-move assignment;
- mechanism name confusion;
- exception promoted to general rule;
- source metadata treated as evidence;
- overmerge;
- oversplit;
- stale source / meta drift;
- review packet incomprehensible to PM.

Every repeated error should become one of:

- error ledger entry;
- Gold negative candidate;
- source reliability update;
- annotation guideline update;
- verifier rule.

## 8. Gold/Eval Contract

Gold Set v0 is not a trophy cabinet. It is the calibration surface for whether
the pipeline is improving.

### 8.1 First Gold v0 Composition

Initial target:

- 20-30 `gold_set_family`;
- 5-10 `gold_split_case`;
- 5 `gold_mechanism_boundary`;
- 3-5 `gold_stateful_form_boundary`;
- 5-10 `gold_negative_case`.

Sampling priority:

1. common PvP usefulness;
2. current high-volume split blockers;
3. mechanism-sensitive cases;
4. real observed errors.

### 8.2 Regression Result Schema

```yaml
schema_version: p14.gold_regression_result.v0
run_id: ""
created_at: ""
gold_manifest_ref: ""
pipeline_version: ""
items:
  - gold_id: ""
    task: extract | canonicalize | merge_split | mechanism_boundary | negative_guard | review_surface
    expected_behavior: ""
    observed_behavior: ""
    result: pass | fail | warn | not_applicable
    severity: critical | major | minor
    evidence_refs: []
summary:
  pass_count: 0
  fail_count: 0
  critical_fail_count: 0
  major_fail_count: 0
  warn_count: 0
  blocked_for_promotion: true
runtime_allowed: false
```

Initial pass policy:

- any critical fail blocks promotion/materialization;
- any negative-case fail blocks promotion/materialization;
- warnings can proceed only if packet states risk and next evidence needed;
- Gold acceptance never implies runtime promotion.

## 9. Snapshot, Versioning, and Datasheet

Canonical snapshot id:

```text
roco_kg_dataset_v0.1-dev/YYYY-MM-DD
```

Snapshot manifest shape:

```yaml
schema_version: p14.dataset_snapshot_manifest.v0
snapshot_id: roco_kg_dataset_v0.1-dev/YYYY-MM-DD
created_at: ""
scope: planning | candidate | reviewed | runtime_candidate
components:
  evidence_kb:
    source_queue_ref: ""
    source_reliability_ledger_ref: ""
    evidence_manifest_refs: []
  structured_kg:
    review_state_refs: []
    set_inventory_summary_refs: []
    mechanism_rule_refs: []
    graph_refs: []
  gold_eval:
    gold_manifest_ref: ""
    regression_result_ref: ""
schema_versions: {}
artifact_hashes: {}
supersession:
  supersedes: []
  superseded_by: null
known_exclusions: []
distribution:
  state: internal_only
  raw_transcripts: internal_reference_only
runtime_allowed: false
```

Dataset card must ship with every release-style snapshot and include:

- task definition;
- component list;
- source composition;
- collection/cleaning/extraction workflow;
- review and role separation;
- quality metrics;
- Gold/Eval coverage;
- known limitations;
- drift/update policy;
- rights/distribution boundary.

## 10. Rights and Distribution Policy v0

Default policy for v0.1 planning:

- dataset snapshots are **internal-only**;
- raw subtitles/transcripts are **internal references only**;
- source URLs, IDs, uploader names, and span refs can be stored for audit;
- derived structured claims are not public deliverables until PM approves a
  distribution policy;
- no public "professional dataset" claim until rights, attribution, and
  redistribution boundaries are reviewed.

This conservative default avoids blocking internal pipeline work while
preventing accidental public dataset language.

## 11. Relationship to Existing P14 Promotion Policy

This planning document does not execute promotion.

It does not revoke the existing P14 standing policy for low-risk automatic
promotion. It only says future dataset-pipeline planning tasks may not perform
promotion or materialization.

If a future production lane uses P14 low-risk automatic promotion, it must still
pass:

- source quality gate;
- A-layer resolution;
- no unresolved ASR in promoted fields;
- no open contradiction;
- reviewed mechanism refs for mechanism-dependent edges;
- strict validators;
- promotion audit log entry.

## 12. Schema Migration Boundary

The plan must acknowledge current graph-root history:

- older material may reference `data/meta_graph/v0/`;
- P14 target root is `data/knowledge_graph/v0/`;
- migration must be explicit, validator-backed, and logged;
- this planning stage does not move graph roots or rewrite runtime consumers.

Any future snapshot/versioning contract must include schema versions and
compatibility references so old artifacts can be interpreted without guessing.

## 13. Agent-executable Task Cards

Each DP task below is executable only if it follows the allowed inputs,
allowed writes, forbidden writes, required sections, validation checklist,
failure handling, and handoff rule.

### DP-01: Dataset Product Contract and Card Template

Objective: create the reusable dataset card/template that turns Roco data into
a documented data product.

Allowed inputs:

- `docs/specs/p14_dataset_pipeline_plan_v0_1.md`
- `docs/specs/p14_dataset_pipeline_external_research_and_local_review_2026_05_22.md`
- `data/knowledge_graph/v0/review_state/source_reliability_ledger.yaml`
- `data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml`

Allowed writes:

- `docs/specs/p14_dataset_card_template_v0.md`

Forbidden writes:

- `artifacts/knowledge_ops/source_probe/`
- `artifacts/knowledge_ops/set_inventory/`
- `data/knowledge_graph/v0/set_graph/`
- `data/knowledge_graph/v0/eval/gold_items/`

Required sections:

- task definition;
- component list;
- source composition placeholders;
- provenance summary;
- review roles;
- quality metrics placeholders;
- rights/distribution boundary;
- known limitations;
- maintenance and drift.

Validation checklist:

- contains `internal_only` default;
- contains raw transcript boundary;
- contains all four Roco products: Evidence KB, Meta Graph/KG, Gold/Eval, LLM
  Wiki;
- does not fill a real snapshot.

Failure handling:

- if source rights cannot be stated, use internal-only default and list PM
  decision.

Handoff artifact:

- one paragraph stating what fields a future snapshot must fill.

### DP-02: Snapshot and Versioning Contract

Objective: define snapshot identity, manifest schema, supersession, and schema
version handling.

Allowed inputs:

- this plan;
- current `data/knowledge_graph/v0/` file layout;
- `docs/specs/p14_knowledge_ops_control_plane.md`.

Allowed writes:

- `docs/specs/p14_dataset_snapshot_versioning_contract_v0.md`

Forbidden writes:

- creating real snapshot directories;
- copying source/evidence artifacts;
- changing graph registry or indexes.

Required sections:

- canonical snapshot id;
- manifest schema;
- included/excluded artifact classes;
- artifact hash policy;
- supersession states;
- schema migration boundary;
- runtime-promotion separation.

Validation checklist:

- uses exactly `roco_kg_dataset_v0.1-dev/YYYY-MM-DD`;
- mentions `data/meta_graph/v0/` compatibility only as historical/input state;
- says snapshot creation is not runtime promotion.

Failure handling:

- if schema root ambiguity remains, record as PM/engineering decision instead
  of moving files.

Handoff artifact:

- minimal manifest example.

### DP-03: Provenance and Sample Schema Contract

Objective: define field-level provenance for Evidence KB, KG, and Gold/Eval
sample units.

Allowed inputs:

- this plan;
- `docs/specs/p14_set_inventory_schema.md`;
- `docs/specs/p14_gold_eval_review_design.md`.

Allowed writes:

- `docs/specs/p14_dataset_provenance_schema_contract_v0.md`

Forbidden writes:

- modifying existing source/evidence/candidate data.

Required sections:

- Evidence KB sample schema;
- KG candidate schema;
- Gold/Eval item schema;
- transform lineage fields;
- repair history fields;
- per-field provenance map tying each promoted species/move/role/relation/
  mechanism field to exact supporting spans;
- reviewer and confidence fields.

Validation checklist:

- every sample type has source/span/provenance fields;
- every promoted structured field has `field_provenance` or an explicit
  unresolved/not-applicable reason;
- every promoted/reviewed decision has reviewer and packet fields;
- review artifacts record extractor/reviewer role, agent id, and run/context
  id;
- `runtime_allowed: false` appears in examples.

Failure handling:

- if existing artifacts lack a field, mark as migration requirement rather than
  editing artifacts.

Handoff artifact:

- migration-needed field list.

### DP-04: Gold/Eval Regression Contract

Objective: define executable Gold/Eval regression behavior.

Allowed inputs:

- this plan;
- `docs/specs/p14_gold_eval_review_design.md`;
- `data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml`;
- pending gold candidate packets as read-only references.

Allowed writes:

- `docs/specs/p14_gold_eval_regression_contract_v0.md`

Forbidden writes:

- accepting pending Gold packets;
- creating `gold_items`;
- changing Gold manifest counts.

Required sections:

- gold item input schema;
- prediction/output schema;
- pass/fail result schema;
- critical/major/minor severity;
- thresholds;
- dashboard integration;
- regression history location.

Validation checklist:

- any critical fail blocks promotion/materialization;
- negative-case fail blocks promotion/materialization;
- Gold acceptance remains separate from runtime promotion;
- first Gold v0 sampling priority is common usefulness plus hard blockers.

Failure handling:

- if Gold manifest is empty, define contract and mark runner as pending seeded
  Gold.

Handoff artifact:

- example regression result YAML.

### DP-05: Quality Metrics and Dashboard Contract

Objective: define metrics that prove the dataset is improving rather than only
growing.

Allowed inputs:

- this plan;
- latest autorun dashboard as read-only operational evidence;
- source reliability ledger;
- error ledger.

Allowed writes:

- `docs/specs/p14_dataset_quality_dashboard_contract_v0.md`

Forbidden writes:

- running batch ingest;
- modifying dashboards generated by previous runs.

Required sections:

- metric definitions;
- sample unit for each metric;
- initial thresholds or baseline-needed status;
- error taxonomy;
- dashboard fields;
- stop thresholds.

Validation checklist:

- includes entity resolution, move legality, unresolved ASR, source span
  coverage, merge/split, negative-case protection, review pass rate, RAG
  retrieval, faithfulness, drift.

Failure handling:

- if a metric lacks baseline, record "baseline_needed" instead of inventing a
  pass threshold.

Handoff artifact:

- dashboard field list.

### DP-06: Retrieval KB Eval Contract

Objective: define how Evidence KB retrieval and answer support will be tested.

Allowed inputs:

- this plan;
- RAG evaluation references in the external review;
- current retrieval specs if needed.

Allowed writes:

- `docs/specs/p14_retrieval_kb_eval_contract_v0.md`

Forbidden writes:

- changing advisor runtime;
- running live answer smoke tests;
- generating new eval data.

Required sections:

- covered/uncovered question classes;
- retrieval relevance;
- context recall/precision;
- faithfulness/groundedness;
- noise sensitivity;
- stale-source rejection;
- answer degradation behavior.

Validation checklist:

- separates retrieval KB eval from graph-card validation;
- no pass threshold is claimed before baseline;
- every eval sample must reference evidence or known-uncovered status.

Failure handling:

- if retrieval runtime does not expose needed trace, record runtime instrumentation
  requirement only.

Handoff artifact:

- eval sample schema.

### DP-07: Mechanism Rule Dataset Lane

Objective: define mechanism-rule dataset states, contradiction handling, and
affected-asset recheck.

Allowed inputs:

- this plan;
- `docs/specs/p14_knowledge_ops_control_plane.md`;
- `data/knowledge_graph/v0/review_state/error_ledger.yaml`;
- mechanism rule templates/registries as read-only references.

Allowed writes:

- `docs/specs/p14_mechanism_rule_dataset_lane_v0.md`

Forbidden writes:

- finalizing mechanism rules;
- modifying rule registry;
- changing affected asset index.

Required sections:

- mechanism claim lifecycle;
- contradiction taxonomy;
- high-impact review threshold;
- affected asset links;
- regression checks;
- version/drift policy.

Validation checklist:

- mechanism-dependent edges require reviewed rule refs;
- contradictions cannot be normalized away;
- source exceptions do not become general rules.

Failure handling:

- if a current mechanism ambiguity is found, log as example only, not as a new
  rule decision.

Handoff artifact:

- mechanism contradiction entry template.

### DP-08: Review Independence and PM Packet Contract

Objective: make PM review readable and prevent same-Agent self-approval.

Allowed inputs:

- this plan;
- `docs/specs/p14_gold_eval_review_design.md`;
- `docs/specs/p14_knowledge_ops_control_plane.md`.

Allowed writes:

- `docs/specs/p14_dataset_review_independence_contract_v0.md`
- `artifacts/knowledge_ops/review_packets/p14_dataset_pipeline_plan_v0_1_pm_review.md`

Forbidden writes:

- accepting data;
- changing review ledgers;
- changing Gold manifest.

Required sections:

- role table;
- independence rule;
- disagreement log;
- PM action vocabulary;
- packet size budget;
- high-risk escalation criteria.

Validation checklist:

- packet uses 3-6 decision budget;
- allowed PM actions align with P14/Gold docs;
- packet states runtime impact none;
- no raw YAML/code required for PM review.

Failure handling:

- if more than 6 PM decisions appear, split or defer lower-priority decisions.

Handoff artifact:

- PM packet plus reviewer role policy.

### DP-09: Plan Verification Runbook

Objective: make planning-only verification executable.

Allowed inputs:

- git diff/status;
- this plan;
- README;
- Gold manifest;
- graph registry and indexes as read-only references.

Allowed writes:

- `docs/specs/p14_dataset_plan_verification_runbook_v0.md`

Forbidden writes:

- any data or runtime mutation.

Required checks:

```bash
git status --short -- docs/specs data/knowledge_graph/v0 artifacts/knowledge_ops
rg -n "^\\s*runtime_allowed:\\s*true\\b" docs/specs/p14_*.md
rg -n "p14_dataset_pipeline_plan_v0_1|p14_acquisition_skill_integration_contract_v0|p14_verifier_llm_judge_eval_contract_v0" docs/specs/README.md
sed -n '1,80p' data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
git diff --name-only -- data/knowledge_graph/v0/set_graph data/knowledge_graph/v0/eval artifacts/knowledge_ops
git status --short -- data/knowledge_graph/v0/set_graph data/knowledge_graph/v0/eval artifacts/knowledge_ops
```

Acceptance criteria:

- only planning docs and PM review packet changed;
- no source ingest artifacts added;
- graph registry/index files unchanged;
- forbidden data/artifact paths have no new tracked diff and no new untracked
  files relative to the pre-goal baseline;
- Gold manifest counts unchanged unless PM explicitly accepted Gold;
- no planning doc introduces a standalone `runtime_allowed` field set to true.

Failure handling:

- if forbidden paths changed, stop and report exact path before continuing.

Handoff artifact:

- final verification note with command outputs summarized.

### DP-10: Acquisition Skill Integration Contract

Objective: define how strengthened `social-media-reader` / Scribe-style
acquisition feeds Roco without bypassing Roco dataset governance.

Allowed inputs:

- this plan;
- `/Users/okfin3/Documents/Obsidian/skills/social-media-reader/SKILL.md`;
- `/Users/okfin3/.codex/skills/roco-video-ingest/SKILL.md`;
- Scribe release/README information as external reference;
- existing Roco ingest tools as read-only references.

Allowed writes:

- `docs/specs/p14_acquisition_skill_integration_contract_v0.md`

Forbidden writes:

- modifying `social-media-reader` implementation;
- modifying Scribe or vendoring Scribe code;
- source discovery expansion;
- transcript acquisition;
- `artifacts/knowledge_ops/source_probe/`;
- `artifacts/knowledge_ops/set_inventory/`;
- `data/knowledge_graph/v0/set_graph/`;
- `data/knowledge_graph/v0/eval/`;
- runtime, API, app, or graph materialization files.

Required sections:

- skill boundary;
- platform router;
- `source_transcript_bundle` schema;
- Scribe import/file-boundary policy;
- Roco import adapter requirements;
- rights/provenance fields;
- failure modes and quality gates.

Validation checklist:

- acquisition output stops at source/transcript bundle;
- bundle contains URL/platform/source/acquisition/transcript method/timestamps
  when available/rights state;
- Roco AB refinement and provenance gates remain mandatory;
- no KG, Gold, D-layer, or runtime data can be created by acquisition;
- no platform credential or cookie leakage is allowed.

Failure handling:

- if a platform cannot supply a full transcript, mark coverage-only or
  unresolved instead of forcing extraction.

Handoff artifact:

- bundle schema plus adapter requirements for future implementation.

### DP-11: Verifier and LLM-as-Judge Eval Contract

Objective: define the professional eval layer that sits before human review and
after deterministic/rule-based checks.

Allowed inputs:

- this plan;
- `docs/specs/p14_gold_eval_regression_contract_v0.md`;
- `docs/specs/p14_retrieval_kb_eval_contract_v0.md`;
- `docs/specs/p14_dataset_quality_dashboard_contract_v0.md`;
- accepted Gold/Eval docs as read-only references if they exist later.

Allowed writes:

- `docs/specs/p14_verifier_llm_judge_eval_contract_v0.md`

Forbidden writes:

- generating eval data;
- accepting Gold;
- running live eval;
- changing runtime instrumentation;
- promoting candidate data;
- modifying graph, mechanism, or review ledgers.

Required sections:

- verifier cascade;
- LLM judge task boundaries;
- judge input/output schemas;
- evidence faithfulness rubric;
- retrieval relevance / answer support rubric;
- merge/split reasoning rubric;
- review-packet readability rubric;
- calibration against Gold and PM review;
- anti-bias/leakage rules;
- human review placement.

Validation checklist:

- LLM judge is not a source of Roco facts;
- deterministic legality/provenance failures cannot be overridden by a judge;
- judge output is structured and evidence-linked;
- PM sees only high-impact failures, conflicts, or escalation packets;
- judge metrics are dashboarded as baseline-needed until calibrated.

Failure handling:

- if Gold is not seeded, define schemas and mark calibration as
  `baseline_needed` rather than inventing thresholds.

Handoff artifact:

- verifier cascade and judge output schema.

## 14. PM Decisions Required Before Production

These decisions block production dataset claims, not this planning rewrite.

1. **Distribution default**
   - Recommendation: v0.1 snapshots are private/internal-only.
2. **Raw transcript handling**
   - Recommendation: raw transcripts are internal references, not
     redistributable snapshot payload.
3. **Gold priority**
   - Recommendation: common PvP usefulness first, with hard blockers and real
     negative cases mixed in.
4. **Low-risk promotion policy**
   - Recommendation: dataset plan acknowledges existing P14 standing policy but
     planning tasks do not execute it.
5. **First runtime-facing snapshot bar**
   - Recommendation: decide after Gold/Eval regression and quality dashboard
     contracts exist.

## 15. Completion Criteria for This Plan

This revised plan is acceptable only if it passes these checks:

- PM summary defines the dataset as a governed data product;
- Roco sample units are defined;
- provenance fields are specified;
- quality metrics and error taxonomy are specified;
- Gold/Eval regression result schema is specified;
- snapshot manifest schema is specified;
- rights/distribution default is specified;
- role separation and reviewer independence are specified;
- acquisition skill boundary is specified;
- verifier / LLM-as-judge eval boundary is specified;
- P14 low-risk promotion policy is acknowledged without executing it;
- schema migration boundary is acknowledged;
- every DP task has allowed inputs, allowed writes, forbidden writes, required
  sections, validation checklist, failure handling, and handoff artifact;
- planning-only constraints remain intact.

## 16. Sources

- Datasheets for Datasets: https://arxiv.org/abs/1803.09010
- DataComp-LM: https://papers.nips.cc/paper_files/paper/2024/hash/19e4ea30dded58259665db375885e412-Abstract-Datasets_and_Benchmarks_Track.html
- FineWeb: https://arxiv.org/abs/2406.17557
- DeepSeek-R1: https://arxiv.org/abs/2501.12948
- Ragas Testset Generation: https://docs.ragas.io/en/latest/concepts/test_data_generation/
- Scribe v0.4.3 release: https://github.com/autogame-17/scribe-studio/releases/tag/v0.4.3
- Scribe repository/README: https://github.com/autogame-17/scribe-studio
