from __future__ import annotations

from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalyticalSubstrate,
    DoctrineDecisionHeuristic,
    DoctrineHonestyBoundary,
    DoctrineMentalModel,
    DoctrinePack,
    AnalysisType,
    SynthesisInput,
    SynthesisResult,
    SynthesisWarning,
    SynthesisWarningSeverity,
)

DEFAULT_SYNTHESIS_VERSION = "p1a_synthesis.v1"
DEFAULT_DOCTRINE_ID = "generic_battle_doctrine_pack"

DEFAULT_DOCTRINE_REFS = [
    "bottleneck_first_reasoning",
    "compressed_grounded_verdict",
    "anti_fabrication_boundary",
    "disputed_evidence_honesty_rule",
    "method_over_style_boundary",
]


def build_default_doctrine_pack() -> DoctrinePack:
    return DoctrinePack(
        doctrine_id=DEFAULT_DOCTRINE_ID,
        mental_models=[
            DoctrineMentalModel(
                name="bottleneck_first_reasoning",
                description="Assess decisions by the main structural bottleneck before secondary decoration.",
                use_when=[
                    "the current state has multiple possible issues",
                    "the user needs one grounded recommendation",
                ],
            ),
            DoctrineMentalModel(
                name="compressed_grounded_verdict",
                description="Collapse stable causal structure into one tight verdict instead of a padded option buffet.",
                use_when=[
                    "evidence is sufficient for a main direction",
                    "the answer should be concise and operational",
                ],
            ),
        ],
        decision_heuristics=[
            DoctrineDecisionHeuristic(
                rule="prioritize the real bottleneck before decorative options",
                rationale="Reasoning should surface the primary causal blocker before presenting nice-to-have branches.",
                preferred_scope=[
                    "team structure analysis",
                    "species role analysis",
                    "patch-direction recommendation",
                ],
            ),
            DoctrineDecisionHeuristic(
                rule="keep uncertainty visible when the evidence is disputed or partial",
                rationale="Honesty is part of the reasoning contract, not a formatting note.",
                preferred_scope=[
                    "partial evidence",
                    "provisional interpretation",
                    "refusal preservation",
                ],
            ),
        ],
        anti_patterns=[
            "empty reassurance in place of diagnosis",
            "fake optionality after the causal core is already clear",
            "style packaging that hides consequence transfer",
        ],
        honesty_boundaries=[
            DoctrineHonestyBoundary(
                trigger="evidence is disputed or only partially grounded",
                required_behavior="label the judgment as provisional and keep the grounded boundary visible.",
            ),
            DoctrineHonestyBoundary(
                trigger="a refusal or warning already exists in the substrate",
                required_behavior="preserve the refusal or warning instead of converting it into a normal recommendation.",
            ),
        ],
    )


def build_synthesis_input(
    substrate: AnalyticalSubstrate,
    doctrine_pack: DoctrinePack | None = None,
) -> SynthesisInput:
    return SynthesisInput(
        analytical_substrate=substrate,
        doctrine_pack=doctrine_pack or build_default_doctrine_pack(),
    )


def build_synthesis_input_from_response(
    response: AgentResponse,
    doctrine_pack: DoctrinePack | None = None,
) -> SynthesisInput:
    return build_synthesis_input(
        substrate=analytical_substrate_from_response(response),
        doctrine_pack=doctrine_pack,
    )


def analytical_substrate_from_response(response: AgentResponse) -> AnalyticalSubstrate:
    return AnalyticalSubstrate(
        status=response.status,
        backend=response.backend,
        analysis_type=response.analysis_type,
        answer_summary=response.answer,
        tool_results=response.tool_results,
        evidence=response.evidence,
        confidence_notes=response.confidence_notes,
        followup_options=response.followup_options,
    )


def run_synthesis(synthesis_input: SynthesisInput) -> SynthesisResult:
    try:
        return _run_synthesis(synthesis_input)
    except Exception as exc:  # pragma: no cover - defensive boundary
        return _fallback_synthesis_result(synthesis_input, reason=exc.__class__.__name__)


