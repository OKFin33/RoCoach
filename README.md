# Roco World Attribute Model

This repository contains a Python model of the attribute relationships extracted from the provided `洛克王国世界` screenshots.

## Included data

- 18 attributes:
  - `普通`, `草`, `火`, `水`, `电`, `冰`, `地`, `虫`, `武`, `翼`, `龙`, `毒`, `萌`, `光`, `幽`, `恶`, `幻`, `机械`
- Status immunities visible in the screenshots:
  - `草 -> 寄生`
  - `火 -> 灼烧`
  - `冰 -> 冻结`
  - `毒 -> 中毒`

## Files

- `data/roco_world_type_chart.json`: canonical chart extracted from the screenshots
- `data/reference/luoke_world_type_database_v2.json`: external updated type database source, staged for review before engine integration
- `roco_world_model.py`: query API for single-type and dual-type effectiveness
- `docs/battle_analysis_architecture.md`: Engine-first architecture for the battle-analysis system
- `docs/domain_primer.md`: internal canonical PvP domain primer for system design
- `docs/agent_framework_decision.md`: framework-adoption decision and upgrade triggers for the report/advisor layer
- `docs/model_centric_option_c.md`: recorded future model-centric advisor architecture and adoption preconditions
- `docs/combat_ontology.md`: battle-analysis ontology for species, move, and ability entities
- `docs/data_source_strategy.md`: source-tier policy for field discovery and later battle-data ingestion
- `log/project_log.md`: persistent decision log, context log, and deferred-work tracker
- `docs/research/luoke_world_pvp_domain_primer_v2.md`: external domain primer research report
- `specs/battle_data_model.yaml`: core data contracts for species, teams, roles, and meta snapshots
- `specs/agent_tool_contracts.yaml`: Agent-facing tool contract definitions
- `specs/role_taxonomy.md`: canonical species-role vocabulary
- `specs/archetype_taxonomy.md`: canonical team-archetype vocabulary
- `specs/scoring_system.md`: deterministic scoring rules for structure, role, and archetype analysis
- `specs/report_layer.md`: report/advisor harness boundary and responsibilities
- `specs/report_schema.yaml`: structured contract for Phase 1.5 report generation
- `specs/report_confidence_policy.md`: confidence and grounding rules for generated reports
- `specs/field_alignment_matrix.yaml`: candidate battle-data fields with confidence state and evidence notes
- `specs/wiki_field_discovery_spec.md`: execution spec for wiki reconnaissance and candidate-field discovery
- `specs/爬session.md`: crawl-track handoff for continuing wiki field discovery in a new thread
- `specs/总session.md`: full-project handoff for resuming the entire current session in a new thread
- `specs/change_policy.md`: change-management policy for specs, contracts, and implementation
- `specs/change_specs/phase1_dual_type_rule_change_spec.md`: breaking-change execution spec for the Phase 1 dual-type rule update
- `battle_engine/contracts.py`: Python contract layer for future Engine and Agent implementation
- `battle_engine/team_structure.py`: Phase 1 team structure analyzer
- `battle_engine/phase1_cli.py`: CLI entry point for Phase 1 structure analysis
- `reporting/contracts.py`: Phase 1.5 report-layer contracts and schema models
- `reporting/knowledge.py`: curated retrieval layer for approved domain snippets
- `reporting/generator.py`: deterministic and PydanticAI-backed report generators
- `reporting/service.py`: Phase 1.5 report service that composes engine, retrieval, generation, and validation
- `reporting/phase15_cli.py`: CLI entry point for grounded narrative reports
- `advisor/contracts.py`: typed advisor response and session-state contracts
- `advisor/battle_dex.py`: typed SQLite repository plus runtime SQLite bootstrap helpers
- `advisor/retrieval.py`: bounded local doc retrieval for advisor context
- `advisor/runtime.py`: deterministic and `PydanticAI` native advisor runtime paths
- `advisor/conversation_cli.py`: conversational advisor CLI
- `advisor/config.py`: local native-agent env-file loader
- `api/main.py`: local FastAPI Product API exposing the `AgentResponse` contract
- `mobile/`: Expo + React Native + TypeScript mobile MVP scaffold that calls the Product API
- `examples/phase1_sample_team.json`: example file-based input for the Phase 1 CLI
- `tests/test_roco_world_model.py`: validation and regression tests
- `tests/test_contracts.py`: contract serialization and shape tests
- `tests/test_team_structure.py`: Phase 1 analyzer and CLI tests
- `tests/test_reporting.py`: Phase 1.5 report service and CLI tests
- `tests/test_advisor.py`: advisor repository, CLI, and native runtime tests
- `requirements.txt`: minimal Python dependencies for the report/advisor layer, including PydanticAI slim

## Example

```python
from roco_world_model import RocoWorldTypeChart

chart = RocoWorldTypeChart()

print(chart.attack_multiplier("火", "草"))              # 2.0
print(chart.combined_multiplier("水", ("火", "地")))   # 3.0
print(chart.immune_statuses(("草", "火")))             # ("寄生", "灼烧")
```

## Run tests

```bash
.venv/bin/python -m unittest discover -s tests
```

## Run local Product API

```bash
bash scripts/run_local_api.sh
```

The API exposes `/health`, `/metadata`, `/chat`, `/team/analyze`,
`/species/search`, and `/species/{species_id}`.

