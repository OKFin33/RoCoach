# P14 Dataset Quality Dashboard Contract v0

Status: planning contract
Date: 2026-05-22
Scope: dataset quality metrics and dashboard fields
Runtime effect: none

This document is the DP-05 output for the dataset pipeline planning package.
It defines what quality means before future volume work resumes. It does not
run batch ingest, modify prior dashboards, or change dataset artifacts.

## 1. Dashboard Purpose

The dashboard must prove the dataset is improving, not merely growing.

It answers:

- Are entities resolved correctly?
- Are move assignments legal?
- Are reviewed fields source-span backed?
- Are Gold/Eval cases preserved?
- Are review packets passing or creating review debt?
- Is retrieval grounded and faithful?
- Are LLM judge verdicts calibrated against Gold/PM review instead of trusted
  blindly?
- Are stale sources or mechanism drift accumulating?

## 2. Metric Schema

Each dashboard metric uses:

```yaml
metric:
  name: ""
  sample_unit: ""
  numerator: ""
  denominator: ""
  value: baseline_needed
  threshold: baseline_needed
  status: pass | warn | fail | baseline_needed
  evidence_refs: []
  notes: ""
```

Do not invent thresholds. If the pipeline has no baseline, use
`baseline_needed`.

## 3. Required Metrics

| Metric | Sample unit | Initial gate |
|---|---|---|
| entity_resolution_rate | promoted/reviewed entity fields | 100% resolved or explicitly unresolved outside promoted fields |
| move_legality_rate | promoted/reviewed move assignments | 100% legal or excluded with reason |
| unresolved_asr_rate | promoted/reviewed fields | 0 unresolved ASR in promoted fields |
| source_span_coverage | Gold/reviewed claims | 100% have source span refs |
| field_completeness | set family candidates | report by field; no universal pass gate yet |
| field_provenance_coverage | reviewed structured fields | 100% have field provenance or explicit reason |
| merge_split_regression | Gold split/family cases | 100% no critical Gold violation |
| negative_case_protection | Gold negative cases | 100% forbidden behavior absent |
| review_pass_defer_reject_rate | review packets | reported per packet |
| rag_context_precision | Evidence KB eval questions | baseline_needed |
| rag_context_recall | Evidence KB eval questions | baseline_needed |
| answer_faithfulness | covered questions | no answer may contradict retrieved spans |
| llm_judge_pm_agreement_rate | judged PM-reviewed items | baseline_needed until reviewed comparison exists |
| llm_judge_gold_agreement_rate | judged Gold/Eval items | baseline_needed until accepted Gold exists |
| llm_judge_conflict_rate | judged candidates | report disagreements with deterministic/reviewer layers |
| human_escalation_rate | judged candidates | report share escalated to PM/human review |
| drift_staleness | source/meta snapshot | reported when source date or mechanism version matters |

## 4. Error Taxonomy

Minimum categories:

- ASR entity hallucination;
- canonicalization overreach;
- illegal species-move assignment;
- mechanism name confusion;
- exception promoted to general rule;
- source metadata treated as evidence;
- overmerge;
- oversplit;
- stale source / meta drift;
- missing field provenance;
- review packet incomprehensible to PM;
- same-context self-review on high-risk item.

Every repeated error should produce one of:

- error ledger entry;
- Gold negative candidate;
- source reliability update;
- annotation guideline update;
- verifier rule.

## 5. Dashboard Fields

```yaml
schema_version: p14.dataset_quality_dashboard.v0
dashboard_id: ""
created_at: ""
snapshot_ref: ""
pipeline_version: ""
runtime_allowed: false
summary:
  status: pass | warn | fail | baseline_needed
  blocked_for_promotion: true
  accepted_gold_count: 0
  reviewed_kg_item_count: 0
  candidate_kg_item_count: 0
metrics:
  entity_resolution_rate: {}
  move_legality_rate: {}
  unresolved_asr_rate: {}
  source_span_coverage: {}
  field_completeness: {}
  field_provenance_coverage: {}
  merge_split_regression: {}
  negative_case_protection: {}
  review_pass_defer_reject_rate: {}
  rag_context_precision: {}
  rag_context_recall: {}
  answer_faithfulness: {}
  llm_judge_pm_agreement_rate: {}
  llm_judge_gold_agreement_rate: {}
  llm_judge_conflict_rate: {}
  human_escalation_rate: {}
  drift_staleness: {}
error_distribution: {}
stop_reasons: []
open_risks: []
```

## 6. Stop Thresholds

Production or promotion tasks must stop when:

- promoted fields contain unresolved ASR;
- promoted move assignments fail A-layer legality;
- reviewed claims lack source spans;
- Gold negative cases fail;
- critical Gold regression fails;
- high-impact mechanism contradiction is open;
- LLM judge passes unsupported claims or conflicts with Gold on critical cases;
- PM packet exceeds review budget and no batch policy exists;
- same-context self-review is detected on high-risk items.

Planning-only tasks may record these conditions but must not attempt to fix
them by editing data.

## 7. Handoff Field List

Future dashboard-producing goals must fill:

- snapshot ref;
- pipeline version;
- metric denominators;
- metric values or `baseline_needed`;
- blocked-for-promotion boolean;
- source refs for each metric;
- judge model/prompt version for LLM judge metrics;
- error distribution;
- stop reasons;
- open risks.

If a metric cannot be computed, record why and what instrumentation is missing.
