# P14 Verifier and LLM-as-Judge Eval Contract v0

Status: planning contract
Date: 2026-05-22
Scope: verifier cascade and LLM-as-judge evaluation boundary
Runtime effect: none

This document is the DP-11 output for the dataset pipeline planning package.
It defines how automated verifiers and LLM judges should evaluate future Roco
dataset outputs. It does not generate eval data, accept Gold items, run live
eval, modify runtime, or promote dataset material.

## 1. Boundary

LLM-as-judge is an evaluator, not a source of Roco truth.

It may judge whether a candidate, answer, or review packet follows the supplied
evidence and rubric. It must not invent game mechanics, create canonical facts,
settle unsupported domain disputes, or override A-layer legality and PM/domain
decisions.

Human review stays last for high-impact or unclear decisions. The point is to
reduce the amount of raw material the PM sees, not to remove PM judgment.

## 2. Verifier Cascade

Future dataset-producing goals should use the cheapest reliable verifier first:

```text
candidate/output
-> deterministic schema validation
-> A-layer legality and canonical entity checks
-> provenance/source-span completeness checks
-> rule/error-ledger checks
-> retrieval/faithfulness metrics
-> LLM judge rubric
-> independent reviewer Agent
-> PM review for high-impact or unresolved decisions
```

Hard failures at earlier layers block later confidence. An LLM judge cannot
turn an illegal species-move assignment or missing source span into a pass.

## 3. LLM Judge Task Classes

Allowed judge tasks:

- evidence faithfulness: whether candidate claims are supported by cited spans;
- extraction completeness: whether major supported claims were missed;
- canonicalization sanity: whether a proposed term repair is plausible given
  A/B candidates and local context;
- merge/split reasoning quality: whether the rationale uses tactical intent
  signals rather than field equality alone;
- retrieval answer support: whether an answer's claims map to retrieved spans;
- uncovered-question behavior: whether the answer admits missing evidence;
- review packet readability: whether the packet is small and PM-decisionable.

Forbidden judge tasks:

- declaring a new game fact without supplied evidence;
- accepting Gold items;
- finalizing mechanism boundaries;
- promoting KG/runtime data;
- deciding whether a disputed community claim is true when evidence conflicts.

## 4. Judge Input Packet

The judge must receive bounded, evidence-linked inputs:

```yaml
schema_version: p14.llm_judge_input.v0
judge_task: evidence_faithfulness | extraction_completeness | canonicalization_sanity | merge_split_reasoning | retrieval_answer_support | review_packet_readability
candidate_ref: ""
pipeline_run_ref: ""
gold_ref: ""
prompt_scope:
  allowed_evidence_refs: []
  allowed_a_layer_refs: []
  allowed_rule_refs: []
  hidden_fields:
    - pm_decision
    - desired_label
candidate_payload: {}
rubric_ref: ""
runtime_allowed: false
```

The judge sees enough context to evaluate the candidate but not the desired PM
label. This prevents the judge from simply echoing an answer key.

## 5. Judge Output Schema

```yaml
schema_version: p14.llm_judge_output.v0
judge_run_id: ""
judge_model: ""
judge_task: ""
candidate_ref: ""
verdict: pass | warn | fail | escalate
severity: critical | major | minor | informational
scores:
  evidence_faithfulness: 0
  a_layer_consistency: 0
  uncertainty_handling: 0
  tactical_intent_reasoning: 0
  packet_readability: 0
findings:
  - finding_id: ""
    issue_type: unsupported_claim | contradicted_evidence | missing_evidence | illegal_entity | overmerge | oversplit | unclear_packet | other
    evidence_refs: []
    explanation: ""
    required_action: reject | defer | repair | ask_pm | add_gold_negative | no_action
confidence: high | medium | low
human_escalation_required: false
runtime_allowed: false
```

Score scale:

- `0`: not applicable or cannot judge from supplied evidence;
- `1`: clear fail;
- `2`: partial / warning;
- `3`: pass.

## 6. Calibration Against Gold

LLM judges are useful only if calibrated.

Future eval should track:

| Metric | Purpose |
|---|---|
| `judge_pm_agreement_rate` | whether judge verdicts match PM decisions on reviewed packets |
| `judge_gold_agreement_rate` | whether judge verdicts preserve accepted Gold/Eval behavior |
| `judge_false_pass_rate` | cases where judge passes an item later rejected by PM/Gold |
| `judge_false_fail_rate` | cases where judge rejects an item later accepted |
| `judge_conflict_rate` | disagreement between judge, deterministic verifier, and reviewer Agent |
| `human_escalation_rate` | share of items correctly pushed to PM/human review |

Before accepted Gold exists, these metrics are `baseline_needed`; do not invent
thresholds.

## 7. Anti-bias and Leakage Rules

LLM judge prompts must:

- hide PM labels and expected verdicts unless running a calibration explanation
  task after the fact;
- distinguish source text from candidate text;
- include instructions that unsupported claims fail even if plausible;
- require evidence refs for every finding;
- forbid use of model memory as Roco domain evidence;
- record model, prompt version, and input refs.

The judge output is audit material. It is not itself provenance for a KG fact.

## 8. Human Review Placement

Human/PM review should receive only high-signal material:

- critical verifier failures;
- LLM judge `escalate` verdicts;
- judge/reviewer disagreements;
- Gold-regression violations;
- high-impact mechanism or set-family decisions;
- packet-readability failures that block PM judgment.

Low-risk pass/warn items can be summarized in dashboard form, but acceptance
still follows the review policy for that item type.

## 9. Dashboard Integration

The quality dashboard should add:

```yaml
llm_judge:
  judge_pm_agreement_rate: baseline_needed
  judge_gold_agreement_rate: baseline_needed
  judge_false_pass_rate: baseline_needed
  judge_false_fail_rate: baseline_needed
  judge_conflict_rate: baseline_needed
  human_escalation_rate: baseline_needed
  latest_prompt_version: ""
  latest_model: ""
```

A high judge score cannot unblock promotion if deterministic gates fail.

## 10. Stop Conditions

Production or promotion tasks must stop when:

- LLM judge passes unsupported claims that deterministic checks can identify;
- judge prompts include desired labels for non-calibration runs;
- judge output lacks evidence refs for findings;
- judge verdict conflicts with Gold on a critical case;
- PM is asked to review raw judge logs instead of a decision packet;
- the pipeline treats judge output as primary Roco evidence.

## 11. Handoff

Future implementation should add this as a separate eval lane after Gold/Eval
seed exists. The first useful run is not "judge everything"; it is a small
calibration batch where the judge grades already packeted decisions and the PM
agreement/error profile becomes visible.
