from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Any, Callable
from uuid import uuid4

from fastapi import HTTPException

from advisor.battle_dex import BattleDexRepository, DEFAULT_RUNTIME_DB, ensure_battle_dex_sqlite
from advisor.config import RocoNativeModelConfig
from advisor.retrieval import DocContextRetriever
from advisor.runtime import AdvisorAgent, InMemorySessionStateStore, _native_runtime_fingerprint
from agent_core.adapters.advisor import AdvisorRuntimeAdapter
from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AgentRuntimePath,
    AnalysisType,
    ConfidenceNote,
    FollowupOption,
    PersonaEnvelope,
    PersonaRuntimeActivationScope,
)
from agent_core.orchestrator import AgentOrchestrator
from agent_core.persona import PersonaBoundary
from agent_core.persona_profile_config import (
    PersonaProfileConfigError,
    build_persona_profile_resolver_from_materialization_path,
)
from agent_core.persona_profile_resolver import PersonaProfileResolver
from api.logging_utils import get_api_logger, summarize_exception
from api.contracts import TeamContextAttachment, TeamContextSlot
from api.runtime_headers import RequestRuntimeConfig, RequestRuntimeMode
from api.services.session_store import (
    ActiveSessionStore,
    SessionEvent,
    SessionResolution,
    allow_in_memory_session_fallback,
    resolve_session_db_path,
)
from engine.contracts import TeamSlot, to_payload
from knowledge.contracts import ConfidenceTier


logger = get_api_logger()


