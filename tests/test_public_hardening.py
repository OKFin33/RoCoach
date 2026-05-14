from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from advisor.battle_dex import BattleDexRepository
from advisor.config import load_native_model_config
from advisor.conversation_cli import resolve_backend_config
from api.main import (
    ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV,
    ROCO_MANAGED_PERSONA_SCOPE_ENV,
    create_app,
    managed_persona_materialization_path_from_env,
    managed_persona_scope_from_env,
)
from agent_core.contracts import PersonaRuntimeActivationScope
from api.release import API_VERSION, RATE_LIMIT_MODE, RELEASE_STAGE, SERVICE_NAME, UNOFFICIAL_NOTICE
from api.services.advisor_service import AdvisorService
from tools.import_battle_dex_sqlite import write_sqlite


ROOT = Path(__file__).resolve().parent.parent
IMPORTER_RUN_DIR = ROOT / "data" / "importer_runs" / "2026-04-14Tpolicy_b_importer_dry_run"
SCHEMA_PATH = ROOT / "specs" / "battle_dex_sqlite_schema_v1.sql"


class PublicHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls._tmpdir.name) / "public_hardening.sqlite"
        write_sqlite(
            argparse_namespace(
                importer_run_dir=IMPORTER_RUN_DIR,
                db_path=cls.db_path,
                schema_path=SCHEMA_PATH,
                write_run_id="public_hardening_run",
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

    def test_health_and_metadata_are_release_coherent(self) -> None:
        health = self.client.get("/health")
        metadata = self.client.get("/metadata")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["service_name"], SERVICE_NAME)
        self.assertEqual(health.json()["release_stage"], RELEASE_STAGE)
        self.assertEqual(health.json()["api_version"], API_VERSION)

        self.assertEqual(metadata.status_code, 200)
        payload = metadata.json()
        self.assertEqual(payload["service_name"], SERVICE_NAME)
        self.assertEqual(payload["release_stage"], RELEASE_STAGE)
        self.assertEqual(payload["api_version"], API_VERSION)
        self.assertEqual(payload["rate_limit_mode"], RATE_LIMIT_MODE)
        self.assertEqual(payload["unofficial_notice"], UNOFFICIAL_NOTICE)
        self.assertIn("release_hardening_p0f", payload["features"])

    def test_unhandled_failures_stay_bounded_and_redacted(self) -> None:
        app = create_app(advisor_service=self.service)

        @app.get("/boom")
        def boom() -> dict[str, str]:
            raise RuntimeError("db=/tmp/demo.sqlite key=test-key env=ROCO_OPENAI_API_KEY=secret")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/boom")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"]["code"], "internal_error")
        self.assertNotIn("demo.sqlite", response.text)
        self.assertNotIn("test-key", response.text)
        self.assertNotIn("ROCO_OPENAI_API_KEY", response.text)

    def test_placeholder_sample_env_is_not_treated_as_valid_native_config(self) -> None:
        sample_env_path = ROOT / ".env.example"

        config = load_native_model_config(env_path=sample_env_path)
        backend, model_name, native_model, auto_selected = resolve_backend_config(
            requested_backend="auto",
            env_file=sample_env_path,
            model_name=None,
        )

        self.assertIsNone(config)
        self.assertEqual(backend, "deterministic")
        self.assertIsNone(model_name)
        self.assertIsNone(native_model)
        self.assertTrue(auto_selected)

    def test_managed_persona_sample_env_placeholder_is_inert(self) -> None:
        sample_env_path = ROOT / ".env.example"
        env_values = {}
        for line in sample_env_path.read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip()

        self.assertEqual(
            env_values[ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV],
            "replace-with-materialized-profile-path",
        )
        self.assertIsNone(managed_persona_materialization_path_from_env(env_values))
        self.assertEqual(
            env_values[ROCO_MANAGED_PERSONA_SCOPE_ENV],
            PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
        )
        self.assertEqual(
            managed_persona_scope_from_env(env_values),
            PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
        )

    def test_managed_persona_scope_env_defaults_to_internal_and_supports_public_gate(self) -> None:
        self.assertEqual(
            managed_persona_scope_from_env({}),
            PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
        )
        self.assertEqual(
            managed_persona_scope_from_env({ROCO_MANAGED_PERSONA_SCOPE_ENV: "public_safe_release"}),
            PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
        )
        self.assertEqual(
            managed_persona_scope_from_env({ROCO_MANAGED_PERSONA_SCOPE_ENV: "garbage"}),
            PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
        )


def argparse_namespace(**kwargs: object):
    class _Namespace:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

    return _Namespace(**kwargs)


if __name__ == "__main__":
    unittest.main()
