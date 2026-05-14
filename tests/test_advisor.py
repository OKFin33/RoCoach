from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import patch

from advisor.battle_dex import BattleDexRepository
from advisor.config import RocoNativeModelConfig, load_native_model_config
from advisor.contracts import (
    AdvisorResponse,
    ClarificationState,
    ConfidenceFloor,
    GroundingMissingEvidence,
    GroundingToolCallStatus,
    MissingEvidenceKind,
    MissingEvidenceSeverity,
    ToolStatus,
)
from advisor.conversation_cli import resolve_backend_config
from battle_engine.team_structure import TeamStructureAnalyzer
from advisor.runtime import (
    AgentExecutionTrace,
    AdvisorAgent,
    Intent,
    LocalQATraceRecorder,
    NativeAdvisorDeps,
    RouteDecision,
    AdvisorSessionState,
    ToolRouter,
    _native_model_settings_for_config,
    _native_output_mode_for_config,
    _answer_shape_violation,
    _build_grounding_packet,
    _resolve_species_query,
    _validate_grounding_packet,
    render_response,
)
from tools.import_battle_dex_sqlite import write_sqlite

try:
    from pydantic_ai.models.test import TestModel
except ModuleNotFoundError:
    TestModel = None


ROOT = Path(__file__).resolve().parent.parent
IMPORTER_RUN_DIR = ROOT / "data" / "importer_runs" / "2026-04-14Tpolicy_b_importer_dry_run"
SCHEMA_PATH = ROOT / "specs" / "battle_dex_sqlite_schema_v1.sql"


class AdvisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls._tmpdir.name) / "advisor_test.sqlite"
        write_sqlite(
            argparse_namespace(
                importer_run_dir=IMPORTER_RUN_DIR,
                db_path=cls.db_path,
                schema_path=SCHEMA_PATH,
                write_run_id="advisor_test_run",
                replace_run=False,
            )
        )
        cls.repository = BattleDexRepository(cls.db_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.repository.close()
        cls._tmpdir.cleanup()

    def test_repository_lookup_returns_species_profile_and_moves(self) -> None:
        profile = self.repository.get_species_profile("豆丁鱼")
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual(profile.display_name, "豆丁鱼")
        self.assertEqual(profile.primary_type, "水")
        moves = self.repository.get_species_available_moves(profile.species_id, limit=5)
        self.assertGreater(len(moves), 0)
        self.assertTrue(all(move.move_name for move in moves))

    def test_tool_status_enum_matches_response_contract(self) -> None:
        self.assertEqual(
            {status.value for status in ToolStatus},
            {"ok", "degraded", "refused", "failed"},
        )

    def test_repository_supports_concurrent_species_queries(self) -> None:
        def lookup() -> str | None:
            profile = self.repository.get_species_profile("豆丁鱼")
            return None if profile is None else profile.display_name

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda _: lookup(), range(12)))

        self.assertEqual(results, ["豆丁鱼"] * 12)

    def test_session_state_carries_team_between_messages(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        first = agent.handle_message("/set-team 草 地 龙 翼 火 水")
        second = agent.handle_message("分析这队联防")

        self.assertIn("已记录当前队伍", first.answer_summary)
        self.assertIn("结构分", second.answer_summary)
        self.assertTrue(any(tool.tool_name == "analyze_team_structure" for tool in second.tool_results))
        self.assertEqual(len(agent.state_store.get().current_team), 6)

    def test_tool_router_routes_team_and_species_intents(self) -> None:
        router = ToolRouter(repository=self.repository)
        state = AdvisorSessionState()

        team_route = router.route("分析 草 地 龙 翼 火 水 这队联防", state)
        self.assertEqual(team_route.intent, "analyze_team")
        self.assertIn("analyze_team_structure", team_route.tools)

        species_route = router.route("豆丁鱼适合干什么", state)
        self.assertEqual(species_route.intent, "species_query")
        self.assertIn("get_species_profile", species_route.tools)
        self.assertEqual(species_route.species_query, "龙鱼")

        compact_species_route = router.route("豆丁鱼是什么定位？", state)
        self.assertEqual(compact_species_route.intent, "species_query")
        self.assertEqual(compact_species_route.species_query, "龙鱼")

        counterplay_route = router.route("怎么反制圣羽翼王", state)
        self.assertEqual(counterplay_route.intent, "counterplay")
        self.assertEqual(counterplay_route.species_query, "圣羽翼王")

        ordinary_route = router.route("先随便聊两句", state)
        self.assertEqual(ordinary_route.intent, "general_chat")

    def test_contextual_followup_routes_from_recent_turn_summary(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)

        first = agent.handle_message("怎么反制圣羽翼王")
        state = agent.state_store.get()
        followup_route = router.route("什么意思", state)
        counterplay_followup = router.route("那怎么打", state)

        self.assertTrue(state.recent_turn_summaries)
        self.assertEqual(state.recent_turn_summaries[-1].resolved_subject, "圣羽翼王")
        self.assertEqual(followup_route.intent, "species_query")
        self.assertEqual(followup_route.species_query, "圣羽翼王")
        self.assertEqual(counterplay_followup.intent, "counterplay")
        self.assertEqual(counterplay_followup.species_query, "圣羽翼王")
        self.assertNotIn("tool_results", first.answer_summary)

    def test_explicit_species_name_beats_pronoun_context(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("恶魔狼")
        state = agent.state_store.get()

        route = router.route("我有一只小夜，这个精灵的玩法是什么", state)
        typo_route = router.route("我有一只小朔夜，这个精灵的玩法是什么", state)

        self.assertEqual(state.current_species_context, "恶魔狼")
        self.assertEqual(route.intent, "species_query")
        self.assertEqual(route.species_query, "朔夜伊芙")
        self.assertEqual(typo_route.intent, "species_query")
        self.assertEqual(typo_route.species_query, "朔夜伊芙")

    def test_battle_language_defaults_base_stage_to_final_evolution(self) -> None:
        router = ToolRouter(repository=self.repository)
        state = AdvisorSessionState()

        natural_route = router.route("小夜有什么玩法", state)
        typo_route = router.route("小朔夜有什么玩法", state)
        base_form_route = router.route("未进化小夜有什么玩法", state)
        dex_route = router.route("/species 小夜", state)

        self.assertEqual(natural_route.species_query, "朔夜伊芙")
        self.assertEqual(typo_route.species_query, "朔夜伊芙")
        self.assertEqual(base_form_route.species_query, "小夜")
        self.assertEqual(dex_route.species_query, "小夜")

    def test_species_visible_answer_hides_backend_uncertainty_vocabulary(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("小夜有什么玩法")

        self.assertIn("朔夜伊芙", response.answer_summary)
        for forbidden in ("provisional", "reviewed", "D-layer", "案例库", "grounding packet", "runtime_path"):
            self.assertNotIn(forbidden, response.answer_summary)

    def test_pronoun_followup_uses_topic_pool_focus_not_stale_subject_slot(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("恶魔狼")
        agent.handle_message("我有一只小朔夜，这个精灵的玩法是什么")
        state = agent.state_store.get()

        route = router.route("这个精灵还有什么玩法", state)

        self.assertEqual(state.current_species_context, "朔夜伊芙")
        self.assertGreaterEqual(len(state.conversation_topic_pool.species), 2)
        self.assertEqual(state.conversation_topic_pool.active_focus.subject_display_names, ["朔夜伊芙"])
        self.assertEqual(route.intent, "species_query")
        self.assertEqual(route.species_query, "朔夜伊芙")

    def test_active_focus_move_question_routes_to_grounded_species_followup(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("小夜怎么玩")
        state = agent.state_store.get()

        route = router.route("贪婪不是能提供恢复能力？", state)

        self.assertEqual(state.conversation_topic_pool.active_focus.subject_display_names, ["朔夜伊芙"])
        self.assertEqual(route.intent, "species_query")
        self.assertEqual(route.species_query, "朔夜伊芙")

    def test_relation_focus_pronoun_does_not_collapse_to_one_species(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("黑猫巫师")
        agent.handle_message("配合恶魔狼主C")
        state = agent.state_store.get()

        route = router.route("这个精灵怎么样", state)
        followup_route = router.route("什么意思", state)

        self.assertEqual(state.conversation_topic_pool.active_focus.focus_type, "relation")
        self.assertEqual(route.intent, "general_chat")
        self.assertIsNone(route.species_query)
        self.assertEqual(followup_route.intent, "relation_query")
        self.assertEqual(followup_route.relation_anchor_query, "黑猫巫师")
        self.assertEqual(followup_route.relation_partner_query, "恶魔狼")

    def test_live_meta_refusal_is_not_static_control_response(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("当前环境热门是什么，明天会不会削弱圣羽翼王？")

        self.assertEqual(response.runtime_path, "deterministic_degraded_fallback")
        self.assertIn("没有 web/live 官方平衡公告 feed", response.answer_summary)

    def test_natural_language_clear_does_not_clear_session_or_return_static_control(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("豆丁鱼是什么定位？")

        response = agent.handle_message("清空是什么意思")
        state = agent.state_store.get()

        self.assertNotEqual(response.runtime_path, "static_control_response")
        self.assertTrue(state.recent_turn_summaries)
        self.assertEqual(state.current_species_context, "龙鱼")

    def test_non_exact_clear_slash_command_does_not_clear_session(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("豆丁鱼是什么定位？")

        response = agent.handle_message("/clear please")
        state = agent.state_store.get()

        self.assertNotEqual(response.runtime_path, "static_control_response")
        self.assertTrue(state.recent_turn_summaries)
        self.assertEqual(state.current_species_context, "龙鱼")

    def test_relation_followup_preserves_anchor_in_topic_pool(self) -> None:
        router = ToolRouter(repository=self.repository)
        agent = AdvisorAgent(repository=self.repository)

        agent.handle_message("黑猫巫师")
        relation_route = router.route("配合恶魔狼主C", agent.state_store.get())
        response = agent.handle_message("配合恶魔狼主C")
        state = agent.state_store.get()

        self.assertEqual(relation_route.intent, "relation_query")
        self.assertEqual(relation_route.relation_anchor_query, "黑猫巫师")
        self.assertEqual(relation_route.relation_partner_query, "恶魔狼")
        self.assertIn("黑猫巫师", response.answer_summary)
        self.assertIn("恶魔狼", response.answer_summary)
        self.assertIn("不会把焦点改成只分析", response.answer_summary)
        self.assertEqual(state.conversation_topic_pool.active_focus.focus_type, "relation")
        self.assertEqual(len(state.conversation_topic_pool.active_focus.subject_species_ids), 2)
        self.assertTrue(state.conversation_topic_pool.relations)
        self.assertTrue(
            all(species.canonical_species_id for species in state.conversation_topic_pool.species)
        )
        self.assertTrue(
            all(species.source_records for species in state.conversation_topic_pool.species)
        )

    def test_counterplay_with_inline_team_keeps_previous_subject_and_team_context(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        agent.handle_message("怎么反制圣羽翼王")

        response = agent.handle_message("那我这队 草 地 龙 翼 火 水 怎么打它")
        state = agent.state_store.get()

        self.assertEqual(state.current_species_context, "圣羽翼王")
        self.assertEqual(len(state.current_team), 6)
        self.assertTrue(any(tool.tool_name == "get_species_profile" for tool in response.tool_results))
        self.assertNotIn("当前 MVP 只支持", response.answer_summary)

    def test_turn_summary_retention_is_bounded_and_secret_free(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        for index in range(15):
            agent.handle_message(f"豆丁鱼是什么定位？ turn-{index} p4b-secret-test-key")

        state = agent.state_store.get()
        dumped = state.model_dump_json()
        self.assertLessEqual(len(state.recent_turn_summaries), 12)
        self.assertNotIn("p4b-secret-test-key", dumped)
        self.assertTrue(all(not summary.user_message for summary in state.recent_turn_summaries))
        self.assertTrue(all(summary.user_message_digest for summary in state.recent_turn_summaries))

    def test_commit_failure_returns_answer_with_continuity_not_persisted(self) -> None:
        class FailingSetStore:
            def __init__(self) -> None:
                self._state = AdvisorSessionState()
                self.set_calls = 0

            def get(self) -> AdvisorSessionState:
                return self._state.model_copy(deep=True)

            def set(self, state: AdvisorSessionState) -> None:
                self.set_calls += 1
                raise RuntimeError("simulated commit failure")

            def clear(self) -> AdvisorSessionState:
                self._state = AdvisorSessionState()
                return self.get()

        store = FailingSetStore()
        agent = AdvisorAgent(repository=self.repository, state_store=store)

        response = agent.handle_message("豆丁鱼是什么定位？")

        self.assertFalse(response.continuity_persisted)
        self.assertIn("龙鱼", response.answer_summary)
        self.assertTrue(any("continuity_not_persisted" in note for note in response.confidence_notes))
        self.assertEqual(store.set_calls, 1)
        self.assertFalse(store.get().recent_turn_summaries)
        self.assertIsNone(store.get().current_species_context)

    def test_grounding_packet_rejects_missing_required_tool_before_native_synthesis(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        state = agent.state_store.get()
        route = agent.router.route("怎么反制圣羽翼王", state)
        response = agent._handle_species_query_deterministic("怎么反制圣羽翼王", route, state)
        response.tool_results = [
            tool for tool in response.tool_results if tool.tool_name != "retrieve_doc_context"
        ]

        packet = _build_grounding_packet(route, response)
        ok, reason = _validate_grounding_packet(packet)

        self.assertFalse(ok)
        self.assertEqual(reason, "fail_closed_missing_evidence")

    def test_grounding_packet_rejects_failed_tool_and_dangling_claim_evidence(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        state = agent.state_store.get()
        route = agent.router.route("豆丁鱼是什么定位？", state)
        response = agent._handle_species_query_deterministic("豆丁鱼是什么定位？", route, state)
        packet = _build_grounding_packet(route, response)
        packet.tool_calls[0].status = GroundingToolCallStatus.FAILED

        ok, reason = _validate_grounding_packet(packet)

        self.assertFalse(ok)
        self.assertTrue(reason and reason.startswith("tool_not_usable:"))

        packet = _build_grounding_packet(route, response)
        packet.claim_support[0].supporting_evidence_ids.append("ev_missing")
        ok, reason = _validate_grounding_packet(packet)

        self.assertFalse(ok)
        self.assertEqual(reason, "dangling_claim_evidence:answer_summary")

    def test_grounding_packet_rejects_unsupported_claim_and_missing_clarification(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        state = agent.state_store.get()
        route = agent.router.route("豆丁鱼是什么定位？", state)
        response = agent._handle_species_query_deterministic("豆丁鱼是什么定位？", route, state)
        packet = _build_grounding_packet(route, response)
        packet.claim_support[0].support_level = ConfidenceFloor.UNSUPPORTED

        ok, reason = _validate_grounding_packet(packet)

        self.assertFalse(ok)
        self.assertEqual(reason, "unsupported_claim:answer_summary")

        packet = _build_grounding_packet(route, response)
        packet.missing_evidence.append(
            GroundingMissingEvidence(
                kind=MissingEvidenceKind.SUBJECT,
                severity=MissingEvidenceSeverity.CLARIFY,
                repair_path="ask_for_species_name",
            )
        )
        packet.clarification_state = ClarificationState.NOT_NEEDED
        ok, reason = _validate_grounding_packet(packet)

        self.assertFalse(ok)
        self.assertEqual(reason, "clarification_missing")

    def test_native_general_chat_prompt_uses_neutral_project_vocabulary(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        agent.set_persona_llm_context(
            "Persona context contract: persona_llm_context.v1. Tone: cold precise. "
            "For casual greetings, avoid generic assistant welcome."
        )

        instructions = agent._native_instructions(
            RouteDecision(Intent.GENERAL_CHAT, ()),
            AdvisorSessionState(),
        )
        runtime_source = (ROOT / "advisor" / "runtime.py").read_text(encoding="utf-8")

        self.assertNotIn("洛克王国世界", instructions)
        self.assertNotIn("Roco is 洛克王国世界", runtime_source)
        self.assertNotIn("Use 洛克王国世界 terminology", runtime_source)
        self.assertIn("精灵, 队伍, 技能", instructions)
        self.assertIn("Do not say Pokémon", instructions)
        self.assertIn("do not list unsupported game-wide features", instructions)
        self.assertIn("cultivation, breeding, leveling, training, resource planning", instructions)
        self.assertIn("Selected persona writing context", instructions)
        self.assertIn("persona_llm_context.v1", instructions)
        self.assertIn("no provisional", instructions)
        self.assertIn("bulk_present", instructions)

    def test_future_live_meta_request_returns_specific_refusal(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("帮我预测明天官方会不会加强豆丁鱼")

        self.assertIn("没有 web/live 官方平衡公告 feed", response.answer_summary)
        self.assertIn("不能预测未来加强/削弱", response.answer_summary)
        self.assertIn("live meta 变化", response.answer_summary)
        self.assertFalse(response.tool_results)
        self.assertIn("分析 草 地 龙 翼 火 水 这队联防", response.followup_options)

    def test_species_query_degrades_cleanly_without_repository(self) -> None:
        agent = AdvisorAgent(repository=None)
        response = agent.handle_message("/species 豆丁鱼")
        self.assertIn("battle-dex 仓库当前不可用", response.answer_summary)
        self.assertFalse(response.tool_results)

    def test_cli_renders_multistep_session(self) -> None:
        output = subprocess.run(
            [
                sys.executable,
                "-m",
                "advisor.conversation_cli",
                "--db-path",
                str(self.db_path),
                "--skip-bootstrap",
                "--backend",
                "deterministic",
                "--message",
                "/set-team 草 地 龙 翼 火 水",
                "--message",
                "分析这队联防",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("== Roco Advisor MVP ==", output.stdout)
        self.assertIn("== Tool Results ==", output.stdout)
        self.assertIn("analyze_team_structure", output.stdout)

    def test_team_analysis_defaults_to_unknown_quality_and_surfaces_counterevidence(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        agent.handle_message("/set-team 草 地 龙 翼 火 水")
        response = agent.handle_message("分析这队联防")

        semantic_tools = [
            tool for tool in response.tool_results if tool.tool_name == "analyze_team_semantics_guard"
        ]
        self.assertTrue(semantic_tools)
        payload = semantic_tools[0].payload or {}
        self.assertTrue(payload.get("unknown_quality_team"))
        self.assertIn(
            payload.get("coherence_verdict"),
            {
                "coherent",
                "partially_coherent",
                "goodstuff_without_clear_plan",
                "internally_conflicted",
                "insufficient_evidence",
            },
        )
        self.assertTrue(payload.get("counterevidence"))
        self.assertTrue(any("unknown-quality team" in note for note in response.confidence_notes))
        self.assertIn("反证", response.answer_summary)

    def test_species_query_auto_retrieves_reviewed_mechanism_page_from_ability_text(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("/species 帕帕斯卡")

        doc_tools = [tool for tool in response.tool_results if tool.tool_name == "retrieve_doc_context"]
        self.assertTrue(doc_tools)
        payload = doc_tools[0].payload or {}
        self.assertIn("迅捷", payload.get("resolved_mechanism_tokens", []))
        self.assertIn("传动", payload.get("resolved_mechanism_tokens", []))
        self.assertTrue(
            any(
                item.source_label == "wiki/pages/mechanics/speed_priority_and_swift.md"
                for item in response.evidence_summary
            )
        )
        self.assertTrue(
            any(
                item.source_label == "wiki/pages/mechanics/transmission_and_skill_slots.md"
                for item in response.evidence_summary
            )
        )

    def test_species_query_auto_retrieves_reviewed_mechanism_page_from_move_text(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("/species 晶石蜗")

        doc_tools = [tool for tool in response.tool_results if tool.tool_name == "retrieve_doc_context"]
        self.assertTrue(doc_tools)
        payload = doc_tools[0].payload or {}
        resolved = set(payload.get("resolved_mechanism_tokens", []))
        self.assertTrue({"迅捷", "应对"} & resolved)
        evidence_sources = {item.source_label for item in response.evidence_summary}
        self.assertTrue(
            {
                "wiki/pages/mechanics/speed_priority_and_swift.md",
                "wiki/pages/mechanics/response_counterplay.md",
            }
            & evidence_sources
        )

    def test_native_model_config_loader_reads_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "env"
            env_path.write_text(
                "\n".join(
                    [
                        "ROCO_ADVISOR_MODEL=kimi-k2.5",
                        "ROCO_OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3",
                        "ROCO_OPENAI_API_KEY=test-key",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_native_model_config(env_path=env_path)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.model_name, "kimi-k2.5")

    def test_auto_backend_uses_native_when_env_config_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "env"
            env_path.write_text(
                "\n".join(
                    [
                        "ROCO_ADVISOR_MODEL=kimi-k2.5",
                        "ROCO_OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3",
                        "ROCO_OPENAI_API_KEY=test-key",
                    ]
                ),
                encoding="utf-8",
            )
            backend, model_name, native_model, auto_selected = resolve_backend_config(
                requested_backend="auto",
                env_file=env_path,
                model_name=None,
            )

        self.assertEqual(backend, "pydantic_ai_native")
        self.assertEqual(model_name, "kimi-k2.5")
        self.assertIsNotNone(native_model)
        self.assertTrue(auto_selected)

    def test_auto_backend_falls_back_to_deterministic_without_env_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            backend, model_name, native_model, auto_selected = resolve_backend_config(
                requested_backend="auto",
                env_file=Path(tmp) / "missing-env",
                model_name=None,
            )

        self.assertEqual(backend, "deterministic")
        self.assertIsNone(model_name)
        self.assertIsNone(native_model)
        self.assertTrue(auto_selected)

    def test_explicit_native_backend_requires_env_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                resolve_backend_config(
                    requested_backend="pydantic_ai_native",
                    env_file=Path(tmp) / "missing-env",
                    model_name=None,
                )

    def test_deepseek_native_config_uses_prompted_output_mode(self) -> None:
        config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )

        self.assertEqual(_native_output_mode_for_config(config), "prompted")
        self.assertEqual(_native_output_mode_for_config(object()), "tool")
        self.assertEqual(
            _native_model_settings_for_config(config),
            {
                "extra_body": {"thinking": {"type": "enabled"}},
                "openai_reasoning_effort": "max",
            },
        )

    def test_native_prompt_does_not_define_roco_as_public_self_identity(self) -> None:
        source = (ROOT / "advisor" / "runtime.py").read_text(encoding="utf-8")

        self.assertNotIn("You are the Roco conversational advisor", source)
        self.assertIn("Answer through the selected public persona", source)
        self.assertIn("Treat battle-advice role as task context, not self-identity", source)
        self.assertIn("Do not proactively mention cultivation, breeding, leveling, training", source)
        self.assertIn("persona identity is supplied by the persona layer", source)

    def test_native_runtime_replays_protocol_message_history_between_turns(self) -> None:
        class _HistoryResult:
            def __init__(self, output: Any, messages: list[Any]) -> None:
                self.output = output
                self._messages = messages

            def all_messages(self) -> list[Any]:
                return list(self._messages)

        class _HistoryAgent:
            def __init__(self) -> None:
                self.seen_histories: list[list[Any] | None] = []

            def run_sync(self, _message: str, **kwargs):
                self.seen_histories.append(kwargs.get("message_history"))
                turn = len(self.seen_histories)
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary=f"native turn {turn}",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    ),
                    messages=[f"protocol-message-{turn}"],
                )

        fake_agent = _HistoryAgent()
        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
        )

        with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
            first = agent.handle_message("我现在该怎么用你来优化队伍？")
            second = agent.handle_message("继续，不要重查")

        self.assertEqual(first.answer_summary, "native turn 1")
        self.assertEqual(second.answer_summary, "native turn 2")
        self.assertEqual(fake_agent.seen_histories, [None, ["protocol-message-1"]])
        state = agent.state_store.get()
        self.assertEqual(state.native_model_messages, ["protocol-message-2"])
        self.assertIsNotNone(state.native_runtime_fingerprint)
        dumped_state = state.model_dump(mode="json")
        self.assertNotIn("native_model_messages", dumped_state)
        self.assertNotIn("native_runtime_fingerprint", dumped_state)

    def test_native_protocol_history_is_bounded(self) -> None:
        class _LongHistoryResult:
            def __init__(self, output: AdvisorResponse) -> None:
                self.output = output

            def all_messages(self) -> list[str]:
                return ["m1", "m2", "m3"]

        class _LongHistoryAgent:
            def run_sync(self, _message: str, **_kwargs):
                return _LongHistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary="native bounded history",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    )
                )

        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
            max_native_model_messages=2,
        )

        with patch("advisor.runtime._build_native_agent", return_value=_LongHistoryAgent()):
            agent.handle_message("我现在该怎么用你来优化队伍？")

        self.assertEqual(agent.state_store.get().native_model_messages, ["m2", "m3"])

    def test_native_runtime_passes_terminal_response_usage_limits(self) -> None:
        class _BudgetResult:
            def __init__(self) -> None:
                self.output = AdvisorResponse(
                    backend="pydantic_ai_native",
                    answer_summary="native budget guarded",
                    tool_results=[],
                    evidence_summary=[],
                    confidence_notes=[],
                    followup_options=[],
                )

            def all_messages(self) -> list[str]:
                return ["budget-message"]

        class _BudgetAgent:
            def __init__(self) -> None:
                self.usage_limits: list[Any] = []

            def run_sync(self, _message: str, **kwargs):
                self.usage_limits.append(kwargs.get("usage_limits"))
                return _BudgetResult()

        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        fake_agent = _BudgetAgent()
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
        )

        with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
            response = agent.handle_message("帮我分析这套队伍怎么优化")

        self.assertEqual(response.answer_summary, "native budget guarded")
        self.assertEqual(len(fake_agent.usage_limits), 1)
        usage_limits = fake_agent.usage_limits[0]
        self.assertEqual(usage_limits.request_limit, 3)
        self.assertEqual(usage_limits.tool_calls_limit, 2)

    def test_native_usage_limit_returns_terminal_budget_response(self) -> None:
        try:
            from pydantic_ai.usage import UsageLimitExceeded
        except ModuleNotFoundError:
            self.skipTest("pydantic_ai is not installed")

        class _BudgetExceededAgent:
            def run_sync(self, _message: str, **_kwargs):
                raise UsageLimitExceeded("request limit reached")

        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
        )

        with patch("advisor.runtime._build_native_agent", return_value=_BudgetExceededAgent()):
            response = agent.handle_message("帮我分析这套队伍怎么优化")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertIn("调用预算上限", response.answer_summary)
        self.assertTrue(
            any("terminal_response_budget_exhausted" in note for note in response.confidence_notes)
        )

    def test_native_grounded_answer_shape_leak_fails_closed(self) -> None:
        class _LeakyResult:
            def __init__(self) -> None:
                self.output = AdvisorResponse(
                    backend="pydantic_ai_native",
                    answer_summary='runtime_path=native_llm_terminal; tool_results={"raw": true}',
                    tool_results=[],
                    evidence_summary=[],
                    confidence_notes=[],
                    followup_options=[],
                )

            def all_messages(self) -> list[str]:
                return ["leaky-message"]

        class _LeakyAgent:
            def run_sync(self, _message: str, **_kwargs):
                return _LeakyResult()

        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
        )

        with patch("advisor.runtime._build_native_agent", return_value=_LeakyAgent()):
            response = agent.handle_message("怎么反制圣羽翼王")

        self.assertEqual(response.runtime_path, "deterministic_degraded_fallback")
        self.assertNotIn("runtime_path", response.answer_summary)
        self.assertNotIn("tool_results", response.answer_summary)
        self.assertTrue(any("answer_shape_invalid" in note for note in response.confidence_notes))

    def test_answer_shape_rejects_backend_uncertainty_and_semantic_tags(self) -> None:
        forbidden_answers = [
            "两种基础打法草图均为provisional，缺完整队伍验证。",
            "624的种族分配倾向速度和一定的耐久线（bulk_present）。",
            "这是 reviewed 机制页支持的判断。",
            "需要 D-layer 案例库才能确认。",
        ]

        for answer in forbidden_answers:
            with self.subTest(answer=answer):
                self.assertIsNotNone(_answer_shape_violation(answer))

    def test_agent_execution_trace_records_plan_loop_packet_and_grade(self) -> None:
        class _TraceRecorder:
            def __init__(self) -> None:
                self.traces: list[AgentExecutionTrace] = []

            def record(self, *, trace: AgentExecutionTrace) -> None:
                self.traces.append(trace)

        recorder = _TraceRecorder()
        agent = AdvisorAgent(repository=self.repository, trace_recorder=recorder)

        response = agent.handle_message("怎么反制圣羽翼王")

        self.assertTrue(response.tool_results)
        self.assertEqual(len(recorder.traces), 1)
        trace = recorder.traces[0]
        self.assertEqual(trace.plan_intent, "counterplay")
        self.assertGreaterEqual(trace.loop_iterations, 1)
        self.assertTrue(trace.loop_actions)
        self.assertIn("passed", trace.answer_shape_checks)
        self.assertEqual(trace.final_grade, "pass")
        self.assertIn("get_species_profile", trace.tool_calls)
        self.assertTrue(trace.retrieval_refs)
        self.assertEqual(trace.provider_timeout_seconds, agent.native_timeout_seconds)
        self.assertEqual(trace.per_tool_timeout_seconds, agent.per_tool_timeout_seconds)
        self.assertEqual(trace.max_turn_timeout_seconds, agent.max_turn_timeout_seconds)

    def test_native_grounded_trace_records_valid_packet_status_and_synthesis_loop(self) -> None:
        class _GroundedResult:
            def __init__(self) -> None:
                self.output = AdvisorResponse(
                    backend="pydantic_ai_native",
                    answer_summary="圣羽翼王要按有条件威胁处理，先拆速度轴再决定反压方式。",
                    tool_results=[],
                    evidence_summary=[],
                    confidence_notes=[],
                    followup_options=[],
                )

            def all_messages(self) -> list[str]:
                return ["grounded-trace-message"]

        class _GroundedAgent:
            def run_sync(self, _message: str, **_kwargs):
                return _GroundedResult()

        class _TraceRecorder:
            def __init__(self) -> None:
                self.traces: list[AgentExecutionTrace] = []

            def record(self, *, trace: AgentExecutionTrace) -> None:
                self.traces.append(trace)

        recorder = _TraceRecorder()
        native_config = RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="test-runtime-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=native_config,
            trace_recorder=recorder,
        )

        with patch("advisor.runtime._build_native_agent", return_value=_GroundedAgent()):
            response = agent.handle_message("怎么反制圣羽翼王")

        self.assertEqual(response.runtime_path, "native_llm_terminal")
        trace = recorder.traces[0]
        self.assertEqual(trace.grounding_packet_status, "valid")
        self.assertIn("validate_packet", trace.loop_actions)
        self.assertIn("synthesize", trace.loop_actions)
        self.assertIn("grade_answer", trace.loop_actions)
        self.assertEqual(trace.stop_reason, "native_grounded_terminal_synthesized")
        self.assertEqual(trace.final_grade, "pass")
        self.assertEqual(trace.topic_pool_delta["active_focus_type"], "single_species")

    def test_grounded_loop_asks_clarification_for_unresolved_relation_subjects(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        route = RouteDecision(
            Intent.RELATION_QUERY,
            ("get_species_profile", "get_species_available_moves", "retrieve_doc_context"),
            species_query="不存在一号",
            relation_anchor_query="不存在一号",
            relation_partner_query="不存在二号",
        )

        result = agent._run_grounded_planner_tool_loop(
            message="不存在一号配合不存在二号",
            route=route,
            state=AdvisorSessionState(),
        )

        self.assertFalse(result.packet_ok)
        self.assertIn("ask_clarification", result.actions)
        self.assertEqual(result.stop_reason, "clarification_required")

    def test_retrieve_more_repairs_missing_required_doc_tool(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        state = agent.state_store.get()
        route = agent.router.route("怎么反制圣羽翼王", state)
        response = agent._handle_species_query_deterministic("怎么反制圣羽翼王", route, state)
        response.tool_results = [
            tool for tool in response.tool_results if tool.tool_name != "retrieve_doc_context"
        ]
        packet = _build_grounding_packet(route, response)
        ok, reason = _validate_grounding_packet(packet)
        self.assertFalse(ok)
        self.assertEqual(reason, "fail_closed_missing_evidence")

        repaired = agent._retrieve_more_for_grounded_packet(
            message="怎么反制圣羽翼王",
            route=route,
            response=response,
        )
        repaired_packet = _build_grounding_packet(route, repaired)
        ok, reason = _validate_grounding_packet(repaired_packet)

        self.assertTrue(ok, reason)
        self.assertTrue(any(tool.tool_name == "retrieve_doc_context" for tool in repaired.tool_results))

    def test_non_doc_tool_timeout_degrades_response(self) -> None:
        class _SlowRepository:
            def __init__(self, inner) -> None:
                self.inner = inner

            def __getattr__(self, name: str):
                return getattr(self.inner, name)

            def get_species_profile(self, *args, **kwargs):
                time.sleep(0.05)
                return self.inner.get_species_profile(*args, **kwargs)

        agent = AdvisorAgent(
            repository=_SlowRepository(self.repository),
            per_tool_timeout_seconds=0.01,
        )

        response = agent.handle_message("豆丁鱼是什么定位？")

        self.assertEqual(response.runtime_path, "deterministic_degraded_fallback")
        self.assertIn("本地工具调用超过预算", response.answer_summary)
        self.assertTrue(any(tool.tool_name == "runtime_tool_timeout" for tool in response.tool_results))

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_team_tool_timeout_degrades_response(self) -> None:
        class _SlowAnalyzer:
            def analyze(self, slots):
                time.sleep(0.05)
                return TeamStructureAnalyzer().analyze(slots)

        agent = AdvisorAgent(
            repository=self.repository,
            analyzer=_SlowAnalyzer(),
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=["analyze_team_structure"],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "ignored by validator",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
            per_tool_timeout_seconds=0.01,
        )

        agent.handle_message("/set-team 草 地 龙 翼 火 水")
        response = agent.handle_message("分析这队联防")

        self.assertEqual(response.runtime_path, "deterministic_degraded_fallback")
        self.assertIn("本地工具调用超过预算", response.answer_summary)
        self.assertTrue(any("tool_timeout" in note for note in response.confidence_notes))

    def test_max_turn_timeout_degrades_user_visible_response(self) -> None:
        agent = AdvisorAgent(repository=self.repository, max_turn_timeout_seconds=1.0)

        with patch("advisor.runtime.monotonic", side_effect=[0.0, 2.0, 2.0, 2.0]):
            response = agent.handle_message("豆丁鱼是什么定位？")

        self.assertEqual(response.runtime_path, "deterministic_degraded_fallback")
        self.assertIn("超过最大回合预算", response.answer_summary)
        self.assertTrue(any("max_turn_timeout_exceeded" in note for note in response.confidence_notes))

    def test_default_trace_recorder_retains_redacted_local_qa_traces(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        agent.handle_message("豆丁鱼是什么定位？ p4b-secret-test-key")

        self.assertIsInstance(agent.trace_recorder, LocalQATraceRecorder)
        traces = agent.trace_recorder.recent()
        self.assertEqual(len(traces), 1)
        dumped = str(traces[0])
        self.assertNotIn("p4b-secret-test-key", dumped)
        self.assertEqual(traces[0].final_grade, "pass")

    def test_species_tool_argument_prefers_router_query_over_model_argument(self) -> None:
        deps = NativeAdvisorDeps(
            repository=self.repository,
            analyzer=None,
            doc_retriever=None,
            state=AdvisorSessionState(),
            route=RouteDecision(Intent.SPECIES_QUERY, (), species_query="豆丁鱼"),
            message="豆丁鱼适合干什么？",
        )

        self.assertEqual(_resolve_species_query(deps, "豆丁鱼？"), "豆丁鱼")
        self.assertEqual(_resolve_species_query(deps, "不存在的精灵？"), "豆丁鱼")

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_handles_general_natural_language_prompt(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "我可以先帮你拆目标、确认队伍信息，再决定是否调用精灵或队伍工具。",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        response = agent.handle_message("我现在该怎么用你来优化队伍？")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertNotIn("当前 MVP 只支持", response.answer_summary)
        self.assertNotIn("可用命令", response.answer_summary)
        self.assertTrue(response.followup_options)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_calls_team_tools_and_merges_trace(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=["analyze_team_structure", "retrieve_doc_context"],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "原生 agent 已完成队伍结构分析。",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        agent.handle_message("/set-team 草 地 龙 翼 火 水")
        response = agent.handle_message("分析这队联防")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertTrue(any(tool.tool_name == "analyze_team_structure" for tool in response.tool_results))
        self.assertTrue(any(tool.tool_name == "analyze_team_semantics_guard" for tool in response.tool_results))
        self.assertTrue(any(item.source_label == "battle_engine.team_structure" for item in response.evidence_summary))
        self.assertTrue(any("unknown-quality team" in note for note in response.confidence_notes))
        self.assertTrue(any("confirmed" in note.lower() for note in response.confidence_notes))
        self.assertTrue(any("双属性" in note for note in response.confidence_notes))

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_team_analysis_without_team_asks_for_context(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=["analyze_team_structure"],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "ignored by validator",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        response = agent.handle_message("帮我分析这套队伍怎么优化")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertIn("还没有拿到可分析的队伍", response.answer_summary)
        self.assertTrue(
            any(
                tool.tool_name == "analyze_team_structure" and tool.status == ToolStatus.REFUSED
                for tool in response.tool_results
            )
        )
        self.assertTrue(any("missing_team_context" in note for note in response.confidence_notes))
        self.assertFalse(response.evidence_summary)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_calls_species_tools_and_updates_species_context(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=[
                    "get_species_profile",
                    "get_species_available_moves",
                    "retrieve_doc_context",
                    "analyze_species_semantics",
                ],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "原生 agent 已完成物种分析。",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        response = agent.handle_message("/species 豆丁鱼")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertTrue(any(tool.tool_name == "get_species_profile" for tool in response.tool_results))
        self.assertTrue(any(tool.tool_name == "analyze_species_semantics" for tool in response.tool_results))
        self.assertTrue(any("用户侧回答" in note for note in response.confidence_notes))
        self.assertTrue(
            any(item.source_label.startswith("derived_ability:") for item in response.evidence_summary)
        )
        self.assertEqual(agent.state_store.get().current_species_context, "豆丁鱼")

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_species_path_surfaces_mechanism_evidence(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=[
                    "get_species_profile",
                    "get_species_available_moves",
                    "retrieve_doc_context",
                    "analyze_species_semantics",
                ],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "原生 agent 已完成物种分析。",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        response = agent.handle_message("/species 帕帕斯卡")

        self.assertTrue(
            any(
                item.source_label == "wiki/pages/mechanics/speed_priority_and_swift.md"
                for item in response.evidence_summary
            )
        )
        doc_tools = [tool for tool in response.tool_results if tool.tool_name == "retrieve_doc_context"]
        self.assertTrue(doc_tools)
        payload = doc_tools[0].payload or {}
        self.assertIn("迅捷", payload.get("resolved_mechanism_tokens", []))
        self.assertIn("传动", payload.get("resolved_mechanism_tokens", []))

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_returns_clean_refusal_for_unknown_species(self) -> None:
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(
                call_tools=[
                    "get_species_profile",
                    "get_species_available_moves",
                    "retrieve_doc_context",
                    "analyze_species_semantics",
                ],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "ignored by validator",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )

        response = agent.handle_message("/species 不存在的精灵")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertIn("battle-dex 里没有找到", response.answer_summary)
        profile_results = [
            tool for tool in response.tool_results if tool.tool_name == "get_species_profile"
        ]
        self.assertTrue(profile_results)
        self.assertEqual(profile_results[0].status, ToolStatus.REFUSED)
        self.assertNotIn(
            "unavailable",
            {tool.status for tool in response.tool_results},
        )
        self.assertFalse(response.evidence_summary)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_runtime_wraps_provider_failures(self) -> None:
        class _BrokenAgent:
            def run_sync(self, *args, **kwargs):
                raise RuntimeError("provider offline")

        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(),
        )

        with patch("advisor.runtime._build_native_agent", return_value=_BrokenAgent()):
            response = agent.handle_message("/species 豆丁鱼")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertIn("native runtime 当前不可用", response.answer_summary)
        self.assertFalse(response.tool_results)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_auto_native_provider_failure_falls_back_to_deterministic(self) -> None:
        class _BrokenAgent:
            def run_sync(self, *args, **kwargs):
                raise RuntimeError("provider offline")

        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(),
            auto_selected=True,
        )
        agent.handle_message("/set-team 草 地 龙 翼 火 水")

        with patch("advisor.runtime._build_native_agent", return_value=_BrokenAgent()):
            response = agent.handle_message("分析这队联防")

        self.assertEqual(response.backend, "auto_fallback_deterministic")
        self.assertTrue(any("回退到 deterministic" in note for note in response.confidence_notes))
        self.assertTrue(any(tool.tool_name == "analyze_team_structure" for tool in response.tool_results))

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_explicit_native_provider_failure_stays_bounded_native_failure(self) -> None:
        class _BrokenAgent:
            def run_sync(self, *args, **kwargs):
                raise RuntimeError("provider offline")

        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(),
            auto_selected=False,
        )

        with patch("advisor.runtime._build_native_agent", return_value=_BrokenAgent()):
            response = agent.handle_message("/species 豆丁鱼")

        self.assertEqual(response.backend, "pydantic_ai_native")
        self.assertIn("native runtime 当前不可用", response.answer_summary)
        self.assertFalse(response.tool_results)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_native_timeout_is_bounded_and_auto_falls_back(self) -> None:
        class _SlowAgent:
            def __init__(self) -> None:
                self.calls = 0

            def run_sync(self, *args, **kwargs):
                self.calls += 1
                time.sleep(0.2)
                raise AssertionError("should not reach successful native result")

        slow_agent = _SlowAgent()
        agent = AdvisorAgent(
            repository=self.repository,
            backend="pydantic_ai_native",
            native_model=TestModel(),
            auto_selected=True,
            native_timeout_seconds=0.01,
        )
        agent.handle_message("/set-team 草 地 龙 翼 火 水")
        started = time.perf_counter()

        with patch("advisor.runtime._build_native_agent", return_value=slow_agent):
            response = agent.handle_message("分析这队联防")
            second_response = agent.handle_message("/species 豆丁鱼")

        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 0.5)
        self.assertEqual(slow_agent.calls, 1)
        self.assertEqual(response.backend, "auto_fallback_deterministic")
        self.assertIn("结构分", response.answer_summary)
        self.assertEqual(second_response.backend, "auto_fallback_deterministic")
        self.assertTrue(
            any("已跳过 native runtime" in note for note in second_response.confidence_notes)
        )
        self.assertTrue(any(tool.tool_name == "get_species_profile" for tool in second_response.tool_results))

    def test_partial_team_analysis_includes_visible_caveat(self) -> None:
        agent = AdvisorAgent(repository=self.repository)

        response = agent.handle_message("帮我看看 草 地 龙 这队有洞吗")

        self.assertIn("partial-team", response.answer_summary)
        self.assertTrue(any("partial-team" in note for note in response.confidence_notes))
        self.assertTrue(any("剩余 3 个槽位" in option for option in response.followup_options))

    def test_renderer_includes_doc_evidence_when_retrieval_ran(self) -> None:
        agent = AdvisorAgent(repository=self.repository)
        response = agent.handle_message("分析 草 地 龙 翼 火 水 这队联防")

        rendered = render_response(response)

        self.assertIn("doc:", rendered)
        self.assertIn("docs/agent_framework_decision.md", rendered)


def argparse_namespace(**kwargs: object):
    class _Namespace:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

    return _Namespace(**kwargs)


if __name__ == "__main__":
    unittest.main()
