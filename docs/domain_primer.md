# 洛克王国世界 PvP Domain Primer

## Purpose

本文件是 Roco 项目的内部正式版领域入门文档，用于统一产品、工程与后续 Agent 对 `洛克王国世界` PvP 相关概念的理解。

本文件的目标不是做玩家百科，而是为后续系统设计提供稳定的认知底座，特别是：

- Phase 1：队伍联防结构分析
- Phase 2：精灵角色与队伍构成分析
- Phase 3：环境与针对分析

## Scope

本文件覆盖：

- 与 PvP 分析系统相关的最小战斗框架
- 属性、联防、换入、角色、队伍风格等核心概念
- 哪些机制可纳入当前体系
- 哪些环境/Meta 判断只能作为低置信参考

## Non-goals

本文件不负责：

- 建立完整精灵图鉴
- 输出最终环境结论
- 直接作为代码实现文档替代 scoring spec
- 替代外部来源的事实核验

## Confidence Model

本文件中的内容按三档使用：

- `Confirmed for system use`
  - 可直接用于当前系统设计与实现
- `Provisional mechanism`
  - 可纳入当前体系，但后续应继续复核
- `Low-confidence meta reference`
  - 只可作为背景参考，不能直接进入 Engine 规则

## 1. Game Boundary

本项目研究对象仅为《洛克王国：世界》的 PvP 系统。

必须与以下对象区分：

- 经典页游《洛克王国》
- 宝可梦系列对战体系

允许借用宝可梦社区中较成熟的分析术语骨架，例如：

- 联防
- check / counter
- stall / balance / offense

但这些术语在本项目中只能作为分析语言的近似框架，不能默认与宝可梦语义完全等价。

## 2. PvP Minimum Mental Model

### 2.1 战斗框架

当前可纳入体系的认知：

- 对战是回合制
- 对战围绕 6 只精灵的队伍构成展开
- 胜负不是简单“全灭判定”，而与 `魔力值` 资源相关
- 技能存在能量消耗
- 技能分为攻击 / 状态 / 防御三类
- `应对` 是关键机制差异点
- 防御技能存在不能连续使用的冷却/复用限制，但该机制目前应作为规则层假设，而不是 wiki 技能字段

其中：

- `回合制`
- `技能三分类`
- `应对机制存在`
  可视为较稳的机制认知

- `魔力值具体扣除逻辑`
- `能量值完整结算细节`
- `应对的全部优先级和打断边界`
- `防御技能冷却/复用限制的完整例外表`
  目前应视为 `Provisional mechanism`

### 2.1.1 防御技能冷却假设

`Provisional mechanism`

PM 当前实战经验：

- 防御技能默认存在 `2` 回合冷却/复用限制，即不能连续两回合使用
- 存在一个特殊地系防御技能例外
- 该地系防御技能效果为减伤 `90%`
- 若该技能成功应对攻击，则冷却 `-1`

工程含义：

- `move.cooldown` 仍不能作为 wiki 结构化字段直接入 schema，因为 `{{技能信息}}` 采样未暴露稳定冷却字段
- 但 Phase 2 之后可以建模为规则层机制：`defense_move_reuse_lock`
- 特殊例外应从技能效果文本或人工校验表派生，而不是默认写死到基础 move 字段

### 2.2 为什么这对系统设计重要

这意味着系统不能简单把本作当作“宝可梦换皮”。

至少在中后期必须考虑：

- 换入节奏不只由属性决定
- 应对机制会改变招式博弈价值
- 能量资源会改变持续输出和长线消耗方式
- 部分特性或技能会直接改变资源交换

但在 Phase 1，这些机制可以先不进入计算核心，只保留为背景约束。

## 3. Attribute and Defensive Core Concepts

### 3.1 属性系统

`Confirmed for system use`

当前项目采用以下属性体系：

- 共 18 属性
- 单克制 `×2`
- 单抵抗 `×0.5`
- 无免疫

### 3.2 双属性倍率规则

`Provisional mechanism`, but accepted into the current system baseline.

当前外部研究与更新后的 `v2` 数据一致指出：

- 双重克制 `×3`
- 双重抵抗 `÷3`
- 克制与抵抗相互抵消时为 `×1`
- 双属性倍率不是简单乘法

这与我们之前的乘算假设不同，因此后续若升级 Phase 1 引擎，需要按 breaking change 处理。

### 3.3 本系加成（STAB）

`Provisional mechanism`

当前外部研究认为：

- 本系加成为 `×1.25`

该点对当前 Phase 1 影响不大，因为 Phase 1 不做实际伤害估算，但该机制应被记入领域体系，供后续 Phase 2/3 使用。

### 3.4 状态免疫

`Confirmed for system use`

当前可采用：

- 草免寄生
- 火免灼烧
- 冰免冻结
- 毒免中毒

### 3.5 联防

`Confirmed for system use` as an analytical concept.

本项目中，`联防` 定义为：

> 队伍通过成员的属性抗性、换入关系与功能互补，分担关键威胁承接压力并维持防守节奏的能力。

