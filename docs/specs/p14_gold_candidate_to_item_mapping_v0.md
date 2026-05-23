# P14 Gold Candidate to Gold Item Mapping v0

Status: active mapping contract
Date: 2026-05-23
Scope: candidate Gold packets to accepted `p14.gold_item.v0`
Runtime effect: none

This document closes the audit gap between `p14.gold_candidate_packet.v0` and
accepted `p14.gold_item.v0`. It does not accept any Gold item.

## 1. Boundary

Gold candidates are review inputs. Accepted Gold items are regression fixtures.
Moving from candidate to item requires an explicit PM decision and a mapping
record. Candidate existence never implies acceptance.

## 2. Required Inputs

An accepted Gold item may be created only from:

- a candidate packet path;
- a PM review packet decision;
- source/review refs with enough provenance for the expected behavior;
- a mapping record using this contract.

## 3. Field Mapping

| Candidate field | Gold item field | Rule |
|---|---|---|
| `candidate_gold_id` | `gold_id` | Preserve id unless PM requests rename; record supersession if changed. |
| `gold_type` | `gold_type` | Must be one of the accepted Gold item types. |
| `recommended_action` | not copied | Becomes audit context only; PM decision controls acceptance. |
| `review_status_before_gold` | `review_status` history | Accepted item uses `pm_accepted`; prior state stays in `source_context`. |
| `source_review_id` / `source_review_packet` | `input_fixture_refs[]` and `review.pm_decision_packet` | Preserve both candidate and review packet refs. |
| `decision_label` | `decision.label` | PM may edit label before acceptance. |
| `set_intent`, `branch_boundary`, `mechanism_boundary`, `expected_behavior` | `decision.expected_behavior` and `expected_output` | Convert to concrete allowed/forbidden behaviors. |
| `signal_bundle` | `field_provenance` inputs | Signals are not expected outputs until mapped to exact evidence refs. |
| `why_useful_for_eval` | `regression_tasks[]` | Convert to executable task names. |
| `known_risks` | `quality.notes` / `open_risks` | Risks do not block acceptance if PM accepts with scope. |
| `runtime_allowed` | `runtime_allowed` | Remains false. |

## 4. Output Schema

```yaml
schema_version: p14.gold_item.v0
gold_id: ""
gold_type: ""
meta_snapshot: "2026-s1"
review_status: pm_accepted
source_context:
  candidate_packet_ref: ""
  candidate_gold_id: ""
  source_review_refs: []
decision:
  label: ""
  expected_behavior: ""
input_fixture_refs: []
expected_output:
  allowed: []
  forbidden: []
field_provenance:
  decision_label: []
  expected_behavior: []
  forbidden_behavior: []
review:
  pm_decision_packet: ""
  pm_decider: ""
  reviewer_role: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
quality:
  confidence: high | medium | low
  reviewer_agreement: single_pm | double_reviewed | disputed | superseded
  known_risks: []
regression_tasks: []
runtime_allowed: false
```

## 5. Negative Candidate Mapping

Negative candidates must preserve:

- false pattern;
- corrected boundary;
- expected forbidden behavior;
- exact source/error ledger refs;
- whether the negative case is local to a source or global to a mechanism.

They must not become canonical facts outside their scope. For example, an
illegal assignment of `极限撕裂` to one species is not a global rejection of
the move.

## 6. Acceptance Checklist

- PM decision exists and is cited;
- accepted item has allowed and forbidden behavior;
- field provenance points to source spans, ledgers, or review packets;
- candidate risks are preserved;
- Gold manifest count changes only after the accepted item file exists;
- runtime remains false.
