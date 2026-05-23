# P14 Mechanism Rule Dataset Lane v0

Status: planning contract
Date: 2026-05-22
Scope: mechanism rule dataset lifecycle, contradictions, and affected assets
Runtime effect: none

This document is the DP-07 output for the dataset pipeline planning package.
It defines how future mechanism-rule candidates should move from mention to
reviewed rule. It does not finalize mechanism rules, modify the rule registry,
change affected asset indexes, or promote runtime data.

## 1. Purpose

Set Graph can store which sets and relations exist. It must not become the
source of mechanism truth.

Mechanism rules govern:

- marks;
- weather;
- energy cost changes;
- bloodline/typed skill behavior;
- ability-triggered exceptions;
- resource loops;
- source contradictions and uncertainty wording.

Every mechanism-dependent edge or set claim must reference a reviewed
mechanism rule before runtime-facing promotion.

## 2. Lifecycle States

```yaml
mechanism_state:
  M0: mechanism_mention
  M1: mechanism_claim_atom
  M2: candidate_rule
  M3: agent_checked_rule
  M4: pm_reviewed_rule
  M5: runtime_rule
```

State rules:

- Agents may move claims through M3.
- PM decision, or explicit PM-approved batch policy, is required for M4.
- M5 requires separate validators and promotion audit.
- This planning package creates no M4 or M5 data.

## 3. Mechanism Claim Schema

```yaml
schema_version: p14.mechanism_claim.v0
claim_id: ""
state: M1
mechanism_key: ""
surface_forms: []
source_id: ""
source_span_ids: []
claim_text: ""
claim_quality: explicit | implied | shorthand | unclear
canonicalization:
  canonical_name: ""
  aliases: []
  unresolved_terms: []
field_provenance:
  mechanism_name: []
  trigger_condition: []
  effect: []
  scope: []
runtime_allowed: false
```

## 4. Candidate Rule Schema

```yaml
schema_version: p14.mechanism_rule_candidate.v0
rule_id: "mechanism/.../2026-s1"
state: M2
title: ""
meta_snapshot: "2026-s1"
mechanism_type: mark | weather | energy | status | bloodline | ability | other
scope:
  applies_to: []
  does_not_apply_to: []
normalized_rule: ""
source_claims:
  - claim_id: ""
    source_id: ""
    source_span_ids: []
    claim_quality: explicit
contradictions: []
affected_assets:
  species_set_ids: []
  edge_ids: []
  gold_ids: []
review:
  status: candidate
  extractor_agent_id: ""
  extractor_run_id: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
runtime:
  runtime_allowed: false
  uncertainty_policy: do_not_inject
```

## 5. Contradiction Taxonomy

Minimum contradiction categories:

- `surface_name_conflict`: ASR or alias may refer to another mechanism.
- `scope_conflict`: sources disagree on affected species, team, or target.
- `trigger_conflict`: sources disagree on when the mechanism activates.
- `effect_conflict`: sources disagree on the result or magnitude.
- `attribute_resolution_conflict`: typed skill or bloodline attribute is
  ambiguous.
- `exception_vs_general_rule`: one source gives a special case that may not be
  general.
- `stale_patch_or_meta`: older source may no longer describe current behavior.

Contradictions cannot be normalized away. They must be logged and either
resolved, deferred, or escalated.

## 6. High-Impact Review Threshold

A mechanism rule is high impact if it can change:

- energy/resource advice;
- move legality or skill identity;
- teammate/combo relation;
- counterplay relation;
- set-family split/merge;
- runtime answer confidence.

High-impact or contradicted rules require reviewer + PM review before M4.

## 7. Affected Asset Recheck

When a mechanism rule changes, future production lanes must recheck:

```yaml
affected_asset_recheck:
  rule_id: ""
  affected_species_sets: []
  affected_edges: []
  affected_gold_items: []
  required_checks:
    - field_provenance
    - source_span_coverage
    - gold_regression
    - quality_dashboard_update
```

This planning package does not update `affected_asset_index.yaml`.

## 8. Regression Checks

Mechanism-regression tasks:

- canonical mechanism name remains stable;
- typed surfaces resolve correctly or stay unresolved;
- exception is not promoted to general rule;
- mechanism-dependent edges cite reviewed rule refs;
- Gold mechanism boundaries are preserved;
- stale or contradicted rules block runtime-facing promotion.

## 9. Version and Drift Policy

```yaml
mechanism_versioning:
  meta_snapshot: "2026-s1"
  rule_version: 0
  supersedes: []
  superseded_by: null
  drift_triggers:
    - new_mechanism_tutorial
    - source_contradiction
    - product_eval_failure
    - gold_regression_failure
```

Rules:

- a changed mechanism rule gets a new version or supersession entry;
- affected assets are rechecked before reuse;
- runtime rules cannot silently change under the same id.

## 10. Contradiction Entry Template

```yaml
schema_version: p14.mechanism_contradiction.v0
contradiction_id: ""
mechanism_key: ""
category: scope_conflict
claims:
  - claim_id: ""
    source_id: ""
    source_span_ids: []
    claim_summary: ""
status: open | resolved | rejected | superseded
impact:
  affected_assets: []
  blocks_runtime_promotion: true
review:
  reviewer_agent_id: ""
  reviewer_run_id: ""
  pm_packet: ""
resolution: ""
runtime_allowed: false
```
