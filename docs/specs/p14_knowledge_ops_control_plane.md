# P14 Knowledge Ops Control Plane

Status: phase0 foundation accepted
Date: 2026-05-18
Owner: PM direction + Agent execution

PM decisions recorded: 2026-05-18

## 0. Purpose

Roco now needs Agent-driven knowledge construction without letting the Agent
invent, over-promote, or silently normalize wrong PvP knowledge.

This spec defines the control plane before any long-running `/goal` or agent
fleet run. It is not a data schema only. It defines:

- what work units Agents may take;
- what artifacts each work unit must produce;
- which states are runtime-forbidden;
- what validators must block;
- what the PM actually reviews;
- when Agents must stop instead of continuing.

This document uses the OpenClaw agent-fleet case as a control-plane reference,
not as a target shape. Roco is not doing "many Agents for its own sake".
Roco is building a small, gated knowledge ops system.

## 1. Current Problem

The project has enough idea-level design to move, but not enough executable
governance to let Agents run freely.

Current risks:

- Set Graph v0.1 has been redefined by PM expectation from a 15-25 card MVP
  into a useful graph of roughly one hundred or more common sets.
- Mechanism guardrails are under-specified. A few corrected rules from one or
  two sources are not enough to govern a large graph.
- Existing Round 1 artifacts prove extraction is possible, but runtime
  promotion is still zero.
- Review debt is the practical bottleneck. If Agents create more YAML than the
  PM can understand, the system has already failed.

Product translation: the next system must let Agents do most of the gathering,
cleaning, clustering, drafting, and validation, while keeping PM attention on
high-leverage judgment points.

## 2. Product Boundary

### Target Product Shape

Set Graph v0.1 is a release-useful map of common PvP sets and relations.
It should not mean "the first six cards run without crashing".

Proposed v0.1 bar:

- 100-150 reviewed `species_set` cards;
- 8-12 represented archetype buckets;
- 250-500 reviewed relation claims / edges;
- 40-80 reviewed mechanism rules or guardrails;
- every mechanism-dependent edge references at least one reviewed mechanism
  rule;
- smoke answers improve on covered questions and degrade honestly on uncovered
  questions;
- runtime never injects unreviewed cards, unresolved ASR terms, or disputed
  mechanism claims.

This bar is intentionally larger than `p13_meta_graph_round1_set_input_plan.md`.
P13 remains useful as the Round 1 source funnel, but P14 supersedes its
"15 reviewed cards is enough for v0.1" stopping condition.

Data source implication: this scale cannot depend on PM-provided links.
Agents must discover Bilibili/community sources themselves, then route them
through source queue, transcript capture/transcription, evidence foundation,
claim extraction, and review packets. PM link-providing is optional, not a
critical-path dependency.

### Non-goals

P14 does not authorize:

- S-Graph / `agent_synthesis` runtime activation;
- D-layer gold case promotion;
- automatic runtime promotion from raw transcripts;
- automatic mechanism rule finalization;
- changing the user-facing UI;
- using community summaries as facts without source spans;
- treating "Agent thinks it is plausible" as evidence.

D-like material found during graph work is allowed only as candidate substrate:
decision moments, analogy-like reasoning, or tactical judgment chains may be
captured under `artifacts/knowledge_ops/analogy_candidates/`, but they do not
become D-layer gold cases and are not runtime-injected by this control plane.

## 3. Two-layer Knowledge Structure

Large-scale Set Graph work needs two knowledge layers, not one.

### Layer A: Set Graph

Set Graph records concrete PvP configuration units:

- species set identity;
- moves and known configuration details;
- role labels;
- team / archetype context;
- relations to other sets;
- source evidence;
- mechanism rule references when a relation depends on mechanics.

Set Graph answers:

- what sets exist;
- what they tend to do;
- what they are commonly paired with;
- what they threaten or struggle against;
- under what conditions a relation holds.

Set Graph must not become the source of mechanism truth.

### Layer B: Mechanism Rule Layer

Mechanism Rules record normalized game-mechanism claims:

