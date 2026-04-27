# LLM Runtime Security Contract

## Purpose

Define the release-grade contract for connecting the V1 single-chat Agent to a
user-provided OpenAI-compatible LLM API.

This contract exists because provider keys, model routing, and Agent tool loops
are security-sensitive. The implementation must not treat this as a prompt-only
feature.

## Release Position

V1 is an open-source, user-owned runtime:

- Users provide their own model API key.
- The app does not ship provider credentials.
- Backend tools remain the only source for approved A/B data.
- LLM reasoning may synthesize and explain, but it may not invent confirmed
  facts.

Release-grade means:

- no plaintext persistent API key storage
- no accidental key echo in responses, metadata, logs, traces, or errors
- no silent fake-LLM fallback that looks like successful native reasoning
- no mobile construction of internal persona selectors
- no web/live-meta expansion

## Threat Model

Protect against:

- accidental key commit to the repo
- key exposure through app logs, backend logs, crash output, screenshots, issue
  templates, debug metadata, or response payloads
- key transmission over insecure production network paths
- backend persistence of user keys
- prompt/model output inventing facts not backed by approved tools
- user confusion when LLM runtime is unavailable and deterministic fallback is
  degraded

Out of scope for this contract:

- enterprise MDM key provisioning
- server-side multi-tenant key vault
- account system
- billing/subscription
- provider-specific adapters beyond OpenAI-compatible chat endpoints

## Supported Provider Scope

V1 supports only OpenAI-compatible endpoints.

Minimum fields:

- `provider_base_url`
- `model`
- provider API key

No provider marketplace, no OAuth, no provider-specific tuning surface, and no
multi-provider routing policy are approved in V1.

## Mobile Secret Storage Contract

Mobile must store provider API keys only in platform secure storage:

- iOS: Keychain-backed storage
- Android: Keystore-backed storage
- Expo implementation may use `expo-secure-store` if it maps to the above
  platform stores

Forbidden:

- AsyncStorage for API keys
- plain JSON config files for API keys
- checked-in `.env` or sample files containing live keys
- logging or rendering the full key outside a masked input field

Required controls:

- masked key input by default
- reveal/hide toggle
- clear/delete key
- explicit warning that keys are user-owned local secrets
- explicit warning not to paste keys into screenshots, logs, GitHub issues, or
  support bundles

If secure storage is unavailable, release builds must degrade to "key not
configured" and must not silently fall back to plaintext persistence.

## Transport Contract

Provider keys must not be sent in URL query parameters or request bodies.

Approved request headers from mobile to Product API:

- `X-Roco-Provider-Key`: provider API key
- `X-Roco-Provider-Base-Url`: OpenAI-compatible base URL
- `X-Roco-Model`: model name
- `X-Roco-Runtime-Mode`: `native`

Transport rules:

- Release builds must send provider keys only over HTTPS.
- Loopback HTTP (`localhost`, `127.0.0.1`) is allowed only for local development
  on the same host.
- LAN HTTP with provider key is not release-safe. If supported for development,
  it must require an explicit unsafe-dev override and clear warning.
- The backend must never echo provider headers in response bodies, metadata,
  logs, tool payloads, or exception text.

## Backend Runtime Config Contract

Runtime provider config is request-scoped.

The Product API may accept provider config on `/chat` through the approved
headers above. The backend must:

- build a native runtime model only for the current request
- not write provider key/base URL/model to disk
- not store provider key in session state
- not include provider config in `AgentResponse`, `presentation`, `persona`,
  `tool_results`, `evidence`, `/metadata`, or error payloads
- redact provider headers from all logging paths
- preserve deterministic fallback as explicitly degraded when used

Server-local env config remains valid for local CLI/backend development:

- `ROCO_ADVISOR_MODEL`
- `ROCO_OPENAI_BASE_URL`
- `ROCO_OPENAI_API_KEY`

But mobile user-provided release config must be request-scoped unless a later
reviewed key-vault design exists.

## API Error And Fallback Contract

Missing key/model/base URL:

