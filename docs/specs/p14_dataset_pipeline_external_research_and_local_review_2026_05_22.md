# P14 Dataset Pipeline External Research and Local Review

Status: planning review
Date: 2026-05-22
Scope: dataset construction pipeline planning only
Runtime effect: none

This review does not authorize dataset production, graph materialization, gold
acceptance, or runtime promotion.

## 0. One-line Goal

Build a plan for a professional-ish Roco knowledge dataset pipeline before
asking `/goal` to execute any dataset construction.

In this project, "dataset" means three connected assets:

1. retrieval knowledge base from source-grounded segments;
2. structured graph dataset for set families, mechanisms, relations, and review
   state;
3. small gold/eval set for regression, calibration, and PM review safety.

## 1. External Research Baseline

The external pattern is not "collect a lot of files". It is a governed data
asset with documentation, provenance, quality gates, eval use, and maintenance.

### 1.1 Dataset Documentation

The `Datasheets for Datasets` proposal frames dataset documentation around why
the dataset was created, what it contains, intended/non-intended use,
distribution, maintenance, and risks. Product consequence for Roco: every
released dataset snapshot needs a dataset card/datasheet, not only scattered
pipeline artifacts.

Google's Data Cards work adds a workflow point: dataset documentation can track
requests, process metadata, annotation metadata, and approvals through the
dataset creation workflow. Product consequence for Roco: review packets and
ledgers should roll up into a dataset-level card, not stay only as local YAML.

Hugging Face Dataset Cards make the public-facing shape concrete: README-level
metadata, dataset context, intended use, and risk/bias notes. Product
consequence for Roco: even if the dataset stays private, the same structure is
useful as the review cockpit.

### 1.2 Eval Dataset Practice

OpenAI's evaluation docs treat datasets as dynamic spaces that grow as edge
cases and blind spots are found, and then move to larger-scale evals for
tracking across versions. Product consequence for Roco: Gold Set v0 should be a
living regression set, not a one-time approval artifact.

OpenAI Evals also separates data, eval parameters, and eval templates. Product
consequence for Roco: Gold/Eval should have machine-checkable tasks and expected
behaviors, not only PM prose.

### 1.3 Knowledge Graph Construction

Automatic KG construction literature commonly separates acquisition,
refinement, and evolution. Acquisition includes entities, types, coreference,
and relation extraction; refinement includes fusion/completion; evolution
handles changing or conditional knowledge. Product consequence for Roco: P14 is
strong on acquisition/volume, partially started on refinement/recluster, and
weak on explicit evolution/versioning.

### 1.4 RAG Evaluation

RAG evaluation literature splits quality into retrieval quality, faithfulness to
retrieved context, and generation quality. Product consequence for Roco: our
pipeline plan should not only validate graph cards; it also needs tests that
the retrieval knowledge base and answer assembly use the right evidence without
overclaiming.

## 2. Local Review Summary

### 2.1 What Roco Already Has

P14 already has a serious candidate pipeline:

- source discovery and queue expansion;
- Bilibili ingest and subtitle/ASR fallback path;
- AB-refined transcript and evidence foundation artifacts;
- Set Inventory L1a/L1b/L2/L3 schema;
- cross-source consolidation and split-blocker handling;
- family review ledgers and reviewer ledgers;
- source reliability ledger;
- error ledger and gold negative candidates;
- autorun dashboards with PM gates;
- tests for key `tools/p14_*` scripts.

Latest local dashboard evidence shows the volume lane is no longer toy-scale:

- active sources: 795;
- subtitle-available sources: 758;
- species in consolidation: 236;
- split-blocked species: 45;
- review candidates: 19;
- family review candidates: 37.

This means the bottleneck is no longer "can we collect data". The bottleneck is
"can the resulting data be documented, versioned, evaluated, reviewed, and
promoted without poisoning runtime".

### 2.2 What Is Still Missing

#### Missing A: Dataset-level product contract

Current docs define P14 control plane and schemas, but there is not yet one
dataset-level contract that says:

- what dataset components exist;
- what counts as one dataset release snapshot;
- what is private/internal only;
- what can be exported or shared;
- what maintenance and supersession rules apply.

Without this, Agents will keep thinking "pipeline success" means another batch
of source ingest.

#### Missing B: Dataset card / datasheet

Roco has review packets and dashboards, but no dataset card that rolls up:

- purpose and intended use;
- source composition;
- annotation/review process;
- known bias and source skew;
- ASR/transcript risk;
- version and maintenance policy;
- non-goals and prohibited uses.

#### Missing C: Snapshot/versioning semantics

We have phase ids and batch ids, but no explicit dataset snapshot unit such as:

```text
roco_kg_dataset_v0.1-dev/YYYY-MM-DD
```

The plan must define snapshot contents and what changes across versions:

- source queue state;
- evidence segments;
- set inventory/consolidation;
- reviewed graph candidates;
- gold/eval set;
- dashboard/eval results.

#### Missing D: Gold/Eval is designed but empty

Gold Set v0 is structurally present, but accepted counts are still zero.
Pending packets exist, but the manifest remains `draft_no_pm_accepted_items`.

For planning, the gap is not "accept them now". The gap is a formal eval loop:

- gold item schema;
- expected behavior per item;
- regression runner;
- dashboard integration;
- pass/fail thresholds;
- how accepted gold differs from runtime promotion.

#### Missing E: Retrieval KB evaluation

