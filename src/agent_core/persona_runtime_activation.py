from __future__ import annotations

from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaArtifactAdmissionStatus,
    PersonaRegistryReviewState,
    PersonaRegistryStoredRecord,
    PersonaRuntimeActivationDecision,
    PersonaRuntimeActivationEvidenceRefs,
    PersonaRuntimeActivationReport,
    PersonaRuntimeActivationScope,
    PersonaRuntimeActivationStatus,
)
from agent_core.persona_registry_store import load_persona_registry_ledger


PERSONA_RUNTIME_ACTIVATION_VERSION = "persona_runtime_activation_gate.v1"


class PersonaRuntimeActivationError(ValueError):
    pass


def build_persona_runtime_activation_report(
    ledger_path: Path,
    *,
    requested_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    output_path: Path | None = None,
) -> PersonaRuntimeActivationReport:
    ledger = load_persona_registry_ledger(ledger_path)
    latest_records = _latest_records_by_identity(ledger.records)
    decisions = [
        evaluate_persona_runtime_activation(record, requested_scope=requested_scope)
        for record in latest_records
    ]
    report = PersonaRuntimeActivationReport(
        activation_version=PERSONA_RUNTIME_ACTIVATION_VERSION,
        requested_scope=requested_scope,
        decisions=decisions,
    )
    if output_path is not None:
        write_persona_runtime_activation_report(report, output_path)
    return report


def evaluate_persona_runtime_activation(
    record: PersonaRegistryStoredRecord,
    *,
    requested_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
) -> PersonaRuntimeActivationDecision:
    _reject_runtime_flag_tampering(record)

    internal_runtime_reasons = _internal_runtime_blocked_reasons(record)
    public_release_reasons = _public_release_blocked_reasons(record)
    eligible_for_internal_runtime = not internal_runtime_reasons
    eligible_for_public_release = not public_release_reasons
    blocked_reasons = (
        public_release_reasons
        if requested_scope == PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE
        else internal_runtime_reasons
    )
    status = (
        PersonaRuntimeActivationStatus.ELIGIBLE
        if not blocked_reasons
        else PersonaRuntimeActivationStatus.BLOCKED
    )

    candidate = record.candidate
    return PersonaRuntimeActivationDecision(
        activation_version=PERSONA_RUNTIME_ACTIVATION_VERSION,
        persona_id=record.persona_id,
        version=record.version,
        revision=record.revision,
        requested_scope=requested_scope,
        status=status,
        admission_status=record.admission_status,
        review_state=record.review_state,
        public_safe=record.public_safe,
        public_safe_approved=record.public_safe_approved,
        internal_only=candidate.internal_only,
        eligible_for_internal_runtime=eligible_for_internal_runtime,
        eligible_for_public_release=eligible_for_public_release,
        runtime_selectable=False,
        evidence_refs=PersonaRuntimeActivationEvidenceRefs(
            source_adapter_id=candidate.source_adapter_id,
            doctrine_ref=candidate.doctrine_ref,
            provenance_ref=candidate.provenance_ref,
            mapping_note_ref=candidate.mapping_note_ref,
            ingestion_version=candidate.ingestion_version,
            review_finding_codes=list(record.review_finding_codes),
        ),
        blocked_reasons=blocked_reasons,
    )


def render_persona_runtime_activation_report_yaml(report: PersonaRuntimeActivationReport) -> str:
    return yaml.safe_dump(
        report.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def write_persona_runtime_activation_report(
    report: PersonaRuntimeActivationReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_persona_runtime_activation_report_yaml(report), encoding="utf-8")


def _latest_records_by_identity(records: list[PersonaRegistryStoredRecord]) -> list[PersonaRegistryStoredRecord]:
    latest: dict[tuple[str, str], PersonaRegistryStoredRecord] = {}
    for record in records:
        identity = (record.persona_id, record.version)
        current = latest.get(identity)
        if current is None or record.revision > current.revision:
            latest[identity] = record
    return sorted(latest.values(), key=lambda record: (record.persona_id, record.version))


def _internal_runtime_blocked_reasons(record: PersonaRegistryStoredRecord) -> list[str]:
    reasons: list[str] = []
    if not record.ingestion_evidence.admitted:
        reasons.append("ingestion_not_admitted")
    if record.review_state not in {
        PersonaRegistryReviewState.INTERNAL_ONLY,
        PersonaRegistryReviewState.PUBLIC_SAFE,
    }:
        reasons.append("review_state_not_internal_runtime_eligible")
    if record.admission_status not in {
        PersonaArtifactAdmissionStatus.INTERNAL_ONLY,
        PersonaArtifactAdmissionStatus.PUBLIC_SAFE,
    }:
        reasons.append("admission_status_not_internal_runtime_eligible")
    if not _has_required_evidence_refs(record):
        reasons.append("required_evidence_refs_missing")
    return reasons


def _public_release_blocked_reasons(record: PersonaRegistryStoredRecord) -> list[str]:
    reasons: list[str] = []
    if not record.ingestion_evidence.admitted:
        reasons.append("ingestion_not_admitted")
    if record.review_state != PersonaRegistryReviewState.PUBLIC_SAFE:
        reasons.append("review_state_not_public_safe")
    if record.admission_status != PersonaArtifactAdmissionStatus.PUBLIC_SAFE:
        reasons.append("admission_status_not_public_safe")
    if not record.public_safe:
        reasons.append("public_safe_false")
    if not record.public_safe_approved:
        reasons.append("public_safe_approval_required")
    if record.candidate.internal_only:
        reasons.append("internal_only_not_public_release_eligible")
    if not _has_required_evidence_refs(record):
        reasons.append("required_evidence_refs_missing")
    return reasons


def _reject_runtime_flag_tampering(record: PersonaRegistryStoredRecord) -> None:
    if record.runtime_selectable or record.candidate.runtime_selectable:
        raise PersonaRuntimeActivationError("tampered runtime_selectable registry record rejected.")


def _has_required_evidence_refs(record: PersonaRegistryStoredRecord) -> bool:
    evidence = record.ingestion_evidence.registry_metadata
    refs = (
        record.candidate.source_adapter_id,
        record.candidate.doctrine_ref,
        record.candidate.provenance_ref,
        record.candidate.mapping_note_ref,
        record.candidate.ingestion_version,
        evidence.source_adapter_id,
        evidence.doctrine_ref,
        evidence.provenance_ref,
        evidence.mapping_note_ref,
        record.ingestion_evidence.ingestion_version,
    )
    return all(bool(ref) for ref in refs)


__all__ = [
    "PERSONA_RUNTIME_ACTIVATION_VERSION",
    "PersonaRuntimeActivationError",
    "build_persona_runtime_activation_report",
    "evaluate_persona_runtime_activation",
    "render_persona_runtime_activation_report_yaml",
    "write_persona_runtime_activation_report",
]
