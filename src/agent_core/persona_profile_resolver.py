from __future__ import annotations

import re

from agent_core.contracts import (
    MaterializedPersonaProfileArtifact,
    PersonaIPSafetyProfile,
    PersonaProfile,
    PersonaProfileResolutionSource,
    PersonaProfileResolutionStatus,
    PersonaProfileResolverResult,
    PersonaProjectionProfileMaterialization,
    PersonaRuntimeActivationScope,
)
from agent_core.persona_registry import (
    DEFAULT_PERSONA_ID,
    FACT_POLICY,
    resolve_builtin_persona,
)


PERSONA_PROFILE_RESOLVER_VERSION = "persona_profile_resolver.v1"
MANAGED_PERSONA_SELECTOR_PATTERN = re.compile(r"^(?P<persona_id>[^@#\s]+)@(?P<version>[^@#\s]+)#(?P<revision>[1-9][0-9]*)$")


class PersonaProfileResolver:
    def __init__(
        self,
        materialization: PersonaProjectionProfileMaterialization | None = None,
        *,
        allowed_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    ) -> None:
        self.allowed_scope = allowed_scope
        self._profiles_by_identity: dict[tuple[str, str, int], MaterializedPersonaProfileArtifact] = {}
        self._persona_ids: set[str] = set()
        if materialization is not None:
            for profile in materialization.profiles:
                identity = (profile.persona_id, profile.version, profile.revision)
                self._profiles_by_identity[identity] = profile
                self._persona_ids.add(profile.persona_id)

    def resolve(self, selector: str | None) -> PersonaProfileResolverResult:
        normalized = _normalize_selector(selector)
        if normalized is None:
            return _built_in_result(None, None)

        parsed = parse_managed_persona_selector(normalized)
        if parsed is not None:
            persona_id, version, revision = parsed
            profile = self._profiles_by_identity.get((persona_id, version, revision))
            if profile is None:
                return _fallback_result(
                    normalized,
                    "materialized_profile_not_found",
                    requested_persona_id=persona_id,
                    requested_version=version,
                    requested_revision=revision,
                )
            blocked_reason = _materialized_profile_blocked_reason(profile, self.allowed_scope)
            if blocked_reason is not None:
                return _fallback_result(
                    normalized,
                    blocked_reason,
                    requested_persona_id=persona_id,
                    requested_version=version,
                    requested_revision=revision,
                )
            return _materialized_result(normalized, profile)

        if "@" in normalized or "#" in normalized:
            return _fallback_result(normalized, "invalid_managed_selector")
        if normalized in self._persona_ids:
            return _fallback_result(
                normalized,
                "materialized_profile_requires_exact_persona_id_version_revision",
                requested_persona_id=normalized,
            )
        return _built_in_result(normalized, normalized)


def make_managed_persona_selector(persona_id: str, version: str, revision: int) -> str:
    if not persona_id or not version or revision < 1:
        raise ValueError("managed persona selector requires persona_id, version, and revision>=1.")
    return f"{persona_id}@{version}#{revision}"


def parse_managed_persona_selector(selector: str) -> tuple[str, str, int] | None:
    match = MANAGED_PERSONA_SELECTOR_PATTERN.match(selector)
    if match is None:
        return None
    return (
        match.group("persona_id"),
        match.group("version"),
        int(match.group("revision")),
    )


def _materialized_profile_blocked_reason(
    artifact: MaterializedPersonaProfileArtifact,
    allowed_scope: PersonaRuntimeActivationScope,
) -> str | None:
    if (
        allowed_scope == PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE
        and artifact.activation_scope != PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE
    ):
        return "materialized_profile_scope_incompatible"
    policy = artifact.policy_profile
    if not artifact.synthesis_profile.facts_locked or artifact.synthesis_profile.fact_policy != FACT_POLICY:
        return "materialized_profile_fact_policy_unsafe"
    if allowed_scope == PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE:
        if not (policy.public_safe and policy.public_safe_approved and policy.eligible_for_public_release):
            return "materialized_profile_not_public_release_safe"
        if not policy.ip_safety_profile.public_safe:
            return "materialized_profile_ip_safety_unsafe"
    if allowed_scope == PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME and not policy.eligible_for_internal_runtime:
        return "materialized_profile_not_internal_runtime_eligible"
    return None


