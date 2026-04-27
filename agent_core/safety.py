from __future__ import annotations

from dataclasses import dataclass, field

from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalysisType,
    FollowupOption,
)


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str | None = None
    answer: str | None = None
    followup_options: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def allow(cls) -> "SafetyDecision":
        return cls(allowed=True)

    @classmethod
    def refuse(
        cls,
        *,
        reason: str,
        answer: str,
        followup_options: tuple[str, ...] = (),
    ) -> "SafetyDecision":
        return cls(
            allowed=False,
            reason=reason,
            answer=answer,
            followup_options=followup_options,
        )


class SafetyGuard:
    def evaluate(self, message: str) -> SafetyDecision:
        return SafetyDecision.allow()


def refusal_response_from_decision(decision: SafetyDecision) -> AgentResponse:
    answer = decision.answer or "当前请求被安全边界拒绝。"
    return AgentResponse(
        status=AgentResponseStatus.REFUSED,
        backend="agent_core_safety",
        analysis_type=AnalysisType.UNSUPPORTED,
        answer=answer,
        tool_results=[],
        evidence=[],
        confidence_notes=[],
        followup_options=[
            FollowupOption(id=f"followup_{index:03d}", label=option, action=option)
            for index, option in enumerate(decision.followup_options, start=1)
        ],
        persona=None,
    )