- marks;
- weather;
- energy cost changes;
- status interactions;
- burst / mark / resource loops;
- ability-triggered exceptions;
- scope and patch/meta snapshot;
- contradictions and unresolved source disagreements.

Mechanism Rules answer:

- how the mechanic works;
- what the rule applies to;
- what it does not apply to;
- which claims are disputed;
- which Set Graph edges depend on it.

Recommendation: store reviewed mechanism rules beside Set Graph under one
Graph-owned runtime root. The prose wiki remains the long-form B layer; runtime
uses the compiled reviewed subset.

```text
data/knowledge_graph/v0/
  runtime_manifest.yaml
  set_graph/
  mechanism_rules/
  review_state/
```

Current `data/meta_graph/v0/` is the existing candidate/runtime-compatible
location. P14's target layout is `data/knowledge_graph/v0/`; migration should
be explicit and validator-backed, not a blind directory move.

## 4. Required Data States

### Evidence States

| State | Meaning | Runtime allowed |
|---|---|---:|
| `raw_source` | URL, video, subtitle, ASR, local transcript | no |
| `evidence_segment` | timestamped or span-preserving cleaned segment | no |
| `claim_atom` | one source-backed claim extracted from a segment | no |
| `candidate` | grouped claim ready for schema-specific drafting | no |
| `agent_checked` | A/B validated and internally consistent | no |
| `review_packeted` | ready for PM decision | no |
| `pm_reviewed` | PM accepted source fidelity / mechanism boundary | yes, if validators pass |
| `runtime_promoted` | copied to runtime-readable data and indexed | yes |

Agents may move data up to `review_packeted`.
Only PM decision, or a PM-approved batch policy, may move data to
`pm_reviewed`.

### Set Inventory and Set Graph States

| Level | Name | Meaning |
|---|---|---|
| L1a | coverage_record | species appears in a PvP/team/ranking context, but no reliable move skeleton yet |
| L1b | set_skeleton | species + resolved move evidence; ideally 4 moves, partial 2-3 moves are useful volume |
| L2 | build_configuration | nature, individual values, bloodline, ability/config details when source states them |
| L3 | tactical_context | role, partners, combos, matchup/counterplay claims; sparse and claim-only by default |
| S3 | agent_curated | A-layer validated, no unresolved ASR, review packet ready |
| S4 | pm_reviewed | PM or batch policy accepted |
| S5 | runtime_promoted | graph registry + indexes rebuilt and strict validation passed |

Authoritative inventory schema: `docs/specs/p14_set_inventory_schema.md`.

Operational rule: large-scale autorun should optimize for L1a/L1b volume first.
Window-level evidence remains trace substrate, not the PM-facing primary object.
L3 tactical context is valuable but must not contaminate L1 set skeletons.

### Mechanism Rule States

| Level | Name | Meaning |
|---|---|---|
| M0 | mechanism_mention | raw source mentions a mechanism |
| M1 | mechanism_claim_atom | one source-backed mechanism claim |
| M2 | candidate_rule | normalized claim cluster |
| M3 | agent_checked_rule | A/B-aligned, contradictions listed |
| M4 | pm_reviewed_rule | PM accepted the rule or accepted its uncertainty wording |
| M5 | runtime_rule | compiled into mechanism rule registry |

Mechanism rules are stricter than set cards. If a rule is high impact or
contradicted by sources, it cannot be batch-approved silently.

## 5. Minimal Schemas

### Mechanism Rule Candidate

