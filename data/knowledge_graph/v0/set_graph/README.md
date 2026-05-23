# Set Graph v0 Runtime Candidate

This directory is the release-readable Set Graph location for V1 under the P14
Knowledge Graph root.

Current status:

- copied from `artifacts/v2_meta_graph/` on 2026-05-16;
- migrated from `data/meta_graph/v0/` to
  `data/knowledge_graph/v0/set_graph/` on 2026-05-18;
- structurally valid;
- mechanism correction note added at
  `mechanism_notes/2026-05-16_photosynthesis_sandstorm.md`;
- not runtime-active yet because all copied cards still have
  `review_status: unreviewed`;
- runtime retrieval must ignore unreviewed cards.

Promotion rule:

1. PM reviews a card against the source material.
2. The card's `review_status` becomes `reviewed`.
3. `graph_registry.yaml`, `edge_index.yaml`, and `speed_index.yaml` are rebuilt.
4. Only then may the advisor runtime inject that card into an answer.

`artifacts/v2_meta_graph/` remains historical candidate workspace. New P14
candidate work belongs under `artifacts/knowledge_ops/`. `data/` is the only
acceptable home for release-readable graph assets.
