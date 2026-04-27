from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaRuntimeActivationReport,
    PersonaRuntimeActivationScope,
    PersonaRuntimeActivationStatus,
)
from agent_core.persona_activation_projection import (
    PersonaActivationProjectionError,
    build_persona_activation_registry_projection,
)
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import write_persona_registry_record
from agent_core.persona_runtime_activation import (
    build_persona_runtime_activation_report,
    evaluate_persona_runtime_activation,
)
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaActivationProjectionTests(unittest.TestCase):
    def test_internal_runtime_eligible_decision_becomes_projection_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            activation_report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )

            projection = build_persona_activation_registry_projection(activation_report)

            self.assertEqual(len(projection.entries), 1)
            self.assertEqual(projection.blocked_decision_summaries, [])
            entry = projection.entries[0]
            self.assertEqual(entry.persona_id, record.persona_id)
            self.assertEqual(entry.version, record.version)
            self.assertEqual(entry.revision, record.revision)
            self.assertTrue(entry.projected_runtime_entry)
            self.assertTrue(entry.eligible_for_internal_runtime)
            self.assertFalse(entry.eligible_for_public_release)
            self.assertTrue(entry.internal_only)
            self.assertFalse(entry.public_safe_approved)
            self.assertEqual(entry.evidence_refs.doctrine_ref, record.candidate.doctrine_ref)

    def test_public_safe_release_eligible_decision_preserves_policy_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_public_safe_record(ledger_path, Path(tmpdir) / "source")
            activation_report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            projection = build_persona_activation_registry_projection(activation_report)

            self.assertEqual(len(projection.entries), 1)
            entry = projection.entries[0]
            self.assertEqual(entry.persona_id, record.persona_id)
            self.assertEqual(entry.activation_scope, PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE)
            self.assertTrue(entry.public_safe)
            self.assertTrue(entry.public_safe_approved)
            self.assertFalse(entry.internal_only)
            self.assertTrue(entry.eligible_for_public_release)
            self.assertEqual(entry.evidence_refs.review_finding_codes, record.review_finding_codes)

    def test_blocked_activation_decision_stays_audit_summary_not_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            activation_report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            projection = build_persona_activation_registry_projection(activation_report)

            self.assertEqual(projection.entries, [])
            self.assertEqual(len(projection.blocked_decision_summaries), 1)
            summary = projection.blocked_decision_summaries[0]
            self.assertIn("public_safe_approval_required", summary.blocked_reasons)
            self.assertTrue(summary.internal_only)
            self.assertFalse(summary.public_safe_approved)

    def test_projection_preserves_per_decision_identity_without_cross_version_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_public_safe_record(ledger_path, Path(tmpdir) / "source")
            decision_v1 = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )
            decision_v2 = decision_v1.model_copy(update={"version": "draft.v2", "revision": 1})
            activation_report = PersonaRuntimeActivationReport(
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
                decisions=[decision_v2, decision_v1],
            )

            projection = build_persona_activation_registry_projection(activation_report)

            self.assertEqual([(entry.version, entry.revision) for entry in projection.entries], [("draft.v1", 1), ("draft.v2", 1)])

    def test_projection_rejects_scope_mismatch_and_runtime_flag_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            internal_decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )
            mismatched_report = PersonaRuntimeActivationReport(
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
                decisions=[internal_decision],
            )
            tampered_report = PersonaRuntimeActivationReport(
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
                decisions=[internal_decision.model_copy(update={"runtime_selectable": True})],
            )

            with self.assertRaisesRegex(PersonaActivationProjectionError, "scope"):
                build_persona_activation_registry_projection(mismatched_report)
            with self.assertRaisesRegex(PersonaActivationProjectionError, "runtime_selectable"):
                build_persona_activation_registry_projection(tampered_report)

    def test_projection_rejects_inconsistent_activation_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )
            inconsistent_decision = decision.model_copy(update={"blocked_reasons": ["impossible"]})
            report = PersonaRuntimeActivationReport(
                requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
                decisions=[inconsistent_decision],
            )

            with self.assertRaisesRegex(PersonaActivationProjectionError, "blocked reasons"):
                build_persona_activation_registry_projection(report)

    def test_projection_yaml_is_deterministic_and_contains_no_raw_doctrine_blob(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            output_path = Path(tmpdir) / "projection" / "runtime_registry_projection.yaml"
            record = _write_public_safe_record(ledger_path, Path(tmpdir) / "source")
            activation_report = build_persona_runtime_activation_report(
                ledger_path,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )

            projection = build_persona_activation_registry_projection(activation_report, output_path=output_path)

            self.assertTrue(output_path.exists())
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("projection_version: persona_activation_registry_projection.v1", rendered)
            self.assertIn("entries:", rendered)
            self.assertIn("projected_runtime_entry: true", rendered)
            self.assertIn("blocked_decision_summaries: []", rendered)
            self.assertIn("doctrine_ref:", rendered)
            self.assertNotIn("mental_models:", rendered)
            self.assertNotIn("expression_dna:", rendered)
            self.assertEqual(projection.entries[0].evidence_refs.doctrine_ref, record.candidate.doctrine_ref)

    def test_blocked_decision_without_reason_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            record = _write_internal_only_record(ledger_path, Path(tmpdir) / "source")
            blocked_decision = evaluate_persona_runtime_activation(
                record,
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            ).model_copy(update={"blocked_reasons": []})
            report = PersonaRuntimeActivationReport(
                requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
                decisions=[blocked_decision],
            )

            self.assertEqual(blocked_decision.status, PersonaRuntimeActivationStatus.BLOCKED)
            with self.assertRaisesRegex(PersonaActivationProjectionError, "blocked reasons"):
                build_persona_activation_registry_projection(report)


def _write_internal_only_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    ingestion_result = ingest_persona_source_bundle(bundle)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


def _write_public_safe_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
    doctrine["persona_id"] = "public_safe_projection_candidate"
    doctrine["display_name"] = "Public Safe Projection Candidate"
    doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
    bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
    ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


if __name__ == "__main__":
    unittest.main()
