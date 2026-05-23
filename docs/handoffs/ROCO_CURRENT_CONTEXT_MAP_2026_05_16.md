# Roco Current Context Map - 2026-05-16

Status: current entrypoint.

This file supersedes older handoff files when they conflict on release scope,
read order, or whether Meta Graph / D-layer belong to V1.

## 1. Current Product Decision

V1 formal release is no longer just "client + API + A/B/C grounded chat".

V1 formal release now requires a small but actually usable knowledge runtime:

- single Agent chat with active-session continuity;
- A-layer Battle Dex structured facts;
- B-layer mechanics / wiki retrieval;
- C-layer runtime policy, persona boundary, and output guard;
- Meta Graph / Knowledge Graph v0.1: reviewed H-Graph `species_set` cards,
  reviewed mechanism guardrails, and relation/speed indexes;
- D-layer v0.1: PM-reviewed expert demonstrations retrieved as analogies.

This does not mean V1 needs a complete environment graph or a large casebank.
The V1 bar is: covered questions must use Meta Graph / D-layer correctly, and
uncovered questions must degrade honestly without exposing internals.

## 2. Superseded Handoff State

The repo currently contains several true-but-old documents. Keep them as
history, but do not let them drive current work.

| File | Current status | Product consequence |
|---|---|---|
| `docs/handoffs/archive/ROCO_V1_ALPHA_HANDOFF_2026_05_03.md` | Archived; superseded by this map | Its A/B/C-only V1 release boundary is no longer current. |
| `docs/handoffs/archive/ROCO_V2_STATUS_2026_05_06.md` | Archived; superseded by this map | Its "D/Meta are V2" framing is now historical. |
| `docs/specs/current_work.md` | Local ignored working note | Useful only as a mutable pointer; this context map is the committed source of truth. |
| `docs/specs/v2_battle_meta_graph_spec.md` | Active design with stale title | The design is active; the V2 naming is historical. H-Graph v0.1 is now V1-gated, S-Graph stays deferred. |

## 3. Read Order

For a zero-context Agent, read in this order:

1. `CLAUDE.md`
2. `docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md`
3. `docs/specs/README.md`
4. `docs/specs/roco_agent_constitution.md`
5. `docs/specs/p12_agent_kv_continuity_and_grounded_llm_reply_bugfix.md`
6. `docs/specs/v2_battle_meta_graph_spec.md`
7. `docs/specs/p10h_tactical_coach_policy_distillation_plan.md`
8. `docs/specs/p10h_d_layer_retrieval_contract.yaml`
9. `docs/specs/p10h_casebank_seed_schema.yaml`
10. `docs/specs/p10h_expert_demo_extraction_manual.md`

Do not start by reading old P0/P1 specs or old P10 release smoke docs unless
debugging a specific historical regression.

## 4. Current Runtime Facts

Observed after the Claude cleanup / staged restructure:

- Python source has been moved under `src/`.
- mobile and desktop clients have been moved under `apps/`.
- `src/advisor/meta_graph.py` exists, but the advisor runtime is not yet wired
  to use Meta Graph context in normal answers.
- Meta Graph raw/candidate data currently lives under `artifacts/v2_meta_graph/`.
- A release-readable Set Graph candidate has been migrated to
  `data/knowledge_graph/v0/set_graph/`, but it is not runtime-active until
  cards are reviewed.
- P14 Knowledge Ops control-plane skeleton exists under
  `data/knowledge_graph/v0/`; mechanism rules and review ledgers are now part
  of the graph-owned runtime target.
- D-layer specs already define runtime storage under
  `data/expert_demonstrations/`; `data/expert_demonstrations/v0/` now exists
  as the V1 target, but no gold cases have been promoted yet.
- Full Python tests are clean after the active-session continuity fix for
  non-exact `/clear` text.
- `apps/desktop` has its own dependency install and passes typecheck/build;
  the old root `desktop/` path is ignored as local residue.

Product translation: the project has useful knowledge assets, but V1 cannot be
called "really usable" until the runtime answer chain consumes a promoted
Meta Graph subset and a promoted D-layer subset.

## 5. Layer Map

