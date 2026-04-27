from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_core.contracts import (
    PersonaSourceAdapterRequest,
    PersonaSourceRunMode,
)
from agent_core.persona_registry import builtin_persona_registry
from agent_core.persona_source_adapter import (
    DOCTRINE_CONTRACT_TARGET,
    NuwaDistillationAdapter,
    PERSONA_SOURCE_STAGE_LABEL,
    PersonaSourceAdapterError,
    generate_internal_nuwa_distillation_bundle,
    validate_persona_source_bundle,
)


class PersonaSourceAdapterTests(unittest.TestCase):
    def test_generate_internal_nuwa_bundle_emits_complete_reviewable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))

            self.assertEqual(bundle.adapter_id, "nuwa_distillation_adapter")
            self.assertEqual(bundle.adapter_kind, "distill_from_existing_subject")
            self.assertEqual(bundle.run_mode, "internal_only")
            self.assertTrue(bundle.memo.path.exists())
            self.assertTrue(bundle.doctrine_draft.path.exists())
            self.assertTrue(bundle.mapping_note.path.exists())
            self.assertTrue(bundle.provenance_metadata.path.exists())
            self.assertEqual(bundle.doctrine_draft.contract_target, DOCTRINE_CONTRACT_TARGET)
            self.assertFalse(bundle.runtime_activation_requested)
            self.assertFalse(bundle.registry_write_requested)

            provenance_text = bundle.provenance_metadata.path.read_text(encoding="utf-8")
            self.assertIn("adapter_id: nuwa_distillation_adapter", provenance_text)
            self.assertIn("adapter_kind: distill_from_existing_subject", provenance_text)
            self.assertIn("run_mode: internal_only", provenance_text)
            self.assertIn("source_summary:", provenance_text)

    def test_generation_does_not_activate_runtime_registry(self) -> None:
        before_registry = builtin_persona_registry()

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))

        after_registry = builtin_persona_registry()
        self.assertEqual(set(before_registry), set(after_registry))
        self.assertNotIn("enzo_internal_nuwa_draft", after_registry)
        self.assertFalse(bundle.runtime_activation_requested)
        self.assertFalse(bundle.registry_write_requested)

    def test_missing_required_artifact_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            memo = temp_root / "memo.md"
            doctrine = temp_root / "doctrine.yaml"
            memo.write_text("# memo\n", encoding="utf-8")
            doctrine.write_text("persona_id: sample\n", encoding="utf-8")

            with patch(
                "agent_core.persona_source_adapter.ENZO_FIXTURE_SOURCES",
                {"memo": memo, "doctrine": doctrine, "mapping": temp_root / "missing.md"},
            ):
                with self.assertRaisesRegex(PersonaSourceAdapterError, "Missing required mapping source"):
                    generate_internal_nuwa_distillation_bundle(output_root=temp_root / "out")

    def test_missing_provenance_summary_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir))
            invalid_bundle = bundle.model_copy(
                update={"provenance": bundle.provenance.model_copy(update={"source_summary": []})}
            )

            with self.assertRaisesRegex(PersonaSourceAdapterError, "source_summary"):
                validate_persona_source_bundle(invalid_bundle)

    def test_crawler_side_p1d_label_is_rejected(self) -> None:
        adapter = NuwaDistillationAdapter()
        request = PersonaSourceAdapterRequest(
            target_subject="enzo",
            public_source_scope=["reviewed_internal_distillation_artifacts"],
            stage_label="P1d crawler dry-run",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(PersonaSourceAdapterError, "full persona-side stage name"):
                adapter.generate_bundle(request, output_root=Path(tmpdir))

    def test_review_candidate_run_mode_is_rejected_for_p1d(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(PersonaSourceAdapterError, "internal_only"):
                generate_internal_nuwa_distillation_bundle(
                    output_root=Path(tmpdir),
                    run_mode=PersonaSourceRunMode.REVIEW_CANDIDATE,
                )

    def test_stage_label_constant_is_persona_side(self) -> None:
        self.assertEqual(PERSONA_SOURCE_STAGE_LABEL, "P1d Persona Source Adapter")


if __name__ == "__main__":
    unittest.main()
