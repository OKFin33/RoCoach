# Roco Specs

## 约定

- **Active**：当前主线。修改需 PM 确认。
- **Supporting**：被 active 引用，或为背景/历史设计文档。可能过时，以 active 为准。
- **Archive**：已完成或已废弃。移入 `archive/` 保留备查，不删除。
- **Historical V2 label**：部分文件名仍带 `v2`，但当前 V1 正式发版已前置 Meta Graph v0.1 和 D-layer v0.1；以 `docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md` 为准。

新 Agent 进来：先读项目根目录 `CLAUDE.md`（当前切片 + 操作规范），再读 `docs/handoffs/ROCO_CURRENT_CONTEXT_MAP_2026_05_16.md`，再读 `roco_agent_constitution.md`（Agent 怎么运作），再按需读各分类。内部路线图和阻塞项以 context map 为准；`current_work.md` 可能是旧工作便签。

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

## Active — P10h D 层（V1 知识前置）

| 文件 | 说明 |
|---|---|
| `p10h_tactical_coach_policy_distillation_plan.md` | **P10h 主策略。** 定义了 D 层 pivot 和整体路线 |
| `p10h_expert_demo_extraction_manual.md` | D 层提取操作手册 |
| `p10h_casebank_seed_schema.yaml` | D 层 case 数据 schema |
| `p10h_d_layer_retrieval_contract.yaml` | D 层检索合同（tag + BM25） |
| `p10h_prebattle_ablation_experiment_plan.md` | 消融实验指针 |
| `tactical_casebank_spec.md` | 战术案例库 |

## Active — Meta Graph（V1 v0.1；S-Graph 后置）

| 文件 | 说明 |
|---|---|
| `p14_knowledge_ops_control_plane.md` | **当前 Meta Graph / mechanism 前置控制面。** 定义 Agent 如何安全推进 100-150 reviewed set 图谱、Graph-owned data root、机制规则层、reviewer ledger、source discovery、review packet、validator、stop rules。 |
| `p14_dataset_pipeline_plan_v0_1.md` | **数据集构建 Pipeline Plan v0.1。** 把 Roco 数据集定义为 Evidence KB + structured KG/Meta Graph + Gold/Eval + LLM Wiki 的治理型数据产品；规定样本单位、来源政策、字段级 provenance、评审独立性、质量指标、snapshot/datasheet、rights 边界和 Agent 可执行任务卡；planning-only，不授权直接制作数据集。 |
| `p14_dataset_card_template_v0.md` | Dataset card / datasheet 模板；定义 future snapshot 必填的任务、组件、来源、provenance、质量、rights、维护字段。 |
| `p14_dataset_snapshot_versioning_contract_v0.md` | Snapshot 与版本合同；定义 `roco_kg_dataset_v0.1-dev/YYYY-MM-DD`、manifest、hash、supersession、schema migration 和 runtime-promotion 分离。 |
| `p14_dataset_provenance_schema_contract_v0.md` | 字段级 provenance 与样本 schema 合同；定义 Evidence KB、claim atom、KG candidate、Gold/Eval 的 source span、repair history、review identity 要求。 |
| `p14_gold_eval_regression_contract_v0.md` | Gold/Eval regression 合同；定义 accepted Gold 输入、prediction/result schema、critical/major/minor、dashboard 接口和 pending-seeded-gold 状态。 |
| `p14_dataset_quality_dashboard_contract_v0.md` | 数据质量 dashboard 合同；定义 entity resolution、move legality、unresolved ASR、field provenance、Gold regression、RAG/faithfulness、drift 等指标。 |
| `p14_retrieval_kb_eval_contract_v0.md` | Evidence KB 检索评测合同；定义 covered/uncovered 问题、context precision/recall、faithfulness、noise sensitivity、stale-source rejection 和降级行为。 |
| `p14_mechanism_rule_dataset_lane_v0.md` | 机制规则数据通道合同；定义 M0-M5 状态、contradiction taxonomy、high-impact review、affected asset recheck 和 mechanism drift。 |
| `p14_dataset_review_independence_contract_v0.md` | Review independence 与 PM packet 合同；定义角色分离、agent/run 身份、disagreement log、PM action vocabulary 和 packet budget。 |
| `p14_dataset_plan_verification_runbook_v0.md` | Planning package 验证 runbook；定义 DP-01 到 DP-11 输出检查、禁止路径、Gold manifest 不变、runtime_allowed scan 和 pre-goal baseline 检查。 |
| `p14_acquisition_skill_integration_contract_v0.md` | Acquisition skill integration 合同；定义强化后的 `social-media-reader` / Scribe 输入层如何输出 `source_transcript_bundle`，并且必须经过 Roco provenance、A/B 精校、质量门后才能进入候选抽取。 |
| `p14_verifier_llm_judge_eval_contract_v0.md` | Verifier / LLM-as-judge eval 合同；定义 deterministic verifier、A-layer、provenance、RAG/faithfulness、LLM judge、Reviewer、PM 的级联，明确 LLM judge 只能评估证据一致性，不能成为事实来源。 |
| `p14_species_set_kg_item_crosswalk_v0.md` | Species Set card 到 `p14.kg_item.v0` 的迁移 crosswalk；要求 reviewed card 补 `schema_version`、字段级 provenance、review identity，避免旧卡和新 KG schema 并行漂移。 |
| `p14_gold_candidate_to_item_mapping_v0.md` | Gold candidate packet 到 accepted `p14.gold_item.v0` 的映射合同；明确候选不等于 Gold 接受，必须有 PM decision、expected allowed/forbidden behavior、字段级 provenance 和 manifest 更新边界。 |
| `p14_dataset_pipeline_external_research_and_local_review_2026_05_22.md` | **数据集构建计划前置 review。** 对照外部 dataset/KG/RAG/eval 实践和本地 P14 状态，定义下一步只做计划包、不直接制作数据集的 `/goal` 边界。 |
| `p14_gold_eval_review_design.md` | **P14 质量层设计。** 定义 Gold Set v0、Annotation Guideline v0、Review Packet Format v1，用于把启发式候选流水线升级为可校准、可审计的数据构建流程。 |
| `p14_set_inventory_schema.md` | **Set Inventory schema。** 定义 L1a/L1b/L2/L3、set family、alter variant、split blocker 和候选 consolidation 语义。 |
| `v2_battle_meta_graph_spec.md` | **Meta Graph 架构。** 文件名仍带 V2；当前 H-Graph v0.1 已是 V1 前置，S-Graph 仍后置 |
| `p13_meta_graph_round1_set_input_plan.md` | Round 1 输入漏斗和候选提取计划。仍可用作 source funnel，但 v0.1 停止条件以 P14 为准。 |

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
