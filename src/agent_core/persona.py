from __future__ import annotations

import re

from agent_core.contracts import (
    AgentResponse,
    PersonaEnvelope,
    PersonaProfile,
    PersonaProfileResolutionSource,
    PersonaProfileResolverResult,
    PersonaRenderInput,
)
from agent_core.persona_registry import (
    DEFAULT_PERSONA_DISPLAY_NAME,
    DEFAULT_PERSONA_ID,
    DEFAULT_PERSONA_LEGACY_ID,
    FACT_POLICY,
    FORBIDDEN_PUBLIC_PERSONA_MARKERS,
    persona_display_style,
    resolve_builtin_persona,
)
from agent_core.persona_profile_resolver import PersonaProfileResolver


PERSONA_RENDER_CONTRACT = "specs/p1c_pluggable_persona_contract.md"
PERSONA_LLM_CONTEXT_CONTRACT = "persona_llm_context.v1"


def public_safe_default_persona() -> PersonaEnvelope:
    return PersonaEnvelope(
        persona_id=DEFAULT_PERSONA_ID,
        display_name=DEFAULT_PERSONA_DISPLAY_NAME,
        display_style=persona_display_style(resolve_builtin_persona(DEFAULT_PERSONA_ID)[0]),
        facts_locked=True,
        fact_policy=FACT_POLICY,
        public_safe=True,
        sanitized=False,
        render_contract=PERSONA_RENDER_CONTRACT,
    )


def persona_request_from_selector(persona_id: str | None) -> PersonaEnvelope | None:
    if persona_id is None or not persona_id.strip():
        return None
    return PersonaEnvelope(persona_id=persona_id.strip())


class PersonaBoundary:
    def __init__(self, *, persona_resolver: PersonaProfileResolver | None = None) -> None:
        self.persona_resolver = persona_resolver or PersonaProfileResolver()

    def attach_metadata(
        self,
        response: AgentResponse,
        persona: PersonaEnvelope | None = None,
    ) -> AgentResponse:
        requested_persona_id = persona.persona_id if persona is not None else None
        resolution = self.persona_resolver.resolve(requested_persona_id)
        effective_persona = resolution.profile
        render_input = PersonaRenderInput(
            requested_persona_id=requested_persona_id,
            effective_persona=effective_persona,
            canonical_answer=response.answer,
            presentation=response.presentation,
        )
        safe_persona = _persona_envelope_from_resolution(resolution, render_input)
        return response.model_copy(update={"persona": safe_persona}, deep=True)


def build_persona_llm_context(
    persona: PersonaEnvelope | None,
    *,
    persona_resolver: PersonaProfileResolver | None = None,
) -> str | None:
    resolver = persona_resolver or PersonaProfileResolver()
    requested_persona_id = persona.persona_id if persona is not None else None
    resolution = resolver.resolve(requested_persona_id)
    return _persona_llm_context_from_resolution(resolution)


def render_persona_answer(render_input: PersonaRenderInput) -> str:
    presentation = render_input.presentation
    reply = presentation.reply if presentation is not None else render_input.canonical_answer
    why = presentation.why if presentation is not None else ""
    warnings = (
        [warning.message for warning in presentation.visible_warnings if warning.message.strip()]
        if presentation is not None
        else []
    )
    followups = (
        [prompt for prompt in presentation.followup_prompts if prompt.strip()]
        if presentation is not None
        else []
    )
    renderer = _ALTERNATE_RENDERERS.get(
        render_input.effective_persona.persona_id,
        _render_obsidian_tactical,
    )
    return renderer(
        render_input.effective_persona,
        reply=reply,
        why=why,
        warnings=warnings,
        followups=followups,
    )


