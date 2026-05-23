from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agent_core.contracts import (
    AnalysisType,
    PersonaArtifactAdmissionStatus,
    PersonaArtifactIngestionResult,
    PersonaArtifactRegistryMetadata,
    PersonaArtifactValidationFinding,
    PersonaArtifactValidationStep,
    PersonaProfile,
    PersonaSourceArtifactBundle,
    PersonaSourceRunMode,
)
from agent_core.persona_registry import FACT_POLICY
from agent_core.persona_source_adapter import (
    DOCTRINE_CONTRACT_TARGET,
    MAPPING_NOTE_REQUIRED_SECTIONS,
)


PERSONA_ARTIFACT_INGESTION_VERSION = "persona_artifact_ingestion.v1"
DEFAULT_ARTIFACT_VERSION = "draft.v1"
SUPPORTED_BATTLE_ANALYSIS_TYPES = (
    AnalysisType.TEAM_ANALYSIS,
    AnalysisType.SPECIES_ANALYSIS,
    AnalysisType.SESSION_COMMAND,
)


class PersonaArtifactIngestionError(ValueError):
    pass


def ingest_persona_source_bundle(
    bundle: PersonaSourceArtifactBundle,
    *,
    approve_public_safe: bool = False,
    output_path: Path | None = None,
) -> PersonaArtifactIngestionResult:
    findings: list[PersonaArtifactValidationFinding] = []
    doctrine_payload: dict[str, Any] | None = None
    profile: PersonaProfile | None = None

    doctrine_payload = _load_yaml_mapping(
        bundle.doctrine_draft.path,
        PersonaArtifactValidationStep.SCHEMA_VALIDATION,
        "doctrine_draft",
        findings,
    )
    _check_required_artifact_refs(bundle, findings)
    _check_provenance(bundle, findings)
    _check_reasoning_rendering_split(bundle, doctrine_payload, findings)

    if doctrine_payload is not None:
        try:
            profile = PersonaProfile.model_validate(doctrine_payload)
        except ValidationError as exc:
            findings.append(
                _finding(
                    PersonaArtifactValidationStep.SCHEMA_VALIDATION,
                    "doctrine_profile_schema_invalid",
                    _compact_validation_error(exc),
                    blocking=True,
                )
            )

    if profile is not None:
        _check_cognitive_structure(profile, findings)
        _check_honesty_boundaries(profile, findings)
        _check_fact_policy(profile, findings)
        _check_ip_safety(profile, approve_public_safe, findings)
    _check_runtime_scope(bundle, findings)

    status = _resolve_status(bundle, profile, findings, approve_public_safe)
    registry_metadata = _build_registry_metadata(bundle, profile, status)
    result = PersonaArtifactIngestionResult(
        ingestion_version=PERSONA_ARTIFACT_INGESTION_VERSION,
        status=status,
        registry_metadata=registry_metadata,
        findings=findings,
        admitted=status
        not in {
            PersonaArtifactAdmissionStatus.REJECTED,
            PersonaArtifactAdmissionStatus.REVIEW_REQUIRED,
        },
        public_safe_approved=status == PersonaArtifactAdmissionStatus.PUBLIC_SAFE,
    )
    if output_path is not None:
        write_persona_artifact_ingestion_result(result, output_path)
    return result


def write_persona_artifact_ingestion_result(
    result: PersonaArtifactIngestionResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_persona_artifact_ingestion_result_yaml(result), encoding="utf-8")


def render_persona_artifact_ingestion_result_yaml(result: PersonaArtifactIngestionResult) -> str:
    return yaml.safe_dump(
        result.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def _load_yaml_mapping(
    path: Path,
    step: PersonaArtifactValidationStep,
    label: str,
    findings: list[PersonaArtifactValidationFinding],
) -> dict[str, Any] | None:
    if not path.exists():
        findings.append(_finding(step, f"{label}_missing", f"Missing required {label}: {path}", True))
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        findings.append(_finding(step, f"{label}_yaml_invalid", f"Invalid YAML in {path}: {exc}", True))
        return None
    if not isinstance(payload, dict):
        findings.append(_finding(step, f"{label}_not_mapping", f"{label} must be a YAML mapping.", True))
        return None
    return payload


def _check_required_artifact_refs(
    bundle: PersonaSourceArtifactBundle,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    for label, artifact_ref in (
        ("memo", bundle.memo),
        ("doctrine_draft", bundle.doctrine_draft),
        ("mapping_note", bundle.mapping_note),
        ("provenance_metadata", bundle.provenance_metadata),
    ):
        if not artifact_ref.path.exists() or not artifact_ref.path.read_text(encoding="utf-8").strip():
            findings.append(
                _finding(
                    PersonaArtifactValidationStep.SCHEMA_VALIDATION,
                    f"{label}_artifact_unreadable",
                    f"{label} artifact must exist and be non-empty: {artifact_ref.path}",
                    blocking=True,
                )
            )
    if bundle.doctrine_draft.contract_target != DOCTRINE_CONTRACT_TARGET:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.SCHEMA_VALIDATION,
                "doctrine_contract_target_mismatch",
                "Doctrine draft must target specs/persona_doctrine_contract.yaml.",
                blocking=True,
            )
        )


