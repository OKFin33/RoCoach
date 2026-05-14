# P10h Structural Audit Prompt

执行机械结构审计。不需要项目上下文、不需要游戏知识、不需要了解 P10h 架构。
只需按此 checklist 逐项检查，输出 pass/fail 清单。

## 输入

审计时读取以下文件：

- `artifacts/p10h_prebattle_ablation/inputs/*.yaml`（全部 case 输入文件）
- `artifacts/p10h_prebattle_ablation/d_layer_selection_manifest.yaml`
- `specs/p10h_prebattle_ablation_experiment_plan.md`（仅 case map 部分）

## 检查项

### A. Roster 一致性

对每个 case YAML：

- [ ] A1. `answer_key` 中直接引用的所有物种 `display_name`，在 `our_team` 或 `opponent_team` 中是否存在？
  - 搜索 pattern：answer_key 全文中的物种中文名
  - 特别检查 `archetype_recognition`、`d1`、`d2`、`d3`、`conditional_knowledge`、`what_if_questions`
  - 排除：`domain_notes`（术语修正）、`source_span`（源文件引用）、`orphaned_fragments`
- [ ] A2. `d_layer_selection_manifest.yaml` 中引用的 `demo_id`，其对应的 D 材料文件是否存在？
- [ ] A3. case 的 `case_label`（Case A/B/C）、`case_order`、`case_id` 在三个 case 间是否唯一且无冲突？

### B. 旧 roster 残留检测

对每个 case YAML：

- [ ] B1. Case C 的 answer_key 中是否不含 `落陨星兔`？（应在 `orphaned_fragments` 中）
- [ ] B2. Case C 的 answer_key 中是否不含旧对手成员引用（如旧版 贝古斯 在对手方的引用）？
- [ ] B3. 扫描全部三个 answer_key，提取所有物种名 → 和 `our_team` / `opponent_team` 对比 → 是否存在不在 roster 中的物种名？

### C. Prompt 泄露检测

- [ ] C1. 搜索 `prompts/` 目录下所有 `.md` 文件 → 是否包含 `case_id:`、`source_ref:`、`case_label:` 等内部标识符？
  - 这些标识符不应出现在模型可见文本中
  - 如果 `prompts/` 目录不存在或为空（尚未 rebuild），标注"N/A — prompts not yet rebuilt"
- [ ] C2. 搜索 `grounding_packs/` 目录下所有 `.md` 文件 → 同上检查

### D. Answer Key 结构完整性

对每个 case YAML，检查以下 section 是否存在且非空：

- [ ] D1. `archetype_recognition`：含 `what_expert_knew` 列表（≥1 项）+ `layer_dependency`
- [ ] D2. `d1_attention_order`：含 `steps` 列表（≥2 项），每项有 `order`、`focus`、`why`、`layer`
- [ ] D3. `d2_activated_priors`：含 `priors` 列表（≥2 项），每项有 `id`、`activation`、`layer`
- [ ] D4. `d3_reasoning_chain`：含 `steps` 列表（≥3 项），每项有 `step`、`action`、`reasoning`、`layer`
- [ ] D5. `conditional_knowledge`：含 `items` 列表（≥1 项）
- [ ] D6. `evaluation_checklist`：含 `d1_alignment`（≥1 check）、`d2_alignment`（≥1 check）、`negative_checks`（≥3 checks）
- [ ] D7. 每个 check 有 `weight` 或 `severity` 字段
- [ ] D8. 每个 `if_fail` 描述足够具体（不是仅"检查 X"或"可能有问题"——应指向具体组件或 trigger 条件）
- [ ] D9. `what_if_questions`：≥2 个问题，每个有 `question`、`purpose`、`key_points`（≥2 点）

### E. Source span 有效性

- [ ] E1. 所有 `source_span` 引用的文件路径是否可解析？
  - 检查格式：`filename:line` 或 `filename:line-line`
  - 检查文件名是否在 repo 中存在
- [ ] E2. 标注为 `PM review` 或非源文稿来源的项（无 `source_span`）——确认它们有替代标注（如 `source_note`）

### F. 跨 case 一致性