```yaml
id: "mechanism/photosynthesis_mark_energy/2026-s1"
title: "光合印记回合末能量回复"
meta_snapshot: "2026-s1"
mechanism_type: "mark_energy"
scope:
  applies_to:
    - "光合印记"
  does_not_apply_to: []
normalized_rule: >
  光合印记在回合结束时提供能量收益。具体触发和对象以 reviewed source
  claim 为准。
source_claims:
  - source_id: ""
    source_span_id: ""
    claim_text: ""
    claim_quality: "explicit" # explicit | implied | shorthand | unclear
a_layer_refs:
  species_ids: []
  move_names: []
  ability_names: []
b_layer_refs: []
contradictions:
  - claim_text: ""
    source_id: ""
    status: "unresolved" # unresolved | resolved | rejected
review:
  review_status: "candidate" # candidate | agent_checked | pm_reviewed | disputed | superseded
  reviewer: ""
  review_date: ""
  notes: ""
runtime:
  runtime_allowed: false
  uncertainty_policy: "do_not_inject" # inject | inject_with_caveat | do_not_inject
affected_assets:
  species_set_ids: []
  edge_ids: []
```

### Set Graph Additions

Existing `species_set` cards need these additions before large-scale work:

```yaml
mechanism_refs:
  - "mechanism/photosynthesis_mark_energy/2026-s1"
source_quality:
  transcript_quality: "good" # good | usable | poor
  asr_unresolved_terms: []
  source_span_ids: []
promotion:
  promotion_status: "agent_curated" # candidate | agent_curated | pm_reviewed | runtime_promoted
  promotion_packet_id: ""
```

Each `related_to` entry may also include:

```yaml
mechanism_refs:
  - "mechanism/sandstorm_ground_energy_discount/2026-s1"
evidence_bundle_id: ""
claim_risk: "low" # low | medium | high
```

## 6. Job Types

Agents do not receive open-ended tasks like "improve the graph".
They receive one of these job types.

| Job type | Input | Output | Must not |
|---|---|---|---|
| `source_discovery` | archetype gap / source target | candidate source queue rows | promote source claims |
| `source_ingest` | source URL or local file | source run directory + manifest | discard timestamps/spans |
| `transcript_refine` | raw subtitle/ASR + A/B vocab | AB-refined transcript + unresolved terms | invent missing domain words |
| `evidence_foundation` | refined transcript | segments + claim atoms + quality gate | mark runtime-ready |
| `mechanism_claim_extract` | evidence segments | mechanism claim atoms | normalize contradictions away |
| `mechanism_rule_cluster` | claim atoms | candidate rules + contradiction report | PM-review conflicted rules |
| `set_inventory_build` | evidence segments + A layer | L1a coverage records + L1b/L2/L3 source dossiers | infer missing moves/config as fact |
| `set_candidate_extract` | evidence segments + A layer | S1/S2 trace/window candidates | treat trace windows as reviewed set cards |
| `relation_candidate_extract` | set candidates + claims | edge candidates | create reviewed edges |
| `promotion_packet_build` | agent-curated candidates | PM review packet | hide risk flags |
| `promotion_apply` | PM decisions or approved low-risk policy | runtime data updates | promote rejected/deferred items |
| `graph_validate` | runtime data | validation report | ignore fail-closed errors |
| `answer_smoke_eval` | covered/uncovered questions | smoke report | use internal labels in user-facing answer |
| `incremental_review_audit` | new candidates + review ledgers | delta audit + quarantine list | rely on chat memory |

## 6.1 Source Discovery Autonomy

Source discovery is required, not optional. A graph of 100-150 reviewed common
sets cannot be built from PM-provided links.

Agents may search Bilibili/community sources and add rows to source queue when
coverage gaps exist. They must not treat discovered source metadata as evidence
until subtitles/ASR/transcripts have passed the evidence foundation pipeline.

Each discovered source row must include:

```yaml
source_id: ""
url: ""
platform: "bilibili"
title: ""
uploader: ""
published_at: ""
source_type: "team_explainer" # team_explainer | matchup_counterplay | tier_overview | gameplay_replay | mechanism_tutorial
target_archetype: ""
target_entities: []
target_moves: []
discovery_reason: ""
expected_value: ""
priority: "medium" # high | medium | low
ingest_status: "queued"
source_quality_prior:
  likely_subtitle_available: "unknown" # yes | no | unknown
  likely_noise: "unknown" # low | medium | high | unknown
  promotion_bias: []
```

Discovery rules:

- all sources must be PvP/battle related;
- prefer team explainers and matchup/counterplay explainers over pure tier
  lists;