The current pipeline focuses heavily on graph/set candidates. The dataset plan
also needs retrieval tests:

- can source-grounded retrieval find the right segments for a question;
- can it avoid stale/low-quality segments;
- can answer assembly cite or use evidence faithfully;
- does it degrade honestly when the dataset lacks coverage.

#### Missing F: Mechanism rule dataset plan

Mechanism rules are specified, but not yet a dataset-quality lane with:

- contradiction taxonomy;
- high-impact rule review threshold;
- affected asset index updates;
- rule-level regression tests;
- explicit versioning when mechanics or meta changes.

#### Missing G: Governance and role separation

The local workflow has PM review packets, but the dataset plan should make the
roles explicit:

- collector/ingester;
- normalizer;
- set-family consolidator;
- mechanism reviewer;
- eval reviewer;
- PM gate.

This matters because same-context review can approve its own mistakes.

#### Missing H: Source rights and distribution policy

Because sources are Bilibili/community material, the plan needs a private-vs-
public boundary:

- raw subtitles/transcripts may be internal-only;
- derived structured facts may be exportable only with source references;
- video URLs and metadata can be stored, but redistribution policy must be
  defined before any public dataset claim.

This is a planning blocker for "professional dataset" language.

## 3. Gap Against Professional Dataset Construction

Roco is already stronger than a casual heuristic scraper in these areas:

- source provenance is preserved;
- runtime promotion is gated;
- A-layer legality checks block fake move assignments;
- PM-readable review packets exist;
- autorun has dashboards and stop gates;
- known errors are being converted into negative gold candidates.

The remaining gap is mostly product/data-governance, not raw engineering:

| Area | Current state | Gap |
|---|---|---|
| Collection | Working at scale | Needs dataset-level scope and source composition targets |
| Transformation | Working for Set Inventory | Needs stronger transcript/normalization quality metrics |
| Documentation | Fragmented specs/packets | Needs dataset card/datasheet |
| Eval | Designed but not activated | Needs accepted gold + regression runner |
| KG refinement | Partial via recluster/split blockers | Needs formal refinement/evolution plan |
| RAG eval | Mostly implicit | Needs retrieval/faithfulness tests |
| Governance | PM packet gates exist | Needs role separation and snapshot/release gates |
| Distribution | Undefined | Needs private/public and rights policy |

## 4. Can `/goal` Help?

Yes, but only for planning and control-plane hardening right now.

Good `/goal` targets:

- write dataset pipeline plan v0.1;
- write dataset card template;
- write snapshot/versioning contract;
- define gold/eval regression harness contract;
- define retrieval KB eval contract;
- define mechanism rule dataset lane;
- produce PM review summary and next `/goal` charters.

Bad `/goal` targets right now:

- run more volume ingest;
- accept gold packets automatically;
- materialize graph cards;
- runtime promotion;
- publish/export a dataset;
- silently change existing reviewed data.

## 5. Recommended Next `/goal`

```text
/goal 完成 Roco Dataset Pipeline Plan v0.1，直到产出 PM 可读、Agent 可执行、可恢复的计划包；
without 直接制作数据集、批量 ingest、runtime promotion、graph materialization、自动接受 gold、修改已审核数据。
```

### Completion Criteria

The plan package is done only if it contains:

1. `Dataset Pipeline Plan v0.1`
   - components: retrieval KB, structured graph, gold/eval;
   - stage map: source -> ingest -> repair -> evidence -> inventory -> graph
     candidates -> gold/eval -> promotion gate;
   - owner/role separation and stop rules.
2. `Dataset Card Template v0`
   - purpose, composition, source types, limitations, review process,
     maintenance, distribution boundary.
3. `Snapshot and Versioning Contract v0`
   - what a snapshot includes;
   - how versions advance;
   - how superseded items are handled.
4. `Eval Contract v0`
   - gold item expected behavior;
   - regression tasks;
   - pass/fail thresholds;
   - dashboard integration.
5. `PM Review Packet`
   - one-page summary;
   - only decisions that affect product/governance;
   - no YAML/code required.

### Stop Conditions

Stop and ask PM only if the plan needs a product decision on:

- private-only vs potentially shareable dataset;
- whether raw transcripts can be part of a dataset snapshot;
- whether gold acceptance can ever be batch accepted;
- minimum review budget before runtime promotion;
- whether D-layer examples belong in this dataset plan or stay separate.

## 6. Immediate Recommendation

Run exactly one planning `/goal` next. Do not continue volume lane in this
conversation.

The right next artifact is a plan package, not a larger dataset.

## Sources

- Timnit Gebru et al., "Datasheets for Datasets":
  https://www.microsoft.com/en-us/research/uploads/prod/2019/01/1803.09010.pdf
- Google Research, "The Data Cards Playbook":
  https://research.google/blog/the-data-cards-playbook-a-toolkit-for-transparency-in-dataset-documentation/
- Hugging Face Hub, "Dataset Cards":
  https://huggingface.co/docs/hub/datasets-cards
- OpenAI, "Getting started with datasets":
  https://developers.openai.com/api/docs/guides/evaluation-getting-started
- OpenAI Evals:
  https://github.com/openai/evals
- Zhong et al., "A Comprehensive Survey on Automatic Knowledge Graph Construction":
  https://arxiv.org/abs/2302.05019
- Es et al., "Ragas: Automated Evaluation of Retrieval Augmented Generation":
  https://arxiv.org/abs/2309.15217
