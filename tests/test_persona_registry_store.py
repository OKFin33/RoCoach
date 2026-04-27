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
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import (
    PersonaRegistryStoreError,
    list_persona_registry_records_by_review_state,
    list_runtime_eligible_persona_registry_records,
    load_persona_registry_ledger,
    read_persona_registry_record,
    write_persona_registry_record,
)
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaRegistryStoreTests(unittest.TestCase):
    def test_write_and_read_preserves_candidate_and_ingestion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "registry" / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)

            written = write_persona_registry_record(ledger_path, candidate, ingestion_result)
            read_back = read_persona_registry_record(ledger_path, candidate.persona_id)

            self.assertIsNotNone(read_back)
            self.assertEqual(written.revision, 1)
            self.assertEqual(read_back, written)
            self.assertEqual(read_back.candidate, candidate)
            self.assertEqual(read_back.ingestion_evidence, ingestion_result)
            self.assertEqual(read_back.review_finding_codes, candidate.review_finding_codes)
            self.assertFalse(read_back.runtime_selectable)

            rendered = ledger_path.read_text(encoding="utf-8")
            self.assertIn("registry_version: persona_registry_ledger.v1", rendered)
            self.assertIn("ingestion_evidence:", rendered)
            self.assertIn("runtime_selectable: false", rendered)

    def test_duplicate_candidate_write_appends_revision_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)

            first = write_persona_registry_record(ledger_path, candidate, ingestion_result)
            second = write_persona_registry_record(ledger_path, candidate, ingestion_result)
            latest = read_persona_registry_record(ledger_path, candidate.persona_id, version=candidate.version)
            first_read = read_persona_registry_record(
                ledger_path,
                candidate.persona_id,
                version=candidate.version,
                revision=1,
            )

            self.assertEqual(first.revision, 1)
            self.assertEqual(second.revision, 2)
            self.assertEqual(latest.revision, 2)
            self.assertEqual(first_read.revision, 1)
            self.assertEqual(len(load_persona_registry_ledger(ledger_path).records), 2)

    def test_missing_ingestion_evidence_ref_blocks_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)
            metadata = ingestion_result.registry_metadata.model_copy(update={"provenance_ref": ""})
            incomplete_evidence = ingestion_result.model_copy(update={"registry_metadata": metadata})

            with self.assertRaisesRegex(PersonaRegistryStoreError, "missing required refs"):
                write_persona_registry_record(ledger_path, candidate, incomplete_evidence)

    def test_status_query_returns_matching_review_state_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            internal_result = ingest_persona_source_bundle(bundle)
            internal_candidate = build_persona_registry_candidate(internal_result)
            rejected_metadata = internal_result.registry_metadata.model_copy(
                update={"status": PersonaArtifactAdmissionStatus.REJECTED}
            )
            rejected_result = internal_result.model_copy(
                update={
                    "status": PersonaArtifactAdmissionStatus.REJECTED,
                    "registry_metadata": rejected_metadata,
                    "admitted": False,
                }
            )
            rejected_candidate = build_persona_registry_candidate(rejected_result)

            write_persona_registry_record(ledger_path, internal_candidate, internal_result)
            write_persona_registry_record(ledger_path, rejected_candidate, rejected_result)

            internal_records = list_persona_registry_records_by_review_state(
                ledger_path,
                PersonaRegistryReviewState.INTERNAL_ONLY,
            )
            rejected_records = list_persona_registry_records_by_review_state(
                ledger_path,
                PersonaRegistryReviewState.REJECTED,
            )

            self.assertEqual([record.review_state for record in internal_records], [PersonaRegistryReviewState.INTERNAL_ONLY])
            self.assertEqual([record.review_state for record in rejected_records], [PersonaRegistryReviewState.REJECTED])

    def test_internal_only_candidate_cannot_escalate_to_public_safe_in_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)
            escalated_candidate = candidate.model_copy(update={"public_safe": True, "public_safe_approved": True})

            with self.assertRaisesRegex(PersonaRegistryStoreError, "internal_only candidates"):
                write_persona_registry_record(ledger_path, escalated_candidate, ingestion_result)

    def test_runtime_selectable_candidate_is_blocked_and_runtime_query_stays_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)
            runtime_candidate = candidate.model_copy(update={"runtime_selectable": True})

            with self.assertRaisesRegex(PersonaRegistryStoreError, "runtime_selectable"):
                write_persona_registry_record(ledger_path, runtime_candidate, ingestion_result)

            write_persona_registry_record(ledger_path, candidate, ingestion_result)
            self.assertEqual(list_runtime_eligible_persona_registry_records(ledger_path), [])

    def test_runtime_selectable_ledger_tampering_is_blocked_on_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            ingestion_result = ingest_persona_source_bundle(bundle)
            candidate = build_persona_registry_candidate(ingestion_result)
            write_persona_registry_record(ledger_path, candidate, ingestion_result)
            payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
            payload["records"][0]["runtime_selectable"] = True
            ledger_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(PersonaRegistryStoreError, "runtime_selectable record"):
                load_persona_registry_ledger(ledger_path)

    def test_public_safe_approved_candidate_is_auditable_but_not_runtime_selectable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.yaml"
            bundle = generate_internal_nuwa_distillation_bundle(output_root=Path(tmpdir) / "source")
            doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
            doctrine["persona_id"] = "public_safe_store_candidate"
            doctrine["display_name"] = "Public Safe Store Candidate"
            doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
            bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
            ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
            candidate = build_persona_registry_candidate(ingestion_result)

            record = write_persona_registry_record(ledger_path, candidate, ingestion_result)

            self.assertEqual(record.review_state, PersonaRegistryReviewState.PUBLIC_SAFE)
            self.assertTrue(record.public_safe)
            self.assertTrue(record.public_safe_approved)
            self.assertFalse(record.runtime_selectable)
            self.assertEqual(list_runtime_eligible_persona_registry_records(ledger_path), [])


if __name__ == "__main__":
    unittest.main()