def _check_provenance(
    bundle: PersonaSourceArtifactBundle,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    provenance_payload = _load_yaml_mapping(
        bundle.provenance_metadata.path,
        PersonaArtifactValidationStep.PROVENANCE_PRESENCE_CHECK,
        "provenance_metadata",
        findings,
    )
    if provenance_payload is None:
        return
    required_fields = (
        "adapter_id",
        "adapter_kind",
        "run_mode",
        "target_subject",
        "stage_label",
        "public_source_scope",
        "source_summary",
        "source_material_refs",
    )
    for field in required_fields:
        value = provenance_payload.get(field)
        if value in (None, "", []):
            findings.append(
                _finding(
                    PersonaArtifactValidationStep.PROVENANCE_PRESENCE_CHECK,
                    f"provenance_{field}_missing",
                    f"Provenance metadata is missing required field: {field}.",
                    blocking=True,
                )
            )
    if provenance_payload.get("adapter_id") != bundle.adapter_id:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.PROVENANCE_PRESENCE_CHECK,
                "provenance_adapter_id_mismatch",
                "Provenance adapter_id must match source bundle adapter_id.",
                blocking=True,
            )
        )
    if provenance_payload.get("run_mode") != str(bundle.run_mode):
        findings.append(
            _finding(
                PersonaArtifactValidationStep.PROVENANCE_PRESENCE_CHECK,
                "provenance_run_mode_mismatch",
                "Provenance run_mode must match source bundle run_mode.",
                blocking=True,
            )
        )


def _check_reasoning_rendering_split(
    bundle: PersonaSourceArtifactBundle,
    doctrine_payload: dict[str, Any] | None,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    if not bundle.mapping_note.path.exists():
        return
    mapping_text = bundle.mapping_note.path.read_text(encoding="utf-8")
    for required_section in MAPPING_NOTE_REQUIRED_SECTIONS:
        if required_section not in mapping_text:
            findings.append(
                _finding(
                    PersonaArtifactValidationStep.REASONING_RENDERING_SPLIT_CHECK,
                    "mapping_required_section_missing",
                    f"Mapping note is missing required section: {required_section}.",
                    blocking=True,
                )
            )

    synthesis_section = _section_text(mapping_text, "## Synthesis-Facing Fields")
    rendering_section = _section_text(mapping_text, "## Rendering-Facing Fields")
    if "expression_dna" in synthesis_section or "display_name" in synthesis_section:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.REASONING_RENDERING_SPLIT_CHECK,
                "rendering_field_in_synthesis_section",
                "Mapping note places rendering-only fields in the synthesis-facing section.",
                blocking=True,
            )
        )
    if any(field in rendering_section for field in ("mental_models", "decision_heuristics", "anti_patterns")):
        findings.append(
            _finding(
                PersonaArtifactValidationStep.REASONING_RENDERING_SPLIT_CHECK,
                "reasoning_field_in_rendering_section",
                "Mapping note places reasoning-facing fields in the rendering-facing section.",
                blocking=True,
            )
        )
    if doctrine_payload is not None and "expression_dna" not in doctrine_payload:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.REASONING_RENDERING_SPLIT_CHECK,
                "rendering_layer_missing",
                "Doctrine draft must keep rendering fields explicit instead of blending them into reasoning.",
                blocking=True,
            )
        )


def _check_honesty_boundaries(
    profile: PersonaProfile,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    if not profile.honesty_boundaries:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.HONESTY_BOUNDARY_PRESENCE_CHECK,
                "honesty_boundaries_missing",
                "Persona doctrine must declare honesty boundaries.",
                blocking=True,
            )
        )
        return
    boundary_text = " ".join(
        f"{boundary.trigger} {boundary.required_behavior}" for boundary in profile.honesty_boundaries
    ).casefold()
    required_markers = ("fact", "confidence", "warning", "refusal")
    if not any(marker in boundary_text for marker in required_markers):
        findings.append(
            _finding(
                PersonaArtifactValidationStep.HONESTY_BOUNDARY_PRESENCE_CHECK,
                "grounding_boundary_missing",
                "Honesty boundaries must preserve facts, confidence, warnings, or refusals.",
                blocking=True,
            )
        )


def _check_cognitive_structure(
    profile: PersonaProfile,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    missing_fields = [
        field
        for field in ("mental_models", "decision_heuristics", "anti_patterns")
        if not getattr(profile, field)
    ]
    if missing_fields:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.SCHEMA_VALIDATION,
                "cognitive_structure_incomplete",
                f"Persona doctrine lacks reasoning-effective fields: {', '.join(missing_fields)}.",
                blocking=True,
            )
        )


def _check_fact_policy(
    profile: PersonaProfile,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    if not profile.facts_locked:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.FACT_POLICY_CHECK,
                "facts_not_locked",
                "Persona doctrine must keep facts_locked=true.",
                blocking=True,
            )
        )
    if profile.fact_policy != FACT_POLICY:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.FACT_POLICY_CHECK,
                "fact_policy_invalid",
                f"Persona doctrine fact_policy must be {FACT_POLICY}.",
                blocking=True,
            )
        )


