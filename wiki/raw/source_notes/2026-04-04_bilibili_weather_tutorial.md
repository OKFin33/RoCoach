---
source_id: "2026-04-04_bilibili_weather_tutorial"
source_type: "bilibili_video_transcript"
published_date: "2026-04-04"
ingested_date: "2026-04-20"
status: "processed"
confidence: "provisional"
volatility: "shifting"
can_commit: "summary_only"
persona_free: true
raw_inputs:
  - "wiki/cache/天气速成0404/NoteGPT_《洛克王国：世界》魔法学院新生速成，玩转天气机制！.txt"
supporting_inputs:
  - "wiki/cache/速度线:词条 0403/NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt"
  - "wiki/cache/光合武队0414/NoteGPT_《光合武队怎么玩？一期视频讲清它的底层逻辑》.txt"
human_corrections:
  - "沙暴主要触发技能确认名为沙咏，能耗 7"
  - "沙暴天气没有类似宝可梦沙暴的回合结束伤害机制"
  - "雨天使水系技能伤害提升 50%"
  - "每层冻结冻结 5% 生命值；若精灵当前生命值低于冻结比例，则力竭；冰系精灵免疫冻结"
---

# 2026-04-04 Weather Tutorial

## Source Context

The 2026-04-04 beginner tutorial is a short dedicated weather-system video. It
describes default weather, three non-default weather states, basic effects,
example weather-starting skills, duration, and battle-log visibility.

The 2026-04-03 speed/glossary tutorial independently supports the global,
single-weather, 8-round framing and gives specific effect values.

## Weather Claims

- The transcript uses `晴天` wording for the common/default state, but this
  should not be treated as a canonical weather name unless later A-layer sources
  explicitly confirm it. Use `default / no special weather` in doctrine.
- Battle can also have `雨天`, `沙暴`, and `暴风雪` / `雪天`.
- Current thread correction on 2026-04-21: `雪天` and `暴风雪` should be treated
  as the same in-game weather mechanism rather than two separate weather names.
- Weather is a full-field effect, visible to both sides.
- Only one weather can exist at a time.
- Weather has a round duration; the 2026-04-03 source says common self-started
  weather lasts 8 rounds.
- After the duration ends, weather returns to the default / no-special-weather
  state. The transcript calls this `晴天`, but that wording is not canonicalized.
- Battle logs can show current weather effect and remaining rounds.

## Weather Effect Claims

| Weather | Effect Claim | Source State |
|---|---|---|
| 雨天 | Water-skill damage +50%. | user-confirmed plus multi-source candidate |
| 沙暴 | Ground-skill energy cost is reduced; 2026-04-03 source says 地面系技能能耗减半. It does not deal end-of-round chip damage like Pokemon sandstorm. | user-confirmed plus multi-source candidate |
| 雪天 / 暴风雪 | Same in-game weather mechanism. Each round, fielded spirits gain 2 freeze layers. Each freeze layer freezes 5% HP; if current HP is below the frozen HP ratio, the spirit becomes exhausted. Ice spirits are immune to freeze. | user-confirmed plus multi-source candidate |

## Weather-Starting Sources

| Weather | Starting Source Mentioned | Review State |
|---|---|---|
| 雨天 | `落雨` skill | plausible |
| 雪天 / 暴风雪 | `冬至` skill | plausible |
| 沙暴 | `沙咏`, energy cost 7 | user-confirmed |

The listed starters are examples, not exhaustive sources. Traits, forms, or
leader effects may also create weather.

## Strategic Interpretation

Weather creates a public, time-limited team window. It is easier for both sides
to see than marks, and it cannot be treated as a hidden long-horizon attachment.

Current source materials suggest these strategic differences:

- rain supports water damage windows
- sandstorm supports ground-skill energy compression
- snow supports freeze pressure and ice-type defensive immunity value
- weather has a duration constraint, commonly cited as 8 rounds
- weather appears harder to clear than marks, but can be time-limited and may be
  replaced by another weather

## Review Notes

- Exact duration and replacement rules need A-layer confirmation.
- Exact timing of snow/freeze application needs A-layer confirmation.
- Do not canonicalize `晴天` as a named weather. It may be only the transcript's
  wording for no special weather, and future game updates could introduce a
  distinct sunny/fire-grass style weather.
- Weather should be represented separately from marks because it is global,
  public, mutually exclusive, and time-limited.
