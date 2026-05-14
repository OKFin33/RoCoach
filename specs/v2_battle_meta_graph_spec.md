# V2 Battle Meta Graph Spec

Status: draft — dual-graph architecture
Author: Clé
Date: 2026-05-03

## 0. 本 spec 的事实边界

**本 spec 是架构设计文档，不是游戏数据文档。**

文档中的示例分两类：

- `[例/已验证]`：来自 P10h answer key 或 repo 已有文件。内容经人工确认，可引用。
- `[例/示意]`：仅用于说明 schema 结构。游戏内容（数值、性格、技能组合、关系判断）是编的，**不可引用、不可录入 Graph、不可用于 prompt 组装**。

如果你看到一个示意例子看起来"对"——那是碰巧。如果你看到一个示意例子看起来"错"——它确实错。

本 spec 的作者不玩这个游戏。所有具体对战知识来自 P10h case 文件和 Battle Dex。
超出这两者的细节均为脑补。

已验证的事实清单（当前 repo 内可确认）：
- 物种正名 & alias：水母→琉璃水母、星光师/金光师→星光狮、化电城铁→画间沉铁兽、球卡→裘卡、修罗→厉毒修萝
- 琉璃水母技能含：泡沫幻影、双联脉冲、雷暴
- 双联脉冲：造成魔伤，迸发：本技能使用次数+1
- 雷暴：造成魔伤，迸发：本技能获得所有生效过的迸发，每获得1种，本技能能耗+1，威力+10
- 闪电鳗鱼 lead value 含泡沫幻影 scouting/rotation、双联脉冲 laying reusable burst for 雷暴
- 圆号鱼是常见 lead
- Case A: prebattle_wingking_poison_vs_snake_balance
- Case B: prebattle_poison_vs_starfall（己方平衡毒视角）
- Case C: prebattle_thunder_wingking_fast_balance

以上之外的细节——性格选择、速度线数值、具体 matchup 结果、技能搭配合理性——本 spec 均不声称知道。

---

## 1. 为什么 V2 才做，为什么 V1 不做

### V1 的边界

V1 发版目标是 **ABC 层 grounded Agent chat**——用 Battle Dex 结构化事实（A）、
curated wiki/机制知识（B）、governance/persona 安全边界（C）提供对战分析。
V1 release claim 不含"高分段战术直觉"，不含"专家示范推理"，不含"环境图谱"。
把 Meta Graph 塞进 V1 会引入新的 failure mode 和审核负担，增加发版不确定性。

### 为什么 P10h 实验跑完之前不设计 Graph schema

[证据] P10h 的 Layer 1 消融实验（45 calls）还没跑。在不知道 D1/D2/D3 子层贡献模式的情况下，
提前设计 Graph schema 会 over-fit 到设计者的直觉，而不是实验暴露的真实缺口。

### V2 的时机

- P10h Layer 1 消融实验跑完，D1/D2/D3 子层贡献模式有初步结论
- P10h Layer 2 增量建设跑过至少一轮
- V1 Alpha 已发版

### 两座 Graph 的递进节奏

Meta Graph 的成长分两个阶段，对应两座 Graph：

**V2.0：Human-seeded Graph（H-Graph）**
- 数据来源：社区配置讲解/评级主题视频。PM 扒结论，手写录入。
- 特征：不对称（热门精灵关系丰富，冷门稀缺）、单视角（up 主视角）、天然向高梯度配置倾斜。
- 质量：60-80 分。够用，但知道自己哪 20-40 分是瞎的。
- 审核：单维护者 review（PM 看过觉得合理）。

**V2.1：Agent Shadow Graph（S-Graph）**
- 前提：Agent 判断力跨过阈值——H-Graph 把 Agent 的判断力拉到"看起来像一个高分玩家"的水准。
- 数据来源：Agent 自己对冷门 matchup 的推理结果。`source_type: agent_synthesis`。
- 特征：补 H-Graph 的结构性缺口——冷门物种配置、冷门 counterplay、不对称关系的另一侧视角。
- 质量：取决于 Agent 当时的实际能力。confidence 从 `inferred` 起步，经 PM spot-check 后可按升级路径 promote 到 H-Graph。
- 激活门控：**硬门控。** Agent 判断力未跨阈值 → S-Graph 不进 runtime retrieval。

**两座 Graph 共享同一套 schema。** species_set、related_to、edge index、speed index 的格式完全一致。
区别在 `graph_origin` 字段、confidence 基线、审核流程、激活条件。

### V1 现在保留的钩子

