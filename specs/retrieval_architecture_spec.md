# Retrieval Architecture Spec

## Purpose

Define the near-term retrieval architecture for the advisor.

This project should use `hybrid local RAG`, not a monolithic vector platform.

## Retrieval Principle

Different knowledge classes require different retrieval methods.

The system should not force one retrieval mechanism onto all data.

## Retrieval Branches

### 1. Structured Retrieval

Primary backend:

- `SQLite`

Purpose:

- exact battle-dex facts
- typed entity lookup
- filters and aggregations

Examples:

- species profile
- move details
- ability text
- learnset membership
- provenance

Required behavior:

- deterministic
- exact or rule-driven
- no semantic similarity fallback for factual fields

### 2. Doc Retrieval

Primary sources:

- `docs/domain_primer.md`
- mechanics supplement
- taxonomy docs
- scoring and confidence docs

Purpose:

- retrieve explanatory or methodological context
- support semantic interpretation

Phase A implementation:

- curated snippets
- metadata filters
- optional keyword / FTS retrieval

Phase B implementation:

- add embeddings
- hybrid keyword + embedding retrieval

### 3. Case Retrieval

Primary source:

- tactical casebank

Purpose:

- retrieve representative tactical analogies
- support role and archetype priors
- provide pattern-based evidence for team-conditional judgement

Phase A implementation:

- metadata lookup
- curated selection

Phase B implementation:

- case-level embeddings
- set-level embeddings
- optional lightweight reranking

## Query Decomposition

The advisor should split incoming requests into one or more of:

- `fact_query`
- `mechanics_query`
- `case_query`
- `structure_query`

Examples:

- “权杖-V 适合干什么”
  - fact query
  - mechanics query
  - case query
- “这队联防有啥洞”
  - structure query
- “这个精灵在这队里像不像副C”
  - fact query
  - case query
  - mechanics query

## Retrieval Metadata

Every retrieved item should carry:

- `source_type`
- `source_path` or `entity_ref`
- `topic`
- `confidence_tier`
- `version`
- `retrieval_reason`

Case retrieval should additionally carry:

- `case_id`
- `archetype`
- `role_labels`

## Context Assembly Rules

The context builder should merge retrieval outputs into three labeled blocks:

- `facts`
- `mechanics`
- `cases`

Rules:

- facts first
- mechanics second
- cases third
- no block should override a higher-trust block

Maximum context budget should stay intentionally small.

Default target:

- `facts`: all directly relevant structured entities
- `mechanics`: `2-5` snippets
- `cases`: `1-3` representative cases

## Why Current State Is Not Full RAG

Current repo state includes:

- SQLite battle-dex
- curated doc snippets
- report harness
- advisor doc retrieval implemented as a bounded curated rule table in
  `advisor/retrieval.py`

Missing pieces for a complete retrieval layer:

- battle-dex-aware retriever interfaces beyond direct repository calls
- retrieval metadata normalization beyond current snippet fields
- query decomposition beyond intent-specific tool routing
- case retrieval
- context assembly contract
- retrieval evaluation

Therefore current state is:

- `RAG-ready substrate`
- `Phase A curated local retrieval`

not:

- complete RAG runtime

## Current Implementation Snapshot

As of `2026-04-16`, advisor doc retrieval is implemented in:

- `advisor/retrieval.py`

Mechanism:

- a static `_RULES` tuple stores curated `DocContextSnippet` objects
- each rule has:
  - approved snippet content
  - allowed `analysis_types`
  - keyword triggers
- retrieval lowercases the query
- rules are filtered by `analysis_type`
- rules get a small score from:
  - baseline guardrail topics
  - keyword matches
- results are sorted by score and topic
- duplicate topics are removed
- output is capped by `limit`

Current snippet topics:

- `engine_grounding`
- `confidence_guard`
- `dual_type_baseline`
- `team_conditional_roles`
- `scope_boundary`

Current properties:

- deterministic
- bounded
- local
- source-aware
- confidence-aware
- no embeddings
- no FTS
- no case retrieval
- no web retrieval

Current limitation:

- snippet corpus is tiny and manually coded
- retrieval is keyword/rule based, not semantic
- there is no retrieval eval harness yet
- no external document chunking/indexing exists
- docs are not automatically parsed into snippets

## Embedding Policy

Embeddings are likely needed later, but only for:

- docs
- tactical casebank

Embeddings are not the primary retrieval mechanism for:

- exact stats
- exact moves
- exact abilities
- learnset membership

## Evaluation Requirements

Retrieval evaluation must separately check:

- factual correctness
- snippet relevance
- case relevance
- context sufficiency
- unsupported-claim leakage

## Non-Goals

This retrieval system does not need:

- web search by default
- large-scale vector infrastructure
- graph retrieval in v1
- cross-session memory search
