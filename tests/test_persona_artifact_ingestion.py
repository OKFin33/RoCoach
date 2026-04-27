from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import PersonaArtifactAdmissionStatus
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_registry import builtin_persona_registry
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaArtifactIngestionTests(unittest.TestCase):
    def test_internal_bundle_is_admitted_as_internal_only_with_registry_metadata(self) -> None:
        before_registry = builtin_persona_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            output_path = Path(tmpdir) / "ingestion" / "result.yaml"

            result = ingest_persona_source_bundle(bundle, output_path=output_path)

            self.assertEqual(result.status, PersonaArtifactAdmissionStatus.INTERNAL_ONLY)
            self.assertTrue(result.admitted)
            self.assertFalse(result.public_safe_approved)
            self.assertEqual(result.registry_metadata.persona_id, "enzo_internal_nuwa_draft")
            self.assertEqual(result.registry_metadata.source_adapter_id, "nuwa_distillation_adapter")
            self.assertEqual(result.registry_metadata.status, "internal_only")
            self.assertEqual(result.registry_metadata.public_safe, False)
            self.assertIn("team_analysis", result.registry_metadata.supported_analysis_types)
            self.assertTrue(output_path.exists())

        after_registry = builtin_persona_registry()
        self.assertEqual(set(before_registry), set(after_registry))
        self.assertNotIn("enzo_internal_nuwa_draft", after_registry)

    def test_missing_provenance_field_rejects_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            provenance = yaml.safe_load(bundle.provenance_metadata.path.read_text(encoding="utf-8"))
            provenance.pop("source_summary")
            bundle.provenance_metadata.path.write_text(yaml.safe_dump(provenance), encoding="utf-8")

            result = ingest_persona_source_bundle(bundle)

            self.assertEqual(result.status, PersonaArtifactAdmissionStatus.REJECTED)
            self.assertFalse(result.admitted)
            self.assertIn("provenance_source_summary_missing", {finding.code for finding in result.findings})

    def test_reasoning_rendering_boundary_violation_rejects_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            mapping_text = bundle.mapping_note.path.read_text(encoding="utf-8")
            mapping_text = mapping_text.replace(
                "- `mental_models`",
                "- `mental_models`\n- `expression_dna`",
                1,
            )
            bundle.mapping_note.path.write_text(mapping_text, encoding="utf-8")

            result = ingest_persona_source_bundle(bundle)

            self.assertEqual(result.status, PersonaArtifactAdmissionStatus.REJECTED)
            self.assertIn("rendering_field_in_synthesis_section", {finding.code for finding in result.findings})

    def test_fact_policy_violation_rejects_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["facts_locked"] = False
            doctrine["fact_policy"] = "persona_may_rewrite_facts"
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            result = ingest_persona_source_bundle(bundle)

            self.assertEqual(result.status, PersonaArtifactAdmissionStatus.REJECTED)
            finding_codes = {finding.code for finding in result.findings}
            self.assertIn("facts_not_locked", finding_codes)
            self.assertIn("fact_policy_invalid", finding_codes)

    def test_empty_cognitive_structure_rejects_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["mental_models"] = []
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            result = ingest_persona_source_bundle(bundle)

            self.assertEqual(result.status, PersonaArtifactAdmissionStatus.REJECTED)
            self.assertIn("cognitive_structure_incomplete", {finding.code for finding in result.findings})

    def test_public_safe_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "sanitized_internal_draft"
            doctrine["display_name"] = "Sanitized Internal Draft"
            doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")

            default_result = ingest_persona_source_bundle(bundle)
            approved_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)

            self.assertEqual(default_result.status, PersonaArtifactAdmissionStatus.REVIEW_REQUIRED)
            self.assertFalse(default_result.admitted)
            self.assertEqual(approved_result.status, PersonaArtifactAdmissionStatus.PUBLIC_SAFE)
            self.assertTrue(approved_result.admitted)
            self.assertTrue(approved_result.public_safe_approved)


if __name__ == "__main__":
    unittest.main()