def _run_synthesis(synthesis_input: SynthesisInput) -> SynthesisResult:
    substrate = synthesis_input.analytical_substrate
    doctrine_pack = synthesis_input.doctrine_pack
    grounded_refs = [item.id for item in substrate.evidence]
    followup_directions = [option.label for option in substrate.followup_options]
    warnings = _derive_warnings(substrate)
    doctrine_refs = list(DEFAULT_DOCTRINE_REFS)
    if doctrine_pack.doctrine_id:
        doctrine_refs.insert(0, doctrine_pack.doctrine_id)

    synthesized_judgement = _compose_judgement(substrate, warnings)
    why_summary = _compose_why_summary(substrate, doctrine_pack, warnings)
    result = SynthesisResult(
        synthesis_version=DEFAULT_SYNTHESIS_VERSION,
        synthesized_judgement=synthesized_judgement,
        why_summary=why_summary,
        surfaced_warnings=warnings,
        followup_directions=followup_directions,
        grounding_refs=grounded_refs,
        doctrine_refs=doctrine_refs,
    )
    _validate_synthesis_result(result, substrate)
    return result


def _compose_judgement(
    substrate: AnalyticalSubstrate,
    warnings: list[SynthesisWarning],
) -> str:
    core = _trim_sentence(substrate.answer_summary)
    if substrate.status == AgentResponseStatus.REFUSED:
        return substrate.answer_summary.strip()

    intro = "硬结论"
    if _has_provisional_only_warning(warnings):
        intro = "暂定判断"

    if substrate.analysis_type == AnalysisType.TEAM_ANALYSIS:
        tail = "先收束真实瓶颈，不要把装饰性选项当成解法。"
    elif substrate.analysis_type == AnalysisType.SPECIES_ANALYSIS:
        tail = "角色判断要围绕主职能收束，不要把边角能力抬成主定位。"
    elif substrate.analysis_type == AnalysisType.UNSUPPORTED:
        tail = "这仍然只能保持拒绝或说明边界，不能改写成正常建议。"
    else:
        tail = "结论必须保持 grounded，不要把解释伪装成新事实。"

    if core:
        return f"{intro}：{core}。{tail}"
    return f"{intro}。{tail}"


def _compose_why_summary(
    substrate: AnalyticalSubstrate,
    doctrine_pack: DoctrinePack,
    warnings: list[SynthesisWarning],
) -> str:
    parts = [
        "基于已锁定的工具证据、置信边界和 follow-up 约束做压缩判断。",
    ]
    if doctrine_pack.mental_models:
        parts.append(f"当前 doctrine 侧重 {doctrine_pack.mental_models[0].name}。")
    if warnings:
        parts.append("已保留显式风险边界与拒绝边界。")
    if substrate.status == AgentResponseStatus.REFUSED:
        parts.append("拒绝结果保持原样，不会被改写成正常推荐。")
    elif any(_confidence_is(note.confidence, "provisional") for note in substrate.confidence_notes):
        parts.append("其中部分判断仍是 provisional，因此不提升为确定性事实。")
    else:
        parts.append("结论只做 framing，不改写 grounded facts。")
    return " ".join(parts)


def _derive_warnings(substrate: AnalyticalSubstrate) -> list[SynthesisWarning]:
    warnings: list[SynthesisWarning] = []
    if _looks_partial_team(substrate):
        warnings.append(
            SynthesisWarning(
                code="partial_team",
                severity=SynthesisWarningSeverity.MEDIUM,
                message="Partial team context remains visible; the judgment only covers the supplied slots.",
            )
        )
    if _looks_provisional_only(substrate):
        warnings.append(
            SynthesisWarning(
                code="provisional_only",
                severity=SynthesisWarningSeverity.MEDIUM,
                message="Only provisional interpretation is available from the current substrate.",
            )
        )
    if _looks_deterministic_fallback(substrate):
        warnings.append(
            SynthesisWarning(
                code="deterministic_fallback",
                severity=SynthesisWarningSeverity.LOW,
                message="Synthesis is operating on a deterministic fallback substrate.",
            )
        )
    if _looks_unsupported_scope(substrate):
        warnings.append(
            SynthesisWarning(
                code="unsupported_scope",
                severity=SynthesisWarningSeverity.HIGH,
                message="The requested scope remains unsupported by the current product boundary.",
            )
        )
    if _looks_refused_missing_context(substrate):
        warnings.append(
            SynthesisWarning(
                code="refused_missing_context",
                severity=SynthesisWarningSeverity.HIGH,
                message="The refusal is driven by missing context required for a grounded answer.",
            )
        )
    if _looks_refused_missing_species(substrate):
        warnings.append(
            SynthesisWarning(
                code="refused_missing_species",
                severity=SynthesisWarningSeverity.HIGH,
                message="The refusal is driven by missing species grounding.",
            )
        )
    return warnings


