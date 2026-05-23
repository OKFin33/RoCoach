# P14 Dataset Planning Package Verification Runbook v0

Status: planning verification contract
Date: 2026-05-22
Scope: verification for DP-01 to DP-11 planning package
Runtime effect: none

This document is the DP-09 output for the dataset pipeline planning package.
It makes verification executable for planning-only work. It does not mutate
data or runtime state.

## 1. Verification Goal

Prove that the planning package produced contracts and a PM packet without
crossing into dataset production.

The check must prove:

- DP-01 through DP-11 contract files exist;
- PM review packet exists;
- README points to the planning package;
- no standalone `runtime_allowed: true` field was introduced in dataset docs;
- Gold manifest counts remain unchanged unless PM explicitly accepted Gold;
- graph/eval/artifact forbidden paths have no new tracked diff;
- forbidden paths have no new untracked files relative to the pre-goal
  baseline.

## 2. Expected Planning Outputs

```text
docs/specs/p14_dataset_card_template_v0.md
docs/specs/p14_dataset_snapshot_versioning_contract_v0.md
docs/specs/p14_dataset_provenance_schema_contract_v0.md
docs/specs/p14_gold_eval_regression_contract_v0.md
docs/specs/p14_dataset_quality_dashboard_contract_v0.md
docs/specs/p14_retrieval_kb_eval_contract_v0.md
docs/specs/p14_mechanism_rule_dataset_lane_v0.md
docs/specs/p14_dataset_review_independence_contract_v0.md
docs/specs/p14_dataset_plan_verification_runbook_v0.md
docs/specs/p14_acquisition_skill_integration_contract_v0.md
docs/specs/p14_verifier_llm_judge_eval_contract_v0.md
artifacts/knowledge_ops/review_packets/p14_dataset_pipeline_plan_v0_1_pm_review.md
```

## 3. Forbidden Writes

The planning package must not create or mutate:

```text
artifacts/knowledge_ops/source_probe/
artifacts/knowledge_ops/set_inventory/
data/knowledge_graph/v0/set_graph/
data/knowledge_graph/v0/eval/gold_items/
data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
data/knowledge_graph/v0/mechanism_rules/rule_registry.yaml
data/knowledge_graph/v0/review_state/
src/
apps/
```

The PM packet path under `artifacts/knowledge_ops/review_packets/` is allowed.
Because `artifacts/` is ignored by the repo-level `.gitignore`, the PM packet
must be verified by direct file existence, not by `git status`.

## 4. Pre-goal Baseline Rule

This repo may already contain untracked P14 data directories. Verification must
compare forbidden-path status to the baseline captured at the start of the
planning goal.

Observed baseline at this goal start:

```text
?? data/knowledge_graph/v0/eval/
?? data/knowledge_graph/v0/set_graph/
```

Those existing untracked directories are not new pollution by themselves. New
files inside forbidden paths after the baseline are failures.

## 5. Commands

Run from repo root:

```bash
for f in \
  docs/specs/p14_dataset_card_template_v0.md \
  docs/specs/p14_dataset_snapshot_versioning_contract_v0.md \
  docs/specs/p14_dataset_provenance_schema_contract_v0.md \
  docs/specs/p14_gold_eval_regression_contract_v0.md \
  docs/specs/p14_dataset_quality_dashboard_contract_v0.md \
  docs/specs/p14_retrieval_kb_eval_contract_v0.md \
  docs/specs/p14_mechanism_rule_dataset_lane_v0.md \
  docs/specs/p14_dataset_review_independence_contract_v0.md \
  docs/specs/p14_dataset_plan_verification_runbook_v0.md \
  docs/specs/p14_acquisition_skill_integration_contract_v0.md \
  docs/specs/p14_verifier_llm_judge_eval_contract_v0.md \
  artifacts/knowledge_ops/review_packets/p14_dataset_pipeline_plan_v0_1_pm_review.md; do
  test -f "$f" || { echo "missing $f"; exit 1; }
done

rg -n "^\\s*runtime_allowed:\\s*true\\b" docs/specs/p14_*.md
rg -n "p14_dataset_pipeline_plan_v0_1|p14_dataset_card_template_v0|p14_dataset_plan_verification_runbook_v0|p14_acquisition_skill_integration_contract_v0|p14_verifier_llm_judge_eval_contract_v0" docs/specs/README.md
sed -n '1,80p' data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
git diff --name-only -- data/knowledge_graph/v0/set_graph data/knowledge_graph/v0/eval artifacts/knowledge_ops/source_probe artifacts/knowledge_ops/set_inventory data/knowledge_graph/v0/mechanism_rules/rule_registry.yaml data/knowledge_graph/v0/review_state
git status --short -- data/knowledge_graph/v0/set_graph data/knowledge_graph/v0/eval artifacts/knowledge_ops/source_probe artifacts/knowledge_ops/set_inventory
```

Expected command behavior:

- the file-existence loop exits 0;
- the `runtime_allowed: true` search returns no matches;
- README search returns planning package rows;
- Gold manifest still reports zero accepted counts unless PM accepted Gold;
- `git diff --name-only` for forbidden paths returns empty;
- `git status --short` for forbidden paths returns only the pre-goal baseline
  entries, or no entries if those paths become tracked elsewhere.

## 6. Acceptance Criteria

The planning package passes when:

- all expected planning outputs exist;
- README references the package;
- no dataset doc introduces standalone `runtime_allowed: true`;
- Gold manifest remains `draft_no_pm_accepted_items` with zero accepted counts;
- no source ingest artifacts are added;
- no Set Graph, Gold item, mechanism registry, review ledger, runtime, API, or
  app file is changed by this goal;
- the only allowed artifact write is the PM packet;
- any pre-existing untracked forbidden paths are identified as baseline, not
  hidden.

## 7. Failure Handling

If a forbidden path changed:

1. stop;
2. report exact path;
3. do not fix by deleting or reverting user work unless explicitly asked;
4. explain whether the change predates the goal or was introduced by the goal;
5. continue only after the boundary is clear.

If Gold manifest counts changed without PM acceptance, the goal fails.

If runtime/API/app files changed, the goal fails because it crossed the
planning-only boundary.

## 8. Final Verification Note Template

```text
Verification summary:
- Planning outputs: pass/fail
- Runtime true scan: pass/fail
- README package refs: pass/fail
- Gold manifest unchanged: pass/fail
- Forbidden tracked diff: pass/fail
- Forbidden untracked delta vs baseline: pass/fail
- Remaining risk:
```
