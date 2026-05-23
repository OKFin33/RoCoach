# Knowledge Graph v0

This is the P14 graph-owned runtime target.

It contains three governed asset groups:

- `set_graph/` - species_set cards, edge index, speed index, graph registry.
- `mechanism_rules/` - compiled mechanism guardrails used by Set Graph gates.
- `review_state/` - reviewer ledgers, error memory, source reliability, and
  promotion audit logs.

Family-level set reviews live in
`review_state/family_review_ledger.yaml`. They may approve a stable set family
without approving the parent species as a species-wide standard card.

The first reviewed family-scoped card is
`set_graph/species_sets/圣羽翼王_waterblade_physical_2026-s1.yaml`. It is
materialized for release-readable graph review, but not runtime-promoted.

`artifacts/knowledge_ops/` remains the candidate/raw workspace. Runtime code
must not read candidate artifacts directly.