def _looks_partial_team(substrate: AnalyticalSubstrate) -> bool:
    haystacks = [
        substrate.answer_summary,
        *(note.note for note in substrate.confidence_notes),
        *(option.label for option in substrate.followup_options),
    ]
    lowered = " ".join(haystacks).lower()
    return "partial-team" in lowered or "剩余" in lowered or "缺少" in lowered


def _looks_provisional_only(substrate: AnalyticalSubstrate) -> bool:
    has_provisional_note = any(_confidence_is(note.confidence, "provisional") for note in substrate.confidence_notes)
    has_confirmed_note = any(_confidence_is(note.confidence, "confirmed") for note in substrate.confidence_notes)
    lowered = substrate.answer_summary.lower()
    return (has_provisional_note and not has_confirmed_note) or "provisional" in lowered


def _looks_deterministic_fallback(substrate: AnalyticalSubstrate) -> bool:
    lowered_backend = substrate.backend.lower()
    lowered_answer = substrate.answer_summary.lower()
    return "auto_fallback" in lowered_backend or "回退" in lowered_answer or "fallback" in lowered_answer


def _looks_unsupported_scope(substrate: AnalyticalSubstrate) -> bool:
    lowered = substrate.answer_summary.lower()
    return substrate.analysis_type == AnalysisType.UNSUPPORTED or any(
        marker in lowered for marker in ("不支持", "unsupported", "cannot", "无法")
    )


def _looks_refused_missing_context(substrate: AnalyticalSubstrate) -> bool:
    lowered = substrate.answer_summary.lower()
    return substrate.status == AgentResponseStatus.REFUSED and any(
        marker in lowered
        for marker in (
            "context",
            "上下文",
            "web/live",
            "官方平衡公告",
        )
    )


def _looks_refused_missing_species(substrate: AnalyticalSubstrate) -> bool:
    lowered = substrate.answer_summary.lower()
    return substrate.status == AgentResponseStatus.REFUSED and any(
        marker in lowered for marker in ("species", "物种", "/species")
    )


def _validate_synthesis_result(result: SynthesisResult, substrate: AnalyticalSubstrate) -> None:
    if not result.synthesized_judgement.strip():
        raise ValueError("synthesized_judgement must not be empty")
    if not result.why_summary.strip():
        raise ValueError("why_summary must not be empty")
    if not result.grounding_refs and substrate.evidence:
        raise ValueError("grounding_refs must preserve evidence grounding")
    if substrate.status == AgentResponseStatus.REFUSED and not result.synthesized_judgement:
        raise ValueError("refusal must remain visible")


def _fallback_synthesis_result(
    synthesis_input: SynthesisInput,
    *,
    reason: str,
) -> SynthesisResult:
    substrate = synthesis_input.analytical_substrate
    grounded_refs = [item.id for item in substrate.evidence]
    followup_directions = [option.label for option in substrate.followup_options]
    warning = SynthesisWarning(
        code="deterministic_fallback",
        severity=SynthesisWarningSeverity.LOW,
        message=f"Synthesis fell back to a bounded deterministic projection after {reason}.",
    )
    return SynthesisResult(
        synthesis_version=DEFAULT_SYNTHESIS_VERSION,
        synthesized_judgement=_trim_sentence(substrate.answer_summary) or "Synthesis unavailable.",
        why_summary="Synthesis fell back to a bounded deterministic projection.",
        surfaced_warnings=[warning],
        followup_directions=followup_directions,
        grounding_refs=grounded_refs,
        doctrine_refs=[synthesis_input.doctrine_pack.doctrine_id, *DEFAULT_DOCTRINE_REFS],
    )


def _has_provisional_only_warning(warnings: list[SynthesisWarning]) -> bool:
    return any(warning.code == "provisional_only" for warning in warnings)


def _confidence_is(value: object, expected: str) -> bool:
    return str(value) == expected


def _trim_sentence(text: str) -> str:
    trimmed = text.strip()
    while trimmed and trimmed[-1] in "。.!?！？":
        trimmed = trimmed[:-1].rstrip()
    return trimmed
