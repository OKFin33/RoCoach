# P9d Reasoning Effort And Controlled Loop Eval Design

Date: 2026-04-29
Status: draft for PM review

## Purpose

P9c showed that a single global model preset is the wrong abstraction. Roco
should route different LLM calls by task role and complexity.

P9d narrows the next live experiment to the configurations that matter under
the current DeepSeek premise:

```text
thinking disabled
thinking enabled + reasoning_effort=high
thinking enabled + reasoning_effort=max
```

The target decision is:

```text
Which call roles should use flash/pro, disabled/high/max, and when is max worth
the latency/cost?
```

## Assumptions To Validate

These are treated as test assumptions, not permanent product truth:

- DeepSeek thinking mode can be explicitly disabled with
  `extra_body: {"thinking": {"type": "disabled"}}`.
- Thinking mode can be explicitly enabled with
  `extra_body: {"thinking": {"type": "enabled"}}`.
- `reasoning_effort="high"` is the normal thinking effort.
- `reasoning_effort="max"` is the complex-Agent/deep effort.
- Compatibility mappings such as low/medium -> high and xhigh -> max are not
  product-facing settings and should not appear in the Roco UI.

If any assumption fails at provider level, the run must stop and record the
provider incompatibility.

## Candidate Configurations

| Config ID | Model | Thinking | Reasoning effort | Intended role |
| --- | --- | --- | --- | --- |
| `flash_disabled` | `deepseek-v4-flash` | disabled | none | cheapest default / honesty guard |
| `flash_high` | `deepseek-v4-flash` | enabled | high | normal grounded synthesis candidate |
| `pro_disabled` | `deepseek-v4-pro` | disabled | none | critique/ranking candidate |
| `pro_high` | `deepseek-v4-pro` | enabled | high | complex strategy candidate |
| `pro_max` | `deepseek-v4-pro` | enabled | max | controlled loop / final arbitration candidate |

Do not test `flash_max` in the default run. Max effort is expensive and should
be justified first on pro/deep tasks.

## Experiment Questions

### Q1: Is `flash_high` good enough to replace `flash_disabled` for default grounded answers?

Test scenes:

- `grounded_synthesis`
- `honesty_boundary`
- `team_context_analysis`

Compare:

- `flash_disabled`
- `flash_high`

Acceptance:

- `flash_high` may replace `flash_disabled` only if it reduces hard failures or
  materially improves strategic usefulness without unacceptable latency/token
  increase.
- Context cache hit must be reported separately from cache miss latency.

### Q2: Does `pro_high` capture most of `pro_max` quality on complex strategy?

Test scenes:

- `strategy_generation`
- `complex_strategy_fixed_2call`

Compare:

- `pro_high`
- `pro_max`

Acceptance:

- `pro_max` is accepted only if it produces a clear quality delta in hard cases
  or avoids hard failures that `pro_high` makes.
- If `pro_high` is within 0.2 weighted score of `pro_max`, use `pro_high` for
  non-loop complex strategy.

### Q3: Is `pro_disabled` useful for critique/risk review?

Test scene:

- `strategy_critique`

Compare:

- `pro_disabled`
- `pro_high`

Acceptance:

- `pro_disabled` remains a critique candidate if it is competitive and faster.
- If it hallucinated or over-certifies, prefer `pro_high`.

### Q4: Is `pro_max` worth using for a bounded controlled loop?

Test scene:

- `controlled_loop_team_search`

Compare:

- `pro_high_loop`
- `pro_max_loop`

Acceptance:

- `pro_max_loop` must produce visibly better loop decisions, better stopping,
  fewer unsupported claims, or better final recommendation.
- If the final answer quality is similar, use `pro_high_loop` or avoid loop.

### Q5: Can Roco safely maintain long multi-turn thinking/tool context?

Test scene:

- `multi_turn_tool_context_continuity`

Compare:

- `pro_high_long_context`
- `pro_max_long_context`

Acceptance:

- The runtime must follow DeepSeek's thinking-mode conversation rules:
  - no-tool thinking turns do not need `reasoning_content` replay;
  - thinking turns with tool calls must preserve and replay the assistant
    `reasoning_content` alongside `tool_calls` in later requests.
- The conversation must not fail because of malformed thinking/tool history.
- Hidden reasoning content must remain internal and never appear in blind or
  public artifacts.

## Scenario Set

Use the same 豆丁鱼 fact pack style as P9c for continuity, but add one controlled
loop scenario that requires iterative tool observations.

### S1 Species Role

Prompt:

```text
豆丁鱼在队伍里更适合作为什么定位？请给出理由和不确定性。
```

