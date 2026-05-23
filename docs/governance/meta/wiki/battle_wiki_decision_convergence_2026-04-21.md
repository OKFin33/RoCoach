# Battle Wiki Decision Convergence

Date: 2026-04-21

## Purpose

This memo converges the Battle Wiki discussion after the bounded first A/B
bridge and the mechanism-guard hardening pass.

Its job is not to expand doctrine content. Its job is to lock the decisions
that define what Battle Wiki is, what it is not, and what the next smallest
useful step should be.

## Current Problem Statement

The project now has a bounded first bridge from:

- A-layer evidence in SQLite / structured records
- to reviewed B-layer mechanism pages
- with explicit downgrade when reviewed mechanism pages are missing

That bridge is good enough for a first constrained use, but not yet mature
enough for broad, stable, live doctrine reasoning.

The current bottleneck is no longer "write more wiki pages". The bottleneck is
decision clarity:

- what exactly counts as B-layer doctrine
- what belongs in A instead
- what is really C-layer usage or enforcement logic
- which mechanics are reviewed enough for current use
- what governance shape prepares a later LLM-maintained wiki workflow without
  opening the floodgates too early

## A / B / C Layer Split

### A Layer

`A` is the exact-fact layer.

Examples:

- SQLite battle-dex
- engine-facing structured data
- approved structured facts
- future executable mechanism fields

Directory anchor:

```text
data/
```

### B Layer

`B` is the doctrine layer.

Examples:

- mechanics interpretation
- team-building methodology
- role and archetype understanding
- tactical cases
- uncertainty and recommendation-taste doctrine

Directory anchor:

```text
wiki/
```

### C Layer

`C` is the governance, maintenance, and usage-policy layer.

Examples:

- review lifecycle
- compile/export contract
- mechanism lexicon ownership
- retrieval / enforcement boundaries for how Agent uses B
- project rules for how A and B are maintained

Directory anchor:

```text
meta/
```

## What A Stores Versus What B Stores

The rule is:

```text
facts go to A
doctrine goes to B
```

This does not mean mechanics live only in one layer.

For mechanisms such as weather, marks, swift, burst, transmission, and charge:

- A should eventually own the exact structured rule fields
- B should own the doctrine interpretation, strategic meaning, and uncertainty
  boundaries

Example:

- A may later store exact fields such as trigger conditions, timing hooks,
  stack rules, or energy gates
- B explains what those mechanics mean for team analysis, advice quality, and
  tactical interpretation

## Reviewed Mechanism Pages

### Definition

A reviewed mechanism page is a reviewed B-layer doctrine unit that:

- explains one mechanism or one tightly related mechanism cluster
- is allowed into compiled exports
- is allowed to be retrieved by runtime
- preserves provenance, confidence, and A-layer boundary
- does not claim engine authority it does not actually have

It is not:

- a raw source note
- an A-layer fact table
- a runtime validator rule
- a persona overlay

### Current Reviewed Mechanism Pages

Current reviewed pages under `wiki/pages/mechanics/` now include at least:

- `burn_timing_and_full_combustion.md`
- `marks_and_persistence.md`
- `morale_and_revive.md`
- `pvp_stat_normalization_and_iv_selection.md`
- `response_counterplay.md`
- `speed_priority_and_swift.md`
- `type_bloodline_move_boundary.md`
- `weather_and_field_effects.md`
- `transmission_and_skill_slots.md`
- `burst_trigger_and_entry_actions.md`
- `charge_and_release.md`
- `bug_contribution_fengxian.md`
- `degeneration_and_menghua.md`
- `status_effects_and_persistence.md`
- `entry_exit_and_replacement_timing.md`
- `energy_actions_and_focus.md`

### Mechanism Tokens Already Recognized By Runtime

Current mechanism lookup covers these tokens:

- `迅捷`
- `先手`
- `速度`
- `印记`
- `天气`
- `应对`
- `传动`
- `迸发`
- `蓄力`
- `奉献`
- `萌化`

Of these, the following already have reviewed pages and runtime wiring:

- `迅捷`
- `先手`
- `速度`
- `印记`
- `天气`
- `应对`
- `传动`
- `迸发`
- `蓄力`
- `奉献`
- `萌化`

Decision status:

- these five were added as reviewed mechanism pages
- they entered as `reviewed + provisional`, not as `confirmed`

### Likely Additional Mechanisms Not Yet In The Runtime Lexicon

The runtime lexicon has since expanded beyond the first bounded set.

Already wired additional coverage now includes at least:

- state/status terms such as `灼烧`, `冻结`, `中毒`, `寄生`
- action/timing terms such as `脱离`, `离场`, `回场`, `入场`, `换人`
- resource/timing terms such as `聚能`, `魔力`
- mark-specific terms such as `星陨印记`, `龙噬印记`, `光合印记`, `蓄电印记`
- weather aliases such as `雨天`, `沙暴`, `雪天`, `暴风雪`

Decision:

- maintain a formal mechanism registry
- distinguish:
  - runtime-wired topics
  - reviewed-but-parent-represented topics
  - reviewed-only topics
  - explicitly deferred standalone work

## Mechanism Lexicon

The mechanism lexicon is the mapping layer from detected mechanism terms to
reviewed mechanism topics.

Example shape:

```text
token -> reviewed mechanism topic/page
```

Its role is:

1. let runtime detect mechanism-bearing ability / move text automatically
2. force retrieval of the relevant reviewed page when it exists
3. force downgrade when the token exists but no reviewed page exists

Decision:

- lexicon meaning and topic ownership belong to C governance
- runtime consumption logic is implemented code, but the governed mapping is a
  meta concern, not an ad hoc hidden implementation detail

## Current State Update

Since this memo was first written, the following have also been completed:

- Battle Wiki governance moved canonically under `meta/wiki/`
- a refreshed mechanism registry now tracks actual runtime coverage
- a dedicated Battle Wiki compile/use contract was added under:
  - `meta/wiki/compile_use_contract_2026-04-22.md`
- a console/main-thread handoff spec was added under:
  - `specs/battle_wiki_console_handoff_2026-04-22.md`

This means the memo should now be read as:

- the decision-convergence baseline
- not the single source of truth for current mechanism coverage

For current coverage and use rules, prefer:

- `meta/wiki/mechanism_registry_2026-04-21.md`
- `meta/wiki/compile_use_contract_2026-04-22.md`

## Why `meta/` Is The C Layer

The project should use:

```text
data/  = A
wiki/  = B
meta/  = C
```

This is cleaner than burying C under `wiki/meta/`, because:

- `data/` and `wiki/` are content/asset directories
- `meta/` is the rule layer above content
- future governance for other project domains can be added without pretending
  everything is "part of wiki"

Subdirectories:

```text
meta/
  data/
  wiki/
```

Where:

- `meta/data/` governs A
- `meta/wiki/` governs B

Historical handoff context packs may stay under `wiki/meta/`, but new canonical
governance should move to root `meta/`.

## How C Relates To B

`meta/wiki/` contains C-layer rules for B.

Examples:

- what qualifies as a reviewed mechanism page
- review lifecycle
- confidence policy
- compile/export contract
- mechanism lexicon policy
- how Agent may use reviewed B pages

These are not B doctrine pages themselves. They are governance and usage rules
about B.

## Weather / Marks / Similar Mechanics And The A-Layer Roadmap

Battle rules such as weather and marks should not remain B-only forever.

Decision:

- B may explain them now
- A should eventually gain structured representations for them

Examples of A-layer targets:

- canonical weather names and duration
- mark polarity, stack rules, and persistence
- exact trigger timing
- exact replacement / clearing rules
- exact swift / burst / charge execution fields

This avoids forcing prose-only pages to act like engine truth.

## Three Workflow Patterns Clarified

### 1. More Open LLM-Maintained Wiki Workflow

Meaning:

- LLM is allowed to propose updates, conflicts, splits, merges, and candidate
  reviewed changes more proactively instead of only editing pages one by one on
  explicit command

Value:

- faster growth
- lower editorial friction
- better support for a doctrine layer that changes with the metagame

Risk:

- confidence drift
- boundary drift
- early noisy interpretations becoming canon too quickly

Decision:

- the project should prepare for this workflow
- but should not enable open-ended autonomous expansion yet

### 2. Automatic Cross-Link Expansion

Meaning:

- the system automatically proposes or adds links between related mechanism,
  role, archetype, and case pages
- it may also surface missing-topic candidates when many pages reference the
  same unresolved mechanism

Value:

- better knowledge graph shape
- easier retrieval
- easier gap discovery

Risk:

- wrong relationships become sticky
- noisy early graph structure hardens too early

Decision:

- allow semi-automatic link suggestion and gap detection
- do not allow broad automatic formal-page expansion yet

### 3. Heavier Wiki-First Authoring Model

Meaning:

- wiki becomes the primary authoring surface for doctrine content, and many
  downstream consumers read compiled wiki exports

Value:

- natural fit for tactical doctrine
- easier PM/LLM co-maintenance
- faster doctrine iteration than strict schema-first authoring

Risk:

- wiki can be mistaken for exact fact authority
- prose can outrun A-layer formalization
- runtime may over-trust narrative text

Decision:

- B may be wiki-first
- A must not be wiki-first
- C should stay contract-first / governance-first

## Current Locked Decisions

1. Use `data/`, `wiki/`, and `meta/` as the A/B/C directory anchors.
2. Treat `meta/` as the project-level governance / usage / maintenance layer.
3. Treat `meta/data/` as A governance.
4. Treat `meta/wiki/` as B governance and B-usage policy.
5. Promote `传动`, `迸发`, `蓄力`, `奉献`, and `萌化` to reviewed mechanism
   pages with `provisional` confidence.
6. Create and maintain a mechanism registry that distinguishes:
   - currently reviewed topics
   - runtime-wired tokens
   - candidate mechanisms not yet wired
7. Prepare for an LLM-maintained wiki workflow, but do not enable open-ended
   autonomous page expansion yet.
8. Allow semi-automatic cross-link suggestion, but not broad uncontrolled
   auto-page generation.
9. Keep A as the long-term owner of exact structured battle-rule fields.
10. Keep `specs/` as a development-process directory; only elevate enduring
    governance assets into `meta/`.

## Immediate Next Deliverables

Recommended smallest useful follow-up work:

1. add a formal mechanism registry under `meta/wiki/`
2. add reviewed provisional pages for:
   - `传动`
   - `迸发`
   - `蓄力`
   - `奉献`
   - `萌化`
3. add a short `meta/wiki/compile_and_usage_contract.md`
4. later decide which weather/mark/swift fields should be formalized into A

## Explicit Non-Decisions

Do not decide yet:

- the full long-term doctrine ontology
- broad autonomous wiki maintenance
- complete casebank schema
- full product-wide C-layer directory structure beyond `meta/data/` and
  `meta/wiki/`
- final live-model-backed doctrine runtime strategy
