# Agent Team Analysis And Mechanism Guard Spec

## Purpose

This request is for the **main development thread**.

It hardens team-analysis behavior so the product stops making two avoidable
classes of mistake:

1. silently assuming the user's team is strong or internally coherent
2. expanding mechanism-heavy reasoning without retrieving the mechanism itself

This is a bounded runtime / retrieval / validation request.

Do not expand product scope.
Do not add web retrieval.
Do not add embeddings or vector DB.
Do not redesign the whole advisor architecture.
Do not touch crawler / import pipelines unless a direct dependency is required
for a reviewed wiki page compile.

## Context

Dogfood findings from the Battle Wiki thread:

- the analyst can still drift into "this team probably has a plan" mode
- when a trait or move explicitly references a special mechanism such as
  `迅捷`, `传动`, `迸发`, `印记`, or `天气`, runtime retrieval does not
  automatically fetch the reviewed mechanism page
- current `advisor/retrieval.py` is keyword-thin and only queries against the
  user message, not against retrieved ability / move text
- current reviewed wiki does not yet include a reviewed `迅捷` mechanics page,
  so the system must degrade honestly instead of improvising

Current repository reality:

- A-layer facts exist through SQLite species / move / ability retrieval
- B-layer first wiki exists under `wiki/`
- compiled wiki exports exist under `wiki/compiled/`
- current runtime tools do not yet consume compiled wiki by mechanism-key
- current species semantics are intentionally shallow and provisional
- team semantics / case retrieval remain deferred

## Product Problem Statement

The current product can produce a plausible-sounding explanation while missing
one of the following:

- the supplied team may simply be weak or incoherent
- the answer mentions a mechanism term but never loaded the mechanism page
- a raw source note exists for a mechanism, but no reviewed page exists

This creates a specific failure mode:

```text
trait text mentions 迅捷
-> model recognizes it as important
-> runtime never retrieves the reviewed mechanism page
-> answer fills the gap from memory or inference
```

This is not acceptable for the intended A+B+LLM design.

## Required Fixes

### P1. Team analysis must default to unknown-quality input

Current bad prior:

- user-provided six-slot team is implicitly treated as likely coherent

Required behavior:

- the runtime and synthesis layer must treat any supplied team as
  `unknown_quality_team` by default
- analysis must test coherence; it must not assume coherence
- final verdict must support at least:
  - `coherent`
  - `partially_coherent`
  - `goodstuff_without_clear_plan`
  - `internally_conflicted`
  - `insufficient_evidence`

Implementation direction:

- introduce a bounded team-semantic output contract or equivalent intermediate
  structure with:
  - `candidate_plan`
  - `supporting_evidence`
  - `counterevidence`
  - `coherence_verdict`
  - `coherence_score`
- if counterevidence is empty, the runtime should not allow a strong
  "self-consistent strong team" verdict

### P1. Mechanism-bearing ability and move text must trigger automatic retrieval

Current failure:

- `retrieve_doc_context` reads the user query only
- it does not scan ability text or move effect text already fetched from A

Required behavior:

- after `get_species_profile` and `get_species_available_moves`, runtime must
  scan:
  - ability effect text
  - selected move effect text
  - highly salient move names
- if mechanism tokens are found, runtime must auto-retrieve the matching
  reviewed mechanics page or approved snippet

Minimum initial mechanism lexicon:

- `迅捷`
- `先手`
- `速度`
- `传动`
- `迸发`
- `蓄力`
- `印记`
- `天气`
- `应对`
- `奉献`
- `萌化`

Implementation direction:

- create a local mechanism lexicon mapping tokens to reviewed wiki topics / page
  ids
- retrieval must not depend only on user wording
- mechanism expansion should run automatically when A-layer evidence mentions the
  token

### P1. Answers must not expand unreviewed mechanisms as confirmed doctrine

Current failure:

- raw source notes may contain a candidate explanation, but there may be no
  reviewed mechanism page

Required behavior:

- if a mechanism token is detected but no reviewed mechanism page exists, the
  answer must degrade explicitly:
  - say the term is present in trait / move text
  - say the reviewed wiki does not yet define it fully
  - avoid a deterministic explanation of its exact execution rule

Implementation direction:

- validator should check:
  - if output mentions a mechanism token in explanatory mode
  - but evidence lacks the matching reviewed mechanism source
  - then reject and retry or force a downgraded explanation

### P2. Add a reviewed mechanics page for speed / priority / swift

Required new reviewed page:

```text
wiki/pages/mechanics/speed_priority_and_swift.md
```

Minimum page coverage:

- speed vs priority ordering
- distinction between speed, priority, and `迅捷`
- whether `迅捷` depends on active switch
- whether passive replacement after death triggers it
- energy requirement
- only one swift move firing rule, if confirmed
- confidence labels and unresolved timing questions

Source inputs may include:

- `wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md`
- `wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md`
- A-layer ability and move text that explicitly mention `迅捷`

Do not overclaim beyond reviewed evidence.

### P2. Team-analysis synthesis must include explicit counterevidence

Required behavior:

- any team identity claim must include at least one of:
  - what does not fit the plan
  - what the plan still lacks
  - what evidence weakens the optimistic interpretation

This is the main protection against random teams being dressed up as
high-quality strategy.

Implementation direction:

- add a required `counterevidence` field to any team-semantics intermediate
- synthesis should surface it in concise form
- absence of counterevidence should downgrade certainty

### P2. Mechanism citation must be visible in evidence

Required behavior:

- when mechanism-aware retrieval runs, at least one mechanism evidence item must
  appear in the trace / evidence output
- the product should not hide all mechanism evidence behind engine items

Implementation direction:

- reserve at least one evidence slot for mechanism retrieval when such retrieval
  occurred

## Files Likely In Scope

- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/runtime.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/agent_core/synthesis.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/agent_core/contracts.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_advisor.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/tests/test_retrieval.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/pages/mechanics/speed_priority_and_swift.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/schema/compile_wiki.py`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`

Possible contract files if needed:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_tool_contracts.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/reasoning_synthesis_contract.yaml`

Do not add case retrieval, embeddings, vector DB, web-in-loop, GUI, or crawler
work.

## Validation Requirements

Minimum:

```bash
.venv/bin/python -m unittest tests.test_advisor
.venv/bin/python -m unittest tests.test_retrieval
python3 wiki/schema/compile_wiki.py
```

Required new or updated tests:

- team analysis does not require coherence and can output a non-coherent verdict
- mechanism tokens in ability text trigger mechanism retrieval
- mechanism tokens in move text trigger mechanism retrieval
- if a mechanism page is missing, output degrades explicitly instead of
  fabricating exact rules
- if output explains `迅捷` without matching mechanism evidence, validator
  rejects and retries / downgrades
- evidence output shows at least one mechanism retrieval item when mechanism
  retrieval ran

## Expected Deliverable

Return:

1. files changed
2. behavior changes by required fix
3. tests run and exact results
4. whether the runtime now protects against:
   - strong-team prior
   - missing mechanism lookup
   - unsupported mechanism overclaiming

## Copy-paste Prompt For Main Development Thread

```text
Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_team_analysis_mechanism_guard_spec.md` first.

You are the main development thread. Execute exactly this bounded runtime hardening request.

Fix:
1. team analysis must default to unknown-quality input instead of assuming the user supplied a coherent strong team
2. mechanism-bearing ability / move text must trigger automatic reviewed-mechanism retrieval
3. when no reviewed mechanism page exists, the answer must degrade explicitly instead of improvising exact rules
4. add a reviewed mechanics page for speed / priority / swift
5. team-semantic output must include explicit counterevidence
6. visible evidence should include mechanism retrieval when it ran

Do not add case retrieval, embeddings, vector DB, web-in-loop, GUI, or ingestion redesign.
Run the required tests and update `log/project_log.md`.

Return files changed, behavior changes, tests run, and whether the three target protections now hold:
- no strong-team default prior
- no missing mechanism lookup
- no unsupported mechanism overclaiming
```
