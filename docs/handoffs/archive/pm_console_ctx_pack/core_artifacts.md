# PM Console Core Artifacts

## Overview

The PM Console is defined by a small set of explicit artifacts.

These artifacts are the minimum viable operating system for the console.

## 1. Locked Execution Plan

Purpose:

- define the sequence of stages
- define gate rules
- define what is blocked until which acceptance point

Typical contents:

- stage order
- gate conditions
- allowed thread ownership
- non-interruption rules
- exit criteria

## 2. Execution State

Purpose:

- record where the project currently is
- record which stage is completed, unlocked, or blocked
- record the next allowed action

Typical contents:

- current gate
- sequence progress
- next action
- blocked tracks
- latest completed artifacts
- forwarding whitelist

The execution state is what allows a fresh control-console thread to start
without rereading the entire project history.

## 3. Task Packet Template

Purpose:

- make handoff transport deterministic
- make worker prompts bounded and reusable

A valid task packet should include:

- `Executor`
- `Read <absolute spec path> first.`
- status
- task
- scope
- do-not list
- deliverables
- validation
- return format

This turns forwarding into transport work rather than interpretation work.

## 4. Handoff Document

Purpose:

- let a new PM console thread or repo start from clean context
- avoid carrying the full legacy conversation into the future

A handoff document should specify:

- what documents are authoritative
- current project position
- current next unlocked step
- what the new console must not do

## 5. Optional GUI Courier Rule

Purpose:

- reduce manual copy-paste work without handing scheduling control to GUI
  automation

This is optional.

If present, it should explicitly say:

- courier may only forward approved packets
- courier may not choose tasks or targets

## Minimal First-Version Artifact Set

A standalone PM Console project does not need much more than:

- `locked_execution_plan.md`
- `execution_state.yaml`
- `task_packet_template.md`
- `console_handoff.md`

Anything heavier than this should be justified by clear user pain, not by
infrastructure appetite.
