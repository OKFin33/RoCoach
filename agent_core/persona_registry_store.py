from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from agent_core.contracts import (
    PersonaArtifactAdmissionStatus,
    PersonaArtifactIngestionResult,
    PersonaRegistryCandidate,
    PersonaRegistryLedger,
    PersonaRegistryReviewState,
    PersonaRegistryStoredRecord,
)


PERSONA_REGISTRY_LEDGER_VERSION = "persona_registry_ledger.v1"
PERSONA_REGISTRY_RECORD_VERSION = "persona_registry_record.v1"


class PersonaRegistryStoreError(ValueError):
    pass


def load_persona_registry_ledger(ledger_path: Path) -> PersonaRegistryLedger:
    if not ledger_path.exists():
        return PersonaRegistryLedger(registry_version=PERSONA_REGISTRY_LEDGER_VERSION, records=[])
    try:
        payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PersonaRegistryStoreError(f"registry ledger YAML is invalid: {exc}") from exc
    if payload is None:
        return PersonaRegistryLedger(registry_version=PERSONA_REGISTRY_LEDGER_VERSION, records=[])
    if not isinstance(payload, dict):
        raise PersonaRegistryStoreError("registry ledger must be a YAML mapping.")
    try:
        ledger = PersonaRegistryLedger.model_validate(payload)
    except ValidationError as exc:
        raise PersonaRegistryStoreError(f"registry ledger schema is invalid: {_compact_validation_error(exc)}") from exc
    if ledger.registry_version != PERSONA_REGISTRY_LEDGER_VERSION:
        raise PersonaRegistryStoreError("registry ledger version is unsupported.")
    for record in ledger.records:
        _validate_record_integrity(record)
    return ledger


def write_persona_registry_record(
    ledger_path: Path,
    candidate: PersonaRegistryCandidate,
    ingestion_evidence: PersonaArtifactIngestionResult,
) -> PersonaRegistryStoredRecord:
    _validate_candidate_for_store(candidate, ingestion_evidence)
    ledger = load_persona_registry_ledger(ledger_path)
    revision = _next_revision(ledger, candidate.persona_id, candidate.version)
    record = PersonaRegistryStoredRecord(
        record_version=PERSONA_REGISTRY_RECORD_VERSION,
        persona_id=candidate.persona_id,
        version=candidate.version,
        revision=revision,
        candidate=candidate,
        ingestion_evidence=ingestion_evidence,
        admission_status=candidate.admission_status,
        review_state=candidate.review_state,
        public_safe=candidate.public_safe,
        public_safe_approved=candidate.public_safe_approved,
        runtime_selectable=False,
        review_finding_codes=list(candidate.review_finding_codes),
    )
    ledger.records.append(record)
    _write_ledger(ledger_path, ledger)
    return record


def read_persona_registry_record(
    ledger_path: Path,
    persona_id: str,
    *,
    version: str | None = None,
    revision: int | None = None,
) -> PersonaRegistryStoredRecord | None:
    ledger = load_persona_registry_ledger(ledger_path)
    records = [
        record
        for record in ledger.records
        if record.persona_id == persona_id
        and (version is None or record.version == version)
        and (revision is None or record.revision == revision)
    ]
    if not records:
        return None
    return max(records, key=lambda record: record.revision)


def list_persona_registry_records_by_review_state(
    ledger_path: Path,
    review_state: PersonaRegistryReviewState,
) -> list[PersonaRegistryStoredRecord]:
    ledger = load_persona_registry_ledger(ledger_path)
    return [record for record in ledger.records if record.review_state == review_state]


def list_runtime_eligible_persona_registry_records(ledger_path: Path) -> list[PersonaRegistryStoredRecord]:
    ledger = load_persona_registry_ledger(ledger_path)
    return [record for record in ledger.records if record.runtime_selectable]