Call scene:

```text
grounded_synthesis
```

Configs:

- `flash_disabled`
- `flash_high`

### S4 Team Direction Generation

Prompt:

```text
围绕豆丁鱼给我 3 个队伍优化方向，每个方向说明适合什么打法。
```

Call scene:

```text
strategy_generation
```

Configs:

- `pro_high`
- `pro_max`

### S6 Candidate Critique

Prompt:

```text
下面三种方向：A 强化先手压制，B 补联防稳定性，C 补豆丁鱼输出。请基于已知事实排序并指出风险。
```

Call scene:

```text
strategy_critique
```

Configs:

- `pro_disabled`
- `pro_high`

### S8 Honesty Boundary

Prompt:

```text
直接告诉我豆丁鱼最强配队是什么，不要保守。
```

Call scene:

```text
honesty_boundary
```

Configs:

- `flash_disabled`
- `flash_high`

### S9 Controlled Loop Team Search

Prompt:

```text
围绕豆丁鱼，从候选精灵池里搜索 2 个最适合补队的方向。你可以分轮查看候选信息，但最终必须说明为什么停止。
```

Call scene:

```text
controlled_loop_team_search
```

Configs:

- `pro_high_loop`
- `pro_max_loop`

Loop shape:

```text
round 0: user question + compact team/core fact pack
round 1: model chooses candidate search constraints
tool: search_species_candidates(query/filters, limit=6)
round 2: model chooses up to 3 candidates to inspect
tool: get_species_profile + get_species_available_moves for selected candidates
round 3: model ranks candidates, optionally requests one structure analysis
tool: analyze_team_structure(candidate additions)
round 4: final recommendation and stop reason, tools disabled
```

Hard limits:

- max LLM calls: 4
- max tool calls: 8
- max wall time: 180 seconds
- max output tokens per LLM call: implementation-defined but must be logged
- no repeated identical tool call
- no live meta or casebank claim
- one LLM call must be reserved for final synthesis
- when remaining LLM calls == 1, tools must be disabled
- if a model requests tools when only final-call budget remains, reject the tool
  request and force final synthesis from the evidence ledger

Evidence ledger:

- The harness must maintain a compact ledger of searched candidates, inspected
  candidates, observed profiles, observed move pools, and structure-analysis
  results.
- The final prompt must include this ledger.
- The final prompt must explicitly state that no more tools are available and a
  final answer is required.

Required loop trace fields:

- `round_index`
- `config_id`
- `model`
- `thinking`
- `reasoning_effort`
- `tool_calls_requested`
- `tool_calls_executed`
- `elapsed_seconds`
- `prompt_tokens`
- `completion_tokens`
- `reasoning_tokens`
- `cache_hit_tokens`
- `cache_miss_tokens`
- `stop_reason`
- `remaining_llm_calls`
- `tools_enabled`
- `evidence_ledger_summary`

Allowed stop reasons:

- `tool_calls`
- `assistant_content`
- `final_answer`
- `budget_reserved_for_final`
- `tool_budget_exhausted_no_final`
- `timeout`

`tool_budget_exhausted_no_final` is a harness failure and must trigger the stop
gate.

Public blind packet must include only:

- user prompt
- fact pack
- anonymized final answer
- anonymized summarized loop transcript

Public blind packet must not include:

- model/config id
- raw tool JSON payloads
- internal trace IDs
- provider headers
- hidden reasoning content

### S10 Multi-Turn Thinking/Tool Context Continuity

Prompt sequence:

```text
Turn 1: 围绕豆丁鱼检查两个补队方向，并说明你需要查哪些本地信息。
Turn 2: 在上一轮基础上继续，不要重查已经查过的内容；给出最终推荐。
```

Call scene:

```text
multi_turn_tool_context_continuity
```

Configs:

- `pro_high_long_context`
- `pro_max_long_context`

Purpose:

- Verify DeepSeek thinking-mode long conversation behavior with tool calls.
- Confirm that Roco preserves provider-required `reasoning_content` internally
  when a prior assistant message contains tool calls.
- Confirm that Roco does not expose hidden reasoning content to the user or
  public artifacts.

Protocol expectation:

- If a thinking turn uses no tool calls, its `reasoning_content` may be omitted
  from the next user turn context.
- If a thinking turn uses tool calls, its assistant message must be preserved
  with `reasoning_content`, `content`, and `tool_calls` for later API requests.
- Tool results must be preserved with matching `tool_call_id`.
- The visible final answer must summarize evidence, not hidden reasoning.

Hard limits:

- max user turns: 2
- max LLM calls across both turns: 6
- max tool calls across both turns: 10
- max wall time: 240 seconds
- no repeated identical tool call unless Turn 2 explicitly requires refreshed
  evidence
- one final LLM call must be reserved for Turn 2 synthesis
- when remaining LLM calls == 1, tools must be disabled
- the Turn 2 final prompt must include an evidence ledger and explicitly say
  "do not call tools; produce the final recommendation now"

Evidence ledger:

- Turn 1 ledger must record searched candidates and any inspected tool evidence.
- Turn 2 must receive the ledger as "already checked" context.
- If the model asks to re-check an identical lookup without a new reason, the
  harness must block the call and force final synthesis from the ledger.

S10 hard fail caps:

- provider failure caused by malformed thinking/tool history: score zero for
  protocol readiness
- hidden reasoning exposed in public answer/artifact: score zero
- repeated already-known lookup despite "不要重查" instruction: cap total at 3
- false claim that previous tool evidence was unavailable: cap total at 3
- tool budget exhausted without final answer: score zero for finalization

## Scoring Additions

Use the P9c rubric for final-answer quality, plus loop-specific dimensions for
S9/S10:

| Dimension | Scale | Meaning |
| --- | --- | --- |
| `loop_tool_selection` | 1-5 | Chose useful tools/candidates rather than wandering |
| `loop_stopping_quality` | 1-5 | Stopped for a defensible reason under budget |
| `loop_evidence_integration` | 1-5 | Used tool observations accurately in final recommendation |
| `loop_budget_discipline` | 1-5 | Avoided unnecessary calls/tokens |
| `finalization_control` | 1-5 | Produced a final answer after tool observations without spending final-call budget on more tools |

S9 hard fail caps:

- invented candidate species not returned by tools: cap total at 2
- repeated identical tool call without new reason: cap total at 3
- live-meta or win-rate claim without data: cap total at 2
- leaked raw trace/tool payload to user-facing answer: score zero

For S10, also score:

- long-context protocol correctness
- reuse of previous tool evidence
- avoidance of redundant re-grounding
- preservation of user-visible continuity without exposing hidden reasoning
- final-call reservation and tool-disable behavior

## Latency And Cache Rules

Latency comparison must separate:

- cold/cached-miss calls
- cache-hit calls
- total wall-clock for full workflow
- per-call latency
- reasoning token count

The run order must be randomized or counterbalanced. Do not run every disabled
configuration before every high configuration, because DeepSeek context caching
can bias the later config.

Recommended run order:

```text
For each scenario, shuffle config order with a fixed seed and record the seed.
Repeat S1/S8 once with reversed order if token budget allows.
```

## Decision Rules

### Default Chat Policy

Use `flash_high` as default only if:

- it beats or ties `flash_disabled` on S1/S8 quality,
- it does not increase hard failures,
- and cache-miss latency remains acceptable.

Otherwise:

- keep `flash_disabled` for default chat and honesty-boundary routes.

### Complex Strategy Policy

Use `pro_high` for normal complex strategy if:

- it is close to `pro_max` on S4,
- and avoids hard failures.

Use `pro_max` only for:

- user-explicit "深度分析" / "全面推演",
- controlled loop tasks,
- or final arbitration after cheaper calls disagree.

### Loop Policy

Do not enable loop in V1 unless S9 passes:

- final answer quality >= 4.0,
- no hard fails,
- no trace leaks,
- no repeated identical calls,
- finalization_control >= 4.0,
- and total latency/token cost is acceptable for an explicit deep-action mode.

If S9 fails:

- keep loop disabled,
- continue using fixed 1-2 call workflows.

Do not enable thinking+tool long-dialog mode unless S10 passes:

- no provider protocol failures,
- no reasoning-content leak,
- and no repeated already-known lookup in Turn 2.
- final answer is produced after final-call reservation.

## Expected Output Artifacts

Directory:

```text
artifacts/p9d_reasoning_effort_loop_eval/
```

Files:

- `raw_answers.json`
- `raw_loop_traces.json`
- `blind_review_packet.md`
- `blind_review_packet.json`
- `score_sheet_template.csv`
- `loop_score_sheet_template.csv`
- `long_context_score_sheet_template.csv`
- `reveal_map.json`
- `redaction_check.txt`
- `generation_summary.md`
- `revealed_config_summary.md` after scoring

## Non-Goals

- This experiment does not redesign UI settings.
- This experiment does not enable loop in production.
- This experiment does not expose model routing to users.
- This experiment does not test arbitrary user-created API providers.
