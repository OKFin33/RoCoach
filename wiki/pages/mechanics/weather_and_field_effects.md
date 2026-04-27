---
title: "Weather And Field Effects"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-04_bilibili_weather_tutorial.md"
  - "wiki/cache/天气速成0404/NoteGPT_《洛克王国：世界》魔法学院新生速成，玩转天气机制！.txt"
  - "wiki/cache/速度线:词条 0403/NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt"
  - "wiki/cache/光合武队0414/NoteGPT_《光合武队怎么玩？一期视频讲清它的底层逻辑》.txt"
a_layer_refs:
  - "data/reference/luoke_world_type_database_v2.json"
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-20"
reviewed_by: "systematic_cache_check"
human_confirmed:
  - "沙暴主要触发技能: 沙咏, 能耗 7"
  - "沙暴没有回合结束伤害机制"
  - "雨天使水系技能伤害提升 50%"
  - "每层冻结冻结 5% 生命值；当前生命值低于冻结比例则力竭；冰系免疫冻结"
  - "每次增加冻结层数时都检查是否达到力竭条件"
  - "技能结算先于回合结束天气结算"
  - "雪天和暴风雪指向同一个游戏内天气机制"
persona_free: true
---

# Weather And Field Effects

## Claim

Weather is a global, public, mutually exclusive, time-limited field condition.
It should be modeled separately from marks, ordinary buffs/debuffs, and species
traits.

Weather gives teams a timed conversion window:

- rain converts setup into water damage pressure
- sandstorm converts setup into ground-skill energy compression
- snow converts setup into freeze pressure and rewards ice-type immunity

## Strategic Use

The advisor should reason about weather as a team window with setup cost,
duration, and payoff density.

For any weather-centered recommendation, ask:

- Which member starts the weather?
- How many turns of payoff does the team realistically get after setup?
- Which skills or species actually convert the weather into damage, energy
  advantage, or attrition?
- Can the opponent stall the weather timer, replace the weather, or force the
  weather starter into bad trades?
- Is a mark engine better for the same team goal because it has no weather
  timer, or is weather better because it is harder to clear?

## Known Weather Registry

This registry is provisional and suitable for B-layer reasoning. Exact engine
semantics belong in A-layer modeling.

| Weather | Status | Known Effect | Common Source Mentioned | Strategic Meaning |
|---|---|---|---|---|
| Default / no special weather | default | Baseline state after non-default weather expires. Some transcripts call this `晴天`, but this page does not canonicalize that as a named weather. | natural/default | Neutral baseline. |
| 雨天 | active weather | Water-skill damage +50%. | 落雨; possible trait/form sources | Timed water burst or pressure window. |
| 沙暴 | active weather | Ground-skill energy cost reduced; source says 地面系技能能耗减半. No end-of-round chip damage. | 沙咏, cost 7; possible trait/form sources | Timed energy-compression window. |
| 雪天 / 暴风雪 | active weather | `雪天` and `暴风雪` refer to the same in-game weather mechanism. Each round, fielded spirits gain 2 freeze layers. Each added freeze layer contributes 5% HP worth of frozen pressure, and each freeze increase checks whether the spirit now reaches exhaustion. Ice spirits are immune to freeze. | 冬至 | Timed freeze attrition and ice-type advantage window. |

## Weather Versus Marks

Weather and marks should not be collapsed.

Weather:

- applies to the field
- is public to both sides
- is mutually exclusive
- has a duration, commonly cited as 8 rounds
- returns to a default / no-special-weather state after duration ends
- can structure whole-team timing windows

Marks:

- attach to a spirit/side as positive or negative marks
- persist through switching
- are constrained by positive/negative mark slots
- can be cleared, stolen, replaced, or converted by specific tools
- can create longer-horizon pressure or resource support

This distinction matters in advice. A weather team must justify the setup turn
and payoff within the weather duration. A mark team must justify mark protection
and counterplay into clear/steal/replacement.

## Evidence

The 2026-04-04 weather tutorial uses `晴天` wording for the common/default
state and explicitly lists three active weather types: `雨天`, `沙暴`, and
`暴风雪`. It states that rain increases water skill power, winter/snow applies
freeze pressure, sandstorm reduces energy cost, weather has a round limit, and
battle logs show current weather effects and remaining rounds. This page does
not canonicalize `晴天` as a named active weather because it may only mean no
special weather in the transcript.

The 2026-04-03 speed/glossary tutorial independently states that current weather
types are `雨天`, `沙暴`, and `雪天`; weather is field-wide, public, and one at a
time; common self-started weather lasts 8 rounds; rain gives water skills 1.5x;
sandstorm halves ground-skill energy cost; snow applies 2 freeze layers each
round and ice spirits are immune to freeze.

The 2026-04-14 光合武队 source compares weather to 光合印记 and treats weather as
harder to clear but time-limited, while 光合印记 has no 8-round limit and rewards
all actions through end-of-round energy.

The current thread adds a direct user confirmation that `雪天` and `暴风雪`
should be treated as the same in-game weather mechanism rather than as two
different weather systems.

## Confidence

`provisional`.

High confidence:

- weather is global/public and distinct from marks
- only one weather exists at a time
- rain, sandstorm, and snow/blizzard are the main non-default weather types
- `雪天` and `暴风雪` are two names for the same in-game weather mechanism
- weather is time-limited and reverts to a default / no-special-weather state
  after expiry
- rain gives water-skill damage +50%
- sandstorm has no Pokemon-like end-of-round chip damage
- `沙咏` is the main sandstorm-starting skill and costs 7 energy
- each freeze layer freezes 5% HP; if current HP is below the frozen HP ratio,
  the spirit becomes exhausted; ice spirits are immune to freeze

Medium confidence:

- common duration is 8 rounds
- sandstorm halves ground-skill energy cost
- snow applies 2 freeze layers each round
- exact multi-layer step ordering when two freeze layers are added together by
  one effect

Low confidence:

- whether `晴天` is a canonical weather name or only transcript wording for no
  special weather
- exact timing order for snow/freeze application
- exact weather replacement rules

## A-Layer Boundary

This page does not define executable weather mechanics.

A-layer modeling should own:

- canonical weather names
- default weather state
- duration and replacement rules
- exact stat/damage/energy formulas
- exact timing hooks
- weather-starting skills, traits, forms, and leader effects
- weather interaction with marks, ordinary buffs/debuffs, freeze, and fainting

## Known Failure Modes

- Treating weather as a mark.
- Treating snow and freeze as the same object.
- Treating `晴天` as a canonical named weather without explicit A-layer support.
- Treating non-confirmed starter-skill names from noisy transcripts as
  canonical. `沙咏` is user-confirmed; other OCR variants are not.
- Do not import Pokemon sandstorm chip damage into Roco sandstorm.
- Recommending weather teams without checking payoff density inside the timer.
- Assuming weather is always better than marks because it is global.
- Assuming marks are always better than weather because they persist longer.

## Draft Review Questions

- Is `晴天` an actual named weather, or only transcript wording for the default
  no-special-weather state?
- Do all weather sources last 8 rounds, or only common skill-started weather?
- Can weather be overwritten directly by another weather?
- At what timing does snow/freeze apply relative to end-of-round marks, poison,
  burn, and fainting?
