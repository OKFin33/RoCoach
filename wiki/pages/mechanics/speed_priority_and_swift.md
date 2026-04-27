---
title: "Speed, Priority, And Swift"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md"
  - "wiki/raw/source_notes/2026-04-02_bilibili_18_type_mechanism_detailed_extraction.md"
  - "wiki/cache/速度线:词条 0403/NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt"
  - "docs/research/luoke_world_pvp_domain_primer_v2.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
  - "data/reference/luoke_world_type_database_v2.json"
last_reviewed: "2026-04-21"
reviewed_by: "mechanism_guard_followup"
persona_free: true
---

# Speed, Priority, And Swift

## Claim

`速度`、`先手`、`迅捷` 不能混成一个概念。

当前 reviewed 结论只允许保守表述为：

- 常规行动顺序应先看先手层级，再看实际速度，最后才可能落到随机或同速处理。
- `迅捷` 不是“永远先手”的同义词，更像一种与特定入场 / 触发条件绑定的自动释放机制。
- 含有 `迅捷` 的技能文本，不能在没有 reviewed 页支撑时直接被解释成完整、确定的时序规则。

## Strategic Use

对 advisor 来说，这页的价值不是输出一套伪精确时间轴，而是避免把速度控制、先手层级、迅捷触发混说。

推荐或分析时至少要区分：

- 这是依赖常规速度线取胜，还是依赖先手层级抢行动权
- 这是主动出手技能，还是与换上场时机绑定的 `迅捷`
- 如果用户问的是队伍角色，是否只是需要知道它“有入场压制 / 反打节奏价值”，而不是需要你假装知道全部结算细节

## Evidence

当前证据来自三类来源：

- reviewed 过的领域 primer，确认 Roco 存在独立于普通速度比较的机制词，如 `迅捷`
- raw source notes 与速度线整理材料，反复把 `先手`、`速度`、`迅捷` 分开讨论
- A 层 battle-dex 中已经有能力 / 技能文本直接出现 `迅捷`

可直接确认的 A 层例子包括：

- 某些特性文本写有 `1号位技能获得迅捷`
- 某些技能文本直接写有 `迅捷`
- 某些技能会引用“已释放过的迅捷技能”

这些都足以证明：`迅捷` 是真实机制词，不是语言噪声；但它的完整执行规则仍不能只靠零散文本硬推。

## Confidence

`provisional`。

高置信：

- `先手`、`速度`、`迅捷` 应视为不同层面的机制信号
- `迅捷` 与普通速度高低不是一回事
- `迅捷` 相关解释必须显式保留不确定性

中低置信，仍待后续 reviewed：

- `迅捷` 是否严格要求主动换上场才触发
- 精灵倒下后的被动替换是否触发 `迅捷`
- 是否存在能量不足时不能触发的约束
- “一次只自动释放一个迅捷技能”是否已足够被当前材料确认
- `迅捷` 与敌方行动、应对、防御、打断的精确先后顺序

## A-Layer Boundary

这页定义的是 B 层 advisor doctrine，不是战斗引擎结算器。

如果未来要把 `速度 / 先手 / 迅捷` 做成 A 层可执行字段，应拆成类似：

```text
priority_tier
speed_modifier
swift_trigger
swift_requires_active_switch
swift_energy_gate
swift_limit_per_entry
timing_uncertainty
```

在这些字段进入 A 层之前，Agent 只能把 `迅捷` 视作“重要机制信号”，不能把自己的猜测包装成 confirmed rule。

## Known Failure Modes

- 把 `迅捷` 直接说成“绝对先手”
- 把任何速度提升都说成等于 `先手`
- 忽略入场条件，默认 `迅捷` 永远生效
- 在没有 reviewed 证据时，擅自断言死亡替换也会触发 `迅捷`
- 用跨游戏直觉替代 Roco 自身机制边界

## Draft Review Questions

- `迅捷` 的最小可确认触发条件到底是什么？
- 死亡替换、主动换人、强制脱离，这三种入场是否共享同一触发逻辑？
- 能量不足时，`迅捷` 技能是跳过、失败，还是存在特殊结算？
- 如果同时存在先手层级和 `迅捷`，时序比较应如何落地到 A 层？
