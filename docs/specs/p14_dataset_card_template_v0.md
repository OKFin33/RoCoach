# P14 Dataset Card Template v0

Status: template contract
Date: 2026-05-22
Scope: Roco dataset card / datasheet template
Runtime effect: none

This document is the DP-01 output for the dataset pipeline planning package.
It defines the card every future release-style dataset snapshot must fill.
It does not create a real snapshot and does not authorize dataset production,
Gold acceptance, graph materialization, or runtime promotion.

## 1. Required Header

```yaml
dataset_card_schema: p14.dataset_card.v0
snapshot_id: roco_kg_dataset_v0.1-dev/YYYY-MM-DD
snapshot_status: planning | candidate | reviewed | runtime_candidate
created_at: ""
created_by_role: ""
runtime_allowed: false
distribution:
  state: internal_only
  raw_transcripts: internal_reference_only
```

Rules:

- `snapshot_id` must be a real snapshot id only when a snapshot manifest exists.
- `runtime_allowed: false` is the default and remains false unless a separate
  PM-approved runtime-promotion gate passes.
- raw subtitles and transcripts are not redistributable snapshot payloads by
  default.

## 2. Task Definition

Every card must state which PvP advisor tasks the snapshot is meant to improve.

Required fields:

```yaml
task_definition:
  product_goal: "support evidence-backed PvP advisor answers"
  supported_tasks:
    - set_existence
    - set_family_identity
    - mechanism_boundary
    - teammate_relation
    - counterplay_relation
    - configuration_intent
    - covered_uncovered_behavior
  explicit_non_goals:
    - full_roco_encyclopedia
    - official_database_replacement
    - unrestricted_public_dataset
```

Acceptance rule: a component that cannot name a supported task stays research
material, not dataset evidence.

## 3. Component Inventory

The card must describe all four Roco dataset products, even when one is empty.

```yaml
components:
  evidence_kb:
    included: true
    source_queue_ref: ""
    evidence_manifest_refs: []
    raw_preservation_policy: "url_platform_id_timestamp_span_repair_log"
  structured_kg:
    included: true
    root: data/knowledge_graph/v0
    set_family_refs: []
    mechanism_rule_refs: []
    review_state_refs: []
  gold_eval:
    included: true
    manifest_ref: data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
    regression_result_ref: ""
  llm_wiki:
    included: true
    readable_note_refs: []
    fact_promotion_policy: "requires source span and structured extraction"
```

Known empty components must be explicit:

```yaml
known_empty:
  gold_eval_reason: "no PM accepted items yet"
```

## 4. Source Composition

The card must summarize source mix without treating discovery metadata as
evidence.

```yaml
source_composition:
  by_source_type:
    official_a_layer: 0
    mechanism_tutorial: 0
    team_explainer: 0
    matchup_counterplay: 0
    high_ladder_gameplay: 0
    tier_ranking_overview: 0
    entertainment_or_rejected: 0
  by_processing_state:
    subtitle: 0
    bailian_asr: 0
    repaired: 0
    partial: 0
    unresolved: 0
  source_policy_notes: []
```

The source-composition section is descriptive. It does not promote facts.

## 5. Provenance Summary

The card must summarize whether field-level provenance is available.

```yaml
provenance_summary:
  field_provenance_required: true
  source_span_required_for_reviewed_claims: true
  transform_lineage_required: true
  reviewer_identity_required: true
  missing_or_migration_needed: []
```

Minimum rule:

- every reviewed or Gold/Eval structured field must either have
  `field_provenance` pointing to exact spans or an explicit
  `unresolved` / `not_applicable` reason.

## 6. Review Roles

The card must state the review roles used by the snapshot.

```yaml
review_roles:
  collector: ""
  ingest_normalizer: ""
  extractor: ""
  consolidator: ""
  reviewer: ""
  pm_decider: ""
independence:
  high_risk_self_review_allowed: false
  reviewer_identity_fields:
    - role
    - agent_id
    - run_or_context_id
```

## 7. Quality Metrics Placeholder

Cards must report metrics or mark them as `baseline_needed`.

```yaml
quality_metrics:
  entity_resolution_rate: baseline_needed
  move_legality_rate: baseline_needed
  unresolved_asr_rate: baseline_needed
  source_span_coverage: baseline_needed
  field_completeness: baseline_needed
  merge_split_regression: baseline_needed
  negative_case_protection: baseline_needed
  review_pass_rate: baseline_needed
  rag_retrieval_quality: baseline_needed
  answer_faithfulness: baseline_needed
  drift_staleness: baseline_needed
```

The card must not invent thresholds. If a metric has no baseline, it says so.

## 8. Rights and Distribution Boundary

Default policy:

```yaml
rights_distribution:
  state: internal_only
  source_urls_allowed_for_audit: true
  raw_transcripts_public: false
  derived_structured_claims_public: false
  public_dataset_claim_allowed: false
  pending_pm_decisions:
    - attribution_policy
    - redistribution_policy
    - public_snapshot_scope
```

Product consequence: v0.1 planning can continue internally without pretending
the result is already publishable.

## 9. Known Limitations

Required fields:

```yaml
known_limitations:
  coverage_gaps: []
  source_biases: []
  asr_or_canonicalization_risks: []
  mechanism_uncertainties: []
  gold_eval_gaps: []
  stale_or_meta_drift_risks: []
  runtime_exclusions: []
```

## 10. Maintenance and Drift

Required fields:

```yaml
maintenance:
  owner_role: ""
  update_triggers:
    - new_meta_source
    - mechanism_contradiction
    - extractor_version_change
    - schema_migration
    - gold_regression_failure
    - product_eval_regression
  supersession_policy: "new snapshots supersede by manifest, not by overwriting"
  drift_check_frequency: "before each runtime-facing promotion"
```

## 11. Future Snapshot Fill Requirements

Before a future snapshot can be considered release-style, it must fill:

- snapshot manifest reference and artifact hashes;
- actual source-composition counts;
- actual Gold/Eval manifest and regression result;
- actual quality metrics or explicit baseline-needed statuses;
- known exclusions and stale-source risks;
- review role/run identity;
- rights/distribution decision state.

Until those fields are filled, the card is a template or candidate card, not a
dataset release.
