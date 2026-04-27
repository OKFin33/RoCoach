# Battle Wiki Decision Convergence Prompt

Use this prompt to resume the separate Battle Wiki thread after the latest P1a
hardening / audit work.

```text
Read the following context first, in order:

1. /Users/okfin3/project/GitHub/OKFin33/Roco/wiki/meta/handoff_2026-04-20/README.md
2. /Users/okfin3/project/GitHub/OKFin33/Roco/wiki/meta/handoff_2026-04-20/battle_wiki_handoff_2026-04-20.md
3. /Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_team_analysis_mechanism_guard_spec.md
4. /Users/okfin3/project/GitHub/OKFin33/Roco/wiki/pages/mechanics/speed_priority_and_swift.md
5. /Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md
   Focus especially on the 2026-04-21 entry about P1a mechanism-guard hardening
   and preliminary audit.

Optional but useful external references:

- Karpathy LLM Wiki gist:
  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Example implementation:
  https://github.com/Pratiyush/llm-wiki

You are not resuming Roco feature implementation.
You are resuming the separate Battle Wiki / doctrine-infrastructure thread.

Current situation:

- Roco P1a hardening and audit have now established a bounded first A/B bridge.
- A-layer evidence can already trigger reviewed B-layer mechanism retrieval.
- Missing reviewed mechanism pages now force explicit downgrade instead of
  improvisation.
- Default synthesis doctrine has been made generic and persona-free.
- Current verdict from the main thread is:
  B-layer wiki is sufficient for a bounded first bridge, but not yet mature
  enough to support stable, broad, live model-backed doctrine reasoning.

The PM now wants to step back and converge the Battle Wiki decisions before
going further.

Your job in this thread is NOT to immediately write more doctrine pages.
Your job is to prepare a decision-convergence discussion.

Please return a structured memo that answers:

1. What exact decisions now need to be locked for B Wiki to move forward?
2. Which of those decisions are pure wiki-infrastructure decisions, and which
   are actually C-layer usage / enforcement decisions?
3. Which parts should be borrowed directly from the Karpathy LLM Wiki pattern,
   and which parts must be Roco-specific?
4. What is the minimum viable next step for the Battle Wiki thread:
   - architecture/spec work
   - schema/governance work
   - page template work
   - PM editing protocol
   - eval design
   - or first doctrine content expansion?
5. What should explicitly NOT be decided yet, because the business semantics
   are still too unclear?

Important boundaries:

- Roco is not Pokemon.
- B layer must remain generic and persona-free.
- Do not treat Enzo or any persona pack as default B doctrine.
- A-layer exact facts remain in SQLite / Engine / approved structured data.
- Do not assume that “having more wiki pages” alone solves stable agent quality.
- Take seriously the possibility that a separate C layer is needed to enforce
  how Agent uses wiki knowledge.

What the PM most needs from you:

- not a big content dump
- not a vague architecture lecture
- but a clean decision agenda:
  - which decisions are blocking
  - why they matter
  - recommended option for each
  - what can wait

Preferred output shape:

- Section 1: Current understanding of the problem
- Section 2: Decisions that must be converged now
- Section 3: Recommended default choices
- Section 4: Decisions to defer
- Section 5: Recommended next deliverable for the Battle Wiki thread

Do not modify runtime code in this thread unless the PM explicitly asks for it.
```