`scripts/run_local_api.sh` reads `~/.config/roco-advisor/env` when present.
Managed persona runtime selection is opt-in only:

```bash
ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH=/path/to/materialized_profiles.yaml
bash scripts/run_local_api.sh
```

The path must reference a generated `PersonaProjectionProfileMaterialization`
YAML artifact for already-reviewed public-safe materialized profiles. Leaving
the sample placeholder in place, omitting the variable, or pointing at a missing
or invalid file keeps the API on built-in public-safe persona fallback. This
config only controls local materialized-profile loading; it does not imply
public persona-release readiness.

Managed persona requests use the public `persona_selector` object on `/chat` and
`/team/analyze`. Legacy `persona_id` remains accepted for compatibility, but
new mobile/client flows should send `persona_selector` rather than internal
encoded selector strings.

Release-facing API notes:

- deterministic local path does not require live provider keys
- `/metadata` exposes release-stage, unofficial notice, and rate-limit mode
- current rate-limit handling is a placeholder only, not production abuse control
- the product is unofficial and is not officially authorized, sponsored, or
  affiliated with Tencent, 洛克王国 / Roco Kingdom, or any official character or
  art asset owner

## Safe sample config

```bash
mkdir -p ~/.config/roco-advisor
chmod 700 ~/.config/roco-advisor
cp .env.example ~/.config/roco-advisor/env
chmod 600 ~/.config/roco-advisor/env
```

Important:

- `.env.example` is a safe sample only
- do not store real secrets in the repository
- deterministic API/CLI usage does not require native-provider config
- `ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH=replace-with-materialized-profile-path`
  is an inert placeholder; replace it only with a local generated materialized
  profile artifact path when testing managed personas
- native config becomes active only after replacing the placeholder API key in
  `~/.config/roco-advisor/env`

## Run Mobile MVP

```bash
bash scripts/run_mobile.sh
```

The mobile scaffold is local-development only. Configure the API base URL in
the Settings screen:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- physical device: use the backend machine LAN IP

The mobile app is a Product API client only. It does not read SQLite, shell out
to the CLI, call model providers, accept provider keys, or duplicate advisor
logic.

The mobile shell is also unofficial and does not bundle official character
assets, official screenshots, or official authorization positioning.

## Run Phase 1 CLI

```bash
python3 -m battle_engine.phase1_cli \
  --slot "A,草" \
  --slot "B,地" \
  --slot "C,龙" \
  --slot "D,翼" \
  --slot "E,火" \
  --slot "F,水"
```

```bash
python3 -m battle_engine.phase1_cli \
  --input-file examples/phase1_sample_team.json \
  --format json
```

## Run Phase 1.5 Report CLI

```bash
python3 -m reporting.phase15_cli \
  --input-file examples/phase1_sample_team.json
```

```bash
python3 -m reporting.phase15_cli \
  --input-file examples/phase1_sample_team.json \
  --format json
```

## Setup local runtime

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The project standard runtime is the local `.venv`.

## Run conversational advisor CLI

Default path:

```bash
.venv/bin/python -m advisor.conversation_cli
```

The default backend is `auto`:

- if `~/.config/roco-advisor/env` contains valid native model config, CLI uses
  `pydantic_ai_native`
- otherwise CLI falls back to `deterministic`
- if native provider/model execution fails or times out while selected by
  `auto`, supported flows fall back to `deterministic`
- after such a native failure, the same CLI process marks native unhealthy and
  skips repeated native timeout windows for later supported messages
- explicit `--backend deterministic` and `--backend pydantic_ai_native`
  override `auto`

```bash
.venv/bin/python -m advisor.conversation_cli \
  --message "/set-team 草 地 龙 翼 火 水" \
  --message "分析这队联防" \
  --message "/species 豆丁鱼"
```

Native `PydanticAI` path:

1. Create a local env file outside the project tree:

```bash
mkdir -p ~/.config/roco-advisor
chmod 700 ~/.config/roco-advisor
cp .env.example ~/.config/roco-advisor/env
chmod 600 ~/.config/roco-advisor/env
```

Then edit `~/.config/roco-advisor/env` and replace
`ROCO_OPENAI_API_KEY=replace-with-live-local-secret` with a real local secret.

2. Run the native advisor backend:

```bash
.venv/bin/python -m advisor.conversation_cli
```

Or force native mode explicitly:

```bash
.venv/bin/python -m advisor.conversation_cli --backend pydantic_ai_native
```

Optional overrides:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend pydantic_ai_native \
  --env-file ~/.config/roco-advisor/env \
  --model-name kimi-k2.5
```

Bound native runtime calls:

```bash
.venv/bin/python -m advisor.conversation_cli \
  --backend pydantic_ai_native \
  --native-timeout 15
```

Notes:

- Keys must not be stored inside the project directory.
- Default CLI backend is `auto` during migration, falling back to deterministic
  when native config is absent or native execution fails under `auto`.
- `auto` keeps this fallback session-local: it does not persist native health
  across CLI processes.
- Explicit `--backend pydantic_ai_native` returns a bounded native failure
  response instead of silently falling back.
- `pydantic_ai_native` is the approved runtime direction for the conversational
  advisor.
- Future/live-meta questions are refused without web search: the current MVP has
  no web/live official-balance feed and cannot predict future buffs/nerfs or
  live meta changes.
