# PM Console Project Brief

## What This Project Is

This project is a lightweight `PM execution console` for agent-native coding
workflows.

It is meant for scenarios where:

- one PM or decision-maker defines strategy
- one or more implementation threads execute bounded tasks
- one or more QA / audit threads verify results
- the project runs long enough that raw chat history becomes a liability

The console is not the worker.

Its job is to:

- know what stage the project is in
- know what the next allowed action is
- know which thread should receive the next task
- know what must be approved before the project can advance

## What Problem It Solves

Without a control console, multi-thread agent workflows usually decay into:

- context overload
- scope drift
- repeated rediscovery of project state
- unclear thread ownership
- copy-paste coordination fatigue
- accidental parallelization of tasks that should have been gated

The PM Console exists to remove that failure mode.

## What It Is Trying To Become

The target product experience is:

- the PM talks to a single control-console thread
- the console reports:
  - current state
  - current gate
  - last accepted artifact
  - next unlocked action
  - target executor, if a handoff is needed
- the PM mostly answers with short commands such as:
  - `接受`
  - `修改`
  - `发送`
  - `暂停`
  - `改计划`

The PM should not need to:

- remember which thread owns what
- manually rebuild context
- manually compose worker prompts
- manually keep project sequencing valid

## What It Is Not

This project is not:

- a generic chat assistant
- a heavy PM SaaS
- a Jira replacement
- a remote orchestration platform
- an autonomous multi-agent planner that self-approves its own work

It is a light control layer on top of an existing agent IDE / CLI environment.

## Current Design State

The concept has already been tested inside another project (`Roco`) and has
produced a stable operating pattern:

- locked execution plan
- machine-readable execution state
- bounded task packet template
- PM console handoff model
- GUI courier rule for thread forwarding

This means the project is beyond vague idea stage.

It already has:

- a usable operating model
- real artifacts
- a concrete migration path into its own repo

## First Build Goal

The first goal of the standalone PM Console project should be:

- make the control console itself clean and reusable
- preserve lightweight operation
- avoid building heavy infrastructure too early
- support agent-host environments such as Codex App, Codex CLI, and Claude Code

The first version should probably be:

- skill/package first
- thin file-driven runtime
- explicit artifacts
- optional GUI courier integration
