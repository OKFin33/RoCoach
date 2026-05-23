# D-layer Expert Demonstrations v0

This directory is the release-readable D-layer location for V1.

Current status:

- no gold demonstrations promoted yet;
- candidate/source material remains under `artifacts/p10h_*`;
- runtime must read only reviewed gold demonstrations from this tree;
- raw transcripts, review notes, and candidate cases must not be prompt-injected.

Expected layout after promotion:

```text
data/expert_demonstrations/v0/
  gold/
  index/
  manifest.yaml
```

Promotion rule:

1. Extract a candidate from source material under `artifacts/p10h_*`.
2. Resolve names against A-layer canonical species/move names.
3. PM reviews source fidelity.
4. Promote the case to `gold/` only after review.
5. Rebuild retrieval index under `index/`.

D-layer examples are analogies. They cannot override A-layer Battle Dex facts.
