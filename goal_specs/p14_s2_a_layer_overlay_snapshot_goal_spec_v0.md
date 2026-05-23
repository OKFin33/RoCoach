# P14 S2 A-layer Overlay Snapshot Goal Spec v0

Date: 2026-05-23
Owner: PM review by Zab; execution by Agent
Scope: controlled A-layer versioning preparation for Roco P14 dataset pipeline

## One-line Goal

Create a durable S1 Battle Dex freeze and a candidate-only S2 A-layer overlay/snapshot from the existing official S2 patch delta and reconciliation artifacts, without changing runtime knowledge, Gold data, reviewed graph cards, or `data/runtime/battle_dex.sqlite`.

## Background

Roco is moving from uncontrolled set extraction toward a governed dataset pipeline:

- Evidence KB preserves raw/source evidence.
- A-layer Battle Dex stores structured game facts.
- P14 Knowledge Graph stores candidate/reviewed set, relation, and mechanism data.
- Gold/Eval measures whether the automated pipeline is improving.

The 2026-05-21 S2 update changed existing species stats, abilities, move pools, and move effects. Post-S2 source ingestion can continue, but candidates touching changed entities must cite a reconciled S2 A-layer version surface or remain blocked.

This goal is not to build the dataset itself. It creates the versioned A-layer substrate needed before later `/goal` runs can safely ingest larger post-S2 data.

## Current Inputs

Use these existing repo assets:

- S1 runtime Battle Dex:
  - `data/runtime/battle_dex.sqlite`
- S2 patch gate:
  - `docs/specs/p14_s2_patch_delta_gate_v0.md`
- S2 official source capture:
  - `data/knowledge_graph/v0/patch_deltas/s2_2026-05-20_official_balance_sources/s2_2026-05-20_official_balance_manifest.yaml`
  - `data/knowledge_graph/v0/patch_deltas/s2_2026-05-20_official_balance_sources/official_article_18788872_text.md`
  - official page: `https://rocom.qq.com/web202507/sub/detail.html?newsid=18788872`
  - discovery page: `https://rocom.qq.com/web202507/sub/detail.html?newsid=18788208`
- S2 patch delta pack:
  - `data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_patch_delta_pack_v0.yaml`
- S2 reconciliation output:
  - `data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_a_layer_reconciliation_v0.yaml`
- Reconciliation tool:
  - `tools/p14_reconcile_s2_patch_delta.py`
- P14 validator:
  - `tools/p14_validate_knowledge_graph.py`

## Required Product Boundary

This run may produce:

- S1 immutable Battle Dex snapshot/copy.
- S2 candidate A-layer overlay files.
- Snapshot manifests and hashes.
- Dashboard/report entries showing blocker status.
- PM review packet explaining what is ready, blocked, and unsafe to promote.

This run may not produce:

- runtime DB overwrite;
- runtime manifest pointing to S2 data;
- reviewed graph card promotion;
- Gold auto-accept;
- D-layer data;
- runtime answer changes;
- any claim that S2 A-layer is production truth.

## Important Domain Correction

Represent `水刃` correctly.

The S2 change is:

```text
水刃：造成物伤，应对状态：本技能能耗永久 -4 -> -3
```

Do not record this as base energy cost changing from 4 to 3. It is a change to the attached effect under response state / successful response context.

## Expected Output Layout

Preferred output directories:

```text
data/runtime/snapshots/s1_2026-05-20/
  battle_dex.sqlite
  manifest.yaml

data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/
  overlay.yaml
  manifest.yaml
  reconciliation_summary.yaml
  pm_review_packet.md
```

If an existing project convention conflicts with this layout, keep the same product boundary but document the alternative path clearly in the PM packet.

## Required Overlay Semantics

The S2 overlay must be candidate-only:

```yaml
schema_version: p14.a_layer_overlay.v0
game_epoch: s2_2026-05-21_candidate
runtime_allowed: false
promotion_status: candidate_only
base_snapshot_ref: data/runtime/snapshots/s1_2026-05-20/manifest.yaml
patch_delta_ref: data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_patch_delta_pack_v0.yaml
reconciliation_ref: data/knowledge_graph/v0/patch_deltas/s2_2026-05-21_a_layer_reconciliation_v0.yaml
official_source_ref: data/knowledge_graph/v0/patch_deltas/s2_2026-05-20_official_balance_sources/s2_2026-05-20_official_balance_manifest.yaml
may_write_runtime_db: false
requires_pm_review_before_runtime: true
```

