# Battle Wiki Console Handoff

Date: 2026-04-22

## Purpose

This document is a development handoff for the console/main thread.

It is not the canonical home for Battle Wiki governance. Canonical governance
remains under:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/`

This file exists because the next tasks are implementation-facing and must be
resumable across sessions by reading repo documents rather than chat memory.

## Read Order

Read the following in order before taking action:

1. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md`
2. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md`
3. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/mechanism_registry_2026-04-21.md`
4. `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/mechanism_review_checklist_2026-04-21.md`
5. `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
6. `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`

Optional but useful context:

7. `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/pages/mechanics/`
8. `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/pages/casebank/firefox_wingking_balance_team_reconciliation.md`

## Current State

Battle Wiki first-pass infrastructure is already usable:

- reviewed mechanics pages compile into `wiki/compiled/`
- runtime mechanism lexicon can auto-retrieve reviewed pages
- missing reviewed pages no longer force silent improvisation
- mechanism coverage has been expanded beyond the initial bounded bridge

This means the Battle Wiki thread should no longer be treated as a pure content
drafting thread.

The immediate work now splits into:

- `Battle Wiki thread`
  - B content maintenance
  - C-for-B governance notes
  - registry hygiene
  - casebank growth
- `console/main thread`
  - runtime/system integration
  - A-layer schema planning and implementation
  - eval execution
  - long-lived engineering contracts

## What Is Already Done

The following mechanism families are now both reviewed and runtime-wired:

- `迅捷 / 先手 / 速度`
- `印记`
- `天气`
- `应对`
- `传动`
- `迸发`
- `蓄力`
- `奉献`
- `萌化`
- `灼烧`
- `冻结`
- `中毒`
- `寄生`
- `聚能`
- `魔力`
- `换人 / 离场 / 脱离 / 回场 / 入场 / 替换上场 / 主动离场`
- specific mark names and mark-operation terms
- weather-name aliases including:
  - `雨天`
  - `沙暴`
  - `雪天`
  - `暴风雪`

Important current reviewed rules include:

- `雪天` and `暴风雪` refer to the same in-game weather mechanism
- `冻结` should be treated as a persistent per-unit status:
  whenever `current_hp` or frozen-threshold state changes, check whether
  `current_hp <= frozen_hp`
- `灼烧` is settled as fire-type damage and uses the reviewed timing model
- `复活` is still intentionally deferred as a standalone runtime token

## What Should Stay In The Battle Wiki Thread

The Battle Wiki thread should continue owning only these:

1. refresh registry documents so they match current runtime and reviewed-page
   state
2. add `meta/wiki` compile/use governance docs for Battle Wiki consumption
3. continue casebank and reconciliation pages
4. maintain reviewed doctrine coverage and parent-topic boundaries
5. design eval cases and scoring criteria for battle-doctrine quality

The Battle Wiki thread should not be the place that directly implements A-layer
schema changes or system-wide evaluator plumbing.

## What Must Be Picked Up By Console/Main

These are the main-thread tasks that should now proceed.

### 1. Plan A-Layer Mechanism Structuring

Goal:

- identify which reviewed mechanics are now stable enough to deserve structured
  A-layer representation

Initial candidate families:

- weather registry
- mark registry
- entry/exit event taxonomy
- status registry
- mechanism hooks for:
  - `迅捷`
  - `传动`
  - `迸发`
  - `蓄力`
  - `奉献`
  - `萌化`

Expected output:

- a design/spec proposal, not yet a rushed schema rewrite

### 2. Promote Battle Wiki Compile/Use Contract Into Explicit Engineering Contract

Goal:

- turn the current de facto linkage between reviewed pages, compiled exports,
  and runtime retrieval into an explicit contract

At minimum, the main thread should decide:

- what fields runtime may rely on from compiled pages
- how mechanism lexicon ownership is split between governance docs and code
- what downgrade behavior is mandatory when reviewed coverage is missing
- what counts as `reviewed + provisional` safe usage

Expected output:

- an implementation-facing spec under `specs/`
- later runtime enforcement work, if needed

### 3. Execute A Minimal System Eval

Goal:

- verify that Battle Wiki actually improves grounded analysis instead of only
  adding documentation

Suggested eval buckets:

- mechanism explanation retrieval
- mark/weather interpretation
- entry/exit timing interpretation
- bad-team detection vs over-coherent hallucination
- case reconciliation against known shared builds

Expected output:

- a small runnable eval plan
- not a giant benchmark

### 4. Prepare LLM-Maintained Wiki Workflow As Engineering Design

Goal:

- prepare the future workflow without prematurely opening uncontrolled
  auto-expansion

The main thread should design:

- proposal flow for page updates
- page ownership / review boundaries
- change provenance requirements
- safe auto-link suggestion boundaries

This is design work first, not immediate automation rollout.

## Constraints

- Do not collapse A/B/C boundaries again.
- Do not move canonical governance out of `meta/`.
- Do not treat `specs/` as canonical doctrine storage.
- Do not market current Battle Wiki as final mature battle understanding.
- Keep `reviewed + provisional` usable, but visibly bounded.

## Recommended Immediate Console Deliverables

If the console thread wants the smallest useful next step, do these in order:

1. write a spec for A-layer mechanism structuring candidates
2. write a spec for Battle Wiki compile/use contract at engineering level
3. define and run a minimal eval set

Do not start with broad new wiki content expansion.

## Suggested Resume Prompt

Use the text below in the console/main thread if a direct resume prompt is
needed:

```text
Read these files first, in order:

1. /Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_console_handoff_2026-04-22.md
2. /Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md
3. /Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/mechanism_registry_2026-04-21.md
4. /Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md
5. /Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py

You are not resuming the Battle Wiki content-authoring thread.
You are resuming the console/main implementation thread.

Your job is to:

1. convert current Battle Wiki state into implementation-facing next steps
2. keep A/B/C boundaries intact
3. propose A-layer mechanism-structuring candidates
4. define an engineering-level Battle Wiki compile/use contract
5. define a minimal eval plan that tests whether wiki-backed retrieval improves
   analysis quality

Do not spend this turn expanding doctrine pages unless required for contract
clarity.
```
