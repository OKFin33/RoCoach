# P14 Gold/Eval Regression Contract v0

Status: planning contract
Date: 2026-05-22
Scope: executable Gold/Eval regression behavior
Runtime effect: none

This document is the DP-04 output for the dataset pipeline planning package.
It defines how future Gold/Eval regression should behave. It does not accept
pending Gold packets, create `gold_items`, change Gold manifest counts, or
promote runtime data.

## 1. Current Gold State

The current manifest is:

```text
data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
```

At planning time it is `draft_no_pm_accepted_items` and has zero accepted Gold
items. Therefore the regression runner contract can be defined now, but actual
pass/fail coverage remains `pending_seeded_gold` until PM accepts Gold items.

## 2. Gold Item Inputs

Accepted regression inputs:

```yaml
schema_version: p14.gold_item.v0
gold_id: ""
gold_type: gold_set_family | gold_split_case | gold_mechanism_boundary | gold_stateful_form_boundary | gold_negative_case
review_status: pm_accepted
input_fixture_refs: []
expected_output:
  allowed: []
  forbidden: []
regression_tasks:
  - extract
  - canonicalize
  - merge_split
  - mechanism_boundary
  - negative_guard
  - review_surface
runtime_allowed: false
```

Only `pm_accepted` items are pass/fail authorities. Draft and pending packet
items can be dry-run examples but must not count as Gold pass/fail.

## 3. Prediction Output Schema

Future pipeline runs must emit predictions in a comparable shape:

```yaml
schema_version: p14.gold_prediction.v0
run_id: ""
created_at: ""
pipeline_version: ""
gold_manifest_ref: ""
predictions:
  - gold_id: ""
    task: extract | canonicalize | merge_split | mechanism_boundary | negative_guard | review_surface
    observed_behavior: ""
    produced_refs: []
    evidence_refs: []
    unresolved: []
runtime_allowed: false
```

No live advisor runtime call is required for this planning contract.

## 4. Regression Result Schema

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
  not_applicable_count: 0
  blocked_for_promotion: true
runtime_allowed: false
```

## 5. Severity Rules

Critical:

- negative case produces forbidden accepted behavior;
- illegal species-move assignment enters promoted/reviewed output;
- mechanism boundary is reversed or generalized beyond evidence;
- Gold split/merge decision is violated in a way that would change user-facing
  set advice.

Major:

- source span missing for reviewed output;
- unresolved ASR appears in a field that should be resolved;
- review packet omits the alternative that Gold says matters;
- field-level provenance missing for a reviewed field.

Minor:

- wording drift without behavioral change;
- missing optional dashboard field;
- low-impact confidence mismatch.

## 6. Initial Pass Policy

Before a runtime-facing snapshot:

- any critical fail blocks promotion/materialization;
- any negative-case fail blocks promotion/materialization;
- any Gold item with missing source-span refs blocks reviewed snapshot claims;
- warnings can proceed only if the packet states the risk and next evidence
  needed;
- `pending_seeded_gold` means no dataset-quality pass claim is allowed.

Gold acceptance remains separate from runtime promotion.

## 7. Dashboard Integration

Regression results feed the quality dashboard:

```yaml
gold_eval_dashboard:
  manifest_ref: ""
  run_id: ""
  accepted_gold_count: 0
  runnable_gold_count: 0
  pass_rate: baseline_needed
  critical_fail_count: 0
  negative_case_fail_count: 0
  blocked_for_promotion: true
```

If accepted Gold count is zero, dashboard status is:

```yaml
status: pending_seeded_gold
```

## 8. Regression History Location

Future regression outputs should live under a dedicated eval-results location,
not mixed into source-ingest artifacts:

```text
artifacts/knowledge_ops/eval_results/gold_regression/
```

This planning package does not create that directory or any regression result.

## 9. First Gold v0 Sampling Priority

When production starts, seed Gold in this order:

1. common PvP usefulness;
2. current high-volume split blockers;
3. mechanism-sensitive cases;
4. real observed negative/error cases;
5. stateful-form boundaries.

Gold Set v0 should contain easy and hard cases. Easy cases catch obvious
regression; hard cases calibrate split/recluster and mechanism boundaries.

## 10. Example Regression Result

```yaml
schema_version: p14.gold_regression_result.v0
run_id: dry_contract_example
created_at: "2026-05-22T00:00:00+08:00"
gold_manifest_ref: data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
pipeline_version: planning_contract_only
items: []
summary:
  pass_count: 0
  fail_count: 0
  critical_fail_count: 0
  major_fail_count: 0
  warn_count: 0
  not_applicable_count: 0
  blocked_for_promotion: true
runtime_allowed: false
```
