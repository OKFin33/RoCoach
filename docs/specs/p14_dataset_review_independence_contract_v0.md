# P14 Dataset Review Independence and PM Packet Contract v0

Status: planning contract
Date: 2026-05-22
Scope: reviewer independence, PM packet shape, and decision vocabulary
Runtime effect: none

This document is the DP-08 output for the dataset pipeline planning package.
It defines how review is separated from extraction and how PM review remains
readable. It does not accept data, change review ledgers, or change Gold
manifest counts.

## 1. Role Table

| Role | May do | Must not do |
|---|---|---|
| Collector | source discovery and queue metadata | claim facts from metadata |
| Ingest/Normalizer | subtitle/ASR repair and canonicalization candidates | promote unresolved terms |
| Extractor | claim atoms, inventory, and candidate extraction | review its own high-risk outputs |
| Consolidator | merge/split proposals and family clustering | finalize high-risk splits |
| Reviewer | audit candidates, run validators, build packets | silently accept disputed/high-risk items |
| PM | decide high-impact product/domain gates | review raw YAML/code as the primary surface |

## 2. Independence Rule

High-risk review requires more than a different label. Review artifacts must
record:

```yaml
review_identity:
  extractor:
    role: ""
    agent_id: ""
    run_or_context_id: ""
  reviewer:
    role: ""
    agent_id: ""
    run_or_context_id: ""
  pm:
    packet_id: ""
    decision_id: ""
```

Rules:

- same-context self-review is allowed only for low-risk candidate hygiene;
- Gold acceptance, mechanism boundaries, runtime promotion, and reviewed-ledger
  changes require independent review or PM decision;
- if independence cannot be proven, status is `review_independence_unproven`;
- unproven independence blocks runtime-facing claims.

## 3. Disagreement Log

```yaml
schema_version: p14.review_disagreement.v0
disagreement_id: ""
item_ref: ""
issue_type: split_merge | mechanism | source_quality | canonicalization | rights | other
positions:
  - role: extractor
    agent_id: ""
    run_or_context_id: ""
    summary: ""
  - role: reviewer
    agent_id: ""
    run_or_context_id: ""
    summary: ""
status: open | resolved | deferred | escalated_to_pm
pm_packet: ""
resolution: ""
runtime_allowed: false
```

Disagreements are not failures. Silent disagreement collapse is the failure.

## 4. PM Action Vocabulary

Allowed PM actions:

- `accept_plan_contract`: accept a planning contract as the next operating
  constraint.
- `request_revision`: require specific changes before the contract is usable.
- `defer_decision`: leave an item out of the active gate.
- `accept_gold_item`: accept a Gold/Eval item. Not allowed in this planning
  package unless explicitly requested.
- `reject_candidate`: reject a candidate or failure pattern.
- `authorize_production_goal`: authorize a later goal to produce data inside
  stated boundaries.
- `authorize_runtime_promotion`: not allowed in this planning package.

PM packets must state which actions are in scope.

## 5. Packet Size Budget

PM packet target:

- 3-6 required decisions;
- 8-12 low-risk candidates if included;
- 5-10 auto defer/reject rows if included;
- one screen of impact summary;
- no raw YAML/code required for review.

If a packet exceeds 6 required decisions, split it or defer lower-priority
items. A too-large packet is a system failure, not a PM failure.

## 6. High-Risk Escalation Criteria

Escalate to PM when an item affects:

- Gold acceptance;
- mechanism boundary;
- rights/distribution policy;
- runtime promotion;
- set-family split with product impact;
- contradiction resolution that changes existing reviewed knowledge;
- source policy that could admit low-quality or noisy material at scale.

## 7. PM Packet Format

```markdown
# PM Review Packet

Status:
Runtime effect:

## Why This Matters

## Decisions Requested

| ID | Decision | Recommendation | Product consequence |
|---|---|---|---|

## Not In Scope

## Evidence Reviewed

## If Accepted

## If Rejected

## Follow-up Work
```

## 8. Handoff Artifact

The planning package PM packet is:

```text
artifacts/knowledge_ops/review_packets/p14_dataset_pipeline_plan_v0_1_pm_review.md
```

That packet may ask the PM to accept the planning package as a planning gate.
It must not ask the PM to accept Gold items or runtime data.
