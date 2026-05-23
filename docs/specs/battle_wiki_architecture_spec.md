# Battle Wiki Architecture Spec

Date: 2026-04-20

Status: Draft v1

Owner surface: B-layer Battle Wiki thread

## 1. Purpose

The Battle Wiki is Roco's source-controlled B-layer doctrine system for
`洛克王国：世界` PvP advisory reasoning.

It exists to give the advisor durable, reviewable battle methodology that can
be consumed by LLM synthesis without allowing the model to become the source of
truth.

The product reasoning equation is:

```text
Final advisory reasoning = Synthesize(A, B)
```

Where:

- `A` is the grounded analytical substrate:
  - deterministic engine output
  - SQLite battle-dex facts
  - approved structured records
  - bounded retrieval snippets
  - confidence, warning, and refusal boundaries
- `B` is the generic battle doctrine layer:
  - mechanics interpretation
  - team-building methodology
  - role and archetype methodology
  - tactical cases and counterexamples
  - recommendation taste and bad-advice rules
  - uncertainty handling rules

The Battle Wiki governs `B`.

## 2. Non-Goals

The Battle Wiki must not become:

- a second species, move, or ability database
- a replacement for `data/runtime/battle_dex.sqlite`
- a replacement for deterministic engine rules
- an unreviewed scrape dump
- a community-meta database
- a persona or roleplay doctrine store
- an Enzo-style default reasoning pack
- a Pokemon doctrine transplant
- raw LLM output presented as authority

Exact species, move, ability, type-chart, source-provenance, and structured
fact queries belong to `A`, not `B`.

## 3. Repository Placement

The Battle Wiki should live at the project root:

```text
wiki/
```

Reason:

- `data/` is the A-layer data and runtime artifact surface
- `wiki/` is the B-layer doctrine and editorial surface
- `docs/` is for ordinary project documentation, reports, and primers
- `specs/` is for system-level architecture, contracts, and policies

This architecture spec remains in:

```text
specs/battle_wiki_architecture_spec.md
```

because it is a system contract. Wiki page templates and compiler/lint
protocols should live under:

```text
wiki/schema/
```

Canonical governance for Battle Wiki no longer lives under `wiki/meta/`.
It now lives under:

```text
meta/wiki/
```

Historical handoff packets may remain under `wiki/meta/`, but should be treated
as thread-context artifacts rather than current governance authority.

## 4. Layer Model

The wiki follows a Karpathy-style LLM Wiki pattern:

```text
raw sources -> reviewed wiki pages -> schema/governance -> compiled exports
```

With current repo ownership split:

```text
wiki/       = B-layer doctrine assets
meta/wiki/  = C-for-B governance
specs/      = implementation-facing contracts and handoff docs
```

Target layout:

```text
wiki/
  README.md
  meta/
    handoff_2026-04-20/
  raw/
    pm_notes/
    source_notes/
    battle_reviews/
    version_observations/
  pages/
    mechanics/
    team_building/
    roles/
    archetypes/
    recommendation_taste/
    counterexamples/
    casebank/
    glossary/
  schema/
    page_contracts.md
    confidence_policy.md
    provenance_policy.md
    lint_rules.md
    ingest_protocol.md
    compile_protocol.md
  compiled/
    llms.txt
    llms-full.txt
    chunks.jsonl
    graph.json
    manifest.yaml
```

Canonical governance lives outside this tree:

```text
meta/
  wiki/
```

### 4.1 `raw/`

`raw/` stores safe, reviewable source notes, not unbounded dumps.

Allowed examples:

- PM-written notes
- reviewed summaries of public materials
- battle review notes
- version observation memos
- links and citation metadata
- source conflict notes

Forbidden examples:

- API keys, cookies, tokens, sessions
- private raw chat logs
- copyrighted full-text dumps
- large raw scrape outputs
- unreviewed HTML dumps
- screenshots or media without usage rights and review notes

`raw/` is not automatically committed to Git. Only safe, reviewed, non-sensitive
source notes should be committed.

### 4.2 `pages/`

`pages/` contains reviewed doctrine pages. These pages are human-editable and
LLM-consumable, but they do not own exact facts.

Each page must distinguish:

- doctrine claim
- supporting source
- confidence level
- A-layer references when exact facts are involved
- known uncertainty
- last review date

### 4.3 `schema/`

`schema/` defines the wiki's local compiler/editorial protocol.

It should contain:

- page templates
- confidence policy
- provenance policy
- lint rules
- ingest protocol
- compile protocol

These files are not optional decoration. They are part of the defense against
doctrine rot, persona drift, and cross-game contamination.

But they are not the only governance layer. Battle Wiki governance also
includes root-level `meta/wiki/` material such as:

- decision convergence
- mechanism registry
- compile/use contract

### 4.4 `compiled/`