@dataclass
class AdvisorService:
    repository: BattleDexRepository | None
    default_backend: str = "deterministic"
    startup_error: str | None = None
    persona_resolver: PersonaProfileResolver = field(default_factory=PersonaProfileResolver)
    managed_persona_startup_error: str | None = None
    request_native_model_factory: Callable[[RequestRuntimeConfig], Any] | None = None
    model_diagnostic_runner: Callable[[RocoNativeModelConfig, str], str] | None = None
    doc_retriever_factory: Callable[[], DocContextRetriever] | None = None
    native_timeout_seconds: float = 45.0
    request_runtime_session_ttl_seconds: float = 3600.0
    max_request_runtime_sessions: int = 128
    session_store: ActiveSessionStore | None = None
    session_db_path: Path | None = None
    _sessions: dict[str, AgentOrchestrator] = field(default_factory=dict)
    _request_runtime_state_stores: dict[str, InMemorySessionStateStore] = field(default_factory=dict)
    _request_runtime_last_used: dict[str, float] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    @classmethod
    def from_db_path(
        cls,
        db_path: Path = DEFAULT_RUNTIME_DB,
        *,
        bootstrap: bool = True,
        default_backend: str = "deterministic",
        managed_persona_materialization_path: Path | None = None,
        managed_persona_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    ) -> "AdvisorService":
        persona_resolver, managed_persona_startup_error = _safe_persona_resolver_from_config(
            managed_persona_materialization_path,
            allowed_scope=managed_persona_scope,
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
                session_db_path=resolve_session_db_path(),
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
                session_db_path=resolve_session_db_path(),
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
        context_attachments: list[dict[str, Any] | TeamContextAttachment] | None = None,
    ) -> tuple[str, AgentResponse, SessionEvent]:
        if not message.strip():
            raise HTTPException(status_code=422, detail=_safe_error("invalid_message"))

        context_slots: list[dict[str, object]] | None = None
        attachment_error: HTTPException | None = None
        try:
            context_slots = self._validated_context_slots(context_attachments)
        except HTTPException as exc:
            attachment_error = exc
        resolution = self._resolve_active_session(session_id)
        resolved_session_id = resolution.session_id
        if attachment_error is not None and _message_depends_on_team_context(message):
            return (
                resolved_session_id,
                _invalid_team_context_agent_response(_error_code_from_http_exception(attachment_error)),
                _with_attachment_diagnostic(
                    resolution.event,
                    code=_error_code_from_http_exception(attachment_error),
                    action="blocked_team_dependent_turn",
                ),
            )
        if attachment_error is not None:
            resolution = SessionResolution(
                session_id=resolution.session_id,
                store=resolution.store,
                event=_with_attachment_diagnostic(
                    resolution.event,
                    code=_error_code_from_http_exception(attachment_error),
                    action="ignored_for_unrelated_chat",
                ),
            )
        if runtime_config is not None and runtime_config.requests_native_runtime:
            resolution = self._prepare_native_session_resolution(
                resolution=resolution,
                runtime_config=runtime_config,
                is_clear_command=_is_clear_command(message),
            )
            resolved_session_id = resolution.session_id
            response = self._handle_request_scoped_runtime_chat(
                message=message,
                persona=persona,
                runtime_config=runtime_config,
                context_slots=context_slots,
                session_id=resolved_session_id,
                state_store=resolution.store,
            )
            if _is_clear_command(message):
                self._purge_session_caches(resolved_session_id)
                return resolved_session_id, response, _clear_session_event("chat_command_clear")
            return resolved_session_id, response, _event_for_response_continuity(response, resolution.event)

        orchestrator = self._get_or_create_session(
            resolved_session_id,
            state_store=resolution.store,
        )
        response = orchestrator.handle_message(
            message,
            persona=persona,
            team_context_slots=context_slots,
        )
        if _is_clear_command(message):
            self._purge_session_caches(resolved_session_id)
            return resolved_session_id, response, _clear_session_event("chat_command_clear")
        return resolved_session_id, response, _event_for_response_continuity(response, resolution.event)

    def clear_session(self, *, reason: str = "user_clear") -> tuple[str, SessionEvent]:
        session_id, event = self._active_session_store().clear_active(reason=reason)
        self._purge_session_caches(session_id)
        return session_id, event

    def _purge_session_caches(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._request_runtime_state_stores.pop(session_id, None)
            self._request_runtime_last_used.pop(session_id, None)

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

    def search_species(
        self,
        *,
        query: str,
        limit: int = 10,
        usage: str = "default",
    ) -> list[dict[str, object]]:
        repository = self._require_repository()
        safe_limit = max(1, min(limit, 50 if usage == "team_builder" else 20))
        return [
            hit.model_dump(mode="json")
            for hit in repository.search_species(
                query,
                limit=safe_limit,
                team_builder_eligible_only=usage == "team_builder",
            )
        ]

    def get_species_profile(self, *, species_id: str) -> dict[str, object]:
        repository = self._require_repository()
        profile = repository.get_species_profile(species_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=_safe_error("species_not_found"))
        return profile.model_dump(mode="json")

    def get_species_moves(self, *, species_id: str, limit: int | None = None) -> dict[str, object]:
        repository = self._require_repository()
        profile = repository.get_species_profile(species_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=_safe_error("species_not_found"))
        safe_limit = None if limit is None else max(1, min(limit, 200))
        moves = repository.get_species_available_moves(species_id, limit=safe_limit)
        return {
            "species_id": profile.species_id,
            "moves": [move.model_dump(mode="json") for move in moves],
        }

    def diagnose_model_service(
        self,
        *,
        runtime_config: RequestRuntimeConfig,
        prompt: str,
    ) -> dict[str, str]:
        if runtime_config.setup_error is not None or runtime_config.native_model_config is None:
            return _diagnostic_payload(
                status="failed",
                diagnostic_code=_diagnostic_code_for_setup_error(runtime_config.setup_error),
                message="Model service is not configured for this request.",
                native_config=runtime_config.native_model_config,
            )

        native_config = runtime_config.native_model_config
        try:
            content = (
                self.model_diagnostic_runner(native_config, prompt)
                if self.model_diagnostic_runner is not None
                else _run_openai_model_diagnostic(native_config, prompt)
            )
        except Exception as exc:
            return _diagnostic_payload(
                status="failed",
                diagnostic_code=_classify_provider_exception(exc),
                message="Model service test failed safely.",
                native_config=native_config,
            )

        if not content.strip():
            return _diagnostic_payload(
                status="failed",
                diagnostic_code="provider_unknown_error",
                message="Model service returned an empty response.",
                native_config=native_config,
            )

        return _diagnostic_payload(
            status="ok",
            diagnostic_code="ok",
            message="Model service responded successfully.",
            native_config=native_config,
        )

    def _get_or_create_session(
        self,
        session_id: str,
        *,
        state_store: InMemorySessionStateStore,
    ) -> AgentOrchestrator:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = self._new_orchestrator(state_store=state_store)
            return self._sessions[session_id]

    def _new_orchestrator(
        self,
        runtime_config: RequestRuntimeConfig | None = None,
        state_store: InMemorySessionStateStore | None = None,
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
            native_timeout_seconds=_native_timeout_for_model(
                native_model,
                default_seconds=self.native_timeout_seconds,
            ),
            doc_retriever=self.doc_retriever_factory() if self.doc_retriever_factory is not None else None,
            state_store=state_store,
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
        context_slots: list[dict[str, object]] | None,
        session_id: str,
        state_store: InMemorySessionStateStore,
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
            ).handle_message(message, persona=persona, team_context_slots=context_slots)

        orchestrator = self._new_orchestrator(
            runtime_config=runtime_config,
            state_store=state_store,
        )
        return orchestrator.handle_message(
            message,
            persona=persona,
            team_context_slots=context_slots,
        )

    def _resolve_active_session(self, requested_session_id: str | None):
        return self._active_session_store().resolve(requested_session_id)

    def _prepare_native_session_resolution(
        self,
        *,
        resolution: SessionResolution,
        runtime_config: RequestRuntimeConfig,
        is_clear_command: bool,
    ) -> SessionResolution:
        if is_clear_command or runtime_config.setup_error is not None:
            return resolution
        store = self._active_session_store()
        expected_fingerprint = _native_runtime_fingerprint(runtime_config.native_model_config)
        drop_event = store.validate_native_history(
            session_id=resolution.session_id,
            expected_fingerprint=expected_fingerprint,
        )
        if drop_event is not None:
            resolution = SessionResolution(
                session_id=resolution.session_id,
                store=resolution.store,
                event=drop_event,
            )
        rollover = store.maybe_rollover_for_context_pressure(session_id=resolution.session_id)
        return rollover or resolution

    def _active_session_store(self) -> ActiveSessionStore:
        with self._lock:
            if self.session_store is None:
                db_path = self.session_db_path or resolve_session_db_path()
                self.session_store = ActiveSessionStore(
                    db_path,
                    allow_in_memory_fallback=allow_in_memory_session_fallback(),
                )
            return self.session_store

    def _get_or_create_request_runtime_state_store(self, session_id: str) -> InMemorySessionStateStore:
        with self._lock:
            now = monotonic()
            self._prune_request_runtime_state_stores_locked(now)
            if session_id not in self._request_runtime_state_stores:
                self._request_runtime_state_stores[session_id] = InMemorySessionStateStore()
            self._request_runtime_last_used[session_id] = now
            return self._request_runtime_state_stores[session_id]

    def _prune_request_runtime_state_stores_locked(self, now: float) -> None:
        ttl = max(0.0, self.request_runtime_session_ttl_seconds)
        expired = [
            session_id
            for session_id, last_used in self._request_runtime_last_used.items()
            if now - last_used > ttl
        ]
        for session_id in expired:
            self._request_runtime_state_stores.pop(session_id, None)
            self._request_runtime_last_used.pop(session_id, None)

        max_sessions = max(1, self.max_request_runtime_sessions)
        overflow = len(self._request_runtime_state_stores) - max_sessions
        if overflow <= 0:
            return
        oldest = sorted(
            self._request_runtime_last_used.items(),
            key=lambda item: item[1],
        )[:overflow]
        for session_id, _last_used in oldest:
            self._request_runtime_state_stores.pop(session_id, None)
            self._request_runtime_last_used.pop(session_id, None)

    def _static_response_orchestrator(self, response: AgentResponse) -> AgentOrchestrator:
        return AgentOrchestrator(
            runtime_adapter=_StaticRuntimeAdapter(response),
            persona_boundary=PersonaBoundary(persona_resolver=self.persona_resolver),
        )

    def _require_repository(self) -> BattleDexRepository:
        if self.repository is None:
            raise HTTPException(status_code=503, detail=_safe_error("battle_dex_unavailable"))
        return self.repository

    def _validated_context_slots(
        self,
        context_attachments: list[dict[str, Any] | TeamContextAttachment] | None,
    ) -> list[dict[str, object]] | None:
        if not context_attachments:
            return None
        if len(context_attachments) > 1:
            raise HTTPException(status_code=422, detail=_safe_error("invalid_team_context"))

        raw_attachment = context_attachments[0]
        try:
            attachment = (
                raw_attachment
                if isinstance(raw_attachment, TeamContextAttachment)
                else TeamContextAttachment.model_validate(raw_attachment)
            )
        except Exception:
            raise HTTPException(status_code=422, detail=_safe_error("invalid_team_context"))
        if attachment.kind != "team_context":
            raise HTTPException(status_code=422, detail=_safe_error("invalid_team_context"))
        return [
            to_payload(slot)
            for slot in self._validated_team_slots_from_context(attachment.slots)
        ]

    def _validated_team_slots_from_context(
        self,
        slots: list[TeamContextSlot],
    ) -> list[TeamSlot]:
        repository = self._require_repository()
        validated_slots: list[TeamSlot] = []
        for slot in slots:
            profile = repository.get_species_profile(slot.species_id)
            if profile is None:
                raise HTTPException(status_code=422, detail=_safe_error("invalid_team_context_species"))
            available_moves = {
                move.move_id: move
                for move in repository.get_species_available_moves(profile.species_id, limit=None)
                if move.move_id
            }
            selected_move_names: list[str] = []
            for selected_move in slot.selected_moves:
                available = available_moves.get(selected_move.move_id)
                if available is None:
                    raise HTTPException(status_code=422, detail=_safe_error("invalid_team_context_move"))
                selected_move_names.append(available.move_name)

            validated_slots.append(
                TeamSlot(
                    slot_index=slot.slot_index,
                    species_key=profile.species_id,
                    primary_type=profile.primary_type,
                    secondary_type=profile.secondary_type,
                    selected_ability=profile.ability_name,
                    selected_moves=tuple(selected_move_names),
                    nature_label=slot.nature.label,
                    individual_value_bonuses=tuple(
                        {"stat": bonus.stat.value, "value": bonus.value}
                        for bonus in slot.individual_value_bonuses
                    ),
                    base_stats=profile.base_stats.model_dump(mode="json"),
                    nickname=slot.display_name,
                )
            )
        return validated_slots


def _safe_error(code: str) -> dict[str, str]:
    messages = {
        "battle_dex_unavailable": "Battle dex is unavailable in this local API process.",
        "invalid_message": "Message must not be empty.",
        "invalid_team": "Team payload must include at least one valid slot.",
        "species_not_found": "Species was not found in the local battle dex.",
        "invalid_team_context": "Team context attachment is invalid.",
        "invalid_team_context_species": "Team context includes a species not found in the local battle dex.",
        "invalid_team_context_move": "Team context includes a move not available to the selected species.",
    }
    return {"code": code, "message": messages.get(code, "Request failed safely.")}


def _error_code_from_http_exception(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, dict) and isinstance(detail.get("code"), str):
        return str(detail["code"])
    return "invalid_team_context"


def _message_depends_on_team_context(message: str) -> bool:
    stripped = message.strip()
    lowered = stripped.lower()
    team_markers = ("队伍", "这队", "联防", "补洞", "team", "analyze", "/analyze")
    return any(marker in stripped or marker in lowered for marker in team_markers)


def _with_attachment_diagnostic(
    event: SessionEvent,
    *,
    code: str,
    action: str,
) -> SessionEvent:
    diagnostic = dict(event.diagnostic)
    diagnostic["attachment_validation"] = {
        "status": "discarded",
        "code": code,
        "action": action,
    }
    return SessionEvent(
        type=event.type,
        reason=event.reason,
        message=event.message,
        user_action=event.user_action,
        diagnostic=diagnostic,
    )


def _event_for_response_continuity(response: AgentResponse, event: SessionEvent) -> SessionEvent:
    if response.continuity_persisted:
        return event
    diagnostic = dict(event.diagnostic)
    diagnostic["continuity"] = {
        "status": "not_persisted",
        "code": "continuity_not_persisted",
    }
    return SessionEvent(
        type=event.type,
        reason="continuity_not_persisted",
        message="本轮回答已生成，但当前会话连续性写入失败。",
        user_action="后续追问可能需要重新说明上下文。",
        diagnostic=diagnostic,
    )


def _invalid_team_context_agent_response(code: str) -> AgentResponse:
    return AgentResponse(
        status=AgentResponseStatus.DEGRADED,
        backend="deterministic",
        runtime_path=AgentRuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
        continuity_persisted=True,
        analysis_type=AnalysisType.RUNTIME_FAILURE,
        answer=(
            "队伍设置里有一项当前无法验证，所以这轮不能按队伍分析继续。"
            "请先修正队伍里的精灵或技能；普通聊天和单只精灵问题仍然可以继续。"
        ),
        tool_results=[],
        evidence=[],
        confidence_notes=[
            ConfidenceNote(
                claim_scope="team_context_validation",
                confidence=ConfidenceTier.CONFIRMED,
                note=f"attachment_validation_failed:{code}; no partial team context was committed.",
            )
        ],
        followup_options=[
            FollowupOption(id="fix_team_context", label="修正队伍设置", action="open_team_builder"),
            FollowupOption(id="ask_species", label="先问单只精灵", action="species_query"),
        ],
    )


def _is_clear_command(message: str) -> bool:
    return message.strip() == "/clear"


def _clear_session_event(reason: str) -> SessionEvent:
    return SessionEvent(
        type="cleared",
        reason=reason,
        message="已清空当前会话状态。",
        user_action="可以继续新的提问。",
        diagnostic={
            "agent_context": "reset",
            "visible_messages": "clear",
            "archive": "written",
            "support_code": reason,
        },
    )


def _runtime_setup_response(
    *,
    status: AgentResponseStatus,
    backend: str,
) -> AgentResponse:
    return AgentResponse(
        status=status,
        backend=backend,
        runtime_path=AgentRuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
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


def _native_timeout_for_model(native_model: Any | None, *, default_seconds: float) -> float:
    if isinstance(native_model, RocoNativeModelConfig):
        marker = f"{native_model.model_name} {native_model.base_url}".casefold()
        if "deepseek" in marker:
            return max(default_seconds, 90.0)
    return default_seconds


def _run_openai_model_diagnostic(native_config: RocoNativeModelConfig, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=native_config.api_key,
        base_url=native_config.base_url,
        timeout=20.0,
    )
    kwargs: dict[str, Any] = {}
    marker = f"{native_config.model_name} {native_config.base_url}".casefold()
    if "deepseek" in marker:
        if native_config.reasoning_mode == "enabled":
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            if native_config.reasoning_effort:
                kwargs["reasoning_effort"] = native_config.reasoning_effort
        else:
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    response = client.chat.completions.create(
        model=native_config.model_name,
        messages=[
            {"role": "system", "content": "You are a concise model-service diagnostic assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
        **kwargs,
    )
    return (response.choices[0].message.content or "").strip()


def _diagnostic_payload(
    *,
    status: str,
    diagnostic_code: str,
    message: str,
    native_config: RocoNativeModelConfig | None,
) -> dict[str, str]:
    marker = ""
    if native_config is not None:
        marker = f"{native_config.model_name} {native_config.base_url}".casefold()
    return {
        "status": status,
        "diagnostic_code": diagnostic_code,
        "message": message,
        "provider_family_hint": "deepseek" if "deepseek" in marker else "openai_compatible",
    }


def _diagnostic_code_for_setup_error(setup_error: str | None) -> str:
    if setup_error in {"missing_native_runtime_config", "missing_runtime_mode"}:
        return "provider_unknown_error"
    if setup_error == "invalid_native_runtime_config":
        return "provider_parameter_error"
    return "provider_unknown_error"


def _classify_provider_exception(exc: Exception) -> str:
    text = f"{exc.__class__.__name__} {exc}".casefold()
    if "401" in text or "unauthorized" in text or "authentication" in text:
        return "invalid_or_unauthorized_provider_key"
    if "404" in text or ("model" in text and "not" in text):
        return "model_id_not_accepted_by_provider"
    if "400" in text or "parameter" in text or "reasoning" in text or "thinking" in text:
        return "unsupported_reasoning_or_tool_parameter"
    if "timeout" in text:
        return "provider_request_exceeded_timeout"
    if "network" in text or "connect" in text or "tls" in text or "dns" in text:
        return "provider_unreachable_or_dns_tls_failure"
    return "provider_failure_not_yet_classified"


class _StaticRuntimeAdapter:
    def __init__(self, response: AgentResponse) -> None:
        self.response = response

    def set_team_context_slots(self, slots: list[dict[str, object]]) -> None:
        return None

    def handle_message(self, message: str) -> AgentResponse:
        return self.response


def _safe_persona_resolver_from_config(
    materialization_path: Path | None,
    *,
    allowed_scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
) -> tuple[PersonaProfileResolver, str | None]:
    if materialization_path is None:
        return PersonaProfileResolver(), None
    try:
        return build_persona_profile_resolver_from_materialization_path(
            materialization_path,
            allowed_scope=allowed_scope,
        ), None
    except PersonaProfileConfigError as exc:
        logger.warning(
            "managed_persona_config_unavailable code=managed_persona_config_unavailable exception_type=%s",
            summarize_exception(exc),
        )
        return PersonaProfileResolver(), "managed_persona_config_unavailable"
