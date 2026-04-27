from __future__ import annotations

from advisor.contracts import AdvisorEvidenceItem, AdvisorResponse, AdvisorToolResult
from advisor.runtime import AdvisorAgent
from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalyticalSubstrate,
    AgentToolResult,
    AnalysisType,
    ConfidenceNote,
    EvidenceItem,
    FollowupOption,
    PersonaEnvelope,
)
from reporting.contracts import ConfidenceTier


class AdvisorRuntimeAdapter:
    def __init__(self, advisor_agent: AdvisorAgent) -> None:
        self.advisor_agent = advisor_agent

    def handle_message(self, message: str) -> AgentResponse:
        return agent_response_from_advisor(self.advisor_agent.handle_message(message))


def analytical_substrate_from_advisor(response: AdvisorResponse) -> AnalyticalSubstrate:
    evidence = [
        _evidence_item_from_advisor(index, item)
        for index, item in enumerate(response.evidence_summary, start=1)
    ]
    tool_results = [
        _tool_result_from_advisor(tool_result, evidence)
        for tool_result in response.tool_results
    ]
    return AnalyticalSubstrate(
        status=_infer_response_status(response),
        backend=response.backend,
        analysis_type=_infer_analysis_type(response),
        answer_summary=response.answer_summary,
        tool_results=tool_results,
        evidence=evidence,
        confidence_notes=[
            _confidence_note_from_advisor(note) for note in response.confidence_notes
        ],
        followup_options=[
            FollowupOption(id=f"followup_{index:03d}", label=option, action=option)
            for index, option in enumerate(response.followup_options, start=1)
        ],
    )


def agent_response_from_advisor(
    response: AdvisorResponse,
    *,
    analysis_type: AnalysisType | str | None = None,
    persona: PersonaEnvelope | None = None,
) -> AgentResponse:
    substrate = analytical_substrate_from_advisor(response)
    return AgentResponse(
        status=substrate.status,
        backend=substrate.backend,
        analysis_type=_coerce_analysis_type(analysis_type) or substrate.analysis_type,
        answer=substrate.answer_summary,
        tool_results=substrate.tool_results,
        evidence=substrate.evidence,
        confidence_notes=substrate.confidence_notes,
        followup_options=substrate.followup_options,
        synthesis=None,
        persona=persona,
    )


def _evidence_item_from_advisor(index: int, item: AdvisorEvidenceItem) -> EvidenceItem:
    return EvidenceItem(
        id=f"ev_{index:03d}",
        source_type=str(item.source_type),
        source_label=item.source_label,
        confidence=item.confidence,
        content=item.content,
        retrieval_reason=item.retrieval_reason,
    )


def _tool_result_from_advisor(
    tool_result: AdvisorToolResult,
    evidence: list[EvidenceItem],
) -> AgentToolResult:
    return AgentToolResult(
        tool_name=tool_result.tool_name,
        status=AgentResponseStatus(str(tool_result.status)),
        summary=tool_result.summary,
        evidence_refs=_evidence_refs_for_tool(tool_result.tool_name, evidence),
        payload=tool_result.payload,
    )


def _evidence_refs_for_tool(tool_name: str, evidence: list[EvidenceItem]) -> list[str]:
    if not evidence:
        return []
    if tool_name == "retrieve_doc_context":
        return [item.id for item in evidence if item.source_type == "doc"]
    if tool_name == "analyze_team_structure":
        return [item.id for item in evidence if item.source_type == "engine"]
    if tool_name in {
        "get_species_profile",
        "get_species_available_moves",
        "analyze_species_semantics",
    }:
        return [item.id for item in evidence if item.source_type == "fact"]
    return [item.id for item in evidence]


def _confidence_note_from_advisor(note: str) -> ConfidenceNote:
    lowered = note.lower()
    if "confirmed" in lowered or "deterministic" in lowered or "sqlite" in lowered:
        confidence = ConfidenceTier.CONFIRMED
    elif "provisional" in lowered:
        confidence = ConfidenceTier.PROVISIONAL
    else:
        confidence = ConfidenceTier.LOW_CONFIDENCE
    return ConfidenceNote(
        claim_scope=_infer_claim_scope(note),
        confidence=confidence,
        note=note,
    )


def _infer_claim_scope(note: str) -> str:
    lowered = note.lower()
    if "auto backend" in lowered or "native" in lowered:
        return "runtime_backend"
    if "partial-team" in lowered:
        return "input_scope"
    if "结构" in note or "team" in lowered:
        return "team_structure"
    if "物种" in note or "定位" in note or "species" in lowered:
        return "species_semantics"
    if "双属性" in note or "dual-type" in lowered:
        return "type_chart_assumption"
    return "general"


def _infer_response_status(response: AdvisorResponse) -> AgentResponseStatus:
    tool_statuses = {str(result.status) for result in response.tool_results}
    answer = response.answer_summary.lower()
    if "failed" in tool_statuses:
        return AgentResponseStatus.FAILED
    if "degraded" in tool_statuses or response.backend == "auto_fallback_deterministic":
        return AgentResponseStatus.DEGRADED
    if tool_statuses and tool_statuses <= {"refused"}:
        return AgentResponseStatus.REFUSED
    if not response.tool_results and _looks_like_runtime_failure(answer):
        return AgentResponseStatus.FAILED
    if not response.tool_results and _looks_like_refusal(answer):
        return AgentResponseStatus.REFUSED
    return AgentResponseStatus.OK


def _looks_like_runtime_failure(answer: str) -> bool:
    return "native runtime" in answer and ("不可用" in answer or "failure" in answer)


def _looks_like_refusal(answer: str) -> bool:
    refusal_markers = (
        "当前 mvp",
        "不能预测",
        "无法",
        "没有找到",
        "不支持",
        "unsupported",
        "refuse",
    )
    return any(marker in answer for marker in refusal_markers)


def _infer_analysis_type(response: AdvisorResponse) -> AnalysisType:
    tool_names = {result.tool_name for result in response.tool_results}
    answer = response.answer_summary.lower()
    if "analyze_team_structure" in tool_names:
        return AnalysisType.TEAM_ANALYSIS
    if {
        "get_species_profile",
        "get_species_available_moves",
        "analyze_species_semantics",
    } & tool_names:
        return AnalysisType.SPECIES_ANALYSIS
    if _looks_like_runtime_failure(answer):
        return AnalysisType.RUNTIME_FAILURE
    if _looks_like_refusal(answer):
        return AnalysisType.UNSUPPORTED
    if not response.tool_results:
        return AnalysisType.SESSION_COMMAND
    return AnalysisType.UNKNOWN


def _coerce_analysis_type(value: AnalysisType | str | None) -> AnalysisType | None:
    if value is None:
        return None
    return value if isinstance(value, AnalysisType) else AnalysisType(value)
