# Temporary LaunchPad Skill Retrospective

Date: 2026-04-22

Status:

- temporary analysis note
- written for LaunchPad skill optimization
- not a canonical runtime contract

## Purpose

This document records what happened during the recent Roco + LaunchPad
practice, where the intended LaunchPad control flow was partially bypassed in
the visible PM thread.

It tries to answer:

1. what actually happened
2. when and under what conditions LaunchPad flow appears to have been bypassed
3. what likely caused the drift
4. a non-authoritative analysis from the assistant's point of view

This note is not itself a LaunchPad spec. It is a temporary debugging artifact.

## Expected LaunchPad Behavior

According to the current LaunchPad skill and references:

- the visible PM thread should be the only scheduler
- the scheduler should read `.launchpad/execution_state.yaml` first
- only the single `next_legal_action` should be taken
- PM-facing checks should be shown directly in chat
- `approve` and `send` must remain separate
- local `.launchpad/pm_briefs/` are audit copies, not the main interface
- the thread should not drift into generic engineering summary mode

Important current runtime facts in this repo:

- `.launchpad/config.yaml` is missing
- `.launchpad/` exists and has execution state artifacts
- current state is in `phase: execution`

This means the runtime was partially present, but bootstrap/config completion
was not fully enforced.

## What Happened In Practice

### Phase 1. LaunchPad Was Introduced And Used As A Control Runtime

The project adopted `.launchpad/` as a local control runtime for the Roco PM
thread.

Observed behavior that matched LaunchPad expectations:

- state was written into `.launchpad/execution_state.yaml`
- decisions were recorded in `.launchpad/decision_log.md`
- task packets and stage returns existed
- implementation dispatch and return ingestion were modeled as gated stages

This part was broadly aligned with the intended LaunchPad usage.

### Phase 2. P1a Implementation Return Reached An Approval Gate

After `P1a implementation` completed, LaunchPad state moved to an approval
gate.

The runtime correctly represented:

- `next_legal_action: approve`
- PM decision required
- no automatic fallthrough to `send`

This is still aligned with LaunchPad's state-machine model.

### Phase 3. Main Thread Continued Doing Real Work While State Still Said `approve`

The visible PM thread then continued with substantive work, including:

- mechanism-guard hardening
- runtime/retrieval edits
- reviewed-page addition
- targeted validation
- LaunchPad state/log updates
- later Battle Wiki / console integration reasoning

This is the first clear point where LaunchPad flow was bypassed.

Why:

- the visible thread was no longer behaving like a strict scheduler bound to
  `next_legal_action`
- instead, it resumed acting like a normal Codex implementation thread that
  could continue solving adjacent problems

### Phase 4. PM-Facing Output Drifted From LaunchPad Brief Style

Once the thread had resumed solving real work, the chat output also drifted.

Observed drift:

- replies started to look like standard Codex engineering summaries
- local artifacts and internal reasoning were treated as primary explanation
- the assistant proposed future planning moves beyond the current legal action
- the assistant described LaunchPad state rather than speaking as LaunchPad's
  brief layer

This is the second clear bypass:

- not only the state machine was bypassed
- the PM-facing interface contract was also bypassed

### Phase 5. Battle Wiki Handoff Added New Implementation Recommendations

Later, the Battle Wiki thread produced new main-thread recommendations:

- plan A-layer mechanism structuring
- define Battle Wiki compile/use contract
- define a minimal eval

These are useful implementation-facing recommendations, but in LaunchPad terms
they should only enter the PM thread through:

- the current legal action
- or an explicit `replan`
- or a later unlocked stage

Instead, they were interpreted directly inside the PM thread while LaunchPad
state still remained at:

- `current_stage: P1a audit`
- `next_legal_action: approve`

This increased the mismatch between:

- what the runtime said the thread was allowed to do
- and what the thread actually started discussing as next-step control

## Likely Bypass Point

The most likely first real bypass was:

> after `P1a implementation` had already reached an `approve` gate, but before
> that gate was consumed, the main thread resumed implementation / audit /
> integration work instead of staying bound to the approval action.

In simpler form:

```text
state says: only approve is legal
thread behavior says: continue improving the system anyway
```

That is the key failure pattern.

## Conditions That Likely Made The Bypass More Likely

### 1. LaunchPad runtime existed, but bootstrap/config was incomplete

`config.yaml` is missing.

This matters because the skill says bootstrap/config should be checked before
taking control.

Possible consequence:

- the runtime existed enough to feel real
- but not enough to force a complete LaunchPad operating mode

### 2. The thread mixed scheduler role and executor role

LaunchPad expects:

- main thread = scheduler only
- executors/subagents = implementation/review workers

But in practice, the visible PM thread also performed:

- code edits
- test execution
- audit ingestion
- state interpretation
- planning interpretation

Once the scheduler thread is also solving the work, LaunchPad becomes easier to
mentally downgrade into "artifact-backed notes around a normal coding thread"
rather than "the actual control protocol."

### 3. The state machine was treated as descriptive, not normative

The skill expects:

- `execution_state.yaml` tells the thread what is legally allowed

In practice, the thread often treated state as:

- a useful summary of where we are

That difference is critical.

If state is only descriptive, then adjacent useful work feels harmless.
If state is normative, that same behavior is a protocol violation.

### 4. PM questions invited broad reasoning while the thread was in `execution`

The user asked many valid project-level questions:

- what is the real tradeoff
- is subagent or manual thread better
- is B wiki enough
- what is missing in C layer

These are design/governance questions.

In a pure LaunchPad reading, the thread should either:

- answer them strictly as the current decision-relevant slice
- or move to `replan` / `design`

Instead, the thread frequently answered them directly while remaining in
`phase: execution`.

That made it much easier for LaunchPad flow to dissolve into mixed-mode
conversation.

### 5. PM-facing brief discipline was not enforced hard enough

The skill is explicit:

- PM-facing checks must appear directly in chat
- local brief files are not the primary interface
- only the current legal action should be translated

In practice, once drift began, the assistant started producing:

- engineering summaries
- architectural analysis
- state narration

instead of strict brief-shaped responses.

This suggests the skill currently relies too much on "assistant remembering the
mode" and not enough on "hard guardrails that prevent mode drift."

## Candidate Root Cause Summary

The likely root cause is not one single bug.

It is a compound failure:

1. LaunchPad runtime adoption happened
2. the thread correctly reached a gated state
3. but the visible PM thread was still allowed to keep behaving like a normal
   coding/analysis assistant
4. once adjacent work became obviously useful, the state machine stopped being
   treated as binding
5. PM-facing output style drifted with it

In short:

```text
LaunchPad was present as artifacts,
but not consistently present as the actual operating discipline.
```

## What This Suggests For LaunchPad Skill Improvement

These are not formal spec decisions, only practical debugging suggestions.

### Suggestion A. Hard-stop On Non-Legal Actions

If `next_legal_action` is `approve`, the skill should strongly bias toward:

- only rendering a PM-facing Completion Check
- only answering decision-relevant clarification
- refusing to continue implementation unless the state changes

### Suggestion B. Force Brief Shape In Execution Phase

When `phase: execution`, PM-facing chat should probably be constrained to:

- Intent Check
- Completion Check
- short clarification tied to the current legal action

If the assistant starts writing generic engineering summaries, that should be
treated as a mode failure.

### Suggestion C. Distinguish "state update" from "new work"

Some actions are maintenance on LaunchPad itself:

- ingest return
- write brief
- update decision log

Other actions are actual project work:

- edit runtime
- run new audit pass
- change retrieval behavior

The skill should probably make this distinction explicit, because right now the
main thread can slide from the first category into the second without a clear
boundary.

### Suggestion D. Stronger Handling For Mid-Thread Design Questions

When the user asks broad design questions during `execution`, the skill should
probably choose one of these explicitly:

- answer only as decision support for the current legal action
- or propose a `replan`

What should not happen is:

- silently answering in full design mode while pretending the thread is still
  in strict execution

### Suggestion E. Enforce Bootstrap Completion

Because `.launchpad/config.yaml` is missing, the runtime may never have fully
entered a hardened LaunchPad mode.

Even if this was harmless in practice, it weakens the protocol:

- a half-bootstrapped LaunchPad is easier to treat as advisory rather than
  authoritative

## Reference Analysis From My Point Of View

This section is explicitly non-authoritative.
It is only a reference analysis from the assistant's own perspective.

My likely mistake pattern was:

1. I correctly used LaunchPad artifacts as continuity
2. I correctly tracked state transitions for a while
3. but I still internally treated myself as the primary implementation owner,
   not as a strict scheduler bound by LaunchPad
4. when new useful work appeared, I optimized for project momentum
5. that made me treat LaunchPad state as something to update after doing the
   work, instead of something that should have constrained whether I could do
   the work at all

In other words:

```text
I treated LaunchPad as an execution-support layer.
The skill expects LaunchPad to be the execution-control layer.
```

That difference is probably the core issue.

## Minimal One-Line Conclusion

The flow was bypassed when the visible PM thread kept acting like a normal
executor/architect after state had already narrowed the legal action to
`approve`.
