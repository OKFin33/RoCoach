# Roco (RoCoach)

洛克王国世界 PvP 对战顾问。技术栈：Python FastAPI + PydanticAI + SQLite + Electron/React/Vite 桌面端 + Expo RN 移动端。

## 当前入口
- 新 Agent 先读 `docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md`。
- 这份 context map 覆盖旧 `ROCO_V1_ALPHA_HANDOFF_2026_05_03.md` 和 `ROCO_V2_STATUS_2026_05_06.md` 中关于 V1/V2 边界的旧判断。
- 当前 V1 正式发版前置：单 Agent Chat + A/B/C + Meta Graph v0.1 + D-layer v0.1。S-Graph 仍然后置。

## 仓库
- `src/api/` — FastAPI 后端，contracts.py + runtime_headers.py
- `src/advisor/` — 对战顾问核心：battle_dex.py（SQLite 仓储）、retrieval.py、runtime.py（PydanticAI native）
- `src/agent_core/` — orchestrator.py + persona_registry.py
- `src/engine/` — 确定性对战引擎和结构分析器
- `src/knowledge/` — 知识检索、置信度、合约
- `apps/mobile/` — Expo React Native MVP
- `apps/desktop/` — Electron + Vite 桌面端
- `docs/specs/` — Agent 宪法、数据契约、实验计划、Meta Graph
- `docs/` — 架构书、研究、设计素材、治理、变更日志
- `wiki/` — B 层对战知识 + 编译管线
- `data/` — 游戏结构化数据
- `tools/` — 消融实验 harness、审计 prompt
- `artifacts/` — 实验输入输出

## 架构约束

1. **Engine-first, Agent-enabled**：确定性 Engine 是上位约束，LLM 在 Engine 输出上做解释。不在 LLM 内做计算。SQLite battle-dex > 模型推测。
2. **A/B/Persona 三层分离**：A=结构化事实（SQLite），B=机制知识（检索文档），Persona=风格叠加。Persona 只影响表达，不改结论、分数、推荐。
3. **Meta Graph（A/B 之间）**：species_set 配置卡 + 关系图谱。Agent 在 A 层事实之上、B 层机制之前查询此层，获取"这只精灵实战中怎么配、跟谁配合、被谁克制"。H-Graph（社区视频提取）始终激活，S-Graph（Agent 推理）硬门控。
4. **事实只能来自知识库**：不从 LLM 训练数据推测游戏事实。信息不足时追问或拒答，不编造。
5. **Content guard 在输出层**：仅在 prompt 层设 guard 不够——P10h 实验证明答案会泄漏内部实验标签。输出后做检查再返回用户。
6. **消融验证产品假设**：产品决策走分层消融实验验证，不靠主观感受。Blind packet + content guard + reveal→backlog 管线。

## 硬约束
- 禁止打印真实 API key。key 只走请求头 `X-Roco-Provider-Key`，不进 body/URL。
- 数据同步：`src/api/contracts.py` ↔ `apps/mobile/src/api/types.ts`
- Header 同步：`src/api/runtime_headers.py` ↔ `apps/mobile/src/runtime/runtimeSettings.ts`
- 不恢复已删除页面（SettingsScreen/SpeciesSearchScreen/TeamEditorScreen）
- 纸纹用 `paper_shell.png` + `paper_outline.png`，不用 SVG

## 命令
```bash
.venv/bin/pip install -r requirements.txt    # 安装依赖
bash scripts/run_local_api.sh                  # 启动 API
bash scripts/run_mobile.sh                     # 启动移动端
bash scripts/run_desktop_dev.sh                # 启动桌面端
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests # 全量测试
cd apps/mobile && npm run typecheck                 # 类型检查

# Meta Graph 管线
PYTHONPATH=.:src .venv/bin/python -m tools.v2_validate_graph --strict      # 校验图谱
PYTHONPATH=.:src .venv/bin/python tools/v2_generate_edge_index.py          # 生成边索引
PYTHONPATH=.:src .venv/bin/python tools/v2_generate_speed_index.py         # 生成速度线索引
# 加卡/改卡后：改 YAML → 更新 registry → 跑校验 → 重建两个索引

# 消融实验
.venv/bin/python tools/p10h_prebattle_ablation_harness.py build --output-dir artifacts/p10h_prebattle_ablation --repeats 3
.venv/bin/python tools/p10h_prebattle_ablation_harness.py run --output-dir artifacts/p10h_prebattle_ablation --repeats 3 --max-calls N
```

## Git
分支：`feature/<描述>` / `fix/<描述>`。提交前跑类型检查和核心测试。不推送未测试代码。

## Provider
密钥文件：`~/.config/roco-advisor/env`（600 权限）。当前默认 `deepseek-v4-flash`，thinking disabled。

## Wiki Bridge
wiki：`/Users/okfin3/Documents/Obsidian`
项目 slug：`roco`
域标签：`agent-architecture, fact-governance, product-methodology, game-ai`

项目侧 agent memory 是本地 `.agent/`，默认不入 git。

启动时：
1. 读 `.agent/bridge-brief.md`（如有）。
2. 如果没有 `.agent/`，或需要刷新项目上下文，加载 `/Users/okfin3/Documents/Obsidian/skills/wiki-bridge/SKILL.md` 执行 init/refresh。

开发中：遇到架构决策、结构性踩坑、候选跨项目 insight，追加 `.agent/wiki-queue.md`。

Legacy：`.claude/wiki-queue.md`、`.claude/dev-log.md`、`.claude/bridge-brief.md` 只作为旧 Claude Code 工作流的迁移来源；新 Wiki Bridge 写入统一走 `.agent/`。

## Dev Log
每次 session 后可追加 `.agent/dev-log.md`：
```
### YYYY-MM-DD | [简述]
- 做了什么：[要点]
- 关键判断：[如有]
- 踩坑：[如有]
```

## Agent 行为准则

这是 PM 主导项目。代码由 Agent 写，产品判断由 Zab 定。

1. 遇到产品判断，先陈述假设和选项。不确定就问，别自己默默挑。
2. 最少代码解决问题。不加没要求的功能。不为用一次的代码建抽象。
3. 手术式改动——只碰需要的，不重构没坏的。遵守已有代码风格。
4. 模糊任务 → 验收标准 → 实现 → 验证。多步骤先列计划。
5. 你不在填空，你在做判断。模糊需求不是猜——列选项、tradeoff、推荐，等 Zab 确认再写。