- return a safe setup-required error or degraded response that clearly says LLM
  runtime is not configured
- do not pretend native reasoning succeeded

Provider failure:

- return safe user-readable error or degraded fallback
- do not include provider key, raw provider response, base URL credentials, local
  paths, or stack traces

Timeout:

- enforce bounded native timeout
- return timeout-specific safe error/degraded response
- do not keep retrying indefinitely

Deterministic fallback:

- allowed only when clearly marked `degraded` / `auto_fallback_deterministic`
- must not be presented as LLM reasoning
- must preserve evidence/confidence boundaries

Explicit native mode:

- if native fails, return bounded native failure
- do not silently fall back unless the request explicitly uses `auto`

## Agent Tool Loop Contract

The LLM may reason only through approved tools and evidence:

- `analyze_team_structure`
- `get_species_profile`
- `get_species_available_moves`
- `retrieve_doc_context`
- `analyze_species_semantics`

Approved data roles:

- A substrate: deterministic engine / SQL-backed facts / tool outputs
- B substrate: reviewed docs, mechanics, methodology, taxonomy, and doctrine
  constraints
- query: user prompt

Hard rules:

- confirmed claims must be grounded in deterministic engine or SQL facts
- reviewed docs may guide interpretation but cannot override Engine/SQL facts
- species/team semantic judgements remain provisional unless a deterministic
  scorer exists
- no web search
- no live meta
- no future patch/balance prediction
- no unsupported official IP claims
- no hidden tool not listed in this contract

## Persona And Presentation Boundary

Persona remains downstream of the analytical contract:

- persona may affect rendering, tone, and `response.persona`
- persona may not mutate factual claims, confidence, tool results, refusal
  status, or evidence
- mobile must still send public `persona_selector` only
- mobile must not construct internal encoded selectors

## Logging And Redaction Requirements

The following must be redacted from logs and error text:

- `X-Roco-Provider-Key`
- `ROCO_OPENAI_API_KEY`
- provider API key values
- Authorization headers
- local materialization paths
- raw provider exception bodies if they may contain request headers

The following must not expose secrets:

- `/metadata`
- `/health`
- `/chat` response
- exception handler response
- `tool_results`
- `evidence`
- mobile error UI
- mobile settings test-connection output

## Implementation Milestones

### P4b Backend Request-Scoped Native Runtime

Implement backend request-header parsing, redaction, request-scoped native model
construction, safe failure behavior, and backend tests.

### P4c Mobile Secure Settings Storage

Implement secure key storage, settings validation, HTTPS/unsafe-dev gating, and
request header injection.

### P4d E2E Agent Tool Loop QA

Verify with TestModel/mock provider that:

- query routes to approved tools
- answer uses grounded evidence
- persona presentation preserves facts
- secrets are not leaked
- failure/timeout behavior is bounded

## Acceptance Criteria

Backend:

- `/chat` accepts request-scoped native runtime headers.
- Backend does not persist provider key.
- Backend redacts provider key in logs/errors.
- Missing config returns safe setup-required/degraded behavior.
- Provider failure and timeout are bounded and safe.
- TestModel/mock native run proves approved tool calls.

Mobile:

- API key is stored only in platform secure storage.
- API key is masked, revealable, and clearable.
- Requests send key only via `X-Roco-Provider-Key`.
- Release build blocks key transmission over non-HTTPS except loopback dev.
- Settings UI explains local user-owned secret risk.

Agent:

- Tool loop uses only approved A/B substrates.
- No confirmed claim appears without tool/evidence support.
- Unsupported live/future/meta requests refuse safely.
- Deterministic fallback is clearly degraded.

Security:

- No API key appears in response payloads, metadata, logs, tool payloads, or
  error text.
- No real key is committed to repo artifacts.
- Static grep tests cover common secret names and header names.

## Non-Goals

- final visual redesign
- account system
- hosted multi-tenant key vault
- payment
- model marketplace
- prompt marketplace
- persona creation workflow
- Nexus adapter
- web search / live meta