def _profile_from_materialized(artifact: MaterializedPersonaProfileArtifact) -> PersonaProfile:
    return PersonaProfile(
        persona_id=artifact.persona_id,
        display_name=artifact.rendering_profile.display_name,
        expression_dna=artifact.rendering_profile.expression_dna,
        rendering_flavor_rules=list(artifact.rendering_profile.rendering_flavor_rules),
        mental_models=list(artifact.synthesis_profile.mental_models),
        decision_heuristics=list(artifact.synthesis_profile.decision_heuristics),
        anti_patterns=list(artifact.synthesis_profile.anti_patterns),
        honesty_boundaries=list(artifact.synthesis_profile.honesty_boundaries),
        facts_locked=artifact.synthesis_profile.facts_locked,
        fact_policy=artifact.synthesis_profile.fact_policy,
        ip_safety_profile=PersonaIPSafetyProfile(
            public_safe=artifact.policy_profile.public_safe,
            forbidden_markers=list(artifact.policy_profile.ip_safety_profile.forbidden_markers),
        ),
    )


def _materialized_result(selector: str, artifact: MaterializedPersonaProfileArtifact) -> PersonaProfileResolverResult:
    profile = _profile_from_materialized(artifact)
    return PersonaProfileResolverResult(
        resolution_version=PERSONA_PROFILE_RESOLVER_VERSION,
        requested_selector=selector,
        requested_persona_id=artifact.persona_id,
        requested_version=artifact.version,
        requested_revision=artifact.revision,
        resolved_persona_id=profile.persona_id,
        source=PersonaProfileResolutionSource.MATERIALIZED_PROFILE,
        status=PersonaProfileResolutionStatus.RESOLVED,
        sanitized=False,
        sanitized_reason=None,
        activation_scope=artifact.activation_scope,
        profile=profile,
    )


def _built_in_result(selector: str | None, requested_persona_id: str | None) -> PersonaProfileResolverResult:
    profile, sanitized = resolve_builtin_persona(requested_persona_id)
    return PersonaProfileResolverResult(
        resolution_version=PERSONA_PROFILE_RESOLVER_VERSION,
        requested_selector=selector,
        requested_persona_id=requested_persona_id,
        resolved_persona_id=profile.persona_id,
        source=PersonaProfileResolutionSource.BUILT_IN if not sanitized else PersonaProfileResolutionSource.PUBLIC_SAFE_FALLBACK,
        status=PersonaProfileResolutionStatus.RESOLVED if not sanitized else PersonaProfileResolutionStatus.FALLBACK_SANITIZED,
        sanitized=sanitized,
        sanitized_reason="built_in_selector_sanitized" if sanitized else None,
        profile=profile,
    )


def _fallback_result(
    selector: str,
    reason: str,
    *,
    requested_persona_id: str | None = None,
    requested_version: str | None = None,
    requested_revision: int | None = None,
) -> PersonaProfileResolverResult:
    profile, _ = resolve_builtin_persona(DEFAULT_PERSONA_ID)
    return PersonaProfileResolverResult(
        resolution_version=PERSONA_PROFILE_RESOLVER_VERSION,
        requested_selector=selector,
        requested_persona_id=requested_persona_id,
        requested_version=requested_version,
        requested_revision=requested_revision,
        resolved_persona_id=profile.persona_id,
        source=PersonaProfileResolutionSource.PUBLIC_SAFE_FALLBACK,
        status=PersonaProfileResolutionStatus.FALLBACK_SANITIZED,
        sanitized=True,
        sanitized_reason=reason,
        profile=profile,
    )


def _normalize_selector(selector: str | None) -> str | None:
    if selector is None:
        return None
    normalized = selector.strip()
    return normalized or None


__all__ = [
    "MANAGED_PERSONA_SELECTOR_PATTERN",
    "PERSONA_PROFILE_RESOLVER_VERSION",
    "PersonaProfileResolver",
    "make_managed_persona_selector",
    "parse_managed_persona_selector",
]