- allowed discovery lanes are:
  - `bilisearch` query discovery for broad gaps;
  - creator-space fallback from uploaders with prior high-value processed
    sources;
  - related-video fallback from seed videos that already passed evidence
    foundation;
- prefer sources with explicit team, species, move, matchup, or mechanism
  explanation;
- discovery may use A-layer move names as a queue-boundary signal, but move
  matches are still raw-source metadata and never evidence by themselves;
- related-video and creator-space candidates remain raw queue substrate; they
  still must pass the same PvP boundary, de-duplication, subtitle/ASR, evidence
  foundation, and Set Inventory gates;
- gameplay / battle commentary is allowed and useful when the commentator
  explains decisions, matchup logic, or set behavior;
- use tier lists mainly for coverage signals and source discovery;
- pure entertainment gameplay with little battle reasoning is coverage-only at
  best and should not directly promote set/edge claims;
- include mechanism tutorials when many edges depend on one unclear mechanism;
- keep uploader/title/date metadata because source reliability can become a
  review signal;
- do not add many near-duplicate videos for the same archetype while other
  archetypes are empty;
- if a source has no usable subtitle, fallback to transcription, then mark the
  source quality honestly.

Queue expansion must go through an auditable import step rather than direct
hand-edits when a batch is larger than a few rows:

```text
artifacts/knowledge_ops/source_candidates/<batch_id>_candidates.yaml
tools/p14_source_queue_expand.py
artifacts/knowledge_ops/audits/<batch_id>.yaml
artifacts/knowledge_ops/review_packets/<batch_id>_pm_brief.md
```

The expansion gate must:

- de-duplicate by `source_id` and Bilibili BV id;
- reject non-Bilibili rows and rows outside the PvP/battle boundary;
- append accepted rows as `ingest_status: queued`;
- record skipped candidates with reasons;
- update `source_queue.latest_source_queue_expansion`;
- preserve the rule that discovered metadata is not evidence.

Operational rule: tools that update `source_queue.yaml` must run sequentially.
Do not run source queue expansion, source gap fill, volume batch planning, and
autorun dashboard updates in parallel, because the last writer can overwrite a
newer `latest_*` pointer from another tool.

## 6.2 Autorun Trusted Framework

The current goal is not to hand-review individual set cards. The current goal
is to make autorun trustworthy enough that later pipeline improvements can
increase throughput without increasing graph pollution.

P14 autorun therefore runs two separate lanes:

| Lane | Purpose | Default output | PM involvement |
|---|---|---|---|
| `volume_lane` | discover / ingest / refine / evidence-foundation / Set Inventory at scale | L1a/L1b/L2/L3 candidate substrate | none unless source quality or ASR is ambiguous |
| `promotion_lane` | convert stable repeated evidence into reviewed graph assets | review packets, ledgers, graph cards after approval | only for pollution-prone or product-boundary decisions |

The default autorun batch unit is 20-30 sources. If the source queue has fewer
than the target batch size, autorun must expand discovery first instead of
falling back to hand-polishing one species. High-detail investigation is allowed
only when it unblocks a promotion candidate or a schema/guardrail problem.

Every autorun batch must produce a dashboard:

```text
artifacts/knowledge_ops/autorun/<batch_id>.yaml
artifacts/knowledge_ops/review_packets/<batch_id>_autorun_dashboard.md
```

The dashboard must show:

- active source ids used by the batch;
- source health: subtitle/ASR status, blocked sources, repair-required spans;
- Set Inventory and consolidation summary;
- promotion candidates separated from already-reviewed candidates;
- split blockers, transcript blockers, and source-queue capacity blockers;
- next automatic action;
- whether PM attention is required.

Hard rule: dashboard builders must read only the active source ids for the
batch. They must not scan `artifacts/knowledge_ops/` broadly and include stale
candidate files from older runs. This is a promotion-safety requirement, not a
performance preference.

PM should usually see this dashboard, not raw YAML:

- If `pm_attention_required_count == 0`, the Agent continues with source
  discovery or batch ingest.
