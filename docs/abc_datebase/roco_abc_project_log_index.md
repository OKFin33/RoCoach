# Roco A+B+C Project Log Index

## Purpose

This file indexes the `log/project_log.md` entries that materially explain the
current A+B+C architecture.

This is not a full chronology. It is a retrieval-oriented index for later
agents.

## Index

### 2026-04-13 - Domain Primer Accepted With Provisional Mechanisms

- Window: `log/project_log.md` around lines `560-610`
- Theme: domain grounding before schema stabilization
- Why it matters:
  - shows that external domain material was accepted only as provisional
    mechanism content
  - meta/environment claims were explicitly kept low-confidence
- Current relevance:
  - still relevant as origin for “facts and mechanisms require controlled
    confidence”
- Status:
  - absorbed into later A/B split and confidence discipline

### 2026-04-13 - P1a Field Discovery Direction Locked

- Window: `log/project_log.md` around lines `980-1038`
- Theme: source-first schema discovery
- Why it matters:
  - records early anti-contamination motive
  - wiki reconnaissance was bounded to field discovery before ingestion
  - marks the first strong “do not import other-game schema assumptions”
    decision
- Current relevance:
  - still relevant as source of A-layer raw-first discipline
- Status:
  - partially superseded in wording, but still foundational

### 2026-04-14 - P1b Minimal Battle Dex Schema Drafted

- Window: `log/project_log.md` around lines `1202-1260`
- Theme: A-layer structured data model
- Why it matters:
  - formalizes raw-first, source-traceable battle-dex schema
  - records `derived_ability` modeling choice
  - keeps source-channel complexity in storage instead of polluting the first
    analytical layer
- Current relevance:
  - directly supports current A-layer design
- Status:
  - current and still canonical alongside `specs/battle_dex_schema.yaml`

### 2026-04-14 - Structured Supplement And SQLite Write Spec / Write Path

- Window: `log/project_log.md` around lines `1963-2058`
- Theme: A-layer runtime substrate becomes real
- Why it matters:
  - explains why structured supplement and SQLite write contract were separated
    from crawl artifacts
  - proves SQLite write path was implemented with transactional, validated
    boundary
- Current relevance:
  - directly supports the statement that A-layer is not paper architecture
- Status:
  - current as implementation history; exact counts later changed, boundary did
    not

### 2026-04-14 - Lightweight RAG And Tactical Casebank Direction Confirmed

- Window: `log/project_log.md` around lines `2155-2265`
- Theme: A/B retrieval split origin
- Why it matters:
  - states battle dex is `RAG-ready substrate`, not complete RAG
  - formalizes `structured retrieval`, `doc retrieval`, and `case retrieval`
  - records that role judgement should be evidence-backed and uncertainty-bearing
- Current relevance:
  - highly relevant; later retrieval architecture spec inherits this split
- Status:
  - current in spirit; later Battle Wiki work makes doc branch more explicit

### 2026-04-14 - SQL vs Embedding Retrieval Boundary Recorded

- Window: `log/project_log.md` around lines `2234-2254`
- Theme: exact-fact lookup vs semantic retrieval
- Why it matters:
  - locks `SQL-first` for structured battle-dex facts
  - reserves embeddings for docs/cases later
- Current relevance:
  - still current; important for explaining why A is not vector-first
- Status:
  - current

### 2026-04-15 - LLM Wiki / RAG Necessity Review Memo Prepared

- Window: `log/project_log.md` around lines `2420-2460`
- Theme: why full LLM wiki platform was deferred
- Why it matters:
  - near-term target was structured KB first
  - warns that stale wiki text can mislead naive RAG
  - supports “do not overbuild vector RAG or entity-page wiki first”
- Current relevance:
  - partially current; later B-layer Battle Wiki was adopted in a bounded,
    doctrine-only form rather than full platform form
- Status:
  - conceptually superseded by bounded B-layer wiki, but still important for
    trade-off explanation

### 2026-04-16 - Retrieval Implementation Status And Phase A Eval Request

- Window: `log/project_log.md` around lines `2688-2835`
- Theme: implemented retrieval reality snapshot
- Why it matters:
  - proves current doc retrieval began as bounded curated rule table
  - explicitly records what did not exist: embeddings, FTS, case retrieval,
    web retrieval
- Current relevance:
  - still useful as implemented baseline before later mechanism-aware bridge
- Status:
  - partially superseded by 2026-04-21 mechanism-aware retrieval hardening

### 2026-04-21 - P1a Mechanism Guard Hardening + Preliminary Audit

- Window: `log/project_log.md` around lines `43-110`
- Theme: first safe A/B bridge
- Why it matters:
  - adds mechanism-aware retrieval from A-layer ability/move text into reviewed
    B-layer pages
  - missing reviewed pages now force explicit downgrade
  - removes persona contamination from default synthesis doctrine
- Current relevance:
  - directly current
- Status:
  - current; later followed by mechanism coverage completion

### 2026-04-21 - Battle Wiki Mechanism Coverage Completion Pass

- Window: `log/project_log.md` around lines `100-179`
- Theme: B-layer coverage expansion + governance traceability
- Why it matters:
  - expands mechanism lexicon and reviewed page coverage
  - records governance artifacts for later debugging
- Current relevance:
  - current
- Status:
  - current, with later governance docs becoming more canonical

### 2026-04-22 - Battle Wiki Thread Closure / Governance Consistency Fix

- Window: `log/project_log.md` around lines `184-244`
- Theme: C-layer for Battle Wiki becomes canonical
- Why it matters:
  - records `meta/wiki/` as canonical governance location
  - adds compile/use contract
  - updates architecture doc to reflect governance ownership
- Current relevance:
  - directly current; strongest historical support for C-layer maturity
- Status:
  - current

## Retrieval Guidance

When another agent needs deeper chronology, start with these themes:

- A-layer origin:
  - `P1a Field Discovery Direction Locked`
  - `P1b Minimal Battle Dex Schema Drafted`
  - `Structured Supplement And SQLite Write Spec`
- Retrieval split origin:
  - `Lightweight RAG And Tactical Casebank Direction Confirmed`
  - `SQL vs Embedding Retrieval Boundary Recorded`
  - `Retrieval implementation status and Phase A eval request`
- B-layer bridge origin:
  - `P1a Mechanism Guard Hardening + Preliminary Audit`
  - `Battle Wiki Mechanism Coverage Completion Pass`
- C-layer governance origin:
  - `Battle Wiki Thread Closure / Governance Consistency Fix`

## Use Rule

- Use this file to find relevant windows in `log/project_log.md`.
- Do not quote the project log as if it were the final architecture contract
  when a later `meta/` or `specs/` source exists.
