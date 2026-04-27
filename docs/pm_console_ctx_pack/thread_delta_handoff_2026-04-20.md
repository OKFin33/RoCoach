# PM Console Thread Delta Handoff

## Purpose

This document captures the **net-new PM Console infrastructure conclusions**
from the current `Roco` PM-control thread.

It is a delta handoff, not a replacement for the existing PM Console context
pack.

Read this **after**:

- [project_brief.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/project_brief.md)
- [operating_model.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/operating_model.md)
- [core_artifacts.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/core_artifacts.md)
- [migration_note.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/migration_note.md)

This handoff exists because the current thread moved beyond:

- `Roco` project sequencing

and into:

- PM Console scheduling semantics
- courier implementation realism
- long-owner-thread vs subagent trade-offs
- PM-consumable output protocol requirements

## What This Thread Added

The current thread confirmed or refined the following:

1. the PM Console should act as the **scheduler**
2. courier is a separate role from scheduler
3. `approve` and `send` are different control actions
4. GUI couriering into Codex threads is not currently reliable enough to be the
   core implementation
5. long-lived owner threads still have structural advantages over subagents
6. those advantages are only real if thread outputs are compressed into a PM-
   consumable protocol
7. the likely end-state is a **hybrid model**, not pure GUI courier and not
   pure subagent replacement

## Locked Role Semantics

### PM Console

The PM Console should own:

- reading execution state
- deciding the single next legal action
- selecting the legal executor
- generating the task packet
- updating state after accepted stage results
- surfacing what the PM must decide now

The PM Console should not be treated as:

- a worker
- a courier
- a self-approving executor

### Courier

Courier should be treated as a pure transport layer.

Courier may:

- open the target surface
- paste the approved packet verbatim
- send it

Courier may not:

- pick the next task
- pick the target
- rewrite the packet
- summarize constraints away
- approve completion

### PM / Decision Maker

The PM should mainly do:

- `approve`
- `reject`
- `pause`
- `send`
- `change plan`

The PM should not need to do:

- routing memory work
- packet writing
- context reconstruction
- scope policing by hand

## `Approve` Versus `Send`

This thread made the control split explicit:

- `approve`
  - accepts the current stage result
  - advances execution state
  - unlocks the next legal stage
  - allows packet generation
- `send`
  - authorizes dispatch of the already-approved packet to the selected
    executor

This split should remain intentional.

Reason:

- approval and dispatch are different control points
- PM may want to inspect or edit packet scope after stage acceptance
- automatic dispatch on `approve` increases misfire risk

Do **not** collapse these two actions by default unless the new PM Console
project explicitly chooses an auto-dispatch mode.

## Courier Reality Check From This Thread

The current thread tested the intended `Computer Use courier` concept against
the actual Codex desktop environment.

Observed outcome:

1. `Computer Use` could not directly control the Codex app
2. local macOS accessibility fallback could partially operate
3. Codex menu access became available after permissions were enabled
4. direct, reliable thread targeting and packet injection into Codex was still
   not stable enough to count as core infrastructure

Practical conclusion:

- `GUI courier` remains a valid **concept**
- but `Computer Use -> Codex thread` is currently not a reliable **default
  implementation**

This means the new PM Console project should not hardcode the assumption that:

- `send` always equals successful GUI dispatch into an existing Codex thread

Instead, courier should be designed as:

- optional
- replaceable
- best-effort unless backed by a real host integration

## Long Owner Threads Versus Subagents

This thread did **not** overturn the earlier conclusion that long-lived owner
threads have distinct advantages.

Those retained advantages are:

- stronger context continuity
- more stable role identity
- better owner persistence
- more credible independent audit separation
- stronger long-horizon implementation/review memory

Examples of those long-lived roles:

- main implementation owner
- QA / audit owner
- persona-source owner

This thread also reaffirmed that subagents are still best suited for:

- bounded one-off tasks
- sidecar exploration
- parallel small-scope work
- short verification work that does not need long role identity

So the new project should **not** assume:

- subagents replace all long-lived owner threads

That would erase a structural advantage already judged valuable.