1. **名称正名 & alias overlay** `[例/已验证]`
   - 水母 → 琉璃水母、星光师/金光师 → 星光狮、
     化电城铁 → 画间沉铁兽、球卡 → 裘卡、修罗 → 厉毒修萝
   - 放在 A 层 Battle Dex 的 alias 字段，不是独立 Graph 文件

2. **P10h expert demo 的结构化元数据**
   - 每个 demo case 保留涉及的 species_set 清单、技能、速度/资源阈值、关系描述
   - 关系先作为 tags / evidence notes，不进 runtime graph

3. **V1 runtime 不依赖未完成的 Graph**

---

## 2. 两座 Graph 的架构定义

### 总览

```
              ┌──────────────────┐
              │   Meta Graph     │
              │                  │
              │  ┌────────────┐  │
              │  │  H-Graph   │  │  ← V2.0 MVP
              │  │  community │  │
              │  │  _video    │  │
              │  └────────────┘  │
              │        │         │
              │        │ promote │  ← PM spot-check
              │        ▼         │
              │  ┌────────────┐  │
              │  │  S-Graph   │  │  ← V2.1 (gated)
              │  │  agent_    │  │
              │  │  synthesis │  │
              │  └────────────┘  │
              │                  │
              └──────────────────┘
```

### H-Graph（Human-seeded Graph）

| 维度 | 定义 |
|---|---|
| 数据来源 | 社区视频（配置讲解/评级主题）。PM 看视频，手写录入 species_set 和 related_to。 |
| 主要 source_type | `community_video`、`battle_dex`（基础数据） |
| confidence 基线 | `observed`（单一来源但来源可追溯、高分玩家明确声称） |
| 审核流程 | PM 看过觉得合理 → `reviewed`。两步：`unreviewed → reviewed` |
| 人口学特征 | 热门倾斜、高梯度倾斜、单视角（up 主视角）。冷门配置和冷门 counterplay 会缺。 |
| 激活 | V2.0 起始终激活 |
| MVP 规模 | 15-25 张卡，每卡 2-5 条 related_to，总计 30-125 条关系 |

### S-Graph（Agent Shadow Graph）

| 维度 | 定义 |
|---|---|
| 数据来源 | Agent 对冷门/未覆盖 matchup 的推理结果 |
| 主要 source_type | `agent_synthesis`（占位，MVP 不使用） |
| confidence 基线 | `inferred` 起步。Agent 推理 + PM spot-check → 可升级到 `observed` + promote 到 H-Graph |
| 审核流程 | 三步：`unreviewed → reviewed`（需 PM spot-check 确认 Agent 判断合理） |
| 人口学特征 | 补 H-Graph 缺口——冷门物种配置、冷门 counterplay、不对称关系另一侧视角、特殊条件 matchup |
| 激活 | **硬门控。** Agent 判断力跨过阈值后，PM 手动开启 `shadow_graph_enabled`。阈值之前不进 runtime。 |
| MVP 规模 | 0（V2.1 的事） |

### 激活门控：Shadow Graph 的前置条件

S-Graph 的激活是**硬门控**——不是"差不多就行"。

```
Shadow Graph 激活条件：
1. H-Graph MVP 已完成并接入 runtime
2. Agent + H-Graph 的判断力经 PM 评估达到"看起来像一个高分玩家"的水准
3. PM 手动设置 shadow_graph_enabled = true
```

条件 2 的评估方式不在本 spec 范围内（届时由 PM 自行设计 blind test / A/B 对比等）。
本 spec 只规定：**没有这个评估和手动开启，S-Graph 数据不进 runtime retrieval。**

### 升级路径：Shadow → Human

```
S-Graph 条目（source_type: agent_synthesis, confidence: inferred）
  → PM spot-check 确认判断合理
  → source_type 改为 expert_review（或保持 agent_synthesis + 标注 PM-reviewed）
  → confidence 升级到 observed
  → graph_origin 改为 human
  → 迁移到 H-Graph
```

升级是单向的。H-Graph 条目不会降级到 S-Graph。
（过期条目走 `review_status: superseded`，不涉及跨 Graph 迁移。）

---

## 3. species_set 节点 Schema（两座 Graph 共享）

### 设计原则

核心节点只有一种：**species_set**。一个 species_set 表示某个精灵在特定对战环境中的
**一套具体配置**，不是泛泛的精灵百科条目。

同一精灵的不同配置（不同性格、技能格、个体值分配）是不同的 species_set。
关系是在配置之间，不是在物种之间。

### Obsidian 式组织

每个 species_set 是一张自包含的"卡"。卡上写清楚自己的配置数据，也写清楚
**自己和谁有关系、什么关系、为什么**。关系不是独立实体——它是卡上的一个 section。

Graph 不是"建"出来的——扫描所有卡，汇总 `related_to` 字段，边索引自动生成。

