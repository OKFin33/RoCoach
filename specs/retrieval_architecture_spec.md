# Retrieval Architecture Spec

## Purpose

Define the near-term retrieval architecture for the advisor.

This project should use `hybrid local RAG`, not a monolithic vector platform.

Architectural placement:

- RoCoach is an Agentic runtime with planner, grounding/tool, reasoning/synthesis,
  validation, continuity, and presentation loops.
- Runtime depth should be:
  `plan -> ground -> validate packet -> maybe retrieve more / ask clarification
  -> synthesize -> grade trace / answer`.
- Retrieval is an implementation capability inside the grounding/tool loop.
- Retrieval is not a standalone product path and not a user-visible answer
  module.
- Retrieved facts, docs, and cases are evidence inputs to Agent synthesis.
- Normal user answers must be produced by the Agent terminal synthesis path, not
  by a retrieval module concatenating snippets.

## Retrieval Principle

Different knowledge classes require different retrieval methods.

The system should not force one retrieval mechanism onto all data.

The system should also not force retrieval to own the answer. Retrieval owns
evidence selection; the Agent loop owns interpretation and final response.

Retrieval must also be packet-aware. If retrieved evidence is insufficient for
the planned answer, the runtime should either perform a bounded retrieve-more
iteration or ask a concise clarification before synthesis.

Retrieval must also be claim-aware. The grounding packet handed to synthesis
must map each grounded claim to evidence ids, or mark that claim as provisional
or unsupported. A retrieval hit without a claim-support map is not enough to
authorize a user-visible tactical answer.

## Retrieval Capabilities Inside The Agent Loop

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

Status:

- Future/conditional for V1.
- Not required for P12 acceptance.
- Use only when an explicit casebank/D-layer artifact is enabled and the packet
  carries matching case evidence.

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

- `evidence_id`
- `source_type`
- `source_path` or `entity_ref`
- `topic`
- `confidence_tier`
- `version`
- `retrieval_reason`
- `content_digest`

Every grounded claim passed to synthesis should carry:

- `claim_id`
- `claim_text_digest`
- `supporting_evidence_ids`
- `support_level`: `confirmed`, `provisional`, or `unsupported`
- `provisional_reason` when not confirmed

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
- no block renders normal chat copy directly
- assembled context returns to Agent synthesis as grounding material
- assembled context must pass packet validation before terminal synthesis

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
- `retrieval-as-grounding-tool`

not:

- complete RAG runtime
- independent retrieval answer runtime

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
- case relevance only when case retrieval is enabled
- context sufficiency
- unsupported-claim leakage

Minimum V1 fixture:

- fixed query or query sequence
- expected structured facts
- expected doc topics or snippet ids
- expected evidence ids in the grounding packet
- no required case evidence unless case retrieval is explicitly enabled
- forbidden unsupported claims
- packet sufficiency decision: synthesize, retrieve more, clarify, or degrade

## Non-Goals

This retrieval system does not need:

- web search by default
- large-scale vector infrastructure
- graph retrieval in v1
- cross-session memory search
