# Roco (RoCoach)

洛克王国世界 PvP 对战顾问。技术栈：Python FastAPI + PydanticAI + SQLite + Electron/React/Vite 桌面端 + Expo RN 移动端。

## 仓库
- `api/` — FastAPI 后端，contracts.py + runtime_headers.py
- `advisor/` — 对战顾问核心：battle_dex.py（SQLite 仓储）、retrieval.py、runtime.py（PydanticAI native）
- `agent_core/` — orchestrator.py + persona_registry.py
- `battle_engine/` — 确定性对战引擎和结构分析器
- `mobile/` — Expo React Native MVP
- `desktop/` — Electron + Vite 桌面端
- `specs/` — Agent 宪法、数据契约、实验计划、Meta Graph
- `tools/` — 消融实验 harness、审计 prompt
- `artifacts/` — 实验输入输出

## 架构约束

1. **Engine-first, Agent-enabled**：确定性 Engine 是上位约束，LLM 在 Engine 输出上做解释。不在 LLM 内做计算。SQLite battle-dex > 模型推测。
2. **A/B/Persona 三层分离**：A=结构化事实（SQLite），B=机制知识（检索文档），Persona=风格叠加。Persona 只影响表达，不改结论、分数、推荐。
3. **事实只能来自知识库**：不从 LLM 训练数据推测游戏事实。信息不足时追问或拒答，不编造。
4. **Content guard 在输出层**：仅在 prompt 层设 guard 不够——P10h 实验证明答案会泄漏内部实验标签。输出后做检查再返回用户。
5. **消融验证产品假设**：产品决策走分层消融实验验证，不靠主观感受。Blind packet + content guard + reveal→backlog 管线。

## 硬约束
- 禁止打印真实 API key。key 只走请求头 `X-Roco-Provider-Key`，不进 body/URL。
- 数据同步：`api/contracts.py` ↔ `mobile/src/api/types.ts`
- Header 同步：`api/runtime_headers.py` ↔ `mobile/src/runtime/runtimeSettings.ts`
- 不恢复已删除页面（SettingsScreen/SpeciesSearchScreen/TeamEditorScreen）
- 纸纹用 `paper_shell.png` + `paper_outline.png`，不用 SVG

## 命令
```bash
.venv/bin/pip install -r requirements.txt    # 安装依赖
bash scripts/run_local_api.sh                  # 启动 API
bash scripts/run_mobile.sh                     # 启动移动端
bash scripts/run_desktop_dev.sh                # 启动桌面端
.venv/bin/python -m unittest discover -s tests # 全量测试
cd mobile && npm run typecheck                 # 类型检查

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

启动时：读 `.claude/bridge-brief.md`（如有）。如无，加载 `skills/wiki-bridge/SKILL.md` 生成。
开发中：遇到架构决策/结构性踩坑/候选 insight → 加载 wiki-bridge skill 追加 `.claude/wiki-queue.md`。

## Dev Log
每次 session 后追加 `.claude/dev-log.md`：
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
