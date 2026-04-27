from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from fastapi import HTTPException

from advisor.battle_dex import BattleDexRepository, DEFAULT_RUNTIME_DB, ensure_battle_dex_sqlite
from advisor.runtime import AdvisorAgent
from agent_core.adapters.advisor import AdvisorRuntimeAdapter
from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalysisType,
    ConfidenceNote,
    PersonaEnvelope,
)
from agent_core.orchestrator import AgentOrchestrator
from agent_core.persona import PersonaBoundary
from agent_core.persona_profile_config import (
    PersonaProfileConfigError,
    build_persona_profile_resolver_from_materialization_path,
)
from agent_core.persona_profile_resolver import PersonaProfileResolver
from api.logging_utils import get_api_logger, summarize_exception
from api.runtime_headers import RequestRuntimeConfig, RequestRuntimeMode
from reporting.contracts import ConfidenceTier


logger = get_api_logger()


@dataclass
class AdvisorService:
    repository: BattleDexRepository | None
    default_backend: str = "deterministic"
    startup_error: str | None = None
    persona_resolver: PersonaProfileResolver = field(default_factory=PersonaProfileResolver)
    managed_persona_startup_error: str | None = None
    request_native_model_factory: Callable[[RequestRuntimeConfig], Any] | None = None
    _sessions: dict[str, AgentOrchestrator] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    @classmethod
    def from_db_path(
        cls,
        db_path: Path = DEFAULT_RUNTIME_DB,
        *,
        bootstrap: bool = True,
        default_backend: str = "deterministic",
        managed_persona_materialization_path: Path | None = None,
    ) -> "AdvisorService":
        persona_resolver, managed_persona_startup_error = _safe_persona_resolver_from_config(
            managed_persona_materialization_path
        )
        try:
            resolved_db_path = ensure_battle_dex_sqlite(db_path) if bootstrap else db_path
            repository = BattleDexRepository(resolved_db_path)
            repository._ensure_db_exists()
            return cls(
                repository=repository,
                default_backend=default_backend,
                persona_resolver=persona_resolver,
                managed_persona_startup_error=managed_persona_startup_error,
            )
        except Exception as exc:
            logger.warning(
                "battle_dex_startup_unavailable code=battle_dex_unavailable exception_type=%s",
                summarize_exception(exc),
            )
            return cls(
                repository=None,
                default_backend=default_backend,
                startup_error="battle_dex_unavailable",
                persona_resolver=persona_resolver,
                managed_persona_startup_error=managed_persona_startup_error,
            )

    @property
    def battle_dex_available(self) -> bool:
        return self.repository is not None

    def chat(
        self,
        *,
        message: str,
        session_id: str | None = None,
        persona: PersonaEnvelope | None = None,
        runtime_config: RequestRuntimeConfig | None = None,
    ) -> tuple[str, AgentResponse]:
        if not message.strip():
            raise HTTPException(status_code=422, detail=_safe_error("invalid_message"))

        resolved_session_id = session_id or uuid4().hex
        if runtime_config is not None and runtime_config.requests_native_runtime:
            return resolved_session_id, self._handle_request_scoped_runtime_chat(
                message=message,
                persona=persona,
                runtime_config=runtime_config,
            )

        orchestrator = self._get_or_create_session(resolved_session_id)
        return resolved_session_id, orchestrator.handle_message(message, persona=persona)

    def analyze_team(
        self,
        *,
        slots: list[tuple[str, str | None]],
        persona: PersonaEnvelope | None = None,
    ) -> AgentResponse:
        if not slots:
            raise HTTPException(status_code=422, detail=_safe_error("invalid_team"))
        message = "分析 " + " ".join(
            primary if secondary is None else f"{primary}/{secondary}"
            for primary, secondary in slots
        ) + " 这队联防"
        orchestrator = self._new_orchestrator()
        return orchestrator.handle_message(message, persona=persona)

    def search_species(self, *, query: str, limit: int = 10) -> list[dict[str, object]]:
        repository = self._require_repository()
        safe_limit = max(1, min(limit, 20))
        return [
            hit.model_dump(mode="json")
            for hit in repository.search_species(query, limit=safe_limit)
        ]

    def get_species_profile(self, *, species_id: str) -> dict[str, object]:
        repository = self._require_repository()
        profile = repository.get_species_profile(species_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=_safe_error("species_not_found"))
        return profile.model_dump(mode="json")

    def _get_or_create_session(self, session_id: str) -> AgentOrchestrator:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = self._new_orchestrator()
            return self._sessions[session_id]

    def _new_orchestrator(
        self,
        runtime_config: RequestRuntimeConfig | None = None,
    ) -> AgentOrchestrator:
        backend = self.default_backend
        native_model: Any | None = None
        auto_selected = False
        if runtime_config is not None and runtime_config.requests_native_runtime:
            backend = "pydantic_ai_native"
            auto_selected = runtime_config.mode == RequestRuntimeMode.AUTO
            native_model = (
                self.request_native_model_factory(runtime_config)
                if self.request_native_model_factory is not None and runtime_config.native_model_config is not None
                else runtime_config.native_model_config
            )
        advisor_agent = AdvisorAgent(
            repository=self.repository,
            backend=backend,
            native_model=native_model,
            auto_selected=auto_selected,
        )
        return AgentOrchestrator(
            runtime_adapter=AdvisorRuntimeAdapter(advisor_agent),
            persona_boundary=PersonaBoundary(persona_resolver=self.persona_resolver),
        )

    def _handle_request_scoped_runtime_chat(
        self,
        *,
        message: str,
        persona: PersonaEnvelope | None,
        runtime_config: RequestRuntimeConfig,
    ) -> AgentResponse:
        if runtime_config.setup_error is not None:
            status = (
                AgentResponseStatus.DEGRADED
                if runtime_config.mode == RequestRuntimeMode.AUTO
                else AgentResponseStatus.FAILED
            )
            backend = (
                "auto_fallback_deterministic"
                if runtime_config.mode == RequestRuntimeMode.AUTO
                else "pydantic_ai_native"
            )
            return self._static_response_orchestrator(
                _runtime_setup_response(status=status, backend=backend)
            ).handle_message(message, persona=persona)

        orchestrator = self._new_orchestrator(runtime_config=runtime_config)
        return orchestrator.handle_message(message, persona=persona)

    def _static_response_orchestrator(self, response: AgentResponse) -> AgentOrchestrator:
        return AgentOrchestrator(
            runtime_adapter=_StaticRuntimeAdapter(response),
            persona_boundary=PersonaBoundary(persona_resolver=self.persona_resolver),
        )

    def _require_repository(self) -> BattleDexRepository:
        if self.repository is None:
            raise HTTPException(status_code=503, detail=_safe_error("battle_dex_unavailable"))
        return self.repository