### Schema

```yaml
# ──────────────────────────────────────────
# 所有具体游戏数据均为 [例/示意]
# 不可引用、不可录入、不可用于 prompt
# ──────────────────────────────────────────

id: "species_set/example_species/variant_2026s1"    # [例/示意]
canonical_species_id: "example_species"              # Battle Dex 引用
canonical_species_name: "示例精灵"                    # [例/示意]
source_aliases:
  - "社区简称A"                                       # [例/示意]
moves:
  - "技能甲"                                          # [例/示意]
  - "技能乙"
  - "技能丙"
  - "技能丁"
nature: "示例性格"                                    # [例/示意]
individual_value_bonuses:
  speed: 31
ability: "示例特性"                                    # [例/示意]
stat_profile:
  speed: 999                                          # [例/示意]
speed_tier: 999
role_labels:
  - "example_role"                                    # [例/示意]
team_context:
  common_partners:
    - "species_set/another_example/variant_2026s1"    # [例/示意]
  archetype_tags:
    - "example_archetype"                             # [例/示意]
meta_snapshot: "2026-s1"

# ══════════════════════════════════════════
# Graph 来源标记 — 两座 Graph 的核心区分
# ══════════════════════════════════════════
graph_origin: "human"                                 # human | shadow

source_refs:
  - source_type: "community_video"                    # [例/示意]
    source_ref: "https://example.com/video/123"
    claim: "up 主在此视频中描述的此配置"
    date: "2026-04-15"
    reviewer: "pm_name"
    review_date: "2026-05-01"
    notes: "天梯前100分段出现"

confidence: "observed"                                # observed | inferred | speculative
review_status: "reviewed"                             # unreviewed | reviewed | disputed | superseded
notes: >
  设计笔记、待验证事项。

# ══════════════════════════════════════════
# 核心：关系直接写在这张卡里
# ══════════════════════════════════════════

related_to:
  - target_species_set_id: "species_set/target_example/variant_2026s1"
    edge_type: "synergy"
    description: >
      描述关系，重点是"为什么"。例如：因为速度线匹配、技能互补。  # [例/示意]
    reasoning_quality: "full_chain"
    conditions:
      - "关系成立的前提条件"
    resource_state:
      some_resource: "资源状态说明"
    confidence: "observed"
    evidence_refs:
      - source_type: "community_video"
        source_ref: "https://example.com/video/123?t=300"
        claim: "up 主明确说明的关系判断"
        reasoning_available: true
        reasoning_summary: "up 主解释了因为 X 技能压制 Y 的启动回合"
        date: "2026-04-15"
    tags:
      - "example_tag"

  - target_species_set_id: "species_set/another_target/variant_2026s1"
    edge_type: "threat"
    description: >
      up 主原话："水刃打贝古斯很疼，基本稳吃"                        # [例/示意]
    reasoning_quality: "claim_only"
    conditions: []
    confidence: "inferred"
    evidence_refs:
      - source_type: "community_video"
        source_ref: "https://example.com/video/456?t=120"
        claim: "视频中 up 主声称了威胁关系但未展开解释原因"
        reasoning_available: false
        date: "2026-04-20"
    tags: []
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | 全局唯一，`species_set/{species}/{variant}_{meta}` |
| `canonical_species_id` | string | 是 | Battle Dex 物种 ID |
| `canonical_species_name` | string | 是 | 中文正名 |
| `source_aliases` | list | 否 | 社区简称、ASR 常错名 |
| `moves` | list | 是 | 技能名（中文正名） |
| `nature` | string | 否 | 性格 |
| `individual_value_bonuses` | map | 否 | 关键个体值 |
| `ability` | string | 是 | 特性 |
| `stat_profile` | map | 否 | 满级实际数值，speed 必填 |
| `speed_tier` | int | 否 | 速度值，speed index 索引键 |
| `role_labels` | list | 是 | 受控词汇，见附录 A |
| `team_context.common_partners` | list | 否 | 常见搭配的 species_set ID |
| `team_context.archetype_tags` | list | 否 | 阵容类型标签 |
| `meta_snapshot` | string | 是 | 版本标识，如 `2026-s1` |
| **`graph_origin`** | enum | 是 | **`human` 或 `shadow`。此卡属于哪座 Graph。** |
| `source_refs` | list | 是 | 此配置本身的来源 |
| `confidence` | enum | 是 | observed / inferred / speculative |
| `review_status` | enum | 是 | unreviewed / reviewed / disputed / superseded |
| `notes` | string | 否 | 设计笔记、待验证事项 |
| **`related_to`** | list | 否 | **此配置与其他 species_set 的关系。** |

### `related_to` 条目字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `target_species_set_id` | string | 是 | 关系指向的目标配置 |
| `edge_type` | enum | 是 | 受控词汇 |
| `description` | string | 是 | **核心。** 自然语言描述"为什么"。MVP 可接受 up 主原话直接引用 |
| `reasoning_quality` | enum | 是 | **推理完整度。** `full_chain`（解释了因果链）、`partial_chain`（部分解释）、`claim_only`（只有结论）。`claim_only` 的关系 confidence 应降级 |
| `conditions` | list | 否 | 关系成立的前提 |
| `resource_state` | map | 否 | 关键资源状态 |
| `confidence` | enum | 是 | observed / inferred / speculative |
| `evidence_refs` | list | 是 | 此关系的来源 |
| `tags` | list | 否 | 过滤/检索辅助标签 |

### `evidence_refs` 条目字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `source_type` | enum | 是 | 来源类型 |
| `source_ref` | string | 是 | 来源引用 |
| `claim` | string | 是 | 来源中的具体声明 |
| `reasoning_available` | bool | 是 | **up 主有没有解释"为什么"。false → confidence 应降级。** |
| `reasoning_summary` | string | 否 | reasoning_available=true 时填写。up 主给出的因果链摘要 |
| `date` | string | 是 | 来源日期 |
| `reviewer` | string | 否 | 审核人 |
| `review_date` | string | 否 | 审核日期 |
| `notes` | string | 否 | 补充说明 |

### Edge 类型（受控词汇）

```
synergy          - 此配置常与 target 搭配
threat           - 此配置对 target 构成威胁
counterplay      - 此配置有处理 target 的手段
bait_punish      - 此配置诱导 target 做 X，然后反惩罚
pivot_path       - 此配置可以通过换位把局面转给 target
killline         - 此配置在特定条件下能收掉 target
resource_race    - 此配置与 target 的资源竞速
mindgame         - 此配置与 target 的博弈/反博弈关系
volatility       - 关系高度依赖具体条件，不稳定
```

### `description` 为什么是最重要的字段

"克制"没有信息量。"因为速度线压制 + 技能甲 scout 剥夺 target 的强化窗口"才有。
`description` 是 LLM 推理时真正需要的东西——不是关系标签，是标签背后的因果链。

MVP 阶段：当 up 主只给了结论没给因果链时，`description` 可以直接引用 up 主原话，
同时标记 `reasoning_quality: claim_only`。LLM 检索时可以区别对待"有完整推理"和
"只有结论"的关系。

### 关系是主张，主张天然有视角

`related_to` 写在此配置的卡上，表示**此配置的主张**。
target 的卡上可能根本没提这个关系，甚至可能写相反的判断。
Graph 不做"统一视角"的仲裁——它保留多视角，让 LLM 知道"这件事有争议"。

H-Graph 的视角偏差尤其明显：视频 up 主天然偏向"什么强""什么好用"，
卡池向高梯度配置倾斜。S-Graph 的目标之一就是补这种不对称。

### 受控词汇：role_labels

[直觉] 角色标签应该从实际对战分析中生长出来，不应该预先穷举。初始集合：

```
speed_control       - 速度控制（高速压制、先手权争夺）
wall                - 属性盾/肉盾
pivot               - 轮转中转点
setup_core          - 强化核心
killline_converter  - 斩杀线转换者
weather_setter      - 天气手
hazard_setter       - 场地/印记布置
cleric              - 解状态/恢复
wallbreaker         - 破盾手
revenge_killer      - 复仇收割
stall_anchor        - 消耗锚点
sacrifice_piece     - 牺牲位（战术性送掉）
```

---

## 4. 关系如何形成图谱：Edge Index（自动派生，两座 Graph 共享）

### 设计原则

Graph 不是手建的。扫描所有 species_set 文件的 `related_to` 字段后自动汇总生成 Edge Index。
H-Graph 和 S-Graph 的边汇总到同一份 index，通过 `graph_origin` 区分。

### Edge Index Schema（自动生成，不手写）

```yaml
# 文件：edge_index.yaml
# ⚠ 此文件由脚本从 species_set 的 related_to 字段自动生成
# 不要手动编辑

