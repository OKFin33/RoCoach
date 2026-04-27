# Project Meta Layer

This directory is the canonical home for project-level governance,
maintenance, and usage rules.

It corresponds to the conceptual `C` layer:

```text
A = exact facts / structured data / engine-facing truth
B = doctrine / wiki / compiled battle understanding
C = governance / maintenance / usage / enforcement policy
```

## Directory Meaning

- `data/`
  - governance for A-layer assets
  - schema, import, provenance, and resolution policy
- `wiki/`
  - governance for B-layer assets
  - review lifecycle, compile/export contract, mechanism-lookup policy,
    and Battle Wiki usage boundaries

Future project-wide governance domains may be added here without changing the
A/B content directories themselves.

## Boundary With Other Top-Level Directories

- `data/` and `wiki/` contain the assets themselves
- `meta/` contains the rules about how those assets are created, maintained,
  and consumed
- `specs/` remains primarily a development-process and execution directory, not
  the canonical home for long-lived product governance

## Current Transition Note

Historical Battle Wiki handoff packets already exist under `wiki/meta/`.
Those files remain valid as thread-context artifacts, but new canonical
governance material should be written under root `meta/`.
