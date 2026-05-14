from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from advisor.battle_dex import BattleDexRepository
from advisor.config import RocoNativeModelConfig
from advisor.contracts import AdvisorEvidenceItem, AdvisorResponse, AdvisorSessionState, AdvisorToolResult, SourceType
from advisor.runtime import _native_runtime_fingerprint
from agent_core.persona import DEFAULT_PERSONA_DISPLAY_NAME, DEFAULT_PERSONA_ID
from agent_core.persona_activation_projection import build_persona_activation_registry_projection
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_profile_materialization import (
    materialize_persona_projection_profiles,
    write_persona_projection_profile_materialization,
)
from agent_core.persona_profile_resolver import make_managed_persona_selector
from agent_core.persona_registry import ALTERNATE_PERSONA_DISPLAY_NAME, ALTERNATE_PERSONA_ID
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import write_persona_registry_record
from agent_core.persona_runtime_activation import build_persona_runtime_activation_report
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle
from agent_core.contracts import PersonaRuntimeActivationScope
from api.main import ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV, ROCO_MANAGED_PERSONA_SCOPE_ENV, create_app
from api.release import RATE_LIMIT_MODE, RELEASE_STAGE, SERVICE_NAME
from api.runtime_headers import (
    HEADER_MODEL,
    HEADER_PROVIDER_BASE_URL,
    HEADER_PROVIDER_KEY,
    HEADER_REASONING_EFFORT,
    HEADER_REASONING_MODE,
    HEADER_RUNTIME_MODE,
)
from api.services.advisor_service import AdvisorService
from api.services.advisor_service import _native_timeout_for_model
from api.services.session_store import ActiveSessionStore
from reporting.contracts import ConfidenceTier
from tools.import_battle_dex_sqlite import write_sqlite

try:
    from pydantic_ai.models.test import TestModel
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    TestModel = None

try:
    from pydantic_ai.messages import ModelRequest, UserPromptPart
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    ModelRequest = None
    UserPromptPart = None