edges:
  - id: "edge/auto/0001"
    source_species_set_id: "species_set/example/variant_2026s1"
    target_species_set_id: "species_set/target_example/variant_2026s1"
    edge_type: "synergy"
    description: "..."                    # 来自 source 的 related_to
    conditions: []
    confidence: "observed"
    evidence_refs: [...]
    tags: [...]
    review_status: "reviewed"
    meta_snapshot: "2026-s1"
    # ═══════════════════════════════════════
    # Graph 来源 + 自动派生元数据
    # ═══════════════════════════════════════
    graph_origin: "human"                 # 来自 source species_set 的 graph_origin
    claimed_by_source_only: true          # target 的 related_to 中未提及 source
    has_counter_claim: false
    counter_claim_id: null

  - id: "edge/auto/0042"
    source_species_set_id: "species_set/shadow_example/variant_2026s1"
    target_species_set_id: "species_set/some_target/variant_2026s1"
    edge_type: "counterplay"
    graph_origin: "shadow"                # 来自 S-Graph
    confidence: "inferred"
    claimed_by_source_only: true
    has_counter_claim: false
```

### 自动派生字段

| 字段 | 说明 |
|---|---|
| `graph_origin` | 来自 source species_set 的 `graph_origin`，标注此边来自哪座 Graph |
| `claimed_by_source_only` | target 的 `related_to` 中未提及 source。单向主张。 |
| `has_counter_claim` | target 声称了矛盾的关系 |
| `counter_claim_id` | 指向矛盾 edge 的 ID |

### 双向关系 vs 单向主张

A 和 B 互相在 `related_to` 里提到对方 → edge_index 有两条边。
可以互补、矛盾、或不对称（A 说 threat、B 没提 A）。都是正常现象。

---

## 5. Speed Index Schema（两座 Graph 共享）

### 设计原则

速度线是 Meta Graph 中最适合结构化的维度。
Speed index 的数据**全部来自 species_set 卡的 `speed_tier` 字段**——不独立维护速度数据。
同一精灵的不同配置（极速版 vs 力度版）是不同的 species_set，各有独立的 `speed_tier`。
查询"此配置快过哪些常见威胁"= 查表 O(1)，从 speed_tiers 的有序列表中直接定位。

H-Graph 和 S-Graph 的物种共用同一份速度索引。

### Schema

```yaml
# 文件：speed_index.yaml
# 从 species_set 的 speed_tier 字段自动汇总生成