## Important Correction: Owner Threads Only Matter If Their Output Is PM-Consumable

This was the most important refinement from the thread.

Long-lived threads are **not** valuable just because they accumulate history.

If PM cannot realistically read or use that history, then “more context” is not
an operational advantage. It is just more chat.

Therefore the real value of owner threads is:

- not that they keep a giant transcript
- but that they can turn long-lived judgment into compressed, explicit stage
  outputs that PM can approve

This means the new PM Console project should treat the following as a hard
requirement:

- owner threads must emit a stable PM-facing result protocol

The PM should not need to read long transcripts by default.

## What PM Actually Needs To Review

This thread clarified that PM does **not** need to replay full thread history.

PM-facing review should focus on:

1. what task was executed
2. what files or artifacts changed
3. what validation was run
4. what findings or risks remain
5. whether scope was respected
6. why the stage should pass or fail the gate

So “复盘” in the new PM Console project should mean:

- replaying **decisions, evidence, scope, and gate transitions**

not:

- replaying whole chat logs

## Recommended PM-Facing Return Protocol

This thread converged toward a return format like:

- `Status`
- `Files changed`
- `Result`
- `Validation`
- `Scope confirmation`
- `Findings / Risks`
- `Recommendation`

This should likely become a first-class artifact or contract in the standalone
PM Console project.

Without this, long-owner-thread advantages degrade fast because the PM Console
must keep translating raw worker output by hand.

## Strategic Trade-Off

The thread's final trade-off conclusion was:

- long owner threads preserve:
  - correctness
  - stable ownership
  - auditability
- subagents preserve:
  - throughput
  - low dispatch cost
  - bounded parallelism

Therefore the likely best operating model is:

- long-lived owner threads for mainline implementation / audit / persona-owner
  work
- subagents for sidecar, bounded, parallel, low-memory tasks
- PM Console as the single scheduler over both

This is a **hybrid model**.

Do not position the new PM Console project as:

- GUI-thread orchestration only

and do not position it as:

- subagent-only orchestration

The abstraction should support both, while making their trade-offs explicit.

## Recommended Abstraction For The New Project

The standalone PM Console project should probably separate:

1. `scheduler`
2. `executor class`
3. `courier`
4. `return protocol`

Suggested executor classes:

- `long_owner_thread`
- `subagent`
- `manual_executor`

Suggested courier classes:

- `manual_copy_send`
- `gui_courier`
- `host_native_dispatch` if such an integration exists later

The key point is:

- executor type and courier type should not be hard-wired together

## What The New Project Should Explore Next

Recommended next design questions:

1. how to formalize the PM-facing return protocol
2. how to represent executor type explicitly in task packets or state
3. whether `approve` and `send` should remain separate in all modes
4. what the fallback chain for courier should be
5. how to support long-owner-thread workflows without forcing PM to read raw
   history
6. whether the first packaged skill should target:
   - manual dispatch first
   - optional GUI dispatch
   - optional subagent sidecar support

## What Should Not Be Re-imported From Roco

Do not pull the following into the standalone PM Console project:

- `Roco` stage names
- Enzo/persona-specific doctrine content
- battle-advisor implementation details
- `Roco` runtime/API/mobile specifics

Carry only the control-plane conclusions.

## Minimal Summary

This thread's final infrastructure conclusion was:

- PM Console should stay the scheduler
- courier should stay courier-only
- `approve` and `send` should stay separate
- GUI courier into Codex is not reliable enough to be assumed as core infra
- long-lived owner threads still matter
- but only if their output is compressed into PM-consumable protocol
- subagents should augment the system, not automatically replace long owners
- the standalone PM Console project should design for a hybrid execution model

## Suggested New-Project Kickoff Prompt

```text
Read the PM Console context pack first, then read:

- /Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/thread_delta_handoff_2026-04-20.md

Treat the current delta handoff as authoritative for:

- scheduler versus courier split
- approve versus send semantics
- GUI courier implementation limits
- long owner thread versus subagent trade-offs
- PM-facing output protocol requirements

Do not re-derive these from scratch unless you are explicitly asked to revisit
them.
```
