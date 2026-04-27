from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from advisor.battle_dex import BattleDexRepository
from advisor.config import load_native_model_config
from advisor.contracts import ToolStatus
from advisor.conversation_cli import resolve_backend_config
from advisor.runtime import AdvisorAgent, AdvisorSessionState, ToolRouter, render_response
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
        self.assertEqual(species_route.species_query, "豆丁鱼")

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
        self.assertTrue(any("provisional" in note.lower() for note in response.confidence_notes))
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