在 Phase 1 中，联防的计算只取其最保守的子集：

- 属性弱点分布
- 抗性覆盖
- 重复弱点
- 缺失抗性

Phase 1 明确**不等于**完整联防能力判定。

## 4. What Phase 1 Needs

### 4.1 必须纳入的概念

Phase 1 必须理解：

- 18 属性
- 属性克制与抵抗关系
- 双属性承伤规则
- 弱点集中
- 抗性覆盖
- 联防的最小定义

### 4.2 可以输出的结论

Phase 1 可以输出：

- 哪些攻击属性会对全队形成集中压力
- 哪些属性缺乏可靠抗性承接
- 哪些属性具备冗余抗性
- 队伍在属性层面的结构优势与缺口
- 按属性给出的补位方向

### 4.3 不应输出的结论

Phase 1 不应输出：

- 某只精灵是否真能安全换入
- 某只精灵是否适合担任墙、辅助手或主C
- 队伍是否适合当前环境
- 实战胜率或 matchup 预测

## 5. What Phase 2 Needs

Phase 2 需要引入的事实层数据：

- 种族值
- 技能池
- 特性
- 速度档
- 回复、控场、强化、转场、状态等功能招信息

Phase 2 才能开始回答：

- 精灵是主C还是副C
- 是联防支点还是纯功能位
- 是收割、破盾、辅助还是展开手
- 这个队伍是平衡、偏受还是偏对攻

## 6. What Phase 3 Needs

Phase 3 需要引入的环境层数据：

- 使用率
- 常见精灵
- 常见核心组合
- 常见队伍风格
- 版本变动后的趋势
- 针对关系与信息差

没有这些数据，就不能严肃地做：

- 当前环境好不好打
- 需要重点防什么
- 哪些是反环境选择
- 哪些是高频热门结构

## 7. Team Roles and Tactical Archetypes

### 7.1 可纳入体系的角色语言

`Provisional mechanism / vocabulary`

当前可以把这些词作为分析语言纳入体系：

- 主攻 / 主C
- 副攻 / 副C
- 辅助
- 功能位
- 增益手
- 减益手
- 周转位

但这些词在系统中的正式定义，应以内部 taxonomy spec 为准，而不是以外部社区口语为准。

### 7.2 可纳入体系的队伍风格语言

`Provisional mechanism / vocabulary`

当前可以把这些词作为队伍风格分析语言纳入体系：

- 受队
- 平衡
- 对攻
- 强化推进
- 换转 / 节奏型
- 天气队
- 控制流

但这些风格在本项目中的正式定义，应以内部 archetype taxonomy 为准。

## 8. Meta Content Policy

### 8.1 当前结论

`Low-confidence meta reference`

外部报告中出现的如下内容：

- 当前主流阵容
- 具体热门体系
- 某些精灵是“当前主流核心”
- 某些队伍风格“已经稳定成型”

目前只能作为低置信背景参考。

### 8.2 为什么不能直接入 Engine

原因：

- 游戏上线时间短
- 缺乏高可信使用率统计
- 社区共识仍在快速变化
- 大量结论来自攻略和经验贴，不是稳定环境样本

因此：

- 这些结论可以指导后续研究方向
- 不可以直接写进当前规则系统

## 9. Working Project Assumptions

在后续实现前，如果没有更高可信证据推翻，项目当前可暂时采用以下工作假设：

1. 属性系统为 18 属性
2. 无免疫机制
3. 双属性倍率采用 `×3 / ÷3 / 抵消为 ×1`
4. 草 / 火 / 冰 / 毒存在对应状态免疫
5. 联防在本作中是有效分析概念，但 Phase 1 只能分析其属性层
6. 环境判断暂不进入 Engine 核心

## 10. Open Questions

以下问题仍需后续继续核验：

- 魔力值是否存在更多变体规则
- 能量系统是否有更严格的上下场恢复与特殊规则
- STAB `×1.25` 是否有更高可信原始证据
- 应对机制在不同技能类型下的完整优先级边界
- 当前环境是否真的已经形成稳定 archetype

## 11. How To Use This Document

推荐使用方式：

- Phase 1 实现：可直接引用本文件的属性与联防定义
- Phase 2 设计：可引用本文件的角色与队伍风格语言，但需以内部 taxonomy spec 固化
- Phase 3 设计：只把 Meta 内容当研究方向，不当事实输入

本文件与以下文档配合使用：

- [Battle Analysis Architecture](./battle_analysis_architecture.md)
- [Role Taxonomy](../specs/role_taxonomy.md)
- [Archetype Taxonomy](../specs/archetype_taxonomy.md)
- [Scoring System](../specs/scoring_system.md)

## 12. Source Note

本文件主要依据以下两类材料整理：

- 外部研究报告：[luoke_world_pvp_domain_primer_v2.md](./research/luoke_world_pvp_domain_primer_v2.md)
- 外部更新数据：[luoke_world_type_database_v2.json](../data/reference/luoke_world_type_database_v2.json)

这些材料已被审查并重新分层使用：

- 机制内容：可暂纳入体系
- 环境内容：仅供低置信参考
