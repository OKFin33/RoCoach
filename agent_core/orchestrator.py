from __future__ import annotations

from agent_core.contracts import AgentResponse, DoctrinePack, PersonaEnvelope
from agent_core.persona import PersonaBoundary
from agent_core.presentation import build_presentation_input, run_presentation
from agent_core.synthesis import (
    analytical_substrate_from_response,
    build_default_doctrine_pack,
    build_synthesis_input,
    run_synthesis,
)
from agent_core.safety import SafetyGuard, refusal_response_from_decision
from agent_core.tools import AgentRuntimeAdapter


class AgentOrchestrator:
    def __init__(
        self,
        *,
        runtime_adapter: AgentRuntimeAdapter,
        safety_guard: SafetyGuard | None = None,
        persona_boundary: PersonaBoundary | None = None,
        doctrine_pack: DoctrinePack | None = None,
    ) -> None:
        self.runtime_adapter = runtime_adapter
        self.safety_guard = safety_guard or SafetyGuard()
        self.persona_boundary = persona_boundary or PersonaBoundary()
        self.doctrine_pack = doctrine_pack or build_default_doctrine_pack()

    def handle_message(
        self,
        message: str,
        *,
        persona: PersonaEnvelope | None = None,
    ) -> AgentResponse:
        safety_decision = self.safety_guard.evaluate(message)
        if not safety_decision.allowed:
            response = refusal_response_from_decision(safety_decision)
        else:
            response = self.runtime_adapter.handle_message(message)

        synthesis_input = build_synthesis_input(
            substrate=analytical_substrate_from_response(response),
            doctrine_pack=self.doctrine_pack,
        )
        synthesis_result = run_synthesis(synthesis_input)
        presentation_input = build_presentation_input(
            synthesis=synthesis_result,
            substrate=synthesis_input.analytical_substrate,
        )
        presentation_result = run_presentation(presentation_input)
        response = response.model_copy(
            update={
                "answer": presentation_result.reply,
                "synthesis": synthesis_result,
                "presentation": presentation_result,
            },
            deep=True,
        )
        return self.persona_boundary.attach_metadata(response, persona)
