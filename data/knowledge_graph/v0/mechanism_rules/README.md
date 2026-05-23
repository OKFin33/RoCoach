# Mechanism Rules v0

This directory stores compiled mechanism guardrails for the Knowledge Graph.

Runtime-injectable rules must satisfy:

- `review.review_status: pm_reviewed`
- `runtime.runtime_allowed: true`
- no unresolved contradictions
- A/B references resolve

Candidate rules generated from source evidence belong under
`artifacts/knowledge_ops/mechanism_rules/candidates/` until promoted.
