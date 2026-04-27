from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaArtifactAdmissionStatus,
    PersonaRuntimeActivationScope,
    PersonaRuntimeActivationStatus,
)
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import (
    PersonaRegistryStoreError,
    read_persona_registry_record,
    write_persona_registry_record,
)
from agent_core.persona_runtime_activation import (
    PersonaRuntimeActivationError,
    build_persona_runtime_activation_report,
    evaluate_persona_runtime_activation,
)
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaRuntimeActivationTests(unittest.TestCase):
    def test_internal_only_record_is_internal_runtime_eligible_not_public_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")

            decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )
            public_decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            self.assertEqual(decision.status, PersonaRuntimeActivationStatus.ELIGIBLE)
            self.assertTrue(decision.eligible_for_internal_runtime)
            self.assertFalse(decision.eligible_for_public_release)
            self.assertFalse(decision.runtime_selectable)
            self.assertEqual(decision.evidence_refs.doctrine_ref, record.candidate.doctrine_ref)
            self.assertEqual(public_decision.status, PersonaRuntimeActivationStatus.BLOCKED)
            self.assertIn("public_safe_approval_required", public_decision.blocked_reasons)
            self.assertIn("internal_only_not_public_release_eligible", public_decision.blocked_reasons)

    def test_public_safe_approved_record_is_public_release_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_public_safe_record(ledger_path, Path(tmpdir) / "source")

            decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            self.assertEqual(decision.status, PersonaRuntimeActivationStatus.ELIGIBLE)
            self.assertTrue(decision.eligible_for_internal_runtime)
            self.assertTrue(decision.eligible_for_public_release)
            self.assertTrue(decision.public_safe)
            self.assertTrue(decision.public_safe_approved)
            self.assertEqual(decision.blocked_reasons, [])
            self.assertFalse(decision.runtime_selectable)

    def test_unapproved_public_safe_candidate_is_blocked_for_public_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "unapproved_public_runtime_candidate"
            doctrine["display_name"] = "Unapproved Public Runtime Candidate"
            doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)
            record = write_persona_registry_record(ledger_path, candidate, ingestion_result)

            decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            self.assertEqual(decision.status, PersonaRuntimeActivationStatus.BLOCKED)
            self.assertFalse(decision.eligible_for_public_release)
            self.assertIn("review_state_not_public_safe", decision.blocked_reasons)
            self.assertIn("public_safe_approval_required", decision.blocked_reasons)

    def test_activation_report_selects_latest_revision_per_persona_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            first = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            rejected_metadata = first.ingestion_evidence.registry_metadata.model_copy(
                update={"status": PersonaArtifactAdmissionStatus.REJECTED}
            )
            rejected_result = first.ingestion_evidence.model_copy(
                update={
                    "status": PersonaArtifactAdmissionStatus.REJECTED,
                    "registry_metadata": rejected_metadata,
                    "admitted": False,
                }
            )
            rejected_candidate = build_persona_registry_candidate(rejected_result)
            second = write_persona_registry_record(ledger_path, rejected_candidate, rejected_result)

            report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )

            self.assertEqual(first.revision, 1)
            self.assertEqual(second.revision, 2)
            self.assertEqual(len(report.decisions), 1)
            self.assertEqual(report.decisions[0].revision, 2)
            self.assertEqual(report.decisions[0].status, PersonaRuntimeActivationStatus.BLOCKED)
            self.assertIn("ingestion_not_admitted", report.decisions[0].blocked_reasons)

    def test_missing_evidence_refs_are_blocked_in_activation_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            candidate = record.candidate.model_copy(update={"doctrine_ref": ""})
            record_with_missing_evidence = record.model_copy(update={"candidate": candidate})

            decision = evaluate_persona_runtime_activation(record_with_missing_evidence)

            self.assertEqual(decision.status, PersonaRuntimeActivationStatus.BLOCKED)
            self.assertIn("required_evidence_refs_missing", decision.blocked_reasons)

    def test_runtime_flag_tampering_is_rejected_before_eligibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            tampered_record = record.model_copy(update={"runtime_selectable": True})
            tampered_candidate = record.candidate.model_copy(update={"runtime_selectable": True})
            tampered_candidate_record = record.model_copy(update={"candidate": tampered_candidate})

            with self.assertRaisesRegex(PersonaRuntimeActivationError, "runtime_selectable"):
                evaluate_persona_runtime_activation(tampered_record)
            with self.assertRaisesRegex(PersonaRuntimeActivationError, "runtime_selectable"):
                evaluate_persona_runtime_activation(tampered_candidate_record)

    def test_tampered_runtime_flag_in_ledger_is_rejected_on_report_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
            payload["records"][0]["runtime_selectable"] = True
            ledger_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(PersonaRegistryStoreError, "runtime_selectable record"):
                build_persona_runtime_activation_report(ledger_path)

    def test_activation_report_yaml_is_deterministic_and_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            output_path = Path(tmpdir) / "activation" / "report.yaml"
            record = _write_public_safe_record(ledger_path, Path(tmpdir) / "source")

            report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
                output_path=output_path,
            )

            self.assertTrue(output_path.exists())
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("activation_version: persona_runtime_activation_gate.v1", rendered)
            self.assertIn("requested_scope: public_safe_release", rendered)
            self.assertIn("eligible_for_public_release: true", rendered)
            self.assertIn("runtime_selectable: false", rendered)
            self.assertEqual(report.decisions[0].persona_id, record.persona_id)
            self.assertEqual(read_persona_registry_record(ledger_path, record.persona_id), record)


def _write_internal_only_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    ingestion_result = ingest_persona_source_bundle(bundle)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


def _write_public_safe_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
    doctrine["persona_id"] = "public_safe_runtime_candidate"
    doctrine["display_name"] = "Public Safe Runtime Candidate"
    doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
    bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
    ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


if __name__ == "__main__":
    unittest.main()
