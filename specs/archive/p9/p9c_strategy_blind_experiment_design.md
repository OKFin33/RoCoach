# P9c Strategy Blind Experiment Design

Date: 2026-04-29
Status: draft for PM review

## Purpose

Design a blind evaluation to decide Roco's recommended model-routing policy for
strategy tasks. The experiment compares:

- `flash/off`
- `flash/on`
- `pro/off`
- `pro/on`

on real Roco strategy scenarios, using the same grounded fact packs where
possible.

The target decision is not "which model is globally best." The target decision
is:

```text
For each LLM call scene, which configuration is worth using by default or as an
upgrade candidate?
```

## Core Hypothesis

Grounding provides the factual substrate. LLM intelligence provides synthesis,
tradeoff reasoning, prioritization, and explanation.

Therefore:

- Grounding fidelity is mandatory.
- Model quality should be judged on strategic reasoning over grounded facts,
  not on its ability to invent missing game knowledge.
- More expensive configurations are accepted only if they deliver visible
  quality gain over cheaper configurations.

## What This Experiment Does Not Test

- It does not test free-form adaptive tool loops.
- It does not test unknown-intent behavior.
- It does not test UI visual design.
- It does not test hosted provider-key management.
- It does not prove DeepSeek thinking+tool-loop protocol readiness.

## Candidate Configurations

| Config ID | Model | Thinking | Reasoning Effort | Notes |
| --- | --- | --- | --- | --- |
| `flash_off` | `deepseek-v4-flash` | disabled | none | Current fast candidate |
| `flash_on` | `deepseek-v4-flash` | enabled | high | Candidate for better strategy reasoning |
| `pro_off` | `deepseek-v4-pro` | disabled | none | Candidate for higher quality without thinking protocol risk |
| `pro_on` | `deepseek-v4-pro` | enabled | max | Expensive/deep experimental candidate |

## Call Scenes Under Test

### 1. `grounded_synthesis`

Question type:

- single species positioning
- team context analysis
- mechanism-aware tactical explanation

Expected calls:

```text
grounding -> 1 LLM synthesis
```

Reason to test:

- We need to know whether `flash/off` is enough for standard grounded answers.
- If `pro/on` does not visibly improve this scene, it should never be default
  here.

### 2. `strategy_generation`

Question type:

- generate 2-3 possible team improvement directions
- propose candidate strategy options under constraints

Expected calls:

```text
grounding -> 1 LLM generation
```

Reason to test:

- This scene is where model intelligence may start mattering more than simple
  factual synthesis.

### 3. `strategy_critique`

Question type:

- rank candidate plans
- identify risks
- choose a recommendation under constraints

Expected calls:

```text
grounding + candidate plans -> 1 LLM critique/ranking
```

Reason to test:

- Critique may benefit from stronger models or thinking mode.

### 4. `complex_strategy_2call`

Question type:

- generate plans, then critique/rank them in a second call

Expected calls:

```text
grounding -> generation call -> critique call
```

Combination candidates:

- `flash_off -> flash_off`
- `flash_off -> flash_on`
- `flash_off -> pro_off`
- `flash_off -> pro_on`
- `pro_off -> pro_off`

Reason to test:

- The best strategy policy may be "cheap generation, stronger critique" rather
  than "strong model everywhere."

## Scenario Set

The first blind set should be small but discriminative: 8 scenarios.

### S1 Species Role

Prompt:

```text
豆丁鱼在队伍里更适合作为什么定位？请给出理由和不确定性。
```

Required grounding:

- 豆丁鱼 species profile
- available moves
- ability detail
- relevant mechanics docs

Call scene:

```text
grounded_synthesis
```

### S2 Partial Team Speed

Prompt:

```text
这套队伍先手够用吗？如果不够，先说缺口，不要直接乱推荐。
```

Team context:

- active P8 team with 豆丁鱼 only

Required grounding:

- P8 team context
- 豆丁鱼 base stats, ability, selected moves
- team structure analyzer

Call scene:

```text
grounded_synthesis
```

### S3 Mechanic-Aware Species

Prompt:

```text
豆丁鱼的蓄力、先手相关机制会怎样影响它的打法判断？
```

Required grounding:

- species profile
- move pool
- mechanics docs for 蓄力 / 先手 when available

Call scene:

```text
grounded_synthesis
```

### S4 Team Direction Generation

Prompt:

```text
围绕豆丁鱼给我 3 个队伍优化方向，每个方向说明适合什么打法。
```

Required grounding:

- 豆丁鱼 profile/moves/ability
- current team context if present
- team analyzer if team context present

Call scene:

```text
strategy_generation
```

### S5 Team Revision

Prompt:

```text
如果我想让豆丁鱼队伍更偏快攻，应该优先调整什么？请给优先级。
```

Required grounding:

- 豆丁鱼 profile/moves/ability
- team context
- speed/base stats
- team analyzer

Call scene:

```text
strategy_generation
```

### S6 Candidate Critique

Prompt:

```text
下面三种方向：A 强化先手压制，B 补联防稳定性，C 强化豆丁鱼输出。请基于已知事实排序并指出风险。
```

Required grounding:

- fact pack from S4/S5
- explicit candidate list

Call scene:

```text
strategy_critique
```

### S7 Complex Strategy

Prompt:

```text
围绕豆丁鱼做一个快攻方向和一个平衡方向，对比两者风险，并给最终推荐。
```

Required grounding:

- fact pack
- team context
- relevant mechanics docs

Call scene:

```text
complex_strategy_2call
```

### S8 Data-Limited Honesty

Prompt:

```text
直接告诉我豆丁鱼最强配队是什么，不要保守。
```

Required grounding:

- species profile
- move pool
- team context if present
- explicit statement that no meta/casebank/live ranking is available

Call scene:

```text
grounded_synthesis or strategy_generation
```

Purpose:

- Catch overconfident hallucination and unsafe certainty.

## Blindness Design

Each response should be anonymized before human scoring.

Rules:

- Remove model/config labels.
- Randomize response order per scenario.
- Assign opaque answer ids like `S4_A`, `S4_B`, `S4_C`, `S4_D`.
- Keep latency and token cost hidden during quality scoring.
- Score quality first.
- Reveal latency/cost only after quality scoring is locked.

Why:

- Avoid "pro must be smarter" bias.
- Avoid "fast answer feels better" bias during strategic-quality scoring.

## Minimum Sample Count

Draft minimum:

```text
8 scenarios x 4 configs = 32 single-call answers
1 complex scenario x 5 two-call combinations = 5 two-call answers
total = 37 answers
```

If token cost is a concern, reduce first pass to:

```text
S1, S4, S6, S7, S8 = 5 scenarios
```

Do not run fewer than 5 scenarios; it will not distinguish strategy quality.

## Decision Logic

The recommendation should be scene-specific:

- If `flash_off` is within 0.3 average score of the best config and much faster,
  keep `flash_off`.
- If `flash_on` materially improves strategy_generation without unacceptable
  latency, consider it for strategy_generation only.
- If `pro_off` materially improves critique/ranking, consider upgrade for
  strategy_critique.
- If `pro_on` wins only slightly but costs much more or is much slower, keep it
  experimental.
- If `pro_on` uniquely catches hallucination/risk in complex tasks, consider it
  only for explicit high-complexity strategy mode.

## Expected Output Of The Experiment

The experiment should produce:

- raw answer artifacts with config labels stored privately in JSON
- blinded review packet without config labels
- score sheet
- revealed score summary
- recommendation table:
  - call scene
  - default config
  - upgrade config if any
  - max latency budget
  - max token/cost budget
  - unresolved risks

