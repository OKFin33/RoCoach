# PM Console Context Pack

## Purpose

This context pack extracts the `PM control console` idea from the `Roco`
project so it can be moved into a separate project and developed on its own.

This pack is written for zero-context readers.

It explains:

- what the PM Console project is
- what user experience it is aiming for
- how the system works
- what artifacts define its operating model
- what should be carried into the new project
- what should stay behind in `Roco`

## Intended Product Shape

The target is not a generic chatbot and not a heavy project-management SaaS.

The target is:

- a lightweight PM execution console
- designed for agent-native coding workflows
- built around locked execution plans, stage gates, task packets, and thread
  routing discipline
- optimized for a PM who wants control without micromanaging context and
  copy-paste work

The intended user experience is:

- the PM interacts with one `control console` thread
- the console explains current state, next allowed action, and what needs
  approval
- workers and audit threads do the bounded execution
- GUI automation may be used as a courier, not as the scheduler

## Documents In This Pack

- [project_brief.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/project_brief.md)
- [operating_model.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/operating_model.md)
- [core_artifacts.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/core_artifacts.md)
- [migration_note.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/migration_note.md)
- [thread_delta_handoff_2026-04-20.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/thread_delta_handoff_2026-04-20.md)

## Minimal Kickoff Recommendation

If this pack is used to start a new project, the new thread or repo should
first read:

1. [project_brief.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/project_brief.md)
2. [operating_model.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/operating_model.md)
3. [core_artifacts.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/core_artifacts.md)
4. [migration_note.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/migration_note.md)
5. [thread_delta_handoff_2026-04-20.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/pm_console_ctx_pack/thread_delta_handoff_2026-04-20.md)
