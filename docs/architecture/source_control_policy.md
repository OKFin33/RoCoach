# Source Control Policy

Date: 2026-04-20

## Git Boundary

`Roco/` is the intentional Git worktree root.

Do not silently move this active workspace into a sibling repository. The active
workspace contains code, specs, docs, tests, tools, data artifacts, mobile
assets, and wiki assets that belong to this product boundary.

## Root Ignore Policy

The root `.gitignore` protects:

- local operating-system files
- Python virtual environments and caches
- local environment secrets
- mobile dependency folders
- generated mobile output
- logs, temporary files, and coverage artifacts

It intentionally does not ignore:

- source code
- specs
- docs
- tests
- tools
- examples
- safe wiki pages
- safe structured reference data
- `.env.example`
- mobile source manifests

## A-Layer SQLite Policy

Current A-layer runtime database:

```text
data/runtime/battle_dex.sqlite
```

Short-term policy:

- `data/runtime/battle_dex.sqlite` may be committed only if Product API or
  advisor MVP execution cannot be rebuilt or run reliably from committed source
  artifacts alone.
- If committed, treat it as a versioned runtime artifact, not an editable source
  of truth.

Long-term policy:

- prefer rebuilding SQLite from committed source data, schema, supplements, and
  importer tools
- commit schema, manifests, checksums, and source inputs
- avoid binary SQLite diffs as the normal review surface

## Importer And Crawler Artifact Policy

These paths require explicit triage before staging:

```text
data/wiki_ingestion_runs/
data/importer_runs/
data/wiki_field_discovery/
```

Commit only reviewed summaries, manifests, validation events, and small
provenance-bearing artifacts required for reproducibility.

Do not commit:

- raw scrape dumps
- large unbounded JSONL artifacts
- copyrighted full-text captures
- credentials
- cookies
- session material
- private raw chat logs

## B-Layer Wiki Policy

`wiki/` is the root B-layer knowledge surface.

Layer split:

```text
data/ = A-layer facts and runtime artifacts
wiki/ = B-layer battle doctrine surface
docs/ = ordinary documentation, reports, primers
specs/ = system-level contracts and architecture specs
```

The Battle Wiki must remain generic and persona-free. Persona overlays belong
downstream from B-layer doctrine.

