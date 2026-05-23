# A+B+C Architecture Book Authoring Spec

Date: 2026-04-25

Status: Draft v1

## 1. Purpose

Produce a **current-version, zero-context, Agent-first architecture book** for
Roco's `A + B + C` layered system.

This spec exists to make the authoring process executable, auditable, and
non-fictional.

The target book is not:

- a chat recap
- a memory-based retrospective
- a PM-facing lightweight brief
- a full historical transcript rewrite

The target book is:

- a current accepted design reference
- a source-mapped methodology document
- an Agent-usable architecture and governance reference
- a bounded record of why the current layered design exists

## 2. Core Rule

Do not invent missing history.

Every important claim in the final book must be one of:

- `normative`
  - directly supported by canonical contracts, architecture specs, governance
    docs, or accepted plans
- `implemented`
  - directly supported by runtime artifacts, code, tests, or accepted stage
    returns
- `inferred`
  - a careful synthesis from multiple first-hand local sources

If a claim cannot be placed in one of the three categories above, do not write
it as accepted design.

## 3. Output Goal

The authoring process must produce these artifacts:

### 3.1 Final book

Canonical target:

```text
docs/roco_abc_architecture_book_current_version.md
```

### 3.2 Mandatory working artifacts

```text
docs/roco_abc_source_inventory.md
docs/roco_abc_project_log_index.md
```

Optional scratch artifact if needed:

```text
docs/roco_abc_open_questions.md
```

The final book must not be written directly from memory without first
producing the source inventory and project-log index.

## 4. Scope

### In Scope

- current A/B/C layer definition
- why the split exists
- what each layer owns
- how directories map to layers
- how the current A/B bridge works
- what parts of C already exist
- key design trade-offs
- known current gaps
- authoritative local source mapping

### Out Of Scope

- reconstructing every historical conversation
- inventing unwritten motives
- promoting future design intent into current accepted architecture
- writing a complete product roadmap for all later phases
- replacing canonical specs with the summary book

## 5. Layer Definitions To Use

Use the current accepted split:

```text
A = exact facts / structured data / engine-facing truth
B = doctrine / wiki / compiled battle understanding
C = governance / maintenance / usage / enforcement policy
```

Do not rewrite the split unless local canonical material explicitly changes it.

## 6. Source Collection Plan

### 6.1 Source tiers

All local material must be collected into these tiers.

#### Tier 1: Normative canonical sources

Use these as primary authority:

- `meta/README.md`
- `meta/wiki/*.md`
- `specs/*architecture*`
- `specs/*contract*`
- `specs/*schema*`
- `specs/*plan*`
- `specs/*_spec.md`

These define:

- layer boundaries
- ownership
- accepted design direction
- explicit trade-offs

#### Tier 2: Implementation-reality sources

Use these to prove the design is real and to bound current capability:

- code under `advisor/`
- code under `agent_core/`
- `wiki/schema/*`
- `wiki/compiled/*`
- `data/runtime/*`
- tests
- accepted stage returns under `.launchpad/`

These define:

- what is actually implemented
- what bridge/runtime behavior exists today
- where current design is still incomplete

#### Tier 3: Decision-evolution sources

Use these to recover chronology and rationale without writing fiction:

- `log/project_log.md`
- `.launchpad/logs/decision_log.md`
- `.launchpad/logs/risk_log.md`
- handoff files
- convergence memos
- completion checks and stage returns when they materially changed design

These define:

- why some boundaries exist
- how the current version was reached
- which risks forced design tightening

### 6.2 Minimum canonical source set

The author must read these before drafting the final book:

1. `meta/README.md`
2. `meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`
3. `meta/wiki/compile_use_contract_2026-04-22.md`
4. `specs/battle_wiki_architecture_spec.md`
5. `specs/retrieval_architecture_spec.md`
6. `docs/source_control_policy.md`
7. `docs/battle_analysis_architecture.md`
8. `wiki/README.md`
9. `log/project_log.md` via targeted retrieval, not blind linear reading

If these cannot support a claimed section, gather more local material before
writing that section.

## 7. Project Log Retrieval Plan

`log/project_log.md` is likely long and noisy. Do not read it linearly first.

Use targeted retrieval.

### 7.1 Search themes

Search at least these keyword families:

- `A layer`, `A-layer`, `A 层`
- `B layer`, `B-layer`, `B 层`
- `C layer`, `C-layer`, `C 层`
- `wiki`
- `doctrine`
- `bridge`
- `mechanism`
- `retrieval`
- `compile`
- `enforcement`
- `database`
- `sqlite`
- `schema`
- `persona`
- `governance`

### 7.2 Transition keywords

Also search:

- `decision`
- `risk`
- `drift`
- `blocked`
- `revisit`
- `canonical`
- `moved`
- `deferred`

### 7.3 Retrieval method

Recommended pattern:

1. run `rg` on `log/project_log.md`
2. capture matching line numbers
3. reopen only bounded windows around the hits
4. index only the entries that materially support architecture or trade-off

Recommended command shape:

```bash
rg -n "A-layer|B-layer|C-layer|wiki|doctrine|bridge|retrieval|enforcement|sqlite|schema|persona|governance|decision|risk|drift|canonical|deferred" log/project_log.md
```

Then reopen bounded windows, for example:

```bash
sed -n '120,190p' log/project_log.md
```

### 7.4 Required output

The project-log pass must produce:

```text
docs/roco_abc_project_log_index.md
```

Each indexed item should include:

- date or heading
- theme
- why it matters
- whether later canonical docs absorbed it
- whether it should be cited directly or only used as rationale support

## 8. Working Artifact Format

### 8.1 `roco_abc_source_inventory.md`

Structure:

```text
# Roco A+B+C Source Inventory

## Canonical Layer Definition
- source
- role
- evidence type

## A-Layer
...

## B-Layer
...

## C-Layer
...

## A/B Bridge
...

## Known Gaps
...
```

For each entry include:

- path
- evidence tier
- short usage note
- whether it is normative / implemented / rationale

### 8.2 `roco_abc_project_log_index.md`

Structure:

```text
# Roco A+B+C Project Log Index

## Indexed Entries

### <date or heading>
- topic
- extracted conclusion
- how it should be used
- source window
```

Do not dump long raw log excerpts. Index them.

## 9. Final Book Design

The final book must be **Agent-first**.

Human-readable prose should exist, but only as a short front door. The main
body should optimize for stable machine and human retrieval.

### 9.1 Required file

```text
docs/roco_abc_architecture_book_current_version.md
```

### 9.2 Required top-level structure

The final book must use this order:

1. `Purpose`
2. `How To Read This Document`
3. `Document Status`
4. `Canonical Layer Definitions`
5. `Directory And Ownership Model`
6. `Why A+B+C Exists`
7. `A-Layer Design`
8. `B-Layer Design`
9. `C-Layer Design`
10. `A/B Bridge And Current Runtime Flow`
11. `Trade-Off Decisions`
12. `Known Gaps`
13. `Non-Goals`
14. `Canonical Source Map`

### 9.3 Required section template

Every major section from `A-Layer Design` onward must use this block pattern:

```markdown
## <Section Name>

### Current Decision
<accepted current-version conclusion>

### Why
<bounded rationale only>

### Directory Anchor
<which repo directories own this layer or concern>

### Canonical Sources
- <path>
- <path>

### Implemented Reality
<what is actually present in runtime/code/artifacts>

### Known Gaps
<what is not yet true or not yet complete>

### Non-Goals
<what this section does not authorize>
```

This is mandatory. Do not switch to essay-only structure.

## 10. Writing Rules

### 10.1 Distinguish claim type

The final book must explicitly separate:

- `Current Decision`
- `Implemented Reality`
- `Known Gaps`

Do not blur them into one paragraph.

### 10.2 Use source-backed statements

Every important conclusion must be traceable to local files.

If a conclusion is synthesized from multiple files, say so implicitly through
the `Canonical Sources` list.

### 10.3 Do not promote future work into current design

Examples of forbidden mistakes:

- writing future C-layer enforcement as already complete
- writing future file-backed persona system as already current runtime
- writing broad live doctrine maturity as current reality when only bounded
  bridge exists

### 10.4 Keep human front matter short

The front sections (`Purpose`, `How To Read This Document`, `Document Status`)
should be short.

Do not spend large word count on narrative setup.

## 11. Trade-Off Coverage Requirements

The final book must explicitly cover these trade-offs if sources support them:

- why A cannot be wiki-first
- why B cannot own exact facts
- why B must remain persona-free
- why C must be independent from both `data/` and `wiki/`
- why current architecture chose bounded A/B bridge before broader live doctrine
- why runtime downgrade rules matter when reviewed doctrine is missing

If any item lacks enough evidence, mark it as unresolved rather than inventing
an answer.

## 12. Synthesis Workflow

The authoring workflow must run in this order:

1. collect Tier 1 canonical sources
2. build `roco_abc_source_inventory.md`
3. run targeted `project_log` retrieval
4. build `roco_abc_project_log_index.md`
5. collect Tier 2 implementation evidence only for sections actually needed
6. draft the final book section by section
7. run a non-fiction pass:
   - remove unsupported claims
   - downgrade uncertain claims
   - separate normative vs implemented vs inferred
8. run an Agent-friendliness pass:
   - stable headings
   - short paragraphs
   - explicit section anchors
   - source lists present

Do not start step 6 before steps 2 and 4 exist.

## 13. Validation Checklist

The authoring task is complete only when all conditions below are true:

- `docs/roco_abc_source_inventory.md` exists
- `docs/roco_abc_project_log_index.md` exists
- `docs/roco_abc_architecture_book_current_version.md` exists
- every major section in the final book has `Canonical Sources`
- every major section distinguishes `Current Decision` from `Implemented Reality`
- no major conclusion depends only on transcript memory
- known future work is not written as current capability
- the final book is structurally Agent-friendly

## 14. Hard Reminder

This task is not to prove that the current design is perfect.

It is to record, without fiction:

- what the current accepted design is
- why it was split this way
- how far implementation has actually reached
- where the architecture is still incomplete
