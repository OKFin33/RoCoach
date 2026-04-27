# Battle Wiki Compile / Use Contract

Date: 2026-04-22

## Purpose

This document defines the current contract between:

- reviewed Battle Wiki doctrine pages
- compiled wiki exports
- runtime mechanism-aware retrieval

It is a governance document for Battle Wiki use.

It is not:

- an A-layer schema spec
- a runtime implementation plan
- a replacement for `wiki/schema/*`

## Contract Boundary

The Battle Wiki stack is split as follows:

- `wiki/raw/`
  - source notes and non-canonical extraction material
- `wiki/pages/`
  - reviewed doctrine pages and other Battle Wiki assets
- `wiki/compiled/`
  - machine-consumable export of reviewed pages
- `advisor/retrieval.py`
  - runtime mechanism token detection and page lookup

Only reviewed pages are allowed into the compiled layer that runtime consumes.

## What Runtime May Rely On

Runtime may rely on the following current properties:

1. a reviewed page under `wiki/pages/mechanics/` can compile into
   `wiki/compiled/`
2. mechanism tokens in `advisor/retrieval.py` can map to a reviewed page path
3. when the reviewed page exists and compiles, runtime may surface it as
   doctrine evidence
4. parent-topic retrieval is valid:
   - a token does not need a standalone page if a reviewed parent topic covers
     it cleanly

Runtime should not assume:

1. every important mechanic has a standalone page
2. compiled wiki content is equivalent to A-layer engine truth
3. `reviewed + provisional` means engine-executable certainty

## Safe Usage Rule

The governing rule is:

```text
reviewed + provisional is usable
raw is not runtime doctrine
```

This means:

- reviewed provisional pages may be used for explanation, interpretation, and
  tactical reasoning
- reviewed provisional pages must preserve uncertainty boundaries
- raw source notes must not be surfaced as doctrine authority

## Required Downgrade Rule

If runtime detects a mechanism-bearing token but no reviewed page is available,
the system must downgrade explicitly instead of improvising.

The minimum acceptable downgrade behavior is:

- state that the mechanism is referenced by move/ability text
- state that no reviewed mechanism page currently covers it
- avoid strong deterministic inference from that mechanism

## Parent-Topic Rule

Standalone page creation is not mandatory for every token.

A token is allowed to resolve to a parent topic when:

1. the parent page already covers the mechanism cleanly
2. the token does not need separate lifecycle/governance
3. retrieval remains useful without a dedicated page

Examples in the current version:

- mark subtypes -> `marks_and_persistence.md`
- `打断` -> `response_counterplay.md`
- `雪天` / `暴风雪` -> `weather_and_field_effects.md`

## Canonical Ownership

Canonical ownership is split as follows:

- `meta/wiki/`
  - governance, registry, and usage policy for Battle Wiki
- `wiki/pages/`
  - doctrine content
- `advisor/retrieval.py`
  - executable runtime token mapping

Therefore:

- governance decides what should exist and how it should be used
- runtime code decides what is currently executed
- when these diverge, both must be updated with traceable log entries

## Minimum Maintenance Discipline

Any change to mechanism coverage should leave evidence in at least one of:

- `meta/wiki/mechanism_registry_2026-04-21.md`
- `meta/wiki/mechanism_review_checklist_2026-04-21.md`
- `log/project_log.md`

This is mandatory because retrieval regressions are otherwise hard to
reconstruct.

## What This Contract Does Not Solve

This contract does not decide:

- how mechanisms should be structured in A-layer schema
- how system-wide validator policy should behave
- how future automated wiki-maintenance workflow should be implemented
- how global eval infrastructure should be executed

Those belong to console/main-thread implementation work.
