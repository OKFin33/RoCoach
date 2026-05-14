# Roco Advisor Mobile

V1 local-development Expo implementation for the Roco Advisor single Agent chat
shell. The current shell follows the accepted prototype language: bright yellow
outer shell, raster cream paper chat surface, thick black hand-drawn outlines,
sticker-like avatars, restrained bubbles, and generic long-response analysis
cards from the RN handoff package.

## Local Run

1. Start the FastAPI backend from the repository root:

   ```bash
   bash scripts/run_local_api.sh
   ```

2. Start the Expo app:

   ```bash
   bash scripts/run_mobile.sh
   ```

   Run the command from the repository root.

3. Swipe left from the right screen edge to open the settings drawer, then set
   the Product API base URL for the device:

   - iOS simulator: `http://127.0.0.1:8000`
   - Android emulator: `http://10.0.2.2:8000`
   - Physical device: use the LAN IP of the backend machine.

## V1 Product Shell

For implementation ownership and file-level responsibilities, read
[`ROCO_RN_UI_FILE_GUIDE.md`](./ROCO_RN_UI_FILE_GUIDE.md) before changing the RN
UI.

The primary UI is one Agent chat surface. Team Analyze, Species Search/Profile,
calculator, dex, evidence/debug panels, and similar modules are hidden from V1
primary navigation and remain Agent-internal capabilities. Backend APIs and
client methods can still exist for the Agent/runtime path; they are not product
tabs.

The authorized `队伍设置` entry in Settings is a different concept: it is a
future roster/context configuration surface, not a Team Analyze or Dex product
entrance. Its purpose is to avoid forcing users to retype a team before every
analysis. It may later use the local species database for graphical search,
selection, team building, move configuration, and individual tuning, while Agent
analysis remains in the single Chat flow.

Chat remains the only visible product entrance. Message actions are local shell
scaffolding and must not copy message content into the prompt composer. Long
Agent responses are rendered from `presentation.reply`, `presentation.why`, and
`presentation.detail_sections`; the mobile UI does not render production
content directly from raw `tool_results.payload`.

The paper surface uses the raster asset
`mobile/assets/paper/paper_shell.png` through React Native `ImageBackground`
with `resizeMode="stretch"`.

## Persona Selector

Long-press the Agent avatar in Chat to open the avatar-anchored radial persona
wheel.

- V1 defaults to `You know who` visually and sends:
  `{ "kind": "managed", "persona_id": "you_know_who", "version": "draft.v1", "revision": 1 }`
- `默认AI助手` sends:
  `{ "kind": "built_in", "persona_id": "lattice_support_coach" }`
- `添加人格` is a reserved seam and does not send a selector.

`You know who` is the public-safe outward codename for the Enzo-derived
distilled persona layer. It comes from the internal Enzo doctrine sample after
abstraction and IP sanitization. The public UI must not claim this is Enzo,
恩佐, an official character, official lore, official dialogue, or official art.
The managed runtime selector for this distilled persona is
`you_know_who@draft.v1#1`. The built-in `you_know_who` and legacy
`obsidian_tactical_coach` paths remain backend compatibility fallbacks when the
local materialized profile path is unavailable.

The mobile client must not construct internal encoded selector strings. Effective
persona and fallback state are displayed from `response.persona`; local
materialization paths, artifacts, and selector internals are not surfaced.

## Settings Drawer And Secrets

Swipe left from the right screen edge or pull the connected rail handle to open
设置. The drawer opens to a small settings home with authorized reserved entries
for `队伍设置`, `API 设置`, and `人格设置`. This does not turn V1 into a
multi-tool app: `队伍设置` is only a future preference/configuration placeholder,
not Team Analyze, Team Editor, Species, Calculator, or Dex navigation.

`API 设置` contains Product API base URL, Provider API key, Provider base URL,
model, model configuration profile, thinking toggle, reasoning effort,
clear/save, reload, Product API test, and Model service test controls. The
connected rail is the only settings entrance in the V1 shell.

V1 exposes only two model configuration options:

- `custom_single_model`: the mainstream open-source mode. Every LLM call uses
  the user's configured provider base URL, API key, model id, and supported
  reasoning settings.
- `deepseek_v4_quick_setup`: a convenience option that fills the DeepSeek base
  URL and a release-safe default model. It is not the full
  `roco_deepseek_v4_reference` call-role router, not a multi-tier preset
  matrix, and does not expose ordinary-user per-role routing controls.

API key fields are user-owned local secret UI only. Provider keys are persisted
with Expo SecureStore, backed by platform secure storage where available. The
key is stored separately from non-secret runtime settings and is never sent in
the request body or URL.

When Provider API key, Provider base URL, and model are complete, settings save
enables the configured model service internally and request headers are injected:

- `X-Roco-Provider-Key`
- `X-Roco-Provider-Base-Url`
- `X-Roco-Model`
- `X-Roco-Runtime-Mode: native`
- `X-Roco-Reasoning-Mode`
- `X-Roco-Reasoning-Effort` when thinking is enabled

The internal `runtimeMode` and `transportMode` fields are not visible V1 user
settings.

Product API health checks do not send provider-key headers. Model service tests
send provider-key headers only after explicit user action and may consume a
small amount of provider tokens.

Provider keys are blocked over non-HTTPS Product API URLs except loopback local
development (`localhost`, `127.0.0.1`, `::1`). LAN HTTP provider-key transport
is not a normal V1 user setting.

## Boundary

The app only calls the Product API. It does not read SQLite, shell out to the
CLI, call model providers directly, persist provider keys outside platform
secure storage, or bundle official IP assets.

Release notes:

- local-only scaffold; no hosted deployment stack is included
- rate-limit handling in the backend is still a placeholder, not production abuse control
- the product is unofficial and not officially authorized, sponsored, or affiliated
  with Tencent, 洛克王国 / Roco Kingdom, or any official character or art asset owner