- If the only blockers are low-quality/transcript-blocked sources, the Agent
  auto-defers them and continues.
- If a blocker would change schema, merge/split a reviewed family, or alter a
  mechanism guardrail, the Agent stops and asks PM.

## 7. Control-plane Directories

Proposed layout:

```text
artifacts/knowledge_ops/
  source_queue.yaml
  source_candidates/*.yaml
  runs/<source_id>/
  evidence/<source_id>/
  mechanism_claims/<source_id>.yaml
  mechanism_rules/candidates/*.yaml
  set_inventory/<source_id>.source_inventory.yaml
  set_candidates/<source_id>.candidate_sets.yaml
  relation_candidates/<source_id>.candidate_edges.yaml
  analogy_candidates/<source_id>.yaml
  review_packets/
  audits/

data/knowledge_graph/v0/
  runtime_manifest.yaml
  set_graph/
    species_sets/*.yaml
    graph_registry.yaml
    edge_index.yaml
    speed_index.yaml
  mechanism_rules/
    rule_registry.yaml
    contradiction_index.yaml
    rules/*.yaml
  review_state/
    reviewer_ledger.yaml
    family_review_ledger.yaml
    error_ledger.yaml
    source_reliability_ledger.yaml
    promotion_audit_log.yaml
    affected_asset_index.yaml
```

Rule: `artifacts/` is candidate/raw workspace. `data/` is release-readable.
No Agent may treat an artifact path as runtime knowledge.

`family_review_ledger.yaml` records set-family scoped review items. It is used
when one family inside a species is stable enough to review, while the parent
species still has unresolved split hypotheses. A family-level ledger entry does
not authorize a species-level standard set card and does not authorize runtime
promotion.

Compatibility rule: until migration is implemented, existing
`data/meta_graph/v0/` remains the current Set Graph candidate location. P14
validators must support the current location first, then migrate into
`data/knowledge_graph/v0/` once the graph root is created.

Why two directories exist:

- `data/meta_graph/v0/` already existed before P14 as the narrow Meta Graph
  candidate/runtime-readable location.
- P14 expands the asset from "meta graph cards" into a broader knowledge graph
  root that also owns mechanism rules and review state.
- The split is transitional, not a desired long-term shape.

Migration policy:

- Phase 0 should run a path/reference audit.
- If impact is low, migrate directly into `data/knowledge_graph/v0/` and update
  tool/runtime references.
- If impact is high, keep a temporary compatibility read path while validators
  and runtime consumers are updated.
- Do not keep two active runtime roots after migration. One graph root should
  own Set Graph, Mechanism Rules, and review ledgers.

## 8. Validators

P14 requires hard validators, not "Agent should remember".

### Mechanism validators

Block if:

- rule is not `pm_reviewed` or `runtime.runtime_allowed != true`;
- source span cannot be found;
- A-layer references do not resolve;
- contradiction exists with `status: unresolved`;
- uncertainty policy is `do_not_inject`;
- rule is marked `superseded` or `disputed`;
- rule changes the meaning of an A-layer move/ability rather than referencing
  it.

### Set Graph validators

Block if:

- card review status is not `pm_reviewed` / `reviewed`;
- any move or species name fails A-layer resolution;
- ASR unresolved terms remain in promoted fields;
- source quality is `poor`;
- source mode is `raw_exact_only` and no AB-refined span exists;
- card depends on mechanism refs that are not runtime rules;
- edge has `claim_only` reasoning but high confidence;
- edge has a high-risk mechanism dependency but no PM-reviewed rule;
- indexes are stale relative to card hashes.

### Runtime validators

Block if:

- runtime reads from `artifacts/`;
- unreviewed graph cards are injected;
- internal labels leak into user-facing answers;
- D-layer or Meta Graph missing case is exposed as an implementation detail;
- covered smoke questions do not improve after claimed promotion;
- uncovered smoke questions become overconfident.

## 9. PM Review Surface

The PM should not review code or YAML. The PM sees review packets.

