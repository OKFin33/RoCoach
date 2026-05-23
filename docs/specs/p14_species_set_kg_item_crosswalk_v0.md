# P14 Species Set Card to KG Item Crosswalk v0

Status: active migration contract
Date: 2026-05-23
Scope: `species_set` card to `p14.kg_item.v0` field mapping
Runtime effect: none

This document closes the audit gap between legacy Set Graph cards and the
dataset pipeline `p14.kg_item.v0` schema. It is a migration contract, not a
runtime promotion.

## 1. Decision

Runtime-readable Set Graph cards remain the current materialized card format
for `data/knowledge_graph/v0/set_graph/species_sets/`.

Dataset snapshots and future data-production lanes must also be able to project
each reviewed card into `p14.kg_item.v0`. The projection is declarative: a card
may keep the legacy runtime shape, but it must carry enough field provenance
and review identity to satisfy the KG item contract.

## 2. Crosswalk

| `species_set` card field | `p14.kg_item.v0` field | Rule |
|---|---|---|
| `id` | `kg_item_id` | Preserve exactly. |
| `canonical_species_id` / `canonical_species_name` | `canonical_entities.species[]` and `a_layer_resolution.species[]` | Species id/name must be A-layer resolved or explicitly unresolved. |
| `moves[]` | `canonical_entities.moves[]` and `a_layer_resolution.moves[]` | Core moves become promoted move fields and require span-level provenance. |
| `flex_moves[]` | `canonical_entities.moves[]` with `field_provenance.support_type=explicit` or `inferred_from_bundle` | Flex moves are preserved but must not be promoted as core. |
| `ability` | `canonical_entities.abilities[]` | Include only if A-layer resolution is known; otherwise mark unresolved/not_applicable. |
| `family_scope.family_name` | `quality.notes` or `field_provenance.role[]` | Family name is reviewer-facing identity, not a deterministic battle fact. |
| `family_scope.parent_species_state` | `review.notes` and `quality.contradiction_state` | `split_blocked` must remain visible. |
| `role_labels[]` | `field_provenance.role[]` | Roles require source/review support and remain semantic labels. |
| `team_context.common_partners[]` | `field_provenance.teammate_relations[]` | Empty or unclaimed partner fields must be explicit not-applicable. |
| `related_to[]` | `relation_claim` KG items or `field_provenance.*_relations[]` | High-risk relation claims require their own evidence and mechanism refs. |
| `mechanism_refs[]` | `field_provenance.mechanism_dependencies[]` | Runtime use requires reviewed mechanism rules. |
| `source_refs[]` | `source_ids[]`, `source_span_ids[]`, `field_provenance.*.source_span_ids[]` | Item-level source refs are not enough for reviewed fields. |
| `source_quality.source_inventory_paths[]` | `transform_lineage.consolidation_batch` / evidence refs | Paths remain internal evidence refs. |
| `promotion.*` | `review.status`, `review.review_packet`, `runtime_allowed` | `runtime_promoted` is false unless a separate promotion gate passes. |

## 3. Required Overlay for Reviewed Cards

Every reviewed `species_set` card must include:

```yaml
schema_version: p14.species_set_card.v0
kg_item_projection:
  schema_version: p14.kg_item.v0
  kg_item_type: set_family
  crosswalk_ref: docs/specs/p14_species_set_kg_item_crosswalk_v0.md
  projection_status: complete | partial | legacy_gap
field_provenance:
  species: []
  moves: []
  nature: []
  iv: []
  bloodline: []
  role: []
  teammate_relations: []
  counter_relations: []
  mechanism_dependencies: []
review_identity:
  extractor_agent_id: ""
  extractor_run_id: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
```

Use `legacy_unknown` only for records created before this policy. New reviewed
items after 2026-05-23 must record real agent/run ids or stay unreviewed.

## 4. Drop / Do Not Project

The following fields do not become KG facts by themselves:

- `notes`;
- `source_refs[].claim` prose;
- `confidence` display label;
- source title or uploader text;
- family names without source/review support;
- empty team partner arrays.

They may remain card metadata, but future KG item materialization must not
infer facts from them.

## 5. Runtime Schema Decision

Current runtime target:

```text
data/knowledge_graph/v0/set_graph/species_sets/*.yaml
```

Future dataset snapshot target:

```text
p14.kg_item.v0 projection over reviewed cards
```

Do not introduce a second runtime reader until a separate migration task has
tests for both old card resolution and `kg_item` projection equivalence.

## 6. Acceptance Checklist

- reviewed cards declare `schema_version`;
- reviewed cards have span-level `field_provenance`;
- reviewed cards record review identity, or `legacy_unknown` with policy;
- item-level source refs are not used as field-level evidence;
- unclaimed nature/IV/bloodline/team fields are explicit not-applicable;
- runtime promotion remains separate from `pm_reviewed` card materialization.