# ──────────────────────────────────────────
# 所有数值均为 [例/示意]
# ──────────────────────────────────────────

speed_tiers:
  999:                                                 # [例/示意]
    - species_set_id: "species_set/fast_example/max_speed_2026s1"
      species_name: "高速精灵示例"
      graph_origin: "human"
      nature: "加速度性格"
      config_note: "极速配置（加速性格 + 31 速个体）"
  888:                                                 # [例/示意]
    - species_set_id: "species_set/mid_example/max_speed_2026s1"
      species_name: "中速精灵示例"
      graph_origin: "human"
      nature: "加速度性格"
      config_note: "极速配置"
  810:                                                 # [例/示意]
    - species_set_id: "species_set/mid_example/power_2026s1"
      species_name: "中速精灵示例"
      graph_origin: "human"
      nature: "加物攻性格"
      config_note: "力度配置（加攻性格 + 31 速个体），比极速版慢 78"

speed_relations:
  - id: "speed_rel/auto/0001"
    faster: "species_set/fast_example/max_speed_2026s1"
    slower: "species_set/mid_example/max_speed_2026s1"
    relation: "outspeeds"
    margin: 111                                        # [例/示意]
    nature_variants_known: true
    note: "双方都是极速配置"

  - id: "speed_rel/auto/0002"
    faster: "species_set/mid_example/max_speed_2026s1"
    slower: "species_set/mid_example/power_2026s1"
    relation: "outspeeds"
    margin: 78                                         # [例/示意]
    nature_variants_known: true
    note: "同精灵的极速 vs 力度——不同性格的 speed_tier 差异"
```

### 查询支持

```
1. get_speed_tier(species_set_id) -> speed_value
2. does_outspeed(A_species_set_id, B_species_set_id) -> bool + margin
3. get_faster_than(species_set_id) -> [all species_sets with lower speed_tier]
4. get_slower_than(species_set_id) -> [all species_sets with higher speed_tier]
```

查询 3/4 直接从 `speed_tiers` 有序列表查表 O(1)。不需要遍历所有卡。

---

## 6. Evidence & Review（分 Graph 的流程）

### 设计原则

Meta Graph 的价值取决于可信度。两座 Graph 的可信度基线不同，
审核流程也不同，但 evidence entry 的格式统一。

### 来源类型

```
battle_dex        - 结构化游戏数据（物种、技能、数值）          → 高置信度
community_video   - 社区对战解说视频（H-Graph 主力来源）        → 中置信度，需 review
community_post    - 社区论坛/社交媒体的策略讨论                 → 低置信度，需多方验证
expert_review     - 项目维护者人工审阅                          → 高置信度
p10h_case         - 来自 P10h expert demonstration case         → 中高置信度
manual_test       - 游戏内实测                                   → 高置信度
agent_synthesis   - Agent 推理生成（S-Graph 主力来源，MVP 保留不用）→ 低置信度，需 PM spot-check
```

### MVP 阶段实际使用的来源

H-Graph 主力来源只有两个：
- `community_video`：PM 扒配置讲解/评级视频，手写录入
- `battle_dex`：物种基础数据、技能、数值

`agent_synthesis` 在 V2.1（S-Graph 激活后）才使用。
其他 source_type 保留占位。

### Evidence entry（统一格式）

```yaml
source_type: "community_video"
source_ref: "https://example.com/video/456?t=120"
claim: "该来源中与当前声明相关的具体内容"
date: "2026-04-15"
reviewer: "pm_name"
review_date: "2026-05-01"
notes: "补充说明"
```

### 置信度体系

```
observed     - H-Graph: 单一来源但来源可追溯、高分玩家明确声称    → runtime 可用
               S-Graph: 经 PM spot-check 确认的 Agent 推理          → runtime 可用
