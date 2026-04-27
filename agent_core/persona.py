from __future__ import annotations

from agent_core.contracts import (
    AgentResponse,
    PersonaEnvelope,
    PersonaProfile,
    PersonaProfileResolverResult,
    PersonaRenderInput,
)
from agent_core.persona_registry import (
    DEFAULT_PERSONA_DISPLAY_NAME,
    DEFAULT_PERSONA_ID,
    FACT_POLICY,
    FORBIDDEN_PUBLIC_PERSONA_MARKERS,
    persona_display_style,
    resolve_builtin_persona,
)
from agent_core.persona_profile_resolver import PersonaProfileResolver


PERSONA_RENDER_CONTRACT = "specs/p1c_pluggable_persona_contract.md"


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
    sections = [
        f"{profile.display_name}｜收口结论",
        reply,
        f"依据：{why}" if why else "",
        f"边界：{_join_items(warnings, fallback='当前无新增显式警告。')}",
        f"下一步：{_join_items(followups, fallback='暂无额外追问建议。')}",
    ]
    return "\n".join(section for section in sections if section)


def _render_lattice_supportive(
    profile: PersonaProfile,
    *,
    reply: str,
    why: str,
    warnings: list[str],
    followups: list[str],
) -> str:
    sections = [
        f"{profile.display_name}：先稳住可信结论。",
        f"主答复：{reply}",
        f"为什么：{why}" if why else "",
        f"警戒线：{_join_items(warnings, fallback='当前无新增显式警告。')}",
        f"建议追问：{_join_items(followups, fallback='暂无额外追问建议。')}",
    ]
    return "\n".join(section for section in sections if section)


def _join_items(items: list[str], *, fallback: str) -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    return "；".join(cleaned) if cleaned else fallback


_ALTERNATE_RENDERERS = {
    "lattice_support_coach": _render_lattice_supportive,
}


__all__ = [
    "DEFAULT_PERSONA_ID",
    "DEFAULT_PERSONA_DISPLAY_NAME",
    "FACT_POLICY",
    "FORBIDDEN_PUBLIC_PERSONA_MARKERS",
    "PERSONA_RENDER_CONTRACT",
    "PersonaBoundary",
    "persona_request_from_selector",
    "public_safe_default_persona",
    "render_persona_answer",
]
