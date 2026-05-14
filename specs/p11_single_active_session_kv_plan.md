# P11 Single Active Session KV Plan

Status: planned  
Date: 2026-05-06  
Owner: backend + desktop integration  
Primary goal: make RoCoach V1 usable as a single local desktop chat session without losing conversation continuity on backend restart.

## Zero-Context Summary

RoCoach V1 is a local desktop app with a Python FastAPI backend. The product surface is one chat box plus settings/team/persona controls. There is no multi-session UI in V1.

The current backend supports `session_id`, but session state is in memory only. Restarting the backend loses:

- current `AdvisorSessionState`
- native provider message history
- request-scoped runtime state stores

This is now a V1 blocker because the app can look persistent while the Agent context is not durable. P11 fixes this by adding a single active persistent session, not a history product.

## Current State

Important current files:

- `api/release.py`: currently declares `SESSION_CONTINUITY_MODE = "optional_session_id_in_memory_only"`.
- `api/main.py`: `/chat` accepts and returns `session_id`.
- `api/services/advisor_service.py`: stores sessions in process memory.
- `advisor/runtime.py`: `InMemorySessionStateStore` owns `AdvisorSessionState`.
- `advisor/contracts.py`: `AdvisorSessionState.native_model_messages` exists and is excluded from normal Pydantic serialization.
- `desktop/src/renderer/App.tsx`: desktop UI keeps `sessionId` in React state only; team/persona/settings have separate local persistence.

Known serialization fact:

- `pydantic_ai.messages.ModelMessagesTypeAdapter` is available in the current environment and should be used to serialize/deserialize native model messages.
- Do not pickle provider messages.

## Product Decision

V1 uses one active session only.

Server authority:

- SQLite owns exactly one active session pointer.
- Desktop may send a `session_id`, but the backend remains authoritative.
- If the client sends an unknown or stale `session_id`, the backend must not
  create a second active runtime session.
- Unless the user explicitly clears the current chat, the backend returns the
  authoritative active `session_id` and a controlled session event with
  diagnostic reason `client_session_mismatch`.

Allowed:

- restore the current active session after backend restart
- clear current chat
- archive old sessions to local JSONL for future import/debug
- auto-rollover when context pressure is reached

Forbidden in V1:

- multi-session list UI
- conversation search UI
- long-term user profile memory
- persona-growth memory
- storing API keys in backend session DB or archive
- using JSONL as runtime source of truth

## Session Policy

```yaml
mode: single_active_session
runtime_source_of_truth: sqlite_kv
archive_format: append_only_jsonl
rollover_triggers:
  context_pressure:
    estimated_context_ratio: 0.75
    max_native_model_messages: 64
    max_serialized_history_bytes: 512000
rollover_action:
  archive_old_session: true
  start_new_session: true
  carry_forward:
    team_context: true
    persona: true
    api_settings_frontend_only: true
    native_model_history: false
    visible_messages: false
```

Context pressure detection is approximate in V1:

- prefer provider usage metadata when available
- otherwise estimate with serialized history bytes, native message count, and conservative token approximation
- unknown model context budget must fail conservative, not optimistic

Context pressure estimator contract:

- Inputs:
  - native message count
  - serialized native history byte size
  - optional provider usage metadata when available from the native run result
  - configured model context budget from model table or env override
- Conservative fallback:
  - if provider usage metadata is unavailable, estimate tokens from serialized
    history bytes with a documented bytes-to-token divisor
  - if model budget is unknown, use the smallest configured safe default rather
    than assuming a large context window
- Rollover must happen before the next provider call when any configured limit
  is exceeded.
- Tests must cover all estimator inputs without requiring a live provider call.

## Storage Design

### Active Session SQLite KV

Use SQLite for active runtime state. The DB must be local-only and gitignored.

Recommended resolution order:

1. `ROCO_SESSION_DB_PATH` when explicitly set
2. app data directory for packaged desktop later
3. local dev fallback under a gitignored runtime path

Path resolver contract:

- Env override:
  - `ROCO_SESSION_DB_PATH` wins when explicitly set
  - parent directory must be created if allowed by OS permissions
- Packaged desktop:
  - use the desktop app data directory provided by the shell/runtime adapter
  - do not derive packaged paths from the repo checkout
- Local dev fallback:
  - use a gitignored runtime path under the project, for example
    `.runtime/roco_session/session.sqlite3`
  - release metadata must not claim packaged continuity when running in this
    fallback mode
