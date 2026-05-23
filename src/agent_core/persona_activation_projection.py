from __future__ import annotations

from pathlib import Path

import yaml

from agent_core.contracts import (
    PersonaActivationProjectionBlockedSummary,
    PersonaActivationProjectionEntry,
    PersonaActivationRegistryProjection,
    PersonaRuntimeActivationDecision,
    PersonaRuntimeActivationReport,
    PersonaRuntimeActivationScope,
    PersonaRuntimeActivationStatus,
)


PERSONA_ACTIVATION_REGISTRY_PROJECTION_VERSION = "persona_activation_registry_projection.v1"
PERSONA_ACTIVATION_PROJECTION_ENTRY_VERSION = "persona_activation_projection_entry.v1"


class PersonaActivationProjectionError(ValueError):
    pass


def build_persona_activation_registry_projection(
    activation_report: PersonaRuntimeActivationReport,
    *,
    output_path: Path | None = None,
) -> PersonaActivationRegistryProjection:
    entries: list[PersonaActivationProjectionEntry] = []
    blocked_summaries: list[PersonaActivationProjectionBlockedSummary] = []

    for decision in sorted(
        activation_report.decisions,
        key=lambda item: (item.persona_id, item.version, item.revision),
    ):
        _validate_decision_scope(activation_report, decision)
        _reject_runtime_flag_tampering(decision)
        _validate_decision_consistency(decision)
        if decision.status == PersonaRuntimeActivationStatus.ELIGIBLE:
            entries.append(_projection_entry_from_decision(decision))
        else:
            blocked_summaries.append(_blocked_summary_from_decision(decision))

    projection = PersonaActivationRegistryProjection(
        projection_version=PERSONA_ACTIVATION_REGISTRY_PROJECTION_VERSION,
        activation_version=activation_report.activation_version,
        requested_scope=activation_report.requested_scope,
        entries=entries,
        blocked_decision_summaries=blocked_summaries,
    )
    if output_path is not None:
        write_persona_activation_registry_projection(projection, output_path)
    return projection


def render_persona_activation_registry_projection_yaml(
    projection: PersonaActivationRegistryProjection,
) -> str:
    return yaml.safe_dump(
        projection.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def write_persona_activation_registry_projection(
    projection: PersonaActivationRegistryProjection,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_persona_activation_registry_projection_yaml(projection), encoding="utf-8")


def _projection_entry_from_decision(
    decision: PersonaRuntimeActivationDecision,
) -> PersonaActivationProjectionEntry:
    return PersonaActivationProjectionEntry(
        projection_entry_version=PERSONA_ACTIVATION_PROJECTION_ENTRY_VERSION,
        persona_id=decision.persona_id,
        version=decision.version,
        revision=decision.revision,
        activation_scope=decision.requested_scope,
        admission_status=decision.admission_status,
        review_state=decision.review_state,
        public_safe=decision.public_safe,
        public_safe_approved=decision.public_safe_approved,
        internal_only=decision.internal_only,
        eligible_for_internal_runtime=decision.eligible_for_internal_runtime,
        eligible_for_public_release=decision.eligible_for_public_release,
        projected_runtime_entry=True,
        evidence_refs=decision.evidence_refs,
    )


def _blocked_summary_from_decision(
    decision: PersonaRuntimeActivationDecision,
) -> PersonaActivationProjectionBlockedSummary:
    return PersonaActivationProjectionBlockedSummary(
        persona_id=decision.persona_id,
        version=decision.version,
        revision=decision.revision,
        activation_scope=decision.requested_scope,
        admission_status=decision.admission_status,
        review_state=decision.review_state,
        public_safe=decision.public_safe,
        public_safe_approved=decision.public_safe_approved,
        internal_only=decision.internal_only,
        evidence_refs=decision.evidence_refs,
        blocked_reasons=list(decision.blocked_reasons),
    )


def _validate_decision_scope(
    activation_report: PersonaRuntimeActivationReport,
    decision: PersonaRuntimeActivationDecision,
) -> None:
    if decision.requested_scope != activation_report.requested_scope:
        raise PersonaActivationProjectionError("activation decision scope must match report scope.")


def _reject_runtime_flag_tampering(decision: PersonaRuntimeActivationDecision) -> None:
    if decision.runtime_selectable:
        raise PersonaActivationProjectionError("tampered runtime_selectable activation decision rejected.")


def _validate_decision_consistency(decision: PersonaRuntimeActivationDecision) -> None:
    if decision.status == PersonaRuntimeActivationStatus.ELIGIBLE:
        if decision.blocked_reasons:
            raise PersonaActivationProjectionError("eligible activation decision must not carry blocked reasons.")
        if not _eligible_for_requested_scope(decision):
            raise PersonaActivationProjectionError("eligible activation decision does not match requested scope flags.")
    if decision.status == PersonaRuntimeActivationStatus.BLOCKED and not decision.blocked_reasons:
        raise PersonaActivationProjectionError("blocked activation decision must preserve blocked reasons.")


def _eligible_for_requested_scope(decision: PersonaRuntimeActivationDecision) -> bool:
    if decision.requested_scope == PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE:
        return decision.eligible_for_public_release
    return decision.eligible_for_internal_runtime


__all__ = [
    "PERSONA_ACTIVATION_PROJECTION_ENTRY_VERSION",
    "PERSONA_ACTIVATION_REGISTRY_PROJECTION_VERSION",
    "PersonaActivationProjectionError",
    "build_persona_activation_registry_projection",
    "render_persona_activation_registry_projection_yaml",
    "write_persona_activation_registry_projection",
]
