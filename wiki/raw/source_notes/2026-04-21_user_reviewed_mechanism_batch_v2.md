# Source Note: User-Reviewed Mechanism Batch V2

```yaml
source_id: user_reviewed_mechanism_batch_v2_2026_04_21
title: "User-reviewed mechanism convergence batch v2"
source_type: user_confirmation
published_at: 2026-04-21
collected_at: 2026-04-21
origin_platform: codex_thread
can_commit: summary_only
sensitivity: public_summary
source_class:
  - battle_mechanics_confirmation
  - mechanism_review_batch
confidence: user_confirmed
volatility:
  mechanics_core: medium
status: confirmed_by_user_pending_page_split
persona_risk: false
cross_game_risk: low
```

## Confirmed Statements

- `传动` 游戏内描述为：回合开始时，带有“传动X”的技能会向下移动 X 个位置，该效果可叠加。
- 当前版本中，`蓄力` 技能的通用工作定义可统一处理；当前版本所有带有蓄力词条的技能均为 `3` 能耗。
- `奉献` 当前版本已确认的触发来源只有 `虫群` 与 `啃咬`。
- `萌化` 每层退化一阶，直到最初形态；基础形态相关属性会回到退化形态，当前生命值不随最大生命值修正自动重算。
- `灼烧` 正常结算为每层 `2%` 最大生命值的火系伤害，受属性克制关系影响；`充分燃烧` 触发的额外灼烧伤害同样按该伤害属性理解。
- 与魔力值直接相关的特性至少包括：
  - `不朽` 所关联的复活场景
  - 卡瓦重：力竭时魔力损耗 `-1`
  - 帕尔链条：击败敌方精灵时敌方额外损失 `1` 点魔力；被敌方精灵击败时自己额外损失 `1` 点魔力
  - 圣羽翼王：被敌方精灵击败时自己额外损失 `1` 点魔力
- `冻结` 在每一次增加层数时都会检查是否达到力竭条件。
- `寄生` 当前版本为：扣除对方 `6%` 最大生命值并回复给自己，且不是草系伤害。
- `连击` 上限按当前通用 buff 层级理解为 `99` 层。
- `打断` 效果会在技能描述里显式写出；当前经验下应视为 `应对` 的一种特殊额外效果，且目前观察中主要由攻击技能携带。

## Boundary

- 本 note 以“当前线上版本可用”为边界。
- 它允许被写入 reviewed provisional 页面。
- 它不自动等价于 A-layer executable rule until structured modeling is added.