- [ ] F1. 同一物种（如 `圣羽翼王`）在不同 case 的 answer_key 中描述是否有明显矛盾？
  - 检查：技能、角色定位、特性
  - 非矛盾的差异（如不同 case 中同一物种使用不同的技能变体/配置）不需要标记
  - 只有"A case 说 X 是强化手，C case 说 X 从不强化"这类直接矛盾才标记
- [ ] F2. `case_label` 分配是否和 `specs/p10h_prebattle_ablation_experiment_plan.md` 中的 stable case map 一致？

### G. `if_fail` 诊断钩子质量

- [ ] G1. 统计每个 case 的 `if_fail` 字段中不含具体组件/trigger 名称的条目数
  - 举例："此原语未激活" → 不合格（太模糊）
  - 举例："此原语未激活→B 层或 D3 demo 缺此队伍引擎描述" → 合格（指向具体组件）
  - 模糊条目 ≥2 个 → 标记 warning

### H. 实验设计完整性

- [ ] H1. 三个 case + 5 个 level（L0-L3）+ N 个 repeat 的排列是否等于 run_order 中的条目数？
  - 从 `run_order.json` 读取实际条目
  - 期望：3 case × 5 level × 3 repeat = 45 条目
- [ ] H2. `d_layer_selection_manifest.yaml` 是否覆盖了全部三个 case 的 L3-exact 和 L3-transfer？
- [ ] H3. 检查 `harness.py` 是否存在且可 import（dry-run：`python -c "import tools.p10h_prebattle_ablation_harness"`）

### I. 实验设计审计（不需要游戏知识，需要实验/评测设计经验）

以下检查不需要知道游戏内容对错——只需要判断实验设计本身是否站得住。

#### I-1. 输入信息充分性

对每个 case：

- [ ] I1a. `visible_context.visibility_rule` 是否明确声明？
   - 如果声明了 `both_teams_visible_hidden_sets` 或等效，则两队的全部成员都应列在 roster 中
   - 如果 roster 不完整（如只有 3 只而非 6 只），则评测测量的不是"分析能力"而是"信息不足下的推理能力"——这可能是设计意图，但必须是显式意图而非疏忽
- [ ] I1b. 每个 case 的 `our_team` 和 `opponent_team` 成员数是否一致？
   - 如果三个 case 中有的 6v6、有的 3v4，需要确认这是有意为之而非疏忽
- [ ] I1c. 输入中是否包含回答所需的全部信息？
   - 对照 answer_key 的 `d1_attention_order`——如果 answer_key 提到某个关键判断依赖某信息（如"裘卡是否携带疫病吐息"），该信息是否在输入中可获取？
   - 如果关键信息不可获取，则 answer_key 在评测一个模型无法知道的变量 → 评分无效

#### I-2. 评测目标与测量手段的对齐

- [ ] I2a. 实验声称测量"A/B/D 层对推理的边际贡献"，但 L0-L3 之间的差异是否**仅**来自知识层的增减？
   - 检查 L0-L3 的 prompt 模板：不同 level 的 prompt 长度、结构、指令措辞是否一致？
   - 如果 L3 的 prompt 比 L0 长 3 倍且含"请专家级分析"等引导语，则 L3-L0 的差值不仅来自知识层，还来自 prompt 本身的暗示效果
   - 这不一定错（有些实验就是测"加了材料之后的表现"），但需在评分报告中显式声明此混淆
- [ ] I2b. L3-exact 的 demo 和 answer key 是否共享同一 source？
   - 如果 `d_layer_selection_manifest.yaml` 中 L3-exact 的 `demo_ids` 来自和 answer key 相同的 source_ref → L3-exact 分数可能反映的是"复述源材料"而非"推理能力"
   - 标记 warning 即可：这不是错误（设计上 L3-exact 就是上界），但下游报告必须标注此泄漏风险
- [ ] I2c. 每个 what-if question 是否能用 case 中提供的信息回答？
   - 对照 `what_if_questions[].key_points` ——这些关键点依赖的信息是否在 case 输入或基础游戏知识中可获取？
   - 如果某个 what-if 的 key_point 依赖"对手后排配置"，但输入是明牌 6v6（无后排隐藏），检查是否逻辑自洽

