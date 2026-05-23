# LaunchPad Dispatch And Lane Continuity Requirements (Zero-Context)

## Purpose

This document explains, from zero context, why two new LaunchPad requirements
emerged during real project usage:

- a lighter PM-facing `dispatch` mode
- lane continuity that does not depend on any one subagent instance staying alive

It also proposes the most practical resolution path.

This is a control-plane infrastructure note. It is not a Roco product feature
spec.

## Zero-Context Starting Point

Assume the reader knows only this:

- one PM-facing thread controls project delivery
- LaunchPad maintains SSD/runtime state in `.launchpad/`
- Codex app can run reusable subagents for implementation and review lanes
- the PM wants low-friction control without manually operating owner threads

## Why New Requirements Emerged

These requirements did not appear in theory. They appeared because real usage
exposed two structural gaps.

### Gap 1: PM control was still heavier than expected

The PM expectation was:

- after a stage completes, the system should prepare the next bounded step
- the PM should mostly authorize dispatch, not repeatedly perform two separate
  actions that feel like "approve this" and then "send that"

But the observed runtime often still behaved like:

- Completion Check
- PM must `approve`
- then a separate Intent Check
- then PM must `send`

Even when `dispatch_gated` was configured, previously materialized strict gates
could remain active. That made the PM-facing surface feel inconsistent.

This created a new requirement:

> LaunchPad needs a clearer light-control dispatch mode with reliable runtime
> materialization.

### Gap 2: Reusable lanes looked persistent, but concrete subagents were not

The PM expectation was:

- there is a `main_dev_lane`
- there is a `main_qa_lane`
- later work should usually go back to those lanes

But real execution showed:

- a lane can still exist while the concrete subagent bound to it becomes
  unavailable or non-resumable
- one finished subagent may no longer be recoverable later
- continuity cannot safely depend on one subagent process staying alive

This created a second new requirement:

> LaunchPad must preserve lane continuity independently from any specific
> subagent instance.

## Root Cause Summary

The new requirements arose because the runtime exposed a mismatch between:

- what the PM thought the control model was
- what the current helpers actually materialized

The first mismatch was about **control surfaces**:

- `dispatch_gated` existed as a config and contract concept
- but active gates could still remain in older strict form

The second mismatch was about **lane continuity**:

- reusable lanes were conceptually present
- but continuity still leaked too much into specific subagent instances

## Requirement A: Light-Control Dispatch Mode

### Desired Product Outcome

The PM should usually experience delivery like this:

1. receive a bounded decision surface
2. authorize dispatch
3. wait for a returned result
4. decide whether to continue

The PM should not have to mentally model:

- whether the current surface is a strict completion gate or a dispatch gate
- whether config was switched after the current node was materialized
- whether the system is showing the old control mode or the new one

### What This Requirement Really Means

This requirement is not just about renaming `send` to `dispatch`.

It means:

- the runtime should reliably materialize the PM-facing dispatch surface
- active nodes must match configured gate mode
- switching gate mode must not leave the runtime in a split state

### Recommended Resolution

LaunchPad should add:

- **gate rematerialization**
  - when `gate_mode` changes, the active node must be explicitly rebuilt
- **dispatch-first PM surface**
  - under `dispatch_gated`, post-execution runtime should route to the next
    dispatch-preparation surface instead of lingering on old strict completion
    semantics
- **mode drift detection**
  - if config and active node disagree, LaunchPad should surface a repair path
    instead of silently continuing
- **dispatch-specific brief rendering**
  - the PM-facing surface should clearly say `Dispatch Check`, not merely reuse
    a `send`-style check with renamed wording

## Requirement B: Lane Continuity Independent Of Subagent Survival

### Desired Product Outcome

The PM should be able to rely on:

- `main_dev_lane`
- `main_qa_lane`

without caring whether the currently bound subagent instance is still alive.

That means:

- the lane survives
- continuity survives
- only the execution body may roll over

### What This Requirement Really Means

This requirement does not mean:

- one subagent must stay alive forever

It means:

- lane continuity must be artifact-backed, not process-backed

The lane must remain usable even if:

- the bound subagent disappears
- the lane is rolled over to a new subagent
- execution falls back to manual or another temporary path

### Recommended Resolution

LaunchPad should make `lane_registry` the true continuity source and store,
per lane:

- lane role
- bound agent id and agent name
- current or last active stage
- pending or last packet
- recent accepted stage return
- unresolved constraints
- recent risk signals
- rollover reason
- ingestion status

LaunchPad should also maintain bounded continuity artifacts such as:

- `agent_deltas/`
- last accepted packet or packet summary
- last accepted stage return summary
- lane notes for unresolved constraints

Then at dispatch time, LaunchPad should inject continuity from those artifacts
into the next execution body.

The key shift is:

- **lane continuity is owned by LaunchPad**
- **subagents are replaceable execution bodies**

## Combined Architectural Conclusion

These two requirements are related.

Why?

Because a lighter PM dispatch model only works if LaunchPad can safely:

- rematerialize the correct next slice
- bind it to the correct lane
- inject continuity into whatever execution body the lane currently uses

If dispatch is light but lane continuity is weak, the PM gets fast buttons but
unstable execution.

If lane continuity is strong but dispatch is heavy, the PM still carries too
much scheduler burden.

So the real target is:

> light PM control + strong artifact-backed lane continuity

## Recommended Priority

### Priority 1: Lane continuity infrastructure

Reason:

- without this, reusable lanes are mostly nominal
- the system still depends on whether one specific subagent happens to survive

### Priority 2: Dispatch-mode materialization

Reason:

- this improves PM UX and reduces gate friction
- but it is safer to simplify PM control only after lane continuity is stable

## Minimum Deliverables

The minimum useful resolution should include:

- `gate_mode` drift detection and repair
- explicit dispatch-check generation under `dispatch_gated`
- lane registry synchronization with runtime and local lane metadata
- continuity injection rules for new or rolled-over execution bodies
- rollover-safe lane recovery when old agent ids are no longer resumable
- clear PM-facing distinction between:
  - current completion artifact
  - next dispatch decision surface

## What Should Not Be Assumed

Do not assume:

- changing `config.yaml` automatically rematerializes current gates
- a reusable lane implies a permanently recoverable subagent
- PM-facing `dispatch` wording alone reduces actual control friction

## One-Sentence Conclusion

The new requirements emerged because real LaunchPad usage exposed two truths:
control surfaces must be rematerialized consistently, and reusable lanes only
become real once their continuity no longer depends on a single surviving
subagent instance.
