# P9d Foundational Infrastructure Audit

Date: 2026-04-29
Status: active audit
Severity: high

## Why This Audit Exists

During P9d planning, we discovered a serious architecture gap: Roco had business
session continuity, but not LLM provider protocol continuity.

This matters because modern Agent chat with thinking + tool calls requires more
than remembering the selected team or species. The runtime must also preserve
model/tool message history when the provider protocol requires it.

This was a severe miss in prior planning. Earlier P7-P9 work treated "multi-turn
chat" too loosely and did not distinguish:

- product/business state continuity, and
- provider/model protocol continuity.

## Immediate Fix Applied

Implemented in code:

- `AdvisorSessionState.native_model_messages`
- `AdvisorSessionState.native_runtime_fingerprint`
- bounded native protocol history retention
- request-scoped native session TTL/eviction
- native runtime now passes `message_history` into PydanticAI when prior native
  messages exist for the same provider/model/thinking configuration
- native runtime now stores `result.all_messages()` after successful native runs
- request-scoped API-key runtime now reuses an in-memory session state store by
  `session_id` without persisting the API key or native orchestrator

Files:

- `advisor/contracts.py`
- `advisor/runtime.py`
- `api/services/advisor_service.py`
- `tests/test_advisor.py`
- `tests/test_api.py`

Validation:

```text
.venv/bin/python -m unittest tests.test_advisor tests.test_api
Ran 75 tests in 1.801s
OK
```

## Current Capability After Fix

Roco can now preserve PydanticAI model messages across turns in the native
runtime path, which is the minimum layer needed for DeepSeek thinking+tool
conversation stitching.

Important boundary:

- This is protocol-layer support, not proof that DeepSeek thinking+tool
  long-dialog behavior is fully accepted.
- P9d S10 still must live-test provider behavior and redaction.

## Similar Infrastructure Gaps Found

### 1. Loop Runtime Is Still A Contract, Not Production Infrastructure

Status: not implemented.

Risk:

- P9c/P9d can design loop policy, but the production runtime still has no
  accepted controlled-loop executor with max rounds, tool-call caps, timeout,
  repeated-tool detection, and trace redaction.

Required before enabling loop:

- controlled loop executor
- per-round budget tracking
- repeated identical tool-call guard
- protocol history preservation under thinking mode
- redacted internal trace artifact

### 2. Conversation History Has No Compaction Or TTL Policy

Status: partially mitigated.

Mitigated:

- Native message history now has a message-count cap.
- Request-scoped native session state now has TTL/eviction.

Residual risk:

- Message-count truncation is not semantic compaction and may still cut useful
  context in long sessions.
- Hidden reasoning content and tool observations can still be large within the
  retained window.

Required before long public use:

- token/turn compaction policy
- `/clear` and session reset live-provider coverage for protocol history
- redaction tests for internal logs/artifacts

### 3. Request-Scoped Key Security Needs Explicit Memory Policy

Status: improved but not complete.

Current behavior:

- API key is still not persisted in service sessions.
- Request-scoped native state stores protocol messages, not API keys.

Residual risk:

- Protocol history can contain tool evidence and hidden reasoning.
- Memory lifetime is process lifetime unless TTL/eviction is added.

Required:

- session eviction
- explicit memory-only disclosure in metadata/docs
- no crash dumps containing hidden reasoning/tool payloads

### 4. Rate Limiting Is Still Placeholder

Status: known placeholder.

Evidence:

- `api/dependencies.py::rate_limit_placeholder`
- metadata reports `placeholder_none_not_production_abuse_control`

Risk:

- Open-source/local use is acceptable, but public deployment would be abusable.

Required before public hosted release:

- request rate limit
- model-service diagnostic rate limit
- provider-key abuse guard
- payload size cap

### 5. Provider Capability Registry Is Still Implicit

Status: partial.

Risk:

- Current behavior infers DeepSeek by marker strings and applies settings.
- There is no durable provider capability matrix for thinking/tool/history
  support.

Required:

- provider capability registry
- explicit support flags:
  - thinking disabled/enabled
  - reasoning_effort values
  - tool calls
  - thinking+tool replay requirements
  - streaming support

### 6. Tool Loop And Presentation Redaction Must Stay Separated

Status: partially implemented.

Current positive:

- Mobile filters public analysis sections and suppresses raw/tool_trace kinds.

Risk:

- Future loop traces could accidentally enter public artifacts if S9/S10 harness
  writes raw traces into blind packets or API responses.

Required:

- shared redaction utility for eval artifacts
- tests that hidden reasoning/raw tool payloads never appear in mobile-visible
  fields

### 7. Intent/Call Policy Is Ahead Of Runtime Enum Granularity

Status: contract ahead of runtime.

Risk:

- P9c defines many intents, but runtime still has coarse routes like
  `GENERAL_CHAT`, `SPECIES_QUERY`, `ANALYZE_TEAM`.
- If implementation jumps directly to model routing without an intent adapter,
  wrong model/call policy may be applied.

Required:

- thin call-policy adapter
- route-to-call-scene mapping tests
- unknown-intent clarify/unsupported tests

## Release Gate Recommendation

Before recommending any `pro_max` or controlled-loop strategy:

1. Run P9d provider capability probe.
2. Run S10 multi-turn thinking/tool context continuity.
3. Add TTL/compaction limits for native message history.
4. Add redaction tests for hidden reasoning and raw tool traces.
5. Keep loop disabled until S9/S10 both pass.

Operational conclusion:

```text
P9d must treat protocol continuity, trace redaction, and budget controls as
infrastructure gates, not optional QA polish.
```
