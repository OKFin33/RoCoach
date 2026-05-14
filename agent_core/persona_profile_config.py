from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from agent_core.contracts import PersonaProjectionProfileMaterialization, PersonaRuntimeActivationScope
from agent_core.persona_profile_resolver import PersonaProfileResolver


PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION = "persona_projection_profile_materialization.v1"


class PersonaProfileConfigError(ValueError):
    pass


def load_persona_projection_profile_materialization(
    materialization_path: Path,
) -> PersonaProjectionProfileMaterialization:
    if not materialization_path.exists():
        raise PersonaProfileConfigError(f"materialized persona profile artifact is missing: {materialization_path}")
    try:
        payload = yaml.safe_load(materialization_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PersonaProfileConfigError(f"materialized persona profile artifact YAML is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise PersonaProfileConfigError("materialized persona profile artifact must be a YAML mapping.")
    try:
        materialization = PersonaProjectionProfileMaterialization.model_validate(payload)
    except ValidationError as exc:
        raise PersonaProfileConfigError(f"materialized persona profile artifact schema is invalid: {_compact_validation_error(exc)}") from exc
    if materialization.materialization_version != PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION:
        raise PersonaProfileConfigError("materialized persona profile artifact version is unsupported.")
    return materialization


def build_persona_profile_resolver_from_materialization_path(
    materialization_path: Path,
    *,
    allowed_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
) -> PersonaProfileResolver:
    materialization = load_persona_projection_profile_materialization(materialization_path)
    return PersonaProfileResolver(materialization, allowed_scope=allowed_scope)


def _compact_validation_error(exc: ValidationError) -> str:
    return "; ".join(error["msg"] for error in exc.errors())


__all__ = [
    "PERSONA_PROJECTION_PROFILE_MATERIALIZATION_VERSION",
    "PersonaProfileConfigError",
    "build_persona_profile_resolver_from_materialization_path",
    "load_persona_projection_profile_materialization",
]
