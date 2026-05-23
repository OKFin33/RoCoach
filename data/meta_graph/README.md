# Meta Graph Path Notice

`data/meta_graph/v0/` was the first narrow runtime-candidate location for Meta
Graph cards.

P14 moved the active graph target to:

```text
data/knowledge_graph/v0/set_graph/
```

The wider `data/knowledge_graph/v0/` root also owns mechanism rules and review
state. New tooling should read from the knowledge graph root. The old
`data/meta_graph/v0/` path is compatibility-only if it exists in an older
checkout.
