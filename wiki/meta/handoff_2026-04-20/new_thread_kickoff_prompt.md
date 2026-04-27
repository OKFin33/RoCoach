# New Thread Kickoff Prompt

Use this prompt to start the separate Battle Wiki thread.

```text
Read this context pack first:

/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/meta/handoff_2026-04-20/README.md

You are now responsible for the B-layer Battle Wiki design for Roco.

Goal:
Design a Karpathy-style, source-controlled, LLM-maintained Battle Wiki for
Roco's generic `洛克王国：世界` PvP doctrine layer.

Critical boundaries:
- Roco is not Pokemon. Do not import Pokemon mechanics or assumptions unless a
  Roco project document explicitly approves the analogy.
- B layer must be generic and persona-free.
- Enzo/persona doctrine must not become default Battle Wiki doctrine.
- A-layer exact facts remain in Engine / SQLite battle-dex / approved structured
  sources. The Battle Wiki must not become a second source of truth for exact
  species, move, or ability facts.
- The wiki should follow a Karpathy-style raw/wiki/schema/compiled pattern.
- The first deliverable should be an architecture spec, not a pile of content.

First deliverable:
Draft `specs/battle_wiki_architecture_spec.md`.

The spec must answer:
1. what B Wiki solves
2. what it explicitly does not solve
3. how raw, wiki, schema, and compiled layers relate
4. what content classes exist
5. what sources are allowed
6. how provenance and confidence work
7. how cross-game contamination is prevented
8. how persona is excluded from default B
9. how A-layer facts are referenced without duplicated authority
10. how the wiki later feeds retrieval and live model-backed synthesis

Do not modify runtime code in the first pass.
```

