# Roco A+B+C Architecture Book (Current Version)

## Purpose

This document records the current accepted `A+B+C` architecture for Roco.

It is written for later agents that need to understand:

- why the project is split into A, B, and C
- what each layer owns
- what is already implemented
- what is still missing
- which local files are canonical for each claim

This is an Agent-first reference, not a retrospective essay.

## How To Read This Document

- Prefer `Current Decision` and `Canonical Sources` over any historical note.
- Treat `Implemented Reality` as the current runtime snapshot, not the full
  design contract.
- Treat `Known Gaps` as active boundaries, not invitations to widen scope.
- If this document conflicts with a later accepted `meta/` or `specs/` source,
  the later accepted source wins.

## Document Status

- Scope: current-version architecture book
- Coverage: A-layer facts, B-layer doctrine, C-layer governance/usage
- Excludes:
  - full persona pipeline details
  - LaunchPad control-plane design
  - exhaustive project chronology
- Evidence model:
  - `Normative`: accepted contract / architecture / governance
  - `Implemented`: code or runtime artifact
  - `Inferred`: synthesis across multiple first-hand sources

## Canonical Summary

### Current Decision

Roco now uses an internal `A+B+C` architecture where:

- `A` = exact facts / structured data / engine-facing truth
- `B` = doctrine / wiki / compiled battle understanding
- `C` = governance / maintenance / usage / enforcement policy

This internal shorthand is useful, but it is not a claim that all three layers
are homogeneous databases.

### Why

- A single structured database is insufficient for battle doctrine,
  recommendation taste, and uncertainty-bearing mechanism explanation.
- A single wiki-like layer is unsafe for exact battle facts.
- A third governance layer is required so B-layer content does not silently
  become an unbounded prose heap or a second source of truth.

### Directory Anchor