- Corruption handling:
  - a corrupt DB must be moved to a timestamped backup path before creating a
    fresh active DB
  - provider secrets must not be copied into the backup because they must never
    be in the DB

The active store should contain:

- `session_id`
- `schema_version`
- `created_at`
- `updated_at`
- `runtime_fingerprint`
- serialized `AdvisorSessionState` excluding provider secrets
- serialized `native_model_messages`
- last rollover metadata

The store must not contain:

- provider API key
- raw request headers
- raw tool trace intended only for internal debugging
- unreduced provider secrets

### Archive JSONL

Archive old sessions as append-only JSONL.

Purpose:

- future import/read feature
- developer audit
- rollback-safe local record

Not purpose:

- runtime state source
- retrieval memory
- user profile memory

Each JSONL row should include:

- `archive_schema_version`
- `archived_at`
- `session_id`
- `reason`
- `created_at`
- `updated_at`
- optional non-secret summary
- diagnostic metadata for why the session was archived
- no API key, no hidden reasoning, no raw provider secret material

V1 archive source rule:

- Backend archive stores non-secret summary and diagnostic metadata by default.
- Desktop visible messages remain frontend-owned display state.
- Full visible-message import/read is a future product and must not be implied
  by the P11 archive.

## Backend Contract

### New Store Layer

Add a persistent store layer rather than expanding `AdvisorService` into storage code.

Suggested modules:

- `advisor/session_store.py`
  - `SessionKVStore`
  - `PersistentSessionStateStore`
  - `SessionArchiveWriter`
  - message serialization helpers
- or `api/services/session_store.py` if implementation needs API-specific path resolution

The state-store interface should remain close to `InMemorySessionStateStore` so `AdvisorAgent` does not become a persistence object.

### Serialization Rules

Advisor state:

- use Pydantic JSON for regular `AdvisorSessionState` fields
- handle excluded `native_model_messages` explicitly

Native messages:

- serialize with `ModelMessagesTypeAdapter`
- persist a `messages_schema_version`
- if deserialization fails, discard native history but keep safe structured state such as current team

Runtime fingerprint:

- include enough data to detect incompatible message history:
  - runtime mode
  - provider family/model id when available
  - pydantic-ai message schema marker
  - RoCoach session schema version

On mismatch:

- drop native model history
- preserve team context/persona selection where safe
- return a controlled session event

### API Response Extension

Extend `/chat` response with optional session event metadata.

```json
{
  "session_id": "active-session-id",
  "response": {},
  "session_event": {
    "type": "continued | reset | rolled_over | cleared | degraded",
    "reason": "none | client_session_mismatch | missing_active_state | corrupted_native_history | runtime_fingerprint_mismatch | age | context_pressure | user_clear | archive_write_failed",
    "message": "已开启新的对话上下文，队伍设置已保留。",
    "user_action": "none | resend_key_context | continue | retry_clear",
    "diagnostic": {
      "agent_context": "continued | reset | native_history_dropped",
      "visible_messages": "unchanged | mark_stale | clear",
      "archive": "not_applicable | pending | written | failed | skipped",
      "support_code": "session.continued"
    }
  }
}
```

User-facing copy rule:

- Normal users see `message` and maybe `user_action`.
- Exact diagnostic fields are for logs, QA, support/debug surfaces, and tests.
- Do not expose backend protocol labels as primary UI copy.

Add an explicit clear endpoint:

```http
POST /session/clear
```

Behavior:

- archives the current active session
- clears active runtime state
- starts a new session id or returns a clear event for the next `/chat`
- does not clear desktop API key/settings/team/persona local storage
- shares the same backend clear service used by chat `/clear`

Clear path rule:

- `POST /session/clear` and chat `/clear` must call the same archive + reset
  service.
- Desktop should prefer `POST /session/clear`.
- `/clear` may remain for CLI/chat compatibility, but it must not bypass archive
  or single-active-session authority.

## Desktop Contract

Desktop should persist only UI-owned state locally:

- active `sessionId`
- visible chat messages
- team context
- selected persona
- provider settings and encrypted/local API key handling

Desktop must not assume that visible messages equal backend native history.

On startup:

- restore `sessionId`
- restore visible messages
- backend loads matching active state if present
- if backend returns mismatch/rollover event later, desktop follows the event

