# Roco V2 开发状态汇报

Date: 2026-05-06
For: zero-context successor agent

## 0. 角色分工

| 角色 | 职责 |
|---|---|
| Tamerael (PM) | 产品决策、游戏知识、V1/V2 方向 |
| Codex | V1 发版（mobile/desktop/API 工程） |
| Clé | V2 架构 + 执行：P10h 实验、D 层、Meta Graph |

Codex 忙 V1 发版期间，Clé 接管了原本属于 Codex 的实验执行和 Meta Graph 建设。

## 1. V2 要解决什么问题

V1 是 ABC-grounded Agent chat——用户问对战问题，Agent 用 Battle Dex 结构化事实（A）、wiki 机制知识（B）、governance/persona 安全边界（C）生成回答。V1 发版不含 D 层和 Meta Graph。

V2 的目标是让 Agent 的推理质量从"查图鉴给建议"升级到"接近高分玩家的判断"。两条腿：
- **D 层（P10h）**：专家示范案例，教 Agent "怎么想"
- **Meta Graph（V2）**：精灵配置 + 关系图谱，为 D 层提供检索基座（"有什么"）

## 2. P10h 消融实验：三次方案迭代

### 目标

验证 A/B/D 各知识层是否有效、哪里造成负迁移、工具门控是否工作。3 case × 5 level × 3 repeat = 45 calls。

### 方案 1：Flat prompt（废弃）

在 prompt 层手工拼装知识材料，模拟不同 level 的 Agent。用 `sample` 字段截断数据（每物种 8 个技能）。

**失败原因**：泄露链结构性——case_id→gounding 头部→反例物种名，每修一个泄露暴露下一个。`sample` 措辞鼓励模型编造不在列表中的技能。

### 方案 2：Runtime Agent via API hack（废弃）

想通过 `X-Roco-Tool-Allowlist` header 在生产 API 上叠加实验门控。

**失败原因**：生产 Agent 架构（ToolRouter 路由分类、output_validator 强制工具调用、Agent 单例缓存）围绕"Agent 自主决定"设计，不兼容"实验者控制"。L0 条件下 validator 强制要求工具调用 → 必然异常。

### 方案 3：Standalone Harness Agent（采用，已完成）

Harness 创建自己的 pydantic-ai Agent 实例，按 level 选择性注册工具。生产代码零改动。

**共享**：Battle Dex SQLite、Constitution、LLM config
**不共享**：ToolRouter、output_validator、Agent 缓存、session 管理

实现：`tools/p10h_agent_tools.py`（薄 wrapper 直调 Repository）、`tools/p10h_agent_factory.py`（按 level 创建 Agent）、`tools/p10h_runtime_agent_harness.py`（主逻辑），共 ~300 行。

### 实验结果

45/45 calls 完成，零报错（2/45 主回答被截断 <500 字符，what-if 完整）。

| Level | 工具 | 关键发现 |
|---|---|---|
| L0 | 无 | 事实编造严重（棋齐垒→岩系，寒音蛇→冰系） |
| L1 | A 层 | 类型/种族值/技能名全部正确。最大单层 delta |
| L2 | A+B | 增加机制知识（星陨印记循环、陨落特性） |
| L3-exact | A+B+D 同源 | 显式引用 D 层方法，推理结构化 |
| L3-transfer | A+B+D 异源 | 方法论迁移成功，不显式引用但结构一致 |

**结论**：工具门控工作正常，A/B/D 层各有可辨识的边际贡献。实验诊断任务完成。

### 已知问题

- Constitution §3 反例用了 Case A 的物种（裘卡+疫病吐息）→ 所有 level 轻度污染。如需重跑应先替换为非 case 物种。
- 速度瓶颈：单 call 180-760s。Agent 逐个调工具 + thinking per round。生产部署前需批量工具和预加载优化。
- N=3 不够统计学显著性，只能出方向性结论。

## 3. Agent Constitution（已重写）

`specs/roco_agent_constitution.md` — 从 9 条并列规则重写为自包含原则体系：

```
§2 事实锚定（A+B 层是唯一事实源）
  → §3 推理链（展示从事实到结论的过程）
    → §4 不确定性（事实不够时说不知道）
      → §5 边界（不可以做什么——前三者的负面空间）
        → §6 表达（Persona 只能改语气不能改事实）
```

每个原则配 → 好 / → 差 反例。~65 行，无多余指令。