Companion format: `docs/specs/p14_gold_eval_review_design.md` defines Review
Packet Format v1 for Gold Set v0, set-family, split, and review-surface work.

Each packet has four sections only:

1. **Decision Needed**
   - high-impact mechanism conflicts;
   - set/edge candidates that need product/domain judgment;
   - schema gaps.
2. **Batch Approve Candidates**
   - low-risk, source-backed candidates;
   - A-layer exact matches;
   - no unresolved ASR;
   - no mechanism conflict.
3. **Auto Defer / Reject**
   - low quality source;
   - raw-only overview;
   - unclear ASR;
   - insufficient source span.
4. **Impact Summary**
   - which archetypes gain coverage;
   - which smoke questions should improve;
   - which rules/edges would be affected by approval.

Allowed PM responses:

```text
approve
accept as gold
reject
fix: ...
needs source
defer
batch approve low-risk
split
keep same family
```

Default if PM does not respond: `defer`, not runtime promotion. Gold acceptance
is an eval/calibration decision by default and does not imply runtime
promotion.

Exception: PM has authorized automatic promotion for low-risk set/edge items
when all low-risk promotion gates pass. This is a standing policy, not a new PM
decision per item.

PM attention policy:

- Ask PM only for decisions that can seriously pollute the graph, block schema
  progress, or change product interpretation.
- Do not ask PM to review routine low-risk set candidates one by one.
- Do not ask PM to resolve low-quality sources; defer them automatically.
- Do ask PM when a mechanism contradiction affects multiple promoted or
  promotable edges.
- Do ask PM when a candidate would revise an already reviewed mechanism rule.
- Do ask PM when the Agent cannot distinguish ASR error from a real domain
  entity after A/B lookup and source comparison.

Low-risk automatic promotion gates:

- source quality is `good` or `usable`, not `poor`;
- source is PvP/battle related and has source spans;
- species, moves, abilities, and mechanism refs resolve;
- no unresolved ASR terms appear in promoted fields;
- no open contradiction touches the card/edge;
- edge reasoning is not high-risk `claim_only`;
- mechanism-dependent edge references reviewed mechanism rules;
- reviewer ledgers contain no matching error pattern;
- strict validators pass;
- promotion is logged in `promotion_audit_log.yaml`.

Any failed gate moves the item to review packet or defer. The reviewer Agent may
not "fix around" a failed gate just to keep volume moving.

## 9.1 Reviewer Cognition as Explicit Ledgers

The reviewer Agent must not rely on chat memory to "remember what it learned".
Its cognition must be externalized into review ledgers under
`data/knowledge_graph/v0/review_state/` or the current compatibility location.

Required ledgers:

| Ledger | Purpose |
|---|---|
| `reviewer_ledger.yaml` | Accepted review policies, batch-approval rules, current PM decisions |
| `error_ledger.yaml` | Known extraction/ASR/mechanism mistakes and their repair patterns |
| `source_reliability_ledger.yaml` | Per-source/uploader quality, recurring bias, subtitle/ASR quality |
| `promotion_audit_log.yaml` | Every promotion decision, source spans, validator hash, reviewer |
| `affected_asset_index.yaml` | Which cards/edges depend on which mechanism rules |
| `contradiction_index.yaml` | Open/resolved mechanism contradictions and affected assets |

Incremental review loop:

1. Load ledgers and current runtime/candidate graph.
2. Compare new candidates against accepted rules, known errors, and source
   reliability.
3. Quarantine candidates that match known error patterns or unresolved
   contradictions.
4. Emit a delta review packet showing only what changed, what became risky, and
   what needs PM judgment.
5. Update ledgers after validation and PM decisions.

If a new source contradicts a reviewed rule, the reviewer Agent must not silently
overwrite the rule. It creates a contradiction entry, marks affected assets, and
asks PM only if the contradiction is high impact or blocks promotion.

Reviewer agents must update their ledgers after every batch:

- accepted auto-promotions become precedents only if later smoke/audit does not
  flag them;
