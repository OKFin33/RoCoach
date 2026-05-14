# P9 DeepSeek Provider QA Plan

Date: 2026-04-28

Contract: `specs/p9_deepseek_runtime_config_contract.yaml`

## Purpose

P9 determines a release-sane runtime configuration strategy for open-source
Roco users while validating the DeepSeek V4 provider path end to end.

The goal is not to hard-code DeepSeek as the only provider. The goal is to:

- keep OpenAI-compatible custom configuration available
- offer a DeepSeek preset that reduces user misconfiguration
- validate `deepseek-v4-flash` and `deepseek-v4-pro`
- validate thinking off/on behavior
- define when Roco should recommend fast, balanced, or deep modes
- add provider diagnostics so users do not confuse Product API health with model
  service health

## Official DeepSeek Constraints Used

Sources:

- DeepSeek first API call docs:
  `https://api-docs.deepseek.com/`
- DeepSeek models and pricing:
  `https://api-docs.deepseek.com/quick_start/pricing`
- DeepSeek thinking mode:
  `https://api-docs.deepseek.com/zh-cn/guides/thinking_mode`
- DeepSeek tool calls:
  `https://api-docs.deepseek.com/zh-cn/guides/tool_calls`

Relevant constraints:

- OpenAI-compatible base URL is `https://api.deepseek.com`.
- Current V4 model ids are `deepseek-v4-flash` and `deepseek-v4-pro`.
- Both V4 models support thinking and non-thinking modes.
- Both V4 models support JSON output and tool calls.
- Thinking mode defaults to enabled in DeepSeek docs.
- To disable thinking, callers must explicitly pass
  `thinking: { type: "disabled" }`.
- OpenAI SDK usage sends thinking through `extra_body`.
- Thinking mode does not effectively use temperature/top_p/presence/frequency
  controls.
- Thinking plus tool calls requires preserving and replaying `reasoning_content`
  in subsequent tool-loop requests; failure can produce provider 400 errors.
- Strict tool-call mode is beta and requires `https://api.deepseek.com/beta`
  plus stricter JSON Schema. It is not the default P9 path.

## Current Roco Baseline

Current mobile settings allow:

- Product API base URL
- Provider API key
- Provider base URL
- Model

Current mobile UI issue:

- `测试 API` only checks Roco Product API health/metadata.
- It does not validate the configured model provider.
- Therefore the simulator can show `Health: ok` while real Agent Chat fails
  with `provider/model failure: ModelHTTPError`.

Current backend runtime:

- Request-scoped native runtime is passed through headers.
- DeepSeek configs use PydanticAI `PromptedOutput(AdvisorResponse)` instead of
  tool-structured output because prior `deepseek-v4-pro` QA found the default
  structured-output path incompatible.
- No explicit thinking-mode header/config exists yet.
- Current runtime does not expose provider-specific errors with enough
  diagnostic granularity for users.

## QA Matrix

The core matrix is four DeepSeek configurations:

| QA id | Model | Thinking | Effort | Intended product mode |
| --- | --- | --- | --- | --- |
| `ds_flash_non_thinking` | `deepseek-v4-flash` | disabled | none | Fast |
| `ds_flash_thinking_high` | `deepseek-v4-flash` | enabled | high | Balanced candidate |
| `ds_pro_non_thinking` | `deepseek-v4-pro` | disabled | none | Balanced/deep candidate |
| `ds_pro_thinking_max` | `deepseek-v4-pro` | enabled | max | Deep |

Do not assume the recommendation before running QA. The matrix determines it.

## Required QA Scenarios

Run every model/thinking combination against every required scenario unless the
scenario is blocked by an earlier provider-level failure.

### S1. Direct Provider Basic Chat

Purpose:

- prove the API key, base URL, model id, and thinking parameters work outside
  Roco Agent abstractions.

Method:

- direct OpenAI-compatible `/chat/completions`
- prompt: `用一句中文回答：Roco 连接测试成功了吗？`
- no Roco tools

Pass:

- HTTP 200
- non-empty final content
- no raw API key/base URL in output
- thinking enabled responses must not expose raw reasoning in user-facing text

Failure classification:

- `provider_auth_error`
- `provider_model_not_found`
- `provider_parameter_error`
- `provider_network_error`
- `provider_timeout`
- `provider_unknown_error`

### S2. Roco General Agent Chat

Purpose:

- prove `/chat` can produce a natural-language Agent response through native
  runtime without deterministic command fallback.

Request:

- Product API `POST /chat`
- message: `我现在该怎么用你来优化队伍？`
- no team context required

