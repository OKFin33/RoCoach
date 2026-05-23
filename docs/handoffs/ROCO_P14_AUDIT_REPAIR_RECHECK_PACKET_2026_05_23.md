# Roco P14 Audit Repair Recheck Packet - 2026-05-23

Status: external recheck requested; post-recheck conditions A/B addressed
Scope: F1-F6/F7 audit repair verification only
Runtime effect: none

This packet asks the reviewer to verify that the audit repair pass closed the
specific findings from the previous external review. It does not ask for a full
dataset audit, Gold acceptance, runtime promotion, source expansion, or graph
materialization.

## Reviewer Task

Review only these questions:

1. Are the six audit-repair items actually represented in durable files?
2. Are the new contracts specific enough for future Agents to follow?
3. Do the validators now catch the repaired failure modes?
4. Are the remaining risks honestly marked instead of hidden?

Do not evaluate whether the Roco dataset is ready for product/runtime use. It
is not.

## Out Of Scope

- accepting Gold items;
- changing `runtime_allowed` to true;
- promoting Set Graph cards into advisor runtime;
- ingesting new sources;
- materializing additional reviewed graph cards;
- publishing a dataset;
- auditing unrelated staged repo restructure work.

## Current Repair Summary

| Finding | Repair status | Primary evidence |
|---|---|---|
| F1 durability / VCS basis | Repaired to staged Git baseline plus snapshot manifest | `data/knowledge_graph/v0/`, `data/knowledge_graph/v0/snapshots/roco_kg_dataset_v0.1-dev/2026-05-23/manifest.yaml` |
| F2 old Set Graph schema vs `p14.kg_item.v0` | Repaired by crosswalk and reviewed-card overlay | `docs/specs/p14_species_set_kg_item_crosswalk_v0.md`, `data/knowledge_graph/v0/set_graph/species_sets/圣羽翼王_waterblade_physical_2026-s1.yaml` |
| F3 review independence evidence | Repaired with identity policy, legacy backfill, and post-policy `legacy_unknown` validator gate | `data/knowledge_graph/v0/review_state/family_review_ledger.yaml`, `data/knowledge_graph/v0/review_state/promotion_audit_log.yaml`, `data/knowledge_graph/v0/review_state/reviewer_ledger.yaml`, `tools/p14_validate_knowledge_graph.py` |
| F4 field-level provenance | Repaired for the materialized reviewed card, enforced by validator, and hash-anchored to referenced set_inventory leaves | `data/knowledge_graph/v0/set_graph/species_sets/圣羽翼王_waterblade_physical_2026-s1.yaml`, `tools/p14_validate_knowledge_graph.py`, `data/knowledge_graph/v0/snapshots/roco_kg_dataset_v0.1-dev/2026-05-23/manifest.yaml` |
| F5 `meta_graph` migration hygiene | Repaired by migration log, schema compatibility manifest, clean old root tracking, validator check | `data/knowledge_graph/v0/migration_log.yaml`, `data/knowledge_graph/v0/runtime_manifest.yaml`, `tools/p14_validate_knowledge_graph.py` |
| F6 candidate Gold to accepted Gold mapping | Repaired by mapping contract; no Gold accepted | `docs/specs/p14_gold_candidate_to_item_mapping_v0.md`, `data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml` |
| F7 measurable baseline | Partially repaired by baseline dashboard; Gold/RAG/judge metrics remain `baseline_needed` | `data/knowledge_graph/v0/eval/quality_dashboard_baseline_2026-05-23.yaml` |

## Required Verification Commands

Run these from repo root:

```bash
git ls-files data/knowledge_graph/v0 | wc -l
git ls-files data/meta_graph/v0 | wc -l
git status --short -- data/meta_graph/v0 data/meta_graph/README.md data/knowledge_graph/v0

PYTHONPATH=.:src .venv/bin/python -m tools.p14_validate_knowledge_graph --strict
PYTHONPATH=.:src .venv/bin/python -m tools.v2_validate_graph --strict
PYTHONPATH=.:src .venv/bin/python -m unittest tests.test_p14_knowledge_graph_validate

rg -n "compatibility_source:" data/knowledge_graph/v0 docs/specs/p14_dataset_snapshot_versioning_contract_v0.md tools/p14_validate_knowledge_graph.py || true

.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
import yaml

manifest = Path("data/knowledge_graph/v0/snapshots/roco_kg_dataset_v0.1-dev/2026-05-23/manifest.yaml")
data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
errors = []
for entry in data["artifact_hashes"]["entries"]:
    path = Path(entry["path"])
    if not path.exists():
        errors.append(f"missing {path}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != entry["sha256"]:
        errors.append(f"hash mismatch {path}: {actual} != {entry['sha256']}")
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"validated {len(data['artifact_hashes']['entries'])} snapshot hashes")
PY
```

Expected current outputs:

- `git ls-files data/knowledge_graph/v0 | wc -l` returns `32`;
- `git ls-files data/meta_graph/v0 | wc -l` returns `0`;
- P14 strict validator prints `P14 Knowledge Graph gates passed`;
- v2 strict validator prints `7` cards validated;
- P14 validator unit test runs `9` tests and passes;
- `compatibility_source:` search returns no matches;
- snapshot hash script validates `24` hashes, including the three set_inventory
  files cited by the reviewed card's span-level provenance.

## Finding-Level Recheck

### F1 - Durability / VCS Basis

Reviewer checks:

- `data/knowledge_graph/v0` is tracked in the Git index;
- snapshot manifest exists and hashes key governance files;
- `data/meta_graph/v0` no longer has tracked active files;
- `artifacts/` is still ignored by design and is not claimed as a durable
  dataset store.

Acceptance:

- pass if Git index and snapshot manifest make the governance asset set
  reproducible enough for an internal dev snapshot;
- fail if reviewer requires a commit instead of staged index as the durability
  threshold.

Residual risk:

- until committed, F1 is staged but not yet in branch history.

### F2 - Species Set Card to `p14.kg_item.v0`

Reviewer checks:

- `docs/specs/p14_species_set_kg_item_crosswalk_v0.md` maps old card fields to
  `p14.kg_item.v0`;
- the materialized reviewed card declares `schema_version`,
  `kg_item_projection`, `crosswalk_ref`, and `projection_status`;
- future runtime reader migration is explicitly deferred.

Acceptance:

- pass if the crosswalk is enough for a future Agent to project reviewed cards
  without inventing a second schema;
- fail if the reviewer requires immediate full conversion of all cards into
  `p14.kg_item.v0`.

Residual risk:

- only the materialized reviewed card has the full overlay. Other cards remain
  unreviewed/candidate.

### F3 - Review Identity / Independence Evidence

Reviewer checks:

- ledgers contain identity policy fields;
- old entries are labeled `legacy_unknown` rather than fabricated;
- validator requires identity fields on `pm_reviewed` entries and promotion
  audit rows.
- validator rejects post-2026-05-23 `pm_reviewed` family-review rows or
  reviewed cards that still use `legacy_unknown` / legacy identity status.

Acceptance:

- pass if `legacy_unknown` is acceptable as historical backfill and new missing
  or post-policy legacy identities are machine-blocked;
- fail if old records must prove actual independent agent/run identity.

Residual risk:

- legacy records cannot prove true independent review. They can only prove that
  the gap is known and future entries are gated.

### F4 - Field-Level Provenance

Reviewer checks:

- the reviewed 圣羽翼王 card has `field_provenance` for species, moves, nature,
  IV, bloodline, role, teammate relations, counter relations, and mechanism
  dependencies;
- claimed fields have span-level or explicit support;
- unclaimed fields are explicit `not_applicable`;
- validator rejects reviewed cards without the overlay.
- snapshot manifest hashes the set_inventory files that contain the referenced
  span leaves.

Acceptance:

- pass if field provenance is sufficient for this first reviewed card;
- fail if reviewer requires every non-materialized candidate card to be
  backfilled now.

Residual risk:

- source span ids are internal anchors into ignored/source artifacts, but the
  three reviewed-card set_inventory leaves are now hash anchored. Broader
  artifacts and raw media remain outside the snapshot.

### F5 - `meta_graph` Migration Hygiene

Reviewer checks:

- `data/knowledge_graph/v0/migration_log.yaml` records source root, target root,
  status, compatibility policy, and Git cleanup status;
- `data/knowledge_graph/v0/runtime_manifest.yaml` uses
  `schema_compatibility.migration_log_ref`;
- `compatibility_source:` is gone;
- strict P14 validator checks root metadata and old active path.

Acceptance:

- pass if old `data/meta_graph/v0` is cleanly historical and current active root
  is `data/knowledge_graph/v0`;
- fail if reviewer finds any runtime/validator path still treating
  `data/meta_graph/v0` as active.

Residual risk:

- `data/meta_graph/README.md` remains as a historical pointer.

### F6 - Gold Candidate to Accepted Gold Mapping

Reviewer checks:

- `docs/specs/p14_gold_candidate_to_item_mapping_v0.md` defines candidate to
  accepted item mapping;
- candidate existence does not alter manifest counts;
- accepted Gold still requires PM decision, expected behavior, provenance, and
  manifest update.

Acceptance:

- pass if mapping closes the schema gap without accepting any Gold;
- fail if reviewer requires a seeded accepted Gold item before this repair can
  close.

Residual risk:

- Gold count remains zero, so regression metrics remain baseline-needed.

### F7 - Baseline Metrics

Reviewer checks:

- dashboard exists and distinguishes real current metrics from
  `baseline_needed`;
- dashboard does not claim Gold/RAG/judge quality before fixtures exist;
- dashboard records the repaired audit findings and residual blockers.

Acceptance:

- pass if the baseline is honest and machine-readable;
- fail if reviewer expects actual Gold/RAG/judge metrics in this repair pass.

Residual risk:

- measurable quality is still early: entity/move/provenance metrics cover only
  the first reviewed materialized card.

## Reviewer Decision Form

Please return one of:

- `accept_repair_packet`: all repair findings are closed for this scope.
- `accept_with_conditions`: list conditions; no new data production should run
  until conditions are addressed.
- `reject_repair_packet`: list failed findings and exact file/command evidence.

Per-finding decision table:

| Finding | Decision | Required note if not accepted |
|---|---|---|
| F1 durability |  |  |
| F2 schema crosswalk |  |  |
| F3 review identity |  |  |
| F4 field provenance |  |  |
| F5 migration hygiene |  |  |
| F6 Gold mapping |  |  |
| F7 baseline metrics |  |  |

## Recommended Next Step If Accepted

Make a focused commit containing only:

- `data/knowledge_graph/v0/`;
- `data/meta_graph/README.md`;
- `docs/specs/p14_species_set_kg_item_crosswalk_v0.md`;
- `docs/specs/p14_gold_candidate_to_item_mapping_v0.md`;
- `docs/specs/p14_dataset_snapshot_versioning_contract_v0.md`;
- `docs/specs/p14_dataset_pipeline_plan_v0_1.md`;
- `docs/specs/README.md`;
- `tools/p14_validate_knowledge_graph.py`;
- `tests/test_p14_knowledge_graph_validate.py`;
- this recheck packet.

Do not include unrelated repo restructure, app, API, or runtime work in the
same commit.