On rollover event:

- clear visible chat messages
- keep team/persona/settings
- show a low-noise notice: `已开启新的对话上下文，队伍设置已保留。`

On native history drop or active-context reset:

- keep the prior visible transcript locally, but mark it as past transcript
  rather than active Agent context
- show a low-noise notice: `已开启新的对话上下文，之前的聊天仅作为记录保留。`
- keep team/persona/settings unless the event explicitly says otherwise

Settings:

- add only `清空当前对话`
- do not add session history UI

## Implementation Slices

### P11a Contract + Store Skeleton

Deliver:

- persistent store module
- path resolution
- schema constants
- serialization helpers
- unit tests for round-trip and secret exclusion

Acceptance:

- `AdvisorSessionState` round-trips through SQLite
- `native_model_messages` round-trips through `ModelMessagesTypeAdapter`
- corrupted native history fails closed and does not crash startup
- API keys are not persisted

### P11b AdvisorService Integration

Deliver:

- replace request runtime in-memory store with persistent store for active session
- preserve current in-memory orchestrator behavior only where safe
- rollover policy hook before request execution
- runtime fingerprint mismatch handling

Acceptance:

- same `session_id` survives backend restart
- team context survives backend restart
- native message history survives compatible backend restart
- incompatible runtime drops native history and emits event

### P11c API + Desktop Integration

Deliver:

- `/chat` response `session_event`
- `POST /session/clear`
- desktop persists active `sessionId` and visible messages
- desktop handles rollover/clear events

Acceptance:

- desktop restart preserves current visible chat and session id
- backend restart preserves Agent continuity
- clear current chat archives and resets only current session
- no multi-session UI appears

### P11d QA + Release Flag

Deliver:

- backend unit/integration tests
- desktop typecheck/build
- release flag update
- project log entry

Acceptance:

- `.venv/bin/python -m unittest discover -s tests`
- `cd desktop && npm run typecheck && npm run build`
- `api/release.py` updates continuity mode to `single_active_session_sqlite_kv_with_local_archive`
- log documents that V1 still has no multi-session history UI

## Required Tests

Backend:

- active session state persists through service restart
- native model messages serialize and deserialize
- deserialization failure drops native history safely
- runtime fingerprint mismatch drops native history safely
- context-pressure rollover archives old state and starts new state
- clear endpoint archives and clears active state
- no API key appears in SQLite or JSONL archive
- `/chat` still works without prior session id
- `/chat` still returns a session id

Desktop:

- active session id persists across app reload
- visible messages persist across app reload
- rollover event clears visible messages and keeps team/persona/settings
- clear action calls backend and clears visible messages
- no history list is rendered

Security:

- provider key redaction test covers SQLite and JSONL bytes
- hidden reasoning and raw tool traces are not persisted into public archive fields

## Migration / Compatibility

Initial migration is simple:

- if no active session DB exists, create one lazily on first chat
- existing desktop users with only local `sessionId` get a fresh backend state
- do not attempt to reconstruct native history from visible messages

If old in-memory mode is still active:

- return current behavior
- release metadata must honestly expose `optional_session_id_in_memory_only`

## Failure Modes

If SQLite is unavailable:

- fail closed to controlled API error in release mode
- allow in-memory fallback only in dev mode when
  `ROCO_SESSION_ALLOW_IN_MEMORY_FALLBACK=1`
- fallback must emit a controlled warning/session event and must not update
  release metadata to the SQLite continuity mode

If archive write fails:

- do not delete active session state
- return controlled warning
- transition must remain before destructive state replacement
- legal order is `archive_pending -> archive_written -> active_replaced`
- if archive write fails, keep the old active session and report
  `archive_write_failed`

If native history is too large:

- rollover before the next provider call
- reserve the next call for a normal user-facing response, not tool churn

If provider protocol changes:

- discard native history
- preserve structured team/persona state
- notify desktop through `session_event`

## Non-Goals

- hosted sync
- account system
- cloud storage
- vector memory
- semantic recall over old sessions
- multi-session management UI
- persona memory growth
- automatic long-term coaching profile

## Definition of Done

P11 is complete when RoCoach V1 can be used as a single local desktop Agent chat where:

- a backend restart does not silently destroy active session continuity
- old context is safely rolled over at context pressure
- old records are archived locally for future versions
- no provider secret is persisted server-side
- the UI remains one active chat, not a session manager
