# Task Packet Template

## Purpose

Standardize the packet that the main thread sends to worker threads or forwards
through `Computer Use`.

This template exists so thread handoff becomes transport work instead of
interpretation work.

## Required Header

Every packet must start with these two lines:

```text
Executor: <approved thread name>
Read <absolute spec path> first.
```

If either line is missing, the packet is invalid and should not be forwarded.

## Packet Body Template

```text
Executor: <approved thread name>
Read <absolute spec path> first.

Status: <RUNNING | REVIEW | AUDIT | IMPLEMENT>

Task:
<one-sentence description of the bounded task>

Scope:
- <allowed item 1>
- <allowed item 2>

Do not:
- <forbidden item 1>
- <forbidden item 2>

Deliverables:
- <file or artifact 1>
- <file or artifact 2>

Validation:
- <command 1>
- <command 2>

Return format:
- Status
- Files changed
- Result
- Validation
- Scope confirmation
```

## Packet Construction Rules

1. One packet should correspond to one unlocked stage only.
2. The packet must point to a single controlling spec.
3. The packet must include a bounded `Do not` list.
4. Validation commands must be concrete and copyable.
5. If the task is review-only, do not ask the receiver to implement code.
6. If the task is implementation-only, do not ask the receiver to change
   product sequencing.

## Default Executor Mapping

- `主开发线程`
  - implementation tasks for the currently unlocked stage
- `QA-1`
  - primary audit / verification tasks for the currently unlocked stage
- `女娲线程`
  - bounded persona-source work only

## Courier Rule

When `Computer Use` forwards a packet, it must preserve the packet text
verbatim.

It may not:

- summarize the packet
- remove the `Do not` list
- change validation commands
- infer a different executor

## Non-Goal

This template is not a substitute for the execution plan or execution state.
It is only the transport envelope.