- `data/` -> A-layer facts and runtime artifacts
- `wiki/` -> B-layer doctrine content and compiled exports
- `meta/` -> C-layer governance, maintenance, and usage policy
- `specs/` -> cross-layer contracts and bounded architecture decisions

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_architecture_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/compile_use_contract_2026-04-22.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/source_control_policy.md`

### Implemented Reality

- A-layer runtime exists as `data/runtime/battle_dex.sqlite`
- B-layer reviewed pages compile into `wiki/compiled/*`
- runtime doc retrieval consumes reviewed B-layer mechanism pages through
  `advisor/retrieval.py`
- missing reviewed pages trigger downgrade instead of silent improvisation

### Known Gaps

- C-layer enforcement is still partial, not complete
- case retrieval exists architecturally, but is not yet a mature runtime branch
- full live model-backed doctrine reasoning is not yet complete

### Non-Goals

- do not treat C as merely “misc docs”
- do not treat B as a second fact database
- do not treat persona as part of the current B-layer default doctrine

## Origin: Why This Architecture Exists

### Current Decision

The current A+B+C split was not adopted at project start. It emerged after the
project first stabilized field discovery, raw-first schema design, SQL-first
fact retrieval, and later recognized that structured facts alone could not carry
doctrine or explanation quality.

This section is an `Inferred` synthesis from multiple first-hand local sources.

### Why

The project faced three distinct pressures:

1. exact fact correctness for battle data
2. doctrine and mechanism interpretation that could not be reduced to flat
   fields
3. maintenance and usage rules so doctrine would remain bounded, reviewed, and
   persona-free

### Directory Anchor

- early origin material lives in `log/project_log.md`
- mature A/B/C decisions live under `meta/` and `specs/`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md`

### Implemented Reality

Historical log evidence shows the sequence:

- 2026-04-13:
  - field discovery was locked before ingestion to prevent cross-game schema
    contamination
  - wiki was treated as the primary structured source for early discovery, not
    yet as a B-layer doctrine system
- 2026-04-14:
  - minimal battle-dex schema and SQLite write path made A-layer real
  - retrieval was split into structured/doc/case branches
  - SQL-first vs embedding boundary was explicitly recorded
- 2026-04-15:
  - a full LLM wiki / vector RAG platform was judged unnecessary for the
    near-term advisor
- 2026-04-21 to 2026-04-22:
  - Battle Wiki became the bounded B-layer doctrine surface
  - governance moved canonically under `meta/wiki/`

### Known Gaps

- the exact moment the project conceptually switched from “wiki-centric source
  strategy” to “A facts + B doctrine + C governance” is inferred from multiple
  first-hand sources rather than recorded in one single acceptance memo

### Non-Goals

- do not retell the entire thread history
- do not treat early wiki-first discovery wording as the current final model

## A-Layer Design

### Current Decision

A-layer owns exact facts, structured storage, and engine-facing truth.

Its job is to provide deterministic or source-traceable battle facts, not free
interpretation.

### Why

Exact battle facts require:

- typed schema
- provenance
- clean repository interfaces
- deterministic lookup and joins

These are not the strengths of a freeform wiki or semantic retrieval layer.

### Directory Anchor

- `data/runtime/`
- `data/manual_supplements/`
- `specs/battle_dex_schema.yaml`
- `specs/battle_dex_sqlite_schema_v1.sql`
- repository/runtime access in `advisor/`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/source_control_policy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

### Implemented Reality

The runtime A-layer currently exists as SQLite.

Rechecked during authoring:

- `species_form = 566`
- `move = 493`
- `derived_ability = 180`
- `species_move_pool = 21974`

The accepted A-layer design includes:

- raw-first, source-traceable schema
- provenance fields
- `derived_ability` because ability evidence was initially embedded in species
  pages rather than clean standalone ability pages
- repository-owned SQL access boundary instead of scattered inline SQL

### Known Gaps

- not every mechanic is yet normalized into structured A-layer fields
- some doctrine-relevant semantics still live only in B-layer reviewed pages
- A-layer is a usable runtime substrate, not a finished total knowledge system

### Non-Goals

- A-layer does not own doctrine interpretation
- A-layer does not own persona behavior
- A-layer should not be replaced by embeddings or freeform wiki lookup for exact
  claims

## B-Layer Design

### Current Decision

B-layer is the Battle Wiki: a reviewed, compiled doctrine layer for battle
understanding.

It is generic, persona-free, and explicitly separate from exact fact storage.

### Why

Some battle knowledge is not well represented as exact rows:

- mechanism interpretation
- team-building methodology
- role and archetype doctrine
- recommendation taste
- counterexamples and failure modes

This knowledge still needs a stable, reviewable, retrievable home.

### Directory Anchor

- `wiki/pages/`
- `wiki/compiled/`
- `wiki/README.md`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_architecture_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`

### Implemented Reality

B-layer is implemented as reviewed markdown pages compiled into runtime-readable
artifacts.

Rechecked during authoring:

- `python3 wiki/schema/compile_wiki.py` returned `compiled 23 reviewed pages`
- compiled reviewed pages currently include:
  - mechanics doctrine
  - casebank pages
  - role taxonomy
  - team-building doctrine
  - recommendation-taste material

The compiler enforces:

- reviewed metadata presence
- persona-free rule
- required sections for reviewed non-casebank pages
- directory README inventory drift checks

### Known Gaps

- current reviewed pages are all still `confidence=provisional` in the compiled
  manifest
- B-layer is sufficient for a bounded first bridge, not for a fully mature
  live-model doctrine system
- coverage depth for teams/cases/taste is still materially thinner than A-layer
  exact facts

### Non-Goals

- B-layer is not a second SQLite battle dex
- B-layer is not an entity-page encyclopedia for every species/move/ability
- B-layer is not a persona store
- B-layer must not import cross-game mechanics without explicit boundary text

## C-Layer Design

### Current Decision

C-layer owns governance, maintenance, usage policy, and enforcement rules for
how B-layer content is created, compiled, and consumed.

### Why

Without C-layer:

- B-layer drifts into arbitrary prose
- reviewed and unreviewed content mix together
- runtime can silently consume untrusted pages
- future agents cannot tell what is canonical governance vs raw content

### Directory Anchor

- `meta/`
- `meta/wiki/`
- contracts in `specs/`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/compile_use_contract_2026-04-22.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`

### Implemented Reality

Current C-layer functions already implemented:

- reviewed-only compile boundary
- mandatory downgrade when reviewed mechanism page is missing
- canonical governance location under `meta/wiki/`
- mechanism-token mapping in runtime retrieval
- compiler lint for persona contamination and directory inventory drift

### Known Gaps

- C-layer today is strongest for Battle Wiki compile/use governance
- broader doctrine usage enforcement is still incomplete
- claim-to-evidence contracts, richer auditability, and broader evaluation loops
  are not yet fully built out

### Non-Goals

- C-layer is not a content layer
- C-layer is not persona runtime governance by default
- C-layer should not be reduced to “just docs” or “just comments”

## Directory And Ownership Model

### Current Decision

Directory ownership follows layer responsibility, not file type alone.

### Why

The project uses markdown, YAML, SQL, Python, and generated artifacts across
multiple layers. File format alone is not enough to infer ownership.

### Directory Anchor

- `data/`
- `wiki/`
- `meta/`
- `specs/`
- `advisor/`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/source_control_policy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/README.md`

### Implemented Reality

Ownership should currently be read as:

- `data/`
  - A-layer facts, supplements, importer artifacts, runtime SQLite
- `wiki/pages/`
  - B-layer reviewed doctrine pages
- `wiki/compiled/`
  - B-layer machine-consumable compiled exports
- `meta/wiki/`
  - C-layer governance for Battle Wiki
- `specs/`
  - cross-layer contracts, schemas, and bounded implementation plans
- `advisor/`
  - runtime bridge and retrieval consumption code

### Known Gaps

- some historical documents in `docs/` still explain earlier architectural
  stages and must not automatically outrank newer `meta/` governance
- not every future governance concern has yet been normalized under `meta/`

### Non-Goals

- do not infer “markdown means wiki/B-layer”
- do not infer “spec means only future plan”

## A/B Bridge And Current Runtime Flow

### Current Decision

Current advisory reasoning is a bounded bridge from A-layer facts into B-layer
reviewed doctrine, not a freeform all-corpus RAG stack.

### Why

The system needs doctrine support without sacrificing exact-fact correctness.

### Directory Anchor

- `advisor/retrieval.py`
- `wiki/compiled/`
- `data/runtime/battle_dex.sqlite`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/compile_use_contract_2026-04-22.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

### Implemented Reality

Current bridge behavior:

- exact facts come from SQLite / repository access
- doc retrieval remains bounded and local
- mechanism-aware retrieval scans A-layer ability text and move effect text for
  known mechanism tokens
- if a matching reviewed mechanism page exists in compiled B-layer exports, its
  doctrine snippet can be injected into context
- if the token exists but no reviewed page exists, runtime must downgrade
  explicitly instead of inventing doctrine

Current runtime retrieval is therefore:

- SQL-first for structured facts
- curated/rule-based for doc retrieval
- mechanism-aware for reviewed Battle Wiki pages
- not embedding-first
- not full case-retrieval-first

### Known Gaps

- case retrieval is architectural, not mature runtime reality
- no full ranking/reranking stack
- no broad automatic chunk selection over arbitrary docs
- no complete doctrine execution layer yet

### Non-Goals

- do not describe the current system as “full RAG”
- do not describe current bridge as fully mature live doctrine reasoning

## Trade-Off Decisions

### Current Decision

The current architecture is shaped by explicit trade-offs rather than by trying
to maximize every capability at once.

### Why

This project needed to stay useful early without collapsing correctness or
creating an unmaintainable knowledge system.

### Directory Anchor

- `meta/wiki/`
- `specs/`
- `log/project_log.md`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

### Implemented Reality

Key accepted trade-offs:

- `A over freeform text for exact facts`
  - reason: provenance, joins, deterministic lookup, lower stale-text risk
- `B over trying to force doctrine into flat schema`
  - reason: mechanism interpretation, role doctrine, recommendation taste, and
    counterexamples need richer reviewed text structures
- `C over unmanaged wiki usage`
  - reason: reviewed-only compile, downgrade rules, and governance location are
    required to keep B bounded
- `SQL-first over embedding-first`
  - reason: most near-term advisor queries are exact fact or relation queries
- `bounded Battle Wiki over full LLM wiki platform`
  - reason: full platform work was premature; current B-layer focuses on
    reviewed doctrine pages and compile/use rules
- `persona-free B-layer over style-driven doctrine`
  - reason: doctrine must remain generic and not collapse into a specific
    persona pack

### Known Gaps

- some earlier documents still reflect a stronger wiki-first or lighter-doc
  posture from before Battle Wiki became a formal B-layer
- current trade-off set may evolve again if casebank and evaluation layers
  mature significantly

### Non-Goals

- do not retroactively pretend the project always had a clean A+B+C model
- do not erase early SQL-vs-RAG or wiki-vs-DB tensions; they explain why the
  current boundaries exist

## Current Runtime Snapshot

### Current Decision

The book should record a compact runtime snapshot so later agents do not have to
rediscover whether the architecture is real or still hypothetical.

### Why

This project has multiple historical design documents. The runtime snapshot
prevents later readers from confusing a future plan with a current capability.

### Directory Anchor

- `data/runtime/battle_dex.sqlite`
- `wiki/compiled/manifest.yaml`
- `advisor/retrieval.py`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/data/runtime/battle_dex.sqlite`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/compiled/manifest.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`

### Implemented Reality

Current snapshot captured during authoring:

- A-layer SQLite:
  - `species_form = 566`
  - `move = 493`
  - `derived_ability = 180`
  - `species_move_pool = 21974`
- B-layer compile:
  - `compiled 23 reviewed pages`
  - `excluded 0 pages`
- runtime retrieval:
  - has curated rule snippets
  - has mechanism lexicon
  - loads compiled wiki manifest/chunks
  - supports mechanism-aware reviewed-page lookup

### Known Gaps

- compiled page count may change later; the architectural point is the existence
  of the reviewed compile/use pipeline, not the exact page count

### Non-Goals

- do not overfit the architecture description to these exact counts

## Known Gaps And Deferred Scope

### Current Decision

The architecture book must explicitly preserve current incompleteness rather
than implying a finished universal knowledge system.

### Why

Overstating maturity would mislead later implementation and review work.

### Directory Anchor

- `log/project_log.md`
- `specs/retrieval_architecture_spec.md`
- `meta/wiki/compile_use_contract_2026-04-22.md`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_architecture_refactor_plan.md`

### Implemented Reality

Still incomplete or deferred:

- broader case retrieval maturity
- embedding retrieval for docs/cases
- full doctrine usage enforcement beyond the current mechanism-guard level
- richer claim-to-evidence contracts
- complete evaluation loops for doctrine obedience
- full live model-backed doctrine reasoning
- future persona source adapter / ingestion pipeline beyond current A+B+C core

### Known Gaps

- some future work is already specced elsewhere, but that does not make it part
  of the current A+B+C runtime

### Non-Goals

- do not pull future persona-creation or source-adapter work into the current
  A+B+C definition
- do not claim casebank or embeddings are mature just because they appear in
  architecture splits

## Persona Boundary Relative To A+B+C

### Current Decision

Persona is downstream of the current default A+B+C doctrine path.

Persona is not the current B-layer authority.

### Why

Battle doctrine must remain generic and trustworthy even when the product later
supports multiple personas or deeper persona pipelines.

### Directory Anchor

- `specs/p1_architecture_refactor_plan.md`
- `specs/persona_doctrine_contract.yaml`
- `wiki/README.md`

### Canonical Sources

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_architecture_refactor_plan.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_doctrine_contract.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/README.md`

### Implemented Reality

- B-layer default doctrine is persona-free
- earlier persona contamination in synthesis doctrine was explicitly removed
- later persona/source-ingestion specs exist, but belong to separate downstream
  tracks

### Known Gaps

- later product/runtime stages may integrate persona more deeply into
  presentation or reasoning inputs, but that is still constrained by fact-lock
  rules and does not redefine current B-layer ownership

### Non-Goals

- do not treat `Enzo` or any other persona as canonical B-layer doctrine
- do not treat persona source adapter specs as proof that persona files are part
  of the current A+B+C runtime

## Canonical Source Map

### Current Decision

Later agents should not have to rediscover the right entrypoints.

### Canonical Sources

- Primary source inventory:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/roco_abc_source_inventory.md`
- Project log retrieval index:
  - `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/roco_abc_project_log_index.md`

### Implemented Reality

Use these as the shortest practical read order:

1. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md`
2. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`
3. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_architecture_spec.md`
4. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/compile_use_contract_2026-04-22.md`
5. `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/source_control_policy.md`
6. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md`
7. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml`
8. `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md`
9. `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/roco_abc_project_log_index.md`
10. `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

### Non-Goals

- do not start from random `docs/` notes if the goal is to understand current
  accepted architecture