#### I-3. 评分协议的可靠性

- [ ] I3a. 评估 checklist 中的 scoring 是否**可复现**？
   - 检查：两个不同 judge（或同一 judge 跑两次）对同一模型输出的评分是否应相近？
   - 指标：`if_fail` 中的判断标准是否足够具体——"此 prior 未激活"需要 judge 自行定义什么叫"激活"→ 不可靠；"是否在答案中出现了'首发'相关的排除过程"→ 可检查
   - Warning：如果一个 case 的 checklist 中有 ≥3 个 `if_fail` 的触发标准模糊（需要 judge 自行理解"激活""对齐"等概念），标记 warning
- [ ] I3b. 正向 checks 和负向 checks 的比例是否合理？
   - 如果某个 case 只有正向 checks（"是否做了 X"）没有负向（"是否不应该做 Y"）→ 模型可以靠多说、全说来刷分
   - Warning：任何 case 的 `negative_checks` 少于 3 条

#### I-4. Case 多样性

- [ ] I4a. 三个 case 是否测试了不同的认知维度？
   - 如果三个 case 都是"选首发" → 评测覆盖面窄，结论不能泛化到"prebattle 推理能力"
   - 如果三个 case 分别测试：archetype 识别、资源引擎建模、对策条件判断 → 覆盖面好
   - 对照每个 case 的 `archetype_recognition.description` 和 `d3_reasoning_chain` 的核心推理类型，判断是否同质化
- [ ] I4b. 三个 case 的 `our_team` archetype 是否不同？
   - 如果三个 case 己方都是同一种队伍 → 评测只覆盖了一个视角
   - 当前：Case A 翼王毒、Case B 传统毒、Case C 雷暴翼王——如果 Case A 和 Case B 己方重叠度过高（都是毒队），标记注意

#### I-5. 结论范围的约束

- [ ] I5a. 实验计划（`specs/p10h_prebattle_ablation_experiment_plan.md` 或等效文件）是否声明了能从实验结果中得出的结论范围？
   - 必须声明：此实验是 3 case × 5 level 的 **诊断性**消融，不是能力评测。N=3 不足以声称"Agent 的 prebattle 能力达到 X 分水平"。
- [ ] I5b. 是否有明确的"此实验不能得出什么结论"的声明？
   - 至少应声明：不能泛化到所有 matchup、不能泛化到所有队伍类型、不能等价于人类评分
   - 如果缺失，标记 warning

#### I-6. 关键：检查非泛化案例特征

- [ ] I6a. 每个 case 的核心判断是否过度耦合到 source_ref 的特异性？
   - 如果 answer_key 的核心推理步骤引用了 source 视频中的特定回合、特定玩家的特定操作 → 这测的是"模型是否复述了源素材"，而非"模型是否具备可泛化的推理结构"
   - 标记方法：检查 `d3_reasoning_chain[].reasoning` 中是否出现了只能在 source 视频中知道的信息（如"主播第 X 回合选择了 Y"、"对手误操作导致"）→ Flag
- [ ] I6b. 如果移除 source 视频的特定语境，answer_key 的判断结构是否仍然适用于该 matchup 的其他实例？
   - 不要求审计者判断"对不对"——只要求识别 answer_key 中的推理步骤是否引用了 source 特有的、不可泛化的细节
   - 例如：`source_span` 指向"实战第 5 回合的某个具体操作" → 标记"可能不可泛化"

## 输出格式

```
## P10h Audit Report
Date: [日期]

### Summary
- Structural checks (A-H): Total [N], Pass [N], Fail [N], Warning [N]
- Design checks (I): Total [N], Pass [N], Fail [N], Warning [N]

### Blocking Failures
[列出所有 structural fail (A-H)，格式：check_id - case - 描述]

### Design Warnings
[列出所有 design fail/warning (I)，格式：check_id - case - 描述 + 为什么这是问题]

### Per-case breakdown
[同上，A-H 和 I 分别列出]

### Verdict
- All structural pass + no design failures → `READY`
- Structural failures → `BLOCKED`
- Only design warnings → `READY WITH NOTES — review warnings before experiment`
```