`compiled/` contains AI-readable exports generated from reviewed pages.

Compiled artifacts may later feed:

- curated document retrieval
- case retrieval
- live model-backed synthesis
- evaluation prompts

Compiled artifacts must include a manifest with:

- build timestamp
- source page list
- page hashes
- compiler version
- excluded pages
- stale page warnings

Runtime consumers should prefer compiled outputs over ad hoc vault traversal.

## 4.5 `meta/wiki/`

`meta/wiki/` is the canonical governance surface for Battle Wiki.

It should contain:

- Battle Wiki decision convergence notes
- mechanism registry
- compile/use contract
- future review/update policy for Battle Wiki usage

It should not be treated as doctrine content itself.

## 5. Content Classes

The first Battle Wiki should support these content classes.

### 5.1 Mechanics Interpretation

Purpose:

- explain game-native mechanics and their strategic implications
- mark what is confirmed, provisional, or speculative

Initial terms:

- 魔力
- 能量
- 聚能
- 应对
- 攻击 / 状态 / 防御技能
- 迅捷 / 先手 / 速度
- 印记
- 增益 / 减益
- 换入 / 脱离 / 周转

Mechanics pages may explain interpretation. They may not override engine rules.

### 5.2 Team-Building Methodology

Purpose:

- describe how to reason about a team as a structure
- define useful diagnosis patterns and patch logic

Initial topics:

- 核心输出
- 增益手 / 减益手
- 反印 / 驱散
- 功能位
- 联防支点
- 节奏位
- 魔力与能量资源交换

### 5.3 Role Methodology

Purpose:

- define Roco-native role vocabulary
- prevent single-label species thinking

Rules:

- role is team-contextual
- species baseline, selected set, and team role must remain separate
- same species may occupy different roles in different teams
- role claims must state confidence

### 5.4 Archetype Methodology

Purpose:

- describe team-level patterns as hypotheses, not immutable classes

Rules:

- archetype labels are diagnostic shortcuts
- labels must not erase set-level or matchup-level uncertainty
- low-confidence archetype claims must not drive hard recommendations

### 5.5 Recommendation Taste

Purpose:

- define what counts as useful advice
- prevent vague, unsupported, or overconfident recommendations

The wiki should define when to:

- give one hard recommendation
- preserve multiple alternatives
- refuse unsupported advice
- mark tactical speculation
- warn that A-layer facts are missing

### 5.6 Counterexamples

Purpose:

- store anti-patterns and bad-advice examples
- teach the synthesis layer what not to infer

Examples:

- treating a species as one fixed role
- recommending a patch that worsens resource tempo
- importing Pokemon mechanics into Roco
- overriding battle-dex facts with stale wiki text

### 5.7 Casebank

Purpose:

- teach patterns, not memorize answers
- provide representative team and set cases

The casebank should follow `specs/tactical_casebank_spec.md`.

Initial target:

- `20-30` team cases
- `30-60` species set examples

Each case must distinguish:

- species baseline
- selected set
- team role
- team context
- confidence tier
- source reference

## 6. Source Policy

Allowed source classes:

- PM-reviewed notes
- internal Roco specs and primers
- reviewed battle cases
- curated public source summaries
- version observation memos
- structured A-layer references

Conditionally allowed:

- community claims with explicit low-confidence labeling
- LLM-generated drafts if treated only as drafts and reviewed before merge

Forbidden as authority:

- unreviewed community dumps
- uncited screenshots
- anonymous one-off teamlists
- Pokemon or other game mechanics by analogy alone
- stale raw wiki text when contradicted by battle-dex or manual supplements
- persona doctrine

## 7. Provenance And Confidence

Every doctrine page must include front matter or an equivalent structured block:

```yaml
title: ""
content_class: ""
status: draft
confidence: provisional
sources: []
a_layer_refs: []
last_reviewed: ""
reviewed_by: ""
persona_free: true
```

Allowed confidence levels:

- `confirmed`
- `provisional`
- `low_confidence`
- `deprecated`

Rules:

- `confirmed` claims require strong project evidence or PM review
- `provisional` claims may guide explanation but must preserve uncertainty
- `low_confidence` claims may not drive hard recommendations by default
- `deprecated` claims remain only to explain drift or rejected advice

## 8. Cross-Game Contamination Control

The Battle Wiki is for `洛克王国：世界`.

It must not import mechanics from:

- Pokemon
- legacy 洛克王国 assumptions
- other monster battlers

unless a Roco project document explicitly approves the analogy.

Mandatory lint rule:

```text
No cross-game mechanic migration without explicit Roco evidence and approval.
```

Pokemon-derived terms such as `check`, `counter`, `balance`, `offense`, or
`stall` may be used only as approximate analysis vocabulary when the page
defines the Roco-specific meaning.

