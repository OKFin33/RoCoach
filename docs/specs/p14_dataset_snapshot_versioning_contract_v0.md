# P14 Dataset Snapshot and Versioning Contract v0

Status: planning contract
Date: 2026-05-22
Scope: dataset snapshot identity, manifest, versioning, and supersession
Runtime effect: none

This document is the DP-02 output for the dataset pipeline planning package.
It defines how future snapshots are named and audited. It does not create a
snapshot directory, copy artifacts, rebuild indexes, or promote runtime data.

## 1. Canonical Snapshot ID

Future v0.1 planning snapshots use:

```text
roco_kg_dataset_v0.1-dev/YYYY-MM-DD
```

Rules:

- `v0.1-dev` means not a public release and not runtime-ready by itself.
- The date is the snapshot assembly date, not the source publication date.
- A snapshot id is valid only when a manifest exists.
- Snapshot creation is not runtime promotion.

## 2. Snapshot Scope States

```yaml
scope: planning | candidate | reviewed | runtime_candidate
```

Meanings:

| State | Meaning | Runtime allowed |
|---|---|---:|
| `planning` | contracts/templates only | no |
| `candidate` | assembled candidate evidence/KG/Gold refs | no |
| `reviewed` | PM/reviewer accepted subset exists | no by default |
| `runtime_candidate` | reviewed subset prepared for separate promotion gate | no until promotion gate passes |

Runtime promotion requires separate P14 validators and PM policy. It is not a
snapshot state transition.

## 3. Manifest Schema

```yaml
schema_version: p14.dataset_snapshot_manifest.v0
snapshot_id: roco_kg_dataset_v0.1-dev/YYYY-MM-DD
created_at: ""
created_by:
  role: ""
  agent_id: ""
  run_or_context_id: ""
scope: planning
runtime_allowed: false
components:
  evidence_kb:
    source_queue_ref: ""
    source_reliability_ledger_ref: ""
    evidence_manifest_refs: []
    excluded_raw_payloads:
      - raw_media
      - redistributable_transcripts
  structured_kg:
    root: data/knowledge_graph/v0
    graph_registry_ref: ""
    set_family_refs: []
    mechanism_rule_refs: []
    review_state_refs: []
    excluded_runtime_indexes: []
  gold_eval:
    gold_manifest_ref: data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
    regression_result_ref: ""
  llm_wiki:
    readable_note_refs: []
schema_versions:
  evidence_segment: ""
  kg_item: ""
  gold_item: ""
  review_packet: ""
artifact_hashes:
  docs: {}
  manifests: {}
  reviewed_data: {}
supersession:
  supersedes: []
  superseded_by: null
known_exclusions: []
distribution:
  state: internal_only
  raw_transcripts: internal_reference_only
```

## 4. Included and Excluded Artifact Classes

Allowed in snapshot manifests:

- source ids, URLs, uploader ids/names, publication dates;
- evidence manifest paths and span ids;
- structured candidate/reviewed KG paths;
- review ledgers and PM packet refs;
- Gold/Eval manifest and regression result refs;
- dataset card and quality dashboard refs;
- hashes for included text/structured artifacts.

Excluded by default:

- raw media;
- redistributable transcript bundles;
- unreviewed runtime indexes as promotion evidence;
- source-probe scratch output;
- unresolved ASR fields in promoted/reviewed facts;
- any artifact whose rights state is unknown and not marked internal-only.

## 5. Artifact Hash Policy

Future manifests should hash stable text/structured artifacts that support the
snapshot:

```yaml
artifact_hashes:
  "docs/specs/p14_dataset_card_template_v0.md": "sha256:..."
  "data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml": "sha256:..."
```

Hashing policy:

- hash the exact file bytes at snapshot assembly time;
- do not hash remote videos or raw media unless a legal storage policy exists;
- record missing hashes as `hash_pending` only for planning/candidate snapshots;
- reviewed/runtime-candidate snapshots cannot silently omit required hashes.

## 6. Supersession

Snapshots are immutable references. They are superseded by new manifests, not
edited in place.

```yaml
supersession:
  supersedes:
    - roco_kg_dataset_v0.1-dev/2026-05-22
  superseded_by: roco_kg_dataset_v0.1-dev/2026-05-23
  reason: "schema migration and corrected canonicalization"
```

Allowed supersession reasons:

- schema migration;
- source correction;
- canonicalization fix;
- mechanism contradiction resolution;
- Gold/Eval regression failure;
- product eval regression;
- rights/distribution correction.

## 7. Schema Migration Boundary

Current graph-root history:

- older material may reference `data/meta_graph/v0/`;
- P14 target root is `data/knowledge_graph/v0/`;
- this planning package does not move graph roots;
- any future migration must be explicit, validator-backed, and logged.

Manifest rule:

```yaml
schema_compatibility:
  historical_roots:
    - data/meta_graph/v0
  current_target_root: data/knowledge_graph/v0
  migration_required: false
  migration_log_ref: data/knowledge_graph/v0/migration_log.yaml
```

If a future task finds root ambiguity, it must record a migration decision
instead of moving files opportunistically.

## 8. Runtime-Promotion Separation

A snapshot may be useful evidence without being runtime-readable.

Promotion is separate and requires:

- source quality gate;
- A-layer canonicalization and legality checks;
- no unresolved ASR in promoted fields;
- no open contradiction;
- reviewed mechanism refs for mechanism-dependent edges;
- strict graph validators;
- promotion audit log entry;
- PM-approved policy for the promotion path.

The manifest field remains:

```yaml
runtime_allowed: false
```

unless the separate promotion gate writes a promotion audit record.

## 9. Minimal Manifest Example

```yaml
schema_version: p14.dataset_snapshot_manifest.v0
snapshot_id: roco_kg_dataset_v0.1-dev/2026-05-22
created_at: "2026-05-22T00:00:00+08:00"
created_by:
  role: planning_agent
  agent_id: ""
  run_or_context_id: ""
scope: planning
runtime_allowed: false
schema_compatibility:
  historical_roots:
    - data/meta_graph/v0
  current_target_root: data/knowledge_graph/v0
  migration_required: false
  migration_log_ref: data/knowledge_graph/v0/migration_log.yaml#migration/meta_graph_v0_to_knowledge_graph_v0_set_graph_2026-05-18
components:
  evidence_kb:
    source_queue_ref: ""
    source_reliability_ledger_ref: data/knowledge_graph/v0/review_state/source_reliability_ledger.yaml
    evidence_manifest_refs: []
    excluded_raw_payloads: [raw_media, redistributable_transcripts]
  structured_kg:
    root: data/knowledge_graph/v0
    graph_registry_ref: data/knowledge_graph/v0/set_graph/graph_registry.yaml
    set_family_refs: []
    mechanism_rule_refs: []
    review_state_refs: []
    excluded_runtime_indexes: []
  gold_eval:
    gold_manifest_ref: data/knowledge_graph/v0/eval/gold_set_v0_manifest.yaml
    regression_result_ref: ""
  llm_wiki:
    readable_note_refs: []
schema_versions: {}
artifact_hashes: {}
supersession:
  supersedes: []
  superseded_by: null
known_exclusions:
  - no PM accepted Gold items at planning time
distribution:
  state: internal_only
  raw_transcripts: internal_reference_only
```