inferred     - 从其他已知事实推断，未经独立验证                    → runtime 可用但标注不确定性
speculative  - 推测、未验证观点                                    → 不在 runtime 注入，仅保留供后续验证
```

H-Graph 的 `observed` bar 比传统标准低（不再要求多人独立验证）——
单维护者、零社区的现实下，一个天梯分段可见的高分玩家在视频里明确说了，就算 `observed`。

### Review 状态机

#### H-Graph（两步）
```
unreviewed → reviewed
```
MVP 阶段不需要 `disputed` 和 `superseded`——没有多人力去 dispute。
过期内容直接标注 `superseded` 并移出活跃检索范围（保留在文件中，不删除）。

#### S-Graph（三步，V2.1 启用）
```
unreviewed → reviewed（需 PM spot-check）
```
S-Graph 的 `reviewed` 需要 PM 确认 Agent 判断合理性。
没有 PM spot-check 的 S-Graph 条目保持 `unreviewed`，不进 runtime。

### 升级路径：Shadow → Human

```
S-Graph 条目（source_type: agent_synthesis, confidence: inferred, review_status: reviewed）
  → PM 二次确认（可以是 spot-check 的子集）
  → source_type 改为 expert_review
  → confidence 升级到 observed
  → graph_origin 改为 human
  → 迁移到 H-Graph（本质上是卡文件里改一个字段）
```

升级是单向的。H-Graph 条目不降级到 S-Graph。

### 时效性

- 每个 species_set 和每条关系都有 `meta_snapshot` 字段。
- Runtime 检索时按当前 meta_snapshot 过滤。
- 旧 snapshot 的数据保留在文件中（可审计，不做历史查询）。

---

## 7. 从 P10h Casebank 迁移到 Meta Graph

### 关系定位

P10h case 是素材，Meta Graph 卡是产品。人工提取，不自动转换。
迁移产物全部进入 H-Graph（`graph_origin: human`）。

### 迁移流程（单 case）

```
1. 读 case — 理解 matchup、判断链、关键推理步骤

2. 提取 species_set
   - 识别涉及的每个精灵配置
   - 已有 → 补充 source_refs
   - 没有 → 创建新卡（graph_origin: human, source_refs 指向此 case）

3. 提取关系 → 写入 related_to
   - 从推理链中识别此配置指向其他配置的关系
   - description 提取"为什么"，不是复述结论
   - evidence_refs 指向此 case（source_type: p10h_case）

4. 提取速度/资源阈值
   - 速度对比 → 更新 speed_tier（如需要）
   - 能量/印记/资源条件 → 写入 conditions / resource_state

5. Review → 标记 review_status: reviewed

6. 注册 → 卡写入 species_sets/，case registry 标记"已迁移"
   → 下次重建 index 时自动包含
```

### 迁移优先级

优先：涉及当前 meta 主流配置、推理链中"为什么"清晰完整、已经过 review 的 case。
低优先：仅涉及冷门配置、推理链模糊的 case。

### 预期产出

每个 P10h case 预计产出：2-6 个 species_set、3-10 条 related_to 条目。

---

## 8. MVP 范围

### V2.0 MVP：H-Graph only

**数据规模**
- 1 个 meta snapshot（当前赛季/版本）
- 15-25 个 species_set（全部 `graph_origin: human`）
- 每卡 2-5 条 related_to（总计 30-125 条关系）
- Speed index 覆盖全部
- 每条数据有至少一个 evidence ref

**文件组织**
```
artifacts/v2_meta_graph/
  species_sets/                          # 唯一的数据源
    example_species_variant_2026s1.yaml  # 每张卡自包含，含 related_to
    another_species_variant_2026s1.yaml
    ...
  edge_index.yaml                        # 自动生成
  speed_index.yaml                       # 自动生成
  evidence_log.yaml                      # 自动生成
  graph_registry.yaml                    # 手动维护：species_set ID 清单 + graph_origin + case 迁移状态
