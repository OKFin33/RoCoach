# RoCoach Project Instructions

General Coco voice and collaboration behavior live in `~/.codex/AGENTS.md`.
This file contains only Roco-specific project context, constraints, and
verification rules.

## Current Entry

Before substantial work, read:

- `docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md`

This context map supersedes older V1/V2 boundary judgments in archived handoff
docs unless current repo evidence says otherwise.

## Product Boundary

Roco is a PvP battle advisor for 洛克王国世界.

Current V1 framing:

- single Agent Chat
- A/B/C layers
- Meta Graph v0.1
- D-layer v0.1
- S-Graph remains post-V1 unless current docs say otherwise

## Repository Map

- `src/api/` - FastAPI backend, contracts, runtime headers
- `src/advisor/` - battle advisor core, retrieval, runtime
- `src/agent_core/` - orchestration and persona registry
- `src/engine/` - deterministic battle engine and team structure
- `src/knowledge/` - knowledge retrieval, confidence, contracts
- `apps/mobile/` - Expo React Native MVP
- `apps/desktop/` - Electron + Vite desktop app
- `docs/specs/` - contracts, agent constitution, experiment plans, Meta Graph
- `docs/` - architecture, research, design, governance, changelog, handoffs
- `wiki/` - battle knowledge and compile pipeline
- `data/` - structured game data
- `tools/` - experiment harnesses and audits
- `artifacts/` - experiment inputs and outputs

## Architecture Constraints

1. Engine-first, Agent-enabled. The deterministic engine constrains the LLM.
   Do not do battle calculation inside the LLM.
2. SQLite battle-dex beats model guesswork.
3. A/B/Persona separation:
   - A = structured facts
   - B = mechanism knowledge
   - Persona = style only
4. Persona must not change conclusions, scores, or recommendations.
5. Meta Graph sits between A and B. Use species-set cards and relation graph
   before mechanism retrieval when relevant.
6. Facts must come from knowledge sources. Do not invent game facts from model
   memory.
7. Content guard belongs at output time too. Prompt-only guard is not enough.
8. Product quality claims require ablation evidence.

## Hard Constraints

- Never print real API keys.
- Provider key only travels in `X-Roco-Provider-Key`, never body or URL.
- Keep API contracts synced:
  `src/api/contracts.py` <-> `apps/mobile/src/api/types.ts`
- Keep runtime headers synced:
  `src/api/runtime_headers.py` <-> `apps/mobile/src/runtime/runtimeSettings.ts`
- Do not restore deleted screens:
  `SettingsScreen`, `SpeciesSearchScreen`, `TeamEditorScreen`.
- Paper texture uses `paper_shell.png` + `paper_outline.png`, not SVG.
- Do not treat session persistence as Agent continuity.

## Wiki Bridge

Project memory can flow to and from the central Obsidian wiki:

- wiki path: `/Users/okfin3/Documents/Obsidian`
- project slug: `roco`
- domain tags: `agent-architecture, fact-governance, product-methodology, game-ai`

Project-side agent memory is local in `.agent/` and should not be committed.

At session start, read `.agent/bridge-brief.md` if it exists locally. If it
does not exist or if project context needs refreshing, load
`/Users/okfin3/Documents/Obsidian/skills/wiki-bridge/SKILL.md` and run
init/refresh.

During development, append architecture decisions, structural pitfalls, and
candidate cross-project insights to `.agent/wiki-queue.md` when they are worth
preserving.

Legacy note: `.claude/wiki-queue.md`, `.claude/dev-log.md`, and
`.claude/bridge-brief.md` may exist from older Claude Code workflows. Read them
only as migration sources; new Wiki Bridge writes go to `.agent/`.

## Commands

```bash
bash scripts/run_local_api.sh
bash scripts/run_mobile.sh
bash scripts/run_desktop_dev.sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
cd apps/mobile && npm run typecheck
```

Meta Graph:

```bash
PYTHONPATH=.:src .venv/bin/python -m tools.v2_validate_graph --strict
PYTHONPATH=.:src .venv/bin/python tools/v2_generate_edge_index.py
PYTHONPATH=.:src .venv/bin/python tools/v2_generate_speed_index.py
```

After adding or changing graph cards: edit YAML, update registry, run strict
validation, rebuild both indexes.

Ablation:

```bash
.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --repeats 3
.venv/bin/python tools/p10h_prebattle_ablation_harness.py run --output-dir artifacts/p10h_prebattle_ablation --repeats 3 --max-calls N
```

## Completion Standard

Completion means:

- behavior changed as requested
- relevant tests or smoke checks ran
- remaining risk is named
- the user can verify the result without reading code
