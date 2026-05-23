# P14 Phase48/49 S2 Overlay Reblock And Post-S2 Expansion Goal Spec v0

Date: 2026-05-23
Owner: PM review by Zab; execution by Agent
Scope: controlled dataset pipeline continuation for RoCoach / Roco P14 knowledge ops

## One-line Goal

Use the existing candidate-only S2 A-layer overlay to re-annotate Phase48/49 blocker semantics, then continue high-signal post-S2 source expansion into candidate-only dataset artifacts, without runtime DB promotion, Gold auto-accept, or reviewed graph materialization.

## Background

Phase48 and Phase49 proved the source/transcript -> A/B refinement -> candidate KG -> field evidence -> dashboard/snapshot pipeline.

After that, the project created:

- S1 Battle Dex freeze:
  - `data/runtime/snapshots/s1_2026-05-20/manifest.yaml`
  - `data/runtime/snapshots/s1_2026-05-20/battle_dex.sqlite`
- S2 candidate A-layer overlay:
  - `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/overlay.yaml`
  - `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/manifest.yaml`

That means the old Phase49 blocker `s2_a_layer_reconciliation_required_before_runtime_or_gold` is no longer the right wording. The S2 reference surface now exists. The correct state is:

```text
S2 overlay is referenced, but candidates still require PM review, reviewed graph/Gold gates, and runtime promotion gates.
```

This goal must not treat the S2 overlay as live runtime truth. It is a versioned candidate reference surface.

## Current Inputs

Use these existing assets as input.

### Phase48

```text
artifacts/knowledge_ops/dataset_pipeline_runs/phase48_controlled_pipeline_drill_2026-05-23/
  candidate_kg_items.yaml
  dashboard.yaml
  field_evidence_index.yaml
  pm_review_packet.md
  provenance_manifest.yaml
  source_bundle_manifest.yaml

data/knowledge_graph/v0/eval/quality_dashboard_phase48_controlled_pipeline_drill_2026-05-23.yaml
```

Current Phase48 status:

- 4 sources, all `pre_s2_source`.
- 20 candidate-only KG items.
- `runtime_allowed=false`.
- `review_candidate_count=0`.
- No S2 reconciliation blocker.
- Must remain historical/pre-S2 evidence; do not recast as post-S2 current truth.

### Phase49

```text
artifacts/knowledge_ops/dataset_pipeline_runs/phase49_post_s2_targeted_ingest_2026-05-23/
  candidate_kg_items.yaml
  dashboard.yaml
  field_evidence_index.yaml
  pm_review_packet.md
  provenance_manifest.yaml
  source_bundle_manifest.yaml

data/knowledge_graph/v0/eval/quality_dashboard_phase49_post_s2_targeted_ingest_2026-05-23.yaml
```

Current Phase49 status:

- 5 sources, all `post_s2_candidate`.
- 50 candidate-only KG items.
- `runtime_allowed=false`.
- `review_candidate_count=0`.
- 5 items currently blocked by `s2_a_layer_reconciliation_required_before_runtime_or_gold`.

The 5 S2-affected Phase49 items are:

```text
candkg/phase49_post_s2_targeted_ingest_2026-05-23/species_set/kgsrc_bili_bv15ygq6beu8/龙鱼
  affected: 龙吟, 龙鱼

candkg/phase49_post_s2_targeted_ingest_2026-05-23/species_set/kgsrc_bili_bv1fely6pe7g/皇家狮鹫
  affected: 皇家狮鹫

candkg/phase49_post_s2_targeted_ingest_2026-05-23/species_set/kgsrc_bili_bv1upgi6jenf/电球咩咩
  affected: 落雷

candkg/phase49_post_s2_targeted_ingest_2026-05-23/relation/kgsrc_bili_bv15ygq6beu8/cand_kgsrc_bili_bv15ygq6beu8_edge_002
  affected: 仪式巨像

candkg/phase49_post_s2_targeted_ingest_2026-05-23/mechanism_dependency/kgsrc_bili_bv15ygq6beu8/仪式巨像/mechanism_mark_unspecified_2026-s1/S0096
  affected: 仪式巨像
```

### S2 Overlay

```text
data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/manifest.yaml
data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/overlay.yaml
data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/reconciliation_summary.yaml
data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/validation_evidence.yaml
data/knowledge_graph/v0/eval/quality_dashboard_s2_a_layer_overlay_snapshot_2026-05-23.yaml
```

Required S2 overlay facts:

- `runtime_allowed: false`
- `promotion_status: candidate_only`
- `may_write_runtime_db: false`
- `requires_pm_review_before_runtime: true`
- `requires_pm_review_before_a_layer_write: true`
- `waterblade_response_state_energy_reduction_ok: true`

