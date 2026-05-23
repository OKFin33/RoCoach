# P14 Set Inventory Schema

Status: draft for Phase 1 volume-first graph building
Date: 2026-05-18

## Purpose

Set Inventory is the raw-to-candidate layer before reviewed Set Graph cards.
It is built for volume: Agents should be able to ingest many PvP sources and
produce comparable set dossiers without promoting runtime graph data.

The output is not a reviewed `species_set` card. It is source-backed inventory
substrate that later consolidation/review can merge into reviewed cards.

## Layer Model

### L1a Coverage Record

Use when a source mentions a species but does not provide enough move evidence
to form a set skeleton.

Typical sources:

- tier/ranking content;
- team preview or roster mention;
- matchup commentary that mentions a species but not its skills;
- environment recommendation lists.

Fields:

```yaml
species_name: ""
source_aliases_used: []
archetype_tags: []
mention_count: 0
evidence_refs:
  - segment_ids: []
    start_ms: 0
    end_ms: 0
    quote: ""
status: "coverage_only"
runtime_allowed: false
```

### L1b Set Skeleton

Use when a source gives a species plus move evidence.

This is the first real set-building unit. A standard set is ideally
`species + 4 moves`, but partial set skeletons are valuable while building
volume. `known_moves` must pass the A-layer species move-pool legality check:
if a transcript says a move near a species but the species cannot learn/use that
move, the move is excluded from L1b and kept only as an excluded mention for
audit. This prevents matchup narration such as "X fears Y's move" from becoming
fake skill-pool data.

States:

- `complete_4_moves`: species + 4 or more resolved move names;
- `move_pool_4plus_unclustered`: source-level move pool has 4+ resolved move
  names, but they have not been proven to belong to one standard set;
- `partial_2_3_moves`: species + 2-3 resolved move names;
- `single_move_signal`: species + 1 resolved move name;
- `insufficient_moves`: species mention only; should be L1a unless kept for
  trace compatibility.

Fields:

```yaml
species_name: ""
source_aliases_used: []
move_slots:
  known_moves: []
  known_move_count: 0
  missing_move_slots: 0
  max_same_evidence_move_count: 0
  completeness: "partial_2_3_moves"
  same_build_confidence: "low"
legality_filter:
  source: "A_layer_species_move_pool"
  excluded_move_counts: {}
  excluded_move_mentions:
    - move_name: ""
      reason: "not_in_species_move_pool"
      evidence: {}
evidence_refs: []
status: "l1b_set_skeleton"
runtime_allowed: false
```

### L2 Build Configuration

Use only when the source states configuration details. Do not infer missing
configuration.

Fields:

```yaml
configuration:
  nature: ""
  individual_values: {}
  bloodline: ""
  ability_mentions: []
  mechanism_mentions: []
```

### Set Family / Alter Variant Layer

Cross-source consolidation must not treat every different move list as a
separate reviewed set. The candidate unit between L1b source dossiers and a
reviewed Set Graph card is a `set_family`.

Default rule: keep variants together in the same family unless there is
positive evidence that they represent different tactical intents. Set identity
is inferred from the whole signal bundle, not from equality or difference of
individual fields.

Treat as the same `set_family` when:

- species is the same;
- core battle job appears unchanged;
- nature / individual values / bloodline / ability signals, taken together, do
  not imply a different build intent;
- at least one core move or mechanism repeats, and the remaining 1-2 move
  differences look like optional slots;
- the source wording implies "can bring", "replace", "depends on meta", or
  similar flex-slot language.
- bloodline appears to serve skill access or coverage rather than a different
  battle job.

Represent this as:

```yaml
set_family_candidates:
  - family_id: family_01
    family_state: candidate_set_family
    core_moves: []
    flex_moves: []
    representative_moves: []
    damage_axes: [] # physical | magical | mixed | status_or_unknown
    role_groups: []
    build_axes: [] # physical | magical | mixed | speed | bulk
    alter_variants:
      - source_id: ""
        variant_type: "alter_variant"
        moves: []
        roles: []
        damage_axis: ""
        build_axes: []
        configuration: {}
        low_confidence_use: ""
    runtime_allowed: false
```

