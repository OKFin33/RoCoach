# P14 Retrieval KB Eval Contract v0

Status: planning contract
Date: 2026-05-22
Scope: Evidence KB retrieval and answer-support evaluation
Runtime effect: none

This document is the DP-06 output for the dataset pipeline planning package.
It defines how future Evidence KB retrieval should be evaluated. It does not
change advisor runtime, run live answer smoke tests, generate eval data, or
materialize graph assets.

## 1. Boundary

Evidence KB eval is not Set Graph validation.

Evidence KB eval checks whether the system can retrieve useful, source-backed
context for PvP questions and degrade honestly when a question is uncovered.
Set Graph validation checks structured KG legality, review state, and indexes.

Both are required before runtime claims, but they are measured separately.

## 2. Question Classes

Future eval samples must label the question class:

```yaml
question_class:
  coverage: covered | partially_covered | uncovered
  task:
    - set_existence
    - set_family_identity
    - mechanism_boundary
    - teammate_relation
    - counterplay_relation
    - configuration_intent
    - source_traceback
  risk: low | medium | high
```

Covered questions require evidence refs. Uncovered questions require a known
uncovered reason, not fabricated evidence.

## 3. Eval Sample Schema

```yaml
schema_version: p14.retrieval_kb_eval_sample.v0
eval_id: ""
question: ""
question_class:
  coverage: covered
  task: []
  risk: medium
expected:
  relevant_evidence_refs: []
  acceptable_answer_facts: []
  forbidden_answer_facts: []
  expected_degradation: ""
source_policy:
  allowed_source_types: []
  stale_source_handling: ""
runtime_allowed: false
```

This contract defines the sample shape only. It does not create samples.

## 4. Retrieval Metrics

Required metrics:

```yaml
retrieval_metrics:
  context_precision:
    status: baseline_needed
    definition: "share of retrieved contexts that support the question"
  context_recall:
    status: baseline_needed
    definition: "share of expected evidence refs retrieved"
  noise_sensitivity:
    status: baseline_needed
    definition: "whether irrelevant contexts change the answer"
  source_traceability:
    status: baseline_needed
    definition: "whether answerable claims point to source spans"
```

No pass threshold is claimed before baseline.

## 5. Faithfulness and Groundedness

Answer-support eval must record:

```yaml
answer_support:
  retrieved_context_refs: []
  answer_claims:
    - claim_text: ""
      supported_by: []
      status: supported | unsupported | contradicted | not_applicable
  faithfulness_result: pass | warn | fail | baseline_needed
```

Hard rule:

- a covered answer may be incomplete, but it must not contradict retrieved
  source spans;
- an uncovered answer must say uncertainty rather than inventing Set Graph or
  mechanism facts.

## 6. Stale-Source Rejection

Each eval sample may define stale-source behavior:

```yaml
stale_source_policy:
  meta_snapshot: "2026-s1"
  stale_if_before: ""
  stale_if_superseded_by: []
  expected_behavior: "cite with caveat | reject | use only as historical"
```

If source date or mechanism version matters, dashboard status should report
drift/staleness instead of hiding it.

## 7. Degradation Behavior

For uncovered or partially covered questions, expected behavior must be
explicit:

```yaml
expected_degradation:
  answer_style: "state missing evidence and narrow what is known"
  must_not:
    - expose_internal_labels
    - promote_candidate_graph_data
    - invent_source_support
```

This connects Evidence KB eval to the product requirement: covered questions
should improve, uncovered questions should degrade honestly.

## 8. Instrumentation Requirement

If current retrieval runtime does not expose enough trace to compute these
metrics, the output is an instrumentation requirement, not a runtime patch:

```yaml
instrumentation_needed:
  - retrieved_context_ids
  - source_span_ids
  - answer_claim_to_context_map
  - stale_source_flags
```

This planning package does not modify runtime instrumentation.

## 9. LLM Judge Boundary

Retrieval KB eval may later use LLM-as-judge for faithfulness, relevance, and
degradation-quality scoring, but only under
`p14_verifier_llm_judge_eval_contract_v0.md`.

Allowed:

- judge whether answer claims are supported by retrieved source spans;
- judge whether irrelevant contexts changed the answer;
- judge whether uncovered answers degrade honestly;
- flag unsupported or contradicted claims for reviewer/PM escalation.

Forbidden:

- use judge output as source evidence;
- let judge memory supply missing Roco facts;
- let a judge pass override missing source spans or A-layer legality failures.

Judge metrics are dashboard inputs, not runtime authorization.

## 10. Handoff Eval Sample Example

```yaml
schema_version: p14.retrieval_kb_eval_sample.v0
eval_id: example_only
question: "A common set question that must be grounded by Evidence KB."
question_class:
  coverage: covered
  task: [set_family_identity]
  risk: medium
expected:
  relevant_evidence_refs: []
  acceptable_answer_facts: []
  forbidden_answer_facts: []
  expected_degradation: ""
source_policy:
  allowed_source_types: [team_explainer, mechanism_tutorial]
  stale_source_handling: "report_if_stale"
runtime_allowed: false
```
