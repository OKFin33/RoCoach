# LaunchPad Subagent Lane Requirements (Zero-Context)

## Purpose

This document explains, from zero context, what LaunchPad needs in order to use
Codex subagents as stable execution lanes instead of repeatedly spawning
temporary workers.

It also draws a hard boundary between:

- what Codex app already supports natively
- what LaunchPad must implement on top of those primitives

This is a control-plane design note. It is not a Roco product feature spec.

## Zero-Context Starting Point

Assume the reader knows nothing except:

- there is one PM-facing control thread
- Codex app can create and message subagents
- LaunchPad wants to run a gated SSD-style delivery flow
- implementation and review work should not be executed directly by the PM
  control thread when avoidable

## Problem Statement

Without additional management, Codex subagents behave like useful agent
primitives, but not like stable project lanes.

This means a system may appear to support:

- a main development worker
- a main QA worker

while in practice it still does:

- spawn a new subagent for many tasks
- lose continuity between tasks
- fail to ingest agent completion automatically
- treat agents as disposable workers rather than managed lanes

The result is:

- the PM control thread keeps too much execution responsibility
- scheduler and executor roles blur
- “reusable subagent” becomes mostly nominal

## Required Product Shape

LaunchPad should target this operating model:

- most implementation tasks default to the `main_dev_lane`
- most audit / QA tasks default to the `main_qa_lane`
- the PM-facing thread is the only scheduler
- lanes are long-lived control concepts
- specific subagents are the current execution bodies attached to those lanes

This is the key distinction:

- **lane** = stable control-plane role
- **subagent** = the currently bound execution body for that lane

LaunchPad should manage lanes, not just agents.

## Codex App Native Capabilities

Codex app already provides the primitives needed for lane-based orchestration:

- `spawn_agent`
- `send_input`
- `wait_agent`
- `resume_agent`
- `close_agent`

From these primitives, the following are already possible:

- create a development subagent
- create a reviewer subagent
- reuse a previously created subagent by sending it more work
- close or replace a subagent when needed
- maintain multiple internal execution lines while keeping one PM-facing thread

## Codex App Native Boundaries

Codex app does **not** natively provide a full lane manager.

It does not automatically provide:

- a `main_dev_lane` concept
- a `main_qa_lane` concept
- default dispatch routing by stage type
- default reuse of the same agent for later lane tasks
- automatic rollover / retirement policy
- automatic conversion of an agent completion into a LaunchPad stage return
- automatic ingestion of agent output back into `execution_state.yaml`

Therefore, Codex app supports the **primitives** for the desired system, but it
does not itself implement the **system**.

## Design Requirement

LaunchPad must treat subagent orchestration as a first-class runtime concern.

The minimum requirement is:

> Implementation and review work should be lane-routed by default, not
> agent-spawned ad hoc.

## Required Lane Model

LaunchPad should define at least:

- `main_dev_lane`
- `main_qa_lane`

Each lane should track:

- lane name
- lane role
- current bound `agent_id`
- current status
- last sync time
- rollover count
- retirement status
- lane notes / unresolved constraints

This should be treated as runtime state, not as a conversational memory trick.

## Required Dispatch Policy

LaunchPad should apply these defaults:

- implementation stage -> `main_dev_lane`
- audit / QA / review stage -> `main_qa_lane`

Manual executor fallback may still exist, but should be exceptional and
explicitly recorded.

Recommended policy:

- `subagent_first`
- if falling back to manual execution, record a `manual_fallback_reason`

## Required Reuse Policy

If a lane already has an active, valid subagent, LaunchPad should prefer:

- `send_input(existing_agent_id, ...)`

not:

- `spawn_agent(...)`

This should be the default for same-lane work unless one of the following is
true:

- the lane agent is retired
- the lane agent is closed or unavailable
- the lane context is too noisy
- the role needs to change
- LaunchPad explicitly decides to roll over the lane

## Required Rollover Policy

LaunchPad must be able to replace the current subagent bound to a lane without
destroying the lane abstraction itself.

This means:

- the lane survives
- the old subagent becomes retired
- a new subagent becomes the lane’s current execution body

Recommended rollover triggers:

- context drift
- repeated low-quality outputs
- role contamination
- explicit PM / scheduler reset

## Required Return-Ingestion Policy

This is the current critical gap.

When a lane subagent completes work, LaunchPad should not stop at:

- “the agent finished”

It must continue through:

1. collect the completion payload
2. translate it into structured stage return form
3. ingest it back into the LaunchPad runtime
4. generate the PM-facing Completion Check
5. move the state machine to the next approval gate

Without this, the system still depends on manual main-thread recovery after
every subagent run.

## Required State Artifacts

To support lane-based orchestration, LaunchPad should persist:

- lane registry
- bound `agent_id` per lane
- lane retirement / rollover history
- pending lane dispatch
- lane completion awaiting ingestion
- last ingested result per lane

At minimum, the runtime must make it easy to answer:

- Which lane owns this stage?
- Which subagent is currently bound to that lane?
- Is the subagent still reusable?
- If not, why not?
- Did the lane return already get ingested?

## Required PM-Facing Behavior

The PM should usually experience the system like this:

- approve current gate
- see the next bounded Intent Check
- say `send`
- LaunchPad dispatches to the correct lane by default
- LaunchPad later returns with a Completion Check

The PM should **not** need to micromanage:

- which exact subagent to use
- whether to reuse or respawn
- whether the result has been ingested

Those are LaunchPad’s responsibilities.

## Manual Fallback Policy

Manual execution should remain allowed for:

- bootstrap or adoption maintenance
- spec generation
- replan discussion
- tiny bounded fixes where packet/agent overhead is not worth it
- cases where subagent execution is unavailable or unsafe

But manual execution should not silently replace lane execution for major
implementation or review stages.

If a major lane stage uses manual execution, LaunchPad should record why.

## What “Reusable Subagent” Actually Means

LaunchPad should not define a reusable subagent as:

- a magically persistent owner thread

It should define it as:

- a reusable execution body currently attached to a stable lane

That is the only version that is operationally reliable.

Therefore:

- **lane permanence** is the design goal
- **agent permanence** is a best-effort implementation detail

## Acceptance Criteria

LaunchPad can claim to support reusable subagent lanes only when all of the
following are true:

- implementation stages default to `main_dev_lane`
- review stages default to `main_qa_lane`
- same-lane work reuses the existing bound subagent by default
- rollover is explicit and tracked
- completed subagent work is ingested back into the state machine
- the PM does not need to manually reconstruct lane continuity after each run

If these conditions are not met, the system is still primarily:

- agent-based dispatch

not:

- lane-based dispatch

## Bottom Line

Codex app supports the required **subagent primitives**.

LaunchPad still needs to implement the **lane manager**.

The target is not:

- “more subagents”

The target is:

- “fewer temporary workers, more stable lanes”
