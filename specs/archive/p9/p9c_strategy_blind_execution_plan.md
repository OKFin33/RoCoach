# P9c Strategy Blind Execution Plan

Date: 2026-04-29
Status: draft for PM review

## Goal

Run a blind evaluation of Roco strategy answers across:

- `flash/off`
- `flash/on`
- `pro/off`
- `pro/on`

The run must produce artifacts that allow quality scoring before model identity,
latency, and cost are revealed.

## Preconditions

Required:

- Local backend can start with `bash scripts/run_local_api.sh`.
- DeepSeek key is configured outside the repo at:

```text
~/.config/roco-advisor/env
```

- The local env provides:

```text
ROCO_OPENAI_BASE_URL=https://api.deepseek.com
ROCO_OPENAI_API_KEY=<local secret>
```

- `data/runtime/battle_dex.sqlite` exists.
- `artifacts/p9/` is available for output.

Do not proceed if:

- provider key would be printed
- Product API is not reachable
- redaction check fails
- the user has not accepted token consumption

## Artifacts To Produce

Planned output directory:

```text
artifacts/p9c_strategy_eval/
```

Files:

- `raw_answers.json`
  - contains config ids, timings, token usage if available, raw answers
  - internal only; do not use for blind scoring
- `blind_review_packet.json`
  - anonymized answer ids only
  - no config labels
  - no latency/cost
- `blind_review_packet.md`
  - human-readable packet for PM scoring
- `score_sheet_template.csv`
  - one row per anonymized answer
  - rubric dimensions as columns
- `reveal_map.json`
  - answer id -> config id
  - keep hidden until scoring is locked
- `redaction_check.txt`
  - `redaction=pass` required
- `run_summary.md`
  - generated after scoring/reveal

## Execution Phases

### Phase 1: Build Grounding Packs

For each scenario:

1. Resolve species/moves/mechanics/team context locally.
2. Build compact fact pack.
3. Store fact pack in internal raw artifact.
4. Do not let a model invent missing facts.

Fact pack should include only high-signal fields:

- species display name
- type
- ability
- ability effect when available
- key base stats
- selected moves
- relevant move pool subset
- team slot count
- deterministic team structure summary
- relevant reviewed mechanics snippets
- explicit missing-data notes

### Phase 2: Generate Answers

For each scenario and config:

1. Create the prompt for the call scene.
2. Send the same fact pack to every config.
3. Collect answer text.
4. Collect elapsed seconds.
5. Collect provider token usage if exposed.
6. Redact provider secrets/base URL/model headers from artifacts.

Config mapping:

| Config ID | Model | Thinking | Effort |
| --- | --- | --- | --- |
| `flash_off` | `deepseek-v4-flash` | disabled | none |
| `flash_on` | `deepseek-v4-flash` | enabled | high |
| `pro_off` | `deepseek-v4-pro` | disabled | none |
| `pro_on` | `deepseek-v4-pro` | enabled | max |

### Phase 3: Blind Packet Generation

For each scenario:

1. Randomize answer order.
2. Replace config id with opaque answer id.
3. Hide latency/cost/token usage.
4. Include the same scenario prompt and fact pack summary for every answer.
5. Write `blind_review_packet.md`.

Opaque id pattern:

```text
S{scenario_number}_{letter}
```

Example:

```text
S4_A
S4_B
S4_C
S4_D
```

### Phase 4: Human Blind Scoring

The PM or reviewer fills `score_sheet_template.csv`.

Required scoring dimensions:

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

Rules:

- Score quality before reveal.
- Do not inspect `raw_answers.json` or `reveal_map.json`.
- Do not use latency/cost in the first scoring pass.

### Phase 5: Reveal And Summarize

After scores are locked:

1. Join scores with `reveal_map.json`.
2. Compute weighted quality score.
3. Add latency/cost.
4. Compute per-call-scene averages.
5. Identify default and upgrade candidates.

Decision rules:

- `flash_off` remains default if it is within 0.3 score of the best config and
  materially faster/cheaper.
- `flash_on` may become strategy-generation upgrade if quality delta >= 0.4
  without unacceptable latency.
- `pro_off` may become critique upgrade if quality delta >= 0.4.
- `pro_on` requires decisive quality gain or unique hallucination/risk
  avoidance to move beyond experimental.

## Prompt Design Rules

Every answer prompt must include:

- user question
- call scene
- compact fact pack
- output requirements
- grounding boundary
- "Do not invent facts not present in the fact pack."
- "If data is insufficient, say what is missing."

Do not include:

- config id
- provider name
- model name
- chain-of-thought request
- raw database dumps
- secret headers
- internal file paths

## Proposed Prompt Skeleton

```text
You are Roco's strategy synthesis call.

Call scene: {call_scene}
User question: {user_question}

Grounded fact pack:
{fact_pack}

Rules:
- Use only the fact pack for confirmed Roco facts.
- You may reason, compare, prioritize, and explain.
- Do not invent species, moves, abilities, meta stats, win rates, or official changes.
- If evidence is missing, state the missing evidence.
- Keep the answer concise but strategically useful.
- Use 洛克王国世界 terminology: 精灵, 技能, 队伍. Do not say Pokémon/宝可梦.

Required output:
{scene_specific_output_schema_or_bullets}
```

## Initial Manual Run Scope

If cost/time is acceptable, run all:

```text
S1-S8 x four configs + S7 two-call combinations
```

If cost/time needs containment, run first pass:

```text
S1, S4, S6, S7, S8
```

Minimum acceptable first pass:

```text
5 scenarios
```

## Safety And Redaction

Required redaction checks:

- API key absent from all artifacts.
- Provider base URL absent from public/blind artifacts.
- Runtime headers absent from answer text.
- Local file paths absent from blind packet.
- Raw tool payloads absent from blind packet unless explicitly summarized.

If redaction fails:

```text
stop, delete unsafe artifact, repair sanitizer, rerun
```

## Implementation Recommendation

Add a script:

```text
artifacts/p9c_strategy_eval/run_strategy_blind_eval.py
```

Suggested structure:

```text
load_runtime_config()
build_scenarios()
build_fact_pack(scenario)
run_single_call(config, scenario, fact_pack)
run_two_call_combo(combo, scenario, fact_pack)
write_raw_answers()
write_blind_packet()
write_score_sheet_template()
write_reveal_map()
run_redaction_check()
```

Do not integrate this script into mobile or backend runtime yet. This is an
eval harness, not production policy implementation.

## Exit Criteria

This planning slice is complete when:

- experiment design exists
- eval rubric exists
- execution plan exists
- PM accepts or revises the scenario set and scoring dimensions

The actual live blind run is a separate dispatch because it consumes provider
tokens and produces scoring artifacts.