ROOT = Path(__file__).resolve().parent.parent
IMPORTER_RUN_DIR = ROOT / "data" / "importer_runs" / "2026-04-14Tpolicy_b_importer_dry_run"
SCHEMA_PATH = ROOT / "specs" / "battle_dex_sqlite_schema_v1.sql"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls._tmpdir.name) / "api_test.sqlite"
        write_sqlite(
            argparse_namespace(
                importer_run_dir=IMPORTER_RUN_DIR,
                db_path=cls.db_path,
                schema_path=SCHEMA_PATH,
                write_run_id="api_test_run",
                replace_run=False,
            )
        )
        repository = BattleDexRepository(cls.db_path)
        cls.service = AdvisorService(
            repository=repository,
            default_backend="deterministic",
            session_db_path=Path(cls._tmpdir.name) / "session.sqlite3",
        )
        cls.client = TestClient(create_app(advisor_service=cls.service))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.service.repository.close() if cls.service.repository is not None else None
        cls._tmpdir.cleanup()

    def test_health_and_metadata_are_redacted(self) -> None:
        health = self.client.get("/health")
        metadata = self.client.get("/metadata")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(health.json()["service_name"], SERVICE_NAME)
        self.assertEqual(health.json()["release_stage"], RELEASE_STAGE)
        self.assertEqual(health.json()["response_schema_version"], "agent_response.v1")
        self.assertEqual(metadata.status_code, 200)
        metadata_payload = metadata.json()
        self.assertEqual(metadata_payload["service_name"], SERVICE_NAME)
        self.assertEqual(metadata_payload["release_stage"], RELEASE_STAGE)
        self.assertEqual(metadata_payload["default_backend"], "deterministic")
        self.assertTrue(metadata_payload["battle_dex_available"])
        self.assertEqual(metadata_payload["provider_key_mode"], "request_scoped_headers_no_server_persistence")
        self.assertEqual(metadata_payload["rate_limit_mode"], RATE_LIMIT_MODE)
        self.assertIn("Unofficial local-use advisor.", metadata_payload["unofficial_notice"])
        self.assertIn("persona_v1_built_in_registry", metadata_payload["features"])
        self.assertIn("managed_persona_public_selector_v1", metadata_payload["features"])
        self.assertNotIn(str(self.db_path), metadata.text)
        self.assertNotIn("API_KEY", metadata.text)

    def test_runtime_headers_are_not_echoed_by_metadata(self) -> None:
        headers = _native_headers()

        metadata = self.client.get("/metadata", headers=headers)

        self.assertEqual(metadata.status_code, 200)
        _assert_no_runtime_secret_leak(self, metadata.text)

    def test_explicit_native_missing_config_returns_safe_setup_failure(self) -> None:
        response = self.client.post(
            "/chat",
            headers={HEADER_RUNTIME_MODE: "native", HEADER_PROVIDER_KEY: "p4b-secret-test-key"},
            json={"message": "/species 豆丁鱼"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["analysis_type"], "runtime_failure")
        self.assertIn("Native LLM runtime is not configured", payload["answer"])
        _assert_no_runtime_secret_leak(self, response.text)

    def test_provider_config_without_runtime_mode_fails_safely(self) -> None:
        response = self.client.post(
            "/chat",
            headers={HEADER_PROVIDER_KEY: "p4b-secret-test-key"},
            json={"message": "/species 豆丁鱼"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["analysis_type"], "runtime_failure")
        _assert_no_runtime_secret_leak(self, response.text)

    def test_unsupported_runtime_mode_fails_safely_without_echoing_header_value(self) -> None:
        response = self.client.post(
            "/chat",
            headers={HEADER_RUNTIME_MODE: "p4b-secret-test-key"},
            json={"message": "/species 豆丁鱼"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["analysis_type"], "runtime_failure")
        _assert_no_runtime_secret_leak(self, response.text)

    def test_auto_missing_config_returns_redacted_degraded_setup_response(self) -> None:
        response = self.client.post(
            "/chat",
            headers={HEADER_RUNTIME_MODE: "auto", HEADER_PROVIDER_BASE_URL: "https://provider.example/v1"},
            json={"message": "/species 豆丁鱼"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["backend"], "auto_fallback_deterministic")
        self.assertEqual(payload["analysis_type"], "runtime_failure")
        _assert_no_runtime_secret_leak(self, response.text)

    def test_native_provider_base_url_rejects_non_loopback_http(self) -> None:
        response = self.client.post(
            "/chat",
            headers={
                HEADER_RUNTIME_MODE: "native",
                HEADER_PROVIDER_KEY: "p4b-secret-test-key",
                HEADER_PROVIDER_BASE_URL: "http://provider.example/v1",
                HEADER_MODEL: "p4b-test-model",
            },
            json={"message": "/species 豆丁鱼"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["analysis_type"], "runtime_failure")
        self.assertNotIn("http://provider.example/v1", response.text)
        _assert_no_runtime_secret_leak(self, response.text)

    def test_request_scoped_native_headers_use_fake_native_tool_trace_without_live_keys(self) -> None:
        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            request_native_model_factory=lambda _runtime_config: object(),
        )
        client = TestClient(create_app(advisor_service=service))

        with patch("advisor.runtime._build_native_agent", return_value=_FakeNativeAgent()):
            response = client.post(
                "/chat",
                headers=_native_headers(),
                json={"message": "分析 草 地 龙 翼 火 水 这队联防"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in payload["tool_results"])
        )
        self.assertTrue(
            any(tool["tool_name"] == "retrieve_doc_context" for tool in payload["tool_results"])
        )
        self.assertTrue(payload["evidence"])
        self.assertFalse(service._sessions)
        _assert_no_runtime_secret_leak(self, response.text)
        service.repository.close() if service.repository is not None else None

    def test_request_scoped_native_headers_handle_general_chat_without_mvp_fallback(self) -> None:
        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            request_native_model_factory=lambda _runtime_config: object(),
        )
        client = TestClient(create_app(advisor_service=service))

        with patch("advisor.runtime._build_native_agent", return_value=_FakeGeneralNativeAgent()):
            response = client.post(
                "/chat",
                headers=_native_headers(),
                json={"message": "我现在该怎么用你来优化队伍？"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["analysis_type"], "chat_response")
        self.assertNotIn("当前 MVP 只支持", payload["answer"])
        self.assertNotIn("可用命令", payload["answer"])
        _assert_no_runtime_secret_leak(self, response.text)
        service.repository.close() if service.repository is not None else None

    def test_request_scoped_native_sequence_keeps_agent_boundary_and_kv_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=Path(tmpdir) / "session.sqlite3",
            )
            client = TestClient(create_app(advisor_service=service))

            with patch("advisor.runtime._build_native_agent", return_value=_FakeP12Agent()):
                first = client.post("/chat", headers=_native_headers(), json={"message": "你好"})
                second = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": first.json()["session_id"], "message": "怎么反制圣羽翼王"},
                )
                third = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": first.json()["session_id"], "message": "什么意思"},
                )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(third.status_code, 200)
            self.assertEqual({first.json()["session_id"], second.json()["session_id"], third.json()["session_id"]}, {first.json()["session_id"]})
            second_payload = second.json()["response"]
            third_payload = third.json()["response"]
            self.assertEqual(first.json()["response"]["runtime_path"], "native_llm_terminal")
            self.assertEqual(second_payload["runtime_path"], "native_llm_terminal")
            self.assertEqual(third_payload["runtime_path"], "native_llm_terminal")
            self.assertEqual(second_payload["backend"], "pydantic_ai_native")
            self.assertTrue(any(tool["tool_name"] == "get_species_profile" for tool in second_payload["tool_results"]))
            self.assertNotIn("当前 MVP 只支持", second_payload["answer"])
            self.assertNotIn("tool_results", second_payload["answer"])
            self.assertNotIn("runtime_path", second_payload["answer"])
            self.assertIn("圣羽翼王", third_payload["answer"])
            stored_state = service.session_store.resolve(first.json()["session_id"]).store.get()
            self.assertTrue(stored_state.recent_turn_summaries)
            self.assertEqual(stored_state.recent_turn_summaries[-1].resolved_subject, "圣羽翼王")
            service.repository.close() if service.repository is not None else None

    def test_future_live_meta_question_uses_native_agent_boundary_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=Path(tmpdir) / "session.sqlite3",
            )
            client = TestClient(create_app(advisor_service=service))

            with patch("advisor.runtime._build_native_agent", return_value=_FakeGeneralNativeAgent()):
                response = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"message": "帮我预测明天官方会不会加强豆丁鱼"},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            self.assertEqual(payload["runtime_path"], "native_llm_terminal")
            self.assertEqual(payload["backend"], "pydantic_ai_native")
            service.repository.close() if service.repository is not None else None

    def test_p12_grounded_followup_survives_service_restart_from_turn_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            first_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            first_client = TestClient(create_app(advisor_service=first_service))
            with patch("advisor.runtime._build_native_agent", return_value=_FakeP12Agent()):
                grounded = first_client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"message": "怎么反制圣羽翼王"},
                )
            session_id = grounded.json()["session_id"]
            first_service.repository.close() if first_service.repository is not None else None

            restarted_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            restarted_client = TestClient(create_app(advisor_service=restarted_service))
            with patch("advisor.runtime._build_native_agent", return_value=_FakeP12Agent()):
                followup = restarted_client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": session_id, "message": "什么意思"},
                )

            self.assertEqual(grounded.status_code, 200)
            self.assertEqual(followup.status_code, 200)
            self.assertEqual(followup.json()["session_id"], session_id)
            payload = followup.json()["response"]
            self.assertEqual(payload["runtime_path"], "native_llm_terminal")
            self.assertIn("圣羽翼王", payload["answer"])
            self.assertTrue(any(tool["tool_name"] == "get_species_profile" for tool in payload["tool_results"]))
            restarted_service.repository.close() if restarted_service.repository is not None else None

    def test_request_scoped_native_runtime_reuses_protocol_state_without_persisting_orchestrator(self) -> None:
        if ModelRequest is None or UserPromptPart is None:
            self.skipTest("pydantic_ai messages are not installed")

        def protocol_message(turn: int):
            return ModelRequest(parts=[UserPromptPart(content=f"api-protocol-message-{turn}")])

        def protocol_contents(history: list[object] | None) -> list[str] | None:
            if history is None:
                return None
            contents: list[str] = []
            for message in history:
                for part in getattr(message, "parts", []):
                    content = getattr(part, "content", None)
                    if isinstance(content, str):
                        contents.append(content)
            return contents

        class _HistoryResult:
            def __init__(self, output: AdvisorResponse, messages: list[object]) -> None:
                self.output = output
                self._messages = messages

            def all_messages(self) -> list[object]:
                return list(self._messages)

        class _HistoryAgent:
            def __init__(self) -> None:
                self.seen_histories: list[list[str] | None] = []

            def run_sync(self, _message: str, **kwargs):
                self.seen_histories.append(protocol_contents(kwargs.get("message_history")))
                turn = len(self.seen_histories)
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary=f"request scoped native turn {turn}",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    ),
                    messages=[protocol_message(turn)],
                )

        fake_agent = _HistoryAgent()
        temp_session_dir = tempfile.TemporaryDirectory()
        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            session_db_path=Path(temp_session_dir.name) / "session.sqlite3",
        )
        client = TestClient(create_app(advisor_service=service))

        with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
            first = client.post(
                "/chat",
                headers=_native_headers(),
                json={"message": "我现在该怎么用你来优化队伍？"},
            )
            session_id = first.json()["session_id"]
            second = client.post(
                "/chat",
                headers=_native_headers(),
                json={"session_id": session_id, "message": "继续，不要重查"},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(fake_agent.seen_histories, [None, ["api-protocol-message-1"]])
        self.assertFalse(service._sessions)
        stored_state = service.session_store.resolve(session_id).store.get()
        self.assertEqual(protocol_contents(stored_state.native_model_messages), ["api-protocol-message-2"])
        _assert_no_runtime_secret_leak(self, first.text)
        _assert_no_runtime_secret_leak(self, second.text)
        service.repository.close() if service.repository is not None else None
        temp_session_dir.cleanup()

    def test_request_scoped_runtime_state_stores_are_evicted(self) -> None:
        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            request_runtime_session_ttl_seconds=0.01,
            max_request_runtime_sessions=1,
        )

        first_store = service._get_or_create_request_runtime_state_store("session-a")
        first_store.set(
            AdvisorSessionState(native_model_messages=["old-message"])
        )
        service._request_runtime_last_used["session-a"] = 0.0
        second_store = service._get_or_create_request_runtime_state_store("session-b")

        self.assertNotIn("session-a", service._request_runtime_state_stores)
        self.assertIn("session-b", service._request_runtime_state_stores)
        self.assertIs(second_store, service._request_runtime_state_stores["session-b"])
        service.repository.close() if service.repository is not None else None

    def test_deepseek_request_scoped_runtime_uses_longer_bounded_timeout(self) -> None:
        native_model = __import__("advisor.config", fromlist=["RocoNativeModelConfig"]).RocoNativeModelConfig(
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com",
            api_key="p4b-secret-test-key",
            reasoning_mode="enabled",
            reasoning_effort="max",
        )

        self.assertEqual(_native_timeout_for_model(native_model, default_seconds=45.0), 90.0)
        self.assertEqual(_native_timeout_for_model(object(), default_seconds=45.0), 45.0)

    def test_model_diagnostic_uses_request_scoped_headers_without_secret_leak(self) -> None:
        seen: dict[str, str | None] = {}

        def runner(config, prompt: str) -> str:
            seen["model"] = config.model_name
            seen["reasoning_mode"] = config.reasoning_mode
            seen["reasoning_effort"] = config.reasoning_effort
            seen["prompt"] = prompt
            return "ok"

        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            model_diagnostic_runner=runner,
        )
        client = TestClient(create_app(advisor_service=service))

        response = client.post(
            "/runtime/model-diagnostic",
            headers={
                **_native_headers(),
                HEADER_MODEL: "deepseek-v4-flash",
                HEADER_PROVIDER_BASE_URL: "https://api.deepseek.com",
                HEADER_REASONING_MODE: "enabled",
                HEADER_REASONING_EFFORT: "high",
            },
            json={"prompt": "ping"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["diagnostic_code"], "ok")
        self.assertEqual(response.json()["provider_family_hint"], "deepseek")
        self.assertEqual(seen["model"], "deepseek-v4-flash")
        self.assertEqual(seen["reasoning_mode"], "enabled")
        self.assertEqual(seen["reasoning_effort"], "high")
        _assert_no_runtime_secret_leak(self, response.text)
        service.repository.close() if service.repository is not None else None

    def test_model_diagnostic_invalid_model_is_classified_without_secret_leak(self) -> None:
        def runner(_config, _prompt: str) -> str:
            raise RuntimeError("404 model not found p4b-secret-test-key https://provider.example/v1")

        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            model_diagnostic_runner=runner,
        )
        client = TestClient(create_app(advisor_service=service))

        response = client.post(
            "/runtime/model-diagnostic",
            headers=_native_headers(),
            json={"prompt": "ping"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual(response.json()["diagnostic_code"], "model_id_not_accepted_by_provider")
        _assert_no_runtime_secret_leak(self, response.text)
        service.repository.close() if service.repository is not None else None

    def test_unhandled_runtime_error_path_redacts_provider_headers(self) -> None:
        app = create_app(advisor_service=self.service)

        @app.get("/runtime-boom")
        def runtime_boom() -> dict[str, str]:
            raise RuntimeError(
                "key=p4b-secret-test-key base=https://provider.example/v1 model=p4b-test-model"
            )

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/runtime-boom", headers=_native_headers())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"]["code"], "internal_error")
        _assert_no_runtime_secret_leak(self, response.text)

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_request_scoped_native_headers_use_test_model_tool_loop_without_leaking_config(self) -> None:
        assert TestModel is not None
        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            request_native_model_factory=lambda _runtime_config: TestModel(
                call_tools=["analyze_team_structure", "retrieve_doc_context"],
                custom_output_args={
                    "backend": "ignored",
                    "answer_summary": "request scoped native completed",
                    "tool_results": [],
                    "evidence_summary": [],
                    "confidence_notes": [],
                    "followup_options": [],
                },
            ),
        )
        client = TestClient(create_app(advisor_service=service))

        response = client.post(
            "/chat",
            headers=_native_headers(),
            json={"message": "分析 草 地 龙 翼 火 水 这队联防"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["backend"], "pydantic_ai_native")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in payload["tool_results"])
        )
        self.assertTrue(
            any(tool["tool_name"] == "retrieve_doc_context" for tool in payload["tool_results"])
        )
        self.assertTrue(payload["evidence"])
        _assert_no_runtime_secret_leak(self, response.text)
        self.assertFalse(service._sessions)
        service.repository.close() if service.repository is not None else None

    @unittest.skipIf(TestModel is None, "pydantic_ai is not installed")
    def test_request_scoped_auto_provider_failure_is_redacted_and_degraded(self) -> None:
        assert TestModel is not None

        class _BrokenAgent:
            def run_sync(self, *args, **kwargs) -> AdvisorResponse:
                raise RuntimeError(
                    "provider failed p4b-secret-test-key https://provider.example/v1 p4b-test-model"
                )

        service = AdvisorService(
            repository=BattleDexRepository(self.db_path),
            default_backend="deterministic",
            request_native_model_factory=lambda _runtime_config: TestModel(),
        )
        client = TestClient(create_app(advisor_service=service))

        with patch("advisor.runtime._build_native_agent", return_value=_BrokenAgent()):
            response = client.post(
                "/chat",
                headers={**_native_headers(), HEADER_RUNTIME_MODE: "auto"},
                json={"message": "分析 草 地 龙 翼 火 水 这队联防"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["backend"], "auto_fallback_deterministic")
        self.assertEqual(payload["status"], "degraded")
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in payload["tool_results"])
        )
        _assert_no_runtime_secret_leak(self, response.text)
        service.repository.close() if service.repository is not None else None

    def test_chat_deterministic_without_live_model_key_serializes_agent_response(self) -> None:
        response = self.client.post("/chat", json={"message": "/help"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["session_id"])
        agent_response = payload["response"]
        self.assertEqual(agent_response["schema_version"], "agent_response.v1")
        self.assertEqual(agent_response["backend"], "deterministic")
        self.assertEqual(agent_response["status"], "ok")
        self.assertIn("可用命令", agent_response["answer"])
        self.assertEqual(agent_response["presentation"]["reply"], agent_response["answer"])
        self.assertIn("当前问题", agent_response["presentation"]["why"])
        self.assertNotEqual(agent_response["synthesis"]["synthesized_judgement"], agent_response["answer"])
        self.assertEqual(agent_response["persona"]["persona_id"], DEFAULT_PERSONA_ID)
        self.assertEqual(agent_response["persona"]["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertTrue(agent_response["persona"]["facts_locked"])
        self.assertFalse(agent_response["persona"]["sanitized"])
        self.assertIsNone(agent_response["presentation"]["presentation_metadata"]["persona_id"])
        self.assertIn(agent_response["answer"], agent_response["persona"]["rendered_answer"])

    def test_chat_accepts_bounded_persona_selector(self) -> None:
        response = self.client.post(
            "/chat",
            json={"message": "/help", "persona_id": DEFAULT_PERSONA_ID},
        )

        self.assertEqual(response.status_code, 200)
        persona = response.json()["response"]["persona"]
        self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
        self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertEqual(persona["fact_policy"], "persona_may_not_alter_facts")
        self.assertTrue(persona["facts_locked"])
        self.assertFalse(persona["sanitized"])

    def test_chat_accepts_alternate_built_in_persona_selector(self) -> None:
        response = self.client.post(
            "/chat",
            json={"message": "/help", "persona_id": ALTERNATE_PERSONA_ID},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        persona = payload["persona"]
        self.assertEqual(persona["persona_id"], ALTERNATE_PERSONA_ID)
        self.assertEqual(persona["display_name"], ALTERNATE_PERSONA_DISPLAY_NAME)
        self.assertFalse(persona["sanitized"])
        self.assertEqual(payload["answer"], payload["presentation"]["reply"])
        self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_unsafe_api_persona_selector_sanitizes_to_default(self) -> None:
        response = self.client.post(
            "/chat",
            json={"message": "/help", "persona_id": "official_enzo"},
        )

        self.assertEqual(response.status_code, 200)
        persona = response.json()["response"]["persona"]
        self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
        self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertTrue(persona["sanitized"])
        self.assertNotIn("enzo", persona["persona_id"].casefold())
        self.assertNotIn("恩佐", persona["display_name"])

    def test_configured_materialized_persona_selector_uses_existing_persona_id_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=materialization_path,
                )
            )

            response = client.post("/chat", json={"message": "/help", "persona_id": selector})

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], "public_safe_api_runtime_persona")
            self.assertEqual(persona["display_name"], "Public Safe API Runtime Persona")
            self.assertFalse(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])
            self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_public_managed_persona_selector_object_uses_exact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, _selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=materialization_path,
                )
            )

            response = client.post(
                "/chat",
                json={
                    "message": "/help",
                    "persona_selector": {
                        "kind": "managed",
                        "persona_id": "public_safe_api_runtime_persona",
                        "version": "draft.v1",
                        "revision": 1,
                    },
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], "public_safe_api_runtime_persona")
            self.assertEqual(persona["display_name"], "Public Safe API Runtime Persona")
            self.assertFalse(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])
            self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_managed_you_know_who_runtime_artifact_is_consumed(self) -> None:
        materialization_path = ROOT / "artifacts" / "persona_runtime" / "you_know_who_minimal" / "materialized_profiles.yaml"
        self.assertTrue(materialization_path.exists())
        client = TestClient(
            create_app(
                db_path=self.db_path,
                bootstrap=False,
                managed_persona_materialization_path=materialization_path,
            )
        )

        response = client.post(
            "/chat",
            json={
                "message": "/help",
                "persona_selector": {
                    "kind": "managed",
                    "persona_id": "you_know_who",
                    "version": "draft.v1",
                    "revision": 1,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        persona = response.json()["response"]["persona"]
        self.assertEqual(persona["persona_id"], "you_know_who")
        self.assertEqual(persona["display_name"], "You know who")
        self.assertFalse(persona["sanitized"])
        self.assertTrue(persona["public_safe"])
        self.assertIn("grass_type_hostility", persona["rendering_flavor_rule_ids"])

    def test_public_selector_takes_precedence_over_legacy_persona_id(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "message": "/help",
                "persona_id": "official_enzo",
                "persona_selector": {
                    "kind": "built_in",
                    "persona_id": ALTERNATE_PERSONA_ID,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        persona = payload["persona"]
        self.assertEqual(persona["persona_id"], ALTERNATE_PERSONA_ID)
        self.assertEqual(persona["display_name"], ALTERNATE_PERSONA_DISPLAY_NAME)
        self.assertFalse(persona["sanitized"])
        self.assertEqual(payload["answer"], payload["presentation"]["reply"])

    def test_public_managed_selector_missing_version_or_revision_falls_back_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, _selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=materialization_path,
                )
            )

            response = client.post(
                "/chat",
                json={
                    "message": "/help",
                    "persona_selector": {
                        "kind": "managed",
                        "persona_id": "public_safe_api_runtime_persona",
                    },
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
            self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
            self.assertTrue(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])

    def test_bad_materialized_persona_config_fails_safely_to_builtin_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing_materialized_profiles.yaml"
            selector = make_managed_persona_selector("public_safe_api_runtime_persona", "draft.v1", 1)
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=missing_path,
                )
            )

            response = client.post("/chat", json={"message": "/help", "persona_id": selector})

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
            self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
            self.assertTrue(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])

    def test_env_configured_materialized_persona_path_enables_exact_selector(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            with patch.dict(
                "os.environ",
                {ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV: str(materialization_path)},
            ):
                client = TestClient(create_app(db_path=self.db_path, bootstrap=False))

            response = client.post("/chat", json={"message": "/help", "persona_id": selector})

            self.assertEqual(response.status_code, 200)
            payload = response.json()["response"]
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], "public_safe_api_runtime_persona")
            self.assertFalse(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])

    def test_env_configured_default_scope_enables_self_managed_internal_persona(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, selector = _write_internal_materialization_artifact(Path(tmpdir))
            with patch.dict(
                "os.environ",
                {ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV: str(materialization_path)},
            ):
                client = TestClient(create_app(db_path=self.db_path, bootstrap=False))

            response = client.post("/chat", json={"message": "/help", "persona_id": selector})

            self.assertEqual(response.status_code, 200)
            persona = response.json()["response"]["persona"]
            self.assertEqual(persona["persona_id"], "enzo_internal_nuwa_draft")
            self.assertFalse(persona["sanitized"])
            self.assertFalse(persona["public_safe"])

    def test_env_configured_public_scope_blocks_internal_persona(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, selector = _write_internal_materialization_artifact(Path(tmpdir))
            with patch.dict(
                "os.environ",
                {
                    ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV: str(materialization_path),
                    ROCO_MANAGED_PERSONA_SCOPE_ENV: "public_safe_release",
                },
            ):
                client = TestClient(create_app(db_path=self.db_path, bootstrap=False))

            response = client.post("/chat", json={"message": "/help", "persona_id": selector})

            self.assertEqual(response.status_code, 200)
            persona = response.json()["response"]["persona"]
            self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
            self.assertTrue(persona["sanitized"])

    def test_placeholder_env_path_does_not_activate_managed_personas(self) -> None:
        selector = make_managed_persona_selector("public_safe_api_runtime_persona", "draft.v1", 1)
        with patch.dict(
            "os.environ",
            {ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV: "replace-with-materialized-profile-path"},
        ):
            client = TestClient(create_app(db_path=self.db_path, bootstrap=False))

        response = client.post("/chat", json={"message": "/help", "persona_id": selector})

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["persona"]["persona_id"], DEFAULT_PERSONA_ID)
        self.assertTrue(payload["persona"]["sanitized"])
        self.assertEqual(payload["answer"], payload["presentation"]["reply"])

    def test_materialized_persona_path_is_redacted_from_metadata_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, _selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            app = create_app(
                db_path=self.db_path,
                bootstrap=False,
                managed_persona_materialization_path=materialization_path,
            )

            @app.get("/managed-persona-boom")
            def managed_persona_boom() -> dict[str, str]:
                raise RuntimeError(
                    f"path={materialization_path} env={ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV} "
                    "key=ROCO_OPENAI_API_KEY=secret"
                )

            client = TestClient(app, raise_server_exceptions=False)
            metadata = client.get("/metadata")
            response = client.get("/managed-persona-boom")

            self.assertEqual(metadata.status_code, 200)
            self.assertNotIn(str(materialization_path), metadata.text)
            self.assertNotIn(ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV, metadata.text)
            self.assertNotIn("public_safe_api_runtime_persona", metadata.text)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()["detail"]["code"], "internal_error")
            self.assertNotIn(str(materialization_path), response.text)
            self.assertNotIn(ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV, response.text)
            self.assertNotIn("ROCO_OPENAI_API_KEY", response.text)

    def test_chat_session_continuity_uses_in_memory_session_id(self) -> None:
        first = self.client.post(
            "/chat",
            json={"message": "/set-team 草 地 龙 翼 火 水"},
        )
        session_id = first.json()["session_id"]
        second = self.client.post(
            "/chat",
            json={"session_id": session_id, "message": "分析这队联防"},
        )

        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["session_id"], session_id)
        agent_response = second.json()["response"]
        self.assertEqual(agent_response["analysis_type"], "team_analysis")
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in agent_response["tool_results"])
        )

    def test_single_active_session_reconciles_stale_client_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=Path(tmpdir) / "session.sqlite3",
            )
            client = TestClient(create_app(advisor_service=service), raise_server_exceptions=False)

            first = client.post("/chat", json={"message": "/set-team 草 地 龙 翼 火 水"})
            second = client.post(
                "/chat",
                json={"session_id": "stale-desktop-session", "message": "分析这队联防"},
            )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["session_id"], first.json()["session_id"])
            self.assertEqual(second.json()["session_event"]["type"], "reconciled")
            self.assertEqual(
                second.json()["session_event"]["diagnostic"]["visible_messages"],
                "mark_stale",
            )
            self.assertEqual(second.json()["response"]["analysis_type"], "team_analysis")
            service.repository.close() if service.repository is not None else None

    def test_non_exact_clear_command_does_not_clear_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=Path(tmpdir) / "session.sqlite3",
            )
            client = TestClient(create_app(advisor_service=service))

            first = client.post("/chat", json={"message": "豆丁鱼是什么定位？"})
            second = client.post(
                "/chat",
                json={"session_id": first.json()["session_id"], "message": "/clear please"},
            )
            third = client.post(
                "/chat",
                json={"session_id": first.json()["session_id"], "message": "什么意思"},
            )

            self.assertEqual(second.status_code, 200)
            self.assertNotEqual(second.json()["response"]["runtime_path"], "static_control_response")
            self.assertNotEqual(second.json()["session_event"]["type"], "cleared")
            self.assertIn("豆丁鱼", third.json()["response"]["answer"])
            service.repository.close() if service.repository is not None else None

    def test_single_active_session_survives_service_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            first_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            first_client = TestClient(create_app(advisor_service=first_service))
            first = first_client.post("/chat", json={"message": "/set-team 草 地 龙 翼 火 水"})
            first_service.repository.close() if first_service.repository is not None else None

            restarted_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            restarted_client = TestClient(create_app(advisor_service=restarted_service))
            second = restarted_client.post("/chat", json={"message": "分析这队联防"})

            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["session_id"], first.json()["session_id"])
            self.assertEqual(second.json()["session_event"]["type"], "continued")
            self.assertEqual(second.json()["response"]["analysis_type"], "team_analysis")
            restarted_service.repository.close() if restarted_service.repository is not None else None

    def test_session_clear_archive_failure_does_not_replace_active_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            archive_path = Path(tmpdir) / "archive-as-directory"
            archive_path.mkdir()
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=ActiveSessionStore(session_db_path, archive_path=archive_path),
            )
            client = TestClient(create_app(advisor_service=service), raise_server_exceptions=False)
            first = client.post("/chat", json={"message": "/set-team 草 地 龙 翼 火 水"})
            failed_clear = client.post("/session/clear", json={"reason": "test_archive_failure"})
            second = client.post(
                "/chat",
                json={"session_id": first.json()["session_id"], "message": "分析这队联防"},
            )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(failed_clear.status_code, 500)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["response"]["analysis_type"], "team_analysis")
            service.repository.close() if service.repository is not None else None

    def test_session_clear_endpoint_archives_summary_without_secret_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            archive_path = Path(tmpdir) / "session_archive.jsonl"
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=ActiveSessionStore(session_db_path, archive_path=archive_path),
            )
            client = TestClient(create_app(advisor_service=service))
            first = client.post("/chat", json={"message": "/set-team 草 地 龙 翼 火 水"})
            cleared = client.post("/session/clear", json={"reason": "user_clear"})

            self.assertEqual(first.status_code, 200)
            self.assertEqual(cleared.status_code, 200)
            self.assertEqual(cleared.json()["session_event"]["type"], "cleared")
            self.assertEqual(
                cleared.json()["session_event"]["diagnostic"]["visible_messages"],
                "clear",
            )
            archive_text = archive_path.read_text(encoding="utf-8")
            self.assertIn('"summary"', archive_text)
            self.assertNotIn("provider", archive_text.casefold())
            self.assertNotIn("api_key", archive_text.casefold())
            service.repository.close() if service.repository is not None else None

    def test_session_store_fails_closed_without_explicit_dev_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            blocked_parent = Path(tmpdir) / "not-a-directory"
            blocked_parent.write_text("blocked", encoding="utf-8")

            with self.assertRaises(Exception):
                ActiveSessionStore(blocked_parent / "session.sqlite3")

            fallback = ActiveSessionStore(
                blocked_parent / "session.sqlite3",
                allow_in_memory_fallback=True,
            )

            self.assertTrue(fallback.using_in_memory_fallback)
            self.assertEqual(fallback.resolve(None).event.diagnostic["archive"], "disabled")

    def test_native_history_restores_across_service_restart(self) -> None:
        if ModelRequest is None or UserPromptPart is None:
            self.skipTest("pydantic_ai messages are not installed")

        class _HistoryResult:
            def __init__(self, output: AdvisorResponse, messages: list[object]) -> None:
                self.output = output
                self._messages = messages

            def all_messages(self) -> list[object]:
                return list(self._messages)

        class _HistoryAgent:
            def __init__(self) -> None:
                self.seen_histories: list[list[str] | None] = []

            def run_sync(self, _message: str, **kwargs):
                self.seen_histories.append(_protocol_contents(kwargs.get("message_history")))
                turn = len(self.seen_histories)
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary=f"native restart turn {turn}",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    ),
                    messages=[_protocol_message(f"restart-message-{turn}")],
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            first_agent = _HistoryAgent()
            first_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            first_client = TestClient(create_app(advisor_service=first_service))
            with patch("advisor.runtime._build_native_agent", return_value=first_agent):
                first = first_client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"message": "第一轮 native"},
                )
            session_id = first.json()["session_id"]
            first_service.repository.close() if first_service.repository is not None else None

            second_agent = _HistoryAgent()
            restarted_service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            restarted_client = TestClient(create_app(advisor_service=restarted_service))
            with patch("advisor.runtime._build_native_agent", return_value=second_agent):
                second = restarted_client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": session_id, "message": "第二轮 native"},
                )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second_agent.seen_histories, [["restart-message-1"]])
            restarted_service.repository.close() if restarted_service.repository is not None else None

    def test_native_fingerprint_mismatch_drops_history_with_controlled_event(self) -> None:
        if ModelRequest is None or UserPromptPart is None:
            self.skipTest("pydantic_ai messages are not installed")

        class _HistoryResult:
            def __init__(self, output: AdvisorResponse) -> None:
                self.output = output

            def all_messages(self) -> list[object]:
                return [_protocol_message("fresh-after-mismatch")]

        class _HistoryAgent:
            def __init__(self) -> None:
                self.seen_histories: list[list[str] | None] = []

            def run_sync(self, _message: str, **kwargs):
                self.seen_histories.append(_protocol_contents(kwargs.get("message_history")))
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary="native mismatch handled",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    )
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            session_store = ActiveSessionStore(Path(tmpdir) / "session.sqlite3")
            resolution = session_store.resolve(None)
            resolution.store.set(
                AdvisorSessionState(
                    native_model_messages=[_protocol_message("old-history")],
                    native_runtime_fingerprint="old-runtime-fingerprint",
                )
            )
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=session_store,
            )
            client = TestClient(create_app(advisor_service=service))
            fake_agent = _HistoryAgent()
            with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
                response = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": resolution.session_id, "message": "继续"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(fake_agent.seen_histories, [None])
            self.assertEqual(response.json()["session_event"]["reason"], "native_runtime_fingerprint_mismatch")
            self.assertEqual(
                response.json()["session_event"]["diagnostic"]["visible_messages"],
                "mark_stale",
            )
            service.repository.close() if service.repository is not None else None

    def test_invalid_serialized_native_history_drops_with_controlled_event(self) -> None:
        if ModelRequest is None or UserPromptPart is None:
            self.skipTest("pydantic_ai messages are not installed")

        class _HistoryResult:
            def __init__(self, output: AdvisorResponse) -> None:
                self.output = output

            def all_messages(self) -> list[object]:
                return [_protocol_message("fresh-after-invalid")]

        class _HistoryAgent:
            def run_sync(self, _message: str, **kwargs):
                self.seen_history = _protocol_contents(kwargs.get("message_history"))
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary="native invalid handled",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    )
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            session_store = ActiveSessionStore(session_db_path)
            resolution = session_store.resolve(None)
            with sqlite3.connect(session_db_path) as connection:
                connection.execute(
                    """
                    UPDATE session_state
                    SET native_messages_json = ?,
                        native_messages_schema_version = ?,
                        native_runtime_fingerprint = ?
                    WHERE session_id = ?
                    """,
                    (
                        "{not-json",
                        "pydantic_ai_model_messages.v1",
                        _native_runtime_fingerprint(_native_test_config()),
                        resolution.session_id,
                    ),
                )
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=session_store,
            )
            client = TestClient(create_app(advisor_service=service))
            fake_agent = _HistoryAgent()
            with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
                response = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": resolution.session_id, "message": "继续"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertIsNone(fake_agent.seen_history)
            self.assertEqual(response.json()["session_event"]["reason"], "native_history_deserialize_failed")
            service.repository.close() if service.repository is not None else None

    def test_invalid_serialized_session_state_drops_with_controlled_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            session_store = ActiveSessionStore(session_db_path)
            resolution = session_store.resolve(None)
            with sqlite3.connect(session_db_path) as connection:
                connection.execute(
                    """
                    UPDATE session_state
                    SET state_json = ?
                    WHERE session_id = ?
                    """,
                    ("{not-json", resolution.session_id),
                )
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=session_store,
            )
            client = TestClient(create_app(advisor_service=service), raise_server_exceptions=False)

            response = client.post(
                "/chat",
                json={"session_id": resolution.session_id, "message": "你好"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["session_id"], resolution.session_id)
            self.assertEqual(response.json()["session_event"]["reason"], "session_state_deserialize_failed")
            self.assertEqual(
                response.json()["session_event"]["diagnostic"]["visible_messages"],
                "mark_stale",
            )
            self.assertNotIn("{not-json", response.text)
            service.repository.close() if service.repository is not None else None

    def test_context_pressure_rolls_over_before_native_call(self) -> None:
        if ModelRequest is None or UserPromptPart is None:
            self.skipTest("pydantic_ai messages are not installed")

        class _HistoryResult:
            def __init__(self, output: AdvisorResponse) -> None:
                self.output = output

            def all_messages(self) -> list[object]:
                return [_protocol_message("fresh-after-rollover")]

        class _HistoryAgent:
            def __init__(self) -> None:
                self.seen_histories: list[list[str] | None] = []

            def run_sync(self, _message: str, **kwargs):
                self.seen_histories.append(_protocol_contents(kwargs.get("message_history")))
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary="native rollover handled",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    )
                )

        with tempfile.TemporaryDirectory() as tmpdir, patch.dict(
            "os.environ",
            {"ROCO_SESSION_NATIVE_HISTORY_MAX_BYTES": "10"},
        ):
            session_store = ActiveSessionStore(Path(tmpdir) / "session.sqlite3")
            resolution = session_store.resolve(None)
            resolution.store.set(
                AdvisorSessionState(
                    native_model_messages=[_protocol_message("history-too-large")],
                    native_runtime_fingerprint=_native_runtime_fingerprint(_native_test_config()),
                )
            )
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_store=session_store,
            )
            client = TestClient(create_app(advisor_service=service))
            fake_agent = _HistoryAgent()
            with patch("advisor.runtime._build_native_agent", return_value=fake_agent):
                response = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"session_id": resolution.session_id, "message": "继续"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response.json()["session_id"], resolution.session_id)
            self.assertEqual(response.json()["session_event"]["type"], "rolled_over")
            self.assertEqual(
                response.json()["session_event"]["diagnostic"]["visible_messages"],
                "clear",
            )
            self.assertEqual(fake_agent.seen_histories, [None])
            service.repository.close() if service.repository is not None else None

    def test_sqlite_session_store_does_not_persist_runtime_secrets(self) -> None:
        class _HistoryResult:
            def __init__(self, output: AdvisorResponse) -> None:
                self.output = output

            def all_messages(self) -> list[object]:
                return []

        class _HistoryAgent:
            def run_sync(self, _message: str, **_kwargs):
                return _HistoryResult(
                    AdvisorResponse(
                        backend="pydantic_ai_native",
                        answer_summary="secret leak check",
                        tool_results=[],
                        evidence_summary=[],
                        confidence_notes=[],
                        followup_options=[],
                    )
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            session_db_path = Path(tmpdir) / "session.sqlite3"
            service = AdvisorService(
                repository=BattleDexRepository(self.db_path),
                default_backend="deterministic",
                session_db_path=session_db_path,
            )
            client = TestClient(create_app(advisor_service=service))
            with patch("advisor.runtime._build_native_agent", return_value=_HistoryAgent()):
                response = client.post(
                    "/chat",
                    headers=_native_headers(),
                    json={"message": "secret leak check"},
                )

            self.assertEqual(response.status_code, 200)
            db_bytes = session_db_path.read_bytes()
            self.assertNotIn(b"p4b-secret-test-key", db_bytes)
            self.assertNotIn(b"https://provider.example/v1", db_bytes)
            service.repository.close() if service.repository is not None else None

    def test_team_analyze_returns_agent_response(self) -> None:
        response = self.client.post(
            "/team/analyze",
            json={
                "team": [
                    {"primary_type": "草"},
                    {"primary_type": "地"},
                    {"primary_type": "龙"},
                    {"primary_type": "翼"},
                    {"primary_type": "火"},
                    {"primary_type": "水"},
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schema_version"], "agent_response.v1")
        self.assertEqual(payload["analysis_type"], "team_analysis")
        self.assertEqual(payload["backend"], "deterministic")
        self.assertEqual(payload["persona"]["persona_id"], DEFAULT_PERSONA_ID)
        self.assertEqual(payload["answer"], payload["presentation"]["reply"])
        self.assertNotEqual(payload["answer"], payload["synthesis"]["synthesized_judgement"])
        self.assertTrue(payload["evidence"])
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in payload["tool_results"])
        )

    def test_team_analyze_configured_materialized_persona_selector_matches_chat_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=materialization_path,
                )
            )

            response = client.post(
                "/team/analyze",
                json={
                    "persona_id": selector,
                    "team": [
                        {"primary_type": "草"},
                        {"primary_type": "地"},
                        {"primary_type": "龙"},
                        {"primary_type": "翼"},
                        {"primary_type": "火"},
                        {"primary_type": "水"},
                    ],
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], "public_safe_api_runtime_persona")
            self.assertEqual(persona["display_name"], "Public Safe API Runtime Persona")
            self.assertFalse(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])
            self.assertNotEqual(payload["answer"], payload["synthesis"]["synthesized_judgement"])
            self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_team_analyze_public_managed_selector_object_matches_chat_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization_path, _selector = _write_public_safe_materialization_artifact(Path(tmpdir))
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=materialization_path,
                )
            )

            response = client.post(
                "/team/analyze",
                json={
                    "persona_selector": {
                        "kind": "managed",
                        "persona_id": "public_safe_api_runtime_persona",
                        "version": "draft.v1",
                        "revision": 1,
                    },
                    "team": [
                        {"primary_type": "草"},
                        {"primary_type": "地"},
                        {"primary_type": "龙"},
                        {"primary_type": "翼"},
                        {"primary_type": "火"},
                        {"primary_type": "水"},
                    ],
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], "public_safe_api_runtime_persona")
            self.assertEqual(persona["display_name"], "Public Safe API Runtime Persona")
            self.assertFalse(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])
            self.assertNotEqual(payload["answer"], payload["synthesis"]["synthesized_judgement"])
            self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_team_analyze_bad_managed_config_falls_back_without_changing_canonical_reply(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing_materialized_profiles.yaml"
            selector = make_managed_persona_selector("public_safe_api_runtime_persona", "draft.v1", 1)
            client = TestClient(
                create_app(
                    db_path=self.db_path,
                    bootstrap=False,
                    managed_persona_materialization_path=missing_path,
                )
            )

            response = client.post(
                "/team/analyze",
                json={
                    "persona_id": selector,
                    "team": [
                        {"primary_type": "草"},
                        {"primary_type": "地"},
                        {"primary_type": "龙"},
                        {"primary_type": "翼"},
                        {"primary_type": "火"},
                        {"primary_type": "水"},
                    ],
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            persona = payload["persona"]
            self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
            self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
            self.assertTrue(persona["sanitized"])
            self.assertEqual(payload["answer"], payload["presentation"]["reply"])
            self.assertIn(payload["answer"], persona["rendered_answer"])

    def test_team_analyze_unsafe_persona_selector_falls_back_to_public_safe_default(self) -> None:
        response = self.client.post(
            "/team/analyze",
            json={
                "persona_id": "official_enzo",
                "team": [
                    {"primary_type": "草"},
                    {"primary_type": "地"},
                    {"primary_type": "龙"},
                    {"primary_type": "翼"},
                    {"primary_type": "火"},
                    {"primary_type": "水"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        persona = payload["persona"]
        self.assertEqual(persona["persona_id"], DEFAULT_PERSONA_ID)
        self.assertEqual(persona["display_name"], DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertTrue(persona["sanitized"])
        self.assertEqual(payload["answer"], payload["presentation"]["reply"])
        self.assertNotIn("enzo", persona["persona_id"].casefold())
        self.assertNotIn("恩佐", persona["display_name"])

    def test_species_search_and_profile(self) -> None:
        search = self.client.get("/species/search", params={"q": "豆丁鱼"})

        self.assertEqual(search.status_code, 200)
        results = search.json()["results"]
        self.assertTrue(results)
        species_id = results[0]["species_id"]
        profile = self.client.get(f"/species/{species_id}")

        self.assertEqual(profile.status_code, 200)
        profile_payload = profile.json()["profile"]
        self.assertEqual(profile_payload["species_id"], species_id)
        self.assertEqual(profile_payload["display_name"], "豆丁鱼")
        self.assertIn("base_stats", profile_payload)
        self.assertNotIn(str(self.db_path), profile.text)

    def test_species_search_exposes_regional_form_for_disambiguation(self) -> None:
        search = self.client.get("/species/search", params={"q": "皇家狮鹫"})

        self.assertEqual(search.status_code, 200)
        results = search.json()["results"]
        royal_griffins = [item for item in results if item["display_name"] == "皇家狮鹫"]
        self.assertGreaterEqual(len(royal_griffins), 2)
        self.assertIn(
            "崖间地的样子",
            {item.get("regional_form_name") for item in royal_griffins},
        )
        self.assertIn(
            "高山地的样子",
            {item.get("regional_form_name") for item in royal_griffins},
        )

    def test_species_search_diversifies_broad_single_character_matches(self) -> None:
        search = self.client.get("/species/search", params={"q": "圣", "limit": 12})

        self.assertEqual(search.status_code, 200)
        results = search.json()["results"]
        names = [item["display_name"] for item in results]
        self.assertIn("圣羽翼王", names)
        self.assertLessEqual(names[:10].count("圣代甜甜"), 1)

    def test_species_search_ignores_regional_form_suffix_text(self) -> None:
        search = self.client.get("/species/search", params={"q": "水", "limit": 20})

        self.assertEqual(search.status_code, 200)
        names = [item["display_name"] for item in search.json()["results"]]
        self.assertNotIn("地鼠", names)
        self.assertNotIn("遁鼠", names)
        self.assertNotIn("遁地鼠", names)

        suffix_only = self.client.get("/species/search", params={"q": "枯水", "limit": 20})

        self.assertEqual(suffix_only.status_code, 200)
        self.assertEqual(suffix_only.json()["results"], [])

    def test_team_builder_species_search_filters_incomplete_entries_and_allows_50(self) -> None:
        regular = self.client.get("/species/search", params={"q": "圣", "limit": 20})
        team_builder = self.client.get(
            "/species/search",
            params={"q": "圣", "limit": 50, "usage": "team_builder"},
        )

        self.assertEqual(regular.status_code, 200)
        self.assertEqual(team_builder.status_code, 200)
        regular_names = [item["display_name"] for item in regular.json()["results"]]
        team_names = [item["display_name"] for item in team_builder.json()["results"]]
        self.assertIn("圣光迪莫", regular_names)
        self.assertNotIn("圣光迪莫", team_names)
        self.assertIn("圣羽翼王", team_names)
        self.assertIn("圣剑-X", team_names)
        first_duplicate_index = next(
            index
            for index, name in enumerate(team_names)
            if name in team_names[:index]
        )
        self.assertEqual(first_duplicate_index, len(set(team_names)))

        broader = self.client.get(
            "/species/search",
            params={"q": "小", "limit": 50, "usage": "team_builder"},
        )

        self.assertEqual(broader.status_code, 200)
        broader_names = [item["display_name"] for item in broader.json()["results"]]
        self.assertGreater(len(broader_names), 20)
        self.assertIn("小狮鹫", broader_names)

    def test_species_moves_endpoint_returns_available_moves_without_paths(self) -> None:
        profile = self.service.repository.get_species_profile("豆丁鱼")
        assert profile is not None

        response = self.client.get(f"/species/{profile.species_id}/moves")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["species_id"], profile.species_id)
        self.assertTrue(payload["moves"])
        self.assertTrue(all(move["move_name"] for move in payload["moves"]))
        self.assertNotIn(str(self.db_path), response.text)

    def test_chat_accepts_database_grounded_team_context_attachment(self) -> None:
        context = self._team_context_payload("豆丁鱼")

        response = self.client.post(
            "/chat",
            json={
                "message": "分析这队联防",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["response"]
        self.assertEqual(payload["analysis_type"], "team_analysis")
        self.assertTrue(
            any(tool["tool_name"] == "analyze_team_structure" for tool in payload["tool_results"])
        )
        self.assertIn("豆丁鱼", payload["answer"])
        self.assertNotIn(str(self.db_path), response.text)

    def test_chat_invalid_team_context_species_blocks_only_team_dependent_turn(self) -> None:
        context = self._team_context_payload("豆丁鱼")
        context["slots"][0]["species_id"] = "not-a-real-species-id"

        response = self.client.post(
            "/chat",
            json={
                "message": "分析这队联防",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(payload["response"]["runtime_path"], "deterministic_degraded_fallback")
        self.assertIn("修正队伍", payload["response"]["answer"])
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["code"],
            "invalid_team_context_species",
        )
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "blocked_team_dependent_turn",
        )
        self.assertNotIn(str(self.db_path), response.text)

    def test_chat_invalid_team_context_move_is_ignored_for_unrelated_chat(self) -> None:
        context = self._team_context_payload("豆丁鱼")
        context["slots"][0]["selected_moves"][0]["move_id"] = "not-a-real-move-id"

        response = self.client.post(
            "/chat",
            json={
                "message": "你好",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["code"],
            "invalid_team_context_move",
        )
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "ignored_for_unrelated_chat",
        )
        self.assertNotIn(str(self.db_path), response.text)

    def test_chat_invalid_team_context_shape_blocks_only_team_dependent_turn(self) -> None:
        context = self._team_context_payload("豆丁鱼")
        context["slots"] = [context["slots"][0], {**context["slots"][0]}]

        response = self.client.post(
            "/chat",
            json={
                "message": "分析这队联防",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "blocked_team_dependent_turn",
        )

    def test_chat_invalid_team_context_shape_is_ignored_for_unrelated_chat(self) -> None:
        context = self._team_context_payload("豆丁鱼")
        context["slots"] = [context["slots"][0], {**context["slots"][0]}]

        response = self.client.post(
            "/chat",
            json={
                "message": "你好",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "ignored_for_unrelated_chat",
        )

    def test_chat_multiple_invalid_context_attachments_are_ignored_for_unrelated_chat(self) -> None:
        first_context = self._team_context_payload("豆丁鱼")
        second_context = self._team_context_payload("豆丁鱼")

        response = self.client.post(
            "/chat",
            json={
                "message": "你好",
                "context_attachments": [first_context, second_context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "ignored_for_unrelated_chat",
        )

    def test_chat_invalid_team_context_value_blocks_only_team_dependent_turn(self) -> None:
        context = self._team_context_payload("豆丁鱼")
        context["slots"][0]["individual_value_bonuses"][0]["value"] = 11

        response = self.client.post(
            "/chat",
            json={
                "message": "分析这队联防",
                "context_attachments": [context],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["response"]["analysis_type"], "runtime_failure")
        self.assertEqual(
            payload["session_event"]["diagnostic"]["attachment_validation"]["action"],
            "blocked_team_dependent_turn",
        )

    def test_error_responses_are_bounded_and_redacted(self) -> None:
        missing_species = self.client.get("/species/not-a-real-species-id")
        invalid_team = self.client.post("/team/analyze", json={"team": []})
        unavailable_client = TestClient(
            create_app(
                advisor_service=AdvisorService(
                    repository=None,
                    default_backend="deterministic",
                    startup_error="battle_dex_unavailable",
                )
            )
        )
        unavailable = unavailable_client.get("/species/search", params={"q": "豆丁鱼"})

        self.assertEqual(missing_species.status_code, 404)
        self.assertEqual(missing_species.json()["detail"]["code"], "species_not_found")
        self.assertEqual(invalid_team.status_code, 422)
        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(unavailable.json()["detail"]["code"], "battle_dex_unavailable")
        combined = missing_species.text + invalid_team.text + unavailable.text
        self.assertNotIn(str(self.db_path), combined)
        self.assertNotIn("ROCO_OPENAI_API_KEY", combined)
        self.assertNotIn("test-key", combined)

    def _team_context_payload(self, species_query: str) -> dict[str, object]:
        profile = self.service.repository.get_species_profile(species_query)
        assert profile is not None
        moves = [
            move
            for move in self.service.repository.get_species_available_moves(profile.species_id, limit=20)
            if move.move_id
        ]
        self.assertTrue(moves)
        move = moves[0]
        return {
            "kind": "team_context",
            "schema_version": "team_context.v1",
            "source": "team_builder",
            "team_id": "test-active-team",
            "active": True,
            "slots": [
                {
                    "slot_index": 1,
                    "species_id": profile.species_id,
                    "display_name": profile.display_name,
                    "primary_type": profile.primary_type,
                    "secondary_type": profile.secondary_type,
                    "fixed_ability": (
                        {
                            "ability_name": profile.ability_name,
                            "effect_text": profile.ability_effect_text,
                        }
                        if profile.ability_name
                        else None
                    ),
                    "selected_moves": [
                        {
                            "move_id": move.move_id,
                            "move_name": move.move_name,
                            "access_channel": move.access_channel,
                            "move_type": move.move_type,
                            "category_raw": move.category_raw,
                        }
                    ],
                    "nature": {
                        "label": "保守",
                        "plus_stat": "spa",
                        "minus_stat": "atk",
                    },
                    "individual_value_bonuses": [
                        {"stat": "spa", "value": 8},
                    ],
                    "notes": "api test context",
                }
            ],
        }


def argparse_namespace(**kwargs: object):
    class _Namespace:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

    return _Namespace(**kwargs)


def _native_headers() -> dict[str, str]:
    return {
        HEADER_RUNTIME_MODE: "native",
        HEADER_PROVIDER_KEY: "p4b-secret-test-key",
        HEADER_PROVIDER_BASE_URL: "https://provider.example/v1",
        HEADER_MODEL: "p4b-test-model",
    }


def _native_test_config() -> RocoNativeModelConfig:
    return RocoNativeModelConfig(
        model_name="p4b-test-model",
        base_url="https://provider.example/v1",
        api_key="p4b-secret-test-key",
    )


def _protocol_message(content: str):
    if ModelRequest is None or UserPromptPart is None:
        raise RuntimeError("pydantic_ai messages are not installed")
    return ModelRequest(parts=[UserPromptPart(content=content)])


def _protocol_contents(history: list[object] | None) -> list[str] | None:
    if history is None:
        return None
    contents: list[str] = []
    for message in history:
        for part in getattr(message, "parts", []):
            content = getattr(part, "content", None)
            if isinstance(content, str):
                contents.append(content)
    return contents


def _assert_no_runtime_secret_leak(testcase: unittest.TestCase, text: str) -> None:
    for forbidden in (
        "p4b-secret-test-key",
        "https://provider.example/v1",
        "p4b-test-model",
        "X-Roco-Provider-Key",
        "X-Roco-Provider-Base-Url",
        "X-Roco-Model",
        "X-Roco-Reasoning-Mode",
        "X-Roco-Reasoning-Effort",
        "ROCO_OPENAI_API_KEY",
    ):
        testcase.assertNotIn(forbidden, text)


class _FakeNativeAgent:
    def run_sync(self, message: str, *, deps, model, instructions: str, **_kwargs):
        slots = deps.route.team_slots
        report = deps.analyzer.analyze(slots)
        deps.trace.team_structure_report = report
        deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="analyze_team_structure",
                summary=f"structural_score={report.structural_score:.3f}",
                payload={"structural_score": report.structural_score},
            )
        )
        deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary="retrieved 1 approved doc snippets",
                payload={"topics": ["test_context"]},
            )
        )
        deps.trace.add_evidence(
            AdvisorEvidenceItem(
                source_type=SourceType.ENGINE,
                source_label="battle_engine.team_structure",
                confidence=ConfidenceTier.CONFIRMED,
                content=report.evidence[0] if report.evidence else "engine evidence",
                retrieval_reason="fake_native_tool_trace",
            )
        )
        return _FakeNativeResult(
            AdvisorResponse(
                backend="pydantic_ai_native",
                answer_summary="fake native tool loop completed with approved tools",
                tool_results=list(deps.trace.tool_results),
                evidence_summary=list(deps.trace.evidence_summary),
                confidence_notes=["confirmed by fake native approved tool trace"],
                followup_options=[],
            )
        )


class _FakeNativeResult:
    def __init__(self, output: AdvisorResponse) -> None:
        self.output = output


class _FakeGeneralNativeAgent:
    def run_sync(self, message: str, *, deps, model, instructions: str, **_kwargs):
        return _FakeNativeResult(
            AdvisorResponse(
                backend="pydantic_ai_native",
                answer_summary="先告诉我你的目标、已有队伍或想保留的精灵，我会再决定是否调用结构分析或图鉴工具。",
                tool_results=[],
                evidence_summary=[],
                confidence_notes=[],
                followup_options=[],
            )
        )


class _FakeP12Agent:
    def run_sync(self, message: str, *, deps, model, instructions: str, **_kwargs):
        if "圣羽翼王" in message and "Draft deterministic digest" in message:
            answer = (
                "圣羽翼王这里要按有条件威胁处理：先看它的速度/先手节奏，再根据已确认技能池决定换入和压迫轴。"
                if "怎么反制" in message
                else "刚才说的是：圣羽翼王不是让你背规则，而是先拆它的威胁来源，再决定怎么换入和反压。"
            )
        else:
            answer = "我在，直接说你的队伍目标或想处理的精灵，我会决定是否需要查工具。"
        return _FakeNativeResult(
            AdvisorResponse(
                backend="pydantic_ai_native",
                answer_summary=answer,
                tool_results=[],
                evidence_summary=[],
                confidence_notes=[],
                followup_options=[],
            )
        )


def _write_public_safe_materialization_artifact(root: Path) -> tuple[Path, str]:
    ledger_path = root / "ledger.yaml"
    bundle = generate_internal_nuwa_distillation_bundle(output_root=root / "source")
    doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
    doctrine["persona_id"] = "public_safe_api_runtime_persona"
    doctrine["display_name"] = "Public Safe API Runtime Persona"
    doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
    bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
    ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
    candidate = build_persona_registry_candidate(ingestion_result)
    record = write_persona_registry_record(ledger_path, candidate, ingestion_result)
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
    )
    projection = build_persona_activation_registry_projection(activation_report)
    materialization = materialize_persona_projection_profiles(projection)
    output_path = root / "materialized_profiles.yaml"
    write_persona_projection_profile_materialization(materialization, output_path)
    selector = make_managed_persona_selector(record.persona_id, record.version, record.revision)
    return output_path, selector


def _write_internal_materialization_artifact(root: Path) -> tuple[Path, str]:
    ledger_path = root / "ledger.yaml"
    bundle = generate_internal_nuwa_distillation_bundle(output_root=root / "source")
    ingestion_result = ingest_persona_source_bundle(bundle)
    candidate = build_persona_registry_candidate(ingestion_result)
    record = write_persona_registry_record(ledger_path, candidate, ingestion_result)
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    )
    projection = build_persona_activation_registry_projection(activation_report)
    materialization = materialize_persona_projection_profiles(projection)
    output_path = root / "internal_materialized_profiles.yaml"
    write_persona_projection_profile_materialization(materialization, output_path)
    selector = make_managed_persona_selector(record.persona_id, record.version, record.revision)
    return output_path, selector


if __name__ == "__main__":
    unittest.main()
