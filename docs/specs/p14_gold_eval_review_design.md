# P14 Gold Set, Annotation Guideline, and Review Packet Design

Status: draft v0
Date: 2026-05-21
Scope: Meta Graph knowledge-ops quality system
Runtime effect: none. This document does not authorize runtime promotion.

## 0. Purpose

P14 already has a working volume lane: sources can be discovered, queued,
transcribed, converted into evidence, and consolidated into set candidates.
The remaining risk is quality, not raw throughput.

This document defines the next quality layer:

- **Gold Set v0**: small reviewed benchmark material used to calibrate Agents
  and detect regression.
- **Annotation Guideline v0**: the rules Agents and reviewers use when deciding
  whether evidence describes the same set, an alter variant, a separate set, or
  a defer/reject case.
- **Review Packet Format v1**: the PM-facing surface. The PM must review
  decisions and evidence, not code, YAML, or raw artifact trees.

Product translation: the system should move from "many plausible candidates" to
"candidates whose quality can be measured, corrected, and audited".

## 1. Relationship to Existing P14 Control Plane

Authoritative base documents:

- `docs/specs/p14_knowledge_ops_control_plane.md`
- `docs/specs/p14_set_inventory_schema.md`

This document adds a quality layer above the current candidate pipeline. It
does not replace source queue, evidence foundation, set inventory, family
consolidation, or dashboard logic.

Important boundary:

- Gold items are eval and calibration assets by default.
- Gold acceptance is not runtime promotion.
- Runtime promotion still requires the P14 promotion gates, strict validators,
  and the current no-promotion policy unless PM explicitly changes it.

## 2. Target Assets

### 2.1 Gold Set v0

Gold Set v0 is a small, PM-reviewed reference set for checking whether the
pipeline is getting better or worse.

It should not try to cover the whole meta. It should cover enough common,
ambiguous, and failure-prone examples to make the pipeline measurable.

Initial composition:

| Asset type | Count | Purpose |
|---|---:|---|
| `gold_set_family` | 20-30 | Confirm common set-family units and their accepted alter variants |
| `gold_split_case` | 5-10 | Confirm how to split or keep together high-evidence blocker species |
| `gold_mechanism_boundary` | 5 | Confirm high-risk mechanism boundaries that affect set/edge reasoning |
| `gold_stateful_form_boundary` | 3-5 | Confirm cases where observed battle form, cosmetic descriptor, or transformation state must not become roster-species set evidence |
| `gold_negative_case` | 5-10 optional | Preserve known ASR, entity, source-quality, or overmerge failure patterns |

Recommended first sampling priority:

1. common PvP set families likely to affect user answers;
2. current high-volume split blockers such as 寂灭骨龙, 圣羽翼王, 化蝶, 音速犬;
3. mechanism-sensitive cases already observed in sources;
4. negative examples that caused real extraction mistakes.

Gold Set v0 should include easy cases and hard cases. Easy cases are needed to
detect obvious regressions. Hard cases are needed to improve split/recluster.

### 2.2 Annotation Guideline v0

Annotation Guideline v0 defines the decision rules. The most important rule is:

```text
Set identity is inferred from tactical intent, not field equality.
```

Fields such as nature, individual values, bloodline, move list, team context,
and source wording are evidence signals. They do not individually decide set
identity.

### 2.3 Review Packet Format v1

Review Packet Format v1 defines what the PM sees.

The packet must be short enough to review and rich enough to audit:

- decision requested;
- Agent recommendation;
- source-backed evidence;
- risk and uncertainty;
- what approval changes;
- what stays deferred.

No code and no raw YAML should be required for PM review.

## 3. Gold Set v0 Design

### 3.1 Gold Item Types

#### `gold_set_family`

Use for a confirmed set-family unit.

Example meaning:

- "This 龙息帕尔 physical-output family exists."
- "These one-slot or bloodline-driven variants belong inside the same family."
- "This is not a separate defensive/control set."

#### `gold_split_case`

Use for a species where clustering behavior is the object being reviewed.

Example meaning:

- "Family A and Family B should be separated because their intent differs."
- "These variants should remain one family despite skill differences."
- "Evidence is still too mixed; keep split_blocked."

#### `gold_mechanism_boundary`

Use for a reviewed mechanism rule or boundary that affects extraction or graph
edges.

Example meaning:

- "光合印记 is produced by 光合作用 and is team-wide."
- "愿力冲击 is the canonical skill; typed surfaces such as 电愿力冲击 mean
  愿力冲击 resolved through bloodline attribute, not a separate skill."
- "愿力冲击 is a skill, not 月影冲击 or 怨力冲击."

#### `gold_negative_case`

Use for a failure pattern the pipeline must remember.

Example meaning:

- unresolved ASR entity;
- illegal move assignment;
- source that is too noisy for promotion;
- overwide set merge that previously looked plausible.

#### `gold_stateful_form_boundary`

Use for cases where a battle-observed name or visual descriptor should be
preserved as evidence but should not become species-level set evidence.

Example meaning:

- "爬爬 is an observed battle form likely derived from 化蝶 through 萌化/化茧
  context, not a reviewed 爬爬 roster-species set."
- "黑白 is a cosmetic descriptor, not an archetype or build axis."
- "Move events near the observed form should be preserved, but Set Graph
  promotion must bind them to the correct roster species or stay deferred."

### 3.2 Gold Item Schema

Gold items should be stored as reviewable structured data, but PM packets should
render them into prose.

Draft shape:

```yaml
gold_id: "gold_set_family/longxi_par_physical_output_2026-s1"
gold_type: "gold_set_family"
review_status: "pm_accepted" # pm_accepted | pm_deferred | rejected | superseded
meta_snapshot: "2026-s1"
species:
  canonical_name: "龙息帕尔"
  species_id: ""
decision:
  label: "same_family" # same_family | separate_set | split_blocked | defer | reject
  short_reason: "Signals align around physical-output intent."
set_intent:
  role_summary: "物攻向输出"
  damage_plan: "physical"
  tempo_plan: "pressure_or_clean"
  defensive_plan: "incidental_bulk"
  control_plan: "none_or_low"
signal_bundle:
  core_moves: []
  flex_moves: []
  nature_direction: "physical_output"
  individual_value_direction: ["hp", "speed", "attack"]
  bloodline_purpose: "skill_unlock_or_coverage"
  explicit_source_roles: []
accepted_variants:
  - variant_id: ""
    reason: "same tactical intent; one-slot or coverage difference"
rejected_or_separate_variants:
  - variant_id: ""
    reason: "different defensive/control intent"
evidence:
  sources:
    - source_id: ""
      url: ""
      span_ref: ""
      evidence_summary: ""
quality:
  confidence: "medium" # high | medium | low
  source_diversity: "single_source" # single_source | multi_source | independent_sources
  asr_risk: "none"
  mechanism_risk: "none"
eval_use:
  tasks:
    - "extract_set_family"
    - "recluster_same_vs_split"
  expected_behavior: "Pipeline keeps accepted variants together."
runtime_allowed: false
review_notes: ""
```

### 3.3 Gold Acceptance Criteria

A candidate can enter Gold Set v0 when:

- the PM can understand the decision from a packet without reading code;
- promoted fields use canonical A-layer names or explicitly unresolved labels;
- evidence spans are preserved;
- the decision records both positive signals and the main alternatives;
- the item is useful for future regression checks.

Gold acceptance does not require perfect coverage. It requires a stable
decision that future Agents should preserve.

### 3.4 Gold Set Uses

Gold Set v0 should be used for four checks:

1. **Extraction regression**: can the pipeline recover the same core species and
   move evidence?
2. **Intent classification regression**: does it keep output, control, bulk, and
   mixed intent distinct where gold says they are distinct?
3. **Recluster regression**: does it avoid over-splitting flex variants and
   overmerging different tactical intents?
4. **Review-surface regression**: can the PM packet still explain the decision
   clearly enough for acceptance/defer/reject?

## 4. Annotation Guideline v0

### 4.1 Evidence Hierarchy

When evidence conflicts, use this hierarchy:

1. source span with explicit role/build wording;
2. A-layer legality and canonical entity resolution;
3. repeated cross-source move/configuration co-occurrence;
4. bundle-level stat/nature/bloodline direction;
5. team context and matchup responsibility;
6. Agent inference.

Agent inference may explain a candidate, but it cannot promote one by itself.

### 4.2 Set Identity Rule

Set identity is based on tactical intent.

The question is not:

```text
Are the fields different?
```

The question is:

```text
Do the fields, moves, source wording, and battle context together imply a
different battle job?
```

### 4.3 Same Family

Keep evidence inside the same `set_family` when the bundle points to the same
tactical intent.

Common same-family signals:

- same species;
- same role or battle job;
- overlapping core move package;
- differences are one-slot or two-slot flex choices;
- nature/IV/bloodline changes still support the same plan;
- source wording implies optional replacement, matchup choice, or coverage;
- bloodline appears to serve skill access or coverage rather than a different
  role.

Example: a 龙息帕尔 line with 固执, HP/speed/attack individual values, and a
bloodline used for skill access or 愿力冲击 coverage is still likely a physical
output family if the move package and source role remain output-oriented.

### 4.4 Alter Variant

Use `alter_variant` when the variant is meaningful enough to preserve, but not
different enough to become a separate set.

Alter variant examples:

- one or two moves differ as matchup or coverage slots;
- bloodline changes to unlock a move while the role stays the same;
- speed vs HP emphasis changes the use case, but not the primary job;
- source says "can also bring X" or "replace Y with X".

Alter variants should be searchable and explainable, but they should not inflate
the reviewed set count.

### 4.5 Separate Set Candidate

Create a separate set candidate only when multiple aligned signals imply a
different tactical intent.

Strong split signals:

- core move package changes the damage, tempo, or control plan;
- nature and individual values together point to a different axis;
- source explicitly describes a different role;
- team job or matchup responsibility changes;
- move overlap is low and both sides have enough evidence;
- one cluster is output/cleaning while another is defensive/control/disruption.

For example, if another 龙息帕尔 bundle has defensive nature direction,
HP/defense/special-defense individual values, and more interference/control
moves, it may be a defensive or disruption set rather than the physical-output
family. The reason is the combined intent, not any one field.

### 4.6 Split Blocked

Use `split_blocked` when evidence is abundant but not clean enough to decide.

Split-blocked means:

- do not promote;
- collect more flow-specific evidence;
- try recluster;
- show PM only when a clear decision is possible or a schema issue blocks
  progress.

It does not mean the species is bad data. It means the current clustering is
not trustworthy enough.

### 4.7 Defer or Reject

Use `defer` when evidence may become useful later but is not currently
decidable.

Use `reject` when the source or candidate is not suitable for this graph.

Common defer reasons:

- insufficient move evidence;
- unresolved ASR entity;
- species or move ambiguity;
- one-source claim with no clear role;
- mechanism dependency without reviewed rule.

Common reject reasons:

- off-boundary content;
- illegal move assignment after A-layer check;
- obvious ASR noise that cannot be repaired;
- source is commentary without usable PvP evidence.

### 4.8 Reason Codes

Use stable reason codes in artifacts and packets:

```yaml
same_family_reason_codes:
  - same_intent_flex_slot
  - same_intent_bloodline_skill_unlock
  - same_intent_coverage_option
  - same_core_move_package
  - explicit_source_flex_language

split_reason_codes:
  - damage_plan_divergence
  - tempo_plan_divergence
  - defensive_control_plan_divergence
  - stat_bundle_axis_divergence
  - explicit_source_role_divergence
  - team_job_divergence
  - low_move_overlap_with_sufficient_evidence

defer_reason_codes:
  - insufficient_core_evidence
  - unresolved_asr_entity
  - ambiguous_a_layer_species_id
  - unresolved_move_legality
  - mechanism_rule_unreviewed
  - source_quality_too_low
  - overwide_cluster_needs_recluster
```

## 5. Review Packet Format v1

### 5.1 Packet Goals

The packet should let the PM make high-leverage decisions quickly.

It must answer:

- what decision is needed;
- why the Agent cannot safely decide alone;
- what evidence supports the recommendation;
- what the risk is if accepted;
- what happens if deferred;
- whether the item should enter Gold Set v0, reviewed candidates, or neither.

### 5.2 Review Budget

Default limits:

- 3-6 required decisions per packet;
- 8-12 low-risk batch candidates per packet;
- 5-10 auto defer/reject rows;
- one screen of impact summary.

If a packet exceeds this, split it. A packet that the PM avoids reading is a
failed interface.

### 5.3 Allowed PM Actions

```text
accept
accept as gold
batch accept low-risk
split
keep same family
defer
needs source
reject
fix: ...
```

All actions remain non-runtime unless the packet explicitly says a separate
runtime promotion step is being requested.

### 5.4 Packet Structure

Use four sections.

#### 1. Decision Needed

For high-risk or blocking items.

Template:

```markdown
## 1. Decision Needed

### D1. <species_or_mechanism> - <decision label>

Recommended action: <accept as gold | split | keep same family | defer | reject>

Why this needs PM:
- <risk or product/domain judgment>

Agent read:
- <one-sentence interpretation>

Evidence:
- <source_id> <span/time>: <short paraphrase>
- <source_id> <span/time>: <short paraphrase>

Signals:
- Core moves: <...>
- Build/stat direction: <...>
- Source role wording: <...>
- Conflicts/uncertainty: <...>

If accepted:
- <what enters gold/review ledger>

If deferred:
- <what the next Agent should collect>

PM response:
```

#### 2. Gold/Eval Candidates

For items recommended as Gold Set v0 seeds.

Template:

```markdown
## 2. Gold/Eval Candidates

| ID | Type | Agent recommendation | Why useful for eval | Risk |
|---|---|---|---|---|
| G1 | gold_set_family | accept as gold | common physical-output family | medium: one-source role wording |
```

#### 3. Batch Accept / Auto Defer

For low-risk candidates and automatic non-decisions.

Template:

```markdown
## 3. Batch Accept / Auto Defer

Batch accept low-risk:
- <candidate>: <reason>

Auto defer:
- <candidate>: <defer reason code>; next needed evidence <...>

Auto reject:
- <candidate>: <reject reason code>
```

#### 4. Impact Summary

For product consequences.

Template:

```markdown
## 4. Impact Summary

Coverage gained:
- <species/archetype/role>

Quality impact:
- <gold regression, recluster, ASR, mechanism boundary>

Runtime impact:
- none

Next Agent action:
- <continue volume | recluster | build gold manifest | ask PM>
```

### 5.5 Packet Style Rules

- Show evidence as short paraphrases with span refs, not long transcripts.
- Put recommendation before details.
- Use "accepted variants" and "separate/rejected variants" so the PM does not
  have to infer the comparison.
- Always say whether runtime changes are requested. Default is "runtime impact:
  none".
- Use stable reason codes so reviewer learning can be externalized into
  ledgers.
- Do not expose artifact paths unless useful for audit.

## 6. Implementation Plan

### Step A: Template and Ledger Skeleton

Create:

```text
data/knowledge_graph/v0/eval/
  gold_set_v0_manifest.yaml
  gold_items/

data/knowledge_graph/v0/review_state/
  annotation_guideline_version.yaml
  review_packet_decisions.yaml

artifacts/knowledge_ops/gold_candidates/
```

No runtime reads these files.

### Step B: Seed Gold Candidates

Pick candidates from current review and blocker queues:

- 10 easy/common set families;
- 5 hard split blockers;
- 3 mechanism boundaries;
- 2 stateful form / cosmetic descriptor boundaries;
- 3 negative ASR/entity cases.

Render them into one PM packet using Review Packet Format v1.

### Step C: First PM Review

PM only responds with packet actions.

Accepted gold items go to the gold manifest. Deferred items stay in candidate
state with next-evidence requirements.

### Step D: Regression Harness

Before changing recluster logic, run a lightweight check against Gold Set v0:

- expected same-family cases stay together;
- expected split cases do not merge;
- negative cases are not promoted;
- mechanism boundaries do not get contradicted by extraction output.

### Step E: Dashboard Integration

Extend the dashboard with quality metrics:

- gold item count by type;
- last gold regression status;
- review packet backlog;
- split blocker count and top species;
- error taxonomy counts.

## 7. Current Decisions Captured

1. Set/alter-set identity is based on tactical intent, not single field
   differences.
2. Nature, individual values, bloodline, moves, source role wording, and team
   context are a signal bundle.
3. Bloodline has lower standalone weight when it mainly unlocks a skill or adds
   coverage.
4. Output vs defensive/control split requires multiple aligned signals.
5. Gold acceptance is for calibration and regression, not runtime promotion.

## 8. Open PM Decisions

These do not block drafting, but they should be settled before the first Gold
Set v0 packet is accepted.

1. Should Gold Set v0 optimize first for common PvP usefulness or for hard
   blocker coverage?
   - Recommendation: common usefulness first, with 5 hard blockers mixed in.
2. Should "accept as gold" also imply "batch accepted reviewed candidate"?
   - Recommendation: no. Gold and reviewed candidate status should stay
     separate until validators exist.
3. Should low-risk batch accept be allowed before Gold Set v0 has 20 items?
   - Recommendation: defer runtime-facing batch acceptance; allow only
     candidate-ledger acceptance.
