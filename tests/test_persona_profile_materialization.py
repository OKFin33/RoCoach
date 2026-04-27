from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaActivationRegistryProjection,
    PersonaRuntimeActivationScope,
)
from agent_core.persona_activation_projection import build_persona_activation_registry_projection
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_profile_materialization import (
    PersonaProfileMaterializationError,
    materialize_persona_projection_profiles,
)
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import write_persona_registry_record
from agent_core.persona_runtime_activation import build_persona_runtime_activation_report
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaProfileMaterializationTests(unittest.TestCase):
    def test_internal_projection_entry_materializes_split_runtime_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_internal_projection(Path(tmpdir))

            artifact = materialize_persona_projection_profiles(projection)

            self.assertEqual(len(artifact.profiles), 1)
            profile = artifact.profiles[0]
            self.assertEqual(profile.persona_id, "enzo_internal_nuwa_draft")
            self.assertEqual(profile.activation_scope, PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME)
            self.assertTrue(profile.synthesis_profile.mental_models)
            self.assertTrue(profile.synthesis_profile.decision_heuristics)
            self.assertTrue(profile.synthesis_profile.honesty_boundaries)
            self.assertEqual(profile.synthesis_profile.fact_policy, "persona_may_not_alter_facts")
            self.assertTrue(profile.synthesis_profile.facts_locked)
            self.assertEqual(profile.rendering_profile.display_name, "Enzo (Internal Nuwa Draft)")
            self.assertFalse(profile.policy_profile.public_safe)
            self.assertTrue(profile.policy_profile.internal_only)
            self.assertTrue(profile.policy_profile.eligible_for_internal_runtime)
            self.assertFalse(profile.policy_profile.eligible_for_public_release)

    def test_public_safe_projection_materializes_release_eligible_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_public_safe_projection(Path(tmpdir))

            artifact = materialize_persona_projection_profiles(projection)

            profile = artifact.profiles[0]
            self.assertEqual(profile.persona_id, "public_safe_materialized_candidate")
            self.assertTrue(profile.policy_profile.public_safe)
            self.assertTrue(profile.policy_profile.public_safe_approved)
            self.assertFalse(profile.policy_profile.internal_only)
            self.assertTrue(profile.policy_profile.eligible_for_public_release)
            self.assertEqual(profile.policy_profile.ip_safety_profile.public_safe, True)

    def test_blocked_projection_summaries_are_preserved_without_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ledger_path = root / "ledger.yaml"
            _write_internal_only_record(ledger_path, root / "source")
            activation_report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )
            projection = build_persona_activation_registry_projection(activation_report)

            artifact = materialize_persona_projection_profiles(projection)

            self.assertEqual(artifact.profiles, [])
            self.assertEqual(len(artifact.blocked_decision_summaries), 1)
            self.assertIn("public_safe_approval_required", artifact.blocked_decision_summaries[0].blocked_reasons)

    def test_non_projected_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_internal_projection(Path(tmpdir))
            projection.entries[0] = projection.entries[0].model_copy(update={"projected_runtime_entry": False})

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "non-projected"):
                materialize_persona_projection_profiles(projection)

    def test_materialization_rejects_doctrine_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_internal_projection(Path(tmpdir))
            doctrine_path = Path(projection.entries[0].evidence_refs.doctrine_ref)
            doctrine = yaml.safe_load(doctrine_path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "forged_persona"
            doctrine_path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "persona_id"):
                materialize_persona_projection_profiles(projection)

    def test_materialization_rejects_fact_policy_or_fact_lock_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_internal_projection(Path(tmpdir))
            doctrine_path = Path(projection.entries[0].evidence_refs.doctrine_ref)
            doctrine = yaml.safe_load(doctrine_path.read_text(encoding="utf-8"))
            doctrine["facts_locked"] = False
            doctrine_path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "facts_locked"):
                materialize_persona_projection_profiles(projection)

            doctrine["facts_locked"] = True
            doctrine["fact_policy"] = "persona_can_rewrite_facts"
            doctrine_path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "fact policy"):
                materialize_persona_projection_profiles(projection)

    def test_materialization_rejects_ip_safety_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_public_safe_projection(Path(tmpdir))
            doctrine_path = Path(projection.entries[0].evidence_refs.doctrine_ref)
            doctrine = yaml.safe_load(doctrine_path.read_text(encoding="utf-8"))
            doctrine["ip_safety_profile"] = {"public_safe": False, "forbidden_markers": ["private_marker"]}
            doctrine_path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "IP safety"):
                materialize_persona_projection_profiles(projection)

    def test_materialization_rejects_missing_evidence_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_internal_projection(Path(tmpdir))
            evidence_refs = projection.entries[0].evidence_refs.model_copy(update={"mapping_note_ref": ""})
            projection.entries[0] = projection.entries[0].model_copy(update={"evidence_refs": evidence_refs})

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "missing evidence refs"):
                materialize_persona_projection_profiles(projection)

            projection = _build_internal_projection(Path(tmpdir))
            evidence_refs = projection.entries[0].evidence_refs.model_copy(
                update={"provenance_ref": str(Path(tmpdir) / "missing_provenance.yaml")}
            )
            projection.entries[0] = projection.entries[0].model_copy(update={"evidence_refs": evidence_refs})

            with self.assertRaisesRegex(PersonaProfileMaterializationError, "provenance_ref"):
                materialize_persona_projection_profiles(projection)

    def test_materialization_preserves_per_entry_identity_without_cross_version_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projection = _build_public_safe_projection(Path(tmpdir))
            entry_v2 = projection.entries[0].model_copy(update={"version": "draft.v2", "revision": 1})
            projection = PersonaActivationRegistryProjection(
                projection_version=projection.projection_version,
                requested_scope=projection.requested_scope,
                activation_version=projection.activation_version,
                entries=[entry_v2, projection.entries[0]],
            )

            artifact = materialize_persona_projection_profiles(projection)

            self.assertEqual([(profile.version, profile.revision) for profile in artifact.profiles], [("draft.v2", 1), ("draft.v1", 1)])

    def test_materialization_yaml_is_deterministic_and_selector_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "materialized" / "profiles.yaml"
            projection = _build_public_safe_projection(Path(tmpdir))

            artifact = materialize_persona_projection_profiles(projection, output_path=output_path)

            self.assertTrue(output_path.exists())
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("materialization_version: persona_projection_profile_materialization.v1", rendered)
            self.assertIn("synthesis_profile:", rendered)
            self.assertIn("rendering_profile:", rendered)
            self.assertIn("policy_profile:", rendered)
            self.assertIn("evidence_refs:", rendered)
            self.assertIn("mental_models:", rendered)
            self.assertIn("expression_dna:", rendered)
            self.assertEqual(artifact.profiles[0].persona_id, "public_safe_materialized_candidate")


def _build_internal_projection(root: Path):
    ledger_path = root / "ledger.yaml"
    _write_internal_only_record(ledger_path, root / "source")
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    )
    return build_persona_activation_registry_projection(activation_report)


def _build_public_safe_projection(root: Path):
    ledger_path = root / "ledger.yaml"
    _write_public_safe_record(ledger_path, root / "source")
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
    )
    return build_persona_activation_registry_projection(activation_report)


def _write_internal_only_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    ingestion_result = ingest_persona_source_bundle(bundle)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


def _write_public_safe_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
    doctrine["persona_id"] = "public_safe_materialized_candidate"
    doctrine["display_name"] = "Public Safe Materialized Candidate"
    doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
    bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
    ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


if __name__ == "__main__":
    unittest.main()
