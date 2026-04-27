# B Layer Battle Wiki Handoff

Date: 2026-04-20

Source thread:

- Roco PM-control / LaunchPad-controlled development thread

Target thread:

- Separate Battle Wiki / doctrine knowledge-infrastructure thread

## Why This Handoff Exists

The current Roco thread is acting as a PM development control console. During
P1a synthesis review, a separate issue emerged:

- the product needs a richer `B` layer so the synthesis system can understand
  battle doctrine, team-building methodology, tactical cases, and advice taste
- that work is knowledge-infrastructure and editorial-system design
- it should not stay inside the current execution-control thread

This document captures the current thread's net-new decisions so the Battle
Wiki thread can start without re-litigating the same boundaries.

## Current Product Architecture Context

Roco currently uses the conceptual split:

```text
Final advisory reasoning = Synthesize(A, B)
```

Where:

- `A` is the grounded analytical substrate:
  - deterministic battle engine outputs
  - SQLite battle-dex facts
  - approved structured records
  - bounded retrieval snippets
  - confidence, refusal, and warning boundaries
- `B` should be the generic battle doctrine layer:
  - mechanics interpretation
  - team-building methodology
  - role and archetype methodology
  - tactical case patterns
  - recommendation taste constraints
  - uncertainty and bad-advice rules

The current P1a code implemented a synthesis seam, but only with a deterministic
bounded synthesis implementation. It did not yet implement a live model-backed
synthesis provider or a mature B-layer knowledge base.

## Critical Correction From This Thread

The assistant incorrectly drifted into Pokemon framing when discussing B Wiki.
That was a domain-contamination signal.

The correct domain is:

```text
洛克王国：世界 PvP 精灵对战教练 Agent
```

Not:

```text
Pokemon team-building assistant
```

Existing Roco docs explicitly warn that Pokemon-style concepts may be borrowed
only as approximate analysis vocabulary, not as imported mechanics.

This must become a first-class Battle Wiki lint rule:

```text
No cross-game mechanic migration without explicit Roco evidence and approval.
```

## B Layer Must Be Persona-Free

The PM clarified that:

- B layer should be generic
- persona layer should be pluggable
- Enzo-style analysis habits do not belong in B

Therefore:

- B should encode battle doctrine, not character voice
- persona-specific reasoning overlays should be optional and downstream
- presentation/persona may shape style, but may not define generic battle truth

Current risk:

- `agent_core/synthesis.py` currently defaults to an
  `internal_enzo_pattern_pack`
- this is acceptable only as an internal sample or fixture
- it should not be treated as the target default B layer

The Battle Wiki thread should treat this as a design requirement:

```text
Default B doctrine must not reference Enzo, persona identity, character style,
or franchise-specific roleplay framing.
```

## Karpathy-Style LLM Wiki Direction

The PM proposed that the B layer should be an LLM Wiki rather than another
ordinary database table or a loose pile of markdown.

The target should follow the Karpathy LLM Wiki pattern:

```text
raw sources -> LLM-maintained interlinked wiki -> schema/governance -> compiled
AI-readable exports
```

Reference links:

- Karpathy LLM Wiki gist:
  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Example implementation / pattern summary:
  https://github.com/Pratiyush/llm-wiki

Important interpretation for Roco:

- do not use LLM Wiki as the primary source for exact facts
- do not replace SQLite battle-dex
- do use LLM Wiki for evolving doctrine, cases, methodology, and tactical taste
- use compilation/export so agents can consume it without reading a messy vault

## Relation To Existing LLM Wiki / RAG Necessity Review

The existing document:

- [specs/llm_wiki_rag_necessity_review.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md)

argues against building a full LLM Wiki for near-term exact fact retrieval.

That remains correct for `A` layer.

The new Battle Wiki proposal is different:

- it is for `B` layer doctrine and tactical understanding
- it should not replace battle-dex
- it can be introduced as a controlled knowledge asset rather than runtime
  dependency on day one

In short:

```text
No full LLM Wiki for A-layer facts.
Yes, consider LLM Wiki for B-layer doctrine.
```

## Suggested New Thread Objective

The new thread should not start by writing all doctrine content.

It should first produce:

1. Battle Wiki architecture spec
2. source/governance policy
3. page templates
4. lint rules
5. initial content map
6. ingest/update workflow
7. compile/export plan
8. PM editing protocol
9. evaluation questions for whether B improves synthesis

Only after those are stable should it start filling doctrine pages.

## Suggested First Deliverable

Create:

```text
specs/battle_wiki_architecture_spec.md
```

It should answer:

- what exact problem B Wiki solves
- what content classes exist
- what sources are allowed
- how raw/wiki/schema/compiled relate
- how confidence and provenance work
- how persona is excluded
- how A-layer facts are referenced without duplicated authority
- how this later feeds retrieval and live synthesis

