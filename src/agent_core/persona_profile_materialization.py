from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from agent_core.contracts import (
    MaterializedPersonaPolicyProfile,
    MaterializedPersonaProfileArtifact,
    MaterializedPersonaRenderingProfile,
    MaterializedPersonaSynthesisProfile,
    PersonaActivationProjectionEntry,
    PersonaActivationRegistryProjection,
    PersonaProfile,
    PersonaProjectionProfileMaterialization,
)
from agent_core.persona_registry import FACT_POLICY


PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION = "persona_projection_profile_materialization.v1"
PERSONA_MATERIALIZED_PROFILE_VERSION = "persona_materialized_profile.v1"


class PersonaProfileMaterializationError(ValueError):
    pass


def materialize_persona_projection_profiles(
    projection: PersonaActivationRegistryProjection,
    *,
    output_path: Path | None = None,
) -> PersonaProjectionProfileMaterialization:
    profiles = [_materialize_entry(entry) for entry in projection.entries]
    artifact = PersonaProjectionProfileMaterialization(
        materialization_version=PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION,
        projection_version=projection.projection_version,
        requested_scope=projection.requested_scope,
        profiles=profiles,
        blocked_decision_summaries=list(projection.blocked_decision_summaries),
    )
    if output_path is not None:
        write_persona_projection_profile_materialization(artifact, output_path)
    return artifact


def render_persona_projection_profile_materialization_yaml(
    artifact: PersonaProjectionProfileMaterialization,
) -> str:
    return yaml.safe_dump(
        artifact.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )


def write_persona_projection_profile_materialization(
    artifact: PersonaProjectionProfileMaterialization,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_persona_projection_profile_materialization_yaml(artifact), encoding="utf-8")


def _materialize_entry(entry: PersonaActivationProjectionEntry) -> MaterializedPersonaProfileArtifact:
    _validate_entry_is_projected(entry)
    _validate_evidence_refs(entry)
    profile = _load_reviewed_doctrine_profile(Path(entry.evidence_refs.doctrine_ref))
    _validate_profile_against_entry(profile, entry)
    return MaterializedPersonaProfileArtifact(
        materialized_profile_version=PERSONA_MATERIALIZED_PROFILE_VERSION,
        persona_id=entry.persona_id,
        version=entry.version,
        revision=entry.revision,
        activation_scope=entry.activation_scope,
        projection_entry_version=entry.projection_entry_version,
        synthesis_profile=MaterializedPersonaSynthesisProfile(
            mental_models=list(profile.mental_models),
            decision_heuristics=list(profile.decision_heuristics),
            anti_patterns=list(profile.anti_patterns),
            honesty_boundaries=list(profile.honesty_boundaries),
            facts_locked=profile.facts_locked,
            fact_policy=profile.fact_policy,
        ),
        rendering_profile=MaterializedPersonaRenderingProfile(
            display_name=profile.display_name,
            expression_dna=profile.expression_dna,
            rendering_flavor_rules=list(profile.rendering_flavor_rules),
        ),
        policy_profile=MaterializedPersonaPolicyProfile(
            public_safe=entry.public_safe,
            public_safe_approved=entry.public_safe_approved,
            internal_only=entry.internal_only,
            eligible_for_internal_runtime=entry.eligible_for_internal_runtime,
            eligible_for_public_release=entry.eligible_for_public_release,
            ip_safety_profile=profile.ip_safety_profile,
        ),
        evidence_refs=entry.evidence_refs,
    )


def _load_reviewed_doctrine_profile(doctrine_path: Path) -> PersonaProfile:
    if not doctrine_path.exists():
        raise PersonaProfileMaterializationError(f"referenced doctrine draft is missing: {doctrine_path}")
    try:
        payload = yaml.safe_load(doctrine_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PersonaProfileMaterializationError(f"referenced doctrine draft YAML is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise PersonaProfileMaterializationError("referenced doctrine draft must be a YAML mapping.")
    try:
        return PersonaProfile.model_validate(payload)
    except ValidationError as exc:
        raise PersonaProfileMaterializationError(f"referenced doctrine draft schema is invalid: {_compact_validation_error(exc)}") from exc


def _validate_entry_is_projected(entry: PersonaActivationProjectionEntry) -> None:
    if not entry.projected_runtime_entry:
        raise PersonaProfileMaterializationError("non-projected activation entry cannot be materialized.")
    if entry.internal_only and entry.public_safe_approved:
        raise PersonaProfileMaterializationError("internal-only projection entry cannot carry public-safe approval.")
    if entry.eligible_for_public_release and not (entry.public_safe and entry.public_safe_approved):
        raise PersonaProfileMaterializationError("public release materialization requires explicit public-safe approval.")
    if not entry.eligible_for_internal_runtime and not entry.eligible_for_public_release:
        raise PersonaProfileMaterializationError("blocked projection entry cannot be materialized.")


def _validate_evidence_refs(entry: PersonaActivationProjectionEntry) -> None:
    refs = {
        "source_adapter_id": entry.evidence_refs.source_adapter_id,
        "doctrine_ref": entry.evidence_refs.doctrine_ref,
        "provenance_ref": entry.evidence_refs.provenance_ref,
        "mapping_note_ref": entry.evidence_refs.mapping_note_ref,
        "ingestion_version": entry.evidence_refs.ingestion_version,
    }
    missing = [label for label, value in refs.items() if not value]
    if missing:
        raise PersonaProfileMaterializationError(f"projection entry is missing evidence refs: {', '.join(missing)}.")
    for label in ("provenance_ref", "mapping_note_ref"):
        ref_path = Path(refs[label])
        if not ref_path.exists():
            raise PersonaProfileMaterializationError(f"referenced {label} is missing: {ref_path}")


def _validate_profile_against_entry(profile: PersonaProfile, entry: PersonaActivationProjectionEntry) -> None:
    if profile.persona_id != entry.persona_id:
        raise PersonaProfileMaterializationError("doctrine persona_id must match projection entry identity.")
    if not profile.facts_locked:
        raise PersonaProfileMaterializationError("materialized persona doctrine must keep facts_locked=true.")
    if profile.fact_policy != FACT_POLICY:
        raise PersonaProfileMaterializationError("materialized persona doctrine has unsupported fact policy.")
    if profile.ip_safety_profile.public_safe != entry.public_safe:
        raise PersonaProfileMaterializationError("doctrine IP safety must match projection public_safe flag.")
    if entry.eligible_for_public_release and not profile.ip_safety_profile.public_safe:
        raise PersonaProfileMaterializationError("public release profile must be public-safe.")


def _compact_validation_error(exc: ValidationError) -> str:
    return "; ".join(error["msg"] for error in exc.errors())


__all__ = [
    "PERSONA_MATERIALIZED_PROFILE_VERSION",
    "PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION",
    "PersonaProfileMaterializationError",
    "materialize_persona_projection_profiles",
    "render_persona_projection_profile_materialization_yaml",
    "write_persona_projection_profile_materialization",
]
