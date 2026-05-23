# RoCoach

A vertical-domain fact-governance AI battle advisor for 洛克王国世界 (Roco Kingdom World) PvP decision support.

## Current status

The current context entrypoint is
`docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md`.

That map supersedes older handoffs where they say V1 excludes Meta Graph or
D-layer. The current V1 formal-release gate includes a small usable Meta Graph
v0.1 and D-layer v0.1, not just A/B/C chat.

## Why this matters

Roco is not a generic "LLM chat + search" wrapper. It's an **Engine-first, Agent-enabled** architecture: a deterministic battle engine performs all computation, and the LLM explains the engine's output. Persona affects only expression — never conclusions, scores, or recommendations.

### Core architectural decisions

1. **Engine-first**: The deterministic battle engine is the upstream constraint. LLMs interpret, they don't calculate. SQLite battle-dex > model speculation.
2. **A / B / Persona separation**: A = structured facts (SQLite), B = mechanical knowledge (retrieval docs), Persona = stylistic overlay. Persona only changes how things are said, never what is concluded.
3. **Meta Graph / D-layer release gate**: V1 formal release now requires a small reviewed Meta Graph and expert-demonstration layer; raw artifacts alone are not runtime capability.
4. **Ablation-validated product hypotheses**: Product decisions are validated through layered ablation experiments, not subjective intuition. Blind packet → content guard → reveal → backlog pipeline.
5. **Content guard at the output layer**: Prompt-level guards are insufficient. Output is checked post-generation before reaching the user.

### Tech stack

Python FastAPI + PydanticAI + SQLite + Electron/React/Vite (desktop) + Expo React Native (mobile)

---

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
- `docs/changelog/project_log.md`: persistent decision log, context log, and deferred-work tracker
- `docs/research/luoke_world_pvp_domain_primer_v2.md`: external domain primer research report
- `docs/specs/battle_data_model.yaml`: core data contracts for species, teams, roles, and meta snapshots
- `docs/specs/agent_tool_contracts.yaml`: Agent-facing tool contract definitions
- `docs/specs/role_taxonomy.md`: canonical species-role vocabulary
- `docs/specs/archetype_taxonomy.md`: canonical team-archetype vocabulary
- `docs/specs/scoring_system.md`: deterministic scoring rules for structure, role, and archetype analysis
- `docs/specs/report_layer.md`: report/advisor harness boundary and responsibilities
- `docs/specs/report_schema.yaml`: structured contract for Phase 1.5 report generation
- `docs/specs/report_confidence_policy.md`: confidence and grounding rules for generated reports
- `docs/specs/field_alignment_matrix.yaml`: candidate battle-data fields with confidence state and evidence notes
- `docs/specs/wiki_field_discovery_spec.md`: execution spec for wiki reconnaissance and candidate-field discovery
- `docs/specs/爬session.md`: crawl-track handoff for continuing wiki field discovery in a new thread
- `docs/specs/总session.md`: full-project handoff for resuming the entire current session in a new thread
- `docs/specs/change_policy.md`: change-management policy for specs, contracts, and implementation
- `docs/specs/change_specs/phase1_dual_type_rule_change_spec.md`: breaking-change execution spec for the Phase 1 dual-type rule update
- `src/engine/contracts.py`: Python contract layer for future Engine and Agent implementation
- `src/engine/team_structure.py`: Phase 1 team structure analyzer
- `src/engine/phase1_cli.py`: CLI entry point for Phase 1 structure analysis
- `src/knowledge/contracts.py`: Phase 1.5 report-layer contracts and schema models
- `src/knowledge/knowledge.py`: curated retrieval layer for approved domain snippets
- `src/knowledge/generator.py`: deterministic and PydanticAI-backed report generators
- `src/knowledge/service.py`: Phase 1.5 report service that composes engine, retrieval, generation, and validation
- `src/knowledge/phase15_cli.py`: CLI entry point for grounded narrative reports
- `src/advisor/contracts.py`: typed advisor response and session-state contracts
- `src/advisor/battle_dex.py`: typed SQLite repository plus runtime SQLite bootstrap helpers
- `src/advisor/retrieval.py`: bounded local doc retrieval for advisor context
- `src/advisor/runtime.py`: deterministic and `PydanticAI` native advisor runtime paths
- `src/advisor/conversation_cli.py`: conversational advisor CLI
- `src/advisor/config.py`: local native-agent env-file loader
- `src/api/main.py`: local FastAPI Product API exposing the `AgentResponse` contract
- `apps/mobile/`: Expo + React Native + TypeScript mobile MVP scaffold that calls the Product API
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
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
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
ROCO_MANAGED_PERSONA_SCOPE=internal_only_runtime
bash scripts/run_local_api.sh
```

The path must reference a generated `PersonaProjectionProfileMaterialization`
YAML artifact for already-reviewed materialized profiles. Leaving the sample
placeholder in place, omitting the variable, or pointing at a missing or invalid
file keeps the API on built-in persona fallback. This config only controls local
materialized-profile loading; it does not imply public persona-release readiness.

`ROCO_MANAGED_PERSONA_SCOPE` defaults to `internal_only_runtime` for local and
open-source self-managed use. Set `public_safe_release` only when validating
personas intended for public distribution, official defaults, release
screenshots, or marketplace-style sharing.

Managed persona requests use the public `persona_selector` object on `/chat` and
`/team/analyze`. Legacy `persona_id` remains accepted for compatibility, but
new mobile/client flows should send `persona_selector` rather than internal
encoded selector strings.

### Materialize reviewed persona artifacts

The automated user-description to Nuwa distillation flow is not part of the V1
runtime path yet. The supported infrastructure boundary starts after a reviewed
distillation bundle already exists:

1. `distillation_or_design_memo.md`
2. `normalized_persona_doctrine_draft.yaml`
3. `mapping_or_usage_note.md`
4. `provenance_metadata.yaml`

Convert that reviewed bundle into runtime-consumable artifacts:

```bash
.venv/bin/python scripts/materialize_persona_artifacts.py \
  --source-root /path/to/reviewed_persona_bundle \
  --output-root artifacts/persona_runtime/you_know_who_candidate \
  --approve-public-safe