def _safe_error(code: str) -> dict[str, str]:
    messages = {
        "battle_dex_unavailable": "Battle dex is unavailable in this local API process.",
        "invalid_message": "Message must not be empty.",
        "invalid_team": "Team payload must include at least one valid slot.",
        "species_not_found": "Species was not found in the local battle dex.",
    }
    return {"code": code, "message": messages.get(code, "Request failed safely.")}


def _runtime_setup_response(
    *,
    status: AgentResponseStatus,
    backend: str,
) -> AgentResponse:
    return AgentResponse(
        status=status,
        backend=backend,
        analysis_type=AnalysisType.RUNTIME_FAILURE,
        answer=(
            "Native LLM runtime is not configured for this request. "
            "Provide runtime mode, provider base URL, model, and provider key, or use deterministic mode."
        ),
        tool_results=[],
        evidence=[],
        confidence_notes=[
            ConfidenceNote(
                claim_scope="runtime_backend",
                confidence=ConfidenceTier.CONFIRMED,
                note="Request-scoped native runtime setup is missing or invalid; no provider secrets were stored.",
            )
        ],
        followup_options=[],
    )


class _StaticRuntimeAdapter:
    def __init__(self, response: AgentResponse) -> None:
        self.response = response

    def handle_message(self, message: str) -> AgentResponse:
        return self.response


def _safe_persona_resolver_from_config(
    materialization_path: Path | None,
) -> tuple[PersonaProfileResolver, str | None]:
    if materialization_path is None:
        return PersonaProfileResolver(), None
    try:
        return build_persona_profile_resolver_from_materialization_path(materialization_path), None
    except PersonaProfileConfigError as exc:
        logger.warning(
            "managed_persona_config_unavailable code=managed_persona_config_unavailable exception_type=%s",
            summarize_exception(exc),
        )
        return PersonaProfileResolver(), "managed_persona_config_unavailable"