```

**检索能力**
- 按 species_set ID 直接查找
- 按 tag 过滤
- 从 species_set 获取所有 `related_to`
- 从 edge_index 查询入边（谁提到了此配置）
- Speed index 快慢查询
- BM25 对 description 做关键词检索

**工具脚本**
- `tools/v2_generate_edge_index.py`
- `tools/v2_generate_speed_index.py`
- `tools/v2_validate_graph.py`：检查孤立引用、必填字段完整性

### V2.0 MVP 不做

- 不建数据库（YAML 文件）
- 不做 S-Graph（V2.1 的事）
- 不做 agent_synthesis 来源（保留占位，不可使用）
- 不做历史 meta snapshot 对比
- 不做图可视化
- 不做查询语言
- 不把 speed index 做成完整伤害计算器
- 不做用户可见的 Graph 浏览 UI
- 不做自动关系推断（LLM 辅助标记可以，最终录入必须 PM review）

### V2.1：S-Graph 激活

S-Graph 的 scope 不在此 spec 中详细定义——届时根据 Agent 实际能力和 H-Graph 覆盖缺口再定。
本 spec 只定义：schema 共享、激活门控、升级路径、confidence 基线。

---

## 9. 不该做的过度设计

### 不要引入额外的节点类型

以下不应该成为节点：team_archetype、move、ability、item、player、tournament。
如果未来需要独立节点，先从 `related_to[].conditions` 长出来。
**加节点类型是不可逆的架构决策。**

### 不要过度形式化

- conditions 不要写成规则引擎。自然语言，人读、LLM 读。
- 不给 confidence 加自动计算。人工标注。
- 不设计查询语言。Python dict + filter + BM25 足够。

### 不要自动生成

- 不让 LLM 从视频转写自动提取关系。PM 手动录入。
- （V2.1 的 `agent_synthesis` 是 Agent 推理自己的判断，不是从视频自动提取——这是两回事。）
- 不自动泛化：一个配置的关系 ≠ 整个物种的关系。

### 不要提前激活 Shadow Graph

- 在 Agent 判断力未达标前，S-Graph 条目不进 runtime。
- S-Graph 的价值取决于 Agent 判断质量。Agent 不行 → S-Graph 是幻觉套壳。
- **宁愿 H-Graph 覆盖不全，也不要 S-Graph 污染检索结果。**

### 不要追求 Obsidian 的完整复刻

- 不做 wikilink 语法
- 不做实时图谱渲染
- 不做反向链接面板（edge_index 的 `claimed_by_source_only` 已提供此信息）

### 不要提前优化

- YAML 文件 + Python dict 完全够
- tag + BM25 检索，不加 embedding 除非明显不够
- 不设计缓存层

### 不要暴露给用户（目前）

- Meta Graph 是完全内部的 Agent 知识表示
- 不在 UI 展示 graph、关系、confidence
- Graph 内容通过 Agent 的自然语言回答间接呈现

---

## 10. 后续如何接入 Roco Agent Runtime

### 接入层级

```
用户提问
  ↓
A 层 Battle Dex: 物种正名、基础数据解析
  ↓
Meta Graph: 检索 H-Graph + (if enabled) S-Graph → 组装知识 block
  ↓
D 层 (V2): 专家推理模式 → 判断链合成
  ↓
B 层: wiki/机制知识补充
  ↓
C 层: governance + persona 边界
  ↓
Agent 回答
```

### Runtime 检索流程

```
1. 用户提问 → A 层正名，解析涉及的物种 canonical_species_id
2. 查找 Meta Graph 中对应 canonical_species_id 的所有 species_set：
   a. graph_origin = "human" 的卡（始终检索）
   b. graph_origin = "shadow" 的卡（仅当 shadow_graph_enabled = true）
3. 对每个匹配的卡：
   a. 读取配置摘要（moves, nature, speed_tier, role_labels）
   b. 读取 related_to（此配置声称的关系）
   c. 从 edge_index 查询入边（谁声称了和此配置的关系）
4. 按 tag + meta_snapshot + confidence 过滤
5. 检索 speed_index 中涉及配置之间的速度对比
6. 组装 context block 注入 D 层 / Agent prompt
```

### 双 Graph 的 Context Block 标注

当 S-Graph 激活时，context block 需要标注每条知识的来源，
让 LLM 能区别对待 H-Graph（人类高分玩家主张）和 S-Graph（Agent 先前推理）。

```text
[Meta Graph Context]
来源: [H] = 社区高分玩家 | [S] = Agent 先前推理

