from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from advisor.battle_dex import BattleDexRepository
from advisor.contracts import AdvisorEvidenceItem, AdvisorResponse, AdvisorToolResult, SourceType
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
from api.main import ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV, create_app
from api.release import RATE_LIMIT_MODE, RELEASE_STAGE, SERVICE_NAME
from api.runtime_headers import (
    HEADER_MODEL,
    HEADER_PROVIDER_BASE_URL,
    HEADER_PROVIDER_KEY,
    HEADER_RUNTIME_MODE,
)
from api.services.advisor_service import AdvisorService
from reporting.contracts import ConfidenceTier
from tools.import_battle_dex_sqlite import write_sqlite

try:
    from pydantic_ai.models.test import TestModel
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    TestModel = None


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
        cls.service = AdvisorService(repository=repository, default_backend="deterministic")
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
        self.assertIn("答复", agent_response["answer"])
        self.assertEqual(agent_response["presentation"]["reply"], agent_response["answer"])
        self.assertIn("基于已锁定的工具证据", agent_response["presentation"]["why"])
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


def _assert_no_runtime_secret_leak(testcase: unittest.TestCase, text: str) -> None:
    for forbidden in (
        "p4b-secret-test-key",
        "https://provider.example/v1",
        "p4b-test-model",
        "X-Roco-Provider-Key",
        "X-Roco-Provider-Base-Url",
        "X-Roco-Model",
        "ROCO_OPENAI_API_KEY",
    ):
        testcase.assertNotIn(forbidden, text)


class _FakeNativeAgent:
    def run_sync(self, message: str, *, deps, model, instructions: str):
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


if __name__ == "__main__":
    unittest.main()