| Layer | Current asset | Runtime status | V1 gate |
|---|---|---|---|
| A | `data/runtime/battle_dex.sqlite`, `src/advisor/battle_dex.py` | Working but must be regression-tested after restructure | Required |
| B | `wiki/`, `src/advisor/retrieval.py`, `src/knowledge/` | Working as bounded doc retrieval | Required |
| Meta Graph / Knowledge Graph | `data/knowledge_graph/v0/set_graph/`, `data/knowledge_graph/v0/mechanism_rules/`, `data/knowledge_graph/v0/review_state/`, `artifacts/knowledge_ops/`, `src/advisor/meta_graph.py`, `tools/v2_*`, `tools/p14_validate_knowledge_graph.py` | Candidate graph exists; unreviewed cards and candidate mechanism rules are runtime-filtered; not integrated into advisor answer chain | Required v0.1 |
| D | `data/expert_demonstrations/v0/`, P10h extraction artifacts + D-layer specs | Target exists; no promoted runtime gold subset yet | Required v0.1 |
| C | Constitution, call policy, output guard specs | Required policy layer; guard must cover internal-label leakage | Required |
| UI | `apps/mobile/`, `apps/desktop/` | Shells exist; desktop move needs dependency verification | Required for chosen release surface |

## 6. Artifact Classification

### Active candidate/raw pools

These are not runtime-ready, but they are current source material:

- `artifacts/v2_meta_graph/`
- `artifacts/p10h_expert_demo_extraction/`
- `artifacts/p10h_full_spectrum_extraction_merged_v2/`
- `artifacts/p10h_name_resolution_cleanup/`
- `artifacts/p10h_transcript_cleaning/`
- `artifacts/p10h_case_extraction/`

Do not archive these yet. They are the input pool for selecting Meta Graph v0.1
and D-layer v0.1.

### Historical experiment evidence

Useful for audit, not current runtime input:

- `artifacts/p10h_prebattle_ablation/`
- `artifacts/p10h_prebattle_ablation_r1_transfer_rule/`
- `artifacts/p9c_strategy_eval/`
- `artifacts/p9d_reasoning_effort_loop_eval/`
- `artifacts/p10c_release_smoke_qa/`
- `artifacts/p10d_simulator_and_live_smoke/`
- `artifacts/p10e_runtime_config_ux_repair/`
- `artifacts/p12_agent_continuity_e2e_smoke/`

Keep these under `artifacts/` as historical evidence. Do not promote them into
runtime data.

### Runtime target directories

These are the directories V1 should eventually read from:

```text
data/knowledge_graph/v0/
data/expert_demonstrations/v0/
```

Current state:

- `data/knowledge_graph/v0/set_graph/` exists as a release-readable candidate
  copy, but all copied cards remain `unreviewed`, so runtime must not inject
  them yet.
- `data/knowledge_graph/v0/mechanism_rules/` exists as the compiled mechanism
  guardrail target, but current Phase 0 rules are candidate-only under
  `artifacts/knowledge_ops/mechanism_rules/candidates/`.
- `data/expert_demonstrations/v0/` exists as the D-layer runtime target, but it
  contains no gold cases yet.

The rule is simple: `artifacts/` may contain experiments and raw material;
`data/` contains release-readable assets.

## 7. Archive Candidates

Archived in the first cleanup wave:

- `docs/handoffs/archive/temporary_launchpad_skill_retrospective_2026-04-22.md`
- `docs/handoffs/archive/temporary_zero_context_project_brief_2026-04-20.md`
- `docs/handoffs/archive/pm_console_ctx_pack/`
- `docs/handoffs/archive/ROCO_V1_ALPHA_HANDOFF_2026_05_03.md`
- `docs/handoffs/archive/ROCO_V2_STATUS_2026_05_06.md`

Keep but label as supporting, not archive:

- `docs/handoffs/roco_v1_ui_design_log_2026-04-27.md`
- `docs/specs/p11_single_active_session_kv_plan.md`
- `docs/specs/p12_agent_kv_continuity_and_grounded_llm_reply_bugfix.md`

Do not archive:

- `docs/specs/v2_battle_meta_graph_spec.md`
- `docs/specs/p10h_tactical_coach_policy_distillation_plan.md`
- `docs/specs/p10h_d_layer_retrieval_contract.yaml`
- `docs/specs/p10h_casebank_seed_schema.yaml`
- `docs/specs/p10h_expert_demo_extraction_manual.md`

Comment: old files are not harmless. If they stay at top-level handoff, the
next Agent will choose the wrong release boundary.

## 8. Next Work

1. Build P14 Knowledge Ops Phase 1: mechanism-rule pilot and reviewer-ledger
   workflow.
2. Review/activate low-risk Set Graph candidates through P14 validators and
   promotion audit logs.
3. Repair command drift from the `src/` move across remaining scripts.
4. Promote 3-5 reviewed D-layer gold demonstrations into
   `data/expert_demonstrations/v0/`.
5. Wire advisor runtime answer assembly:
   A facts -> Meta Graph -> B mechanics -> D demonstrations -> synthesis -> C guard.
6. Verify with covered and uncovered user questions before calling V1 usable.