涉及的配置:
- [H] 示例精灵A (示例性格, speed=999): role标签             [例/示意]
- [S] 冷门精灵B (示例性格, speed=777): role标签             [例/示意]

关联关系:
- [H] 示例精灵A → threat → 目标精灵C: 关系描述和原因         [例/示意]
  置信度: observed
- [S] 冷门精灵B → counterplay → 示例精灵A: 关系描述和原因    [例/示意]
  置信度: inferred
```

### 接入时机

- V1：不接。
- V2.0：H-Graph 作为只读检索源。
- V2.1：S-Graph 激活后，双 Graph 检索合并。

---

## 11. 需要 PM 人工审阅的决策点

### D1. Meta snapshot 粒度

当前用 `2026-s1`（赛季级）。备选：月级、年级。

**需要决策**：严格按赛季还是按实际 meta 变化灵活调整？

### D2. Review 人力和 bar（已基本定案）

单维护者。H-Graph 审核 = PM 看过觉得合理 → `reviewed`。
不需要多人签字，不需要独立验证。

**确认即可**：这个 bar 你接受？

### D3. 社区视频的 `observed` 标准（已基本定案）

H-Graph 的 `observed` = 一个天梯分段可见的高分玩家在视频中明确声称。
不再要求多源交叉验证（MVP 阶段不现实）。

**确认即可**：这个 bar 你接受？

### D4. Graph 文件是否进 public repo

H-Graph 数据含主观判断。公开 = 别人会引用、challenge、fork。

**需要决策**：进 public repo + disclaimer？还是保持私有/本地？

### D5. V2 启动时机

**需要决策**：P10h Layer 1 跑完就开干 H-Graph MVP，还是等 Layer 2 第一轮？

### D6. Shadow Graph 激活阈值

**需要决策**：什么构成"Agent 判断力 ≈ 高分玩家"？
- 由你主观评估？
- 还是一套 blind test（Agent vs 人类判断，你盲评）？
- 通过的最低标准是什么？

这个不需要现在定（V2.1 的事），但需要记着。

### D7. Shadow → Human 升级标准

**需要决策**：S-Graph 条目什么条件可以 promote 到 H-Graph？
- PM 每个条目都 spot-check？
- 还是抽查通过率达到某个阈值后批量 promote？

也不需要现在定，但需要在 S-Graph 激活前有答案。

### D8. `related_to` 的最小信息门槛

**确认即可**：`description` 和至少一个 `evidence_ref` 是否强制？

---

## 附录 A：受控词汇汇总

### role_labels
```
speed_control, wall, pivot, setup_core, killline_converter,
weather_setter, hazard_setter, cleric, wallbreaker, revenge_killer,
stall_anchor, sacrifice_piece, role_tbd
```

### edge_types
```
synergy, threat, counterplay, bait_punish, pivot_path,
killline, resource_race, mindgame, volatility
```

### graph_origin
```
human, shadow
```

### confidence
```
observed, inferred, speculative
```

### review_status
```
unreviewed, reviewed, disputed, superseded
```

### source_types
```
battle_dex, community_video, community_post, expert_review,
p10h_case, manual_test, agent_synthesis
```

注：`community_post`、`manual_test`、`agent_synthesis` 在 MVP 阶段为占位，
实际使用仅 `community_video` + `battle_dex`。

---

## 附录 B：和 P10h 的边界总表

| 维度 | P10h (D 层) | Meta Graph (V2) |
|---|---|---|
| 存储内容 | 专家推理案例（完整推理链） | 配置卡 + 卡上的关系（可复用知识单元） |
| 粒度 | 一个 case = 一个 matchup 的完整判断 | 一个 related_to 条目 = 两个配置之间的单一关系主张 |
| 组织形式 | 案例文件（narrative + checklist + answer key） | 自包含卡 + 自动派生的 edge/speed index |
| 检索方式 | 按 case 标签检索 | 按 species_set + edge_type + tag 检索 |
| 更新方式 | 新增 case、修 answer key | 新增/更新卡 → 重建 index |
| 关系存储 | case 内 narrative 描述 | 嵌在 species_set 卡的 related_to 字段 |
| Graph 体系 | 无（素材定位） | H-Graph（社区视频）+ S-Graph（Agent 推理，V2.1） |
| 在 runtime 的角色 | 推理模式参考（"怎么想"） | 知识检索基座（"有什么"） |
| MVP 规模 | 已有 3 case + D1/D2/D3 材料 | V2.0: 15-25 卡（H-Graph only） |