Pass:

- HTTP 200
- response backend is `pydantic_ai_native`
- response status is `ok`
- analysis type is `chat_response`
- answer does not contain old command-only MVP fallback copy
- no provider secret/base URL/model/header leak

### S3. Roco Tool-Required Species Grounding

Purpose:

- prove the model can use approved tools and produce grounded species facts.

Request:

- Product API `POST /chat`
- message: `豆丁鱼是什么定位？`

Pass:

- HTTP 200
- response backend is `pydantic_ai_native`
- response status is `ok`
- analysis type is `species_analysis`
- tool results include `get_species_profile`
- answer includes confirmed DB facts such as `豆丁鱼`, `水 / 龙`, or `洄游`
- no local DB path, raw SQL, raw tool payload, provider secret, base URL, or
  runtime header leak

Special watch:

- Thinking+tool configurations must not fail with provider 400 due to missing
  `reasoning_content` replay.

### S4. Roco P8 Team Context Chat

Purpose:

- prove P8 structured team context can be used without visible Chat chip and
  without requiring the user to re-enter team data.

Request:

- Product API `POST /chat`
- message: `这套队伍先手够用吗？`
- include a valid `team_context.v1` attachment with one selected database
  species, one legal move, one nature, and one IV bonus `生命=10` represented
  internally as `hp=10`

Pass:

- HTTP 200
- response backend is `pydantic_ai_native`
- response status is `ok`
- response either analyzes available team structure or asks a precise
  clarifying question based on structured slots
- request body includes `context_attachments`
- response does not expose raw context JSON wholesale
- Chat UI remains free of visible active-team chip

### S5. Negative Diagnostics

Purpose:

- prove user-facing diagnostics are actionable and safe.

Cases:

- invalid key
- invalid model id
- valid Product API but unreachable provider base URL
- unsupported thinking parameter simulation if provider rejects it
- timeout

Pass:

- errors are classified into stable diagnostic codes
- no API key/base URL/model/header-name leak in response text
- Product API health and model-provider health are reported separately

## Optional QA Scenarios

### O1. Strict Tool Calls Beta Probe

Do not make strict mode a V1 default.

Only run this probe if explicitly selected:

- provider base URL: `https://api.deepseek.com/beta`
- tools all have `strict: true`
- JSON Schema avoids unsupported features and follows DeepSeek strict schema
  requirements

Pass:

- strict tool call works for a minimal tool schema

Outcome:

- If pass, record as future hardening option.
- If fail, do not block P9 recommendation.

### O2. Legacy Alias Probe

Test only for migration copy, not as recommendation:

- `deepseek-chat`
- `deepseek-reasoner`

Expected:

- docs say they map to V4 Flash modes and are scheduled for deprecation.

Pass:

- any UI copy must not recommend legacy ids as V1 defaults.

## Timing Measurements

Record elapsed seconds for every scenario.

Suggested soft targets:

- direct basic chat: under 20s
- general chat: under 30s
- species grounding/tool loop: under 90s
- team context chat: under 90s

Do not fail only because a call is slow unless it hits timeout. Slow-but-correct
configs inform the recommendation.

## Recommendation Rules

After QA, pick the V1 recommended DeepSeek preset using these rules:

- Fast mode can only use a config that passes S1 and S2.
- Balanced mode must pass S1, S2, and either S3 or S4 with acceptable latency.
- Deep mode must pass all required scenarios or clearly warn if tool-heavy
  tasks may be slow.
- If thinking+tool calls fail due to `reasoning_content` handling, do not
  recommend thinking mode for Agent/tool routes until runtime support is fixed.
- If flash passes basic chat but fails tool routes, flash can be recommended
  only for simple chat, not for grounded analysis.
- If pro passes tool routes and flash does not, default grounded analysis to pro.

## Required Artifacts

After running QA:

- `artifacts/p9/deepseek_matrix_summary.json`
- `artifacts/p9/deepseek_matrix_summary.md`
- `artifacts/p9/redaction_check.txt`
- LaunchPad stage return for P9 QA

Artifacts must redact:

- raw provider API key
- provider base URL if copied from user settings
- model configuration headers
- local DB paths
- raw request headers

## Implementation Readiness Criteria

Only after this QA plan and contract are accepted should implementation begin.

Implementation must include:

- separate Product API health and provider-model test actions
- DeepSeek preset UI
- custom provider mode preserved
- thinking on/off UI
- provider diagnostics with stable error codes
- no raw reasoning content surfaced to users
- no visible P8 active-team chip on Chat main screen