## Required Product Boundary

This goal may produce:

- a derived Phase50 reblock package that cites Phase48/49 and the S2 overlay;
- reblocked candidate copies or an overlay-style blocker migration report;
- updated PM-readable dashboard and review packet;
- new post-S2 source probes, transcripts, AB-refined transcripts, segments, field evidence, candidate-only KG items, and source hashes;
- snapshot/hash manifests for the new Phase50 package.

This goal may not produce:

- writes to `data/runtime/battle_dex.sqlite`;
- runtime manifest changes;
- runtime DB promotion;
- reviewed graph cards;
- Gold auto-accept;
- D-layer promotion;
- runtime answer behavior changes;
- removal of PM/review/Gold gates.

## Historical Artifact Rule

Do not edit Phase48/49 original run files in place.

Reason: Phase48/49 are historical run outputs with their own dashboards and snapshot/hash expectations. Rewriting them would make earlier audit evidence lie.

Instead, create a derived Phase50 package that records:

- source Phase48/49 file paths and hashes;
- S2 overlay manifest path and hash;
- blocker migration rules;
- old blocker counts;
- new blocker counts;
- item-level migration decisions.

## Required Reblock Semantics

### Phase48

Phase48 remains pre-S2 historical evidence.

Do:

- add an epoch-boundary note in the derived Phase50 report;
- keep candidate-only and blocked status;
- require post-S2 confirmation or PM review before any reviewed/Gold/runtime use.

Do not:

- attach S2 overlay as if it validates Phase48 set correctness;
- mark Phase48 items as post-S2 current truth;
- remove existing blockers.

Suggested Phase48 wording:

```text
pre_s2_historical_evidence_requires_post_s2_confirmation_or_pm_review
```

### Phase49

For Phase49 candidate items that currently have:

```text
s2_a_layer_reconciliation_required_before_runtime_or_gold
```

replace it in the derived Phase50 package with:

```text
s2_a_layer_overlay_referenced_pm_review_gold_gate_required
```

This means:

- the missing S2 reference-surface problem is resolved;
- the item is still not review-ready unless all other blockers are resolved;
- the item still cannot enter reviewed graph, Gold, or runtime without explicit PM/review gates.

Preserve all other blockers, including but not limited to:

- `pm_review_required`
- `cross_source_consolidation_required`
- `incomplete_move_slots`
- `source_inventory_not_reviewed`
- `mechanism_rule_not_reviewed`
- `single_evidence_window`
- `source_phrase_only`

The derived Phase50 package should report:

```yaml
old_s2_reference_surface_blocker_count: 5
new_s2_overlay_referenced_gate_count: 5
review_candidate_count: 0
runtime_allowed: false
```

If the actual counts differ, stop and report the mismatch instead of silently continuing.

## Post-S2 Expansion Lane

After reblock is complete, continue source discovery and candidate extraction with strict priority.

### Source Priority

P1 sources:

- post-S2 team/set explainers;
- explicit PvP/ranked current-season content;
- source likely to contain species + move set + role/intent;
- source likely to contain repeated relation/counterplay evidence.

P2 sources:

- post-S2 gameplay replays with clear commentary and repeated set/relation mentions;
- post-S2 tier/overview videos only if they include concrete set or relation details.

P3 sources:

- official update pages and balance notes for mechanism/reference support;
- short clips or social posts used only as low-confidence supporting evidence.

Reject or quarantine:

- pure entertainment clips with no PvP structure;
- pre-S2 sources unless explicitly used as historical contrast;
- sources with no recoverable transcript or provenance;
- sources that cannot produce local source_probe, transcript/ASR, AB-refined transcript, segments, and hashes.

### Expansion Targets

Prefer high-signal set/relation directions already surfaced by Phase48/49:

- direct post-S2 primary sources for `帕帕斯卡`;
- `风起印记/狮鹫迪迪` related set evidence;
- relation/counterplay evidence around `雷暴队/兽花蕾`, still without graph edge promotion;
- candidates touching S2-changed species or moves only when they can cite the S2 overlay.

Do not spend this goal on low-yield broad scraping. The point is higher-signal ingestion, not raw volume.

## Expected Output Layout

Preferred new run directory:

```text
artifacts/knowledge_ops/dataset_pipeline_runs/phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23/
  candidate_kg_items.yaml
  dashboard.yaml
  field_evidence_index.yaml
  pm_review_packet.md
  provenance_manifest.yaml
  source_bundle_manifest.yaml
  blocker_migration_report.yaml
  validation_evidence.yaml
```

Preferred tracked dashboard/snapshot outputs:

```text
data/knowledge_graph/v0/eval/quality_dashboard_phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23.yaml

data/knowledge_graph/v0/snapshots/roco_kg_dataset_v0.1-dev/phase50_s2_overlay_reblock_and_post_s2_expansion_2026-05-23/
  manifest.yaml
```

If project conventions force different names, keep the same semantics and explain the difference in the PM packet.

## Required PM Packet Questions

The PM review packet must answer:

1. What changed from Phase48/49, and what did not change?
2. Which exact blocker label was migrated?
3. Which items were affected by the migration?
4. Does any item become reviewed, Gold, or runtime-allowed? Expected answer: no.
5. Which post-S2 sources were added, and why were they high-signal?
6. What candidate items were produced by the new expansion lane?
7. Which candidates now cite the S2 overlay?
8. What still blocks reviewed graph, Gold, and runtime DB promotion?
9. What should PM review first?

Use PM-readable language. Do not require PM to inspect code.

## Validation Commands

At minimum run:

```bash
PYTHONPATH=.:src .venv/bin/python -m tools.p14_validate_knowledge_graph --strict
PYTHONPATH=.:src .venv/bin/python -m unittest \
  tests.test_p14_knowledge_graph_validate \
  tests.test_p14_s2_a_layer_overlay_snapshot
```

If the run adds or changes source ingestion/transcript tooling, also run the relevant focused tests for that path. Prefer the existing Phase48/49 validation style:

```bash
PYTHONPATH=.:src .venv/bin/python -m unittest \
  tests.test_transcript_ab_refine \
  tests.test_transcript_quality \
  tests.test_video_evidence_foundation \
  tests.test_p14_source_queue_expand \
  tests.test_p14_volume_ingest_batch
```

Also verify:

- `data/runtime/battle_dex.sqlite` hash is unchanged;
- every new source has a source artifact hash;
- every candidate item has field evidence or explicit unresolved/not_observed status;
- every candidate item has `runtime_allowed=false`;
- no files were written under reviewed set graph or Gold as promotion outputs;
- snapshot/hash self-check passes for all Phase50 durable outputs.

## Acceptance Criteria

All must be true:

1. Phase48/49 originals are not modified in place.
2. Phase50 package records Phase48/49 source file hashes.
3. Phase50 package records S2 overlay manifest hash.
4. Phase49 old S2 reference-surface blocker count is 5, or mismatch is reported as a stop condition.
5. Phase50 reblock output has `old_s2_reference_surface_blocker_count: 5`.
6. Phase50 reblock output has `new_s2_overlay_referenced_gate_count: 5`.
7. Phase50 reblock output has `review_candidate_count: 0`.
8. All Phase50 candidate items remain `runtime_allowed=false`.
9. S2-affected Phase49 candidates cite the S2 overlay manifest instead of claiming S2 truth from source text alone.
10. Phase48 remains marked as pre-S2 historical evidence.
11. New post-S2 sources are P1/P2 by the source policy above, or explicitly quarantined as P3 support.
12. New candidate items are candidate-only and blocked by PM/review/Gold gates.
13. P14 strict validator passes.
14. Focused tests and snapshot/hash checks pass.
15. PM packet clearly lists residual blockers and next review targets.

## Stop Conditions

Stop and report instead of improvising if:

- Phase48/49 original files must be edited to make validation pass;
- S2 overlay manifest hash cannot be verified;
- the 5 expected Phase49 S2 blockers are not found;
- any candidate would become `runtime_allowed=true`;
- any reviewed graph card, Gold item, or runtime DB write is required;
- source discovery cannot find any P1/P2 post-S2 source after reasonable attempts;
- validation failure would require relaxing P14 gates;
- source evidence cannot be preserved with local transcript/segments/hash.

## Suggested /goal Prompt

```text
/goal Execute the RoCoach/Roco P14 Phase48/49 S2 overlay reblock and controlled post-S2 high-signal expansion described in goal_specs/p14_phase48_49_s2_overlay_reblock_and_post_s2_expansion_goal_spec_v0.md until the PM review packet, blocker migration report, dashboard, provenance manifests, field evidence, and snapshot/hash evidence are complete, without modifying Phase48/49 originals in place, without modifying data/runtime/battle_dex.sqlite, without runtime promotion, without Gold auto-accept, without reviewed graph materialization, and without removing PM/review/Gold gates.
```

## Expected Final State

The expected result is not "S2 data is live".

The expected result is:

```text
Phase48 remains pre-S2 historical candidate evidence.
Phase49 no longer says the S2 reference surface is missing.
Phase49-derived S2-affected candidates now cite the S2 overlay but remain gated.
New post-S2 sources expand high-signal set/relation candidate coverage.
All new outputs remain candidate-only, hashable, reviewable, and blocked from runtime.
```
