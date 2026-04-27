# P1 Locked Execution Plan

## Purpose

Define the locked execution sequence for the next phase of work so the project
does not drift into opportunistic implementation.

This document is a hard execution-order spec, not a brainstorming note.

## Core Rule

Do not parallelize major P1 tracks by default.

Until explicitly unlocked by the main thread, the project should advance in the
sequence defined below. Later tracks do not begin just because they are already
specified.

## Locked Sequence

The approved sequence is:

1. `Enzo integration review`
2. `P1a synthesis implementation spec`
3. `P1a implementation`
4. `P1a audit`
5. `P1b presentation implementation spec`
6. `P1b implementation`
7. `P1b audit`
8. only then revisit:
   - `P1c Pluggable Persona Contract`
   - `P1d Persona Source Adapter Contract`
   - `P1e Persona Artifact Ingestion`
   - `P1f Managed Persona Creation Pipeline`

## Gate Rules

### Gate 1. Before P1a spec

Required:

- Enzo integration review completed

Blocked before Gate 1 opens:

- implementation of synthesis layer
- implementation of presentation layer
- implementation of registry/runtime persona creation
- distillation of additional persona samples unless explicitly approved

### Gate 2. Before P1a implementation

Required:

- `P1a synthesis implementation spec` completed and accepted by main thread

Blocked before Gate 2 opens:

- direct code implementation of `agent_core/synthesis.py`
- runtime wiring for doctrine-driven synthesis

### Gate 3. Before P1b spec

Required:

- `P1a implementation` completed
- `P1a audit` passed or passed with accepted non-blocking findings

Blocked before Gate 3 opens:

- `Reply + Why` presentation implementation
- persona-first front-stage UX changes

### Gate 4. Before revisiting P1c/P1d/P1e/P1f implementation

Required:

- `P1b implementation` completed
- `P1b audit` passed or passed with accepted non-blocking findings

Blocked before Gate 4 opens:

- persona registry implementation
- persona source-adapter implementation
- persona ingestion implementation
- managed persona creation product flow

## Thread Assignment

### Main thread

Owns:

- sequence control
- SSD updates
- acceptance criteria
- review of Enzo integration conclusions
- unlock decisions for the next stage

### Main development thread

Owns:

- implementation only for the currently unlocked stage
- no speculative implementation of later stages

### Test / audit thread

Owns:

- audit only for the currently unlocked implementation stage
- no product-scope expansion

### Persona distillation thread

Owns:

- only explicitly requested persona-source work
- no runtime / registry / presentation implementation

Default rule:

- do not open another persona-distillation thread while Enzo integration review
  is still the active gate, unless main thread explicitly asks for comparison
  data

## Thread Forwarding Protocol

### Purpose

Allow the project to use a GUI courier such as `Computer Use` for thread
handoff without changing ownership, gate rules, or execution order.

### Hard Rule

`Computer Use` may act as a thread-forwarding courier only.

It may:

- open the correct existing thread
- paste the main-thread-approved task packet
- send the message

It may not:

- choose the next task
- choose the target thread
- rewrite the task spec
- summarize away constraints
- approve completion
- unlock later stages

### Allowed Forwarding Targets

Only the following existing threads are approved forwarding targets by default:

- `主开发线程`
- `QA-1`
- `女娲线程`

All other threads require an explicit main-thread instruction in the task
packet.

### Required Packet Header

Every forwarded task packet must begin with:

- `Executor: <approved thread name>`
- `Read <absolute spec path> first.`

If either line is missing, the packet should not be forwarded.

### Forwarding Safety Checks

Before forwarding, the courier must verify:

1. the target thread name exactly matches the approved executor
2. the spec path is absolute
3. the currently unlocked gate in this plan permits the requested task

If any of the above fail, forwarding must stop and return to the main thread.

## Non-Interruption Rules

The following may not interrupt the locked sequence unless the main thread
explicitly unlocks them:

- second persona sample distillation
- Nexus original-persona adapter work
- persona registry implementation
- persona ingestion implementation
- managed persona creation UI/UX
- session persistence
- embeddings
- case retrieval
- web-in-loop
- new mobile feature work beyond regression fixes

## Exit Criteria

### Enzo integration review complete

Means:

- doctrine fields are classified into:
  - retain
  - abstract
  - sanitize
  - forbid
- reusable generic persona patterns are identified
- task-adaptation implications are documented

### P1a complete

Means:

- synthesis contract is implemented
- grounded `A + B` reasoning path exists
- doctrine-facing persona inputs can influence synthesis without changing facts
- audit confirms:
  - no fact drift
  - no confidence drift
  - no refusal drift

### P1b complete

Means:

- default front-stage response is `Reply + Why`
- evidence/confidence/tool traces move to secondary inspectable layer
- audit confirms:
  - no factual drift
  - no confidence drift
  - warnings remain visible when required

## Hard Reminder

P1 is no longer "implement whatever persona-related thing seems useful next."

P1 is a controlled migration from:

`analytical payload + thin persona wrapper`

to:

`grounded facts + doctrine-driven synthesis + Reply/Why presentation`

If a proposed task does not clearly advance the currently unlocked gate, it
should be deferred.

The forwarding mechanism does not alter this rule. It only replaces manual
copy/paste.
