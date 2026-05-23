from __future__ import annotations

from agent_core.contracts import (
    AgentResponseStatus,
    DetailSection,
    DetailSectionContentKind,
    DetailSectionVisibility,
    PresentationInput,
    PresentationMetadata,
    PresentationResult,
    SynthesisWarning,
    VisibleWarning,
)

DEFAULT_PRESENTATION_VERSION = "p1b_presentation.v1"
SOURCE_CONTRACT = "specs/presentation_response_contract.yaml"
FACT_POLICY = "persona_may_not_alter_facts"


def build_presentation_input(
    *,
    synthesis,
    substrate,
) -> PresentationInput:
    return PresentationInput(
        analytical_substrate=substrate,
        synthesis=synthesis,
    )


def run_presentation(presentation_input: PresentationInput) -> PresentationResult:
    synthesis = presentation_input.synthesis
    substrate = presentation_input.analytical_substrate
    visible_warnings = [
        VisibleWarning(
            code=warning.code,
            severity=warning.severity,
            message=warning.message,
        )
        for warning in synthesis.surfaced_warnings
    ]
    return PresentationResult(
        presentation_version=DEFAULT_PRESENTATION_VERSION,
        reply=_render_reply(synthesis.synthesized_judgement, substrate.status),
        why=_render_why(synthesis.why_summary, synthesis.surfaced_warnings),
        visible_warnings=visible_warnings,
        detail_sections=_build_detail_sections(presentation_input),
        followup_prompts=list(synthesis.followup_directions),
        presentation_metadata=PresentationMetadata(
            persona_id=None,
            facts_locked=True,
            fact_policy=FACT_POLICY,
            source_contract=SOURCE_CONTRACT,
        ),
    )


def _render_reply(judgement: str, status: AgentResponseStatus) -> str:
    text = judgement.strip()
    if status == AgentResponseStatus.REFUSED:
        return text
    if text.startswith("硬结论："):
        return text.removeprefix("硬结论：").lstrip()
    if text.startswith("暂定判断："):
        return text.removeprefix("暂定判断：").lstrip()
    if text.startswith("判断："):
        return text.removeprefix("判断：").lstrip()
    return text


def _render_why(why_summary: str, warnings: list[SynthesisWarning]) -> str:
    warning_line = _warning_line(warnings)
    if not warning_line:
        return why_summary.strip()
    base = why_summary.strip()
    if warning_line in base:
        return base
    return f"{warning_line} {base}".strip()


def _warning_line(warnings: list[SynthesisWarning]) -> str:
    if not warnings:
        return ""
    messages = [warning.message.strip() for warning in warnings if warning.message.strip()]
    if not messages:
        return ""
    return "注意：" + "；".join(messages)


def _build_detail_sections(presentation_input: PresentationInput) -> list[DetailSection]:
    substrate = presentation_input.analytical_substrate
    synthesis = presentation_input.synthesis
    sections = [
        DetailSection(
            section_id="analytical_base",
            label="分析基底",
            default_visibility=DetailSectionVisibility.EXPANDED,
            content_kind=DetailSectionContentKind.ANALYTICAL_BASE,
            content=substrate.answer_summary,
        ),
        DetailSection(
            section_id="evidence",
            label="证据",
            default_visibility=DetailSectionVisibility.COLLAPSED,
            content_kind=DetailSectionContentKind.EVIDENCE,
            content=_join_lines(
                f"{item.id} | {item.source_type} | {item.confidence} | {item.source_label}"
                for item in substrate.evidence
            ),
        ),
        DetailSection(
            section_id="confidence",
            label="置信说明",
            default_visibility=DetailSectionVisibility.COLLAPSED,
            content_kind=DetailSectionContentKind.CONFIDENCE,
            content=_join_lines(
                f"{note.claim_scope} | {note.confidence} | {note.note}"
                for note in substrate.confidence_notes
            ),
        ),
        DetailSection(
            section_id="tool_trace",
            label="工具轨迹",
            default_visibility=DetailSectionVisibility.COLLAPSED,
            content_kind=DetailSectionContentKind.TOOL_TRACE,
            content=_join_lines(
                f"{tool.tool_name} | {tool.status} | {tool.summary}"
                for tool in substrate.tool_results
            ),
        ),
        DetailSection(
            section_id="followup",
            label="后续建议",
            default_visibility=DetailSectionVisibility.COLLAPSED,
            content_kind=DetailSectionContentKind.FOLLOWUP,
            content=_join_lines(synthesis.followup_directions),
        ),
    ]
    return sections


def _join_lines(items) -> str:
    lines = [item for item in items if item]
    return "\n".join(lines) if lines else "None."