def render_persona_registry_ledger_yaml(ledger: PersonaRegistryLedger) -> str:
    return yaml.safe_dump(
        ledger.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def _write_ledger(ledger_path: Path, ledger: PersonaRegistryLedger) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(render_persona_registry_ledger_yaml(ledger), encoding="utf-8")


def _next_revision(ledger: PersonaRegistryLedger, persona_id: str, version: str) -> int:
    revisions = [
        record.revision
        for record in ledger.records
        if record.persona_id == persona_id and record.version == version
    ]
    if not revisions:
        return 1
    return max(revisions) + 1


def _validate_candidate_for_store(
    candidate: PersonaRegistryCandidate,
    ingestion_evidence: PersonaArtifactIngestionResult,
) -> None:
    if candidate.runtime_selectable:
        raise PersonaRegistryStoreError("registry store cannot persist runtime_selectable candidates.")
    if not ingestion_evidence.ingestion_version:
        raise PersonaRegistryStoreError("ingestion evidence must include ingestion_version.")

    metadata = ingestion_evidence.registry_metadata
    required_refs = {
        "source_adapter_id": metadata.source_adapter_id,
        "doctrine_ref": metadata.doctrine_ref,
        "provenance_ref": metadata.provenance_ref,
        "mapping_note_ref": metadata.mapping_note_ref,
    }
    missing_refs = [label for label, value in required_refs.items() if not value]
    if missing_refs:
        raise PersonaRegistryStoreError(f"ingestion evidence is missing required refs: {', '.join(missing_refs)}.")

    if candidate.persona_id != metadata.persona_id or candidate.version != metadata.version:
        raise PersonaRegistryStoreError("candidate identity must match ingestion evidence metadata.")
    if candidate.source_adapter_id != metadata.source_adapter_id:
        raise PersonaRegistryStoreError("candidate source adapter must match ingestion evidence.")
    if candidate.doctrine_ref != metadata.doctrine_ref:
        raise PersonaRegistryStoreError("candidate doctrine ref must match ingestion evidence.")
    if candidate.provenance_ref != metadata.provenance_ref:
        raise PersonaRegistryStoreError("candidate provenance ref must match ingestion evidence.")
    if candidate.mapping_note_ref != metadata.mapping_note_ref:
        raise PersonaRegistryStoreError("candidate mapping note ref must match ingestion evidence.")
    if candidate.admission_status != ingestion_evidence.status:
        raise PersonaRegistryStoreError("candidate admission status must match ingestion evidence status.")
    if candidate.ingestion_version != ingestion_evidence.ingestion_version:
        raise PersonaRegistryStoreError("candidate ingestion version must match ingestion evidence.")
    if candidate.ingestion_admitted != ingestion_evidence.admitted:
        raise PersonaRegistryStoreError("candidate admission flag must match ingestion evidence.")

    evidence_finding_codes = [finding.code for finding in ingestion_evidence.findings]
    if candidate.review_finding_codes != evidence_finding_codes:
        raise PersonaRegistryStoreError("candidate review findings must match ingestion evidence findings.")

    _validate_public_safe_boundary(candidate, ingestion_evidence)


def _validate_record_integrity(record: PersonaRegistryStoredRecord) -> None:
    candidate = record.candidate
    if record.runtime_selectable or candidate.runtime_selectable:
        raise PersonaRegistryStoreError("registry ledger contains runtime_selectable record.")
    if record.persona_id != candidate.persona_id or record.version != candidate.version:
        raise PersonaRegistryStoreError("registry record identity must mirror its candidate.")
    if record.admission_status != candidate.admission_status:
        raise PersonaRegistryStoreError("registry record admission status must mirror its candidate.")
    if record.review_state != candidate.review_state:
        raise PersonaRegistryStoreError("registry record review state must mirror its candidate.")
    if record.public_safe != candidate.public_safe:
        raise PersonaRegistryStoreError("registry record public_safe must mirror its candidate.")
    if record.public_safe_approved != candidate.public_safe_approved:
        raise PersonaRegistryStoreError("registry record public_safe_approved must mirror its candidate.")
    if record.review_finding_codes != candidate.review_finding_codes:
        raise PersonaRegistryStoreError("registry record findings must mirror its candidate.")


def _validate_public_safe_boundary(
    candidate: PersonaRegistryCandidate,
    ingestion_evidence: PersonaArtifactIngestionResult,
) -> None:
    status = PersonaArtifactAdmissionStatus(candidate.admission_status)
    if candidate.internal_only and (candidate.public_safe or candidate.public_safe_approved):
        raise PersonaRegistryStoreError("internal_only candidates cannot be public-safe approved.")
    if status == PersonaArtifactAdmissionStatus.INTERNAL_ONLY and not candidate.internal_only:
        raise PersonaRegistryStoreError("internal_only admission status must keep internal_only=true.")
    if candidate.public_safe != ingestion_evidence.registry_metadata.public_safe:
        raise PersonaRegistryStoreError("candidate public_safe must match ingestion evidence metadata.")
    if candidate.public_safe_approved != ingestion_evidence.public_safe_approved:
        raise PersonaRegistryStoreError("candidate public_safe_approved must match ingestion evidence.")
    if candidate.public_safe and status != PersonaArtifactAdmissionStatus.PUBLIC_SAFE:
        raise PersonaRegistryStoreError("public-safe candidates require public_safe admission status.")
    if candidate.public_safe and candidate.review_state != PersonaRegistryReviewState.PUBLIC_SAFE:
        raise PersonaRegistryStoreError("public-safe candidates require public_safe review state.")


def _compact_validation_error(exc: ValidationError) -> str:
    return "; ".join(error["msg"] for error in exc.errors())


__all__ = [
    "PERSONA_REGISTRY_LEDGER_VERSION",
    "PERSONA_REGISTRY_RECORD_VERSION",
    "PersonaRegistryStoreError",
    "list_persona_registry_records_by_review_state",
    "list_runtime_eligible_persona_registry_records",
    "load_persona_registry_ledger",
    "read_persona_registry_record",
    "render_persona_registry_ledger_yaml",
    "write_persona_registry_record",
]
