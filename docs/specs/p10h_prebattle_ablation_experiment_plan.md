# P10h Prebattle Ablation Experiment Plan

Status: blocked pending full-roster answer-key repair

Canonical artifact:

- `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md`

Living experiment log:

- `artifacts/p10h_prebattle_ablation_experiment_log.md`

Purpose:

- Test A/B/D knowledge-layer contribution for Roco prebattle preview reasoning.
- Produce a D-layer repair map from primitive-level failed checks, so the
  experiment tells us what to add/change in D1/D2/D3/retrieval/prompt after
  scoring.
- Use DeepSeek v4 Pro with thinking enabled.
- Keep D-layer exact-match upper bound separate from D-layer transfer value.

Current state warning (2026-05-03):

- The active P10h inputs were corrected from partial/source-derived rosters to
  full 6v6 visible-team rosters.
- `artifacts/p10h_prebattle_ablation/inputs/*.yaml` are current, but their
  answer keys intentionally contain `roster_revision_warning: TODO`.
- Existing prompts, grounding packs, outputs, blind packets, and analysis
  reports in `artifacts/p10h_prebattle_ablation/` are historical partial-roster
  artifacts unless rebuilt after answer-key repair.
- `artifacts/p10h_prebattle_ablation_r1_transfer_rule/` is also historical and
  uses old partial-roster inputs.
- Do not run live generation or cite old aggregate deltas as full-roster
  results until the answer keys/checklists are re-audited.
- Model-visible prompts must not include `case_id` or `source_ref`; these are
  internal identifiers only.
- PM decision: ambiguous species forms use base / first form by default, and
  `星光狮` is pinned to `星光能量的样子` (`species_ca356f37a9548d10`).
- The old `落陨星兔` what-if for the thunder WingKing case is an orphaned
  fragment from another scenario, not an active full-roster scoring anchor.
- The `贝古斯` 4-energy / 防御-倾泻互斥 what-if belongs to the
  `wingking_poison_0429` 寒音蛇平衡队 case.
- Never use bare `1/2/3` to refer to cases. Use the stable label or `case_id`:
  `Case A = prebattle_wingking_poison_vs_snake_balance`,
  `Case B = prebattle_poison_vs_starfall`,
  `Case C = prebattle_thunder_wingking_fast_balance`.

Audit:

- `artifacts/p10h_prebattle_ablation/STALENESS_AUDIT_2026_05_03.md`

Updates from Clé review (2026-05-02):

- L4 is not part of the first-pass main experiment because D-layer runtime
  retrieval does not exist yet.
- `L4-retrieval-only` and `L4-e2e` are future separate measurements.
- `L3-exact` measures same-source upper bound and may include answer leakage.
- `L3-transfer` is the primary D-layer ROI condition.
- Every case must have an answer key before generation starts.
- Do not store hidden chain-of-thought or provider reasoning traces.
- Final answers must not mention internal experiment/software metadata such as
  grounding, A/B/D-layer labels, B+, L0-L3, retrieval, model, prompt, source, or
  source material.
- LLM Judge Protocol added (Section 10): Claude Opus as judge, PM calibrates
  2 outputs and spot-checks 8-12 boundary outputs. Codex executes the judge.
  PM does not score 45 outputs manually.
- Judge output must include primitive-level `failed_checks` and a completed
  `primitive_failure_log_completed.csv`; this is the repair map for improving
  D1/D2/D3 after the ablation, not just a scoring artifact.
- Answer keys redesigned as D1/D2/D3 judgement structure:
  archetype_recognition → attention order → activated priors → reasoning chain
  → conditional knowledge → diagnostic checklist with D-layer primitive IDs.
- What-if sub-questions added per case (1-2 per case, scored separately).
- Real-time in-battle judgement stripped from answer keys; preview-inappropriate
  items moved to `conditional_knowledge` or removed.
- Terminology corrections applied (地阅力→地系愿力冲击, 开元力→开愿力).
- Case C second what-if tests information-honesty rather than analysis of
  under-documented matchups.

First-pass levels:

- L0: bare task.
- L1: L0 + A-layer facts.
- L2: L1 + B-layer snippets.
- L3-exact: L2 + same-source D/context pinned by
  `artifacts/p10h_prebattle_ablation/d_layer_selection_manifest.yaml`.
- L3-transfer: L2 + related non-identical D/context pinned by the same
  manifest.

First-pass scale:

- 3 cases.
- 5 levels.
- N=3.
- 45 calls + what-if sub-questions per call.
- PM scores: 2 calibration + 8-12 spot-check. Judge scores all 45.

Boundary:

- Offline experiment only.
- Controlled L0-L3 experiment does not require runtime code changes.
- App-path/L4 checks use `tools/p10h_experiment_harness.py` and are not a
  substitute for the clean L0-L3 ablation.
- No gold promotion.