- discovered mistakes become negative examples in `error_ledger.yaml`;
- source/uploader quality updates accumulate in `source_reliability_ledger.yaml`;
- any rule revision updates `affected_asset_index.yaml` so dependent cards and
  edges can be rechecked.

## 10. Agent Execution Model

Recommended execution model:

- one supervisor Agent maintains the mission board and stop rules;
- one to two worker Agents run extraction / clustering jobs;
- one reviewer/verifier Agent runs incremental audits, validators, and smoke
  reports;
- PM only reviews packets.

Do not start with a large parallel fleet. More Agents create more review debt.
The right first target is a reliable small loop.

## 11. Mission Board

Before `/goal`, create a machine-readable mission board:

```yaml
mission_id: "p14_knowledge_ops_foundation"
stage: "structure_pilot"
allowed_dirs:
  - "docs/specs/"
  - "tools/"
  - "tests/"
  - "artifacts/knowledge_ops/"
  - "data/knowledge_graph/v0/"
  - "data/meta_graph/v0/" # compatibility until migration
forbidden:
  - "runtime promotion outside PM-approved policy, ledgers, and validators"
  - "S-Graph activation"
  - "D-layer gold promotion"
  - "UI changes"
stop_rules:
  - "schema cannot express repeated source pattern"
  - "mechanism contradiction affects promoted edge"
  - "validator fails after attempted fix"
  - "PM review packet exceeds review budget"
  - "source quality too low for target archetype"
  - "reviewer ledger contradicts proposed promotion"
```

## 12. Phases

### Phase 0: Structure Pilot

Goal: prove the control plane on existing small data.

Outputs:

- P14 spec accepted;
- `data/knowledge_graph/v0/` target layout drafted or created;
- path/reference audit decides whether to migrate `data/meta_graph/v0/`
  directly;
- mechanism rule candidate schema;
- first validators;
- review packet template;
- reviewer ledgers;
- existing photosynthesis/sandstorm notes converted into mechanism rule
  candidates;
- current six cards remain non-runtime until reviewed against the new gates.

### Phase 1: Set-Centric Incremental Pipeline Pilot

Goal: make the automatic incremental loop executable before running volume.

The primary unit is a `species_set` / relation candidate, not a mechanism rule.
Mechanism work is a supporting guardrail: it only becomes the main task when a
set edge or promotion gate depends on a disputed mechanic.

Outputs:

- machine-readable mission board for source -> evidence -> set candidates ->
  relation candidates -> review packet -> audit;
- 2-4 ingested sources processed end-to-end through the set-centric loop;
- candidate set and edge artifacts generated from at least two different
  archetype/source types;
- PM-readable delta packet that shows stable set candidates, conflicts, and
  blocked promotions without exposing YAML/code;
- reviewer ledgers updated from every batch;
- mechanism claim extraction runs only as a side channel when set/edge
  candidates mention mechanism-dependent reasoning;
- validator blocks mechanism-dependent edges without reviewed refs;
- no runtime promotion unless low-risk promotion policy, ledgers, and strict
  validators all pass.

Mechanism pilot result: the first two-video pilot produced enough
`星陨印记` evidence to prove the guardrail side channel can work. It does not
change the product direction. It is a dependency check for the set graph, not
the main graph construction loop.

### Phase 2: Set Graph Alpha

Goal: run the set-centric loop at modest volume without review overload.

Outputs:

- 30-50 reviewed set cards;
- 5+ archetype buckets;
- 80-150 reviewed edges;
- every mechanism-dependent edge has a reviewed rule;
- Agent-discovered source queue covers missing archetype gaps;
- D-like analogy candidates are captured as artifacts only;
- first answer smoke report.

### Phase 3: Set Graph v0.1

Goal: useful common-set graph.

Outputs:

- 100-150 reviewed set cards;
- 8-12 archetype buckets;
- 250-500 reviewed relation claims;
- 40-80 reviewed mechanism rules / guardrails;
- graph and mechanism validators pass strictly;
- answer smoke improves on covered questions and degrades honestly elsewhere.

## 13. `/goal` Readiness Checklist

