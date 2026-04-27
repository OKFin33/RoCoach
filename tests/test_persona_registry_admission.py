from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaArtifactAdmissionStatus,
    PersonaRegistryReviewState,
)
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_registry import builtin_persona_registry
from agent_core.persona_registry_admission import (
    PersonaRegistryAdmissionError,
    build_persona_registry_candidate,
)
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaRegistryAdmissionTests(unittest.TestCase):
    def test_internal_only_ingestion_becomes_non_public_non_runtime_candidate(self) -> None:
        before_registry = builtin_persona_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)

            candidate = build_persona_registry_candidate(ingestion_result)

            self.assertEqual(candidate.persona_id, "enzo_internal_nuwa_draft")
            self.assertEqual(candidate.admission_status, PersonaArtifactAdmissionStatus.INTERNAL_ONLY)
            self.assertEqual(candidate.review_state, PersonaRegistryReviewState.INTERNAL_ONLY)
            self.assertTrue(candidate.ingestion_admitted)
            self.assertTrue(candidate.internal_only)
            self.assertFalse(candidate.public_safe)
            self.assertFalse(candidate.public_safe_approved)
            self.assertFalse(candidate.runtime_selectable)
            self.assertIn("internal_only_ip_profile", candidate.review_finding_codes)

        after_registry = builtin_persona_registry()
        self.assertEqual(set(before_registry), set(after_registry))
        self.assertNotIn("enzo_internal_nuwa_draft", after_registry)

    def test_public_safe_candidate_requires_explicit_ingestion_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "sanitized_registry_candidate"
            doctrine["display_name"] = "Sanitized Registry Candidate"
            doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            unapproved_result = ingest_persona_source_bundle(bundle)
            approved_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)

            unapproved_candidate = build_persona_registry_candidate(unapproved_result)
            approved_candidate = build_persona_registry_candidate(approved_result)

            self.assertEqual(unapproved_candidate.review_state, PersonaRegistryReviewState.REVIEW_REQUIRED)
            self.assertFalse(unapproved_candidate.public_safe)
            self.assertFalse(unapproved_candidate.runtime_selectable)
            self.assertEqual(approved_candidate.review_state, PersonaRegistryReviewState.PUBLIC_SAFE)
            self.assertTrue(approved_candidate.public_safe)
            self.assertTrue(approved_candidate.public_safe_approved)
            self.assertFalse(approved_candidate.runtime_selectable)

    def test_rejected_ingestion_is_preserved_as_non_admitted_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            provenance = yaml.safe_load(bundle.provenance_metadata.path.read_text(encoding="utf-8"))
            provenance.pop("source_summary")
            bundle.provenance_metadata.path.write_text(yaml.safe_dump(provenance), encoding="utf-8")
            ingestion_result = ingest_persona_source_bundle(bundle)

            candidate = build_persona_registry_candidate(ingestion_result)

            self.assertEqual(candidate.review_state, PersonaRegistryReviewState.REJECTED)
            self.assertFalse(candidate.ingestion_admitted)
            self.assertFalse(candidate.public_safe)
            self.assertFalse(candidate.runtime_selectable)
            self.assertIn("provenance_source_summary_missing", candidate.review_finding_codes)

    def test_review_ready_ingestion_status_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            ingestion_result = ingest_persona_source_bundle(bundle)
            metadata = ingestion_result.registry_metadata.model_copy(
                update={"status": PersonaArtifactAdmissionStatus.REVIEW_READY}
            )
            review_ready_result = ingestion_result.model_copy(
                update={
                    "status": PersonaArtifactAdmissionStatus.REVIEW_READY,
                    "registry_metadata": metadata,
                    "admitted": True,
                    "public_safe_approved": False,
                }
            )

            candidate = build_persona_registry_candidate(review_ready_result)

            self.assertEqual(candidate.admission_status, PersonaArtifactAdmissionStatus.REVIEW_READY)
            self.assertEqual(candidate.review_state, PersonaRegistryReviewState.REVIEW_READY)
            self.assertFalse(candidate.public_safe)
            self.assertFalse(candidate.runtime_selectable)

    def test_missing_ingestion_evidence_fails_registry_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            ingestion_result = ingest_persona_source_bundle(bundle)
            invalid_result = ingestion_result.model_copy(update={"ingestion_version": ""})

            with self.assertRaisesRegex(PersonaRegistryAdmissionError, "ingestion_version"):
                build_persona_registry_candidate(invalid_result)

    def test_public_safe_metadata_cannot_be_forged_from_internal_only_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            ingestion_result = ingest_persona_source_bundle(bundle)
            metadata = ingestion_result.registry_metadata.model_copy(update={"public_safe": True})
            forged_result = ingestion_result.model_copy(
                update={
                    "registry_metadata": metadata,
                    "public_safe_approved": True,
                }
            )

            with self.assertRaisesRegex(PersonaRegistryAdmissionError, "public-safe metadata"):
                build_persona_registry_candidate(forged_result)

    def test_registry_candidate_yaml_is_deterministic_and_reviewable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "registry" / "candidate.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)

            candidate = build_persona_registry_candidate(ingestion_result, output_path=output_path)

            self.assertTrue(output_path.exists())
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("candidate_version: persona_registry_candidate.v1", rendered)
            self.assertIn("review_state: internal_only", rendered)
            self.assertIn("runtime_selectable: false", rendered)
            self.assertEqual(yaml.safe_load(rendered)["persona_id"], candidate.persona_id)


if __name__ == "__main__":
    unittest.main()
