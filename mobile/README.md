# Roco Advisor Mobile

V1 local-development Expo scaffold for the Roco Advisor single Agent chat shell.
The current shell follows the accepted prototype language: bright yellow outer
shell, SVG cream paper chat surface, thick black hand-drawn outlines,
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

3. Swipe left from the right screen edge to open the in-memory settings drawer,
   then set the API base URL for the device:

   - iOS simulator: `http://127.0.0.1:8000`
   - Android emulator: `http://10.0.2.2:8000`
   - Physical device: use the LAN IP of the backend machine.

## V1 Product Shell

The primary UI is one Agent chat surface. Team Analyze, Species Search/Profile,
calculator, dex, evidence/debug panels, and similar modules are hidden from V1
primary navigation and remain Agent-internal capabilities. Backend APIs and
client methods can still exist for the Agent/runtime path; they are not product
tabs.

Chat remains the only visible product entrance. Message actions are local shell
scaffolding and must not copy message content into the prompt composer. Long
Agent responses are rendered from `presentation.reply`, `presentation.why`, and
`presentation.detail_sections`; the mobile UI does not render production
content directly from raw `tool_results.payload`. The paper surface ports
`ui_handoff/roco_v1_rn/assets/paper/paper_frame.svg` through
`react-native-svg` with `preserveAspectRatio="none"`.

## Managed Persona Selector Scaffold

Long-press the Agent avatar in Chat to open the avatar-anchored radial persona
wheel scaffold. It is not final UI design.

- no selection sends no persona selector and preserves backend default behavior.
- `You know who` maps to built-in `obsidian_tactical_coach`.
- `默认AI助手` maps to built-in `lattice_support_coach`.
- `Add` is a disabled/seam placeholder for a later persona creation page.

The mobile client must not construct internal encoded selector strings. Effective
persona and fallback state are displayed from `response.persona`; local
materialization paths, artifacts, and selector internals are not surfaced.

## Settings Drawer And Secrets

Swipe left from the right screen edge or pull the connected rail handle to open
设置. The drawer includes API base URL, provider API key, model,
endpoint/provider preference, and runtime mode controls. The connected rail is
the only settings entrance in the V1 shell.

API key fields are user-owned local secret UI only. Provider keys are persisted
with Expo SecureStore, backed by platform secure storage where available. The
key is stored separately from non-secret runtime settings and is never sent in
the request body or URL.

Native runtime headers are injected only when `Native` mode is enabled and API
key, provider base URL, and model are complete:

- `X-Roco-Provider-Key`
- `X-Roco-Provider-Base-Url`
- `X-Roco-Model`
- `X-Roco-Runtime-Mode: native`

Provider keys are blocked over non-HTTPS Product API URLs except loopback local
development (`localhost`, `127.0.0.1`, `::1`). LAN HTTP requires the explicit
unsafe-dev override in the drawer and should not be used for release.

## Boundary

The app only calls the Product API. It does not read SQLite, shell out to the
CLI, call model providers directly, persist provider keys outside platform
secure storage, or bundle official IP assets.

Release notes:

- local-only scaffold; no hosted deployment stack is included
- rate-limit handling in the backend is still a placeholder, not production abuse control
- the product is unofficial and not officially authorized, sponsored, or affiliated
  with Tencent, 洛克王国 / Roco Kingdom, or any official character or art asset owner