Do not start a long-running `/goal` until:

- P14 is accepted or revised by PM;
- mission board exists;
- graph root / mechanism rule storage location is chosen;
- validators fail closed for unreviewed/unresolved assets;
- review packet format is accepted by PM;
- reviewer ledgers exist and incremental audit is defined;
- first source queue has target archetype gaps, not just random videos;
- git/worktree baseline is understandable enough to separate goal changes from
  prior cleanup;
- PM-approved low-risk automatic promotion policy is encoded in ledgers and
  validators.

## 14. PM Decisions Recorded

### D1. Set Graph v0.1 scale

Decision: `100-150 reviewed species_set cards`.

Design implication: source discovery must be Agent-owned. PM-provided links are
not a scalable input path.

### D2. Graph storage

Decision: create a Graph-owned folder under `data/`.

Design target: `data/knowledge_graph/v0/` with `set_graph/`,
`mechanism_rules/`, and `review_state/` subdirectories. Existing
`data/meta_graph/v0/` remains compatibility input until migration.

### D3. Review authority

Decision: only ask PM for items that can cause serious pollution or block the
system. Routine low-risk set/edge candidates may be automatically promoted when
they pass the standing low-risk promotion gates.

Design implication: reviewer Agent must maintain explicit incremental cognition
through ledgers, find mistakes from new evidence, quarantine suspect assets, and
escalate only high-impact conflicts. Automatic promotion must be audit-logged.

### D4. D-layer scope in this control plane

Decision: do not do D-layer gold promotion for now.

Design implication: D-like material discovered during graph work is captured as
`analogy_candidates` only. It does not enter D-layer gold or runtime.

Minimal analogy candidate shape:

```yaml
source_id: ""
source_span_ids: []
situation: ""
entities: []
judgment: ""
why: ""
transfer_hint: ""
review_status: "candidate"
runtime_allowed: false
```

### D5. Source discovery autonomy

Decision: Agents must independently find sources, including Bilibili videos,
when archetype or mechanism coverage is missing.

Design implication: `source_discovery` is a required job type and source queue
must record discovery rationale, expected value, source type, target archetype,
and quality priors.

Source boundary: soft limit to PvP/battle-related content. Team/species
explainers are preferred; battle commentary is allowed when it contains actual
decision or set reasoning.

Fallback discovery lanes are required when Bilibili search is unstable or
low-yield: creator-space mining may expand from proven uploaders, and
related-video mining may expand from proven seed videos. Both lanes only create
source queue candidates; queue expansion and evidence foundation still decide
whether the source is usable.

### D6. Mechanism rule grain

Decision: start with guardrail-grain mechanism rules.

Design implication: mechanism rules should first prevent wrong mechanism
pollution and provide coarse runtime constraints. Exact formulas or
fine-grained numeric variants are added only when A/B data or multiple clear
sources support them.

### D7. Graph directory migration

Decision: if impact is low, migrate directly from `data/meta_graph/v0/` to
`data/knowledge_graph/v0/`.

Design implication: Phase 0 starts with a path/reference audit and should avoid
keeping two active runtime graph roots.

### D8. Smoke eval standard

Decision: defer exact final smoke standard until Graph Alpha has enough reviewed
coverage.

Design implication: Phase 0/1 smoke can be lightweight; formal covered/uncovered
question sets should be designed around the 30-50 reviewed set alpha.

### D9. Public repo boundary

Decision: defer.

Design implication: for now, keep candidate artifacts controlled and do not
optimize graph data for public reuse.

## 15. Immediate Next Step

Implement Phase 0:

1. run a path/reference audit for `data/meta_graph/v0/`;
2. if impact is low, migrate to `data/knowledge_graph/v0/`;
3. create reviewer ledgers and source queue schema;
4. add validators for mechanism refs, promotion status, and low-risk auto
   promotion gates;
5. convert current photosynthesis/sandstorm note into guardrail-grain candidate
   rules;
6. generate a PM review packet using the new format;
7. do not promote high-risk or conflicted runtime assets.
