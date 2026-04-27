from __future__ import annotations

from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaArtifactAdmissionStatus,
    PersonaArtifactIngestionResult,
    PersonaRegistryCandidate,
    PersonaRegistryReviewState,
)


PERSONA_REGISTRY_CANDIDATE_VERSION = "persona_registry_candidate.v1"


class PersonaRegistryAdmissionError(ValueError):
    pass


def build_persona_registry_candidate(
    ingestion_result: PersonaArtifactIngestionResult,
    *,
    output_path: Path | None = None,
) -> PersonaRegistryCandidate:
    _validate_ingestion_evidence(ingestion_result)
    metadata = ingestion_result.registry_metadata
    status = PersonaArtifactAdmissionStatus(ingestion_result.status)
    public_safe_approved = bool(ingestion_result.public_safe_approved)
    public_safe = status == PersonaArtifactAdmissionStatus.PUBLIC_SAFE and public_safe_approved
    internal_only = status == PersonaArtifactAdmissionStatus.INTERNAL_ONLY

    candidate = PersonaRegistryCandidate(
        candidate_version=PERSONA_REGISTRY_CANDIDATE_VERSION,
        persona_id=metadata.persona_id,
        version=metadata.version,
        admission_status=status,
        review_state=_review_state_for_status(status, public_safe_approved),
        source_adapter_id=metadata.source_adapter_id,
        doctrine_ref=metadata.doctrine_ref,
        provenance_ref=metadata.provenance_ref,
        mapping_note_ref=metadata.mapping_note_ref,
        supported_analysis_types=list(metadata.supported_analysis_types),
        ingestion_version=ingestion_result.ingestion_version,
        ingestion_admitted=ingestion_result.admitted,
        public_safe=public_safe,
        public_safe_approved=public_safe_approved,
        internal_only=internal_only,
        runtime_selectable=False,
        review_finding_codes=[finding.code for finding in ingestion_result.findings],
    )
    if output_path is not None:
        write_persona_registry_candidate(candidate, output_path)
    return candidate


def render_persona_registry_candidate_yaml(candidate: PersonaRegistryCandidate) -> str:
    return yaml.safe_dump(
        candidate.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def write_persona_registry_candidate(candidate: PersonaRegistryCandidate, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_persona_registry_candidate_yaml(candidate), encoding="utf-8")


def _validate_ingestion_evidence(ingestion_result: PersonaArtifactIngestionResult) -> None:
    if not ingestion_result.ingestion_version:
        raise PersonaRegistryAdmissionError("ingestion_version is required for registry admission.")
    metadata = ingestion_result.registry_metadata
    if ingestion_result.status != metadata.status:
        raise PersonaRegistryAdmissionError("ingestion status must match registry metadata status.")
    status = PersonaArtifactAdmissionStatus(ingestion_result.status)
    expected_public_safe = status == PersonaArtifactAdmissionStatus.PUBLIC_SAFE and ingestion_result.public_safe_approved
    if metadata.public_safe != expected_public_safe:
        raise PersonaRegistryAdmissionError("public-safe metadata must match explicit public-safe admission.")
    if not ingestion_result.admitted and ingestion_result.status not in {
        PersonaArtifactAdmissionStatus.REJECTED,
        PersonaArtifactAdmissionStatus.REVIEW_REQUIRED,
    }:
        raise PersonaRegistryAdmissionError("admitted=false is inconsistent with an admitted ingestion status.")


def _review_state_for_status(
    status: PersonaArtifactAdmissionStatus,
    public_safe_approved: bool,
) -> PersonaRegistryReviewState:
    if status == PersonaArtifactAdmissionStatus.PUBLIC_SAFE:
        if not public_safe_approved:
            raise PersonaRegistryAdmissionError("public_safe status requires explicit public_safe_approved=true.")
        return PersonaRegistryReviewState.PUBLIC_SAFE
    return PersonaRegistryReviewState(status)


__all__ = [
    "PERSONA_REGISTRY_CANDIDATE_VERSION",
    "PersonaRegistryAdmissionError",
    "build_persona_registry_candidate",
    "render_persona_registry_candidate_yaml",
    "write_persona_registry_candidate",
]
