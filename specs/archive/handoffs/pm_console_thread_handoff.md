# PM Console Thread Handoff

## Purpose

Create a clean main-control thread after the project accumulated enough design
history that the original thread became heavy.

This handoff is for a new PM-console thread only. It does not replace the
project SSD or the locked execution plan.

## What The New PM Console Thread Must Treat As Authoritative

- `specs/p1_locked_execution_plan.md`
- `specs/p1_execution_state.yaml`
- `specs/current_task_allocation.md`
- `specs/enzo_integration_review.md`
- `specs/task_packet_template.md`

## Current Project Position

- P0 is fully complete and audited
- post-P0 direction is locked:
  - LLM is the core analysis/synthesis unit
  - Engine / SQL / approved docs remain source-of-truth
  - default UX should feel like talking to a coach
- Enzo internal doctrine sample has been reviewed and accepted for internal
  pattern extraction only
- Gate 1 is open
- next unlocked step is:
  - `P1a synthesis implementation spec`

## New Thread Responsibilities

- act as PM control console
- read execution state first
- update execution state after every accepted stage result
- generate task packets from `specs/task_packet_template.md`
- never unlock future stages without explicit main-thread acceptance

## What The New Thread Must Not Do

- re-litigate finished SSD decisions by default
- skip the locked execution plan
- reopen P0 tracks without a concrete regression
- start P1a code implementation before `P1a synthesis implementation spec`
  exists and is accepted

## Minimal Kickoff Prompt

```text
Read these files first and treat them as authoritative:

- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_locked_execution_plan.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_execution_state.yaml
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/current_task_allocation.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/enzo_integration_review.md
- /Users/okfin3/project/GitHub/OKFin33/Roco/specs/task_packet_template.md

You are now the PM control console thread for this project.
Do not redesign the roadmap.
Use the locked execution plan and execution state to determine the single next
allowed action.
If no worker handoff is needed, continue the main-thread work directly.
Current next unlocked step is `P1a synthesis implementation spec`.
```

## Recommendation

Starting a new PM-console thread is recommended now that:

- the execution state exists
- the locked plan exists
- the Enzo integration review is complete

This reduces context drag while preserving strict sequencing.
