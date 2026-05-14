# P9d Reasoning Effort And Controlled Loop Execution Plan

Date: 2026-04-29
Status: draft for PM review

## Goal

Run a smaller, cleaner live matrix than P9c to decide:

- whether `flash_high` should replace `flash_disabled` for default grounded
  answers,
- whether `pro_high` is enough for complex strategy,
- whether `pro_max` is only worth using for explicit deep/loop tasks,
- whether a bounded controlled loop is safe enough to keep designing,
- whether DeepSeek thinking+tool long-dialog history can be maintained without
  protocol errors or hidden-reasoning leaks.

## Required Preconditions

- DeepSeek API key is configured only outside the repo.
- Provider calls can explicitly set:
  - `extra_body: {"thinking": {"type": "disabled"}}`
  - `extra_body: {"thinking": {"type": "enabled"}}`
  - `reasoning_effort: "high"`
  - `reasoning_effort: "max"`
- Backend grounding works for species, move pool, team context, and team
  structure analysis.
- Candidate species search exists or a deterministic local candidate fixture is
  prepared for S9.
- User accepts token-consuming live tests.

Stop immediately if:

- API key or provider secret appears in any artifact.
- `reasoning_effort="max"` is rejected by provider.
- thinking disabled cannot be explicitly enforced.
- loop trace leaks raw internal/tool payload into blind packet.

## Output Directory

```text
artifacts/p9d_reasoning_effort_loop_eval/
```

## Config Matrix

| Config ID | Model | Request shape |
| --- | --- | --- |
| `flash_disabled` | `deepseek-v4-flash` | `extra_body.thinking.type=disabled` |
| `flash_high` | `deepseek-v4-flash` | `reasoning_effort=high`, `extra_body.thinking.type=enabled` |
| `pro_disabled` | `deepseek-v4-pro` | `extra_body.thinking.type=disabled` |
| `pro_high` | `deepseek-v4-pro` | `reasoning_effort=high`, `extra_body.thinking.type=enabled` |
| `pro_max` | `deepseek-v4-pro` | `reasoning_effort=max`, `extra_body.thinking.type=enabled` |
| `pro_high_loop` | `deepseek-v4-pro` | same as `pro_high`, controlled loop wrapper |
| `pro_max_loop` | `deepseek-v4-pro` | same as `pro_max`, controlled loop wrapper |
| `pro_high_long_context` | `deepseek-v4-pro` | same as `pro_high`, multi-turn thinking/tool history |
| `pro_max_long_context` | `deepseek-v4-pro` | same as `pro_max`, multi-turn thinking/tool history |

## Scenario Matrix

| Scenario | Scene | Configs |
| --- | --- | --- |
| S1 | grounded synthesis | `flash_disabled`, `flash_high` |
| S4 | strategy generation | `pro_high`, `pro_max` |
| S6 | strategy critique | `pro_disabled`, `pro_high` |
| S8 | honesty boundary | `flash_disabled`, `flash_high` |
| S9 | controlled loop team search | `pro_high_loop`, `pro_max_loop` |
| S10 | multi-turn thinking/tool context continuity | `pro_high_long_context`, `pro_max_long_context` |

Total planned calls:

- Fixed single-call scenarios: 8 provider calls.
- Loop scenarios: up to 8 provider calls total if each loop uses 4 LLM calls.
- Long-context scenarios: up to 12 provider calls total if each run uses 6 LLM
  calls.
- Total worst case: 28 provider calls.

## Run Order

Use deterministic shuffled order to reduce cache bias.

Required artifact field:

```json
{
  "run_order_seed": "...",
  "scenario_config_order": {
    "S1": ["...", "..."]
  }
}
```

Recommended:

- Shuffle config order per scenario with fixed seed.
- If token budget allows, rerun S1/S8 with reversed config order and mark them
  as latency-only repeats, not quality duplicates.

## Phase 1: Provider Capability Probe

Run tiny non-sensitive requests:

1. `flash_disabled`
2. `flash_high`
3. `pro_disabled`
4. `pro_high`
5. `pro_max`

Record:

- status
- elapsed seconds
- token usage
- reasoning token usage
- whether provider accepted request shape

No prompt should include game data in this phase.

## Phase 2: Grounding Pack Build

For S1/S4/S6/S8:

- Build fact packs identical in structure to P9c minimal where possible.
- Include explicit missing data:
  - no live meta
  - no casebank
  - incomplete charge/speed mechanics if still incomplete
  - partial team when only one slot exists

For S9:

- Build core fact pack for 豆丁鱼.
- Build deterministic candidate fixture or search index query plan.
- Candidate search must return only real local database species.

For S10:

- Build the same core fact pack and candidate fixture/search access as S9.
- Prepare a two-user-turn conversation where Turn 2 depends on Turn 1 tool
  evidence and explicitly says not to re-check already-known information.

## Phase 3: Fixed-Call Generation

For S1/S4/S6/S8:

1. Send same fact pack to each scenario's configs.
2. Record raw answer.
3. Record usage, reasoning tokens, cache hit/miss tokens, and elapsed seconds.
4. Redact provider headers and secrets.

Prompt must include:

- call scene
- user prompt
- compact fact pack
- grounding boundary
- no invented species/moves/meta/win-rate rule
- concise but strategically useful output requirement

## Phase 4: Controlled Loop Generation For S9

Loop wrapper must be deterministic outside model decisions.

Allowed tools:

- `search_species_candidates`
- `get_species_profile`
- `get_species_available_moves`
- `analyze_team_structure`

Hard limits:

- max LLM calls: 4
- max tool calls: 8
- timeout: 180 seconds
- no identical repeated tool call
- no live meta claims
- reserve one final LLM call for synthesis
- when remaining LLM calls is 1, tools must be disabled
- if the model requests more tools while final-call budget is reserved, the
  harness must reject that request and run final synthesis from the evidence
  ledger

Provider protocol:

- For a thinking turn without tool calls, assistant `reasoning_content` does
  not need to be replayed in later requests.
- For a thinking turn with tool calls, the assistant message containing
  `reasoning_content`, `content`, and `tool_calls` must be preserved and
  replayed in later requests, with matching tool result messages.
- Hidden reasoning content must never be written to public/blind artifacts.

Finalization control:

- The harness owns budget, not the model.
- Maintain an evidence ledger across rounds:
  - searched candidate queries
  - candidate ids/names returned
  - inspected profile summaries
  - inspected move-pool summaries
  - structure-analysis summaries
- Before the final reserved call, build a final prompt:

```text
You are now in finalization mode.
No more tools are available.
Use only the evidence ledger below.
Produce the final recommendation and explain why the loop stops.
```

- The final reserved call must run with tools disabled.
- If no final answer is produced, mark `stop_reason=tool_budget_exhausted_no_final`
  and fail the gate.

Loop transcript for blind packet should be summarized as:

```text
Round 1: requested candidate search for X.
Tool observation: 6 candidates returned, names redacted or retained depending
on whether they are public game facts.
Round 2: inspected candidates A/B/C.
Tool observation: profiles and available moves returned.
Round 3: requested team-structure comparison.
Tool observation: candidate B improved structure most.
Final: recommended B/C and explained stop reason.
```

Do not include:

- raw JSON payloads
- internal trace IDs
- hidden reasoning content
- provider/model identity

## Phase 4b: Multi-Turn Thinking/Tool Context Test For S10

S10 verifies long conversation stitching, not just final answer quality.

Turn sequence:

```text
Turn 1: user asks for two team-patch directions and what local information
needs checking.
Turn 1 runtime: model may request tools; runtime executes allowed tools.
Turn 1 assistant: visible answer plus internal provider-required reasoning/tool
history preserved.

Turn 2: user says to continue from prior evidence and not re-check known facts.
Turn 2 runtime: sends conversation history according to DeepSeek protocol.
Turn 2 runtime: passes an "already checked" evidence ledger from Turn 1.
Turn 2 assistant: final recommendation.
```

Allowed tools:

- `search_species_candidates`
- `get_species_profile`
- `get_species_available_moves`
- `analyze_team_structure`

Protocol assertions:

- If Turn 1 has tool calls, Turn 2 request must include the prior assistant
  message with `reasoning_content`, visible `content`, and `tool_calls`.
- Tool result messages must match prior `tool_call_id`.
- If Turn 1 has no tool calls, Turn 2 may omit `reasoning_content`.
- Hidden reasoning content must not appear in public answer, blind packet, or
  review logs.
- Turn 2 should reuse prior evidence and avoid identical repeated lookups.

Finalization assertions:

- One final LLM call must be reserved for Turn 2 final synthesis.
- When only that final call remains, tools must be disabled.
- If the model requests a tool at final-call budget, block the tool request and
  force final synthesis from the evidence ledger.
- The final prompt must say not to call tools and to produce the final answer
  now.

Evidence ledger requirements:

- Turn 1 tool observations must be summarized into a compact ledger.
- Turn 2 must receive the ledger as already-known evidence.
- The ledger must be public-safe and must not contain raw tool JSON.

S10 raw artifact must record:

- provider status per call
- whether tool-call reasoning history was included
- whether any provider protocol error occurred
- repeated-tool-call detection result
- redaction result for hidden reasoning
- whether final-call budget was reserved
- whether tools were disabled for finalization
- stop reason

## Phase 5: Blind Packet

Create:

- `blind_review_packet.md`
- `blind_review_packet.json`
- `score_sheet_template.csv`
- `loop_score_sheet_template.csv`
- `long_context_score_sheet_template.csv`
- `reveal_map.json`

Blind packet must hide:

- model
- config
- latency
- token usage
- cache status

## Phase 6: Blind Scoring

Reviewer scores before reveal.

Use P9c dimensions for all answers:

- grounding_fidelity
- strategic_depth
- actionability
- risk_awareness
- constraint_following
- concision_and_structure
- persona_fit
- refusal_or_clarify_quality
- hallucination_flag
- hard_fail_notes

Add loop dimensions for S9:

- loop_tool_selection
- loop_stopping_quality
- loop_evidence_integration
- loop_budget_discipline
- finalization_control

Add long-context dimensions for S10:

- protocol_continuity
- prior_evidence_reuse
- no_hidden_reasoning_leak
- redundant_lookup_avoidance
- finalization_control

## Phase 7: Reveal

After scoring is locked:

1. Join scores with `reveal_map.json`.
2. Add latency/token/cache/reasoning usage from raw artifacts.
3. Compute per-config score.
4. Compute per-scene winner.
5. Write `revealed_config_summary.md`.

## Decision Surface After Reveal

Expected PM decision:

- default: `flash_disabled` or `flash_high`
- complex strategy: `pro_high` or `pro_max`
- critique: `pro_disabled` or `pro_high`
- loop: keep disabled or continue loop development with `pro_high_loop`/`pro_max_loop`
- long-dialog thinking/tool mode: blocked or continue protocol hardening with
  `pro_high_long_context`/`pro_max_long_context`

No production runtime change should be made in this slice unless PM explicitly
dispatches implementation after reviewing the reveal.
