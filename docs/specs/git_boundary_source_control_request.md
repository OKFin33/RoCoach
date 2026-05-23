# Git Boundary And Source-Control Request

Date: 2026-04-20

Audience: Roco PM-control / development-console thread

## Status

`Roco/` is currently outside the detected Git worktree.

Observed local layout:

```text
/Users/okfin3/project/GitHub/OKFin33/
  OKFin33/        # contains .git, currently only a minimal repo
  Roco/           # active Roco project workspace, no .git ancestor
```

This means edits inside:

```text
/Users/okfin3/project/GitHub/OKFin33/Roco
```

are not currently tracked by Git.

## Request

Decide and execute one Git boundary repair before treating Roco as a
source-controlled product workspace.

Recommended decision:

```text
Make /Users/okfin3/project/GitHub/OKFin33/Roco the Git worktree root.
```

Do not silently move the active project into the sibling `OKFin33/` repo without
an explicit migration plan, because the active Roco workspace already contains
code, data, specs, docs, mobile assets, tests, tools, and local runtime files.

## Required Git Policy

Create a root `.gitignore` before the first commit.

Must ignore:

```text
.DS_Store
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
!.env.example
mobile/node_modules/
mobile/.expo/
mobile/dist/
```

Recommended additional ignores:

```text
*.log
*.tmp
*.bak
coverage/
htmlcov/
wiki/cache/
```

Do not ignore:

```text
.env.example
requirements.txt
README.md
specs/
docs/
wiki/
examples/
tests/
tools/
scripts/
advisor/
agent_core/
api/
battle_engine/
reporting/
mobile/package.json
mobile/package-lock.json
mobile/App.tsx
mobile/app.json
mobile/tsconfig.json
data/reference/
data/manual_supplements/
data/roco_world_type_chart.json
```

`wiki/cache/` is the exception under `wiki/`: it is a local source-material
staging area for videos, transcripts, PDFs, screenshots, and intermediate
extractions. Commit reviewed notes under `wiki/raw/` and doctrine under
`wiki/pages/`, not the cache folder itself.

## Data Policy

The current A-layer database is:

```text
data/runtime/battle_dex.sqlite
```

Short-term policy:

- commit `data/runtime/battle_dex.sqlite` only if the Product API / advisor MVP
  cannot be rebuilt or run reliably from committed source artifacts alone
- if committed, mark it as a versioned runtime artifact, not an editable source
  of truth

Long-term policy:

- prefer rebuilding SQLite from committed source data, schema, supplements, and
  importer tools
- commit the schema, manifests, checksums, and source inputs
- do not treat binary SQLite diffs as the normal review surface

Importer and crawler artifacts require triage:

```text
data/wiki_ingestion_runs/
data/importer_runs/
data/wiki_field_discovery/
```

Commit only reviewed summaries, manifests, validation events, and small
provenance-bearing artifacts required for reproducibility.

Do not commit raw scrape dumps, large unbounded JSONL artifacts, copyrighted
full-text captures, credentials, cookies, session material, or private raw chat
logs.

## Wiki Placement Decision

The B-layer Battle Wiki should be a root-level project asset:

```text
wiki/
```

Reason:

- `data/` is the A-layer fact/data surface
- `wiki/` is the B-layer doctrine surface
- `docs/` remains for ordinary project documentation, primers, and reports
- `specs/` remains for system-level contracts and architecture specs

Recommended first layout:

```text
wiki/
  README.md
  meta/
  raw/
  pages/
  schema/
  compiled/
```

## Migration Request

After the Git boundary is repaired, migrate the current Battle Wiki context pack:

```text
docs/battle_wiki_ctx_pack/
```

to:

```text
wiki/meta/handoff_2026-04-20/
```

Keep a short redirect note at the old path for one transition window if other
threads still reference it.

## Acceptance Criteria

The console work is complete when:

- `Roco/` is under an intentional Git worktree
- a root `.gitignore` protects local environments, dependencies, caches, and
  secrets
- source code, specs, tests, examples, safe docs, safe wiki pages, and safe
  structured data are trackable
- `wiki/` exists as the root B-layer knowledge surface
- local secrets and generated dependency folders are not tracked
- the A-layer SQLite policy is explicitly recorded

## Non-Goals

This request does not ask the console to:

- modify runtime code
- change database schema
- import new battle data
- build live model-backed synthesis
- populate doctrine content beyond the initial Battle Wiki architecture surface