## 4. Meta Graph Spec（已定稿）

`specs/v2_battle_meta_graph_spec.md`

### 核心理念

- **Obsidian 式组织**：每个 species_set 是一张自包含的"卡"。卡上写配置数据 + `related_to`（和谁有什么关系、为什么）。扫描所有卡 → edge index 自动生成。图 emergent。
- **核心节点只有一种**：species_set（某精灵在特定 meta 中的一套具体配置）。关系/角色/标签不是节点。
- **两座 Graph**：H-Graph（V2.0，社区视频人工录入）+ S-Graph（V2.1，Agent 推理生成，硬门控——Agent 判断力跨阈值后才激活）
- **边的重要性**：`description` 是最重要的字段——"为什么"比"是什么"值钱。

### 两座 Graph 架构

| | H-Graph (Human) | S-Graph (Shadow) |
|---|---|---|
| 数据来源 | 社区配置讲解/评级视频 | Agent 推理 |
| Source type | `community_video` + `battle_dex` | `agent_synthesis`（保留占位） |
| Confidence 基线 | `observed`（单来源可追溯即可） | `inferred` |
| 审核 | PM 看过→reviewed | PM spot-check→reviewed |
| 激活 | V2.0 起始终激活 | V2.1 硬门控（Agent 判断力≈高玩） |
| MVP 规模 | 15-25 张卡，30-125 条关系 | 0（V2.1 的事） |

### 升级路径

S-Graph 条目 → PM spot-check 确认 → `graph_origin` 改为 human → migrate 到 H-Graph。单向。

## 5. 当前状态 & 下一步

### 已完成

- [x] P10h 消融实验（Layer 1 诊断完成）
- [x] Runtime Agent harness（诊断工具，已归档）
- [x] Agent Constitution v2（已定稿）
- [x] Meta Graph spec v3（已定稿，双 Graph + Obsidian 路线）
- [x] Case label registry（diagnostic / repair_source / heldout_eval 三级标签）
- [x] Case answer key full-roster 修复（3 case 全部修复）
- [x] Case label registry（防止训练集污染）
- [x] 实验计划三次迭代全记录在 project_log

### 待定

- [ ] Meta Graph H-Graph 第一批精灵清单
- [ ] PM 选定社区视频素材
- [ ] Clé 提取 species_set 配置写入 graph
- [ ] Constitution §3 反例修复（替换为非 case 物种）
- [ ] Meta Graph PM 决策：D4（Graph 进不进 public repo）、D5（V2 启动时机）
- [ ] Layer 2 增量建设流程定义
- [ ] Layer 3 冻结评测 heldout case 准备

### 关键决策（不要推翻）

- 不手写启发式规则。D 层走 expert demonstration + retrieval
- Tag quality > embedding。30-50 case 规模下 tag + BM25/lexical 足够
- 实验 harness 是诊断工具，用完即弃。Layer 2 直接用 Runtime Agent
- S-Graph 激活硬门控：Agent 判断力未达标前不进 runtime
- Meta Graph 核心节点只有 species_set。不引入额外节点类型
- 生产代码零改动。Harness 独立于生产系统

## 6. 关键文件索引

| 领域 | 文件 |
|---|---|
| 实验计划（最终版） | `artifacts/p10h_prebattle_ablation/runtime_agent_experiment_plan_2026_05_04.md` |
| 实验 Harness | `tools/p10h_agent_tools.py` `tools/p10h_agent_factory.py` `tools/p10h_runtime_agent_harness.py` |
| 实验输出 | `artifacts/p10h_prebattle_ablation/outputs/` (45 JSON) |
| 盲评包 | `artifacts/p10h_prebattle_ablation/blind_review/blind_review_packet.json` |
| 全部输出汇总 | `artifacts/p10h_prebattle_ablation/all_outputs.txt` |
| Case 标签注册 | `artifacts/p10h_prebattle_ablation/case_label_registry.yaml` |
| Case Answer Key | `artifacts/p10h_prebattle_ablation/inputs/*.yaml` (3 case, 已修复) |
| Agent Constitution | `specs/roco_agent_constitution.md` |
| Meta Graph Spec | `specs/v2_battle_meta_graph_spec.md` |
| 结构审计 Prompt | `tools/p10h_structural_audit_prompt.md` |
| Clé 配置 | `CLAUDE.md` |
| 项目日志 | `log/project_log.md` |