def _persona_llm_context_from_resolution(resolution: PersonaProfileResolverResult) -> str:
    profile = resolution.profile
    dna = profile.expression_dna
    mental_models = _limit_items(
        [
            f"{model.name}: {model.description.strip()}"
            for model in profile.mental_models
        ],
        limit=4,
    )
    heuristics = _limit_items(
        [
            f"{item.rule.strip()} ({item.rationale.strip()})"
            for item in profile.decision_heuristics
        ],
        limit=4,
    )
    boundaries = _limit_items(
        [
            f"{item.trigger.strip()}: {item.required_behavior.strip()}"
            for item in profile.honesty_boundaries
        ],
        limit=4,
    )
    flavor_rules = _limit_items(
        [
            f"{rule.id}: trigger={','.join(rule.trigger_terms)}; {rule.style_hint.strip()}"
            for rule in profile.rendering_flavor_rules
        ],
        limit=3,
    )
    source = (
        "managed materialized profile"
        if resolution.source == PersonaProfileResolutionSource.MATERIALIZED_PROFILE
        else "built-in profile"
    )
    lines = [
        f"Persona context contract: {PERSONA_LLM_CONTEXT_CONTRACT}.",
        f"Selected persona codename: {profile.display_name}.",
        f"Persona source: {source}; sanitized={str(resolution.sanitized).lower()}.",
        f"Tone: {dna.tone}.",
        f"Pacing: {dna.pacing}.",
        f"Wording preferences: {_join_items(dna.wording_preferences, fallback='none')}.",
        f"Signature moves: {_join_items(dna.signature_moves, fallback='none')}.",
        f"Taboo phrases: {_join_items(dna.taboo_phrases, fallback='none')}.",
        f"Anti-patterns: {_join_items(profile.anti_patterns[:6], fallback='none')}.",
        "Mental models: " + _join_items(mental_models, fallback="none") + ".",
        "Decision heuristics: " + _join_items(heuristics, fallback="none") + ".",
        "Honesty boundaries: " + _join_items(boundaries, fallback="none") + ".",
        "Rendering flavor rules: " + _join_items(flavor_rules, fallback="none") + ".",
        "Hard rule: persona controls wording and pressure only; it must not alter facts, scores, evidence, warnings, recommendations, or refusals.",
        "For casual greetings, do not use generic assistant welcome or service-offer boilerplate; answer in persona voice and ask for the concrete task.",
    ]
    return " ".join(_strip_forbidden_public_markers(line, profile) for line in lines)


def _persona_envelope_from_resolution(
    resolution: PersonaProfileResolverResult,
    render_input: PersonaRenderInput,
) -> PersonaEnvelope:
    effective_persona = resolution.profile
    return PersonaEnvelope(
        persona_id=effective_persona.persona_id,
        display_name=effective_persona.display_name,
        display_style=persona_display_style(effective_persona),
        rendered_answer=render_persona_answer(render_input),
        rendering_flavor_rule_ids=[rule.id for rule in effective_persona.rendering_flavor_rules],
        facts_locked=True,
        fact_policy=FACT_POLICY,
        public_safe=effective_persona.ip_safety_profile.public_safe,
        sanitized=resolution.sanitized,
        render_contract=PERSONA_RENDER_CONTRACT,
    )


def _render_obsidian_tactical(
    profile: PersonaProfile,
    *,
    reply: str,
    why: str,
    warnings: list[str],
    followups: list[str],
) -> str:
    return _apply_rendering_flavor_rules(profile, reply.strip(), context=[reply, why, *warnings, *followups])


def _render_lattice_supportive(
    profile: PersonaProfile,
    *,
    reply: str,
    why: str,
    warnings: list[str],
    followups: list[str],
) -> str:
    cleaned = reply.strip()
    return f"我会先给一个稳妥结论：{cleaned}" if cleaned else cleaned


def _apply_rendering_flavor_rules(
    profile: PersonaProfile,
    rendered: str,
    *,
    context: list[str],
) -> str:
    if not rendered:
        return rendered
    combined_context = "\n".join(item for item in context if item)
    for rule in profile.rendering_flavor_rules:
        if rule.id != "grass_type_hostility":
            continue
        if not any(term and term in combined_context for term in rule.trigger_terms):
            continue
        return f"{rendered}\n\n草系我不会替它说好话；如果它确实适合，我也只按事实放行。"
    return rendered


def _join_items(items: list[str], *, fallback: str) -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    return "；".join(cleaned) if cleaned else fallback


def _limit_items(items: list[str], *, limit: int) -> list[str]:
    return [item for item in items if item.strip()][:limit]


def _strip_forbidden_public_markers(text: str, profile: PersonaProfile) -> str:
    sanitized = text
    markers = [*FORBIDDEN_PUBLIC_PERSONA_MARKERS, *profile.ip_safety_profile.forbidden_markers]
    for marker in markers:
        if marker:
            sanitized = re.sub(re.escape(marker), "[redacted]", sanitized, flags=re.IGNORECASE)
    return sanitized


_ALTERNATE_RENDERERS = {
    "lattice_support_coach": _render_lattice_supportive,
}


__all__ = [
    "DEFAULT_PERSONA_ID",
    "DEFAULT_PERSONA_LEGACY_ID",
    "DEFAULT_PERSONA_DISPLAY_NAME",
    "FACT_POLICY",
    "FORBIDDEN_PUBLIC_PERSONA_MARKERS",
    "PERSONA_RENDER_CONTRACT",
    "PERSONA_LLM_CONTEXT_CONTRACT",
    "PersonaBoundary",
    "build_persona_llm_context",
    "persona_request_from_selector",
    "public_safe_default_persona",
    "render_persona_answer",
]