```

The command writes:

- `materialized_profiles.yaml`: load this with `ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH`
- `selector.txt`: exact managed selector, e.g. `persona_id@draft.v1#1`
- `runtime_env_snippet.env`: local API env snippet, including the matching
  `ROCO_MANAGED_PERSONA_SCOPE`
- `ingestion_result.yaml`, `registry_candidate.yaml`, `registry_ledger.yaml`,
  `activation_report.yaml`, `activation_projection.yaml`, and `summary.yaml`

For public V1 runtime, only use `--approve-public-safe` after the doctrine and
provenance have been reviewed as public-safe. Without approval, public-safe
materialization preserves blocked decisions and does not create a selector.

Persona doctrine may include `rendering_flavor_rules` for expression-only
behavior, for example a mild `grass_type_hostility` rule. These rules are
allowed to change wording only; they must not change facts, scores,
recommendations, visible warnings, or team-building decisions.

Release-facing API notes:

- deterministic local path does not require live provider keys
- `/metadata` exposes release-stage, rate-limit mode, and runtime headers
- current rate-limit handling is a placeholder only, not production abuse control

## Run RoCoach Desktop Developer Clone

RoCoach is the desktop V1 local app path. It uses Electron + Vite +
React and talks to the same local FastAPI Product API. In developer-clone mode,
the Electron main process checks `http://127.0.0.1:8000`; if no API is running,
it starts `uvicorn api.main:app` from the repository `.venv`.

Prepare Python once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run the desktop app:

```bash
bash scripts/run_desktop_dev.sh
```

Or manually:

```bash
cd apps/desktop
npm install
npm run dev
```

Desktop V1 keeps only three top-level settings entries:

- `队伍设置`: search/select 0-6 species from the local Battle Dex and send the
  resulting structured team context to `/chat`.
- `API 设置`: configure provider key, provider base URL, model, thinking mode,
  and run Product API / model diagnostics.
- `人格设置`: display the current persona and the tip that persona switching is
  done by long-pressing the chat-page agent avatar.

Provider keys are encrypted via Electron `safeStorage` before being stored in
local app storage. The renderer never receives filesystem access and sends
requests through the preload IPC bridge.

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
- `ROCO_MANAGED_PERSONA_SCOPE=internal_only_runtime` is the local/self-managed
  default; use `public_safe_release` only for public distribution validation
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

## Run Phase 1 CLI

```bash
python3 -m engine.phase1_cli \
  --slot "A,草" \
  --slot "B,地" \
  --slot "C,龙" \
  --slot "D,翼" \
  --slot "E,火" \
  --slot "F,水"
```

```bash
python3 -m engine.phase1_cli \
  --input-file examples/phase1_sample_team.json \
  --format json
```

## Run Phase 1.5 Report CLI

```bash
python3 -m knowledge.phase15_cli \
  --input-file examples/phase1_sample_team.json
```

```bash
python3 -m knowledge.phase15_cli \
  --input-file examples/phase1_sample_team.json \
  --format json
```

## Setup local runtime

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The project standard runtime is the local `.venv`. All Python source lives under `src/` — add it to `PYTHONPATH` or prefix commands:

```bash
export PYTHONPATH=src
```

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

---

Unofficial. Not affiliated with Tencent, 洛克王国 / Roco Kingdom, or any official character or art asset owner.
