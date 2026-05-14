# Roco Specs

## 约定

- **Active**：当前主线。修改需 PM 确认。
- **Supporting**：被 active 引用，或为背景/历史设计文档。可能过时，以 active 为准。
- **Archive**：已完成或已废弃。移入 `archive/` 保留备查，不删除。
- **V2**：V2 范围的规格，V1 不启用。

新 Agent 进来：先读项目根目录 `CLAUDE.md`（当前切片 + 操作规范），再读 `roco_agent_constitution.md`（Agent 怎么运作），再按需读各分类。内部路线图和阻塞项在 `current_work.md`（不入库，由 PM 维护）。

## Active — V1 Runtime

| 文件 | 说明 |
|---|---|
| `roco_agent_constitution.md` | **入口。** Agent 操作宪法。 |
| `agent_tool_contracts.yaml` | 所有工具的定义、入参、出参 |
| `p9c_agent_call_policy_contract.yaml` | Agent 何时调用工具 |
| `p9c_agent_loop_policy_contract.yaml` | Agent 调用循环上限 |
| `p9e_runtime_policy_closure_contract.yaml` | Runtime 闭合策略 |
| `p9_deepseek_runtime_config_contract.yaml` | Provider 运行时配置 |
| `p9e_deepseek_v4_reference_profile.yaml` | DeepSeek V4 参考配置 |
| `p9e_custom_single_model_support_level.yaml` | 模型支持级别 |
| `llm_runtime_security_contract.yaml` | 安全边界 |
| `presentation_response_contract.yaml` | 回答格式 |
| `persona_doctrine_contract.yaml` | Persona 表达边界 |
| `reasoning_synthesis_contract.yaml` | 推理合成层 |
| `advisor_response_contract.yaml` | Advisor 响应 |
| `p12_agent_kv_continuity_and_grounded_llm_reply_bugfix.md` | **V1 阻塞修复。** KV 连续性与 grounded battle question 的 LLM Agent 终局回复 |

## Active — 数据层

| 文件 | 说明 |
|---|---|
| `battle_dex_schema.yaml` | Battle Dex 数据 schema |
| `battle_dex_sqlite_schema_v1.sql` | SQLite schema |
| `battle_dex_repository_contract.md` | Battle Dex 仓库接口 |
| `manual_battle_data_supplement_schema.yaml` | 手动数据补充格式 |
| `battle_data_model.yaml` | 对战数据模型 |
| `battle_wiki_architecture_spec.md` | Wiki/文档架构 |
| `wiki_crawler_cleaner_contract.yaml` | Wiki 爬取清洗合同 |
| `wiki_field_discovery_spec.md` | Wiki 字段发现 |
| `retrieval_architecture_spec.md` | 检索架构 |
| `retrieval_eval_spec.md` | 检索评估 |
| `abc_architecture_book_authoring_spec.md` | ABC 架构写作 |

## Active — P7/P8（V1 基础）

| 文件 | 说明 |
|---|---|
| `p7_real_agent_chat_contract.yaml` | Chat 接口合同 |
| `p7_real_agent_chat_core.md` | Chat 核心设计 |
| `p8_team_builder_structured_context_contract.yaml` | 队伍构建器合同 |
| `p8_team_builder_structured_context_mvp.md` | 队伍构建器 MVP |

## Active — P10h D 层（V2 预备）

| 文件 | 说明 |
|---|---|
| `p10h_tactical_coach_policy_distillation_plan.md` | **P10h 主策略。** 定义了 D 层 pivot 和整体路线 |
| `p10h_expert_demo_extraction_manual.md` | D 层提取操作手册 |
| `p10h_casebank_seed_schema.yaml` | D 层 case 数据 schema |
| `p10h_d_layer_retrieval_contract.yaml` | D 层检索合同（tag + BM25） |
| `p10h_prebattle_ablation_experiment_plan.md` | 消融实验指针 |
| `tactical_casebank_spec.md` | 战术案例库 |

## V2

| 文件 | 说明 |
|---|---|
| `v2_battle_meta_graph_spec.md` | **V2 Meta Graph 架构。** H-Graph + S-Graph 双架构设计 |

## Active — 领域知识

| 文件 | 说明 |
|---|---|
| `archetype_taxonomy.md` | 队伍 archetype 分类 |
| `role_taxonomy.md` | 精灵角色分类 |
| `semantic_role_policy.md` | 语义角色策略 |
| `report_confidence_policy.md` | 报告置信度策略 |
| `scoring_system.md` | 评分系统 |
| `report_layer.md` | 报告层 |
| `report_schema.yaml` | 报告 schema |

## Supporting — Persona / IP

| 文件 | 说明 |
|---|---|
| `persona_artifact_ingestion_contract.yaml` | Persona 素材摄入 |
| `persona_source_adapter_contract.yaml` | Persona 来源适配器 |
| `enzo_integration_review.md` | Enzo 集成审查 |
| `nuwa_persona_distillation_enzo_request.md` | Nuwa Persona 蒸馏 |
| `managed_persona_creation_pipeline_spec.md` | 托管 Persona 创建 |
| `managed_persona_public_selector_contract.md` | 公开 Persona 选择器 |

## Supporting — UI / V1 设计

| 文件 | 说明 |
|---|---|
| `roco_v1_chat_ui_direction_brief.md` | V1 聊天 UI 方向 |
| `roco_v1_delivery_plan_2026-04-27.md` | V1 交付计划 |
| `roco_v1_ui_prototype_handoff_2026-04-26.md` | UI 原型交接 |
| `v1_single_chat_app_shell_interaction_brief.md` | 单聊天壳交互 |
| `conversation_cli_spec.md` | 对话 CLI |

## Supporting — 产品 / 架构

| 文件 | 说明 |
|---|---|
| `product_architecture_roadmap.md` | 产品架构路线图 |
| `advisor_runtime_spec.md` | Advisor 运行时 |
| `field_alignment_matrix.yaml` | 字段对齐矩阵 |

## 旧文件（可能还值得留）

| 文件 | 说明 |
|---|---|
| `git_boundary_source_control_request.md` | Git 边界管理 |
| `llm_wiki_rag_necessity_review.md` | RAG 必要性审查 |
| `retrieval_phase_a_eval_request.md` | 检索评估请求 |
| `resolver_importer_contract.md` | 解析导入器 |
| `change_policy.md` | 变更策略 |
| `change_specs/` | 变更记录目录 |
| `task_packet_template.md` | 任务包模板 |

## Archive

已归档文件在 `archive/` 下：

| 目录 | 内容 | 说明 |
|---|---|---|
| `archive/p0-p1/` | 45 files | P0/P1 时代规格，已 superseded |
| `archive/p9/` | 7 files | P9 实验设计和 QA 计划，已完成 |
| `archive/p10h/` | 2 files | P10h heuristic schema + full-spectrum extraction plan，已被 expert demo pivot 替代 |
| `archive/adviser_dogfood/` | 5 files | Advisor dogfood 审计和调优，已完成 |
| `archive/handoffs/` | 10 files | 历史交接文档和 session 记录 |
| `archive/p10_early/` | 0 files | （早期 P10 specs 为 untracked，已不在 repo 内） |
