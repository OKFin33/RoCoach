# LLM Wiki / RAG Necessity Review

Date: 2026-04-15

Owner: crawl / knowledge-base thread

Audience: main thread review

## Purpose

Clarify whether the project needs a full `LLM Wiki`, Markdown page layer, or vector RAG layer for the near-term advisor.

This memo is a scope-control recommendation. It does not request crawler expansion.

## Current State

The current battle-dex pipeline is best described as:

```text
structured wiki knowledge base substrate
```

Implemented or validated:

- wiki crawler artifacts
- template parser
- normalized species / move / derived ability candidates
- species move-pool resolution
- manual supplement layer
- move alias rules
- exclusion policy
- importer / resolver dry-run
- provenance through `wiki_source_refs` and `supplement_refs`
- artifact validators

Latest clean dry-run:

```text
data/importer_runs/2026-04-15Tfull_policy_b_alias_checked_dry_run
resolved_species_forms = 566
resolved_moves = 493
resolved_derived_abilities = 180
excluded_entities = 23
review_required_entities = 0
supplement_backed_entities = 9
unresolved_entities = 0
```

SQLite mutation was not performed by the crawl thread.

## What This Is Not

The current system is not a finished RAG system.

It does not yet provide:

- query decomposition over multiple retrieval branches
- vector index
- ranking / reranking
- context assembly runtime
- retrieval evaluation
- tactical case retrieval
- LLM-maintained Markdown wiki pages

The current system is also not a complete `LLM Wiki` as shown in generic architecture diagrams.

It lacks an LLM maintenance layer that automatically:

- generates entity pages
- suggests cross-links
- finds orphan pages
- detects stale references
- drafts update memos
- classifies mechanics gaps
- maintains a human-readable Markdown wiki

## Key Recommendation

Do not build a full LLM Wiki or full vector RAG layer now.

The near-term product target is:

```text
Agent-ready structured battle knowledge base
```

not:

```text
full Markdown LLM Wiki
```

and not:

```text
all-content vector RAG
```

## Why Full Vector RAG Is Not Necessary Now

Most near-term advisor questions are exact fact or relation questions:

- species stats
- form differences
- move type / category / energy cost / power
- ability text
- learnset membership
- source provenance
- exclusion / supplement status

These should be answered through deterministic structured lookup:

```text
SQLite / repository query / ID-based joins
```

Using embedding retrieval for these facts would be less stable and would reintroduce errors from stale wiki text.

Recent example:

- wiki text for the `花魁蜂后 -> 女王蜂` chain was wrong
- manual supplement corrected it to:
  - `一窝蜂 / 黄蜂后 / 花魁蜂后 = 虫群鼓舞 +10%`
  - `女王蜂 = 虫群突袭 +15%`
- a naive vector RAG path could retrieve the stale wiki statement and mislead the Agent
- the structured resolver path preserves provenance and applies the accepted correction

## Recommended Retrieval Shape

Keep the existing `hybrid local RAG` language, but interpret it narrowly:

```text
structured facts first
curated text second
embeddings later and only where justified
```

Near-term branches:

- `structured retrieval`
  - primary backend: battle-dex repository / SQLite
  - use for exact facts, joins, filters, provenance

- `curated doc retrieval`
  - primary backend: approved docs / mechanics supplement
  - use for mechanics explanations and policy context
  - can start as keyword / metadata lookup

- `case retrieval`
  - primary backend: tactical casebank after it exists
  - use for analogies, role priors, archetype reasoning
  - embeddings are optional later

## Markdown Wiki Page Layer

Full Markdown entity pages are not necessary for the near-term advisor.

Do not prioritize generating pages such as:

```text
精灵/女王蜂.md
技能/打湿.md
特性/虫群突袭.md
```

Those pages mainly serve:

- human browsing
- long-term documentation
- readable LLM context
- editorial workflows

They are not required for:

- exact fact lookup
- Agent tool calls
- resolver correctness
- importer validation

If Markdown is introduced, it should be selective and memo-oriented:

- mechanics notes
- conflict review memos
- drift summaries
- human-facing explanations for accepted manual supplements

## LLM Maintenance Layer

An LLM maintenance layer may be useful later, but the first version should be lightweight and job-based.

Do not build a platform.

Acceptable future jobs:

- `review_memo_generator`
  - input: unresolved / review_required / validation events
  - output: concise human review memo

- `drift_summary_generator`
  - input: old vs new crawl/importer artifacts
  - output: changed stats, move text, ability text, excluded/review changes

- `mechanics_gap_detector`
  - input: move/ability texts
  - output: mechanism terms that lack explanation docs
  - examples: `印记`, `蓄力`, `应对`, `连击`, `迅捷`, `魔力`

These jobs can output Markdown memos without creating a full Markdown wiki.

## Recommended Phase Order

### Phase 1: Agent-Ready Structured KB

Priority:

- stabilize battle-dex repository queries
- expose species / move / ability / learnset / provenance tools
- ensure manual supplement and alias rules are visible to Agent responses

### Phase 2: Minimal Mechanics Context

Priority:

- expose mechanics supplement to Agent
- keep it curated and small
- use keyword / metadata lookup first

### Phase 3: Review / Drift Memos

Priority:

- generate human review memos after new crawls
- summarize source changes
- flag stale wiki vs manual supplement conflicts

### Phase 4: Optional Selective Markdown Pages

Only if human maintenance cost becomes painful.

Generate pages selectively for:

- complex mechanics
- important corrected entities
- public-facing explanations

### Phase 5: Optional Embeddings

Only when there is enough non-structured corpus:

- mechanics docs
- version notes
- community guides
- tactical cases

Do not embed the structured battle-dex tables as the primary factual access path.

## Main Thread Review Questions

Please decide:

1. Should `hybrid local RAG` in existing specs be interpreted as `SQL-first structured retrieval + optional curated text retrieval`, not as a mandate for vector RAG?
2. Should full Markdown entity-page generation be explicitly deferred?
3. Should near-term LLM maintenance be limited to review/drift/mechanics-gap memo jobs?
4. Should Agent implementation prioritize battle-dex repository tools over Markdown wiki generation?

## Proposed Decision

Accept the following:

```text
Near-term target = Agent-ready structured KB, not full LLM Wiki.
```

```text
Vector RAG = optional later for docs/cases, not primary path for battle facts.
```

```text
Markdown Wiki pages = deferred unless human maintenance pressure justifies them.
```

```text
LLM maintenance layer = lightweight memo jobs, not a platform.
```