Overlay entries should preserve enough structure for future tools to apply them to a copied DB, but this run should not apply them to `data/runtime/battle_dex.sqlite`.

## Execution Steps

1. Inspect current git state and note unrelated dirty files. Do not revert anything.
2. Re-run S2 reconciliation:

```bash
PYTHONPATH=.:src .venv/bin/python tools/p14_reconcile_s2_patch_delta.py
```

3. Verify reconciliation has no unresolved or non-dex items.
4. Create S1 Battle Dex freeze under `data/runtime/snapshots/s1_2026-05-20/`.
5. Write an S1 snapshot manifest with:
   - source path;
   - frozen copy path;
   - SHA-256 hash;
   - created timestamp;
   - immutable / historical baseline note.
6. Build S2 A-layer candidate overlay from the reconciliation output.
7. Write S2 overlay manifest with:
   - base S1 snapshot ref;
   - patch delta ref/hash;
   - reconciliation ref/hash;
   - official source ref/hash;
   - overlay hash;
   - `runtime_allowed: false`;
   - `promotion_status: candidate_only`;
   - remaining blockers.
8. Update or create a dashboard/report artifact that says:
   - S1 freeze exists;
   - S2 overlay exists;
   - whether unresolved S2 items remain;
   - whether post-S2 candidates can reference the overlay;
   - whether runtime/Gold/review promotion remains blocked.
9. Run validation commands.
10. Produce PM review packet with a concise decision table.

## Validation Commands

At minimum run:

```bash
PYTHONPATH=.:src .venv/bin/python tools/p14_reconcile_s2_patch_delta.py
PYTHONPATH=.:src .venv/bin/python -m tools.p14_validate_knowledge_graph --strict
PYTHONPATH=.:src .venv/bin/python -m unittest \
  tests.test_import_battle_dex_sqlite \
  tests.test_import_battle_dex_dry_run \
  tests.test_p14_knowledge_graph_validate
```

If new helper code is added, add focused tests for:

- snapshot hash reproducibility;
- overlay manifest required fields;
- `runtime_allowed=false` enforcement;
- `水刃` response-state energy-reduction wording.

## Acceptance Criteria

All must be true:

1. `data/runtime/battle_dex.sqlite` is byte-identical before and after the run.
2. S1 Battle Dex snapshot exists and has a manifest with hash.
3. S2 candidate overlay exists and has a manifest with hash.
4. Overlay references official S2 source, patch delta pack, reconciliation, and S1 base snapshot.
5. Overlay and all related manifests state `runtime_allowed: false`.
6. Reconciliation summary reports zero unresolved/non-dex items, or every unresolved item is explicitly listed as blocker.
7. `水刃` is represented as response-state attached-effect change: `-4 -> -3`, not base energy-cost change.
8. P14 strict validator passes.
9. Relevant tests pass.
10. PM review packet clearly says what can happen next and what is still forbidden.

## Stop Conditions

Stop and report instead of improvising if:

- reconciliation introduces unresolved high-impact entities;
- S1 dex hash changes unexpectedly;
- official source hashes cannot be verified;
- validator fails in a way that would require relaxing rules;
- applying the overlay requires writing to `data/runtime/battle_dex.sqlite`;
- the expected fields cannot be represented without inventing a new schema.

## PM Review Packet Requirements

The PM packet should answer:

- What files were produced?
- What did the S1 freeze prove?
- What does the S2 overlay contain?
- Which S2 changes still block runtime/Gold/review?
- Can Phase48/Phase49 candidate-only items now cite the S2 overlay?
- What remains before actual S2 runtime DB promotion?

Use PM-readable language. Do not require the PM to inspect code.

## Suggested /goal Prompt

```text
/goal Execute the Roco P14 S2 A-layer overlay snapshot goal described in goal_specs/p14_s2_a_layer_overlay_snapshot_goal_spec_v0.md until the PM review packet and validation evidence are complete, without modifying data/runtime/battle_dex.sqlite, without runtime promotion, without Gold auto-accept, without reviewed graph materialization, and without bypassing P14 validator/dashboard/hash checks.
```

## Expected Final State

The expected result is not "S2 data is live".

The expected result is:

```text
S1 Battle Dex is durably frozen.
S2 candidate overlay is durably described and hashable.
Post-S2 candidate ingestion has a versioned A-layer reference surface.
Runtime, Gold, and reviewed graph promotion remain blocked until PM review.
```