## 9. Persona Exclusion

Default B-layer doctrine must be persona-free.

Forbidden in default wiki pages:

- Enzo identity
- persona voice
- character roleplay framing
- persona-specific taste presented as generic truth
- style directives for final user-facing language

Persona materials may be referenced only in separation-boundary documents or
persona-layer integration specs.

If a future persona wants to consume B, the allowed direction is:

```text
generic B doctrine -> persona overlay -> presentation
```

Never:

```text
persona habit -> generic B doctrine
```

## 10. A-Layer Reference Rules

B pages may reference A-layer facts, but may not duplicate authority.

Allowed:

- "See battle-dex for current move data."
- "This doctrine assumes the Engine-provided weakness profile."
- "This case uses species IDs from battle-dex snapshot X."

Forbidden:

- hand-maintained species stat tables in wiki pages
- hand-maintained move power / energy tables in wiki pages
- wiki pages overriding SQLite or engine output
- stale source text winning over manual supplements

If a page needs exact data, it should reference:

```text
data/runtime/battle_dex.sqlite
specs/battle_dex_sqlite_schema_v1.sql
data/reference/
data/manual_supplements/
```

or the future repository/API contract that exposes those facts.

## 11. Retrieval And Synthesis Integration

Near-term use:

- no runtime dependency required
- use the architecture spec and initial pages as reviewable design assets

Mid-term use:

- compile reviewed pages into `wiki/compiled/`
- expose curated B snippets to synthesis through bounded retrieval
- keep exact facts routed through A-layer tools

Long-term use:

- live model-backed synthesis consumes:
  - `A`: engine, SQL, structured retrieval, confidence boundaries
  - `B`: compiled doctrine snippets and case patterns
  - optional persona overlay downstream

Synthesis may:

- interpret
- prioritize
- explain tradeoffs
- generate concrete advisory judgement

Synthesis may not:

- invent facts outside A
- override Engine / SQL / approved-doc truth
- erase confidence boundaries
- use persona doctrine as default B

## 12. Compile Safety

The compiler must avoid turning stale pages into false authority.

Required checks:

- exclude pages with `status: draft` unless explicitly requested
- warn on missing `last_reviewed`
- warn on missing sources
- warn on low-confidence pages
- record source page hashes
- record A-layer snapshot references when used
- fail on forbidden cross-game terms unless explicitly waived
- fail on persona contamination markers in default pages

The compiled manifest must be reviewable before runtime adoption.

## 13. PM Editing Protocol

PM edits should operate at the page and case level, not through runtime code.

Minimum workflow:

1. add or update raw note
2. draft or update wiki page
3. assign confidence
4. attach source references
5. run lint
6. compile preview
7. review changed compiled snippets
8. merge

No doctrine claim should become default runtime context without a reviewed page
and a compiled manifest entry.

## 14. First Ten Candidate Pages

Initial pages should be architecture-bearing, not content-heavy.

Recommended first ten:

1. `mechanics/magic_and_energy.md`
2. `mechanics/response_counterplay.md`
3. `mechanics/move_categories.md`
4. `team_building/defensive_structure.md`
5. `team_building/resource_tempo.md`
6. `roles/contextual_role_assignment.md`
7. `archetypes/archetype_labels_are_hypotheses.md`
8. `recommendation_taste/hard_recommendation_rules.md`
9. `counterexamples/cross_game_contamination.md`
10. `casebank/case_annotation_rules.md`

## 15. Golden Evaluation Questions

The first evaluation set should test whether B improves synthesis without
weakening A-layer truth.

Examples:

- Does the answer refuse to import Pokemon mechanics?
- Does the answer keep exact facts in A?
- Does the answer distinguish role from species identity?
- Does the answer mark provisional mechanics as provisional?
- Does the answer avoid persona voice in default reasoning?
- Does the answer produce a concrete recommendation only when supported?
- Does the answer preserve alternatives when confidence is low?
- Does the answer explain why a patch improves team structure?
- Does the answer use cases as analogies rather than facts?
- Does the answer warn when meta data is missing?

## 16. Open Decisions

Still needs PM-control decision:

- final Git worktree boundary for `Roco/`
- whether `data/runtime/battle_dex.sqlite` is committed short-term
- whether `wiki/compiled/` artifacts are committed or generated locally
- exact migration timing for `docs/battle_wiki_ctx_pack/`
- first PM-reviewed doctrine source batch

## 17. Acceptance Criteria

This architecture is ready for implementation when:

- `wiki/` exists at project root
- page contracts exist under `wiki/schema/`
- provenance and confidence policies are explicit
- cross-game contamination lint exists
- persona exclusion lint exists
- first doctrine pages can be drafted without duplicating A-layer facts
- compiled output format is defined before runtime integration
- PM-control has repaired the Git boundary