def _check_ip_safety(
    profile: PersonaProfile,
    approve_public_safe: bool,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    searchable = " ".join(
        [
            profile.persona_id,
            profile.display_name,
            profile.expression_dna.tone,
            profile.expression_dna.pacing,
            *profile.expression_dna.wording_preferences,
            *profile.expression_dna.signature_moves,
            *profile.expression_dna.taboo_phrases,
        ]
    ).casefold()
    matched_markers = [
        marker for marker in profile.ip_safety_profile.forbidden_markers if marker.casefold() in searchable
    ]
    if profile.ip_safety_profile.public_safe and matched_markers:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.IP_SAFETY_REVIEW,
                "public_safe_marker_conflict",
                f"Public-safe doctrine contains forbidden renderable markers: {', '.join(matched_markers)}.",
                blocking=False,
            )
        )
    if not approve_public_safe and profile.ip_safety_profile.public_safe:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.IP_SAFETY_REVIEW,
                "public_safe_requires_explicit_approval",
                "Public-safe admission requires explicit ingestion-side approval.",
                blocking=False,
            )
        )
    if not profile.ip_safety_profile.public_safe:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.IP_SAFETY_REVIEW,
                "internal_only_ip_profile",
                "Doctrine IP safety profile is not public-safe; admission remains internal-only unless sanitized later.",
                blocking=False,
            )
        )


def _check_runtime_scope(
    bundle: PersonaSourceArtifactBundle,
    findings: list[PersonaArtifactValidationFinding],
) -> None:
    if bundle.runtime_activation_requested or bundle.registry_write_requested:
        findings.append(
            _finding(
                PersonaArtifactValidationStep.RUNTIME_SCOPE_REVIEW,
                "runtime_or_registry_bypass_requested",
                "Source bundle must not request runtime activation or direct registry write.",
                blocking=True,
            )
        )


def _resolve_status(
    bundle: PersonaSourceArtifactBundle,
    profile: PersonaProfile | None,
    findings: list[PersonaArtifactValidationFinding],
    approve_public_safe: bool,
) -> PersonaArtifactAdmissionStatus:
    if any(finding.blocking for finding in findings):
        return PersonaArtifactAdmissionStatus.REJECTED
    if profile is not None and profile.ip_safety_profile.public_safe:
        marker_conflict = any(finding.code == "public_safe_marker_conflict" for finding in findings)
        if approve_public_safe and not marker_conflict:
            return PersonaArtifactAdmissionStatus.PUBLIC_SAFE
        if bundle.run_mode == PersonaSourceRunMode.REVIEW_CANDIDATE:
            return PersonaArtifactAdmissionStatus.REVIEW_READY
        return PersonaArtifactAdmissionStatus.REVIEW_REQUIRED
    if bundle.run_mode == PersonaSourceRunMode.REVIEW_CANDIDATE:
        return PersonaArtifactAdmissionStatus.REVIEW_REQUIRED
    return PersonaArtifactAdmissionStatus.INTERNAL_ONLY


def _build_registry_metadata(
    bundle: PersonaSourceArtifactBundle,
    profile: PersonaProfile | None,
    status: PersonaArtifactAdmissionStatus,
) -> PersonaArtifactRegistryMetadata:
    persona_id = profile.persona_id if profile is not None else "unknown_persona"
    public_safe = status == PersonaArtifactAdmissionStatus.PUBLIC_SAFE
    return PersonaArtifactRegistryMetadata(
        persona_id=persona_id,
        version=DEFAULT_ARTIFACT_VERSION,
        status=status,
        source_adapter_id=bundle.adapter_id,
        doctrine_ref=str(bundle.doctrine_draft.path),
        provenance_ref=str(bundle.provenance_metadata.path),
        mapping_note_ref=str(bundle.mapping_note.path),
        supported_analysis_types=[str(analysis_type) for analysis_type in SUPPORTED_BATTLE_ANALYSIS_TYPES],
        public_safe=public_safe,
    )


def _section_text(markdown: str, heading: str) -> str:
    start = markdown.find(heading)
    if start == -1:
        return ""
    next_heading = markdown.find("\n## ", start + len(heading))
    if next_heading == -1:
        return markdown[start:].casefold()
    return markdown[start:next_heading].casefold()


def _finding(
    step: PersonaArtifactValidationStep,
    code: str,
    message: str,
    blocking: bool,
) -> PersonaArtifactValidationFinding:
    return PersonaArtifactValidationFinding(step=step, code=code, message=message, blocking=blocking)


def _compact_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return str(exc)
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {first.get('msg', 'validation failed')}"


__all__ = [
    "DEFAULT_ARTIFACT_VERSION",
    "PERSONA_ARTIFACT_INGESTION_VERSION",
    "PersonaArtifactIngestionError",
    "ingest_persona_source_bundle",
    "render_persona_artifact_ingestion_result_yaml",
    "write_persona_artifact_ingestion_result",
]
