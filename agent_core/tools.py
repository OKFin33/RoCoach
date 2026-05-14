from __future__ import annotations

from typing import Protocol

from agent_core.contracts import AgentResponse


class AgentRuntimeAdapter(Protocol):
    def set_team_context_slots(self, slots: list[dict[str, object]]) -> None:
        """Replace the current runtime team context with validated structured slots."""

    def handle_message(self, message: str) -> AgentResponse:
        """Execute one user message and return the app-facing agent response."""
