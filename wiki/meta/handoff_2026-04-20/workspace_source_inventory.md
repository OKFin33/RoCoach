# Battle Wiki Workspace Source Inventory

## Purpose

List the existing Roco workspace sources the new Battle Wiki thread should read
before designing the B-layer wiki.

This inventory intentionally separates:

- domain facts and boundaries
- structured A-layer data
- existing B-layer-related specs
- persona materials that should not be merged into generic B

## Must-Read Domain Boundary

- [docs/domain_primer.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/domain_primer.md)
  - current internal domain primer
  - explicitly states Roco targets `洛克王国：世界`
  - warns against treating the game as Pokemon

- [docs/research/luoke_world_pvp_domain_primer_v2.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/research/luoke_world_pvp_domain_primer_v2.md)
  - deeper research primer
  - contains mechanics such as 魔力, 能量, 应对, 属性倍率, 速度
  - use with confidence labels; not all sections should become hard runtime
    truth

- [docs/combat_ontology.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/combat_ontology.md)
  - defines species / form / move / ability boundaries
  - forbids importing fields by Pokemon-like intuition

## Structured A-Layer Sources

- [data/runtime/battle_dex.sqlite](/Users/okfin3/project/GitHub/OKFin33/Roco/data/runtime/battle_dex.sqlite)
  - current SQLite battle-dex
  - contains structured species, moves, derived abilities, provenance
  - as checked in this thread:
    - `species_form`: 566
    - `move`: 493
    - `derived_ability`: 180

- [specs/battle_dex_sqlite_schema_v1.sql](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_sqlite_schema_v1.sql)
  - SQLite schema for A-layer facts

- [specs/battle_data_model.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_data_model.yaml)
  - battle data model

- [data/reference/luoke_world_type_database_v2.json](/Users/okfin3/project/GitHub/OKFin33/Roco/data/reference/luoke_world_type_database_v2.json)
  - type chart and key formulas

- [data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml)
  - manually reviewed corrections and supplements
  - important evidence that raw wiki facts can be stale or wrong

## Existing Retrieval / Wiki Design Sources

- [specs/llm_wiki_rag_necessity_review.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/llm_wiki_rag_necessity_review.md)
  - says full LLM Wiki is not needed for near-term A-layer exact fact lookup
  - still compatible with a later B-layer doctrine wiki

- [specs/retrieval_architecture_spec.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_architecture_spec.md)
  - defines hybrid local RAG:
    - structured retrieval
    - doc retrieval
    - case retrieval

- [specs/retrieval_eval_spec.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/retrieval_eval_spec.md)
  - retrieval evaluation requirements

- [advisor/retrieval.py](/Users/okfin3/project/GitHub/OKFin33/Roco/advisor/retrieval.py)
  - current bounded curated retrieval implementation
  - very small rule-based snippet table, not full B Wiki

## Existing B-Layer-Adjacent Specs

- [specs/p1a_reasoning_synthesis_layer.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1a_reasoning_synthesis_layer.md)
  - defines `Synthesize(A, B)`
  - currently allows reasoning-facing persona doctrine subset, but the new
    Battle Wiki thread should keep generic B separate from persona overlays

- [specs/reasoning_synthesis_contract.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/reasoning_synthesis_contract.yaml)
  - synthesis output contract

- [specs/agent_tool_contracts.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/agent_tool_contracts.yaml)
  - tool contracts and A/B layering assumptions

- [specs/tactical_casebank_spec.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/tactical_casebank_spec.md)
  - casebank scope, entities, confidence tiers
  - should probably become part of Battle Wiki architecture

- [specs/role_taxonomy.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/role_taxonomy.md)
  - role taxonomy, but should be reviewed for Roco-native terminology

- [specs/archetype_taxonomy.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/archetype_taxonomy.md)
  - archetype taxonomy

- [specs/semantic_role_policy.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/semantic_role_policy.md)
  - policy for semantic role judgement

- [specs/report_confidence_policy.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_confidence_policy.md)
  - confidence language and boundaries

## Persona Materials: Read Only For Separation Boundary

The new Battle Wiki thread may inspect these only to understand what must stay
outside generic B:

- [specs/enzo_integration_review.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/enzo_integration_review.md)
- [specs/persona_doctrine_contract.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/persona_doctrine_contract.yaml)
- [docs/personas/enzo_internal_persona_doctrine.yaml](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/personas/enzo_internal_persona_doctrine.yaml)

Do not treat these as default Battle Wiki doctrine.

## Current Implementation Risk To Audit Later

- [agent_core/synthesis.py](/Users/okfin3/project/GitHub/OKFin33/Roco/agent_core/synthesis.py)
  - currently defaults to `internal_enzo_pattern_pack`
  - this should be treated as an audit finding against B/persona separation if
    it remains the default product doctrine

