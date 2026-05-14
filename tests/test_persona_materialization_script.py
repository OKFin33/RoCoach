from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import PersonaRuntimeActivationScope
from agent_core.persona_profile_config import build_persona_profile_resolver_from_materialization_path
from agent_core.persona_profile_resolver import make_managed_persona_selector
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "materialize_persona_artifacts.py"


class PersonaMaterializationScriptTests(unittest.TestCase):
    def test_checked_in_you_know_who_minimal_bundle_materializes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "you_know_who_runtime"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--source-root",
                    str(ROOT / "docs" / "personas" / "you_know_who_minimal"),
                    "--output-root",
                    str(output_root),
                    "--approve-public-safe",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            materialization_path = output_root / "materialized_profiles.yaml"
            self.assertIn("selector=you_know_who@draft.v1#1", completed.stdout)
            self.assertIn("profile_count=1", completed.stdout)
            self.assertEqual((output_root / "selector.txt").read_text(encoding="utf-8").strip(), "you_know_who@draft.v1#1")

            resolver = build_persona_profile_resolver_from_materialization_path(materialization_path)
            resolved = resolver.resolve(make_managed_persona_selector("you_know_who", "draft.v1", 1))
            self.assertFalse(resolved.sanitized)
            self.assertEqual(resolved.profile.persona_id, "you_know_who")
            self.assertEqual(resolved.profile.display_name, "You know who")
            self.assertTrue(resolved.profile.ip_safety_profile.public_safe)
            self.assertIn("helplessness_debt", [model.name for model in resolved.profile.mental_models])
            self.assertIn(
                "forbidden_knowledge_is_not_automatically_false",
                [model.name for model in resolved.profile.mental_models],
            )
            self.assertIn("grass_type_hostility", [rule.id for rule in resolved.profile.rendering_flavor_rules])

    def test_script_materializes_public_safe_artifacts_and_selector(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = generate_internal_nuwa_distillation_bundle(output_root=root / "source")
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "public_safe_cli_persona"
            doctrine["display_name"] = "Public Safe CLI Persona"
            doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
            output_root = root / "runtime_artifacts"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--source-root",
                    str(bundle.output_root),
                    "--output-root",
                    str(output_root),
                    "--approve-public-safe",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            materialization_path = output_root / "materialized_profiles.yaml"
            selector_path = output_root / "selector.txt"
            env_path = output_root / "runtime_env_snippet.env"
            self.assertTrue(materialization_path.exists())
            self.assertTrue(selector_path.exists())
            self.assertTrue(env_path.exists())
            self.assertIn("profile_count=1", completed.stdout)
            self.assertEqual(selector_path.read_text(encoding="utf-8").strip(), "public_safe_cli_persona@draft.v1#1")
            self.assertIn(
                f"ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH={materialization_path.resolve()}",
                env_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "ROCO_MANAGED_PERSONA_SCOPE=internal_only_runtime",
                env_path.read_text(encoding="utf-8"),
            )

            resolver = build_persona_profile_resolver_from_materialization_path(materialization_path)
            resolved = resolver.resolve(make_managed_persona_selector("public_safe_cli_persona", "draft.v1", 1))
            self.assertFalse(resolved.sanitized)
            self.assertEqual(resolved.profile.display_name, "Public Safe CLI Persona")

    def test_script_preserves_blocked_public_scope_without_public_safe_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = generate_internal_nuwa_distillation_bundle(output_root=root / "source")
            output_root = root / "runtime_artifacts"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--source-root",
                    str(bundle.output_root),
                    "--output-root",
                    str(output_root),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("profile_count=1", completed.stdout)
            self.assertIn("blocked_count=0", completed.stdout)
            self.assertTrue((output_root / "selector.txt").exists())
            summary = yaml.safe_load((output_root / "summary.yaml").read_text(encoding="utf-8"))
            self.assertEqual(summary["scope"], PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME)
            self.assertEqual(summary["blocked_count"], 0)


if __name__ == "__main__":
    unittest.main()