Use `split_hypothesis` instead of immediately creating separate set cards when
there is evidence of a possible independent set, but not enough to review it:

- physical vs magical vs mixed damage axis divergence when move overlap is low
  enough that the variants do not share a visible core;
- explicit build-axis divergence, such as physical / magical / speed / bulk,
  when nature, individual values, move package, and source role wording align
  around that different axis;
- role divergence, such as cleaner vs defensive pivot;
- near-zero move overlap across source-level dossiers with enough moves to be
  meaningful;
- different team jobs or matchup responsibilities.

Represent this as:

```yaml
split_hypotheses:
  - hypothesis_id: split_01_02
    family_ids: [family_01, family_02]
    reason_codes:
      - damage_axis_divergence
      - configuration_axis_divergence
      - role_axis_divergence
      - no_move_overlap
    status: candidate_only_needs_more_flow_specific_evidence
    runtime_allowed: false
```

Important boundary: `split_hypothesis` blocks promotion, but it is not a final
product decision. It tells the next Agent to collect flow-specific evidence or
ask for PM review. It does not create runtime graph cards.

Damage category alone is not enough to split a set if the variants share a
visible core move or are only one optional slot apart. Keep those as alter
variants until role/build evidence says otherwise.

Likewise, a single nature, individual-value, bloodline, or ability difference is
not enough to split a set. These fields are evidence signals. A separate set
requires multiple aligned signals that imply a different battle job, such as an
output-oriented bundle versus a defensive/control bundle.

### L3 Tactical Context

Use for sparse tactical signals. This layer is useful, but it is not required
for a standard set skeleton and should not pollute L1/L2.

Fields:

```yaml
tactical_context:
  roles: []
  common_partners: []
  combo_notes: []
  matchup_claims: []
  counterplay_claims: []
```

## Source-Level Inventory Output

Each ingested source should produce one inventory file:

```text
artifacts/knowledge_ops/set_inventory/<source_id>.source_inventory.yaml
```

Schema:

```yaml
schema_version: p14.set_inventory.v0
source_id: ""
generated_at: "YYYY-MM-DD"
runtime_allowed: false
source:
  title: ""
  url: ""
  source_type: ""
  low_confidence_use: ""
coverage_records: []
set_dossiers: []
summary:
  coverage_record_count: 0
  set_dossier_count: 0
  complete_4_moves_count: 0
  move_pool_4plus_unclustered_count: 0
  partial_2_3_moves_count: 0
  single_move_signal_count: 0
```

## Cross-Source Consolidation Output

Consolidation is the emergence observer between source-level inventory and
reviewed Set Graph cards. It should not decide final truth or promote runtime
data. Its job is to show which set skeletons repeat as source volume grows.

Output path:

```text
artifacts/knowledge_ops/set_inventory_consolidation/<batch_id>.yaml
artifacts/knowledge_ops/review_packets/<batch_id>_pm_brief.md
artifacts/knowledge_ops/review_packets/<batch_id>_family_review.md
```

Schema:

```yaml
schema_version: p14.set_inventory_consolidation.v0
batch_id: ""
generated_at: "YYYY-MM-DD"
runtime_allowed: false
summary:
  inventory_source_count: 0
  species_count: 0
  split_blocked_count: 0
  review_candidate_count: 0
  family_review_candidate_count: 0
  emerging_count: 0
  needs_more_source_count: 0
  coverage_only_count: 0
species_records:
  - species_name: ""
    state: "emerging" # split_blocked | review_candidate | emerging | needs_more_source | coverage_only
    source_count: 0
    primary_source_count: 0
    supporting_source_count: 0
    coverage_source_count: 0
    stable_moves: []
    observed_moves:
      - move_name: ""
        source_count: 0
        primary_source_count: 0
        sources: []
    dossier_variants:
      - source_id: ""
        source_type: ""
        low_confidence_use: ""
        moves: []
        completeness: ""
        roles: []
        damage_axis: ""
        build_axes: []
        configuration: {}
    set_family_summary:
      family_count: 0
      split_hypothesis_count: 0
      decision: "same_family_or_insufficient_split_evidence"
      default_policy: "keep_skill_differences_as_alter_variants_until_role_or_build_axis_split_is_supported"
    set_family_candidates: []
    split_hypotheses: []
    family_review_candidates:
      - review_scope: set_family
        species_name: ""
        family_id: ""
        core_moves: []
        flex_moves: []
        primary_source_count: 0
        primary_source_ids: []
        promotion_boundary: "family_only_species_level_card_remains_blocked_if_split_hypotheses_exist"
        suggested_next_action: "build_family_level_reviewer_packet_before_any_promotion"
        runtime_allowed: false
    suggested_next_action: ""
    promotion_blockers: []
    runtime_allowed: false
```

Consolidation states:

- `split_blocked`: enough signal may exist inside one family, but the same
  species has unresolved set-family split hypotheses; species-level reviewer
  packet and species-level graph card are blocked, while any listed
  `family_review_candidates` may proceed as family-scoped review items;
- `review_candidate`: enough repeated legal move evidence to justify a reviewer
  packet, but still not runtime-ready;
- `emerging`: cross-source or strong single-source signal exists, but not enough
  to review as a stable set;
- `needs_more_source`: only weak or single-source move evidence exists;
- `coverage_only`: species appears but no reliable move skeleton exists.

## Autorun Dashboard Contract

Set Inventory and consolidation are still candidate substrate. The autorun
dashboard is the PM-facing control surface that decides whether the next batch
can continue automatically.

Output:

```text
artifacts/knowledge_ops/autorun/<batch_id>.yaml
artifacts/knowledge_ops/review_packets/<batch_id>_autorun_dashboard.md
```

Schema sketch:

```yaml
schema_version: p14.autorun_dashboard.v0
batch_id: ""
generated_at: "YYYY-MM-DD"
runtime_allowed: false
active_source_ids: []
source_health:
  active_source_count: 0
  blocked_source_count: 0
  repair_required_source_count: 0
  queued_source_count: 0
volume_batch_plan:
  batch_id: ""
  selected_source_count: 0
  selected_source_ids: []
  completed_selected_source_count: 0
  remaining_selected_source_count: 0
  remaining_selected_source_ids: []
consolidation_summary: {}
promotion_lane:
  pm_attention_required_count: 0
  family_review_candidates: []
  already_reviewed_candidates: []
blocker_lane:
  split_blocked_species: []
  transcript_blocked_sources: []
  missing_active_artifacts: []
  ignored_stale_inventory_count: 0
next_action:
  action: ""
  reason: ""
```

The dashboard is allowed to summarize candidate evidence, but it is not a
review packet by itself and never changes runtime data.

Default promotion remains forbidden. Consolidation may recommend targeted source
gap fill, reviewer packet construction, or quarantine, but it must not write
reviewed graph cards.

## Promotion Boundary

Inventory data may feed reviewed Set Graph cards only after consolidation and
review gates. It must never be injected into runtime directly.

Minimum future promotion gates:

- species resolves to A-layer species/form;
- promoted moves resolve to A-layer move names and are legal for that species;
- long/short overlapping term hits are de-duplicated before promotion;
- no unresolved ASR terms remain in promoted fields;
- source spans are present;
- cross-source repetition or explicit PM approval exists;
- alter variants have been kept within a reviewed set family, or
  split hypotheses have been resolved by flow-specific evidence / PM decision;
- family-level review candidates may be reviewed before species-level split
  hypotheses are fully resolved, but their promotion boundary must remain
  scoped to that set family and must not imply a species-wide standard set;
- family-level review decisions should be recorded in
  `data/knowledge_graph/v0/review_state/family_review_ledger.yaml` before any
  graph card materialization;
- strict graph validators pass after materialization.
