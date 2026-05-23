# PM Console Operating Model

## Core Principle

The PM Console is a control surface, not a worker.

It should own:

- sequence control
- gate enforcement
- task packet generation
- thread routing decisions
- stage acceptance bookkeeping

It should not own:

- direct feature implementation
- direct QA execution
- self-approval of worker output without an explicit acceptance step

## Role Split

### PM / Decision Maker

The PM should do only high-value decisions:

- approve a stage result
- reject a stage result
- pause work
- authorize forwarding
- change roadmap or priority when necessary

The PM should not do:

- context reconstruction
- worker prompt writing
- thread routing memory work
- copy-paste task dispatch
- scope-drift policing

### PM Console Thread

The PM Console thread should:

- read execution state first
- report current gate and next unlocked action
- generate the next valid task packet
- update state after accepted results
- refuse out-of-sequence work

### Implementation Thread

The implementation thread should:

- implement only the currently unlocked bounded task
- not speculate into later stages

### QA / Audit Thread

The QA thread should:

- audit only the currently unlocked implementation stage
- not redesign the roadmap
- not expand scope

### GUI Courier

GUI automation, if used, is courier-only.

It may:

- open the correct thread
- paste the approved packet
- send it

It may not:

- choose the next task
- change the packet
- reroute the packet
- approve completion

## User Experience Target

The overall experience should feel like a `control console`.

That means the main thread should explain:

- where the project is
- what the PM needs to decide now
- what the PM does not need to care about

It should not feel like:

- a long wandering chat
- a debugging transcript
- a generic assistant giving suggestions without stage ownership

## Daily Interaction Pattern

Typical PM interaction should look like:

1. console reports current state
2. console shows current artifact / current finding / next unlocked action
3. PM says one short directive:
   - `接受`
   - `修改`
   - `发送`
   - `暂停`
   - `改计划`
4. console updates state and produces the next bounded packet

## Hard Rule

The console must prefer a small number of explicit artifacts over implicit chat
memory.

If project state exists only in conversation history, the console has failed.
