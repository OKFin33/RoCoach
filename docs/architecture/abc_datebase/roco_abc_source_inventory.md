# Roco A+B+C Source Inventory

## Purpose

This file inventories the primary local sources used to write the current-version
`Roco A+B+C` architecture book.

This is an Agent-facing working index, not a narrative summary.

## Evidence Classes

- `Normative`: accepted contract, architecture, or governance source
- `Implemented`: code or generated artifact proving current runtime reality
- `Historical`: decision memo or precursor that explains why the current design
  exists

## Canonical Sources

| Source | Class | Role In Book | Current Weight |
| --- | --- | --- | --- |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/README.md` | Normative | canonical A/B/C layer split and directory meaning | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/battle_wiki_decision_convergence_2026-04-21.md` | Normative | strongest explicit A/B/C convergence memo; explains why facts/doctrine/governance were split | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_wiki_architecture_spec.md` | Normative | formal B-layer architecture and A+B synthesis statement | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/meta/wiki/compile_use_contract_2026-04-22.md` | Normative | C-layer usage/enforcement rule for reviewed pages, compile, runtime downgrade | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/source_control_policy.md` | Normative | directory ownership model; `data/` vs `wiki/` boundary | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md` | Normative | A/B bridge shape: structured retrieval, doc retrieval, case retrieval | High |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml` | Normative | A-layer minimum data model for structured fact storage | High |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_repository_contract.md` | Normative | A-layer runtime access boundary; repository owns SQL interface | High |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/README.md` | Normative | B-layer entrypoint; explicitly persona-free and separate from A-layer facts | High |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1_architecture_refactor_plan.md` | Normative | higher-level post-P0 refactor model; useful for placing A/B/C relative to synthesis/presentation/persona | Medium |

## Implemented Reality Sources

| Source | Class | What It Proves | Current Weight |
| --- | --- | --- | --- |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py` | Implemented | current doc retrieval is bounded rule-based + mechanism-aware B-layer page lookup via compiled wiki | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/schema/compile_wiki.py` | Implemented | reviewed-page compiler exists; persona-free lint and required-section checks exist | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/compiled/manifest.yaml` | Implemented | reviewed B-layer compiled export currently exists; 23 reviewed pages compiled | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/data/runtime/battle_dex.sqlite` | Implemented | current A-layer runtime substrate exists as SQLite battle dex | Highest |

## Historical / Decision Sources

| Source | Class | Why It Matters | Current Weight |
| --- | --- | --- | --- |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md` | Historical | chronology of schema decisions, SQL-first retrieval boundary, LLM wiki deferral, mechanism-guard hardening, Battle Wiki governance closure | Highest |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md` | Historical | precursor architecture: engine + knowledge + agent layers before explicit A/B/C naming | Medium |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md` | Historical | records why full LLM Wiki / vector RAG was deferred in favor of structured KB first | High |

## Boundary / Future-Phase Sources

These are not primary sources for the current A+B+C runtime, but they help
state what is still out of scope.

| Source | Class | Why It Is Included | Current Weight |
| --- | --- | --- | --- |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_doctrine_contract.yaml` | Normative | proves persona is a downstream layer with fact-lock rules, not B-layer doctrine authority | Medium |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_source_adapter_contract.yaml` | Normative | proves persona source ingestion belongs to later pipeline work, not current A/B/C data runtime | Medium |
| `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_artifact_ingestion_contract.yaml` | Normative | proves ingestion/governance for persona is separate from Battle Wiki governance | Medium |

## Runtime Snapshot Captured During Authoring

These values were re-checked locally during authoring and can be used in the
architecture book as current implemented reality.

- A-layer SQLite counts from `data/runtime/battle_dex.sqlite`:
  - `species_form = 566`
  - `move = 493`
  - `derived_ability = 180`
  - `species_move_pool = 21974`
- B-layer compile check:
  - `python3 wiki/schema/compile_wiki.py` returned `compiled 23 reviewed pages`
- Reviewed compiled pages currently include:
  - mechanics pages
  - casebank pages
  - role taxonomy
  - team-building doctrine
  - recommendation-taste page

## Inventory Use Rules

- Prefer `Normative` sources over `Historical` sources when they conflict.
- Use `Implemented` sources only to describe current reality, not to redefine
  accepted architecture.
- Use `Historical` sources to explain origin, trade-off, and why certain
  boundaries exist.
- Do not treat persona pipeline sources as proof that persona is part of the
  current A/B/C runtime boundary.
