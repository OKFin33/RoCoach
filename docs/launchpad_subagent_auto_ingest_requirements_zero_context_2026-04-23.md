# LaunchPad Subagent Auto-Ingest Requirements (Zero-Context)

## Purpose

This document explains, from zero context, how LaunchPad should automatically
recover and ingest reusable subagent results back into its SSD runtime.

It draws a hard line between:

- what Codex app already provides natively
- what LaunchPad must implement on top of those primitives

This is a control-plane infrastructure note. It is not a Roco product spec.

## Zero-Context Starting Point

Assume the reader knows only this:

- one PM-facing thread controls project delivery
- Codex app can spawn and message subagents
- LaunchPad maintains gated SSD execution state in `.launchpad/`
- implementation and review work may run on reusable subagent lanes

## Problem Statement

Even if LaunchPad can dispatch a task to a reusable subagent lane, the system
is still incomplete if the main thread must manually recover the result every
time a subagent finishes.

That failure mode looks like this:

1. subagent finishes work
2. completion is visible in the thread
3. the PM or main thread must manually translate the result
4. `execution_state.yaml` is not updated until someone performs recovery

This means the system has lane dispatch, but not lane closure.

## Required Product Outcome

LaunchPad should support this behavior:

1. PM approves and sends work
2. LaunchPad dispatches work to the correct reusable lane
3. subagent completes
4. LaunchPad automatically converts the completion into a stage return
5. LaunchPad automatically ingests that stage return into runtime state
6. PM sees a standard Completion Check without asking for recovery

The PM should not need to say:

- "subagent finished"
- "please ingest the result"
- "update LaunchPad state"

Those are LaunchPad runtime responsibilities.

## Codex App Native Capabilities

Codex app already provides the primitives needed to support auto-ingest:

- `spawn_agent`
- `send_input`
- `wait_agent`
- `resume_agent`
- `close_agent`
- subagent completion notifications delivered to the main thread

This means Codex app already supports:

- creating a reusable executor or reviewer subagent
- reusing an existing subagent
- receiving a completion event when the subagent finishes

## Codex App Native Boundaries

Codex app does **not** natively provide LaunchPad-aware auto-ingest.

It does not automatically:

- map a completion event to a LaunchPad lane
- map a completion event to a LaunchPad stage
- validate that the subagent stayed in scope
- translate freeform completion text into a stage return contract
- call `ingest_stage_return.py`
- update `execution_state.yaml`
- generate a PM-facing Completion Check
- decide whether the result should produce `approve`, `revise`, `pause`, or `replan`

Therefore:

> Codex app provides completion notification primitives.
>
> LaunchPad must turn those primitives into SSD state transitions.

## Design Requirement

LaunchPad should implement deterministic auto-ingest for subagent lanes.

The requirement is not:

- "subagent completion should be visible"

The requirement is:

- "subagent completion should be sufficient to move the LaunchPad control plane
  to the next valid gate without manual recovery"

## Required Runtime Model

LaunchPad should track enough runtime data to answer all of the following:

- Which lane owns the current stage?
- Which `agent_id` is bound to that lane?
- Which packet is active for that lane?
- Is the lane currently awaiting completion?
- Has a completion for that lane already been ingested?
- If ingestion failed, why?

This cannot rely only on conversational memory.

At minimum, runtime should persist:

- lane name
- lane role
- bound `agent_id`
- current stage
- current gate
- active packet
- dispatch timestamp
- completion timestamp
- ingestion status
- last stage return path
- last completion check path

## Required Event Flow

The intended flow should be:

1. LaunchPad dispatches a stage to a reusable lane
2. LaunchPad records the lane binding and active packet
3. subagent returns a structured completion payload
4. main thread receives the completion notification
5. LaunchPad validates the payload against the expected return contract
6. LaunchPad writes a `stage_return_input` artifact
7. LaunchPad runs `ingest_stage_return.py`
8. LaunchPad updates `execution_state.yaml`
9. LaunchPad renders the PM-facing Completion Check

This is automatic recovery at the control-plane level.

## Required Return Contract

Auto-ingest is only reliable if subagents return a predictable structure.

LaunchPad should require reusable lane subagents to return, at minimum:

- status
- task_executed
- files_changed
- result
- validation
- scope_confirmation
- findings_risks
- recommendation

This matches the existing LaunchPad `ingest_stage_return.py` contract.

Freeform prose should not be the primary ingestion format.

If the subagent returns only prose, LaunchPad may attempt translation, but that
should be treated as a weaker fallback path.

## Required Validation Gate

LaunchPad must validate before ingesting.

At minimum, it should reject or downgrade auto-ingest when:

- the return format is malformed
- the reported scope exceeds the active packet
- validation commands are missing where required
- the stage recommendation is invalid
- the lane/stage mapping is ambiguous

When validation fails, LaunchPad should not silently approve.

Instead it should move to a bounded fallback such as:

- `revise`
- `pause`
- `replan`

## Required Failure Handling

LaunchPad should explicitly model these failure paths:

- subagent finished but returned malformed output
- subagent finished but changed files outside declared ownership
- subagent finished but did not run required validation
- subagent finished but lane binding is stale
- subagent finished after the PM had already interrupted the node

These should not be treated as successful completion.

They should produce a deterministic fallback state.

## Required Lane Binding Policy

Auto-ingest only works if LaunchPad knows which lane owns the completion event.

Therefore LaunchPad should persist a lane binding such as:

- `main_dev_lane -> agent_id -> current_stage -> active_packet`
- `main_qa_lane -> agent_id -> current_stage -> active_packet`

If a completion event arrives from an unbound or retired agent, LaunchPad
should not auto-ingest it blindly.

It should either:

- ignore it
- mark it as stale
- require manual review

## Required Replan Awareness

Auto-ingest must respect interrupted execution.

If the PM pauses or replans a node before the subagent completes, LaunchPad
must check whether:

- the completion still belongs to the active node
- the node was archived or replaced
- the result is now stale relative to the new plan

A stale completion should not overwrite current state.

## Implementation Boundary

This capability should be implemented in LaunchPad, not expected from Codex
app itself.

Codex app is responsible for:

- running subagents
- returning completion notifications to the main thread

LaunchPad is responsible for:

- lane binding
- return contract enforcement
- stage return generation
- ingestion
- PM check generation
- state-machine advancement

## Most Feasible Implementation Path

The most practical path is not a background daemon.

The most practical path is:

1. rely on the main thread receiving subagent completion notifications
2. add a LaunchPad-side auto-ingest handler in the main thread flow
3. on notification:
   - resolve lane by `agent_id`
   - resolve active stage and packet
   - translate or validate the completion payload
   - write `stage_return_input`
   - call `ingest_stage_return.py`
   - move state to `pm_review_ready`

This is feasible with current primitives.

## What Is Not Required

This design does **not** require:

- a separate always-on background service
- a Codex platform change
- a new agent system outside existing subagent primitives

It also does not require LaunchPad to fully automate PM approval.

Approval should remain a PM decision unless a later design explicitly changes
that.

## Minimum Deliverables

The minimum useful implementation should include:

- lane registry with `agent_id` tracking
- active dispatch registry per lane
- structured subagent return contract
- auto-ingest handler for completion notifications
- stale-result protection
- failure fallback paths
- PM-facing Completion Check generation

Without all of these, LaunchPad still depends on manual recovery.

## One-Sentence Conclusion

Codex app already provides enough primitives for subagent auto-recovery, but
LaunchPad must implement the lane-aware ingestion pipeline that turns a
completion notification into a valid SSD state transition.
